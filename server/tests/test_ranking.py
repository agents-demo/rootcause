from __future__ import annotations

from rootcause.demo.build_pack import build_pack
from rootcause.engine.orchestrator import run_investigation
from rootcause.engine.ranking import rank_hypotheses, unknown_confidence
from rootcause.models import Scenario


def test_pack_is_deterministic():
    a = build_pack().model_dump(mode="json")
    b = build_pack().model_dump(mode="json")
    assert a == b
    assert len(a["scenarios"]) == 4


def test_trust_beat_reranks_gas_porosity():
    pack = build_pack()
    bracket = pack.scenarios[0]
    initial = rank_hypotheses(bracket.hypotheses)
    assert initial[0].id == "tool_mark"
    after = rank_hypotheses(bracket.hypotheses, rejected=["tool_mark"])
    assert after[0].id == "gas_porosity"
    assert after[0].confidence > initial[0].confidence * 0.9
    tool = next(h for h in after if h.id == "tool_mark")
    assert tool.status == "rejected"
    assert tool.confidence < 5


def test_confidences_leave_room_for_unknown():
    pack = build_pack()
    for scenario in pack.scenarios:
        ranked = rank_hypotheses(scenario.hypotheses)
        assert 0 < unknown_confidence(ranked) < 30
        assert sum(h.confidence for h in ranked) < 100


def test_orchestrator_builds_trace_and_window():
    bracket: Scenario = build_pack().scenarios[0]
    inv = run_investigation(bracket)
    assert len(inv["window"]) == 6
    assert inv["hypotheses"][0]["id"] == "tool_mark"
    assert any(step["tool"] == "opcua.read_window" for step in inv["trace"])
    assert inv["trace"][-1]["status"] == "waiting"

    rejected = run_investigation(bracket, rejected=["tool_mark"])
    assert rejected["hypotheses"][0]["id"] == "gas_porosity"
    assert any(step["tool"] == "cause.rerank" for step in rejected["trace"])
    assert rejected["chain"]["confidence"] > 0.6
