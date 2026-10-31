from __future__ import annotations

import json
from pathlib import Path

from laix import DecisionRequest, Layer

from rootcause.laix_adapter import decision_from_layer
from rootcause.quality import (
    Constraints,
    ExperienceState,
    FollowUp,
    QualityPolicy,
    Signal,
    estimate_outcome,
)

FIXTURES = Path(__file__).resolve().parents[1] / "rootcause" / "quality" / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def replay(case: dict):
    signal = Signal(**case["signal"])
    state = ExperienceState(**case["state"])
    constraints = Constraints(**case["constraints"])
    request = DecisionRequest(
        subject=signal.id,
        at=signal.at or "",
        attributes={
            "quality_signal": signal,
            "quality_state": state,
            "quality_constraints": constraints,
        },
    )
    layer_decision = Layer(policy=QualityPolicy()).decide(request)[0]
    return decision_from_layer(layer_decision, signal, state)


def test_replay_fixture_has_the_frozen_case_count():
    replay_fixture = load("replay.json")
    assert replay_fixture["contract"] == "laix-replay"
    assert replay_fixture["version"] == "1"
    assert replay_fixture["capturedFrom"].startswith("rootcause@")
    assert len(replay_fixture["cases"]) == 12


def test_replay_decisions_match_the_fixture_through_the_plugin():
    mismatches = []
    for case in load("replay.json")["cases"]:
        decision = replay(case)
        actual = {
            "action": decision.action,
            "confidence": decision.confidence,
            "why": list(decision.why),
            "requires_approval": decision.requires_approval,
        }
        if actual != case["expected"]:
            mismatches.append({"id": case["id"], "expected": case["expected"], "actual": actual})
    assert mismatches == []


def test_outcome_fixture_matches_estimate_outcome():
    fixture = load("outcome.json")
    assert fixture["contract"] == "laix-outcome"
    assert fixture["version"] == "1"
    mismatches = []
    for case in fixture["cases"]:
        followups = [FollowUp(**row) for row in case["followups"]]
        outcome = estimate_outcome(
            case["action_id"],
            case["action"],
            followups,
            fixture["baseline_rate"],
            window_days=fixture["window_days"],
        )
        actual = {
            "treated": outcome.treated,
            "recurred": outcome.recurred,
            "treated_rate": outcome.treated_rate,
            "effect": outcome.effect,
            "confidence": outcome.confidence,
            "causal": outcome.causal,
        }
        if actual != case["expected"]:
            mismatches.append({"id": case["id"], "expected": case["expected"], "actual": actual})
    assert mismatches == []


def test_outcome_is_still_observational():
    fixture = load("outcome.json")
    case = next(case for case in fixture["cases"] if case["id"] == "ten-followups")
    outcome = estimate_outcome(
        case["action_id"],
        case["action"],
        [FollowUp(**row) for row in case["followups"]],
        fixture["baseline_rate"],
        window_days=fixture["window_days"],
    )
    assert outcome.causal is False
    assert "not a causal claim" in outcome.note
