from __future__ import annotations

from pathlib import Path

import pytest

from rootcause.agent.jiuwen_runtime import OpenJiuwenRuntime
from rootcause.demo.build_pack import build_pack
from rootcause.npu.onnx_backend import OnnxBroker
from rootcause.npu.service import _backend as npu_backend


def test_agent_reports_unconfigured_without_fake_fallback(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_BASE", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    runtime = OpenJiuwenRuntime(build_pack().scenarios)
    status = runtime.status()
    assert status.backend == "openjiuwen"
    assert status.configured is False
    assert "not configured" in status.detail or "not installed" in status.detail


def test_onnx_broker_refuses_missing_model(tmp_path: Path):
    broker = OnnxBroker(tmp_path / "defect.onnx")
    health = broker.health()
    assert health["ready"] is False
    with pytest.raises(FileNotFoundError):
        broker.infer(tmp_path / "frame.png")


def test_npu_backend_is_explicit(monkeypatch):
    monkeypatch.delenv("ROOTCAUSE_NPU_SIMULATE", raising=False)
    monkeypatch.setenv("ROOTCAUSE_NPU_BACKEND", "onnx")
    assert npu_backend() == "onnx"
    monkeypatch.setenv("ROOTCAUSE_NPU_BACKEND", "ascend")
    assert npu_backend() == "ascend"
    monkeypatch.setenv("ROOTCAUSE_NPU_SIMULATE", "1")
    assert npu_backend() == "simulated"
