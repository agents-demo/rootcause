# Production wiring

This document is the line between **code that is wired** and **a site that is connected**. The
repository now contains the real adapters. A production deployment still needs the customer's model
credentials, NPU/ONNX model, plant endpoints and identity provider.

**Readiness is explicit.** `GET /api/ready` returns 503 when `ROOTCAUSE_STRICT_INTEGRATIONS=1` and
the agent, inference backend or a live plant connector is missing. The app never claims to be
connected when it is not.

---

## 1. Agent runtime — JiuwenSwarm / openJiuwen

`server/rootcause/agent/jiuwen_runtime.py` builds a real `DeepAgent` with tools over the current
case:

| Tool | Reads |
|---|---|
| `read_machine_window` | the 3-hour sensor window, z-scores and spec breaches |
| `read_batch` | batch, maintenance and joined case history |
| `similar_cases` | closest historical cases |
| `ranked_causes` | the evidence-ranked cause list |
| `evidence` | evidence IDs, sources, timestamps and strength |
| `coverage` | coverage context (site-level pack) |

The agent is instructed to cite evidence IDs, admit insufficient evidence and never approve a
cause or control the line. It is **not** allowed to replace the deterministic ranking: the engineer
still approves.

### Configure

```bash
ROOTCAUSE_AGENT_BACKEND=openjiuwen
MODEL_PROVIDER=OpenAI          # or DeepSeek / compatible provider
API_BASE=https://...
API_KEY=...
MODEL_NAME=...
LLM_SSL_VERIFY=true
ROOTCAUSE_AGENT_MAX_ITERATIONS=8
```

### Verify

```bash
curl http://127.0.0.1:8000/api/agent/status
curl -X POST http://127.0.0.1:8000/api/agent/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why hydrogen?","case_id":"RC-0417"}'
```

Without credentials, `/api/agent/ask` returns **503** with the missing configuration. There is no
silent fake answer. The UI `AskPanel` uses the agent when the on-site API is live; if it receives
503 it labels the answer as coming from the local evidence engine.

### Still needed at the site

- A production model account/key and an approved data-processing basis.
- An agent eval set: faithfulness, citation coverage, refusal on missing evidence, prompt injection.
- A latency/cost budget and trace retention.
- Red-team the agent against attempts to exfiltrate data or bypass the approval guard.

## 2. Inference — ONNX / Ascend

### ONNX Runtime path

`server/rootcause/npu/onnx_backend.py` is a real YOLO-style ONNX inference backend:

- letterbox to 640 × 640;
- ONNX Runtime session;
- confidence filter and NMS;
- normalised bounding box + latency;
- explicit `FileNotFoundError` when the model is missing.

Export the fine-tuned model:

```bash
cd server
python -m rootcause.training.finetune --data dataset/data.yaml --export onnx
```

Configure:

```bash
ROOTCAUSE_NPU_BACKEND=onnx
ROOTCAUSE_NPU_MODEL=/models/defect.onnx
ROOTCAUSE_NPU_IMGSZ=640
ROOTCAUSE_NPU_CONF=0.25
ROOTCAUSE_NPU_TOKEN=change-me
```

The broker service:

```bash
ROOTCAUSE_NPU_BACKEND=onnx ROOTCAUSE_NPU_MODEL=/models/defect.onnx \
  uvicorn rootcause.npu.service:app --host 127.0.0.1 --port 7788
curl http://127.0.0.1:7788/health
```

`POST /infer` requires `Authorization: Bearer <ROOTCAUSE_NPU_TOKEN>` when the token is set.

### Ascend path

`AscendBroker` keeps the same `/health` and `/infer` contract. On a site with the ACL runtime and a
compiled `.om` model, install the customer executor behind `npu/service.py`. Without it, the broker
returns **503/501**; it never pretends the CPU is an NPU.

### Still needed at the site

- Customer `.onnx` or `.om` model with checksum and version.
- Held-out accuracy evaluation against the customer's defect types.
- Latency/throughput benchmark on the actual edge box.
- NPU broker TLS/mTLS if it crosses a network boundary.

## 3. Connectors

Real paths:

- **OPC-UA** — `asyncua` sync client, tag reads.
- **Modbus** — `pymodbus` holding-register reads.
- **Siemens S7** — `python-snap7` DB reads.
- **Camera** — generic TCP trigger + metadata; HTTP JPEG snapshot.
- **MES/ERP** — CSV batch import.
- **CMMS/SAP QM/PM/REST** — HTTP JSON.
- **Normalisation** — tag mapping, unit mapping, QC counters.

Each connector defaults to `simulate=True` only when constructed without hardware. For production,
configure a real endpoint and set `simulate=False` in the site config. The readiness endpoint reports
`live` vs `simulated` connectors.

### Still needed at the site

- Network access, service accounts and read-only permissions.
- A tag map agreed with the customer; clock-drift measurement.
- A 24-hour soak and a known-defect replay.
- Secrets in a vault, rotation, and no credentials in the repository.

## 4. Data and storage

- SQLite with WAL is the single-site store; append-only audit triggers are active.
- Tenants are separate database files.
- The public/reference pack is **not** customer data. A production site must replace it with
  imported MES/quality/NPU data and record provenance.
- Reports and evidence exports are versioned; backups must restore the whole store.

### Still needed at the site

- Six-month historical import and a data-quality report.
- Customer data-processing agreement and retention schedule.
- Backup/restore drill and an evidence export test.

## 5. Security and operations

Implemented now:

- append-only audit triggers;
- signed webhook payloads with timestamp;
- NPU broker bearer token;
- tenant database isolation;
- offline operation with no outbound dependency.

Still needed:

- OIDC/SSO at the reverse proxy and server-side role checks (the UI role selector is not auth).
- TLS termination and network segmentation.
- Secrets vault, SBOM, dependency scanning.
- Metrics/tracing, log retention and alerting.
- Readiness/liveness probes and a rollback runbook.

## 6. Readiness

```bash
curl -i http://127.0.0.1:8000/api/ready
```

With `ROOTCAUSE_STRICT_INTEGRATIONS=1`, it returns **503** until:

1. the agent runtime is configured,
2. the NPU/ONNX broker reports ready,
3. at least one plant connector is live.

This is deliberate. A green UI on synthetic data is not a connected factory.
