"""Language-neutral contract for the LAIX quality decision layer.

The Python dataclasses are the runtime; this schema is the boundary for a TypeScript SDK or another
service. It describes the same objects without importing Python.
"""

from __future__ import annotations

import copy
from typing import Any

ACTION = ["wait", "ask", "guide", "act", "verify", "escalate"]
SEVERITY = ["info", "warning", "high", "critical"]

JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://openjiuwen.example/laix/quality-decision.schema.json",
    "title": "LAIX quality decision contract v1",
    "type": "object",
    "$defs": {
        "Signal": {
            "type": "object",
            "required": ["id", "source", "kind", "line_id", "parameter"],
            "properties": {
                "id": {"type": "string"},
                "source": {"type": "string"},
                "kind": {"type": "string"},
                "line_id": {"type": "string"},
                "parameter": {"type": "string"},
                "value": {"type": ["number", "null"]},
                "baseline": {"type": ["number", "null"]},
                "z": {"type": ["number", "null"]},
                "at": {"type": ["string", "null"]},
                "severity": {"enum": SEVERITY},
                "evidence_id": {"type": "string"},
                "attributes": {"type": "object", "additionalProperties": True},
            },
            "additionalProperties": False,
        },
        "ExperienceState": {
            "type": "object",
            "required": ["id", "goal", "phase"],
            "properties": {
                "id": {"type": "string"},
                "goal": {"type": "string"},
                "phase": {"type": "string"},
                "beliefs": {"type": "object", "additionalProperties": {"type": "number"}},
                "confidence": {"type": "number"},
                "open_watch_keys": {"type": "array", "items": {"type": "string"}},
                "actions": {"type": "array", "items": {"type": "string"}},
                "expires_at": {"type": ["string", "null"]},
            },
            "additionalProperties": False,
        },
        "Constraints": {
            "type": "object",
            "properties": {
                "max_interruptions_per_shift": {"type": "integer", "minimum": 0},
                "interruptions_used": {"type": "integer", "minimum": 0},
                "interrupt_cost": {"type": "number", "minimum": 0},
                "miss_cost": {"type": "number", "minimum": 0},
                "latency_budget_ms": {"type": "integer", "minimum": 0},
                "risk_ceiling": {"enum": SEVERITY},
                "require_approval": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "Decision": {
            "type": "object",
            "required": ["action", "confidence", "why"],
            "properties": {
                "action": {"enum": ACTION},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "why": {"type": "array", "items": {"type": "string"}},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
                "expected_cost": {"type": "number"},
                "wait_cost": {"type": "number"},
                "requires_approval": {"type": "boolean"},
                "policy": {"type": "string"},
                "state_id": {"type": "string"},
                "signal_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "DecisionRecord": {
            "type": "object",
            "required": ["id", "at", "state_id", "signal_id", "action", "confidence", "why", "inputs_digest", "actor"],
            "properties": {
                "id": {"type": "string"},
                "at": {"type": "string"},
                "state_id": {"type": "string"},
                "signal_id": {"type": "string"},
                "action": {"enum": ACTION},
                "confidence": {"type": "number"},
                "why": {"type": "array", "items": {"type": "string"}},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
                "inputs_digest": {"type": "string"},
                "actor": {"type": "string"},
                "approval": {"enum": ["not_required", "pending", "approved", "rejected"]},
            },
            "additionalProperties": False,
        },
        "FollowUp": {
            "type": "object",
            "required": ["action_id", "case_id", "at", "recurrence"],
            "properties": {
                "action_id": {"type": "string"},
                "case_id": {"type": "string"},
                "at": {"type": "string"},
                "recurrence": {"type": "boolean"},
                "line_id": {"type": "string"},
                "defect": {"type": "string"},
                "notes": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "Outcome": {
            "type": "object",
            "required": ["action_id", "action", "treated", "recurred", "baseline_rate", "treated_rate", "effect", "confidence", "window_days", "note"],
            "properties": {
                "action_id": {"type": "string"},
                "action": {"type": "string"},
                "treated": {"type": "integer"},
                "recurred": {"type": "integer"},
                "baseline_rate": {"type": "number"},
                "treated_rate": {"type": "number"},
                "effect": {"type": "number"},
                "confidence": {"type": "number"},
                "window_days": {"type": "integer"},
                "note": {"type": "string"},
                "causal": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
}


def schema() -> dict[str, Any]:
    """Return a copy so callers cannot mutate the module constant."""
    return copy.deepcopy(JSON_SCHEMA)
