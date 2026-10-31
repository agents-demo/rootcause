"""Run the policy over the fixture set and report decision agreement.

    python -m rootcause.laix.bench

This is the seed of LAIX-Bench for quality decisions: an expert-annotated action per case, replayed
through the same policy the app uses. It measures agreement, not outcome improvement.
"""

from __future__ import annotations

import json
from typing import Any

from .fixtures import cases
from .intervention import QualityInterventionPolicy


def run() -> dict[str, Any]:
    policy = QualityInterventionPolicy()
    results: list[dict[str, Any]] = []
    for case in cases():
        decision = policy.decide(case.signal, case.state, case.constraints)
        results.append(
            {
                "id": case.id,
                "expected": case.expected,
                "action": decision.action,
                "confidence": decision.confidence,
                "pass": decision.action == case.expected,
                "why": list(decision.why),
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
