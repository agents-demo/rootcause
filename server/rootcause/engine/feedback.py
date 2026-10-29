"""Feedback loop: engineer corrections adjust the next ranking iteration.

The correction stays local. A label rejected repeatedly on a line gets a small prior penalty on
that line; it never disappears from the list, and the evidence can always bring it back.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

PENALTY_PER_REJECTION = 0.12
MAX_PENALTY = 0.45


def priors_from_corrections(corrections: Iterable[dict[str, Any]], *, line_id: str = "") -> dict[str, float]:
    counts: dict[str, int] = defaultdict(int)
    for correction in corrections:
        if correction.get("action") != "cause.rejected":
            continue
        payload = correction.get("payload") or {}
        hypotheses = payload.get("hypotheses") or []
        hid = correction.get("hypothesis_id")
        label = ""
        for h in hypotheses:
            if h.get("id") == hid:
                label = h.get("label", "")
                break
        if not label:
            label = hid or "unknown"
        counts[label] += 1
    return {
        label: max(1.0 - MAX_PENALTY, 1.0 - PENALTY_PER_REJECTION * count)
        for label, count in counts.items()
    }


def apply_priors(hypotheses: Iterable[Any], priors: dict[str, float]) -> None:
    for h in hypotheses:
        factor = priors.get(h.label)
        if not factor:
            continue
        for name in ("frequency", "deviation", "batch_match", "similarity", "recurrence"):
            setattr(h.factors, name, round(getattr(h.factors, name) * factor, 4))
        h.note = (h.note + " ").strip() + f" Prior reduced after {round((1 - factor) * 100)}% historical rejections."
