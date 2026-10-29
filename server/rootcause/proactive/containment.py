"""Containment recommendations, exposure and follow-through.

Recommendations are always human-approved. Nothing here talks to a PLC or a line controller.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from ..models import Exposure, ExposurePart, FollowUp, ImpactEstimate, Recommendation, SuggestedCheck, WatchCase

TZ = UTC

PLAYBOOKS: dict[str, dict[str, Any]] = {
    "hold_batch": {
        "title": "Hold the affected batch",
        "detail": "Quarantine the remaining parts from {batch} and release only after the verification check passes.",
        "cost": 1800.0,
    },
    "extra_sampling": {
        "title": "Add inspection sampling",
        "detail": "Add {check} at the affected station for the next {days} days; the failure mode is not visible to the current check.",
        "cost": 900.0,
    },
    "first_off": {
        "title": "Hold first-off until verified",
        "detail": "Do not release the first pallet after the change. Run {check} and compare it to the golden fingerprint.",
        "cost": 350.0,
    },
    "check_dryer": {
        "title": "Restore the dryer and verify dew point",
        "detail": "Regenerate the dryer, run a moisture coupon on the current lot ({batch}) and release only if it passes.",
        "cost": 400.0,
    },
    "check_calibration": {
        "title": "Recalibrate the instrument",
        "detail": "Calibrate the instrument, weld or cast a verification coupon, and hold production until the coupon passes.",
        "cost": 900.0,
    },
    "pull_maintenance": {
        "title": "Pull the maintenance window forward",
        "detail": "Bring the planned maintenance forward for {machine}; verify the parameter after the intervention.",
        "cost": 1200.0,
    },
    "supplier_notice": {
        "title": "Draft a supplier notice",
        "detail": "Send the batch and certificate references to the supplier and request a containment response.",
        "cost": 0.0,
    },
    "verify_parameter": {
        "title": "Verify the parameter after the change",
        "detail": "Confirm the parameter returned and held for three consecutive readings before closing the watch.",
        "cost": 0.0,
    },
}


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_recommendation(
    *,
    rec_id: str,
    watch: WatchCase,
    kind: str,
    pattern: dict[str, Any],
    parts_at_risk: int,
    now: datetime,
    batch_id: str = "",
    machine: str = "",
    check: str = "the first part",
    days: int = 30,
) -> Recommendation:
    play = PLAYBOOKS.get(kind, PLAYBOOKS["verify_parameter"])
    detail = play["detail"].format(batch=batch_id or "the affected lot", machine=machine or "the machine", check=check, days=days)
    scrap = min(24000.0, parts_at_risk * 1450.0) if kind in {"hold_batch", "check_dryer", "check_calibration"} else min(9200.0, parts_at_risk * 700.0)
    return Recommendation(
        id=rec_id,
        watch_id=watch.id,
        kind=kind,  # type: ignore[arg-type]
        title=play["title"],
        detail=detail,
        impact=ImpactEstimate(
            parts_at_risk=parts_at_risk,
            scrap_avoided_eur=round(scrap, 2),
            engineer_hours=round(1 + parts_at_risk / 12, 1),
            cost_eur=play["cost"],
            note="Estimate only, not booked savings. Calculated from the exposure count and the site scrap value.",
        ),
        status="proposed",
        pattern_id=str(pattern.get("id", "")),
    )


def approve(rec: Recommendation, *, actor: str, now: datetime) -> Recommendation:
    rec.status = "approved"
    rec.approved_by = actor
    rec.approved_at = iso(now)
    return rec


def reject(rec: Recommendation, *, actor: str, reason: str, now: datetime) -> Recommendation:
    rec.status = "rejected"
    rec.reason = f"{actor}: {reason}"
    rec.approved_at = iso(now)
    return rec


def execute(rec: Recommendation, *, actor: str, now: datetime) -> Recommendation:
    rec.status = "executed"
    rec.executed_at = iso(now)
    rec.reason = (rec.reason + f" Executed by {actor}.").strip()
    return rec


def verify(rec: Recommendation, *, actor: str, note: str, now: datetime) -> Recommendation:
    rec.status = "verified"
    rec.verified_at = iso(now)
    rec.reason = (rec.reason + f" Verified by {actor}: {note}").strip()
    return rec


def exposure_for(
    *,
    exposure_id: str,
    watch: WatchCase,
    batch_id: str,
    parts: Iterable[dict[str, Any]],
    now: datetime,
    customer_count: int = 1,
) -> Exposure:
    rows = [
        ExposurePart(
            serial=p.get("serial", ""),
            part=p.get("part", ""),
            line_id=p.get("line_id", watch.line_id),
            shift=p.get("shift", "A"),
            customer=p.get("customer", ""),
            status=p.get("status", "in_plant"),
            containment=p.get("containment", "hold"),
        )
        for p in parts
    ]
    return Exposure(
        id=exposure_id,
        watch_id=watch.id,
        batch_id=batch_id,
        generated_at=iso(now),
        parts=rows,
        customers=customer_count or len({p.customer for p in rows}),
        estimated_eur=round(len(rows) * 1450.0, 2),
        status="open",
        note="Trace based on MES batch records. Customer names are fictional in the demo.",
    )


def corrective_draft(watch: WatchCase, rec: Recommendation) -> dict[str, Any]:
    return {
        "title": rec.title,
        "owner": watch.owner,
        "due": iso(datetime.fromisoformat(watch.opened_at.replace("Z", "+00:00")) + timedelta(days=3)),
        "case_id": watch.linked_case_id or watch.id,
        "detail": rec.detail,
        "status": "open",
    }


def supplier_notice(watch: WatchCase, batch_id: str, rec: Recommendation) -> str:
    return (
        f"Subject: containment request for batch {batch_id}\n\n"
        f"Watch {watch.id} on line {watch.line_id} identified a risk with batch {batch_id}. "
        f"Recommended action: {rec.title}.\n\n"
        f"Details: {rec.detail}\n\n"
        "Please confirm containment, certificate traceability and the next delivery batch. "
        "This is a quality notification, not an automatic rejection."
    )


def followup_for(
    *,
    followup_id: str,
    case_id: str,
    action_id: str,
    title: str,
    now: datetime,
    days: int = 30,
    watch_id: str | None = None,
) -> FollowUp:
    return FollowUp(
        id=followup_id,
        case_id=case_id,
        action_id=action_id,
        title=title,
        window_start=iso(now),
        window_end=iso(now + timedelta(days=days)),
        status="monitoring",
        recurrence_watch_id=watch_id,
        note="Post-fix monitoring window. The case is not 'fixed' until the parameter holds.",
    )


def effectiveness(followup: FollowUp, *, parameter_returned: bool, defect_rate_delta: float, recurrence_watch_id: str | None = None) -> FollowUp:
    followup.parameter_returned = parameter_returned
    followup.defect_rate_delta = round(defect_rate_delta, 3)
    if recurrence_watch_id:
        followup.recurrence_watch_id = recurrence_watch_id
        followup.status = "reopened"
        followup.note = "The same signature returned inside the monitoring window; the fix is not verified."
    elif parameter_returned and defect_rate_delta <= 0:
        followup.status = "verified"
        followup.note = "Parameter returned and defect rate did not regress. Verified."
    else:
        followup.status = "monitoring"
    return followup


def suggested_checks_from_pattern(pattern: dict[str, Any]) -> list[SuggestedCheck]:
    return [
        SuggestedCheck(id=f"CH-{pattern.get('id', 'P')}-{i}", label=label, why=f"Defined by {pattern.get('name', 'pattern')}")
        for i, label in enumerate(pattern.get("checks", []), start=1)
    ]


def recurrence_guard(
    followups: Iterable[FollowUp],
    watches: Iterable[WatchCase],
) -> list[FollowUp]:
    """Reopen a post-fix follow-up when the same pattern returns inside its window."""
    active = [w for w in watches if w.status in {"watching", "triage", "investigating"}]
    reopened = []
    for follow in followups:
        if follow.status not in {"monitoring", "verified"} or not follow.pattern_id:
            continue
        match = next((w for w in active if w.pattern_id == follow.pattern_id), None)
        if match:
            follow.status = "reopened"
            follow.recurrence_watch_id = match.id
            follow.note = f"The same signature returned in {match.id}. The fix is not verified."
            reopened.append(follow)
    return reopened
