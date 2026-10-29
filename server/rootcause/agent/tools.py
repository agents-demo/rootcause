"""Plain-callable tools for the RootCause quality agent.

The builder decorates these with openjiuwen metadata. Application code never imports provider
decorators; this is the only place tools are turned into agent tools.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..engine.investigation import batch_linker, similar_cases, time_window_query
from ..models import Scenario

try:
    from openjiuwen.core.foundation.tool import tool as _tool
except Exception:  # pragma: no cover - host environment only
    def _tool(func=None, **_kwargs):  # type: ignore[misc]
        def wrap(fn):
            return fn

        return wrap(func) if func is not None else wrap


def make_tools(scenario: Scenario) -> list[Any]:
    """Build the case-scoped tool list."""

    def read_machine_window() -> str:
        """Read the 3-hour machine window around the defect, including z-scores and spec breaches."""
        rows = time_window_query(scenario.sensors, scenario.case.detected_at, hours=3)
        return json.dumps(rows, default=str)[:14000]

    def read_batch() -> str:
        """Read the material batch, supplier certificate, maintenance and linked case history."""
        data = batch_linker(scenario.batch, scenario.maintenance, scenario.history)
        return json.dumps(data, default=str)[:14000]

    def read_similar_cases() -> str:
        """Find the closest historical cases for this defect."""
        return json.dumps([h.model_dump() for h in similar_cases(scenario.history, limit=5)], default=str)

    def read_ranked_causes() -> str:
        """Read the evidence-ranked cause list. The engineer owns approval."""
        return json.dumps([h.model_dump() for h in scenario.hypotheses], default=str)

    def read_evidence() -> str:
        """Read evidence items with IDs, source, timestamp, strength and payload."""
        return json.dumps([e.model_dump() for e in scenario.evidence], default=str)

    def read_case_header() -> str:
        """Read the case identity, line, part, serial, defect, severity and provenance."""
        return json.dumps({"case": scenario.case.model_dump(), "provenance": scenario.provenance}, default=str)

    return [
        _tool(read_machine_window),
        _tool(read_batch),
        _tool(read_similar_cases),
        _tool(read_ranked_causes),
        _tool(read_evidence),
        _tool(read_case_header),
    ]


def make_tools_from_callables(funcs: list[Callable]) -> list[Any]:
    return [_tool(fn) for fn in funcs]
