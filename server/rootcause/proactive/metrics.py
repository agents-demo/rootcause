"""Proactive metrics and alert-fatigue calculations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from ..models import FollowUp, WatchCase


def compute_metrics(
    pack: dict[str, Any],
    watches: Iterable[WatchCase],
    *,
    coverage: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base = pack.get("proactive", {}).get("metrics", {})
    items = list(watches)
    outcomes = [w for w in items if w.outcome in {"converted", "true_risk", "false_alarm", "operational"}]
    quality_outcomes = [w for w in outcomes if w.outcome != "operational"]
    quality_useful = [w for w in quality_outcomes if w.useful]
    precision = round(len(quality_useful) / len(quality_outcomes), 3) if quality_outcomes else float(base.get("watch_precision", 0))
    open_watches = [w for w in items if w.status in {"watching", "triage", "investigating", "snoozed"}]
    triaged = [w for w in items if w.status in {"triage", "investigating", "converted", "dismissed"}]
    triage_values = []
    for w in triaged:
        if w.status == "triage":
            continue
        try:
            opened = datetime.fromisoformat(w.opened_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat((w.outcome_at or w.updated_at).replace("Z", "+00:00"))
            triage_values.append(max(0, (end - opened).total_seconds() / 60))
        except Exception:
            continue
    median_triage = round(sorted(triage_values)[len(triage_values) // 2], 1) if triage_values else float(base.get("median_triage_min", 0))
    coverage_rows = list(coverage or pack.get("proactive", {}).get("coverage", []))
    coverage_pct = round(sum(float(c.get("pct", 0)) for c in coverage_rows) / len(coverage_rows), 4) if coverage_rows else 0
    containment = [
        r for r in pack.get("proactive", {}).get("recommendations", [])
        if r.get("status") in {"approved", "executed", "verified"}
    ]
    total_recs = pack.get("proactive", {}).get("recommendations", [])
    conversion = round(len(containment) / len(total_recs), 3) if total_recs else float(base.get("containment_conversion", 0))
    return {
        **base,
        "watch_precision": precision,
        "useful_watches": len(quality_useful),
        "total_watches": len(quality_outcomes) or int(base.get("total_watches", 0)),
        "open_watches": len(open_watches),
        "median_triage_min": median_triage,
        "coverage_pct": coverage_pct,
        "containment_conversion": conversion,
        "alerts_open": len(open_watches),
        "drift": drift_status(base.get("weekly", [])),
    }


def alert_fatigue(watches: Iterable[WatchCase], *, shifts: int = 8, lines: int = 4) -> dict[str, float]:
    items = list(watches)
    per_line_shift = round(len(items) / max(1, shifts * lines), 2)
    dismissed = sum(1 for w in items if w.status == "dismissed")
    snoozed = sum(1 for w in items if w.status == "snoozed")
    return {
        "alerts_per_line_shift": per_line_shift,
        "dismissal_rate": round(dismissed / len(items), 3) if items else 0.0,
        "snooze_rate": round(snoozed / len(items), 3) if items else 0.0,
        "open": sum(1 for w in items if w.status in {"watching", "triage", "investigating", "snoozed"}),
    }


def drift_status(weekly: Iterable[dict[str, Any]], *, target: float = 0.6) -> dict[str, Any]:
    rows = list(weekly)
    if len(rows) < 4:
        return {"status": "unknown", "detail": "Not enough weekly history for drift detection."}
    recent = sum(float(r.get("precision", 0)) for r in rows[-2:]) / 2
    prior = sum(float(r.get("precision", 0)) for r in rows[-4:-2]) / 2
    delta = round(recent - prior, 3)
    if recent < target and delta < -0.03:
        return {"status": "warning", "delta": delta, "detail": f"Precision fell {abs(delta) * 100:.1f} points over two weeks and is below the {target:.0%} target."}
    return {"status": "ok", "delta": delta, "detail": f"Precision is stable ({delta:+.1%} over two weeks)."}


def threshold_tuning(watches: Iterable[WatchCase], *, target_precision: float = 0.6) -> list[dict[str, Any]]:
    """A conservative tuning hint. A human must approve every change."""
    items = list(watches)
    outcomes = [w for w in items if w.useful is not None]
    precision = sum(1 for w in outcomes if w.useful) / len(outcomes) if outcomes else 0.0
    if precision < target_precision:
        return [
            {
                "action": "tighten",
                "reason": f"Precision {precision:.0%} is below the {target_precision:.0%} target.",
                "suggestion": "Raise the score threshold by 0.05 and re-run replay before promoting.",
                "requires_approval": True,
            }
        ]
    return [
        {
            "action": "hold",
            "reason": f"Precision {precision:.0%} meets the target.",
            "suggestion": "Keep the champion; evaluate the challenger in shadow.",
            "requires_approval": True,
        }
    ]


def coverage_status(rows: Iterable[dict[str, Any]], *, floor: float = 0.95) -> dict[str, Any]:
    items = list(rows)
    blind = [r for r in items if float(r.get("pct", 1)) < floor]
    return {
        "floor": floor,
        "coverage_pct": round(sum(float(r.get("pct", 0)) for r in items) / len(items), 4) if items else 0,
        "below_floor": [r.get("line_id") for r in blind],
        "status": "blind" if any(float(r.get("pct", 1)) < 0.8 for r in items) else "degraded" if blind else "ok",
    }


def followup_effectiveness(followups: Iterable[FollowUp]) -> dict[str, Any]:
    items = list(followups)
    verified = [f for f in items if f.status == "verified"]
    reopened = [f for f in items if f.status == "reopened"]
    return {
        "total": len(items),
        "verified": len(verified),
        "reopened": len(reopened),
        "monitoring": len([f for f in items if f.status == "monitoring"]),
        "verification_rate": round(len(verified) / len(items), 3) if items else 0,
        "reopened_ids": [f.recurrence_watch_id for f in reopened if f.recurrence_watch_id],
    }
