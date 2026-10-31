# LAIX quality intervention contract

- **Policy:** `quality-intervention.v1`
- **Version:** `1`
- **Provenance:** `rootcause@a8b7851`, captured 2026-10-31
- **Source of cases:** `server/rootcause/laix/fixtures.py` (`cases()` plus `contract_cases()`)
- **Frozen output:** `quality-intervention.v1.json` in this directory

The JSON file is a behavioural snapshot, not a specification of intent. Each case records one
signal, experience state and constraint set, together with the action, confidence, reasoning and
approval requirement the policy produced at capture time. It exists so a later LAIX core can be
diffed against RootCause's behaviour. It must not be edited to make a new policy pass; a difference
is a finding to report.

The twelve cases cover wait, ask, guide, act and escalate, including the budget, duplicate-signal
and missing-baseline branches. They are generated, never hand-edited.

## Shape

`quality-intervention.v1.json` is described by `server/rootcause/laix/schema.py` (`JSON_SCHEMA`),
which is the language-neutral contract for the decision layer. The schema is normative for shape;
the policy rules themselves are documented in `docs/laix-module.md`. The policy's own docstrings in
`server/rootcause/laix/intervention.py` remain the reference for rule order and thresholds.

## Regenerating

From `server/`, with the repository's Python environment:

```bash
python - <<'PY'
from dataclasses import asdict
import json
from pathlib import Path
from rootcause.laix.fixtures import cases, contract_cases
from rootcause.laix.intervention import QualityInterventionPolicy

policy = QualityInterventionPolicy()
rows = []
for case in [*cases(), *contract_cases()]:
    decision = policy.decide(case.signal, case.state, case.constraints)
    if decision.action != case.expected:
        raise SystemExit(f"policy disagrees with {case.id}: {case.expected} != {decision.action}")
    rows.append({
        "id": case.id,
        "signal": asdict(case.signal),
        "state": asdict(case.state),
        "constraints": asdict(case.constraints),
        "expected": {
            "action": decision.action,
            "confidence": decision.confidence,
            "why": list(decision.why),
            "requires_approval": decision.requires_approval,
        },
    })
print(json.dumps({"policy": policy.name, "version": "1", "cases": rows}, indent=2))
PY
```

Regenerate only when a deliberate policy change is approved; include the new commit hash in the
provenance. `server/tests/test_laix_replay.py` fails if the frozen file drifts from the policy.
