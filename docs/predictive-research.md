# Predictive research gate

Prediction is **not** a product commitment. It stays behind a gate until a specific question has
enough data, a baseline, a shadow evaluation and an economic case. A negative result is a valid and
useful result.

## The question

Current demo question:

> Can the next 200 cycles of the Line 6 furnace door seal be predicted with a validated lift over
> SPC?

## The gate

| Check | Requirement |
|---|---|
| Question | One component, one horizon, one customer |
| Data | ≥ 12 months and ≥ 30 events per failure mode |
| Labelling | Right-censoring and maintenance-induced removals handled |
| Baseline | SPC rule and survival/Kaplan-Meier; the model must beat the baseline |
| Shadow | Predictions logged, never shown to an operator |
| Metrics | Lead time, precision, recall, calibration and cost of both errors |
| Cost | False-positive and false-negative costs agreed with quality and finance |
| Decision | Separate product, embedded feature, or stop |
| Stop rule | No validated lift over SPC → do not ship |

## Current demo result

The pack ships a **stopped** gate:

- 14 months, 34 events (above the data floor).
- Model lift over SPC: **+0.02** — below the +0.05 requirement.
- False alarms: 31%; annualised cost of errors: €41,000.
- Decision: **stopped**. Prediction is not shipped.

This is deliberate. A demo that always shows a successful prediction is not a credible gate.

## Run the harness

```bash
cd server
python -m rootcause.research.predictive --months 14 --events-count 34
# gradient-boosted challenger
python -m rootcause.research.predictive --months 14 --events-count 34 --model gbm
# or with a real CSV: timestamp, event, feature_1..n
python -m rootcause.research.predictive --events path/to/events.csv --months 14 --events-count 34
```

Output: `runtime/research/gate.json`, including data audit, AUC, lift, precision, recall, false-alarm
rate, lead time, cost of errors and the decision.

## Methods

- `data_audit` checks months and event count.
- `prepare_survival` validates right-censored durations.
- `kaplan_meier` is the non-parametric baseline.
- `c_index` evaluates concordance with censoring.
- Logistic regression is the lightweight demonstration model; a pilot would use gradient boosting or
  a survival model with proper cross-validation.
- The harness is deterministic with a fixed seed and runs offline.

## Product boundary

Even a passing shadow result does **not** authorise:

- line control or automatic process changes;
- automatic rejection;
- hiding the prediction from the operator;
- a cloud prediction service;
- a claim of “predictive maintenance” without a separate product decision.

The gate exists so the team can say no with evidence.
