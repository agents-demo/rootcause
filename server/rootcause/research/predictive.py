"""Gated predictive research harness.

Prediction is not a product commitment. This module exists so a predictive claim can be tested
properly — with a data audit, censoring, a baseline, a shadow evaluation and a stop rule — and so a
negative result can be recorded instead of quietly shipped.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class GateResult:
    question: str
    data_months: int
    events: int
    required_events: int
    baseline_auc: float
    model_auc: float
    lift: float
    precision: float
    recall: float
    false_alarm_rate: float
    lead_time_hours: float
    cost_of_errors_eur: float
    decision: str
    status: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _auc(y: np.ndarray, score: np.ndarray) -> float:
    pos = score[y == 1]
    neg = score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return float(wins / (len(pos) * len(neg)))


def _logistic(x: np.ndarray, y: np.ndarray, *, epochs: int = 400, lr: float = 0.08) -> np.ndarray:
    """Small, dependency-light logistic regression. Features are standardised first."""
    mean = x.mean(axis=0)
    std = x.std(axis=0) + 1e-9
    xs = (x - mean) / std
    xs = np.hstack([np.ones((xs.shape[0], 1)), xs])
    w = np.zeros(xs.shape[1])
    for _ in range(epochs):
        p = 1 / (1 + np.exp(-np.clip(xs @ w, -30, 30)))
        grad = xs.T @ (p - y) / len(y)
        w -= lr * grad
    return 1 / (1 + np.exp(-np.clip(xs @ w, -30, 30)))


def gradient_boosting_stumps(x: np.ndarray, y: np.ndarray, *, rounds: int = 40, lr: float = 0.1) -> np.ndarray:
    """A compact gradient-boosted stump model, used as the research baseline challenger."""
    n, features = x.shape
    base = max(1e-4, min(1 - 1e-4, float(y.mean())))
    logit = np.full(n, np.log(base / (1 - base)))
    for _ in range(rounds):
        p = 1 / (1 + np.exp(-np.clip(logit, -30, 30)))
        residual = y - p
        best = None
        for f in range(features):
            values = x[:, f]
            for q in (0.25, 0.5, 0.75):
                threshold = float(np.quantile(values, q))
                left = values <= threshold
                if left.sum() == 0 or (~left).sum() == 0:
                    continue
                lv = float(residual[left].mean())
                rv = float(residual[~left].mean())
                sse = float(((residual[left] - lv) ** 2).sum() + ((residual[~left] - rv) ** 2).sum())
                if best is None or sse < best[0]:
                    best = (sse, f, threshold, lv, rv)
        if best is None:
            break
        _, f, threshold, lv, rv = best
        logit += lr * np.where(x[:, f] <= threshold, lv, rv)
    return 1 / (1 + np.exp(-np.clip(logit, -30, 30)))


def data_audit(months: int, events: int, *, required_months: int = 12, required_events: int = 30) -> dict[str, Any]:
    return {
        "months_ok": months >= required_months,
        "events_ok": events >= required_events,
        "sufficient": months >= required_months and events >= required_events,
        "months": months,
        "events": events,
        "required_months": required_months,
        "required_events": required_events,
    }


def prepare_survival(durations: list[float], events: list[int]) -> dict[str, Any]:
    """Validate right-censored durations: event=1 failure, event=0 censored/removed."""
    if len(durations) != len(events):
        raise ValueError("durations and events must have the same length")
    if any(d < 0 for d in durations):
        raise ValueError("durations must be non-negative")
    if any(e not in (0, 1) for e in events):
        raise ValueError("events must be 0 or 1")
    return {
        "durations": durations,
        "events": events,
        "failures": sum(events),
        "censored": len(events) - sum(events),
        "median_follow_up": sorted(durations)[len(durations) // 2] if durations else 0.0,
    }


def kaplan_meier(durations: list[float], events: list[int]) -> list[dict[str, float]]:
    """Kaplan-Meier survival curve; handles censoring explicitly."""
    pairs = sorted(zip(durations, events, strict=True))
    n = len(pairs)
    survival = 1.0
    curve: list[dict[str, float]] = []
    at_risk = n
    i = 0
    while i < n:
        time = pairs[i][0]
        failures = 0
        removed = 0
        while i < n and pairs[i][0] == time:
            removed += 1
            if pairs[i][1] == 1:
                failures += 1
            i += 1
        if at_risk > 0 and failures:
            survival *= 1 - failures / at_risk
        curve.append({"time": float(time), "survival": round(survival, 4), "at_risk": at_risk, "failures": failures})
        at_risk -= removed
    return curve


def c_index(durations: list[float], events: list[int], risk: list[float]) -> float:
    """Harrell's concordance for right-censored data."""
    concordant = discordant = tied = 0
    n = len(durations)
    for i in range(n):
        if events[i] != 1:
            continue
        for j in range(n):
            if i == j or durations[j] <= durations[i]:
                continue
            if risk[i] > risk[j]:
                concordant += 1
            elif risk[i] < risk[j]:
                discordant += 1
            else:
                tied += 1
    total = concordant + discordant + tied
    return round((concordant + 0.5 * tied) / total, 4) if total else 0.5


