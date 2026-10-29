"""Investigation primitives: time windows, batch linking and similar-case search."""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from ..models import BatchRecord, HistoricalCase, MaintenanceRecord, SensorSeries


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def time_window_query(sensors: Iterable[SensorSeries], defect_at: str, hours: float = 3.0) -> list[dict[str, Any]]:
    """Return window statistics around the defect timestamp.

    A pilot reads the machine's own history; the demo uses the preloaded series but applies the
    same windowing maths so the result is computed, not hard-coded.
    """
    anchor = _parse(defect_at)
    start = anchor.timestamp() - hours * 3600
    end = anchor.timestamp() + hours * 3600
    out: list[dict[str, Any]] = []
    for s in sensors:
        window = [p for p in s.points if start <= _parse(p.t).timestamp() <= end]
        values = [p.v for p in window]
        if not values:
            continue
        mean = sum(values) / len(values)
        z = (mean - s.baseline) / s.std if s.std else 0.0
        out.append(
            {
                "id": s.id,
                "name": s.name,
                "unit": s.unit,
                "baseline": s.baseline,
                "spec_low": s.spec_low,
                "spec_high": s.spec_high,
                "mean": round(mean, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "std": s.std,
                "z": round(z, 2),
                "out_of_spec": sum(
                    1
                    for v in values
                    if (s.spec_low is not None and v < s.spec_low) or (s.spec_high is not None and v > s.spec_high)
                ),
                "samples": len(values),
                "points": [{"t": p.t, "v": p.v} for p in window],
            }
        )
    return out


def batch_linker(
    batch: BatchRecord,
    maintenance: Iterable[MaintenanceRecord],
    history: Iterable[HistoricalCase],
) -> dict[str, Any]:
    """Join a case to its material batch, maintenance context and historical siblings."""
    batch_cases = [h for h in history if h.batch == batch.id]
    supplier_cases = [h for h in history if h.batch[:2] == batch.id[:2]]
    recent_maintenance = sorted(maintenance, key=lambda m: m.days_before_defect)[:3]
    return {
        "batch": batch.model_dump(),
        "batch_cases": [h.model_dump() for h in batch_cases],
        "supplier_cases": [h.model_dump() for h in supplier_cases],
        "maintenance": [m.model_dump() for m in recent_maintenance],
        "flag": "exception"
        if (batch.notes and "exception" in batch.notes.lower()) or (batch.moisture_pct or 0) > 0.12
        else "normal",
    }


def _feature_vector(h: HistoricalCase) -> list[float]:
    # A small, stable feature space. In a pilot these numbers come from the case record.
    return [h.similarity, 1.0 if h.batch else 0.0, math.log1p(h.resolution_hours)]


def similar_cases(history: Iterable[HistoricalCase], query: HistoricalCase | None = None, limit: int = 5) -> list[HistoricalCase]:
    cases = list(history)
    if query is None:
        return sorted(cases, key=lambda h: (-h.similarity, h.at))[:limit]
    q = _feature_vector(query)
    scored: list[tuple[float, HistoricalCase]] = []
    for h in cases:
        if h.id == query.id:
            continue
        v = _feature_vector(h)
        dot = sum(a * b for a, b in zip(q, v, strict=True))
        na = math.sqrt(sum(a * a for a in q)) or 1.0
        nb = math.sqrt(sum(b * b for b in v)) or 1.0
        scored.append((dot / (na * nb), h))
    scored.sort(key=lambda pair: -pair[0])
    return [h.model_copy(update={"similarity": round(score, 3)}) for score, h in scored[:limit]]


def evidence_package(
    *,
    sensors: list[dict[str, Any]],
    batch: dict[str, Any],
    similar: list[HistoricalCase],
    maintenance: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the evidence list a cause card can cite."""
    package: list[dict[str, Any]] = []
    for s in sensors:
        if abs(s["z"]) >= 2:
            package.append(
                {
                    "kind": "chart",
                    "title": f"{s['name']} deviated {s['z']:+.1f}σ",
                    "detail": f"Window mean {s['mean']} {s['unit']} against a {s['baseline']} {s['unit']} baseline.",
                    "source": f"OPC-UA / {s['id']}",
                    "strength": min(1.0, abs(s["z"]) / 8),
                }
            )
    if batch.get("notes") or batch.get("moisture_pct") or batch.get("hydrogen_ppm"):
        package.append(
            {
                "kind": "record",
                "title": f"Batch {batch['id']} has a material exception",
                "detail": batch.get("notes") or "Material record contains a limit exception.",
                "source": f"MES / {batch['id']}",
                "strength": 0.8,
            }
        )
    for h in similar[:2]:
        package.append(
            {
                "kind": "similar",
                "title": f"{h.id} resolved to {h.cause}",
                "detail": h.notes,
                "source": "Case history",
                "strength": h.similarity,
            }
        )
    for m in maintenance[:2]:
        package.append(
            {
                "kind": "record",
                "title": m["kind"],
                "detail": m["note"],
                "source": f"CMMS / {m['id']}",
                "strength": 0.5,
            }
        )
    return package
