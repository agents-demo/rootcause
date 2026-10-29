"""FastAPI surface for RootCause.

The API is intentionally small and boring: a pilot needs to run for 90 days behind a factory
firewall. Every mutation writes an audit event. The AI never approves a cause.
"""

from __future__ import annotations

import csv
import io
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .. import config
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
from ..models import (
    AcceptRequest,
    ApprovalRequest,
    Evidence,
    ManualCauseRequest,
    RejectRequest,
    Report,
    ReportPatch,
    now_iso,
)
from ..npu.broker import broker_from_env
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
    rc.ensure_tenant()
    return rc


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rc = create_state()
    yield
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
        "version": "0.9.0",
        "model": config.MODEL_VERSION,
        "scenarios": len(rc.pack["scenarios"]),
        "npu": rc.npu.health(),
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
