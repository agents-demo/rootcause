# Integration status

What is coded, what is wired to run live, and what is actually running. Last verified 2026-10-30
against the local API on ports 8017/8018 (`/api/agent/status`, `/api/integrations`, `/api/ready`).

| Service | Why we need it / what the app does with it | Code | Wired live | Running |
|---|---|---|---|---|
| **openjiuwen DeepAgent** | Answers engineer questions and writes case narratives over the evidence, with citations; never ranks or approves | Yes | Yes | **Yes** |
| **DeepSeek `deepseek-v4-pro`** | The model behind the agent: cited answers, refusals, disagreement notes | Yes | Yes | **Yes** |
| **SQLite store + audit** | Persists decisions, reports, corrections, approvals, watches and an append-only audit trail | Yes | Yes | **Yes** |
| **OPC-UA** | Reads machine tags (temperature, pressure, cycle) to build the 3-hour machine window per case | Yes (`asyncua`) | No — forced `simulate=True` | No |
| **Modbus** | Reads holding registers from older presses that have no OPC-UA | Yes (`pymodbus`) | No | No |
| **Siemens S7** | Reads DB blocks from Siemens PLCs on the line | Yes (`snap7`) | No | No |
| **FactoryTalk** | OPC-UA access to Rockwell/FactoryTalk tags | Partial (OPC-UA subclass) | No | No |
| **Camera — HTTP snapshot** | Pulls a defect photo into the case and the detector | Yes | No | No |
| **Camera — TCP trigger** | Triggers an industrial camera and reads the frame header | Minimal | No | No |
| **MES / quality CSV** | Imports batches, quality history and supplier certificates into cases | Yes (parser) | No | No |
| **SAP QM / PM / CMMS** | Pulls inspection lots, work orders and maintenance history | Generic REST GET, no auth/OData | No | No |
| **ONNX Runtime** | Runs the defect detector on an image: bbox, confidence, latency | Yes | Needs `.onnx` model | No — `local-cpu` fallback |
| **Ascend NPU** | Production inference path on the edge box | Client yes; ACL executor returns 501 | No hardware | No |
| **NPU broker** | Isolated on-site inference service with bearer-token auth | Yes | Not started | No |
| **SSO / OIDC** | Real user identity and server-side roles (the role picker is not auth) | **Not coded** | — | No |
| **TLS / mTLS** | Encrypts API and broker traffic across the network boundary | **Not coded** | — | No |
| **Secrets vault** | Stores plant and model credentials outside the repo | **Not coded** | — | No |
| **Proactive scheduler** | Scans machine/batch signals on an interval and opens watches before defects | Yes | Opt-in (`ROOTCAUSE_SCHEDULER=1`) | No |
| **GitHub Pages** | Hosts the static UI for the public showcase | Static build | N/A | **Yes**, no backend |

## So what

- The agent, the model and the local database are doing real work.
- Every factory protocol is written but never switched out of simulation, so the app currently has no
  physical input.
- ONNX and Ascend need a model and hardware.
- SSO, TLS and the vault do not exist in code yet.
- `ROOTCAUSE_DATA_MODE=production` plus `/api/ready` refuse to claim readiness while synthetic cases
  exist or a connector is missing.

## Code gaps behind the "No" column

1. `server/rootcause/connectors/__init__.py:registry()` constructs every connector with
   `simulate=True`, even when an endpoint is supplied.
2. `POST /api/connectors/{id}/test` also hardcodes `simulate=True`.
3. `/api/ready` counts a connector as live from the presence of `ROOTCAUSE_*_ENDPOINT`, not from a
   successful connection.
4. Tests cover only the simulated path.

Closing these is local work. Validating them needs a real endpoint, credentials and network access.

See also: [production wiring](production-wiring.md), [roadmap Phase 7](roadmap.md#phase-7--production-wiring-implemented-code-site-connection-pending).
