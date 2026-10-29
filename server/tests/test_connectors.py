from __future__ import annotations

from rootcause.connectors import ModbusConnector, OpcUaConnector, normalise_frame
from rootcause.engine.analytics import trend_alerts
from rootcause.engine.feedback import apply_priors, priors_from_corrections
from rootcause.models import Hypothesis


def test_normalisation_drops_bad_values_and_keeps_provenance():
    out = normalise_frame(
        {"TAG_01": "712.4", "TAG_02": "bad", "TAG_03": 58.2, "TAG_04": float("nan")},
        {"TAG_01": "pour_temp", "TAG_03": "quench_temp"},
        units={"pour_temp": "C", "quench_temp": "C"},
    )
    assert out["values"] == {"pour_temp": 712.4, "quench_temp": 58.2}
    assert out["dropped"] == ["TAG_02", "TAG_04"]
    assert out["quality"] == "partial"
    assert out["units"]["pour_temp"] == "C"


def test_connectors_simulate_without_hardware():
    opc = OpcUaConnector("opc.tcp://10.0.0.1:4840", simulate=True)
    assert opc.test().reachable
    assert opc.read(["a", "b"])["mode"] == "simulated"
    modbus = ModbusConnector("10.0.0.2:502", simulate=True)
    assert modbus.read([1, 2, 3])["mode"] == "simulated"


def test_trend_alerts_flag_a_step_change():
    values = [1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.0, 2.4]
    alerts = trend_alerts({"line-6": values}, sigma=2.0)
    assert alerts and alerts[0]["direction"] == "up"
    assert alerts[0]["level"] == "critical"


def test_feedback_priors():
    corrections = [
        {"action": "cause.rejected", "hypothesis_id": "tool_mark", "payload": {"hypotheses": [{"id": "tool_mark", "label": "Tool mark"}]}},
        {"action": "cause.rejected", "hypothesis_id": "tool_mark", "payload": {"hypotheses": [{"id": "tool_mark", "label": "Tool mark"}]}},
    ]
    priors = priors_from_corrections(corrections)
    assert priors["Tool mark"] == 0.76

    h = Hypothesis(
        id="tool_mark",
        label="Tool mark",
        category="process",
        summary="",
        score=0.5,
        confidence=0,
        rank=1,
        factors={"frequency": 1, "deviation": 1, "batch_match": 1, "similarity": 1, "recurrence": 1},
    )
    apply_priors([h], priors)
    assert h.factors.frequency == 0.76
    assert "historical rejections" in h.note
