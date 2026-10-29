# Quick start

## Public demo

Open <https://jiuwendemos.github.io/rootcause/>. It works offline after the first visit.
Stage piece: press `R` to reset.

## Local development

### 1. Build the demo pack

```powershell
cd C:\Workspace\openjiuwendemos\rootcause
C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe scripts\build_demo_pack.py
```

### 2. Web

```powershell
cd web
npm.cmd install
npm.cmd run dev
# http://localhost:5173
```

`npm.cmd` avoids the Windows script-execution policy that blocks `npm.ps1`. On macOS/Linux use
`npm`.

### 3. API (optional for the UI, needed for exports and connectors)

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY -m pip install -e "server[dev,pdf,docx]"
& $PY -m uvicorn rootcause.api.app:app --app-dir server --port 8000 --reload
```

The Vite dev server proxies `/api` to port 8000. The built SPA is served by the API at `/` when
`web/dist` exists.

### 4. Tests

```powershell
& $PY -m pytest -q server
& $PY -m ruff check server
cd web; npm.cmd run build
```

## First five minutes in the app

1. Open `/#/stage`. Drag the lens; go to 60% depth; click **Reconstruct the cause**.
2. **Reject** tool mark. Watch gas porosity jump to 48%.
3. **Accept gas porosity and stamp**. The case sheet appears.
4. Open `/#/cases/RC-0417`. Inspect the machine window, batch, evidence and trace.
5. Open `/#/reports`. Edit the summary, save a new version, sign off, print to PDF.

## Docker

```bash
docker compose up --build
# http://127.0.0.1:8000
```

## Deploying the public site

GitHub Pages workflow: `.github/workflows/pages.yml`. It regenerates the pack, builds the web app
and deploys `web/dist`. Enable **Settings → Pages → Source: GitHub Actions** once.

## Troubleshooting

- **Loading evidence pack forever** → `web/public/demo-pack.json` missing; run the pack script.
- **`npm` blocked in PowerShell** → use `npm.cmd`.
- **PDF export 501** → install the `pdf` extra; use the HTML print view meanwhile.
- **No NPU** → the CPU detector is the fallback; the broker will not pretend.
