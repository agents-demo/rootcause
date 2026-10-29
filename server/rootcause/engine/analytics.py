"""Analytics, alerts, savings and compliance exports for the pilot."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

from ..models import CorrectiveAction, Scenario

SCRAP_COST_PER_CASE = {
    "critical": 12400.0,
    "high": 6800.0,
    "medium": 2400.0,
    "low": 700.0,
}


def savings_from_actions(actions: Iterable[CorrectiveAction]) -> dict[str, float]:
    done = [a for a in actions if a.status == "done"]
    open_actions = [a for a in actions if a.status != "done"]
    prevented = sum(a.saving_eur for a in done)
    pipeline = sum(a.saving_eur for a in open_actions)
    return {
        "realised_eur": round(prevented, 2),
        "pipeline_eur": round(pipeline, 2),
        "total_eur": round(prevented + pipeline, 2),
        "engineer_hours_saved": round((prevented + pipeline) / 240.0, 1),
    }


def estimate_case_savings(scenario: Scenario) -> float:
    baseline_cost = SCRAP_COST_PER_CASE.get(scenario.case.severity, 2400.0)
    hours_saved = max(0.0, scenario.baseline_hours - scenario.current_hours)
    return round(baseline_cost + hours_saved * 95.0, 2)


def trend_alerts(series: dict[str, list[float]], *, sigma: float = 2.0) -> list[dict[str, Any]]:
    """Flag a series whose latest value exceeds its history by ``sigma`` standard deviations."""
    import statistics

    alerts: list[dict[str, Any]] = []
    for name, values in series.items():
        if len(values) < 4:
            continue
        history, latest = values[:-1], values[-1]
        mean = statistics.fmean(history)
        sd = statistics.pstdev(history) or 1e-9
        z = (latest - mean) / sd
        if abs(z) >= sigma:
            alerts.append(
                {
                    "series": name,
                    "latest": latest,
                    "mean": round(mean, 3),
                    "z": round(z, 2),
                    "direction": "up" if z > 0 else "down",
                    "level": "critical" if abs(z) >= 3 else "warning",
                }
            )
    return alerts


def defect_series(pack: dict[str, Any], line_id: str | None = None) -> dict[str, list[float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for row in pack["dashboard"]["defect_rate_pct"]:
        for key, value in row.items():
            if key == "week":
                continue
            if line_id and key != line_id:
                continue
            out[key].append(float(value))
    return dict(out)


def top_causes(scenarios: Iterable[Scenario]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for s in scenarios:
        approved = [h for h in s.hypotheses if h.status in {"accepted", "proposed"}]
        if approved:
            counter[approved[0].label] += 1
    total = sum(counter.values()) or 1
    return [
        {"cause": cause, "count": count, "share": round(count / total, 3)}
        for cause, count in counter.most_common(10)
    ]


def cross_line_patterns(scenarios: Iterable[Scenario]) -> list[dict[str, Any]]:
    """Find causes that appear on more than one line, with anonymised identifiers."""
    by_cause: dict[str, set[str]] = defaultdict(set)
    for s in scenarios:
        for h in s.hypotheses:
            by_cause[h.label].add(s.case.line_id)
    return [
        {"cause": cause, "lines": len(lines), "pattern": "shared across lines"}
        for cause, lines in sorted(by_cause.items(), key=lambda kv: -len(kv[1]))
        if len(lines) > 1
    ]


def anonymised_sharing_payload(scenarios: Iterable[Scenario], *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False, "records": [], "note": "Cross-factory sharing is off."}
    records = []
    for s in scenarios:
        top = next((h for h in s.hypotheses if h.status in {"accepted", "proposed"}), None)
        if not top:
            continue
        records.append(
            {
                "process": s.process.split(" ")[0].lower(),
                "cause": top.label,
                "factors": top.factors.model_dump(),
                "time_to_cause_h": s.current_hours,
                "factory": "anonymous",
            }
        )
    return {"enabled": True, "records": records, "note": "No images, batches, serial numbers or machine IDs."}


COMPLIANCE_CONTROLS = {
    "iso9001": [
        ("Case ownership and responsibility", "Each case has an assigned engineer and quality owner."),
        ("Documented investigation method", "Evidence-weighted ranking with a traceable tool trace."),
        ("Approval before closure", "A human approves the report; the AI cannot close a case."),
        ("Corrective action loop", "Actions have owner, due date and status."),
        ("Record retention", "Local append-only case store with report versions."),
        ("Management review data", "Weekly accuracy and time-to-cause reporting."),
    ],
    "iatf": [
        ("Part traceability", "Serial and batch linked to every defect case."),
        ("Supplier quality evidence", "Batch certificates and deviations attached."),
        ("Process change control", "Maintenance events and process deviations in the record."),
        ("PPAP evidence export", "Report and evidence appendix exportable as PDF/Word."),
        ("Control plan linkage", "Defect type mapped to the control plan station."),
        ("Containment record", "Quarantine actions tracked with owner and due date."),
    ],
    "fda": [
        ("Electronic signature", "Named sign-off with timestamp."),
        ("Immutable audit trail", "Database triggers reject update/delete."),
        ("Reason for change", "Rejection and manual-cause actions record a reason."),
        ("Access control", "Role-based review and approval."),
        ("Data integrity", "Append-only case and report versions."),
        ("Retention policy", "On-site store with export package."),
    ],
}


def compliance_export(pack: dict[str, Any], pack_id: str) -> dict[str, Any] | None:
    entry = next((c for c in pack["compliance"] if c["id"] == pack_id), None)
    if not entry:
        return None
    controls = COMPLIANCE_CONTROLS.get(pack_id, [])
    return {
        "id": pack_id,
        "name": entry["name"],
        "standard": entry["standard"],
        "status": entry["status"],
        "controls": [{"control": c, "evidence": e, "state": "covered"} for c, e in controls],
        "generated_at": pack["meta"]["generated"],
        "note": "Evidence map for a pilot review, not a certificate. A notified body performs the audit.",
    }


def pilot_summary(pack: dict[str, Any], store_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    d = pack["dashboard"]
    baseline = d["baseline_hours_to_cause"]
    current = d["median_hours_to_cause"]
    return {
        "investigations": d["investigations_this_week"],
        "median_hours": current,
        "baseline_hours": baseline,
        "speedup": round(baseline / current, 1) if current else None,
        "accuracy": d["cause_accuracy"],
        "scrap_prevented_eur": d["scrap_prevented_eur"],
        "rework_prevented_eur": d["rework_prevented_eur"],
        "engineer_hours_saved": d["engineer_hours_saved"],
        "store": store_metrics or {},
    }
