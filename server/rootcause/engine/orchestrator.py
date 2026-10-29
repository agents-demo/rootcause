"""Agent orchestration for the investigation.

The demo is deterministic: the same case produces the same trace. Each step is a tool call with
citable evidence. An LLM can sit on top of this in a pilot, but it cannot approve a cause.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import Hypothesis, Scenario
from .investigation import batch_linker, similar_cases, time_window_query
from .ranking import rank_hypotheses


def _step(
    n: int,
    agent: str,
    tool: str,
    title: str,
    detail: str,
    evidence: list[str],
    status: str = "done",
    ms: int = 220,
) -> dict[str, Any]:
    return {
        "step": n,
        "agent": agent,
        "tool": tool,
        "title": title,
        "detail": detail,
        "status": status,
        "evidence": evidence,
        "ms": ms,
    }


def run_investigation(scenario: Scenario, rejected: Iterable[str] | None = None) -> dict[str, Any]:
    """Gather facts, rank causes and return the full investigation.

    Rejections are applied before ranking, so the same function produces the trust beat.
    """
    rejected_set = set(rejected or [])
    case = scenario.case
    window = time_window_query(scenario.sensors, case.detected_at, hours=3)
    out_of_spec = [w for w in window if w["out_of_spec"] > 0]
    batch = batch_linker(scenario.batch, scenario.maintenance, scenario.history)
    similar = similar_cases(scenario.history, limit=4)

    hypotheses = rank_hypotheses(scenario.hypotheses, rejected=rejected_set)

    findings = [f for f in scenario.findings if f.evidence_id]
    trace: list[dict[str, Any]] = [
        _step(
            1,
            "Intake",
            "detector.detect",
            f"Defect confirmed: {case.defect_type}",
            f"Camera confidence {case.detection_confidence:.2f}. Case {case.id} opened on {case.station}.",
            [scenario.evidence[0].id] if scenario.evidence else [],
            ms=240,
        ),
        _step(
            2,
            "Data",
            "opcua.read_window",
            f"Pulled {len(window)} machine parameters",
            f"{len(out_of_spec)} parameters out of spec in the 3-hour window around the defect.",
            [e.id for e in scenario.evidence if e.kind == "chart"],
            ms=610,
        ),
        _step(
            3,
            "Data",
            "mes.batch",
            f"Linked batch {batch['batch']['id']}",
            f"Batch flag: {batch['flag']}. {len(batch['batch_cases'])} prior cases on this exact batch.",
            [e.id for e in scenario.evidence if e.kind == "record"][:1],
            ms=180,
        ),
        _step(
            4,
            "Data",
            "cmms.history",
            f"Found {len(batch['maintenance'])} maintenance events",
            "Recent maintenance is included when it can explain a process change.",
            [e.id for e in scenario.evidence if e.kind == "record"],
            ms=150,
        ),
        _step(
            5,
            "Reasoner",
            "similar.search",
            f"Matched {len(similar)} historical cases",
            "Similarity uses cause, material batch and time-to-resolution features.",
            [e.id for e in scenario.evidence if e.kind == "similar"],
            ms=320,
        ),
        _step(
            6,
            "Reasoner",
            "cause.rank",
            f"Ranked {len(hypotheses)} causes",
            f"Leading cause: {hypotheses[0].label} at {hypotheses[0].confidence:.0f}%. "
            "Subsurface evidence is still unreviewed.",
            [e.id for e in scenario.evidence if e.kind == "image"][:1],
            ms=430,
        ),
    ]

    for i, hid in enumerate(sorted(rejected_set), start=7):
        rejected_hyp = next((h for h in scenario.hypotheses if h.id == hid), None)
        label = rejected_hyp.label if rejected_hyp else hid
        trace.append(
            _step(
                i,
                "Engineer",
                "engineer.reject",
                f"Rejected: {label}",
                "The engineer rejected this cause; its weight is reduced and the ranking is recomputed.",
                [],
                ms=1200,
            )
        )
        top = hypotheses[0]
        trace.append(
            _step(
                i + 1,
                "Reasoner",
                "cause.rerank",
                f"Re-ranked: {top.label} now leads",
                f"{top.label} at {top.confidence:.0f}% confidence. The correction is saved to the case.",
                top.evidence_ids[:2],
                ms=520,
            )
        )

    trace.append(
        _step(
            len(trace) + 1,
            "Guard",
            "engineer.check",
            "Engineer sign-off required",
            "No cause is approved automatically. Accept or reject the remaining candidates.",
            [],
            status="waiting",
            ms=0,
        )
    )

    chain = scenario.chain.model_copy()
    if hypotheses:
        chain.confidence = round(min(0.95, hypotheses[0].confidence / 100 + 0.36), 2)

    return {
        "case": case,
        "window": window,
        "batch": batch,
        "similar": [s.model_dump() for s in similar],
        "hypotheses": [h.model_dump() for h in hypotheses],
        "chain": chain.model_dump(),
        "trace": trace,
        "findings": [f.model_dump() for f in findings],
    }


def reorder_rejection(scenario: Scenario, rejected: list[str]) -> list[Hypothesis]:
    return rank_hypotheses(scenario.hypotheses, rejected=rejected)
