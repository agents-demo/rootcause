"""Run the policy over the fixture set and report decision agreement.

    python -m rootcause.quality.bench

This is the seed of a quality policy bench: an expert-annotated action per case, replayed through the
same LAIX plugin the app uses. It measures agreement, not outcome improvement.
"""

from __future__ import annotations

import json
from typing import Any

from laix import DecisionRequest, Layer

from .fixtures import cases
from .policy import QualityPolicy


def run() -> dict[str, Any]:
    policy = QualityPolicy()
    layer = Layer(policy=policy)
    results: list[dict[str, Any]] = []
    for case in cases():
        request = DecisionRequest(
            subject=case.signal.id,
            at=case.signal.at or "",
            attributes={
                "quality_signal": case.signal,
                "quality_state": case.state,
                "quality_constraints": case.constraints,
            },
        )
        decision = layer.decide(request)[0]
        results.append(
            {
                "id": case.id,
                "expected": case.expected,
                "action": decision.verb,
                "confidence": decision.confidence,
                "pass": decision.verb == case.expected,
                "why": list(decision.rationale.split("\n")),
            }
        )
    passed = sum(1 for row in results if row["pass"])
    acted = [row for row in results if row["action"] in {"ask", "guide", "act", "escalate"}]
    agreement = round(passed / len(results), 3) if results else 0.0
    precision = round(sum(1 for row in acted if row["pass"]) / len(acted), 3) if acted else 0.0
    return {
        "policy": policy.name,
        "cases": len(results),
        "pass": passed,
        "fail": len(results) - passed,
        "agreement": agreement,
        "intervention_precision": precision,
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
