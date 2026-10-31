"""The proactive scheduler and replay harness.

The scan is deterministic and idempotent enough for a demo: it produces candidate signals, matches
them to patterns, opens watches (deduplicated by group key), honours storm protection, and records
a scan run. It never writes to a machine.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from ..laix_adapter import QUALITY_POLICY, decide_for_risk_signal
from ..models import RiskSignal, ScanRun, WatchCase
from . import signals as sig
from .containment import suggested_checks_from_pattern
from .learning import apply_pattern_prior, pattern_priors
from .watch import build_watch, duplicate_for, storm_guard

TZ = UTC


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


PATTERN_RULES = [
    ("P-H2", lambda s: "hydrogen" in s.parameter.lower()),
    ("P-MOIST", lambda s: "moist" in s.parameter.lower() or "dryer" in s.parameter.lower() or "batch pl" in s.parameter.lower()),
    ("P-LASER", lambda s: "laser" in s.parameter.lower() or "foil" in s.parameter.lower() or "calibration" in s.parameter.lower()),
    ("P-REFLOW", lambda s: "zone" in s.parameter.lower() or "reflow" in s.parameter.lower() or "x-ray" in s.parameter.lower()),
    ("P-DQ", lambda s: s.kind == "data_quality"),
    ("P-SEAL", lambda s: s.kind in {"maintenance", "setup", "environment"}),
]


def match_pattern(signal: RiskSignal, patterns: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    by_id = {p["id"]: p for p in patterns}
    for pid, rule in PATTERN_RULES:
        try:
            if rule(signal) and pid in by_id:
                return by_id[pid]
        except Exception:
            continue
    return None


def run_scan(
    *,
    pack: dict[str, Any],
    existing: Iterable[WatchCase],
    now: datetime | None = None,
    mode: str = "shadow",
    owner: str = "M. Weber",
    max_alerts: int = 10,
    coverage_floor: float = 0.95,
) -> dict[str, Any]:
    started = time.perf_counter()
    now = now or datetime.now(TZ)
    patterns = pack.get("proactive", {}).get("patterns", [])
    coverage = pack.get("proactive", {}).get("coverage", [])
    blind_lines = {row.get("line_id") for row in coverage if float(row.get("pct", 1)) < coverage_floor}
    raw = sig.scan_pack(pack, at=iso(now))
    cleaned = sig.dedupe(raw)
    existing_list = list(existing)
    candidates: list[WatchCase] = []
    suppressed = 0
    laix_records: list[dict] = []
    priors = pattern_priors(existing_list)
    for signal in cleaned:
        if signal.line_id in blind_lines and signal.kind != "data_quality":
            suppressed += 1
            continue
        pattern = match_pattern(signal, patterns)
        if not pattern:
            suppressed += 1
            continue
        key = f"{signal.line_id}:{pattern['id']}"
        if duplicate_for(existing_list, key):
            suppressed += 1
            continue
        decision, record = decide_for_risk_signal(
            signal,
            [*existing_list, *candidates],
            max_alerts=max_alerts,
            interruptions_used=len(existing_list),
        )
        laix_records.append(record.as_dict())
        if decision.action == "wait":
            suppressed += 1
            continue
        watch = build_watch(
            watch_id=f"W-{now.strftime('%H%M%S')}-{len(candidates) + 1}",
            signals=[signal],
            pattern=pattern,
            owner=owner,
            now=now,
            checks=suggested_checks_from_pattern(pattern),
            evidence_ids=[signal.evidence_id] if signal.evidence_id else [],
        )
        watch.risk_score = apply_pattern_prior(watch.risk_score, str(pattern.get("id", "")), priors)
        candidates.append(watch)
    kept, stormed = storm_guard(candidates, max_alerts=max_alerts)
    suppressed += stormed
    run = ScanRun(
        id=f"SCAN-{now.strftime('%Y%m%d%H%M%S')}",
        at=iso(now),
        mode=mode,
        lines_scanned=len({s.get("case", {}).get("line_id") for s in pack.get("scenarios", [])}),
        signals=len(cleaned),
        watches_opened=len(kept),
        suppressed=suppressed,
        duration_ms=int((time.perf_counter() - started) * 1000),
        status="ok",
        lag_seconds=0,
        note="Shadow mode: no notifications sent." if mode == "shadow" else "Live scan.",
    )
    return {
        "run": run,
        "signals": [s.model_dump() for s in cleaned],
        "candidates": [w.model_dump() for w in kept],
        "laix": {
            "engine": "laix",
            "enabled": True,
            "policy": QUALITY_POLICY.name,
            "decisions": laix_records,
            "records": laix_records,
        },
    }


def health(runs: Iterable[dict[str, Any]], *, now: datetime | None = None, interval_minutes: int = 15) -> dict[str, Any]:
    items = list(runs)
    now = now or datetime.now(TZ)
    if not items:
        return {"status": "blind", "last_scan": None, "lag_seconds": None, "detail": "No scan has run."}
    last = datetime.fromisoformat(items[0]["at"].replace("Z", "+00:00"))
    lag = (now - last).total_seconds()
    dead = lag > max(300, interval_minutes * 60 * 2)
    return {
        "status": "blind" if dead else "ok",
        "last_scan": items[0]["at"],
        "lag_seconds": int(lag),
        "detail": "Scheduler is late; the dead-man's switch should page the site." if dead else "Scheduler healthy.",
    }


def replay(pack: dict[str, Any]) -> dict[str, Any]:
    """Backtest the signal layer on the seeded scenarios and return a precision/recall estimate."""
    results = []
    for scenario in pack.get("scenarios", []):
        signals = sig.scan_scenario(scenario)
        expected = bool(scenario.get("case", {}).get("severity") in {"high", "critical"})
        opened = bool(signals)
        results.append(
            {
                "scenario": scenario.get("id"),
                "signals": len(signals),
                "expected_risk": expected,
                "opened": opened,
                "line": scenario.get("case", {}).get("line_id"),
            }
        )
    tp = sum(1 for r in results if r["opened"] and r["expected_risk"])
    fp = sum(1 for r in results if r["opened"] and not r["expected_risk"])
    fn = sum(1 for r in results if not r["opened"] and r["expected_risk"])
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "rows": results,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "note": "Replay on the seeded pack only. A pilot backtests six to twelve months of history before any live alert.",
    }


def next_run(settings: dict[str, Any], now: datetime | None = None) -> str:
    now = now or datetime.now(TZ)
    interval = int(settings.get("interval_minutes", 15))
    nxt = now + timedelta(minutes=interval - (now.minute % interval))
    return iso(nxt)
