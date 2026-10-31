"""RootCause → LAIX adapter.

This is the only file that knows both worlds. It maps a RootCause ``RiskSignal`` and the open watches
to a generic ``DecisionRequest``, calls the LAIX ``Layer`` with the RootCause quality policy plugin,
and maps the returned ``LayerDecision`` back to the shape the app, API and scheduler already use.

LAIX owns the contract, the layer, the policy plugin interface, records and outcomes. RootCause owns
the quality signal, the quality policy, the line/case/watch data and this adapter.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from laix import DecisionRequest, Layer
from laix.layer import Decision as LayerDecision

from .models import RiskSignal, WatchCase
from .quality import (
    Constraints,
    Decision,
    DecisionRecord,
    ExperienceState,
    QualityPolicy,
    Signal,
    record_for,
)

QUALITY_POLICY = QualityPolicy()
LAYER = Layer(policy=QUALITY_POLICY)


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


def decision_from_layer(decision: LayerDecision, signal: Signal, state: ExperienceState) -> Decision:
    expected_cost = decision.breakdown.interruption if decision.breakdown else 0.0
    return Decision(
        action=decision.verb,
        confidence=decision.confidence,
        why=list(decision.rationale.split("\n")) if decision.rationale else [],
        evidence_ids=[ref.id for ref in decision.evidence],
        expected_cost=expected_cost,
        wait_cost=decision.cost_of_waiting,
        requires_approval=decision.requires_approval,
        policy=decision.policy_version or QUALITY_POLICY.name,
        state_id=state.id,
        signal_id=signal.id,
    )


def decide_quality(
    signal: Signal,
    state: ExperienceState,
    constraints: Constraints,
    *,
    actor: str = "policy",
) -> tuple[Decision, DecisionRecord]:
    """One quality decision through ``Layer(policy=QualityPolicy())``."""
    request = DecisionRequest(
        subject=signal.id,
        at=signal.at or "",
        attributes={
            "quality_signal": signal,
            "quality_state": state,
            "quality_constraints": constraints,
        },
    )
    layer_decision = LAYER.decide(request)[0]
    return decision_from_layer(layer_decision, signal, state), record_for(layer_decision, request, actor=actor)


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
    return decide_quality(laix_signal, state, constraints)
