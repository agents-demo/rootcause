"""Small LAIX-Bench-shaped fixture set for the quality intervention policy.

Each case is one decision an expert should agree with. It is not a full benchmark; it is the seed of
one, and the same cases can be replayed by the LAIX runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Constraints, ExperienceState, Signal


@dataclass(frozen=True)
class BenchCase:
    id: str
    expected: str
    signal: Signal
    state: ExperienceState
    constraints: Constraints


def _state(**overrides) -> ExperienceState:
    base = {"id": "line-6", "goal": "prevent the next escape", "phase": "watch", "confidence": 0.6}
    base.update(overrides)
    return ExperienceState(**base)


def _constraints(**overrides) -> Constraints:
    base = {
        "max_interruptions_per_shift": 10,
        "interruptions_used": 1,
        "interrupt_cost": 1.0,
        "miss_cost": 10.0,
        "require_approval": True,
    }
    base.update(overrides)
    return Constraints(**base)


def _signal(**overrides) -> Signal:
    base = {
        "id": "SIG",
        "source": "fixture",
        "kind": "ewma",
        "line_id": "line-6",
        "parameter": "hydrogen",
        "value": 2.1,
        "baseline": 1.2,
        "z": 2.0,
        "at": "2026-10-31T00:00:00Z",
        "severity": "warning",
        "evidence_id": "EV-04",
    }
    base.update(overrides)
    return Signal(**base)


def cases() -> list[BenchCase]:
    return [
        BenchCase("high-hydrogen", "act", _signal(id="high", severity="high", z=3.2), _state(), _constraints()),
        BenchCase("weak-drift", "wait", _signal(id="weak", severity="info", z=0.3), _state(), _constraints()),
        BenchCase("thin-evidence", "ask", _signal(id="thin", severity="warning", z=0.1), _state(), _constraints()),
        BenchCase("medium-trend", "guide", _signal(id="medium", severity="warning", z=2.0), _state(), _constraints()),
        BenchCase("critical-hydrogen", "escalate", _signal(id="critical", severity="critical", z=4.0), _state(), _constraints()),
        BenchCase(
            "budget-spent",
            "wait",
            _signal(id="budget", severity="high", z=3.2),
            _state(),
            _constraints(max_interruptions_per_shift=2, interruptions_used=2),
        ),
        BenchCase(
            "already-open",
            "wait",
            _signal(id="duplicate"),
            _state(open_watch_keys=("line-6:hydrogen",)),
            _constraints(),
        ),
    ]

def contract_cases() -> list[BenchCase]:
    """Additional labelled cases for the frozen policy contract; not part of the bench score."""
    return [
        BenchCase(
            "critical-thin",
            "escalate",
            _signal(id="critical-thin", severity="critical", z=0.0, baseline=None),
            _state(),
            _constraints(),
        ),
        BenchCase(
            "critical-budget",
            "escalate",
            _signal(id="critical-budget", severity="critical", z=3.0),
            _state(),
            _constraints(max_interruptions_per_shift=2, interruptions_used=2),
        ),
        BenchCase(
            "info-strong",
            "guide",
            _signal(id="info-strong", severity="info", z=3.0),
            _state(),
            _constraints(),
        ),
        BenchCase(
            "warning-no-baseline",
            "guide",
            _signal(id="warning-no-baseline", severity="warning", z=3.0, baseline=None),
            _state(),
            _constraints(),
        ),
        BenchCase(
            "high-budget",
            "wait",
            _signal(id="high-budget", severity="high", z=3.2),
            _state(),
            _constraints(max_interruptions_per_shift=2, interruptions_used=2),
        ),
    ]
