"""Quality contracts for the RootCause policy plugin.

These dataclasses are the vertical half of the decision layer. They stay in RootCause; LAIX receives
them only as opaque values inside ``DecisionRequest.attributes``. The generic LAIX contract and the
``Layer`` live in the installed ``laix`` package.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Action = Literal["wait", "ask", "guide", "act", "verify", "escalate"]
Severity = Literal["info", "warning", "high", "critical"]


@dataclass(frozen=True)
class Signal:
    """One observation from the app. Cheap detectors produce these; deep models are optional."""

    id: str
    source: str
    kind: str
    line_id: str
    parameter: str
    value: float | None = None
    baseline: float | None = None
    z: float | None = None
    at: str | None = None
    severity: Severity = "warning"
    evidence_id: str = ""
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_generic(self) -> dict[str, Any]:
        """A domain-free view of the signal for the portable contract.

        Existing fields stay for the app and tests. ``subject`` is the app's line identifier and
        ``kind`` is the observed parameter; the numeric evidence moves into ``attributes``.
        """
        return {
            "subject": self.line_id,
            "kind": self.parameter,
            "attributes": {"value": self.value, "baseline": self.baseline, "z": self.z},
            "evidence_id": self.evidence_id,
        }


@dataclass(frozen=True)
class ExperienceState:
    """What the app knows about the live situation, not the chat history."""

    id: str
    goal: str
    phase: str
    beliefs: Mapping[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    open_watch_keys: Sequence[str] = ()
    actions: Sequence[str] = ()
    expires_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Constraints:
    """Latency, cost, interruption tolerance and risk limits supplied by the app."""

    max_interruptions_per_shift: int = 10
    interruptions_used: int = 0
    interrupt_cost: float = 1.0
    miss_cost: float = 10.0
    latency_budget_ms: int = 1000
    risk_ceiling: Severity = "critical"
    require_approval: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Decision:
    action: Action
    confidence: float
    why: Sequence[str]
    evidence_ids: Sequence[str] = ()
    expected_cost: float = 0.0
    wait_cost: float = 0.0
    requires_approval: bool = False
    policy: str = "quality-intervention.v1"
    state_id: str = ""
    signal_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionRecord:
    """The LAIX 'decision record' addition: what, why, evidence, confidence and approval state."""

    id: str
    at: str
    state_id: str
    signal_id: str
    action: Action
    confidence: float
    why: Sequence[str]
    evidence_ids: Sequence[str]
    inputs_digest: str
    actor: str
    approval: Literal["not_required", "pending", "approved", "rejected"] = "not_required"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FollowUp:
    """What happened after an action, inside an agreed window."""

    action_id: str
    case_id: str
    at: str
    recurrence: bool
    line_id: str = ""
    defect: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Outcome:
    action_id: str
    action: str
    treated: int
    recurred: int
    baseline_rate: float
    treated_rate: float
    effect: float
    confidence: float
    window_days: int
    note: str
    causal: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
