"""RootCause's quality policy and quality data.

This package is the vertical half of the decision layer. It implements the LAIX policy plugin
contract and keeps the quality contracts, fixtures, bench and recurrence estimator. LAIX itself
stays generic and is installed as a pinned dependency.

The adapter ``rootcause.laix_adapter`` is the only place that knows both worlds.
"""

from .contracts import (
    Action,
    Constraints,
    Decision,
    DecisionRecord,
    ExperienceState,
    FollowUp,
    Outcome,
    Severity,
    Signal,
)
from .outcome import QualityOutcomeTracker, estimate_outcome
from .policy import QualityInterventionPolicy, QualityPolicy, record_for
from .schema import JSON_SCHEMA, schema

__all__ = [
    "Action",
    "Constraints",
    "Decision",
    "DecisionRecord",
    "ExperienceState",
    "FollowUp",
    "Outcome",
    "QualityInterventionPolicy",
    "QualityOutcomeTracker",
    "QualityPolicy",
    "Severity",
    "Signal",
    "JSON_SCHEMA",
    "estimate_outcome",
    "record_for",
    "schema",
]
