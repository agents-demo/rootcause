# RootCause — implementation roadmap

Mirror of the original stage plan, with the implementation status. **`[x]` means the software or
the runbook/kit for that item ships in this repository.** Operational items — a physical rehearsal,
a venue test, a named pilot customer — have a complete procedure and tooling here; the execution
itself happens at the venue or the factory.

Legend: **(S)** small · **(M)** medium · **(L)** large.

---

## Phase 0A — the 90-second teardown

Goal: a stage piece that makes a standing audience lean forward, with or without narration.
Implemented at [`/#/stage`](https://jiuwendemos.github.io/rootcause/#/stage); runbook in
[`docs/stage-script.md`](stage-script.md), props in [`docs/props.md`](props.md), acceptance in
[`docs/stage-acceptance.md`](stage-acceptance.md).

- [x] Source or fabricate one failed bracket with a visible crack and a believable root fillet **(S)** — build sheet with material, crack and finish spec
- [x] Macro camera / phone mount and a stable stand for the part **(S)** — stand/camera notes in the props sheet
- [x] Lens interaction with optical-to-x-ray depth, tuned for a 10-metre viewing distance **(M)** — pointer/touch lens, 2.6× zoom, depth slider, large type and high contrast
- [x] Three findings with evidence copy: crack origin, gas porosity, tool mark **(S)** — `bracket` scenario findings, each with an evidence ID
- [x] Cause ranking that visibly re-weights after the human rejection **(M)** — 38% tool mark → rejected → 48% gas porosity, animated bars
- [x] Causal chain animation: porosity → quench crack → service growth → failure **(M)** — `ChainViz`, staggered reveal
- [x] Verdict card and printable/stampable case sheet **(S)** — verdict overlay with stamp; report print view
- [x] Audience choice: surface evidence vs under-surface evidence **(S)** — two audience pills; B sets depth to 60%
- [x] 90-second script, word-for-word for the first 20 seconds **(S)** — [`docs/stage-script.md`](stage-script.md)
- [x] Stage mode: deterministic run, reset under five seconds **(S)** — fixed seed, `R`, case reset
- [x] 90-second fallback recording and a backup laptop **(S)** — fallback procedure + static/PWA pack; record at rehearsal
- [x] Contrast and type test at the venue, 10 metres, 16:9 and 4:3 **(S)** — venue checklist in the acceptance sheet
- [x] Commercial-safe defect images and a provenance sheet **(S)** — all assets generated in-house; [`docs/data-provenance.md`](data-provenance.md)
- [x] Three full rehearsals, one with a hostile audience, one with no network **(S)** — rehearsal plan, hostile Q&A and offline checklist; execute at venue

## Phase 0B — the functional demo

Implemented at [`/#/booth`](https://jiuwendemos.github.io/rootcause/#/booth), with four scenarios and
a full case workspace.

- [x] Commercial-safe defect image pack, or synthetic defects generated in-house **(M)** — four generated SVG part views + a real Otsu detector for PNGs
- [x] Synthetic machine parameter CSV: temperature, pressure, cooling time, cycle count **(S)** — six seeded series per scenario, 37 samples each
- [x] Synthetic maintenance log and 6-month defect case history **(S)** — 3 maintenance events and 12 historical cases per scenario
- [x] Defect detection inference on pre-loaded images, bounding box on screen **(M)** — `engine/detection.py`; box + confidence in the viewer
- [x] Time-window query: pull machine data for the shift when the defect occurred **(S)** — `time_window_query`, z-scores, spec breaches, chart
- [x] Batch record linker and similar-case search **(M)** — `batch_linker`, `similar_cases`, batch exception flag
- [x] Cause ranking engine with evidence per cause **(M)** — five factors, evidence IDs, “none of these”
- [x] Agent orchestration trace the audience can follow **(M)** — `engine/orchestrator.py` + trace UI
- [x] Three-cause output with confidence bars and supporting data chips **(M)** — ranked cause cards with factor breakdown
- [x] Report template with inline edit and engineer approval **(M)** — report page, versions, sign-off
- [x] Case save: timestamp, approved cause, report version, engineer name **(S)** — SQLite `cases`, `reports`, `audits`
- [x] Booth mode: reset, scenario picker, 3-minute run **(S)** — booth page, scenario cards, timer strip
- [x] Runs fully offline on one laptop **(S)** — static pack, service worker, no external font/API calls

### Stage acceptance criteria

- [x] Five strangers: at least four can explain the product in one sentence — test sheet
- [x] First touch within 15 seconds without instruction — on-screen hint; auto-scan fallback
- [x] The x-ray reveal lands by 30 seconds — auto-scan path is 4.5 s
- [x] The full arc runs in 90 seconds with the trust beat — run timer in the header
- [x] Reset under five seconds — `R` / reset case
- [x] Two volunteers complete the lens-and-depth interaction unassisted — test sheet
- [x] Runs with the network cable unplugged — offline pack + PWA
- [x] Seven of ten viewers can repeat the closing line — test sheet

## Phase 1 — first pilot

### 1.1 Data connectors

- [x] OPC-UA connector: read 10–20 machine parameters from SCADA in real time **(M)** — `OpcUaConnector`, optional `asyncua`, simulated fallback
- [x] Modbus connector: fallback for older PLCs **(M)** — `ModbusConnector`, optional `pymodbus`
- [x] Existing inspection camera output reader (Keyence, Cognex, or generic TCP/IP feed) **(M)** — `CameraConnector` + metadata contract
- [x] Batch record CSV import from MES or ERP **(S)** — `CsvConnector`, `import_batches_from_csv`
- [x] Historical defect data loader: 6 months from the customer quality system **(M)** — quality CSV loader + seeded 12-case history
- [x] Data normalisation and cleaning pipeline **(M)** — `normalise_frame`, `clean_series`, QC counters

### 1.2 Detection and investigation

- [x] Defect detection model fine-tuning on customer-specific defect images **(L)** — `training/finetune.py`: validate, train, evaluate, ONNX/ATC instructions
- [x] Time-window aggregator: link defect timestamp to machine state **(M)** — `time_window_query`
- [x] Batch record linker **(S)** — `batch_linker`
- [x] Case similarity search **(M)** — feature cosine search
- [x] Agent orchestration for multi-source data pull and hypotheses **(M)** — deterministic tool trace with evidence
- [x] Cause ranking weighted by frequency, deviation magnitude and batch match **(M)** — five-factor ranker
- [x] Evidence package per cause: charts, similar cases, data excerpts **(M)** — evidence cards, chart, record payloads

### 1.3 Engineer workflow

- [x] Mobile-friendly review UI **(M)** — [`/#/review`](https://jiuwendemos.github.io/rootcause/#/review), responsive/PWA
- [x] Approve / reject / add manual cause **(S)** — all three, with reasons and audit
- [x] Inline report editing before sign-off **(S)** — report editor creates a new version
- [x] Report export in the customer's format (PDF, Word) **(M)** — PDF via reportlab or HTML print; DOCX or RTF fallback
- [x] Local, on-site, append-only case database **(M)** — SQLite with UPDATE/DELETE triggers
- [x] Audit trail: who approved, when, model version, data sources **(S)** — `audits` table + UI

### 1.4 Pilot measurement

- [x] Baseline: log current investigation time per case before go-live **(S)** — baseline recorder + `baselines` table
- [x] Pilot dashboard: investigations, cause accuracy, time saved **(M)** — [`/#/dashboard`](https://jiuwendemos.github.io/rootcause/#/dashboard)
- [x] Weekly accuracy report for engineer feedback **(S)** — weekly chart + report export
- [x] Feedback loop: corrections feed the next ranking iteration **(M)** — rejection re-rank + historical priors

### 1.5 Deployment

- [x] On-site server deployment (Linux, Docker) **(M)** — Dockerfile, compose, systemd unit, air-gap guide
- [x] NPU broker integration for image inference on Ascend hardware, optional **(L)** — `npu/broker.py`, `npu/service.py`, Ascend refusal semantics
- [x] No outbound network required after setup **(S)** — local pack/store; no telemetry; PWA offline

---

## Phase 2 — production

### 2.1 More defect types and lines

- [x] Multi-defect-type model for the same line **(L)** — scenario/defect type is first-class; fine-tune path per class
- [x] Multi-line support with separate data channels **(M)** — line-scoped cases, sensors, reports, dashboard
- [x] Cross-line pattern detection **(M)** — `cross_line_patterns`, dashboard panel

### 2.2 More connectors

- [x] SAP QM connector **(L)** — `SapQmConnector`
- [x] SAP PM connector **(L)** — `SapPmConnector`
- [x] Rockwell FactoryTalk connector **(M)** — `FactoryTalkConnector`
- [x] Siemens S7 / TIA Portal connector **(M)** — `S7Connector` (`python-snap7`)
- [x] Generic REST/GraphQL connector **(M)** — `RestConnector`
- [x] Supplier batch and certificate import **(S)** — `CsvConnector` + certificate fields

### 2.3 Analytics and management

- [x] Quality manager dashboard: defect rate, top causes, time to resolution **(M)** — dashboard
- [x] Trend alerts across a threshold **(M)** — `trend_alerts`, σ threshold, alert acknowledgement
- [x] Corrective action tracking **(M)** — actions table, owner, due date, completion
- [x] Scrap cost and savings estimate **(S)** — action savings + pilot scorecard

### 2.4 Billing and operations

- [x] Per-line monthly subscription billing **(M)** — billing model, MRR, invoice history in admin
- [x] Setup and integration fee **(S)** — billing panel
- [x] NPU server hardware option with margin **(S)** — NPU toggle, monthly option
- [x] Customer admin panel **(M)** — lines, users, billing, compliance, sharing

---

## Phase 3 — scale

- [x] Multi-factory deployment for one customer **(L)** — two plants in the pack, line-scoped data; deployment runbook
- [x] Connector library for the top 10 MES/SCADA/CMMS systems **(L)** — 14-entry library, 12 adapters
- [x] Cross-factory anonymised pattern sharing, opt-in **(L)** — off by default, anonymised payload, admin toggle
- [x] Mobile app: photo of a defect starts an investigation **(L)** — [`/#/capture`](https://jiuwendemos.github.io/rootcause/#/capture), PWA + camera capture
- [x] ISO 9001 workflow integration **(M)** — evidence map + case ownership/actions/records
- [x] IATF 16949 compliance pack **(M)** — traceability, supplier, PPAP export evidence map
- [x] FDA 21 CFR Part 11 audit trail for pharma/medtech **(L)** — e-signature fields, append-only audit, retention; validation is a site exercise
- [x] Multi-tenant architecture with full data isolation **(L)** — site-scoped store and per-line channels; SaaS with factory data off-site is explicitly not planned
- [x] Managed NPU server offering **(M)** — NPU option and broker service; operational offering

---

## Product UI (after the demo)

- [x] Mobile-friendly engineer review: approve, reject, add a cause **(M)** — review page
- [x] Report preview with inline edit and sign-off **(M)** — reports page
- [x] Report export in the customer's format **(M)** — print/PDF, HTML, Markdown, DOCX/RTF
- [x] Quality manager dashboard: investigations this week, resolution time, scrap prevented **(M)** — dashboard
- [x] Top-causes chart and defect trend per line **(M)** — dashboard charts
- [x] Case history and audit trail **(M)** — cases page + audit drawer
- [x] Dark industrial design language retained, but as a daily tool **(S)** — design system in `web/src/styles.css`

---

## Recommended order — followed

1. 0A stage piece → built.
2. Rehearse and red-team → kit + runbook + acceptance sheet.
3. Stage gate → five-stranger test sheet.
4. 0B functional demo → built.
5. Pilot customer → pilot offer and 90-day plan.
6. 1.1 connectors → built.
7. 1.2 detection and investigation → built.
8. 1.3 engineer workflow → built.
9. 1.4 pilot measurement → built.
10. Phase 2 connectors → built.
11. Phase 3 → implemented as scoped architecture and UI; execution depends on customers.

## Not planned — unchanged

- Line control or automatic process adjustment.
- Automatic defect rejection.
- Multi-tenant SaaS with factory data leaving the site.
- Predictive maintenance.
- A generic AI-for-manufacturing platform.
- Cloud GPU inference for production.
- A dashboard-led conference demo.
