from __future__ import annotations

import ast
import importlib.metadata
import importlib.util
from pathlib import Path

from laix import DecisionRequest, Layer, LayerDecision

from rootcause.laix_adapter import LAYER, QUALITY_POLICY
from rootcause.quality import Constraints, ExperienceState, QualityPolicy, Signal

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "rootcause"


def python_files() -> list[Path]:
    return sorted([*PACKAGE_ROOT.rglob("*.py"), *(ROOT / "tests").rglob("*.py")])


def test_local_rootcause_laix_package_is_gone():
    assert not (PACKAGE_ROOT / "laix").exists()
    assert not (PACKAGE_ROOT / "laix" / "__init__.py").exists()


def test_external_laix_package_is_installed():
    spec = importlib.util.find_spec("laix")
    assert spec is not None and spec.origin is not None
    installed = Path(spec.origin).resolve()
    assert PACKAGE_ROOT.resolve() not in installed.parents
    assert importlib.metadata.version("laix")


def test_no_rootcause_laix_imports_remain():
    offenders = []
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "rootcause.laix" or alias.name.startswith("rootcause.laix."):
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level and module == "laix":
                    offenders.append(f"{path.name}: from {'.' * node.level}{module}")
                elif module == "rootcause.laix" or module.startswith("rootcause.laix."):
                    offenders.append(f"{path.name}: from {module}")
    assert offenders == []


def test_quality_policy_is_the_selected_plugin():
    assert isinstance(QUALITY_POLICY, QualityPolicy)
    assert QUALITY_POLICY.name == "quality-intervention.v1"
    assert QUALITY_POLICY.version == "1.0"
    status = LAYER.status()
    assert status["policy"] == QUALITY_POLICY.name
    assert status["policyVersion"] == QUALITY_POLICY.version


def test_plugin_returns_layer_decisions_from_a_generic_request():
    signal = Signal(
        id="SIG-ISO-1",
        source="test",
        kind="ewma",
        line_id="line-6",
        parameter="hydrogen",
        value=2.1,
        baseline=1.2,
        z=3.0,
        severity="high",
        evidence_id="EV-01",
    )
    request = DecisionRequest(
        subject=signal.id,
        at="2026-10-31T00:00:00Z",
        attributes={
            "quality_signal": signal,
            "quality_state": ExperienceState(
                id="line-6", goal="prevent escape", phase="watch", confidence=0.6
            ),
            "quality_constraints": Constraints(max_interruptions_per_shift=10, interruptions_used=0),
        },
    )
    decisions = Layer(policy=QualityPolicy()).decide(request)
    assert len(decisions) == 1
    assert isinstance(decisions[0], LayerDecision)
    assert decisions[0].verb in {"wait", "ask", "guide", "act", "escalate"}
