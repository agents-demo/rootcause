from __future__ import annotations

import json
from pathlib import Path

from rootcause.laix import (
    Constraints,
    ExperienceState,
    FollowUp,
    QualityInterventionPolicy,
    Signal,
    estimate_outcome,
)

FIXTURES = Path(__file__).resolve().parents[1] / "rootcause" / "laix" / "fixtures"
CONTRACT = Path(__file__).resolve().parents[1] / "rootcause" / "laix" / "contract"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_replay_fixture_has_the_frozen_case_count():
    replay = load("replay.json")
    assert replay["contract"] == "laix-replay"
    assert replay["version"] == "1"
    assert replay["capturedFrom"].startswith("rootcause@")
    assert len(replay["cases"]) == 12


def test_replay_decisions_match_the_fixture():
    policy = QualityInterventionPolicy()
    mismatches = []
    for case in load("replay.json")["cases"]:
        signal = Signal(**case["signal"])
        state = ExperienceState(**case["state"])
        constraints = Constraints(**case["constraints"])
        decision = policy.decide(signal, state, constraints)
        expected = case["expected"]
        actual = {
            "action": decision.action,
            "confidence": decision.confidence,
            "why": list(decision.why),
            "requires_approval": decision.requires_approval,
        }
        if actual != expected:
            mismatches.append({"id": case["id"], "expected": expected, "actual": actual})
        assert decision.policy == policy.name
        assert decision.state_id == state.id
        assert decision.signal_id == signal.id
    assert mismatches == []


def test_contract_file_matches_the_policy():
    contract = json.loads((CONTRACT / "quality-intervention.v1.json").read_text(encoding="utf-8"))
    assert contract["policy"] == QualityInterventionPolicy.name
    assert contract["version"] == "1"
    assert 10 <= len(contract["cases"]) <= 20

    policy = QualityInterventionPolicy()
    mismatches = []
    for case in contract["cases"]:
        decision = policy.decide(
            Signal(**case["signal"]),
            ExperienceState(**case["state"]),
            Constraints(**case["constraints"]),
        )
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
