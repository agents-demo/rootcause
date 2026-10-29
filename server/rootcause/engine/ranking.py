"""Evidence-weighted cause ranking.

The ranking is intentionally simple and auditable. Every factor is a 0..1 number that maps
back to a piece of evidence, which is what makes the "why is this first?" question answerable.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from copy import deepcopy

from ..models import Hypothesis

WEIGHTS = {
    "frequency": 0.28,
    "deviation": 0.30,
    "batch_match": 0.18,
    "similarity": 0.18,
    "recurrence": 0.06,
}

REJECTION_FACTOR = 0.16
# The "something else" bucket. It keeps the model honest: a short list of causes never gets
# 95% of the probability just because it is the only list on screen.
UNKNOWN_SCORE = 0.30


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def raw_score(h: Hypothesis) -> float:
    f = h.factors
    total = sum(WEIGHTS.values())
    weighted = (
        WEIGHTS["frequency"] * _clamp(f.frequency)
        + WEIGHTS["deviation"] * _clamp(f.deviation)
        + WEIGHTS["batch_match"] * _clamp(f.batch_match)
        + WEIGHTS["similarity"] * _clamp(f.similarity)
        + WEIGHTS["recurrence"] * _clamp(f.recurrence)
    )
    score = weighted / total
    if h.status == "rejected":
        score *= REJECTION_FACTOR
    if h.status == "manual":
        score = max(score, 0.34)
    return round(score, 4)


def _softmax_confidences(scores: Sequence[float]) -> list[float]:
    if not scores:
        return []
    # Scale the temperature to the winner: a strong, well-evidenced case may reach ~80%, never 99%.
    temperature = max(0.11, 0.22 * max(scores))
    exps = [math.exp(s / temperature) for s in scores]
    exps_unknown = math.exp(UNKNOWN_SCORE / temperature)
    total = sum(exps) + exps_unknown
    return [round(100 * e / total, 1) for e in exps]


def unknown_confidence(hypotheses: Iterable[Hypothesis]) -> float:
    """Probability mass left for 'none of these'."""
    return round(max(0.0, 100.0 - sum(h.confidence for h in hypotheses)), 1)


def rank_hypotheses(hypotheses: Iterable[Hypothesis], rejected: Iterable[str] | None = None) -> list[Hypothesis]:
    """Return ranked copies. Rejected causes keep their place but lose weight visibly."""
    rejected_set = set(rejected or [])
    ranked = [deepcopy(h) for h in hypotheses]
    for h in ranked:
        if h.id in rejected_set:
            h.status = "rejected"
        elif h.status == "rejected":
            # allow the caller to pass a rejection set only, keeping pack data clean
            h.status = "proposed"
    for h in ranked:
        h.score = raw_score(h)
    ranked.sort(key=lambda h: (-h.score, h.label))
    confidences = _softmax_confidences([h.score for h in ranked])
    for i, (h, c) in enumerate(zip(ranked, confidences, strict=True), start=1):
        h.rank = i
        h.confidence = c
    return ranked


def top_cause(hypotheses: Iterable[Hypothesis]) -> Hypothesis | None:
    ranked = sorted(hypotheses, key=lambda h: (-h.score, h.label))
    return ranked[0] if ranked else None


def explain(h: Hypothesis) -> list[dict[str, float | str]]:
    """Factor breakdown for the UI, in display order."""
    labels = {
        "frequency": "Known failure mode frequency",
        "deviation": "Machine deviation magnitude",
        "batch_match": "Batch / material match",
        "similarity": "Similar-case match",
        "recurrence": "Recurrence on this line",
    }
    factors = h.factors.model_dump()
    return [
        {"key": k, "label": labels[k], "value": round(float(factors[k]), 3), "weight": WEIGHTS[k]}
        for k in WEIGHTS
    ]
