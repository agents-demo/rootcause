from __future__ import annotations

from rootcause.laix import (
    Constraints,
    ExperienceState,
    FollowUp,
    QualityInterventionPolicy,
    Signal,
    estimate_outcome,
)
from rootcause.laix_adapter import decide_for_risk_signal, signal_from_risk
from rootcause.models import RiskSignal


def state(**overrides) -> ExperienceState:
    base = dict(id="line-6", goal="prevent the next escape", phase="watch", confidence=0.6)
    base.update(overrides)
    return ExperienceState(**base)


def constraints(**overrides) -> Constraints:
    base = dict(max_interruptions_per_shift=10, interruptions_used=1, interrupt_cost=1.0, miss_cost=10.0)
    base.update(overrides)
    return Constraints(**base)


def signal(**overrides) -> Signal:
    base = dict(
        id="SIG-1",
        source="test",
        kind="ewma",
        line_id="line-6",
        parameter="hydrogen",
        value=2.1,
        baseline=1.2,
        z=2.0,
        at="2026-10-30T00:00:00Z",
        severity="warning",
        evidence_id="EV-04",
    )
    base.update(overrides)
    return Signal(**base)


def test_low_signal_waits():
    decision = QualityInterventionPolicy().decide(signal(severity="info", z=0.4), state(), constraints())
    assert decision.action == "wait"


def test_thin_evidence_asks_for_a_check():
    decision = QualityInterventionPolicy().decide(signal(severity="warning", z=0.2), state(), constraints())
    assert decision.action == "ask"
    assert "thin" in " ".join(decision.why)


def test_medium_signal_guides_with_a_watch():
    decision = QualityInterventionPolicy().decide(signal(severity="warning", z=2.0), state(), constraints())
    assert decision.action == "guide"
    assert decision.requires_approval is False
    assert decision.evidence_ids == ["EV-04"]


def test_high_signal_acts():
    decision = QualityInterventionPolicy().decide(signal(severity="high", z=3.0), state(), constraints())
    assert decision.action == "act"
    assert decision.requires_approval is True
    assert decision.wait_cost > 0


def test_critical_signal_escalates():
    decision = QualityInterventionPolicy().decide(signal(severity="critical", z=4.0), state(), constraints())
    assert decision.action == "escalate"
    assert decision.requires_approval is True


def test_budget_stops_non_critical_interruptions():
    policy = QualityInterventionPolicy()
    spent = constraints(max_interruptions_per_shift=2, interruptions_used=2)
    assert policy.decide(signal(severity="high", z=3.0), state(), spent).action == "wait"
    assert policy.decide(signal(severity="critical", z=4.0), state(), spent).action == "escalate"


def test_duplicate_signal_is_not_repeated():
    decision = QualityInterventionPolicy().decide(signal(), state(open_watch_keys=("line-6:hydrogen",)), constraints())
    assert decision.action == "wait"
    assert "already" in decision.why[0]


def test_record_contains_digest_and_approval_state():
    policy = QualityInterventionPolicy()
    sig, st, con = signal(severity="high", z=3.0), state(), constraints()
    decision = policy.decide(sig, st, con)
    record = policy.record(decision, sig, st, con, actor="engineer")
    assert record.action == "act"
    assert record.inputs_digest
    assert record.approval == "pending"
    assert record.actor == "engineer"


def test_replay_updates_state_and_suppresses_the_second_signal():
    policy = QualityInterventionPolicy()
    signals = [signal(id="SIG-1"), signal(id="SIG-2")]
    decisions = policy.replay(signals, state(), constraints())
    assert decisions[0].action in {"guide", "act"}
    assert decisions[1].action == "wait"


def test_outcome_is_observational_and_reports_effect():
    followups = [
        FollowUp(action_id="A-1", case_id=f"RC-{i}", at="2026-10-30T00:00:00Z", recurrence=i < 2)
        for i in range(10)
    ]
    outcome = estimate_outcome("A-1", "venting-check", followups, baseline_rate=0.3)
    assert outcome.treated == 10
    assert outcome.recurred == 2
    assert outcome.effect == 0.3333
    assert outcome.confidence == 0.5
    assert outcome.causal is False
    assert "not a causal claim" in outcome.note


def test_outcome_without_followup_is_unmeasured():
    outcome = estimate_outcome("A-2", "venting-check", [], baseline_rate=0.3)
    assert outcome.treated == 0
    assert outcome.confidence == 0
    assert "unmeasured" in outcome.note


def test_adapter_maps_risk_signal_and_decision():
    sig = RiskSignal(
        id="SIG-9",
        kind="ewma",
        at="2026-10-30T00:00:00Z",
        line_id="line-6",
        parameter="hydrogen",
        value=2.1,
        baseline=1.2,
        z=3.0,
        severity="high",
        detail="hydrogen above baseline",
        evidence_id="EV-04",
    )
    mapped = signal_from_risk(sig)
    assert mapped.id == "SIG-9"
    assert mapped.evidence_id == "EV-04"
    decision, record = decide_for_risk_signal(sig, [], max_alerts=10, interruptions_used=0)
    assert decision.action in {"act", "guide"}
    assert record.signal_id == "SIG-9"
    assert record.approval in {"pending", "not_required"}