def evaluate(
    *,
    question: str,
    y: np.ndarray,
    baseline_score: np.ndarray,
    model_score: np.ndarray,
    lead_time_hours: float,
    months: int,
    events: int,
    cost_false_positive: float = 1200.0,
    cost_false_negative: float = 18000.0,
    min_lift: float = 0.05,
) -> GateResult:
    baseline_auc = _auc(y, baseline_score)
    model_auc = _auc(y, model_score)
    threshold = float(np.quantile(model_score, 0.75))
    pred = (model_score >= threshold).astype(int)
    tp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    false_alarm_rate = fp / (fp + tp) if (fp + tp) else 0.0
    cost = fp * cost_false_positive + fn * cost_false_negative
    lift = round(model_auc - baseline_auc, 4)
    if lift < min_lift:
        decision = f"Stopped: no validated lift over SPC (lift {lift:+.3f}, required {min_lift:.2f}). Prediction is not shipped."
        status = "stopped"
    elif precision < 0.5 or false_alarm_rate > 0.3:
        decision = "Stopped: the error profile is not economically acceptable at this false-alarm rate."
        status = "stopped"
    else:
        decision = "Shadow result meets the gate. A separate product decision is still required before exposure."
        status = "shadow"
    return GateResult(
        question=question,
        data_months=months,
        events=events,
        required_events=30,
        baseline_auc=round(baseline_auc, 3),
        model_auc=round(model_auc, 3),
        lift=lift,
        precision=round(precision, 3),
        recall=round(recall, 3),
        false_alarm_rate=round(false_alarm_rate, 3),
        lead_time_hours=lead_time_hours,
        cost_of_errors_eur=round(cost, 2),
        decision=decision,
        status=status,
        note="Research gate only. The model is logged in shadow mode and never shown to an operator.",
    )


def synthetic_events(n: int = 240, seed: int = 417) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """A deliberately weak signal: enough to exercise the gate, not to claim a product."""
    rng = np.random.default_rng(seed)
    vibration = rng.normal(0, 1, n)
    temperature = rng.normal(0, 1, n)
    maintenance = rng.integers(0, 2, n)
    latent = 0.35 * vibration + 0.15 * temperature + 0.4 * maintenance + rng.normal(0, 1, n)
    y = (latent > np.quantile(latent, 0.7)).astype(int)
    noise = rng.normal(0, 1, n)
    baseline = 0.9 * vibration + 0.1 * noise
    model = _logistic(np.column_stack([vibration, temperature, maintenance]), y)
    return y, baseline, model, np.column_stack([vibration, temperature, maintenance])


def load_events(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("empty event file")
    y = np.array([int(float(r.get("event", 0))) for r in rows])
    feature_names = [k for k in rows[0] if k not in {"event", "timestamp"}]
    x = np.array([[float(r.get(k, 0) or 0) for k in feature_names] for r in rows])
    baseline = 1 / (1 + np.exp(-np.array([float(r.get(feature_names[0], 0) or 0) for r in rows])))
    model = _logistic(x, y)
    return y, baseline, model, x


def run(question: str, y: np.ndarray, baseline: np.ndarray, model: np.ndarray, months: int, events: int, lead: float) -> GateResult:
    audit = data_audit(months, events)
    if not audit["sufficient"]:
        return GateResult(
            question=question, data_months=months, events=events, required_events=30,
            baseline_auc=0.0, model_auc=0.0, lift=0.0, precision=0.0, recall=0.0,
            false_alarm_rate=0.0, lead_time_hours=lead, cost_of_errors_eur=0.0,
            decision="Stopped at data audit: not enough history or events to test the question.",
            status="data_audit", note="Collect more history; do not fit a model yet.",
        )
    return evaluate(question=question, y=y, baseline_score=baseline, model_score=model, lead_time_hours=lead, months=months, events=events)


def main() -> None:
    parser = argparse.ArgumentParser(description="RootCause predictive research gate")
    parser.add_argument("--events", type=Path, help="CSV with timestamp, event and numeric features")
    parser.add_argument("--months", type=int, default=14)
    parser.add_argument("--events-count", type=int, default=34)
    parser.add_argument("--question", default="Can the next 200 cycles of the furnace door seal be predicted with a lift over SPC?")
    parser.add_argument("--model", choices=["logistic", "gbm"], default="logistic")
    parser.add_argument("--out", type=Path, default=Path("runtime/research/gate.json"))
    args = parser.parse_args()

    if args.events:
        y, baseline, logistic, x = load_events(args.events)
        model = gradient_boosting_stumps(x, y) if args.model == "gbm" else logistic
        result = run(args.question, y, baseline, model, args.months, args.events_count, 8.0)
    else:
        y, baseline, logistic, x = synthetic_events()
        model = gradient_boosting_stumps(x, y) if args.model == "gbm" else logistic
        result = run(args.question, y, baseline, model, args.months, args.events_count, 8.0)
        print("Using the synthetic event set; this is a harness demonstration, not a product claim.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result.as_dict(), indent=2), encoding="utf-8")
    print(json.dumps(result.as_dict(), indent=2))


if __name__ == "__main__":
    main()
