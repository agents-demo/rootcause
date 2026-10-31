# LAIX handoff: RootCause → LAIX core

This is the handoff record for the portable decision layer that currently lives inside RootCause.
It freezes the policy, proves the package runs without the app, and gives LAIX a replay fixture and
an extraction manifest. It does **not** rename public types or change a single decision.

- Repository: RootCause (`C:\Workspace\openjiuwendemos\rootcause`)
- Branch: `laix/handoff-v1`
- Tag: `laix-handoff-v1`
- Captured from: `rootcause@a8b7851`
- Handoff commit: `72cac4c` (this file is `72cac4c` plus the hash-recording follow-up)

## Module paths and line counts

| Path | Lines | Role |
|---|---:|---|
| `server/rootcause/laix/__init__.py` | 44 | public exports |
| `server/rootcause/laix/contracts.py` | 152 | dataclasses: signal, state, constraints, decision, record, follow-up, outcome |
| `server/rootcause/laix/intervention.py` | 204 | `QualityInterventionPolicy` (rules, decision record, replay) |
| `server/rootcause/laix/outcome.py` | 82 | `estimate_outcome`, `QualityOutcomeTracker` |
| `server/rootcause/laix/schema.py` | 141 | language-neutral JSON Schema (`JSON_SCHEMA`, `schema()`) |
| `server/rootcause/laix/bench.py` | 49 | LAIX-Bench seed (7 cases) |
| `server/rootcause/laix/fixtures.py` | 120 | bench cases + `contract_cases()` |
| `server/rootcause/laix/contract/quality-intervention.v1.json` | 597 | frozen 12-case behavioural contract |
| `server/rootcause/laix/contract/README.md` | 60 | contract provenance and regeneration |
| `server/rootcause/laix/fixtures/replay.json` | 593 | 12 golden decisions |
| `server/rootcause/laix/fixtures/outcome.json` | 178 | 3 golden outcome estimates |
| `server/rootcause/laix_adapter.py` | 92 | **stays in RootCause**: the only file that knows both worlds |
| `server/tests/test_laix.py` | 197 | policy, outcome, adapter and persistence tests |
| `server/tests/test_laix_replay.py` | 117 | replay, contract-freeze and outcome fixtures |
| `server/tests/test_laix_isolation.py` | 134 | host-import and domain-noun guard |

The portable package is `server/rootcause/laix/`. Nothing outside that folder belongs to the core.
Note that `contracts.py` grew by the additive `Signal.as_generic()`; the frozen fields are unchanged.

## Public API

Exported from `laix/__init__.py`:

| Name | Kind | Purpose |
|---|---|---|
| `QualityInterventionPolicy` | class | `decide`, `record`, `replay`; policy name `quality-intervention.v1` |
| `Signal` | frozen dataclass | one observation, quality fields plus generic attributes |
| `ExperienceState` | frozen dataclass | what the app knows: open keys, actions, confidence |
| `Constraints` | frozen dataclass | interruption budget, costs, risk ceiling, approval |
| `Decision` | frozen dataclass | action, confidence, why, evidence, costs, approval |
| `DecisionRecord` | frozen dataclass | what/why/evidence/confidence, digest, actor, approval state |
| `FollowUp` | frozen dataclass | what happened after an action in a window |
| `Outcome` | frozen dataclass | treated, recurred, effect, confidence, observational note |
| `QualityOutcomeTracker` | class | in-memory action/follow-up tracker |
| `estimate_outcome` | function | follow-ups + baseline → `Outcome` |
| `decision_summary` | function | one-line human summary |
| `schema` / `JSON_SCHEMA` | function / dict | JSON Schema boundary |

Actions are `wait`, `ask`, `guide`, `act`, `verify`, `escalate`; severities are `info`, `warning`,
`high`, `critical`.

## Dependencies

**None.** The package imports only the standard library:

`__future__`, `collections.abc`, `copy`, `dataclasses`, `datetime`, `hashlib`, `json`, `typing`,
`uuid`.

`server/tests/test_laix_isolation.py` asserts that every absolute import is in
`sys.stdlib_module_names` and that no import names RootCause, FastAPI, SQLite, numpy or an agent
framework. The clean-copy run below used `python -S` (no site-packages) and still imported and ran.

## Tests and commands

From `server/`:

```bash
python -m pytest -q tests/test_laix.py tests/test_laix_replay.py tests/test_laix_isolation.py
python -m pytest -q
```

From the repository root:

```bash
python -m ruff check server scripts
```

RootCause has no parity harness for this policy. The equivalent evidence is the bench and the replay
fixture: 7/7 bench cases agree, 12/12 frozen replay cases agree, 0 diffs.

## Generic vs quality vocabulary

`Signal.as_generic()` is additive. Existing fields stay, so the app and the frozen contract keep
working; the generic view is what a domain-free LAIX core should read.

| Generic | Quality field | Notes |
|---|---|---|
| `subject` | `line_id` | the thing being observed (a production line here) |
| `kind` | `parameter` | the observed quantity, not the detector method |
| `attributes["value"]` | `value` | current value |
| `attributes["baseline"]` | `baseline` | reference value |
| `attributes["z"]` | `z` | standardised deviation |
| `evidence_id` | `evidence_id` | unchanged |
| — | `id`, `source`, `at`, `severity`, `attributes` | retained on the quality object |

