"""LAIX sub-module extracted from RootCause.

The package is portable: no RootCause, FastAPI, SQLite or agent imports. RootCause wires it through
``rootcause.laix_adapter``; LAIX can take this folder as-is.

Public API:

- ``Signal``, ``ExperienceState``, ``Constraints``, ``Decision``, ``DecisionRecord``, ``Outcome``
- ``QualityInterventionPolicy`` — wait / ask / guide / act / verify / escalate
- ``QualityOutcomeTracker``, ``estimate_outcome`` — did the action help?
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
from .intervention import QualityInterventionPolicy, decision_summary
from .outcome import QualityOutcomeTracker, estimate_outcome
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
    "Severity",
    "Signal",
    "JSON_SCHEMA",
    "decision_summary",
    "estimate_outcome",
    "schema",
]
