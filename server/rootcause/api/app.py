"""FastAPI surface for RootCause.

The API is intentionally small and boring: a pilot needs to run for 90 days behind a factory
firewall. Every mutation writes an audit event. The AI never approves a cause.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .. import config
from ..agent.jiuwen_runtime import OpenJiuwenRuntime
from ..connectors import CmmsConnector, ModbusConnector, OpcUaConnector, connector_catalog, normalise_frame
from ..demo.build_pack import build_pack
from ..engine.analytics import (
    anonymised_sharing_payload,
    compliance_export,
    cross_line_patterns,
    defect_series,
    pilot_summary,
    savings_from_actions,
    top_causes,
    trend_alerts,
)
from ..engine.feedback import apply_priors, priors_from_corrections
from ..engine.orchestrator import run_investigation
from ..engine.ranking import explain, rank_hypotheses
from ..engine.reporting import report_docx, report_html, report_markdown, report_pdf, report_rtf
from ..laix import (
    Constraints as LaixConstraints,
)
from ..laix import (
    ExperienceState as LaixState,
)
from ..laix import (
    FollowUp as LaixFollowUp,
)
from ..laix import (
    QualityInterventionPolicy,
    estimate_outcome,
)
from ..laix import (
    Signal as LaixSignal,
)
from ..models import (
    AcceptRequest,
    ApprovalRequest,
    Evidence,
    ManualCauseRequest,
    RejectRequest,
    Report,
    ReportPatch,
    RiskSignal,
    now_iso,
)
from ..npu.broker import broker_from_env
from ..proactive import brief as brief_engine
from ..proactive import containment, scheduler
from ..proactive import metrics as proactive_metrics
from ..proactive import notifications as notify
from ..proactive import watch as watch_engine
from ..proactive.privacy import sanitize_note
from ..proactive.queue import OfflineQueue
from ..research import predictive
from ..tenancy import DEFAULT_TENANT, StoreRouter, current_tenant, set_tenant


def load_pack() -> dict[str, Any]:
    import os

    pack_path = Path(os.getenv("ROOTCAUSE_PACK", str(config.PACK_PATH)))
    if pack_path.exists():
        try:
            return json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    pack = build_pack().model_dump(mode="json")
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    return pack


@dataclass
class State:
    pack: dict[str, Any]
    store: StoreRouter
    npu: Any
    rejected: dict[str, list[str]] = field(default_factory=dict)
    accepted: dict[str, str] = field(default_factory=dict)
    manual: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    actions_done: set[str] = field(default_factory=set)
    alerts_ack: set[str] = field(default_factory=set)
    sharing: dict[str, bool] = field(default_factory=dict)
    loaded: set[str] = field(default_factory=set)
    research_result: dict[str, Any] | None = None
    offline: OfflineQueue = field(default_factory=lambda: OfflineQueue(max_items=500))
    agent: OpenJiuwenRuntime | None = None

    def _key(self, case_id: str) -> str:
        return f"{current_tenant()}::{case_id}"

    def ensure_tenant(self) -> None:
        tenant = current_tenant()
        if tenant in self.loaded:
            return
        self.loaded.add(tenant)
        for cid, decision in self.store.for_tenant(tenant).decisions().items():
            key = f"{tenant}::{cid}"
            if decision["rejected"]:
                self.rejected[key] = decision["rejected"]
            if decision["accepted"]:
                self.accepted[key] = decision["accepted"]
            if decision["manual"]:
                self.manual[key] = decision["manual"]

    def scenario(self, sid: str) -> dict[str, Any]:
        for s in self.pack["scenarios"]:
            if s["id"] == sid:
                return s
        raise HTTPException(404, f"scenario {sid} not found")

    def case_scenario(self, case_id: str) -> dict[str, Any]:
        for s in self.pack["scenarios"]:
            if s["case"]["id"] == case_id:
                return s
        raise HTTPException(404, f"case {case_id} not found")

    def investigations(self) -> dict[str, dict[str, Any]]:
        out = {}
        for s in self.pack["scenarios"]:
            out[s["case"]["id"]] = self.investigation(s)
        return out

    def investigation(self, scenario: dict[str, Any]) -> dict[str, Any]:
        self.ensure_tenant()
        case_id = scenario["case"]["id"]
        key = self._key(case_id)
        scenario_obj = _as_scenario(scenario)
        priors = priors_from_corrections(self.store.corrections(), line_id=scenario["case"]["line_id"])
        apply_priors(scenario_obj.hypotheses, priors)
        result = run_investigation(scenario_obj, rejected=self.rejected.get(key, []))
        accepted = self.accepted.get(key)
        if accepted:
            for h in result["hypotheses"]:
                if h["id"] == accepted:
                    h["status"] = "accepted"
        for m in self.manual.get(key, []):
            result["hypotheses"].append(m)
        result["hypotheses"] = rank_hypotheses([_as_hypothesis(h) for h in result["hypotheses"]], rejected=self.rejected.get(key, []))
        result["hypotheses"] = [h.model_dump(mode="json") for h in result["hypotheses"]]
        result["factors"] = {h["id"]: explain(_as_hypothesis(h)) for h in result["hypotheses"]}
        result["report"] = self.store.get_report(case_id) or scenario["report"]
        result["audits"] = self.store.audits(case_id, limit=50)
        return result


def _as_scenario(data: dict[str, Any]):
    from ..models import Scenario

    return Scenario.model_validate(data)


def _as_hypothesis(data: dict[str, Any]):
    from ..models import Hypothesis

    return Hypothesis.model_validate(data)


def create_state() -> State:
    import os

    pack = load_pack()
    db_path = Path(os.getenv("ROOTCAUSE_DB", str(config.DB_PATH)))
    router = StoreRouter(db_path, pack)
    router.for_tenant(DEFAULT_TENANT)
    rc = State(pack=pack, store=router, npu=broker_from_env())
    rc.agent = OpenJiuwenRuntime([_as_scenario(s) for s in pack["scenarios"]])
    rc.ensure_tenant()
    return rc


async def _scheduler_loop(app: FastAPI) -> None:
    """Optional in-process scheduler. In production, a systemd timer or the site orchestrator may
    call the scan endpoint instead; the state and audit are identical."""
    while True:
        rc = getattr(app.state, "rc", None)
        if rc:
            try:
                settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
                schedule = settings.get("schedule", {})
                interval = max(1, int(schedule.get("interval_minutes", 15)))
                if schedule.get("enabled") and not schedule.get("stop_switch"):
                    existing = [_as_watch(w) for w in rc.store.list_watches()]
                    result = scheduler.run_scan(
                        pack=rc.pack,
                        existing=existing,
                        mode=schedule.get("mode", "shadow"),
                        max_alerts=int(schedule.get("max_alerts_per_shift", 10)),
                        coverage_floor=float(schedule.get("coverage_floor", 0.95)),
                    )
                    run = result["run"]
                    rc.store.save_scan_run(run.model_dump(mode="json") if hasattr(run, "model_dump") else run)
                    for candidate in result["candidates"]:
                        rc.store.save_watch(candidate, actor="scheduler", action="watch.opened", detail=f"Scheduled scan opened {candidate['id']}")
                await asyncio.sleep(interval * 60)
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(60)
        else:
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rc = create_state()
    background = None
    if os.getenv("ROOTCAUSE_SCHEDULER", "0").lower() in {"1", "true", "yes"}:
        background = asyncio.create_task(_scheduler_loop(app))
    yield
    if background:
        background.cancel()
    app.state.rc.store.close()


app = FastAPI(title="RootCause", version="0.9.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    token = set_tenant(request.headers.get("X-RootCause-Tenant"))
    try:
        response = await call_next(request)
        response.headers["X-RootCause-Tenant"] = current_tenant()
        return response
    finally:
        from ..tenancy import tenant_var

        tenant_var.reset(token)


def state(request: Request) -> State:
    return request.app.state.rc


@app.get("/api/health")
def health(request: Request) -> dict[str, Any]:
    rc = state(request)
    return {
        "ok": True,
        "version": "1.0.0",
        "model": config.MODEL_VERSION,
        "scenarios": len(rc.pack["scenarios"]),
        "npu": rc.npu.health(),
        "agent": rc.agent.status().as_dict() if rc.agent else {"configured": False},
        "db": str(config.DB_PATH),
        "tenant": current_tenant(),
        "at": now_iso(),
    }


@app.get("/api/tenants")
def tenants() -> dict[str, Any]:
    """The configured tenants. Each one resolves to a separate SQLite file."""
    import os

    raw = os.getenv("ROOTCAUSE_TENANTS", DEFAULT_TENANT)
    entries = [t.strip().lower() for t in raw.split(",") if t.strip()]
    return {
        "default": DEFAULT_TENANT,
        "tenants": entries or [DEFAULT_TENANT],
        "header": "X-RootCause-Tenant",
        "note": "Every tenant has its own append-only case store; no shared table to leak across.",
    }


@app.get("/api/agent/status")
def agent_status(request: Request) -> dict[str, Any]:
    rc = state(request)
    return rc.agent.status().as_dict() if rc.agent else {"configured": False, "available": False, "backend": "none", "detail": "no runtime"}


@app.post("/api/agent/ask")
async def agent_ask(request: Request) -> dict[str, Any]:
    rc = state(request)
    if not rc.agent or not rc.agent.status().configured:
        detail = rc.agent.status().detail if rc.agent else "agent runtime not initialised"
        raise HTTPException(503, f"JiuwenSwarm runtime is not configured: {detail}")
    body = await request.json()
    question = str(body.get("question", "")).strip()
    if not question:
        raise HTTPException(400, "question is required")
    try:
        result = await rc.agent.ask(question, case_id=body.get("case_id"))
        detail = (
            f"Question: {question[:200]} | model={result.get('model', '')} "
            f"| latency_ms={result.get('latency_ms', '')} | citations={','.join(result.get('citations', []))[:120]}"
        )
        rc.store._audit("agent", "agent.answer", body.get("case_id") or "case", detail)
        rc.store._conn.commit()
        return result
    except Exception as exc:
        raise HTTPException(502, f"agent runtime error: {exc}") from exc


@app.post("/api/agent/case/{case_id}")
async def agent_case(case_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    if not rc.agent or not rc.agent.status().configured:
        detail = rc.agent.status().detail if rc.agent else "agent runtime not initialised"
        raise HTTPException(503, f"JiuwenSwarm runtime is not configured: {detail}")
    rc.case_scenario(case_id)
    try:
        result = await rc.agent.case_narrative(case_id)
        detail = (
            f"Case narrative | model={result.get('model', '')} "
            f"| latency_ms={result.get('latency_ms', '')} | citations={','.join(result.get('citations', []))[:120]}"
        )
        rc.store._audit("agent", "agent.narrative", case_id, detail)
        rc.store._conn.commit()
        return result
    except Exception as exc:
        raise HTTPException(502, f"agent runtime error: {exc}") from exc


@app.get("/api/integrations")
def integrations(request: Request) -> dict[str, Any]:
    rc = state(request)
    connectors = rc.pack["connectors"]
    live_env = {
        "opcua": bool(os.getenv("ROOTCAUSE_OPCUA_ENDPOINT")),
        "modbus": bool(os.getenv("ROOTCAUSE_MODBUS_ENDPOINT")),
        "camera": bool(os.getenv("ROOTCAUSE_CAMERA_HTTP_URL")),
        "mes": bool(os.getenv("ROOTCAUSE_MES_CSV")),
    }
    live_ids = [k for k, v in live_env.items() if v]
    agent = rc.agent.status().as_dict() if rc.agent else {"configured": False}
    npu = rc.npu.health()
    npu_ready = bool(npu.get("ready")) and npu.get("backend") in {"onnx", "ascend"}
    ready = bool(agent.get("configured")) and npu_ready and bool(live_ids)
    return {
        "ready": ready,
        "strict": os.getenv("ROOTCAUSE_STRICT_INTEGRATIONS", "0") == "1",
        "agent": agent,
        "npu": npu,
        "connectors": {
            "total": len(connectors),
            "live": len(live_ids),
            "live_ids": live_ids,
            "simulated": len([c for c in connectors if c["status"] == "simulated"]),
            "available": len([c for c in connectors if c["status"] == "available"]),
            "reference_live": len([c for c in connectors if c["status"] == "connected"]),
            "reference_live_ids": [c["id"] for c in connectors if c["status"] == "connected"],
            "simulated_ids": [c["id"] for c in connectors if c["status"] == "simulated"],
        },
        "scheduler": scheduler.health(rc.store.list_scan_runs(), now=_demo_now(rc.pack)),
        "note": "Production requires the agent model config, a real ONNX/Ascend broker, and at least one configured plant endpoint.",
    }


@app.get("/api/ready")
def ready(request: Request) -> dict[str, Any]:
    rc = state(request)
    agent = rc.agent.status().as_dict() if rc.agent else {"configured": False}
    npu = rc.npu.health()
    npu_ready = bool(npu.get("ready")) and npu.get("backend") in {"onnx", "ascend"}
    live = [k for k in ("ROOTCAUSE_OPCUA_ENDPOINT", "ROOTCAUSE_MODBUS_ENDPOINT", "ROOTCAUSE_CAMERA_HTTP_URL", "ROOTCAUSE_MES_CSV") if os.getenv(k)]
    strict = os.getenv("ROOTCAUSE_STRICT_INTEGRATIONS", "0") == "1"
    data_mode = config.data_mode()
    synthetic_cases = rc.store.synthetic_case_count()
    provenance_ok = not (config.production_data_mode() and synthetic_cases > 0)
    ok = bool(agent.get("configured")) and npu_ready and bool(live) and provenance_ok
    if strict and not ok:
        raise HTTPException(
            503,
            detail={
                "ready": False,
                "agent": agent,
                "npu": npu,
                "live_connectors": live,
                "data_mode": data_mode,
                "synthetic_cases": synthetic_cases,
                "provenance_ok": provenance_ok,
                "note": (
                    "ROOTCAUSE_STRICT_INTEGRATIONS=1: configure the agent, ONNX/Ascend broker and at least one live "
                    "plant connector. A production data mode also requires zero synthetic cases."
                ),
            },
        )
    return {
        "ready": ok,
        "strict": strict,
        "agent": agent,
        "npu": npu,
        "live_connectors": live,
        "data_mode": data_mode,
        "synthetic_cases": synthetic_cases,
        "provenance_ok": provenance_ok,
    }


@app.get("/api/pack")
def get_pack(request: Request) -> dict[str, Any]:
    rc = state(request)
    pack = dict(rc.pack)
    pack["alerts"] = [{**a, "acknowledged": a["id"] in rc.alerts_ack} for a in pack["alerts"]]
    pack["actions"] = [{**a, "status": "done" if a["id"] in rc.actions_done else a["status"]} for a in pack["actions"]]
    pack["sharing"] = {**pack["sharing"], "enabled": rc.sharing.get(current_tenant(), False)}
    pack["audits"] = rc.store.audits(limit=40)
    return pack


@app.get("/api/scenarios")
def scenarios(request: Request) -> list[dict[str, Any]]:
    rc = state(request)
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "subtitle": s["subtitle"],
            "case": s["case"],
            "process": s["process"],
            "defect": s["defect"],
            "part": s["part"],
            "findings": s["findings"],
            "image_keys": s["image_keys"],
            "baseline_hours": s["baseline_hours"],
            "current_hours": s["current_hours"],
        }
        for s in rc.pack["scenarios"]
    ]


@app.get("/api/scenarios/{sid}")
def scenario(sid: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.scenario(sid)
    return {**s, "investigation": rc.investigation(s)}


@app.post("/api/scenarios/{sid}/investigate")
async def investigate(sid: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    rejected = body.get("rejected", [])
    s = rc.scenario(sid)
    rc.rejected[rc._key(s["case"]["id"])] = list(rejected)
    return rc.investigation(s)


@app.get("/api/cases")
def cases(request: Request) -> list[dict[str, Any]]:
    rc = state(request)
    out = []
    for s in rc.pack["scenarios"]:
        inv = rc.investigation(s)
        top = next((h for h in inv["hypotheses"] if h["status"] != "rejected"), None)
        out.append(
            {
                **s["case"],
                "scenario_title": s["title"],
                "top_cause": top["label"] if top else None,
                "top_confidence": top["confidence"] if top else None,
                "report_status": inv["report"]["status"],
                "hours_to_cause": s["current_hours"],
                "baseline_hours": s["baseline_hours"],
            }
        )
    return out


@app.get("/api/cases/{case_id}")
def case(case_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    return {"scenario": s, "investigation": rc.investigation(s)}


@app.post("/api/cases/{case_id}/reject")
def reject(case_id: str, body: RejectRequest, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    rejected = rc.rejected.setdefault(rc._key(case_id), [])
    if body.hypothesis_id not in rejected:
        rejected.append(body.hypothesis_id)
    rc.store.update_hypotheses(
        case_id,
        [h.model_dump(mode="json") for h in rank_hypotheses([_as_hypothesis(h) for h in s["hypotheses"]], rejected=rejected)],
        actor=body.actor,
        action="cause.rejected",
        detail=f"Rejected {body.hypothesis_id}: {body.reason} {body.note}".strip(),
        reason=body.reason,
        hid=body.hypothesis_id,
    )
    return rc.investigation(s)


@app.post("/api/cases/{case_id}/accept")
def accept(case_id: str, body: AcceptRequest, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    if not any(h["id"] == body.hypothesis_id for h in s["hypotheses"]):
        raise HTTPException(404, "hypothesis not found")
    rc.accepted[rc._key(case_id)] = body.hypothesis_id
    label = next(h["label"] for h in s["hypotheses"] if h["id"] == body.hypothesis_id)
    rc.store.set_status(case_id, "awaiting_review", actor=body.actor, detail=f"Accepted cause: {label}. {body.note}".strip())
    rc.store.update_hypotheses(
        case_id,
        [h.model_dump(mode="json") for h in rank_hypotheses([_as_hypothesis(h) for h in s["hypotheses"]], rejected=rc.rejected.get(rc._key(case_id), []))],
        actor=body.actor,
        action="cause.accepted",
        detail=f"Accepted {label}: {body.note}".strip(),
        hid=body.hypothesis_id,
    )
    return rc.investigation(s)


@app.post("/api/cases/{case_id}/manual")
def manual_cause(case_id: str, body: ManualCauseRequest, request: Request) -> dict[str, Any]:
    from ..models import Hypothesis, HypothesisFactor

    rc = state(request)
    s = rc.case_scenario(case_id)
    manual = Hypothesis(
        id=f"manual-{len(rc.manual.get(rc._key(case_id), [])) + 1}",
        label=body.label,
        category="manual",
        summary=body.summary,
        score=0.34,
        confidence=0.0,
        rank=99,
        status="manual",
        factors=HypothesisFactor(frequency=0.5, deviation=0.5, batch_match=0.5, similarity=0.5, recurrence=0.5),
        evidence_ids=body.evidence_ids,
        note="Added by the engineer during review.",
    )
    rc.manual.setdefault(rc._key(case_id), []).append(manual.model_dump(mode="json"))
    rc.store.update_hypotheses(
        case_id,
        [manual.model_dump(mode="json")],
        actor=body.actor,
        action="cause.manual",
        detail=f"Engineer added manual cause: {body.label}",
        reason=body.summary,
        hid=manual.id,
    )
    return rc.investigation(s)


@app.post("/api/cases/{case_id}/approve")
def approve(case_id: str, body: ApprovalRequest, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    updated = rc.store.approve(case_id, actor=body.actor, scope=body.scope, note=body.note)
    existing = {f["case_id"] for f in rc.store.list_followups()}
    if case_id not in existing:
        action = next((a for a in rc.pack["actions"] if a["case_id"] == case_id and a["status"] != "done"), None)
        if action:
            watch = next((w for w in rc.store.list_watches() if w.get("linked_case_id") == case_id), None)
            follow = containment.followup_for(
                followup_id=f"FU-{case_id.split('-')[-1]}",
                case_id=case_id,
                action_id=action["id"],
                title=action["title"],
                now=datetime.now().astimezone(),
                days=30,
                watch_id=watch["id"] if watch else None,
            )
            rc.store.save_followup(follow.model_dump(mode="json"), actor=body.actor, detail="Post-fix monitoring window opened")
    return {"case": updated, "investigation": rc.investigation(s)}


@app.patch("/api/reports/{case_id}")
def patch_report(case_id: str, body: ReportPatch, request: Request) -> dict[str, Any]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    current = rc.store.get_report(case_id) or s["report"]
    report = Report.model_validate(current)
    if body.title:
        report.title = body.title
    if body.summary:
        report.summary = body.summary
    if body.sections is not None:
        report.sections = body.sections
    report.version += 1
    report.edits += 1
    report.status = "in_review"
    rc.store.save_report(case_id, report.model_dump(mode="json"), actor=body.actor, action="report.edited", detail=f"Report v{report.version} edited")
    return {"report": report.model_dump(mode="json"), "audits": rc.store.audits(case_id)}


def _report_bundle(case_id: str, request: Request) -> tuple[State, dict[str, Any], Report, list[Evidence]]:
    rc = state(request)
    s = rc.case_scenario(case_id)
    current = rc.store.get_report(case_id) or s["report"]
    report = Report.model_validate(current)
    evidence = [Evidence.model_validate(e) for e in s["evidence"]]
    return rc, s, report, evidence


@app.get("/api/reports/{case_id}")
def get_report(case_id: str, request: Request) -> dict[str, Any]:
    rc, s, report, _ = _report_bundle(case_id, request)
    return {"report": report.model_dump(mode="json"), "versions": rc.store.report_versions(report.id)}


@app.get("/api/reports/{case_id}/html", response_class=HTMLResponse)
def export_html(case_id: str, request: Request, printable: bool = True) -> str:
    rc, s, report, evidence = _report_bundle(case_id, request)
    from ..models import AuditEvent

    return report_html(
        report,
        evidence=evidence,
        audits=[AuditEvent.model_validate(a) for a in rc.store.audits(case_id)],
        printable=printable,
    )


@app.get("/api/reports/{case_id}/markdown", response_class=PlainTextResponse)
def export_md(case_id: str, request: Request) -> str:
    rc, s, report, evidence = _report_bundle(case_id, request)
    from ..models import AuditEvent

    return report_markdown(
        report,
        evidence=evidence,
        audits=[AuditEvent.model_validate(a) for a in rc.store.audits(case_id)],
    )


@app.get("/api/reports/{case_id}/pdf")
def export_pdf(case_id: str, request: Request) -> Response:
    rc, s, report, evidence = _report_bundle(case_id, request)
    data = report_pdf(report, evidence=evidence)
    if data is None:
        raise HTTPException(501, "PDF exporter unavailable; install the 'pdf' extra or use the HTML print view")
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{report.id}.pdf"'})


@app.get("/api/reports/{case_id}/docx")
def export_docx(case_id: str, request: Request) -> Response:
    rc, s, report, evidence = _report_bundle(case_id, request)
    data = report_docx(report, evidence=evidence)
    if data is None:
        data = report_rtf(report, evidence=evidence)
        return Response(data, media_type="application/rtf", headers={"Content-Disposition": f'attachment; filename="{report.id}.rtf"'})
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{report.id}.docx"'},
    )


@app.get("/api/audits")
def audits(request: Request, object_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return state(request).store.audits(object_id, limit=limit)


@app.get("/api/corrections")
def corrections(request: Request, case_id: str | None = None) -> list[dict[str, Any]]:
    return state(request).store.corrections(case_id)


@app.get("/api/dashboard")
def dashboard(request: Request) -> dict[str, Any]:
    rc = state(request)
    pack = rc.pack
    actions = [{**a, "status": "done" if a["id"] in rc.actions_done else a["status"]} for a in pack["actions"]]
    alerts = trend_alerts(defect_series(pack), sigma=1.8)
    return {
        "kpis": pack["dashboard"],
        "alerts": [{**a, "acknowledged": a["id"] in rc.alerts_ack} for a in pack["alerts"]],
        "trend_alerts": alerts,
        "actions": actions,
        "savings": savings_from_actions([_as_action(a) for a in actions]),
        "pilot": pilot_summary(pack, rc.store.metrics()),
        "top_causes": top_causes([_as_scenario(s) for s in pack["scenarios"]]),
        "patterns": cross_line_patterns([_as_scenario(s) for s in pack["scenarios"]]),
        "baselines": rc.store.baselines(),
    }


def _as_action(a: dict[str, Any]):
    from ..models import CorrectiveAction

    return CorrectiveAction.model_validate(a)


@app.post("/api/alerts/{alert_id}/ack")
def ack_alert(alert_id: str, request: Request) -> dict[str, Any]:
    state(request).alerts_ack.add(alert_id)
    return {"id": alert_id, "acknowledged": True}


@app.patch("/api/actions/{action_id}")
def update_action(action_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    rc.actions_done.add(action_id)
    return {"id": action_id, "status": "done"}


@app.post("/api/baselines")
async def set_baseline(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    line_id = body.get("line_id")
    hours = float(body.get("baseline_hours", 0))
    if not line_id or hours <= 0:
        raise HTTPException(400, "line_id and a positive baseline_hours are required")
    rc.store.set_baseline(line_id, hours)
    return {"line_id": line_id, "baseline_hours": hours}


@app.get("/api/connectors")
def connectors(request: Request) -> dict[str, Any]:
    rc = state(request)
    return {"connectors": rc.pack["connectors"], "library": connector_catalog(), "npu": rc.npu.health()}


@app.post("/api/connectors/{connector_id}/test")
def test_connector(connector_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    entry = next((c for c in rc.pack["connectors"] if c["id"] == connector_id), None)
    if not entry:
        raise HTTPException(404, "connector not found")
    proto = entry["protocol"]
    if proto == "OPC-UA":
        result = OpcUaConnector(entry.get("endpoint", ""), simulate=True).test()
    elif proto == "Modbus":
        result = ModbusConnector(entry.get("endpoint", ""), simulate=True).test()
    elif proto == "REST":
        result = CmmsConnector(entry.get("endpoint", ""), simulate=True).test()
    else:
        result = OpcUaConnector(entry.get("endpoint", ""), simulate=True).test()
    return {
        "connector": entry,
        "result": result.as_dict(),
        "note": "No hardware is attached to the public demo, so the handshake is simulated. The same adapter reads live tags when an endpoint is configured.",
    }


@app.get("/api/npu/health")
def npu_health(request: Request) -> dict[str, Any]:
    return state(request).npu.health()


@app.post("/api/detect")
async def detect_image(request: Request, file: Annotated[UploadFile, File()], label: str = "defect") -> dict[str, Any]:
    rc = state(request)
    tmp = config.RUNTIME_DIR / f"upload-{now_iso().replace(':', '-')}-{file.filename or 'frame.png'}"
    tmp.write_bytes(await file.read())
    try:
        result = rc.npu.infer(tmp, label=label)
    finally:
        tmp.unlink(missing_ok=True)
    return {"detection": result.as_dict(), "source": "upload", "note": "Image processed on site and not retained."}


@app.post("/api/investigate/new")
async def investigate_new(request: Request, file: Annotated[UploadFile, File()], scenario_id: str = "bracket") -> dict[str, Any]:
    """Mobile path: a photo of a defect starts an investigation."""
    rc = state(request)
    s = rc.scenario(scenario_id)
    tmp = config.RUNTIME_DIR / f"mobile-{now_iso().replace(':', '-')}-{file.filename or 'photo.png'}"
    tmp.write_bytes(await file.read())
    try:
        det = rc.npu.infer(tmp, label=s["defect"])
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "created": True,
        "case_id": s["case"]["id"],
        "detection": det.as_dict(),
        "scenario": s["id"],
        "note": "Mobile capture is treated as a new observation on the existing demo case. No image leaves the site.",
    }


@app.get("/api/compliance/{pack_id}")
def get_compliance(pack_id: str, request: Request) -> dict[str, Any]:
    data = compliance_export(state(request).pack, pack_id)
    if not data:
        raise HTTPException(404, "compliance pack not found")
    return data


@app.get("/api/sharing")
def get_sharing(request: Request) -> dict[str, Any]:
    rc = state(request)
    return anonymised_sharing_payload([_as_scenario(s) for s in rc.pack["scenarios"]], enabled=rc.sharing.get(current_tenant(), False))


@app.post("/api/sharing")
async def set_sharing(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    rc.sharing[current_tenant()] = bool(body.get("enabled", False))
    return anonymised_sharing_payload([_as_scenario(s) for s in rc.pack["scenarios"]], enabled=rc.sharing[current_tenant()])


@app.get("/api/proactive")
def proactive(request: Request) -> dict[str, Any]:
    rc = state(request)
    data = rc.pack["proactive"]
    settings = rc.store.proactive_settings() or data["settings"]
    reviews = {r.get("pattern_id"): r.get("status") for r in settings.get("pattern_reviews", [])}
    patterns = [{**p, "status": reviews.get(p["id"], p["status"])} for p in data["patterns"]]
    watches = rc.store.list_watches()
    watch_objs = []
    for w in watches:
        try:
            watch_objs.append(_as_watch(w))
        except Exception:
            continue
    followups = rc.store.list_followups()
    metrics = proactive_metrics.compute_metrics(rc.pack, watch_objs, coverage=data["coverage"])
    metrics.update(proactive_metrics.alert_fatigue(watch_objs))
    metrics["coverage"] = proactive_metrics.coverage_status(data["coverage"], floor=settings.get("schedule", {}).get("coverage_floor", 0.95))
    metrics["followups"] = proactive_metrics.followup_effectiveness([_as_followup(f) for f in followups])
    metrics["store"] = rc.store.proactive_counts()
    return {
        "settings": settings,
        "watches": watches,
        "patterns": patterns,
        "recommendations": rc.store.list_recommendations(),
        "scan_runs": rc.store.list_scan_runs(),
        "briefs": data["briefs"],
        "notifications": rc.store.list_notifications(),
        "exposures": rc.store.list_exposures() or data["exposures"],
        "followups": followups or data["followups"],
        "coverage": data["coverage"],
        "metrics": metrics,
        "model_cards": data["model_cards"],
        "research": rc.research_result or data["research"],
        "health": scheduler.health(rc.store.list_scan_runs(), now=_demo_now(rc.pack), interval_minutes=int(settings.get("schedule", {}).get("interval_minutes", 15))),
        "replay": scheduler.replay(rc.pack),
        "tuning": proactive_metrics.threshold_tuning(watch_objs),
        "queue": rc.offline.summary(),
    }


def _demo_now(pack: dict[str, Any]) -> datetime:
    anchor = pack.get("meta", {}).get("anchor")
    if anchor:
        try:
            return datetime.fromisoformat(anchor.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now().astimezone()


def _as_watch(data: dict[str, Any]):
    from ..models import WatchCase

    return WatchCase.model_validate(data)


def _as_rec(data: dict[str, Any]):
    from ..models import Recommendation

    return Recommendation.model_validate(data)


def _as_followup(data: dict[str, Any]):
    from ..models import FollowUp

    return FollowUp.model_validate(data)


def _watch_or_404(rc: State, watch_id: str):
    watch = rc.store.get_watch(watch_id)
    if not watch:
        raise HTTPException(404, f"watch {watch_id} not found")
    return _as_watch(watch)


@app.post("/api/proactive/near-miss")
async def near_miss(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    now = datetime.now().astimezone()
    note = sanitize_note(body.get("note", "Operator reported an unusual condition with no defective part."))
    signal = RiskSignal(
        id=f"NM-{now.strftime('%Y%m%d%H%M%S')}",
        kind="near_miss",
        at=now.replace(microsecond=0).isoformat(),
        line_id=body.get("line_id", "line-6"),
        parameter=body.get("parameter", "Operator observation"),
        severity=body.get("severity", "warning"),
        detail=note,
    )
    pattern = next((p for p in rc.pack["proactive"]["patterns"] if p["id"] == "P-SEAL"), rc.pack["proactive"]["patterns"][0])
    watch = watch_engine.build_watch(
        watch_id=f"W-NM-{now.strftime('%H%M%S')}",
        signals=[signal],
        pattern=pattern,
        owner=body.get("actor", "M. Weber"),
        now=now,
    )
    rc.store.save_watch(watch.model_dump(mode="json"), actor=body.get("actor", "M. Weber"), action="watch.near_miss", detail=note)
    return watch.model_dump(mode="json")


@app.post("/api/proactive/scan")
async def proactive_scan(request: Request) -> dict[str, Any]:
    rc = state(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    data = rc.pack["proactive"]
    settings = rc.store.proactive_settings() or data["settings"]
    if settings.get("schedule", {}).get("stop_switch"):
        raise HTTPException(409, "proactive scanning is stopped; start it before scanning")
    existing = [_as_watch(w) for w in rc.store.list_watches()]
    result = scheduler.run_scan(
        pack=rc.pack,
        existing=existing,
        mode=body.get("mode", settings.get("schedule", {}).get("mode", "shadow")),
        owner=body.get("owner", "M. Weber"),
        max_alerts=int(settings.get("schedule", {}).get("max_alerts_per_shift", 10)),
        coverage_floor=float(settings.get("schedule", {}).get("coverage_floor", 0.95)),
    )
    run = result["run"]
    run_data = run.model_dump(mode="json") if hasattr(run, "model_dump") else run
    rc.store.save_scan_run(run_data)
    for record in result.get("laix", {}).get("decisions", []):
        rc.store._audit("laix", "laix.decision", str(record.get("signal_id", "")), json.dumps(record))
    rc.store._conn.commit()
    for candidate in result["candidates"]:
        w = _as_watch(candidate)
        rc.store.save_watch(candidate, actor="scheduler", action="watch.opened", detail=f"Open watch {w.id}: {w.title}")
        notification = notify.build_notification(
            notification_id=f"NT-{w.id}",
            watch=w,
            kind="watch",
            severity=w.severity,
            title=f"New watch: {w.title}",
            detail=w.summary,
            now=datetime.now().astimezone(),
            role="quality_manager",
        )
        quiet = notify.in_quiet_hours(
            datetime.now().astimezone(),
            settings.get("schedule", {}).get("quiet_hours", "22:00-06:00"),
        ) and w.severity not in {"critical", "high"}
        if quiet:
            notification.delivered = False
            notification.detail += " Held for the quiet-hours digest."
        if not notify.dedupe(rc.store.list_notifications(), notification):
            rc.store._conn.execute(
                "INSERT OR IGNORE INTO notifications(id, at, payload, read) VALUES (?,?,?,0)",
                (notification.id, notification.at, json.dumps(notification.model_dump(mode="json"))),
            )
            rc.store._conn.commit()
            notify.deliver_webhook(
                settings.get("schedule", {}).get("webhook_url", ""),
                notification.model_dump(mode="json"),
                secret=settings.get("schedule", {}).get("webhook_secret", ""),
            )
    reopened = containment.recurrence_guard(
        [_as_followup(f) for f in rc.store.list_followups()],
        [_as_watch(w) for w in rc.store.list_watches()],
    )
    for follow in reopened:
        rc.store.save_followup(follow.model_dump(mode="json"), actor="scheduler", detail="Recurrence guard reopened the follow-up")
    return {
        "run": run_data,
        "signals": result["signals"],
        "opened": result["candidates"],
        "watchlist": rc.store.list_watches(),
        "reopened": [f.model_dump(mode="json") for f in reopened],
        "laix": result.get("laix", {"enabled": False, "decisions": []}),
    }


@app.get("/api/watch/{watch_id}")
def watch_detail(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    watch = _watch_or_404(rc, watch_id)
    data = rc.pack["proactive"]
    pattern = next((p for p in data["patterns"] if p["id"] == watch.pattern_id), None)
    card = next((c for c in data["model_cards"] if c["id"].lower().find(watch.pattern_id.lower().replace("p-", "")) >= 0), None)
    recs = [r for r in rc.store.list_recommendations(watch_id)]
    exposure = rc.store.get_exposure(watch_id) or next((e for e in data["exposures"] if e["watch_id"] == watch_id), None)
    linked = None
    if watch.linked_case_id:
        linked = next((s["case"] for s in rc.pack["scenarios"] if s["case"]["id"] == watch.linked_case_id), None)
    return {
        "watch": watch.model_dump(),
        "pattern": pattern,
        "model_card": card,
        "recommendations": recs,
        "exposure": exposure,
        "linked_case": linked,
        "audits": rc.store.audits(watch_id, limit=30),
        "notifications": [n for n in rc.store.list_notifications() if n.get("watch_id") == watch_id],
    }


@app.post("/api/watch/{watch_id}/triage")
async def watch_triage(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watch = _watch_or_404(rc, watch_id)
    watch = watch_engine.triage(watch, actor=body.get("actor", "M. Weber"), note=body.get("note", ""), now=datetime.now().astimezone())
    rc.store.save_watch(watch.model_dump(mode="json"), actor=body.get("actor", "M. Weber"), action="watch.triage", detail=body.get("note", "Triage started"))
    return watch.model_dump()


@app.post("/api/watch/{watch_id}/snooze")
async def watch_snooze(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watch = _watch_or_404(rc, watch_id)
    hours = int(body.get("hours", 4))
    watch = watch_engine.snooze(watch, hours=hours, actor=body.get("actor", "M. Weber"))
    rc.store.save_watch(watch.model_dump(mode="json"), actor=body.get("actor", "M. Weber"), action="watch.snoozed", detail=f"Snoozed {hours} h")
    return watch.model_dump()


@app.post("/api/watch/{watch_id}/dismiss")
async def watch_dismiss(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watch = _watch_or_404(rc, watch_id)
    actor = body.get("actor", "M. Weber")
    watch = watch_engine.dismiss(
        watch, actor=actor, reason=body.get("reason", "Dismissed by engineer"),
        now=datetime.now().astimezone(), operational=bool(body.get("operational", False)),
    )
    rc.store.add_watch_outcome(watch.model_dump(mode="json"), actor=actor, outcome=watch.outcome, reason=watch.outcome_reason)
    return watch.model_dump()


@app.post("/api/watch/{watch_id}/convert")
async def watch_convert(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watch = _watch_or_404(rc, watch_id)
    actor = body.get("actor", "M. Weber")
    case_id = body.get("case_id") or watch.linked_case_id
    if not case_id:
        raise HTTPException(400, "case_id is required to convert a watch")
    if not any(s["case"]["id"] == case_id for s in rc.pack["scenarios"]):
        raise HTTPException(404, f"case {case_id} not found")
    watch = watch_engine.convert(watch, case_id=case_id, actor=actor, reason=body.get("reason", "Risk converted to a defect case"), now=datetime.now().astimezone())
    rc.store.add_watch_outcome(watch.model_dump(mode="json"), actor=actor, outcome="converted", reason=watch.outcome_reason)
    return watch.model_dump()


@app.post("/api/watch/{watch_id}/true-risk")
async def watch_true_risk(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watch = _watch_or_404(rc, watch_id)
    actor = body.get("actor", "M. Weber")
    watch = watch_engine.true_risk(watch, actor=actor, reason=body.get("reason", "Confirmed risk"), now=datetime.now().astimezone())
    rc.store.save_watch(watch.model_dump(mode="json"), actor=actor, action="watch.true_risk", detail=watch.outcome_reason)
    return watch.model_dump()


@app.post("/api/watch/{watch_id}/checks/{check_id}")
def watch_check(watch_id: str, check_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    watch = _watch_or_404(rc, watch_id)
    done = False
    for check in watch.suggested_checks:
        if check.id == check_id:
            check.done = True
            done = True
    if not done:
        raise HTTPException(404, "check not found")
    rc.store.save_watch(watch.model_dump(mode="json"), actor="M. Weber", action="watch.check", detail=f"Completed check {check_id}")
    return watch.model_dump()


@app.post("/api/recommendations/{rec_id}/{action}")
async def recommendation_action(rec_id: str, action: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    rec_data = next((r for r in rc.store.list_recommendations() if r["id"] == rec_id), None)
    if not rec_data:
        raise HTTPException(404, "recommendation not found")
    rec = _as_rec(rec_data)
    actor = body.get("actor", "M. Weber")
    now = datetime.now().astimezone()
    if action == "approve":
        rec = containment.approve(rec, actor=actor, now=now)
    elif action == "reject":
        rec = containment.reject(rec, actor=actor, reason=body.get("reason", "Rejected by engineer"), now=now)
    elif action == "execute":
        if rec.status != "approved":
            raise HTTPException(409, "approve the recommendation before executing it")
        rec = containment.execute(rec, actor=actor, now=now)
    elif action == "verify":
        rec = containment.verify(rec, actor=actor, note=body.get("note", "Verified"), now=now)
    else:
        raise HTTPException(400, "unknown recommendation action")
    rc.store.save_recommendation(rec.model_dump(mode="json"), actor=actor, action=f"recommendation.{action}", detail=f"{rec.title}: {rec.reason}".strip())
    watch = rc.store.get_watch(rec.watch_id)
    if watch:
        rc.store.save_watch(watch, actor=actor, action="watch.recommendation", detail=f"{action}: {rec.title}")
    return rec.model_dump()


@app.post("/api/recommendations/{rec_id}/corrective-draft")
def recommendation_corrective(rec_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    rec_data = next((r for r in rc.store.list_recommendations() if r["id"] == rec_id), None)
    if not rec_data:
        raise HTTPException(404, "recommendation not found")
    rec = _as_rec(rec_data)
    watch = _watch_or_404(rc, rec.watch_id)
    return containment.corrective_draft(watch, rec)


@app.post("/api/recommendations/{rec_id}/supplier-notice")
def recommendation_supplier(rec_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    rec_data = next((r for r in rc.store.list_recommendations() if r["id"] == rec_id), None)
    if not rec_data:
        raise HTTPException(404, "recommendation not found")
    rec = _as_rec(rec_data)
    watch = _watch_or_404(rc, rec.watch_id)
    exposure = next((e for e in rc.pack["proactive"]["exposures"] if e["watch_id"] == watch.id), None)
    batch = exposure["batch_id"] if exposure else watch.linked_case_id or "unknown"
    return {"notice": containment.supplier_notice(watch, batch, rec), "batch_id": batch}


@app.get("/api/exposures/{watch_id}")
def get_exposure(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    exposure = rc.store.get_exposure(watch_id) or next((e for e in rc.pack["proactive"]["exposures"] if e["watch_id"] == watch_id), None)
    if not exposure:
        raise HTTPException(404, "no exposure recorded for this watch")
    return exposure


@app.post("/api/exposures/{watch_id}/release")
async def release_exposure(watch_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    exposure = rc.store.get_exposure(watch_id) or next((e for e in rc.pack["proactive"]["exposures"] if e["watch_id"] == watch_id), None)
    if not exposure:
        raise HTTPException(404, "no exposure recorded for this watch")
    status = body.get("status", "contained")
    if status not in {"open", "contained", "released"}:
        raise HTTPException(400, "status must be open, contained or released")
    exposure["status"] = status
    for part in exposure["parts"]:
        if status == "released":
            part["containment"] = "release"
    rc.store.save_exposure(exposure, actor=body.get("actor", "M. Weber"), detail=f"{status}: {body.get('note', '')}")
    return exposure


@app.get("/api/exposures/{watch_id}/export.csv")
def export_exposure(watch_id: str, request: Request) -> Response:
    rc = state(request)
    exposure = rc.store.get_exposure(watch_id) or next((e for e in rc.pack["proactive"]["exposures"] if e["watch_id"] == watch_id), None)
    if not exposure:
        raise HTTPException(404, "no exposure recorded for this watch")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["serial", "part", "line", "shift", "customer", "status", "containment"])
    for p in exposure["parts"]:
        writer.writerow([p["serial"], p["part"], p["line_id"], p["shift"], p["customer"], p["status"], p["containment"]])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={watch_id}-exposure.csv"})


@app.get("/api/briefs")
def get_briefs(request: Request) -> list[dict[str, Any]]:
    return state(request).pack["proactive"]["briefs"]


@app.post("/api/briefs/generate")
async def generate_brief(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    watches = [_as_watch(w) for w in rc.store.list_watches()]
    followups = rc.store.list_followups() or rc.pack["proactive"]["followups"]
    brief = brief_engine.build_brief(
        brief_id=f"BRIEF-{datetime.now().strftime('%Y%m%d%H%M')}",
        watches=watches,
        cases=rc.store.list_cases(),
        actions=rc.pack["actions"],
        followups=followups,
        coverage=rc.pack["proactive"]["coverage"],
        lines=body.get("line_ids", ["line-6", "line-2", "line-4", "line-3"]),
        shift=body.get("shift", "B"),
        now=datetime.now().astimezone(),
    )
    return {"brief": brief.model_dump(mode="json"), "markdown": brief_engine.render_brief_markdown(brief)}


@app.get("/api/notifications")
def get_notifications(request: Request, unread_only: bool = False) -> list[dict[str, Any]]:
    return state(request).store.list_notifications(unread_only=unread_only)


@app.post("/api/notifications/{notification_id}/read")
def read_notification(notification_id: str, request: Request) -> dict[str, Any]:
    state(request).store.mark_notification(notification_id, True)
    return {"id": notification_id, "read": True}


@app.post("/api/notifications/read-all")
def read_all_notifications(request: Request) -> dict[str, Any]:
    store = state(request).store
    for n in store.list_notifications(unread_only=True):
        store.mark_notification(n["id"], True)
    return {"read": True}


@app.get("/api/proactive/metrics")
def get_proactive_metrics(request: Request) -> dict[str, Any]:
    return proactive(request)["metrics"]


@app.get("/api/proactive/coverage")
def get_coverage(request: Request) -> list[dict[str, Any]]:
    return state(request).pack["proactive"]["coverage"]


@app.get("/api/proactive/health")
def get_health(request: Request) -> dict[str, Any]:
    rc = state(request)
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    health = scheduler.health(rc.store.list_scan_runs(), now=_demo_now(rc.pack), interval_minutes=int(settings.get("schedule", {}).get("interval_minutes", 15)))
    health["queue"] = rc.offline.summary()
    return health


@app.get("/api/proactive/replay")
def get_replay(request: Request) -> dict[str, Any]:
    return scheduler.replay(state(request).pack)


@app.post("/api/proactive/settings")
async def save_settings(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    current = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    if "schedule" in body:
        current["schedule"] = {**current.get("schedule", {}), **body["schedule"]}
    if "thresholds" in body:
        current["thresholds"] = body["thresholds"]
    rc.store.save_proactive_settings(current, actor=body.get("actor", "Site Admin"), detail="Proactive settings updated")
    return current


@app.post("/api/proactive/thresholds/{threshold_id}")
async def update_threshold(threshold_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    found = None
    for rule in settings.get("thresholds", []):
        if rule["id"] == threshold_id:
            rule.update({k: body[k] for k in ("limit", "direction", "active", "notes", "version") if k in body})
            rule["version"] = body.get("version", rule.get("version", "v1"))
            found = rule
    if not found:
        raise HTTPException(404, "threshold not found")
    rc.store.save_proactive_settings(settings, actor=body.get("actor", "Site Admin"), detail=f"Threshold {threshold_id} updated; requires engineer sign-off")
    return found


@app.post("/api/proactive/patterns/{pattern_id}")
async def review_pattern(pattern_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    pattern = next((p for p in rc.pack["proactive"]["patterns"] if p["id"] == pattern_id), None)
    if not pattern:
        raise HTTPException(404, "pattern not found")
    status = body.get("status", pattern["status"])
    if status not in {"active", "shadow", "retired"}:
        raise HTTPException(400, "status must be active, shadow or retired")
    pattern["status"] = status
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    settings.setdefault("pattern_reviews", []).append(
        {
            "at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
            "pattern_id": pattern_id,
            "status": status,
            "actor": body.get("actor", "Quality manager"),
            "note": body.get("note", ""),
        }
    )
    rc.store.save_proactive_settings(settings, actor=body.get("actor", "Quality manager"), detail=f"Pattern {pattern_id} set to {status}")
    return pattern


@app.post("/api/proactive/stop")
async def stop_proactive(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    settings["schedule"]["stop_switch"] = True
    settings["schedule"]["enabled"] = False
    reason = body.get("reason", "Stopped by site admin")
    settings.setdefault("stop_reasons", []).append(f"{datetime.now().isoformat()}: {reason}")
    rc.store.save_proactive_settings(settings, actor=body.get("actor", "Site Admin"), detail=f"Proactive scanning stopped: {reason}")
    return settings["schedule"]


@app.post("/api/proactive/start")
def start_proactive(request: Request) -> dict[str, Any]:
    rc = state(request)
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    settings["schedule"]["stop_switch"] = False
    settings["schedule"]["enabled"] = True
    rc.store.save_proactive_settings(settings, actor="Site Admin", detail="Proactive scanning started")
    return settings["schedule"]


@app.post("/api/proactive/webhook/test")
async def test_webhook(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    settings = rc.store.proactive_settings() or rc.pack["proactive"]["settings"]
    url = body.get("url") or settings.get("schedule", {}).get("webhook_url", "")
    return {"url": url, "result": notify.deliver_webhook(url, {"event": "rootcause.test", "site": "werk-sued"}, secret=body.get("secret", ""))}


@app.get("/api/proactive/research")
def get_research(request: Request) -> dict[str, Any]:
    rc = state(request)
    return rc.research_result or rc.pack["proactive"]["research"]


@app.post("/api/proactive/research/run")
def run_research(request: Request) -> dict[str, Any]:
    rc = state(request)
    y, baseline, model, _ = predictive.synthetic_events()
    result = predictive.run(
        rc.pack["proactive"]["research"]["question"], y, baseline, model, 14, 34, 8.0
    )
    merged = {**rc.pack["proactive"]["research"], **result.as_dict(), "model_lift": result.lift}
    rc.research_result = merged
    return merged


@app.post("/api/followups/{followup_id}/verify")
async def verify_followup(followup_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    rows = rc.store.list_followups()
    row = next((f for f in rows if f["id"] == followup_id), None)
    if not row:
        raise HTTPException(404, "follow-up not found")
    follow = containment.effectiveness(
        _as_followup(row),
        parameter_returned=bool(body.get("parameter_returned", False)),
        defect_rate_delta=float(body.get("defect_rate_delta", 0)),
        recurrence_watch_id=body.get("recurrence_watch_id"),
    )
    rc.store.save_followup(follow.model_dump(mode="json"), actor=body.get("actor", "M. Weber"), detail=follow.note)
    return follow.model_dump(mode="json")


@app.get("/api/export/cases.csv")
def export_cases(request: Request) -> Response:
    rc = state(request)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["case_id", "line", "part", "defect", "detected_at", "status", "top_cause", "confidence", "hours_to_cause"])
    for s in rc.pack["scenarios"]:
        inv = rc.investigation(s)
        top = next((h for h in inv["hypotheses"] if h["status"] != "rejected"), None)
        writer.writerow([
            s["case"]["id"], s["case"]["line_id"], s["case"]["part"], s["case"]["defect_type"],
            s["case"]["detected_at"], inv["report"]["status"], top["label"] if top else "",
            top["confidence"] if top else "", s["current_hours"],
        ])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=rootcause-cases.csv"})


@app.get("/api/normalise/example")
def normalise_example() -> dict[str, Any]:
    return normalise_frame({"TAG_01": "712.4", "TAG_02": "bad", "TAG_03": 58.2}, {"TAG_01": "pour_temp", "TAG_03": "quench_temp"}, units={"pour_temp": "C", "quench_temp": "C"})


def run() -> None:
    import uvicorn

    uvicorn.run("rootcause.api.app:app", host="127.0.0.1", port=8000, reload=False)


@app.get("/api/laix/decisions")
def laix_decisions(request: Request, limit: int = 50) -> dict[str, Any]:
    rc = state(request)
    decisions: list[dict[str, Any]] = []
    for row in rc.store.audits(limit=500):
        if row["action"] != "laix.decision":
            continue
        try:
            decisions.append(json.loads(row["detail"]))
        except (TypeError, ValueError):
            continue
        if len(decisions) >= max(1, limit):
            break
    return {"count": len(decisions), "decisions": decisions}


@app.get("/api/laix/status")
def laix_status() -> dict[str, Any]:
    return {
        "policy": "quality-intervention.v1",
        "enabled": os.getenv("ROOTCAUSE_LAIX", "0").lower() in {"1", "true", "yes"},
        "components": ["intervention", "outcome"],
        "actions": ["wait", "ask", "guide", "act", "verify", "escalate"],
        "note": (
            "Portable decision layer. It reads signals, state and constraints; it does not approve a "
            "cause, control a line or call a model."
        ),
    }


@app.post("/api/laix/decide")
async def laix_decide(request: Request) -> dict[str, Any]:
    body = await request.json()
    try:
        signal = LaixSignal(**body["signal"])
        state = LaixState(**body["state"])
        constraints = LaixConstraints(**body.get("constraints", {}))
    except (KeyError, TypeError) as exc:
        raise HTTPException(400, f"invalid LAIX input: {exc}") from exc
    policy = QualityInterventionPolicy()
    decision = policy.decide(signal, state, constraints)
    record = policy.record(decision, signal, state, constraints, actor=str(body.get("actor", "api")))
    return {"decision": decision.as_dict(), "record": record.as_dict()}


@app.post("/api/laix/outcome")
async def laix_outcome(request: Request) -> dict[str, Any]:
    body = await request.json()
    action_id = body.get("action_id")
    if not action_id:
        raise HTTPException(400, "action_id is required")
    try:
        followups = [LaixFollowUp(**row) for row in body.get("followups", [])]
    except TypeError as exc:
        raise HTTPException(400, f"invalid follow-up: {exc}") from exc
    outcome = estimate_outcome(
        str(action_id),
        str(body.get("action", "action")),
        followups,
        float(body.get("baseline_rate", 0.0)),
        window_days=int(body.get("window_days", 30)),
    )
    return outcome.as_dict()

@app.get("/api/laix/actions")
def laix_actions(request: Request) -> dict[str, Any]:
    rc = state(request)
    actions = rc.store.list_laix_actions()
    return {"count": len(actions), "actions": actions}


@app.post("/api/laix/actions")
async def laix_record_action(request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    action_name = body.get("action")
    if not action_name:
        raise HTTPException(400, "action is required")
    record = {
        "id": str(body.get("id") or f"ACT-{uuid.uuid4().hex[:12]}"),
        "at": str(body.get("at") or now_iso()),
        "action": str(action_name),
        "case_id": str(body.get("case_id", "")),
        "line_id": str(body.get("line_id", "")),
        "window_days": int(body.get("window_days", 30)),
        "baseline_rate": float(body.get("baseline_rate", 0.0)),
        "note": str(body.get("note", "")),
    }
    return rc.store.save_laix_action(record, actor=str(body.get("actor", "api")))


@app.post("/api/laix/actions/{action_id}/followup")
async def laix_record_followup(action_id: str, request: Request) -> dict[str, Any]:
    rc = state(request)
    body = await request.json()
    if not isinstance(body.get("recurrence"), bool):
        raise HTTPException(400, "recurrence must be true or false")
    followup = {
        "action_id": action_id,
        "case_id": str(body.get("case_id", "")),
        "at": str(body.get("at") or now_iso()),
        "recurrence": body["recurrence"],
        "line_id": str(body.get("line_id", "")),
        "defect": str(body.get("defect", "")),
        "notes": str(body.get("notes", "")),
    }
    return rc.store.add_laix_followup(followup, actor=str(body.get("actor", "api")))


@app.get("/api/laix/outcomes")
def laix_outcomes(request: Request) -> dict[str, Any]:
    rc = state(request)
    actions = rc.store.list_laix_actions()
    followups = rc.store.list_laix_followups()
    outcomes = []
    for action in actions:
        rows = [
            LaixFollowUp(
                action_id=row["action_id"],
                case_id=row.get("case_id", ""),
                at=row["at"],
                recurrence=bool(row.get("recurrence")),
                line_id=row.get("line_id", ""),
                defect=row.get("defect", ""),
                notes=row.get("notes", ""),
            )
            for row in followups
            if row["action_id"] == action["id"]
        ]
        outcome = estimate_outcome(
            action["id"],
            action["action"],
            rows,
            float(action.get("baseline_rate", 0.0)),
            window_days=int(action.get("window_days", 30)),
        )
        outcomes.append(outcome.as_dict())
    return {"count": len(outcomes), "outcomes": outcomes}

# Serve the built SPA when present. The dev server proxies /api instead.
if config.WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=config.WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        candidate = config.WEB_DIST / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        index = config.WEB_DIST / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(404, "not found")
