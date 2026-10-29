# Deployment

## Option A — Docker (recommended for a pilot)

```bash
docker compose up --build -d
curl http://127.0.0.1:8000/api/health
```

- The image builds the React app and serves it from the API at `/`.
- Data lives in the `rootcause-data` volume: `rootcause.sqlite3` and any uploads.
- No outbound network is required after the image is present.
- Health check: `/api/health`.

### NPU broker

```bash
docker compose --profile npu up --build -d
```

This starts `npu-broker` on port 7788 with the Ascend device nodes mounted. Then set on the API:

```
ROOTCAUSE_NPU=ascend
ROOTCAUSE_NPU_ENDPOINT=http://npu-broker:7788
```

If the Ascend runtime or the `.om` file is missing, the broker returns 503 instead of pretending.

## Option B — systemd on a Linux box

```bash
sudo useradd -r -s /usr/sbin/nologin rootcause
sudo mkdir -p /opt/rootcause /var/lib/rootcause
sudo chown -R rootcause:rootcause /var/lib/rootcause
# copy the repo to /opt/rootcause
sudo -u rootcause python3.11 -m venv /opt/rootcause/venv
sudo -u rootcause /opt/rootcause/venv/bin/pip install "./server[pdf,docx]"
sudo -u rootcause /opt/rootcause/venv/bin/python -c "import rootcause"  # app-dir handles path
sudo cp deploy/rootcause.service /etc/systemd/system/
sudo systemctl enable --now rootcause
```

The unit runs uvicorn with `--app-dir /opt/rootcause/server`, writes to `/var/lib/rootcause`, and is
hardened with `ProtectSystem=strict`. Build `web/dist` first (`cd web && npm ci && npm run build`)
or serve only the API and put the static app on the factory web server.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ROOTCAUSE_RUNTIME` | `./runtime` | Writable directory for the SQLite DB and temp uploads |
| `ROOTCAUSE_DB` | `$RUNTIME/rootcause.sqlite3` | Case store |
| `ROOTCAUSE_PACK` | `server/rootcause/data/demo_pack.json` | Offline pack |
| `ROOTCAUSE_CORS` | localhost dev origins | Comma-separated allowed origins |
| `ROOTCAUSE_NPU` | empty (CPU) | Set `ascend` to use the NPU broker |
| `ROOTCAUSE_NPU_ENDPOINT` | `http://127.0.0.1:7788` | Broker URL |
| `ROOTCAUSE_NPU_MODEL` | `defect.om` | Compiled model name |
| `ROOTCAUSE_NPU_SIMULATE` | unset | `1` runs the broker service on CPU for a laptop demo |

## Backups

```bash
# consistent copy while the service is running
sqlite3 /var/lib/rootcause/rootcause.sqlite3 ".backup '/backup/rootcause-$(date +%F).sqlite3'"
```

The audit trail is append-only. Do not restore a subset of tables; restore the whole file.

## Updating the model

1. Fine-tune on the training box with `python -m rootcause.training.finetune`.
2. Export ONNX, then ATC to `.om` on the NPU host.
3. Score the new model on 200 held-out images.
4. Update `ROOTCAUSE_NPU_MODEL`, restart the broker, and check `/api/npu/health`.
5. Record the model version and hash in the pilot log. Cases created after the switch carry the new
   version.

## Network

- Bind the API to the factory LAN only; do not expose it to the internet.
- Put it behind the site reverse proxy and SSO for named users.
- Allow the API to reach OPC-UA, the camera feed, the MES drop folder and the CMMS.
- No cloud endpoints are required. The only optional outbound call is a model download during setup,
  which can be done offline with a USB image.

## Air-gapped install

1. Build the Docker image on a connected machine: `docker build -t rootcause:0.9.0 .`
2. `docker save rootcause:0.9.0 | gzip > rootcause.tar.gz`
3. Move it to the factory; `docker load < rootcause.tar.gz`.
4. `docker compose up -d` with the image pinned.
5. The demo pack is inside the image; the site works with the cable out.

## Troubleshooting

- **Demo stuck on “Loading evidence pack”** — `web/dist/demo-pack.json` is missing. Run
  `python scripts/build_demo_pack.py` before `npm run build`.
- **PDF export returns 501** — install the `pdf` extra (`reportlab`). The HTML print view always
  works. Word export falls back to RTF if `python-docx` is absent.
- **Connector test says simulated** — no hardware is attached. Configure the endpoint and set
  `simulate=False` in the adapter for a live handshake.
- **NPU health not ready** — the Ascend runtime or `.om` is missing; the broker refuses to pretend.
- **Audit update fails** — that is the append-only trigger doing its job. Never drop the triggers in
  production.
