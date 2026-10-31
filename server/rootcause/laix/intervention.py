"""The quality intervention policy.

This is the part of RootCause that decides **whether, when and how** the app interrupts a quality
engineer: wait, ask for a check, guide with a watch, act (watch + notification), verify a follow-up,
or escalate. It replaces the hand-coded thresholds in the proactive scheduler with an explicit,
testable policy.

It is deliberately not a learned model. Rules first, as LAIX requires; a bandit or calibrated scorer
can replace `_score` later without changing the contract.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, datetime

from .contracts import (
    Constraints,
    Decision,
    DecisionRecord,
    ExperienceState,
    Signal,
)

SEVERITY_WEIGHT = {"info": 0.1, "warning": 0.4, "high": 0.75, "critical": 1.0}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _wait(why: list[str], *, confidence: float, signal: Signal, state: ExperienceState, evidence: bool = True) -> Decision:
    return Decision(
        action="wait",
        confidence=confidence,
        why=why,
        evidence_ids=[signal.evidence_id] if evidence and signal.evidence_id else [],
        state_id=state.id,
        signal_id=signal.id,
    )


class QualityInterventionPolicy:
    """Decide the next action for one quality signal, under interruption and risk constraints."""

    name = "quality-intervention.v1"

    def _score(self, signal: Signal) -> tuple[float, float]:
        severity = SEVERITY_WEIGHT.get(signal.severity, 0.4)
        z = abs(signal.z or 0.0)
        evidence = min(1.0, 0.25 + z / 6.0 + (0.15 if signal.baseline is not None else 0.0))
        if signal.severity in {"high", "critical"}:
            evidence = max(evidence, 0.55)
        score = round(0.55 * severity + 0.30 * evidence + 0.15, 3)  # novelty is 1 unless deduped
        return score, round(evidence, 3)

    def decide(self, signal: Signal, state: ExperienceState, constraints: Constraints) -> Decision:
        key = f"{signal.line_id}:{signal.parameter}"
        if signal.id in state.actions or key in state.open_watch_keys:
            return _wait(
                ["already actioned or already open for this line and parameter"],
                confidence=0.95,
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
            return _wait(
                why + ["interruption budget spent; stay silent unless the signal is critical"],
                confidence=0.8,
                signal=signal,
                state=state,
            )
        if score < 0.40:
            return _wait(
                why + ["below the action threshold"],
                confidence=0.7,
                signal=signal,
                state=state,
            )
        if evidence < 0.50 and not critical:
            return Decision(
                action="ask",
                confidence=round(min(1.0, 0.4 + score * 0.3), 3),
                why=why + ["signal is real but evidence is thin: ask for a check or a second view"],
                evidence_ids=[signal.evidence_id] if signal.evidence_id else [],
                expected_cost=interrupt_cost,
                wait_cost=wait_cost,
                requires_approval=False,
                policy=self.name,
                state_id=state.id,
                signal_id=signal.id,
            )
        if critical:
            return Decision(
                action="escalate",
                confidence=round(min(1.0, 0.6 + score * 0.35), 3),
                why=why + ["critical signal: a named human decides now"],
                evidence_ids=[signal.evidence_id] if signal.evidence_id else [],
                expected_cost=interrupt_cost,
                wait_cost=wait_cost,
                requires_approval=constraints.require_approval,
                policy=self.name,
                state_id=state.id,
                signal_id=signal.id,
            )
        if score < 0.70:
            return Decision(
                action="guide",
                confidence=round(min(1.0, 0.45 + score * 0.4), 3),
                why=why + ["open a watch and let the engineer choose when to look"],
                evidence_ids=[signal.evidence_id] if signal.evidence_id else [],
                expected_cost=0.0,
                wait_cost=wait_cost,
                requires_approval=False,
                policy=self.name,
                state_id=state.id,
                signal_id=signal.id,
            )
        return Decision(
            action="act",
            confidence=round(min(1.0, 0.5 + score * 0.4), 3),
            why=why + ["surface it now: the cost of waiting is higher than the interruption"],
            evidence_ids=[signal.evidence_id] if signal.evidence_id else [],
            expected_cost=interrupt_cost,
            wait_cost=wait_cost,
            requires_approval=constraints.require_approval,
            policy=self.name,
            state_id=state.id,
            signal_id=signal.id,
        )

    def record(
        self,
        decision: Decision,
        signal: Signal,
        state: ExperienceState,
        constraints: Constraints,
        *,
        actor: str = "policy",
    ) -> DecisionRecord:
        payload = {
            "signal": signal.as_dict(),
            "state": state.as_dict(),
            "constraints": constraints.as_dict(),
            "decision": decision.as_dict(),
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
        return DecisionRecord(
            id=f"DR-{uuid.uuid4().hex[:12]}",
            at=_now(),
            state_id=state.id,
            signal_id=signal.id,
            action=decision.action,
            confidence=decision.confidence,
            why=decision.why,
            evidence_ids=decision.evidence_ids,
            inputs_digest=digest,
            actor=actor,
            approval="pending" if decision.requires_approval else "not_required",
        )

    def replay(
        self,
        signals: Iterable[Signal],
        state: ExperienceState,
        constraints: Constraints,
    ) -> list[Decision]:
        """Run the policy over a signal stream, updating the state after each decision."""
        current = state
        out: list[Decision] = []
        for signal in signals:
            decision = self.decide(signal, current, constraints)
            out.append(decision)
            if decision.action != "wait":
                current = replace(
                    current,
                    actions=tuple([*current.actions, signal.id]),
                    open_watch_keys=tuple([*current.open_watch_keys, f"{signal.line_id}:{signal.parameter}"]),
                )
        return out


def decision_summary(decision: Decision) -> str:
    return f"{decision.action} ({decision.confidence:.0%}): {'; '.join(decision.why[:2])}"
