# RootCause server

The on-site API and domain engine. See the [root README](../README.md) for the product and
[`docs/`](../docs) for deployment, architecture and the pilot plan.

```bash
pip install -e ".[dev,pdf,docx]"
uvicorn rootcause.api.app:app --reload --port 8000
pytest -q
ruff check .
```

Key entry points:

- `rootcause.api.app` — FastAPI app and static SPA serving.
- `rootcause.engine.ranking` — the evidence-weighted cause ranking.
- `rootcause.engine.orchestrator` — the deterministic agent trace.
- `rootcause.store.db` — SQLite store with append-only audit triggers.
- `rootcause.npu.service` — optional NPU broker.
- `rootcause.training.finetune` — customer-specific detector fine-tuning.