The policy dedupe/replay key is now built from `as_generic()['subject']` and `['kind']`. The strings
are identical to the previous `f"{line_id}:{parameter}"` key, so behaviour is unchanged.

Still quality-specific in the core (deliberately, this round): `line_id` and `parameter` on
`Signal`; `case_id`, `line_id`, `defect` on `FollowUp`; `baseline_rate` and the word "line" in the
outcome note. They are listed in the isolation guard so every one is visible and new ones fail.

## RootCause integration and defaults

The adapter `server/rootcause/laix_adapter.py` maps a `RiskSignal` and open watches into the portable
contracts, calls the policy, and returns a decision plus its record. The scheduler only consults it
when the flag is on:

| Variable | Default | Effect |
|---|---|---|
| `ROOTCAUSE_LAIX` | `0` (off) | scheduler runs the policy; `wait` suppresses the watch |
| `ROOTCAUSE_LAIX_BASELINE` | `0` | report approval auto-records a post-fix action only when > 0 |
| `ROOTCAUSE_LAIX_WINDOW_DAYS` | `30` | outcome window |
| `ROOTCAUSE_LAIX_INTERRUPT_COST` | `1.0` | cost of an interruption |
| `ROOTCAUSE_LAIX_MISS_COST` | `10.0` | cost of a miss |
| `ROOTCAUSE_LAIX_REQUIRE_APPROVAL` | `0` / false | require approval for `act` / `escalate` |

The interruption budget comes from the scan's `max_alerts` (default 10) and `interruptions_used` from
the number of existing watches. The app's scan mode stays `shadow` by default, so no notifications
are sent. The policy never opens a valve or controls a line; `act` means watch plus notification.

With the flag off, the scheduler follows the previous code path exactly: no import of the adapter,
no policy decisions, no change to the API payload beyond `"laix": {"enabled": false}` already
present at the base commit. The SQLite schema, API and UI are untouched by this pass.

## Measured parity

- LAIX-Bench seed: **7/7** cases, agreement 1.0, intervention precision 1.0.
- Frozen behavioural contract: **12/12** cases, 0 mismatches.
- Golden replay: **12/12** cases, **0 diffs**.
- Outcome fixtures: **3/3** cases, 0 diffs (10, 4 and 0 follow-ups).
- Clean copy: imports and replays with no RootCause, FastAPI, SQLite or numpy module loaded.

Caveat: the cases are synthetic fixtures written by the same author as the policy. 100% agreement
means the policy is stable and replayable, not that it is correct on real plant data.

## Known limits

- Outcomes are observational. `causal` is always `false`; there is no matching or control window.
- `confidence` is a sample-size proxy (`treated / 20`), not a statistical confidence.
- Signals are synthetic or manually entered; there is no plant connection in this repository.
- The bench is a seed (7 cases), not LAIX-Bench proper.
- The policy is a rule scorer with fixed thresholds; no calibrated scorer or bandit yet.
- The core still carries quality fields (`line_id`, `parameter`, `baseline`, `case_id`); the generic
  view is additive, not a rename.
- `verify` exists as an action but the policy never emits it; follow-up verification is an app flow.

## Extraction steps

1. Copy `server/rootcause/laix/` to the LAIX repository as `laix/` (the folder is already an importable
   package). Keep `contract/` and `fixtures/` with it as package data.
2. Add this metadata to the new repository's `pyproject.toml`; change nothing else:

   ```toml
   [build-system]
   requires = ["setuptools>=68"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "laix-core"
   version = "1.0.0"
   description = "Portable LAIX decision layer: contracts, policy, decision records and outcomes."
   requires-python = ">=3.11"
   license = { text = "MIT" }
   dependencies = []

   [tool.setuptools.packages.find]
   where = ["."]
   include = ["laix*"]

   [tool.setuptools.package-data]
   laix = ["contract/*.json", "fixtures/*.json"]
   ```

3. Keep `server/rootcause/laix_adapter.py` in RootCause. Change its imports from `from .laix import …`
   to `from laix import …` (or a thin local shim). Do not move geospatial or quality code into LAIX.
4. Replace the SQLite tables `laix_actions` / `laix_followups` in `server/rootcause/store/db.py` with
   the LAIX state store, keeping the existing API payload shapes. This is the only persistence work.
5. Run `python -m pytest -q` and the replay fixture in the new repository; publish `laix-core` when
   the tag is approved. Nothing is published by this pass.
6. Switch `ROOTCAUSE_LAIX=1` only after the extracted package matches the replay fixture. `native`
   remains the default until then.
7. Do not delete `server/rootcause/laix/` until one release has run against the extracted package.

## Scan modes and the flag

The app's scan mode (`shadow` by default) controls whether notifications are sent. The LAIX flag is
separate: `ROOTCAUSE_LAIX=0` keeps the pre-LAIX scheduler path regardless of the scan mode, and
`ROOTCAUSE_LAIX=1` lets policy decisions suppress `wait` watches and records every decision. The
policy never actuates equipment; `act` means watch plus notification.

## Behaviour change in this pass

None intended and none observed. The only code change to the core is the additive
`Signal.as_generic()` and replacing the two internal dedupe/replay key expressions with the same
string values read through that method. The contract was generated from the policy's own output; no
case was edited to pass.

## Flag-off confirmation

The full suite was run with `ROOTCAUSE_LAIX` unset (the default) and passed. The scheduler's flag
check, default values, API routes, SQLite schema and UI are unchanged. RootCause still runs the
native path when the flag is absent.
