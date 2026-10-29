"""Watch-case workflow: grouping, scoring, triage, conversion and storm control."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from ..models import RiskSignal, SuggestedCheck, WatchCase

TZ = UTC
SEVERITY_RANK = {"info": 0, "warning": 1, "high": 2, "critical": 3}


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def group_key(signals: Iterable[RiskSignal], pattern_id: str) -> str:
    first = next(iter(signals), None)
    line = first.line_id if first else "unknown"
    return f"{line}:{pattern_id}"


def severity_of(signals: Iterable[RiskSignal]) -> str:
    return max((s.severity for s in signals), key=lambda x: SEVERITY_RANK.get(x, 0), default="warning")


def build_watch(
    *,
    watch_id: str,
    signals: list[RiskSignal],
    pattern: dict[str, Any],
    owner: str,
    now: datetime,
    triage_sla_min: int = 15,
    evidence_ids: Iterable[str] = (),
    checks: Iterable[SuggestedCheck] = (),
) -> WatchCase:
    pattern_id = pattern.get("id", "P-UNKNOWN")
    key = group_key(signals, pattern_id)
    risk = min(0.99, 0.18 + 0.16 * len(signals) + 0.2 * max(SEVERITY_RANK.get(s.severity, 1) for s in signals) / 3)
    confidence = min(95.0, 45 + 8 * len(signals) + 100 * float(pattern.get("historical_precision", 0.55)))
    top = sorted(signals, key=lambda s: -SEVERITY_RANK.get(s.severity, 0))[0] if signals else None
    line = top.line_id if top else "line-6"
    return WatchCase(
        id=watch_id,
        plant_id="plant-de",
        line_id=line,
        title=top.detail.split(".")[0] if top else pattern.get("name", "Risk watch"),
        summary=f"{len(signals)} signal(s) matched {pattern.get('name', 'a known pattern')}. " + (top.detail if top else ""),
        status="watching",
        severity=severity_of(signals),  # type: ignore[arg-type]
        risk_score=round(risk, 3),
        confidence=round(confidence, 1),
        opened_at=iso(now),
        updated_at=iso(now),
        owner=owner,
        sla_due=iso(now + timedelta(minutes=triage_sla_min)),
        group_key=key,
        pattern_id=pattern_id,
        pattern_name=pattern.get("name", "Unknown pattern"),
        pattern_version=pattern.get("version", ""),
        signal_count=len(signals),
        signals=signals,
        evidence_ids=list(evidence_ids),
        suggested_checks=list(checks),
    )


def storm_guard(watches: Iterable[WatchCase], *, max_alerts: int) -> tuple[list[WatchCase], int]:
    """Keep the highest-risk watches in a shift; suppress the rest as a digest count."""
    ordered = sorted(watches, key=lambda w: (-w.risk_score, w.opened_at))
    if len(ordered) <= max_alerts:
        return ordered, 0
    return ordered[:max_alerts], len(ordered) - max_alerts


def duplicate_for(watches: Iterable[WatchCase], key: str) -> WatchCase | None:
    for w in watches:
        if w.group_key == key and w.status in {"watching", "triage", "investigating", "snoozed"}:
            return w
    return None


def triage(watch: WatchCase, *, actor: str, note: str, now: datetime) -> WatchCase:
    watch.status = "triage"
    watch.owner = actor
    watch.triage_note = note
    watch.updated_at = iso(now)
    return watch


def investigate(watch: WatchCase, *, actor: str, note: str = "", now: datetime | None = None) -> WatchCase:
    watch.status = "investigating"
    watch.owner = actor
    if note:
        watch.triage_note = note
    watch.updated_at = iso(now or datetime.now(TZ))
    return watch


def snooze(watch: WatchCase, *, hours: int = 4, actor: str, now: datetime | None = None) -> WatchCase:
    current = now or datetime.now(TZ)
    watch.status = "snoozed"
    watch.updated_at = iso(current)
    watch.sla_due = iso(current + timedelta(hours=hours))
    watch.triage_note = f"Snoozed for {hours} h by {actor}."
    return watch


def dismiss(watch: WatchCase, *, actor: str, reason: str, now: datetime, operational: bool = False) -> WatchCase:
    watch.status = "dismissed"
    watch.outcome = "operational" if operational else "false_alarm"
    watch.outcome_reason = reason
    watch.outcome_actor = actor
    watch.outcome_at = iso(now)
    watch.useful = False
    watch.updated_at = iso(now)
    return watch


def convert(watch: WatchCase, *, case_id: str, actor: str, reason: str, now: datetime, useful: bool = True) -> WatchCase:
    watch.status = "converted"
    watch.linked_case_id = case_id
    watch.outcome = "converted"
    watch.outcome_reason = reason
    watch.outcome_actor = actor
    watch.outcome_at = iso(now)
    watch.useful = useful
    watch.updated_at = iso(now)
    return watch


def true_risk(watch: WatchCase, *, actor: str, reason: str, now: datetime) -> WatchCase:
    watch.status = "converted" if watch.linked_case_id else "investigating"
    watch.outcome = "true_risk"
    watch.outcome_reason = reason
    watch.outcome_actor = actor
    watch.outcome_at = iso(now)
    watch.useful = True
    watch.updated_at = iso(now)
    return watch


def triage_minutes(watch: WatchCase) -> float:
    if watch.status == "watching":
        return 0.0
    opened = _parse(watch.opened_at)
    end = _parse(watch.outcome_at or watch.updated_at)
    return round(max(0.0, (end - opened).total_seconds() / 60), 1)


def is_overdue(watch: WatchCase, now: datetime | None = None) -> bool:
    if watch.status not in {"watching", "triage"}:
        return False
    return _parse(watch.sla_due) < (now or datetime.now(TZ))


def watch_metrics(watches: Iterable[WatchCase], *, alerts_per_line_shift: float = 1.6) -> dict[str, Any]:
    items = list(watches)
    outcomes = [w for w in items if w.outcome in {"converted", "true_risk", "false_alarm", "operational"}]
    useful = [w for w in outcomes if w.useful]
    return {
        "watches": len(items),
        "open": sum(1 for w in items if w.status in {"watching", "triage", "investigating", "snoozed"}),
        "converted": sum(1 for w in items if w.status == "converted"),
        "outcomes": len(outcomes),
        "useful": len(useful),
        "precision": round(len(useful) / len(outcomes), 3) if outcomes else 0.0,
        "alerts_per_line_shift": alerts_per_line_shift,
    }
