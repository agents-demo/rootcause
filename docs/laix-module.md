# LAIX in RootCause: generic layer, quality plugin

RootCause uses **LAIX** as an installed dependency for the generic decision layer. The quality
policy is a **RootCause plugin**, not a fork of LAIX. LAIX stays domain-neutral; RootCause keeps the
quality vocabulary, the line/case/watch data and the recurrence estimator.

```text
quality RiskSignal
  -> rootcause.laix_adapter        (the only file that knows both worlds)
  -> laix.Layer(policy=QualityPolicy())
  -> laix.LayerDecision
  -> rootcause watch / check / notification
```

## What belongs where

| Piece | Owner | Location |
|---|---|---|
| Decision contract, `Layer`, `DecisionRequest`, `LayerDecision`, `EvidenceRef`, policy interface | LAIX | installed `laix` package |
| Quality signal, state, constraints, decision record, follow-up, outcome | RootCause | `server/rootcause/quality/contracts.py` |
| Quality intervention policy | RootCause | `server/rootcause/quality/policy.py` |
| Recurrence outcome estimator | RootCause | `server/rootcause/quality/outcome.py` |
| Quality bench and fixtures | RootCause | `server/rootcause/quality/bench.py`, `fixtures.py`, `fixtures/` |
| App-to-LAIX translation | RootCause | `server/rootcause/laix_adapter.py` |
| Line, case, watch, report, store, API, UI, connectors | RootCause | the rest of the app |

The adapter places the quality objects in `DecisionRequest.attributes`:

```python
DecisionRequest(
    subject=signal.id,
    at=signal.at,
    attributes={
        "quality_signal": quality_signal,
        "quality_state": quality_state,
        "quality_constraints": quality_constraints,
    },
)
```

No quality noun enters LAIX. The policy reads those attributes and returns a `LayerDecision` with
the LAIX fields (`verb`, `reason_code`, `rationale`, `evidence`, `requires_approval`,
`cost_of_waiting`). The adapter maps it back to the app's decision shape (`action`, `why`,
`evidence_ids`, `confidence`, `expected_cost`, `wait_cost`, `requires_approval`, `policy`,
`state_id`, `signal_id`) and builds the app's decision record.

## The pinned dependency

`server/pyproject.toml` pins LAIX to a tag, never a branch:

```toml
"laix @ git+https://github.com/michaelatamuk/laix.git@v0.2.1#subdirectory=python/laix",
```

Local co-development, once:

```powershell
py -m pip install -e C:\Workspace\laix\python\laix
```

CI and release install from the pinned tag. Ordinary RootCause changes do not need a reinstall.

## The quality plugin

`server/rootcause/quality/policy.py` defines:

```python
class QualityInterventionPolicy:
    name = "quality-intervention.v1"
    version = "1.0"

    def decide(self, request: DecisionRequest) -> list[LayerDecision]:
        ...
```

`QualityPolicy` is an alias. It keeps the existing scoring, severity weights, interruption budget,
novelty checks, approval rules and reason strings. Only the outer shape changed:

- `verb` instead of `action`;
- a `reason_code` per branch (`below_threshold`, `budget_spent`, `already_open`, `thin_evidence`,
  `critical_signal`, `open_watch`, `surface_now`);
- `rationale` is the existing `why` list joined with newlines; the adapter splits it back;
- evidence is `EvidenceRef(id=evidence_id, kind="quality_signal")`;
- `cost_of_waiting` carries the old `wait_cost`;
- `expected_cost` is carried in `breakdown.interruption`;
- `record` is built by `quality.policy.record_for` for the app's audit trail.

The plugin is selected once in the adapter:

```python
QUALITY_POLICY = QualityPolicy()
LAYER = Layer(policy=QUALITY_POLICY)
```

## The decision path is always LAIX

There is no native/shadow decision-engine switch and no `ROOTCAUSE_LAIX` gate. Every proactive scan
calls `Layer(policy=QualityPolicy())`, and every decision record is written to the scan result and
the audit trail. A `wait` verb suppresses the watch; `ask`, `guide`, `act` and `escalate` open it, as
before. The scan mode (`shadow` / live) still controls notifications only.

The adapter reads these app-level settings:

| Variable | Default | Effect |
|---|---|---|
| `ROOTCAUSE_LAIX_INTERRUPT_COST` | `1.0` | cost of an interruption |
| `ROOTCAUSE_LAIX_MISS_COST` | `10.0` | cost of a miss |
| `ROOTCAUSE_LAIX_REQUIRE_APPROVAL` | `0` / false | require approval for `act` / `escalate` |
| `ROOTCAUSE_LAIX_BASELINE` | `0` | auto-record an outcome action on report approval when > 0 |
| `ROOTCAUSE_LAIX_WINDOW_DAYS` | `30` | outcome window |

