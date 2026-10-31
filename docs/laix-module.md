# LAIX extraction: a portable decision layer inside RootCause

This is a real extraction, not a rebrand. RootCause is the vertical quality app. `server/rootcause/laix/`
is a horizontal decision layer that can be lifted into LAIX and reused by another app.

The package has **no RootCause, FastAPI, SQLite or agent imports**. RootCause wires it through
`server/rootcause/laix_adapter.py`; that adapter is the only file that knows both worlds.

## What was extracted

| LAIX component | RootCause use | Where |
|---|---|---|
| **Live Context + Decision Engine** | When to wait, ask for a check, open a watch, notify, or escalate a quality signal | `laix/intervention.py` |
| **Experience State** | Line-level state: open watch keys, handled signals, confidence, expiry | `laix/contracts.py` |
| **Execution bridge** | The app maps a decision to a watch, a check or a notification; the policy never controls a line | `laix_adapter.py` |
| **Outcome Learning** | Recurrence after an action, compared with a baseline, with an honest confidence | `laix/outcome.py` |
| **Decision record** | What was decided, why, which evidence, confidence, approval state, input digest | `laix/intervention.py` |

The six LAIX actions are used directly: `wait`, `ask`, `guide`, `act`, `verify`, `escalate`.

## The policy

`QualityInterventionPolicy` is rule-based and deterministic. It scores a signal from:

- severity,
- evidence (z-score, baseline, a floor for high/critical signals),
- novelty (already handled or already open → `wait`),
- the interruption budget (spent budget → `wait` unless critical).

It returns a decision with `why`, `evidence_ids`, `confidence`, `expected_cost`, `wait_cost`,
`requires_approval`, and the policy version. It is deliberately not a learned model: LAIX says safety
rules first; a calibrated scorer or bandit can replace `_score` without changing the contract.

## The outcome loop

RootCause persists the loop in SQLite (`laix_actions`, `laix_followups`). `QualityOutcomeTracker`
and `estimate_outcome` compute it; the API records actions and follow-ups:

```bash
GET  /api/laix/actions
POST /api/laix/actions                  # action, case, line, baseline, window
POST /api/laix/actions/{id}/followup    # recurrence true/false
GET  /api/laix/outcomes                 # treated, recurred, effect, confidence
```

It returns an `Outcome`:

- treated cases, recurrences, treated rate,
- baseline rate, relative effect,
- a sample-size confidence,
- `causal: false` and a note that this is observational, not a causal claim.

This is the piece RootCause was missing: a corrective action now has a measurable “did it help?”
answer instead of only “it was done”. The app does not auto-record actions from report approval yet;
the caller supplies the real baseline and window.

## How RootCause uses it

The proactive scheduler has an opt-in switch:

```bash
ROOTCAUSE_LAIX=1
```

When enabled, `scheduler.run_scan` calls the policy for each candidate signal. `wait` suppresses the
watch; `ask`, `guide`, `act` and `escalate` open it. The scan result includes a `laix` block with the
policy version and every decision record; the records are also written to the append-only audit as
`laix.decision`, so the “what, why, evidence, confidence” survives the request.

There are HTTP endpoints for a future TypeScript SDK or another app:

```bash
GET  /api/laix/status
GET  /api/laix/decisions # recent decision records from the audit trail
POST /api/laix/decide    # signal + state + constraints -> decision + record
POST /api/laix/outcome   # one-off estimate from supplied follow-ups
```

The app does **not** use LAIX to approve a cause, control a line, or call a model. The engineer still
decides and signs.

## How to lift it into LAIX

1. Copy `server/rootcause/laix/` into the LAIX runtime/SDK. It has no app dependency.
2. Replace the SQLite-backed `laix_actions` / `laix_followups` store with the LAIX experience-state store.
3. Keep `laix_adapter.py` in RootCause as the south-interface implementation: read state, run a skill,
   ask for approval, stream events.
4. Add the policy to the LAIX decision registry. The contract is the north interface in
   `interfaces.md`: the app supplies signals, state, outcome and constraints; LAIX returns a decision,
   its evidence, confidence and costs.
5. If a learned policy replaces the rules, keep the same `decide` signature and evidence/why fields.
   LAIX-Bench can replay the same `Signal` fixtures.

## What is not portable

- The RootCause case workspace, report, ranking engine, UI and manager proof.
- The SQLite case store and its audit tables.
- The synthetic pack and the demo video.
- The connector and NPU code; those belong to the app/platform, not the decision layer.

## Honest limits

- The policy is **rules, not a learned model**. It is testable and explainable, but not optimised.
- The outcome is **observational**. It does not control for confounders; a pilot with matching is
  required before claiming causality.
- RootCause currently feeds it synthetic or manually uploaded signals. The module is real; the plant
  connection is not.
- It is one decision class (quality intervention) and one outcome type (recurrence). That is a module,
  not LAIX in full.

## Mapping to the LAIX case

| LAIX decision class | Fit with this module |
|---|---|
| 3.1 Real-time intervention under uncertainty | **Strong** — when to surface a quality risk, under alert-fatigue cost |
| 3.5 Causal outcome estimation | **Strong** — the outcome loop, currently observational |
| 3.9 Safety-constrained action | **Strong pattern** — no auto-approval, no line control, audit trail |
| 3.2 Active perception | Weak — no camera policy yet |
| 3.3 Stochastic replanning | Not present |
| 3.4 Resource allocation | Partial — the decision queue prioritises engineer attention |
| 3.6–3.8, 3.10 | Not present |

This is the slow, high-stakes end of the LAIX decision map, not the 400 ms coach. It is a candidate
reference app for that end, and a source of two modules: **Quality Intervention Policy** and
**Quality Outcome Learning**.

## Files

| File | Purpose |
|---|---|
| `server/rootcause/laix/contracts.py` | Portable dataclasses |
| `server/rootcause/laix/intervention.py` | Policy, decision record, replay |
| `server/rootcause/laix/outcome.py` | Outcome tracker and estimator |
| `server/rootcause/laix_adapter.py` | RootCause ↔ LAIX mapping |
| `server/rootcause/proactive/scheduler.py` | Optional `ROOTCAUSE_LAIX=1` integration |
| `server/rootcause/api/app.py` | `/api/laix/*` endpoints |
| `server/tests/test_laix.py` | Policy, outcome, adapter tests |

Read also: [LAIX overview](../agentic-desk/projects/middleware/laix/overview.md) and
[the LAIX case](../agentic-desk/projects/middleware/laix/laix-case.md) in the agentic-desk workspace.
