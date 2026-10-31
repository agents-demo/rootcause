"""RootCause → LAIX adapter.

This is the only file that knows both worlds. It maps a RootCause ``RiskSignal`` and the open watches
to the portable LAIX contracts, calls the policy, and returns a decision plus its record.

If RootCause is later rebuilt on LAIX, this adapter shrinks to implementing the LAIX south interface
(read state, run skill, ask approval, stream events).
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from .laix import (
    Constraints,
    Decision,
    DecisionRecord,
    ExperienceState,
    QualityInterventionPolicy,
    Signal,
)
from .models import RiskSignal, WatchCase

POLICY = QualityInterventionPolicy()


def signal_from_risk(signal: RiskSignal) -> Signal:
    return Signal(
        id=signal.id,
        source="rootcause.proactive",
        kind=signal.kind,
        line_id=signal.line_id,
        parameter=signal.parameter,
        value=signal.value,
        baseline=signal.baseline,
        z=signal.z,
        at=signal.at,
        severity=signal.severity,
        evidence_id=signal.evidence_id,
        attributes={"detail": signal.detail, "cleared": signal.cleared},
    )


def state_from_existing(
    signal: RiskSignal,
    existing: Iterable[WatchCase],
) -> ExperienceState:
    watches = list(existing)
    open_keys = {
        f"{watch.line_id}:{watch.signals[0].parameter}" if watch.signals else watch.group_key
        for watch in watches
        if watch.status in {"watching", "triage", "investigating"}
    }
    actions = tuple(sig.id for watch in watches for sig in watch.signals)
    return ExperienceState(
        id=f"line:{signal.line_id}",
        goal="prevent the next quality escape without alert fatigue",
        phase="watch",
        beliefs={"coverage": 0.0},
        confidence=0.6,
        open_watch_keys=tuple(open_keys),
        actions=actions,
        expires_at=None,
    )


def constraints_for_scan(*, max_alerts: int, interruptions_used: int) -> Constraints:
    return Constraints(
        max_interruptions_per_shift=max(1, int(max_alerts)),
        interruptions_used=max(0, int(interruptions_used)),
        interrupt_cost=float(os.getenv("ROOTCAUSE_LAIX_INTERRUPT_COST", "1.0")),
        miss_cost=float(os.getenv("ROOTCAUSE_LAIX_MISS_COST", "10.0")),
        latency_budget_ms=1000,
        risk_ceiling="critical",
        require_approval=os.getenv("ROOTCAUSE_LAIX_REQUIRE_APPROVAL", "0").lower() in {"1", "true", "yes"},  # the app only opens a watch/notification; it never controls the line
    )


def decide_for_risk_signal(
    signal: RiskSignal,
    existing: Iterable[WatchCase],
    *,
    max_alerts: int,
    interruptions_used: int,
) -> tuple[Decision, DecisionRecord]:
    laix_signal = signal_from_risk(signal)
    state = state_from_existing(signal, existing)
    constraints = constraints_for_scan(max_alerts=max_alerts, interruptions_used=interruptions_used)
    decision = POLICY.decide(laix_signal, state, constraints)
    record = POLICY.record(decision, laix_signal, state, constraints)
    return decision, record
