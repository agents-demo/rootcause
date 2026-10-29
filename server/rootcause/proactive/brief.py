"""Shift brief generation for proactive triage."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from ..models import ShiftBrief, WatchCase

TZ = UTC


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_brief(
    *,
    brief_id: str,
    watches: Iterable[WatchCase],
    cases: Iterable[dict[str, Any]],
    actions: Iterable[dict[str, Any]],
    followups: Iterable[dict[str, Any]],
    coverage: Iterable[dict[str, Any]],
    lines: Iterable[str],
    shift: str,
    now: datetime,
) -> ShiftBrief:
    active = [w for w in watches if w.status in {"watching", "triage", "investigating", "snoozed"}]
    active.sort(key=lambda w: (-w.risk_score, w.opened_at))
    open_cases = [
        {"case_id": c.get("id"), "title": c.get("defect_type"), "status": c.get("status")}
        for c in cases
        if c.get("status") not in {"approved", "closed"}
    ][:6]
    due = [a for a in actions if a.get("status") != "done"][:6]
    fixed = [
        {"case_id": f.get("case_id"), "title": f.get("title"), "note": f.get("note", "")}
        for f in followups
        if f.get("status") == "monitoring" and not f.get("parameter_returned")
    ][:4]
    coverage_rows = list(coverage)
    low = [c for c in coverage_rows if float(c.get("pct", 1)) < 0.95]
    if low:
        coverage_note = "Below the 95% floor: " + ", ".join(
            f"{c.get('line_id')} ({float(c.get('pct', 0)) * 100:.0f}%)" for c in low
        ) + ". No quality risk is scored for the stale sources."
    else:
        coverage_note = f"Coverage {min((float(c.get('pct', 1)) for c in coverage_rows), default=1) * 100:.0f}–100%; all sources above the floor."

    if active:
        summary = (
            f"{len(active)} active watch(es). Top risk: {active[0].title} on {active[0].line_id.replace('line-', 'Line ')} "
            f"({active[0].confidence:.0f}% confidence). {len(open_cases)} open case(s), {len(due)} action(s) due."
        )
    else:
        summary = f"No active watch. {len(open_cases)} open case(s), {len(due)} action(s) due. {coverage_note}"

    return ShiftBrief(
        id=brief_id,
        at=iso(now),
        shift=shift,
        line_ids=list(lines),
        title=f"Shift {shift} risk brief — {now.strftime('%d %b')}",
        summary=summary,
        top_risks=[
            {
                "watch_id": w.id,
                "title": w.title,
                "severity": w.severity,
                "action": w.suggested_checks[0].label if w.suggested_checks else "Triage the watch",
            }
            for w in active[:5]
        ],
        open_cases=open_cases,
        actions_due=due,
        fixed_not_verified=fixed,
        coverage_note=coverage_note,
        generated_by="RootCause proactive scheduler",
    )


def render_brief_markdown(brief: ShiftBrief) -> str:
    lines = [f"# {brief.title}", "", brief.summary, ""]
    lines += ["## Top risks", ""]
    if brief.top_risks:
        for r in brief.top_risks:
            lines.append(f"- **{r['title']}** ({r['severity']}) — {r['action']} · `{r['watch_id']}`")
    else:
        lines.append("- None open.")
    lines += ["", "## Open cases", ""]
    lines += [f"- {c['case_id']} · {c['title']} · {c['status']}" for c in brief.open_cases] or ["- None."]
    lines += ["", "## Actions due", ""]
    lines += [f"- {a.get('title')} · {a.get('owner', '')} · due {a.get('due', '')}" for a in brief.actions_due] or ["- None."]
    lines += ["", "## Fixed but not verified", ""]
    lines += [f"- {f['title']} · {f.get('note', '')}" for f in brief.fixed_not_verified] or ["- None."]
    lines += ["", "## Coverage", "", brief.coverage_note, ""]
    lines += ["---", "Recommendations only. No automatic line control, rejection or batch hold.", ""]
    return "\n".join(lines)
