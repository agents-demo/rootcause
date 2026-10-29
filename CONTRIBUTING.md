# Contributing

## The rules

1. **Evidence first.** A cause without an evidence ID is not a cause.
2. **The engineer decides.** Never add an automatic approval or line-control path.
3. **No data leaves the site.** No cloud inference, telemetry or external font/tile calls in the
   runtime.
4. **Synthetic public data.** No customer data and no MVTec AD in the public demo.
5. **Every claim is labelled.** If a connector or an NPU is simulated, the UI says so.

## Local checks

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY -m ruff check server
& $PY -m pytest -q server
cd web; npm.cmd run build
```

## Regenerating the demo pack

```powershell
& $PY scripts\build_demo_pack.py
```

Commit both `server/rootcause/data/demo_pack.json` and `web/public/demo-pack.json`; the static build
and the API must agree.

## Changing the ranking

- Update `engine/ranking.py` and `web/src/lib/engine.ts` together.
- Keep the weights visible in the UI.
- Add a test that the trust beat still re-ranks to gas porosity.
- Never let the confidence for a short list exceed the “none of these” guarantee without a reason.

## Style

- Python: ruff, 120 columns, standard library first.
- TypeScript: strict, no `any` in new code, design tokens in `styles.css`.
- CSS: dark industrial; amber for evidence, cyan for accepted, red for failure, never colour-only
  meaning.
