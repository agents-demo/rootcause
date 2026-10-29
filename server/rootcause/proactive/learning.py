"""Outcome-weighted pattern priors.

A pattern that repeatedly produces false alarms on a line should not keep the same risk weight. The
prior is deliberately gentle: evidence can still bring it back, and a human reviews the pattern.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from ..models import WatchCase


def pattern_priors(watches: Iterable[WatchCase]) -> dict[str, float]:
    counts: dict[str, list[bool]] = defaultdict(list)
    for w in watches:
        if w.useful is not None:
            counts[w.pattern_id].append(bool(w.useful))
    return {
        pattern: round(1.0 - 0.12 * (1 - sum(values) / len(values)), 3)
        for pattern, values in counts.items()
    }


def apply_pattern_prior(risk: float, pattern_id: str, priors: dict[str, float]) -> float:
    return round(max(0.05, min(0.99, risk * priors.get(pattern_id, 1.0))), 3)
