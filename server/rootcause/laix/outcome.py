"""Outcome learning for quality actions.

LAIX asks whether the intervention helped. RootCause currently records corrective actions and
follow-ups but does not measure recurrence. This module is the smallest honest version of that loop:

- an action (a cause accepted, a prevention check, a batch held),
- a follow-up window,
- the recurrence rate after the action,
- a comparison with the baseline rate.

It is observational. It does not claim causality; matching and a controlled pilot come later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .contracts import FollowUp, Outcome


def estimate_outcome(
    action_id: str,
    action: str,
    followups: Iterable[FollowUp],
    baseline_rate: float,
    *,
    window_days: int = 30,
) -> Outcome:
    rows = [row for row in followups if row.action_id == action_id]
    treated = len(rows)
    recurred = sum(1 for row in rows if row.recurrence)
    treated_rate = round(recurred / treated, 4) if treated else 0.0
    baseline = max(0.0, float(baseline_rate))
    effect = round((baseline - treated_rate) / baseline, 4) if baseline else 0.0
    confidence = round(min(1.0, treated / 20.0), 3)  # sample-size confidence, not statistical proof
    if not treated:
        note = "No follow-up yet. The action is stored, but its effect is unmeasured."
    elif treated < 5:
        note = (
            f"{treated} follow-up case(s); the estimate is directional only. "
            "Match on line, defect and batch before treating it as an effect."
        )
    else:
        note = (
            f"{treated} follow-up cases in a {window_days}-day window. "
            "Observational estimate, not a causal claim; a controlled pilot is still required."
        )
    return Outcome(
        action_id=action_id,
        action=action,
        treated=treated,
        recurred=recurred,
        baseline_rate=round(baseline, 4),
        treated_rate=treated_rate,
        effect=effect,
        confidence=confidence,
        window_days=window_days,
        note=note,
        causal=False,
    )


@dataclass
class QualityOutcomeTracker:
    """In-memory tracker; the LAIX runtime would persist this behind its state interface."""

    actions: dict[str, dict] = field(default_factory=dict)
    followups: list[FollowUp] = field(default_factory=list)

    def record_action(self, action_id: str, action: str, *, at: str, case_id: str = "", line_id: str = "", note: str = "") -> None:
        self.actions[action_id] = {"action": action, "at": at, "case_id": case_id, "line_id": line_id, "note": note}

    def record_followup(self, followup: FollowUp) -> None:
        self.followups.append(followup)

    def estimate(self, action_id: str, baseline_rate: float, *, window_days: int = 30) -> Outcome:
        action = str(self.actions.get(action_id, {}).get("action", "unknown"))
        return estimate_outcome(action_id, action, self.followups, baseline_rate, window_days=window_days)

    def report(self, baseline_rate: float, *, window_days: int = 30) -> list[Outcome]:
        return [self.estimate(action_id, baseline_rate, window_days=window_days) for action_id in self.actions]
