"""Proactive signal detection.

Pure, deterministic functions. The demo ships curated signals; the API can also scan the seeded
sensor series and produce candidates with the same maths a pilot would use.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable
from typing import Any

from ..models import RiskSignal, SensorSeries


def ewma(values: Iterable[float], alpha: float = 0.3) -> list[float]:
    out: list[float] = []
    current: float | None = None
    for v in values:
        current = v if current is None else alpha * v + (1 - alpha) * current
        out.append(current)
    return out


def cusum(values: Iterable[float], target: float, *, k: float = 0.5, h: float = 5.0, sigma: float = 1.0) -> dict[str, float]:
    """Two-sided tabular CUSUM, returned as final statistics and a first-crossing index."""
    high = low = 0.0
    high_at = low_at = -1
    for i, v in enumerate(values):
        z = (v - target) / (sigma or 1.0)
        high = max(0.0, high + z - k)
        low = min(0.0, low + z + k)
        if high > h and high_at < 0:
            high_at = i
        if low < -h and low_at < 0:
            low_at = i
    return {"high": round(high, 3), "low": round(low, 3), "high_at": high_at, "low_at": low_at}


def change_point(values: Iterable[float]) -> dict[str, float | int]:
    """Largest mean shift between the first and last half of the window."""
    vals = list(values)
    if len(vals) < 8:
        return {"shift": 0.0, "index": -1, "sigma": 0.0}
    best = 0.0
    best_i = -1
    overall = statistics.pstdev(vals) or 1.0
    for i in range(3, len(vals) - 3):
        left = vals[:i]
        right = vals[i:]
        shift = abs(statistics.fmean(right) - statistics.fmean(left)) / overall
        if shift > best:
            best = shift
            best_i = i
    return {"shift": round(best, 3), "index": best_i, "sigma": round(overall, 4)}


def recent_deviation(series: SensorSeries, *, window: int = 8) -> float:
    values = [p.v for p in series.points[-window:]]
    if not values or not series.std:
        return 0.0
    return (statistics.fmean(values) - series.baseline) / series.std


def severity_for(z: float) -> str:
    a = abs(z)
    if a >= 5:
        return "critical"
    if a >= 3.5:
        return "high"
    if a >= 2.5:
        return "warning"
    return "info"


def scan_sensor(series: SensorSeries, *, line_id: str, at: str) -> RiskSignal | None:
    values = [p.v for p in series.points]
    if len(values) < 12 or not series.std:
        return None
    z = recent_deviation(series)
    peak_z = max(((v - series.baseline) / series.std for v in values), key=abs)
    smooth = ewma(values)
    ewma_z = (smooth[-1] - series.baseline) / series.std
    ewma_peak = max(((v - series.baseline) / series.std for v in smooth), key=abs)
    cp = change_point(values)
    level = max(abs(z), abs(peak_z), abs(ewma_z), abs(ewma_peak), float(cp["shift"]))
    if level < 2.5:
        return None
    kind = "spc"
    detail = f"{series.name} peaks {peak_z:+.1f}σ from its baseline in the window."
    if abs(ewma_peak) >= abs(peak_z) and abs(ewma_peak) >= 2.5:
        kind = "ewma"
        detail = f"EWMA of {series.name} peaks {ewma_peak:+.1f}σ from baseline."
    if float(cp["shift"]) >= 2.5 and float(cp["shift"]) > abs(peak_z):
        kind = "change_point"
        detail = f"{series.name} shows a step change of {cp['shift']}σ at sample {cp['index']}."
    if abs(peak_z) < 2.5 and kind == "spc":
        return None
    return RiskSignal(
        id=f"SCAN-{series.id}",
        kind=kind,  # type: ignore[arg-type]
        at=at,
        line_id=line_id,
        parameter=series.name,
        value=round(statistics.fmean(values[-8:]), 4),
        baseline=series.baseline,
        z=round(max(z, peak_z, ewma_z, ewma_peak, key=abs), 2),
        severity=severity_for(level),  # type: ignore[arg-type]
        detail=detail,
    )


def scan_scenario(scenario: dict[str, Any]) -> list[RiskSignal]:
    line_id = scenario["case"]["line_id"]
    at = scenario["case"]["detected_at"]
    signals: list[RiskSignal] = []
    for series in scenario.get("sensors", []):
        from ..models import SensorSeries

        sig = scan_sensor(SensorSeries.model_validate(series), line_id=line_id, at=at)
        if sig:
            signals.append(sig)

    batch = scenario.get("batch", {})
    limit_breach = (batch.get("moisture_pct") or 0) > 0.12 or (batch.get("hydrogen_ppm") or 0) > 1.4
    if limit_breach or "exception" in (batch.get("notes") or "").lower():
        signals.append(
            RiskSignal(
                id=f"BATCH-{batch.get('id')}",
                kind="batch",
                at=at,
                line_id=line_id,
                parameter=f"Batch {batch.get('id')}",
                value=batch.get("moisture_pct") or batch.get("hydrogen_ppm"),
                baseline=0.12 if batch.get("moisture_pct") is not None else 1.4,
                z=3.0,
                severity="high",
                detail=f"Material batch {batch.get('id')} carries a limit exception or a supplier deviation.",
            )
        )

    received = batch.get("received")
    if received:
        try:
            from datetime import datetime

            age_days = (datetime.fromisoformat(at.replace("Z", "+00:00")) - datetime.fromisoformat(received.replace("Z", "+00:00"))).days
            if age_days <= 7:
                signals.append(
                    RiskSignal(
                        id=f"SETUP-{batch.get('id')}",
                        kind="setup",
                        at=at,
                        line_id=line_id,
                        parameter=f"New batch {batch.get('id')}",
                        severity="info",
                        detail=f"New material lot opened {age_days} day(s) ago; a setup watch window is open for the first production run.",
                    )
                )
        except ValueError:
            pass

    for record in scenario.get("maintenance", []):
        if record.get("days_before_defect", 99) <= 15:
            signals.append(
                RiskSignal(
                    id=f"MAINT-{record.get('id')}",
                    kind="maintenance",
                    at=at,
                    line_id=line_id,
                    parameter=record.get("kind", "Maintenance"),
                    severity="warning",
                    detail=f"{record.get('kind')} on {record.get('machine')} {record.get('days_before_defect')} days before the reference event. Post-repair validation: {record.get('note', '')}",
                )
            )
            break
    return signals


def scan_pack(pack: dict[str, Any], *, at: str, coverage: list[dict[str, Any]] | None = None) -> list[RiskSignal]:
    signals: list[RiskSignal] = []
    for scenario in pack.get("scenarios", []):
        signals.extend(scan_scenario(scenario))
    for row in coverage or pack.get("proactive", {}).get("coverage", []):
        if row.get("status") in {"degraded", "blind"} or float(row.get("pct", 1)) < 0.95:
            signals.append(
                RiskSignal(
                    id=f"COV-{row.get('line_id')}",
                    kind="data_quality",
                    at=at,
                    line_id=row.get("line_id", ""),
                    parameter="Source coverage",
                    value=float(row.get("pct", 0)) * 100,
                    baseline=95.0,
                    z=None,
                    severity="warning" if row.get("status") == "degraded" else "critical",
                    detail=f"Coverage {float(row.get('pct', 0)) * 100:.0f}%. Stale: {', '.join(row.get('stale', [])) or 'unknown'}.",
                )
            )
    return signals


def signal_risk(signals: Iterable[RiskSignal]) -> float:
    weights = {"info": 0.12, "warning": 0.28, "high": 0.46, "critical": 0.62}
    score = 0.0
    for s in signals:
        score += weights.get(s.severity, 0.2)
    return round(min(0.99, score), 3)


def confidence_for(signals: Iterable[RiskSignal], pattern_precision: float = 0.6) -> float:
    count = len(list(signals))
    return round(min(95.0, 45 + 10 * count + 20 * pattern_precision), 1)


def dedupe(signals: Iterable[RiskSignal]) -> list[RiskSignal]:
    """Keep the strongest signal per line/parameter."""
    order = {"info": 0, "warning": 1, "high": 2, "critical": 3}
    best: dict[tuple[str, str], RiskSignal] = {}
    for s in signals:
        key = (s.line_id, s.parameter)
        if key not in best or order.get(s.severity, 0) > order.get(best[key].severity, 0):
            best[key] = s
    return sorted(best.values(), key=lambda s: (-order.get(s.severity, 0), s.parameter))


def quality_baseline(values: Iterable[float]) -> dict[str, float]:
    vals = [float(v) for v in values]
    if not vals:
        return {"mean": 0.0, "std": 0.0}
    return {"mean": statistics.fmean(vals), "std": statistics.pstdev(vals) or 0.0}


def golden_fingerprint(values: Iterable[float]) -> list[float]:
    """Min-max normalised fingerprint, robust to scale differences with a golden run."""
    vals = list(values)
    if not vals:
        return []
    lo, hi = min(vals), max(vals)
    span = hi - lo or 1.0
    return [round((v - lo) / span, 4) for v in vals]


def fingerprint_distance(a: Iterable[float], b: Iterable[float]) -> float:
    va, vb = list(a), list(b)
    if not va or len(va) != len(vb):
        return 1.0
    return round(math.sqrt(sum((x - y) ** 2 for x, y in zip(va, vb, strict=True)) / len(va)), 4)