The interruption budget comes from the scan's `max_alerts` and `interruptions_used` from the number
of existing watches.

## API

```bash
GET  /api/laix/status       # engine, LAIX version, LAIX schema/policy versions, quality plugin, outcome config
GET  /api/laix/decisions    # recent decision records from the audit trail
POST /api/laix/decide       # quality signal + state + constraints -> decision + record
POST /api/laix/outcome      # one-off estimate from supplied follow-ups
GET  /api/laix/actions
POST /api/laix/actions
POST /api/laix/actions/{id}/followup
GET  /api/laix/outcomes
```

`POST /api/laix/decide` goes through the adapter and `Layer`, so it returns the same decision and
record as a proactive scan. `GET /api/laix/status` reports `engine: "laix"`, the installed package
version, `schema_version`, `laix_policy_version`, and the quality plugin name/version.

The app does **not** use LAIX to approve a cause, control a line, or call a model. The engineer still
decides and signs.

## The outcome loop

RootCause persists the loop in SQLite (`laix_actions`, `laix_followups`). On report approval, the
existing post-fix follow-up becomes an action when `ROOTCAUSE_LAIX_BASELINE` > 0; verifying that
follow-up records the recurrence. `QualityOutcomeTracker` and `estimate_outcome` compute treated,
recurred, effect and a sample-size confidence. The result is explicitly observational (`causal:
false`), not a causal claim.

The Admin page has a **Decision layer · LAIX** panel (on-site API only) with the policy, baseline,
window and each outcome, plus **No recurrence** / **Recurred** buttons.

## How to upgrade LAIX

1. Pick a new LAIX tag; do not use `main`.
2. Change the pin in `server/pyproject.toml`.
3. Install it: `py -m pip install "git+https://github.com/michaelatamuk/laix.git@<tag>#subdirectory=python/laix"`.
4. Run `py -m pytest -q server`, the quality replay test and `py -m rootcause.quality.bench`.
5. If a contract change is breaking, update the adapter and the quality plugin in the same commit.

## Rollback

Revert the commit that adopted the new LAIX or plugin version. There is no second decision path to
fall back to and no shadow mode to keep alive. If a rollback is needed, pin the previous tag and
revert the adapter/plugin change together.

## Bench and fixtures

`server/rootcause/quality/fixtures.py` and `bench.py` are app policy evidence, not LAIX contracts.
`server/tests/test_laix_replay.py` replays the 12-case quality fixture through the plugin and checks
the app decision fields; `test_laix_isolation.py` asserts the local `rootcause.laix` package is gone
and the external `laix` package is installed.

The bench was 7/7 at the last run, and the replay 12/12. Agreement means the policy is stable and
replayable, not that it is correct on real plant data.

## Honest limits

- The policy is **rules, not a learned model**. It is testable and explainable, but not optimised.
- The outcome is **observational**; there is no matching or control window.
- Confidence is a sample-size proxy, not a statistical confidence.
- RootCause currently feeds it synthetic or manually uploaded signals; the plant connection is not.
- The bench is a seed (7 cases), not a full benchmark.
- The quality contracts still use `line_id`, `parameter`, `baseline` and `case_id`; they are passed
  to LAIX as opaque attributes, not as LAIX fields.

## Files

| File | Purpose |
|---|---|
| `server/rootcause/quality/contracts.py` | Quality signal, state, constraints, decision, record, follow-up, outcome |
| `server/rootcause/quality/policy.py` | LAIX policy plugin, rules, decision record builder |
| `server/rootcause/quality/outcome.py` | Outcome tracker and estimator |
| `server/rootcause/quality/schema.py` | Quality JSON Schema |
| `server/rootcause/quality/bench.py`, `fixtures.py`, `fixtures/` | Bench and replay evidence |
| `server/rootcause/laix_adapter.py` | RootCause ↔ LAIX mapping; owns `Layer(policy=QualityPolicy())` |
| `server/rootcause/proactive/scheduler.py` | Always-on quality decision path |
| `server/rootcause/api/app.py` | `/api/laix/*` endpoints |
| `server/tests/test_laix.py` | Policy, plugin, adapter and outcome tests |
| `server/tests/test_laix_replay.py` | Fixture replay through the plugin |
| `server/tests/test_laix_isolation.py` | Local package removed; external LAIX installed |

Read also: [LAIX integration](https://github.com/michaelatamuk/laix/blob/v0.2.1/docs/integration.md)
and [the LAIX Python package](https://github.com/michaelatamuk/laix/blob/v0.2.1/python/laix/README.md).
