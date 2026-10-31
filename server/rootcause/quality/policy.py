"""The RootCause quality intervention policy, a LAIX policy plugin.

This is the quality-specific part of the decision layer. LAIX owns the generic ``Layer``,
``DecisionRequest`` and ``LayerDecision`` contract; RootCause owns the rules below. The plugin
receives a generic request and reads the quality objects the adapter placed in
``request.attributes``. No quality noun enters LAIX.

The rules are deliberately not a learned model. Rules first, as LAIX requires; a bandit or calibrated
scorer can replace ``_score`` later without changing the plugin contract.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime

from laix import DecisionRequest, LayerDecision
from laix.layer import Breakdown, EvidenceRef

from .contracts import Constraints, DecisionRecord, ExperienceState, Signal

SEVERITY_WEIGHT = {"info": 0.1, "warning": 0.4, "high": 0.75, "critical": 1.0}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class QualityInterventionPolicy:
    """Decide the next action for one quality signal, under interruption and risk constraints."""

    name = "quality-intervention.v1"
    version = "1.0"

    def decide(self, request: DecisionRequest) -> list[LayerDecision]:
        signal: Signal = request.attributes["quality_signal"]
        state: ExperienceState = request.attributes["quality_state"]
        constraints: Constraints = request.attributes["quality_constraints"]
        return [self._decide(signal, state, constraints)]

    def _score(self, signal: Signal) -> tuple[float, float]:
        severity = SEVERITY_WEIGHT.get(signal.severity, 0.4)
        z = abs(signal.z or 0.0)
        evidence = min(1.0, 0.25 + z / 6.0 + (0.15 if signal.baseline is not None else 0.0))
        if signal.severity in {"high", "critical"}:
            evidence = max(evidence, 0.55)
        score = round(0.55 * severity + 0.30 * evidence + 0.15, 3)  # novelty is 1 unless deduped
        return score, round(evidence, 3)

    def _make(
        self,
        *,
        verb: str,
        confidence: float,
        reason_code: str,
        why: list[str],
        signal: Signal,
        state: ExperienceState,
        expected_cost: float = 0.0,
        wait_cost: float = 0.0,
        requires_approval: bool = False,
        score: float | None = None,
        evidence: bool = True,
    ) -> LayerDecision:
        refs = (EvidenceRef(id=signal.evidence_id, kind="quality_signal"),) if evidence and signal.evidence_id else ()
        return LayerDecision(
            verb=verb,
            confidence=confidence,
            reason_code=reason_code,
            rationale="\n".join(why),
            evidence=refs,
            requires_approval=requires_approval,
            score=score,
            breakdown=Breakdown(severity=score or 0.0, total=score or 0.0, interruption=expected_cost),
            cost_of_waiting=wait_cost,
            policy_version=self.name,
        )

    def _decide(self, signal: Signal, state: ExperienceState, constraints: Constraints) -> LayerDecision:
        generic = signal.as_generic()
        key = f"{generic['subject']}:{generic['kind']}"
        if signal.id in state.actions or key in state.open_watch_keys:
            return self._make(
                verb="wait",
                confidence=0.95,
                reason_code="already_open",
                why=["already actioned or already open for this line and parameter"],
                signal=signal,
                state=state,
            )

        score, evidence = self._score(signal)
        budget = max(0, constraints.max_interruptions_per_shift)
        left = max(0, budget - constraints.interruptions_used)
        critical = signal.severity == "critical"
        wait_cost = round(constraints.miss_cost * (1.0 - score), 2)
        interrupt_cost = round(constraints.interrupt_cost, 2)

        why = [
            f"severity={signal.severity}",
            f"evidence={evidence}" + (f" (z={signal.z})" if signal.z is not None else " (no z-score)"),
            f"attention budget {constraints.interruptions_used}/{budget}",
            f"score={score}; wait cost={wait_cost}; interrupt cost={interrupt_cost}",
        ]

        if left == 0 and not critical:
            return self._make(
                verb="wait",
                confidence=0.8,
                reason_code="budget_spent",
                why=why + ["interruption budget spent; stay silent unless the signal is critical"],
                signal=signal,
                state=state,
                wait_cost=wait_cost,
                score=score,
            )
        if score < 0.40:
            return self._make(
                verb="wait",
                confidence=0.7,
                reason_code="below_threshold",
                why=why + ["below the action threshold"],
                signal=signal,
                state=state,
                wait_cost=wait_cost,
                score=score,
            )
        if evidence < 0.50 and not critical:
            return self._make(
                verb="ask",
                confidence=round(min(1.0, 0.4 + score * 0.3), 3),
                reason_code="thin_evidence",
                why=why + ["signal is real but evidence is thin: ask for a check or a second view"],
                signal=signal,
                state=state,
                expected_cost=interrupt_cost,
                wait_cost=wait_cost,
                requires_approval=False,
                score=score,
            )
        if critical:
            return self._make(
                verb="escalate",
                confidence=round(min(1.0, 0.6 + score * 0.35), 3),
                reason_code="critical_signal",
                why=why + ["critical signal: a named human decides now"],
                signal=signal,
                state=state,
                expected_cost=interrupt_cost,
                wait_cost=wait_cost,
                requires_approval=constraints.require_approval,
                score=score,
            )
        if score < 0.70:
            return self._make(
                verb="guide",
                confidence=round(min(1.0, 0.45 + score * 0.4), 3),
                reason_code="open_watch",
                why=why + ["open a watch and let the engineer choose when to look"],
                signal=signal,
                state=state,
                expected_cost=0.0,
                wait_cost=wait_cost,
                requires_approval=False,
                score=score,
            )
        return self._make(
            verb="act",
            confidence=round(min(1.0, 0.5 + score * 0.4), 3),
            reason_code="surface_now",
            why=why + ["surface it now: the cost of waiting is higher than the interruption"],
            signal=signal,
            state=state,
            expected_cost=interrupt_cost,
            wait_cost=wait_cost,
            requires_approval=constraints.require_approval,
            score=score,
        )


QualityPolicy = QualityInterventionPolicy


def record_for(decision: LayerDecision, request: DecisionRequest, *, actor: str = "policy") -> DecisionRecord:
    """Build the RootCause decision record from a LAIX decision and its request."""
    signal: Signal = request.attributes["quality_signal"]
    state: ExperienceState = request.attributes["quality_state"]
    constraints: Constraints = request.attributes["quality_constraints"]
    payload = {
        "subject": request.subject,
        "at": request.at,
        "signal": asdict(signal),
        "state": asdict(state),
        "constraints": asdict(constraints),
        "decision": decision.to_dict(),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
    why = list(decision.rationale.split("\n")) if decision.rationale else []
    return DecisionRecord(
        id=f"DR-{uuid.uuid4().hex[:12]}",
        at=_now(),
        state_id=state.id,
        signal_id=signal.id,
        action=decision.verb,
        confidence=decision.confidence,
        why=why,
        evidence_ids=[ref.id for ref in decision.evidence],
        inputs_digest=digest,
        actor=actor,
        approval="pending" if decision.requires_approval else "not_required",
    )
