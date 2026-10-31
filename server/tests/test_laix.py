from __future__ import annotations

from laix import DecisionRequest, Layer

from rootcause.laix_adapter import decide_for_risk_signal, signal_from_risk
from rootcause.models import RiskSignal
from rootcause.quality import (
    Constraints,
    ExperienceState,
    FollowUp,
    QualityPolicy,
    Signal,
    estimate_outcome,
)


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


def layer() -> Layer:
    return Layer(policy=QualityPolicy())


def decide(sig: Signal, st: ExperienceState, con: Constraints):
    request = DecisionRequest(
        subject=sig.id,
        at=sig.at or "",
        attributes={"quality_signal": sig, "quality_state": st, "quality_constraints": con},
    )
    return layer().decide(request)[0]


def test_low_signal_waits():
    decision = decide(signal(severity="info", z=0.4), state(), constraints())
    assert decision.verb == "wait"
    assert decision.reason_code == "below_threshold"


def test_thin_evidence_asks_for_a_check():
    decision = decide(signal(severity="warning", z=0.2), state(), constraints())
    assert decision.verb == "ask"
    assert decision.reason_code == "thin_evidence"
    assert "thin" in decision.rationale


def test_medium_signal_guides_with_a_watch():
    decision = decide(signal(severity="warning", z=2.0), state(), constraints())
    assert decision.verb == "guide"
    assert decision.reason_code == "open_watch"
    assert decision.requires_approval is False
    assert [ref.id for ref in decision.evidence] == ["EV-04"]


def test_high_signal_acts():
    decision = decide(signal(severity="high", z=3.0), state(), constraints())
    assert decision.verb == "act"
    assert decision.requires_approval is True
    assert decision.cost_of_waiting > 0


def test_critical_signal_escalates():
    decision = decide(signal(severity="critical", z=4.0), state(), constraints())
    assert decision.verb == "escalate"
    assert decision.reason_code == "critical_signal"
    assert decision.requires_approval is True


def test_budget_stops_non_critical_interruptions():
    spent = constraints(max_interruptions_per_shift=2, interruptions_used=2)
    assert decide(signal(severity="high", z=3.0), state(), spent).verb == "wait"
    assert decide(signal(severity="critical", z=4.0), state(), spent).verb == "escalate"


def test_duplicate_signal_is_not_repeated():
    decision = decide(signal(), state(open_watch_keys=("line-6:hydrogen",)), constraints())
    assert decision.verb == "wait"
    assert decision.reason_code == "already_open"
    assert "already" in decision.rationale.split("\n")[0]


def test_layer_selects_the_quality_plugin():
    selected = Layer(policy=QualityPolicy())
    status = selected.status()
    assert status["policy"] == "quality-intervention.v1"
    assert status["policyVersion"] == "1.0"
    assert status["schemaVersion"] == "1.1"


def test_adapter_records_the_decision_and_maps_the_app_shape():
    sig = signal(severity="high", z=3.0)
    st, con = state(), constraints(interruptions_used=0)
    request = DecisionRequest(
        subject=sig.id,
        at=sig.at or "",
        attributes={"quality_signal": sig, "quality_state": st, "quality_constraints": con},
    )
    layer_decision = layer().decide(request)[0]
    decision, record = decide_for_risk_signal(
        RiskSignal(
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
        ),
        [],
        max_alerts=10,
        interruptions_used=0,
    )
    assert decision.action == "act"
    assert decision.why == layer_decision.rationale.split("\n")
    assert decision.evidence_ids == ["EV-04"]
    assert decision.confidence == layer_decision.confidence
    assert decision.requires_approval in {True, False}
    assert decision.policy == "quality-intervention.v1"
    assert decision.state_id == "line:line-6"
    assert decision.signal_id == "SIG-9"

    assert record.action == decision.action
    assert record.signal_id == "SIG-9"
    assert record.inputs_digest
    assert record.approval == ("pending" if decision.requires_approval else "not_required")


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


def test_bench_reaches_full_agreement():
    from rootcause.quality.bench import run

    report = run()
    assert report["cases"] >= 7
    assert report["fail"] == 0
    assert report["agreement"] == 1.0
    assert report["intervention_precision"] == 1.0


def test_json_schema_covers_the_contract():
    from rootcause.quality.schema import schema

    contract = schema()
    for name in ("Signal", "ExperienceState", "Constraints", "Decision", "DecisionRecord", "FollowUp", "Outcome"):
        assert name in contract["$defs"]
    assert contract["$defs"]["Decision"]["properties"]["action"]["enum"] == [
        "wait", "ask", "guide", "act", "verify", "escalate"
    ]


def test_outcome_loop_is_persisted(tmp_path):
    from rootcause.store.db import Store

    store = Store(tmp_path / "laix.sqlite3")
    store.save_laix_action(
        {
            "id": "ACT-T1",
            "at": "2026-10-31T00:00:00Z",
            "action": "venting-check",
            "case_id": "RC-1",
            "line_id": "line-6",
            "window_days": 30,
            "baseline_rate": 0.3,
            "note": "test",
        }
    )
    store.add_laix_followup(
        {"action_id": "ACT-T1", "case_id": "RC-2", "at": "2026-11-30T00:00:00Z", "recurrence": False}
    )
    store.add_laix_followup(
        {"action_id": "ACT-T1", "case_id": "RC-3", "at": "2026-11-30T00:00:00Z", "recurrence": True}
    )
    assert store.list_laix_actions()[0]["id"] == "ACT-T1"
    rows = store.list_laix_followups("ACT-T1")
    assert len(rows) == 2
    assert sum(1 for row in rows if row["recurrence"]) == 1
    store.close()
