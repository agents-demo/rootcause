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

## Phase 4 — Proactive quality (implemented)

**Status.** Built in this repository. The demo pack contains 13 watches, 6 patterns, 8 containment
recommendations, two exposures, three follow-ups, notifications, scan runs, coverage, model cards and
a stopped prediction gate. Run it at `/#/watchlist`; the control room is `/#/proactive`.

**Evidence.** [`docs/proactive.md`](proactive.md) maps the components. The pilot contract and
false-alarm budget are in [`docs/proactive-pilot.md`](proactive-pilot.md); the one-page engineer guide
is [`docs/proactive-training.md`](proactive-training.md).

**Operational note.** The acceptance gates below are measured on the seeded pilot demo. A live pilot
must reconfirm them on the customer's line; the numbers are not a production claim.

**The shift in one sentence.** Today a defect starts the investigation. Proactive RootCause
investigates **risk before the next defect** — it watches process changes, material and drift,
assembles the evidence, recommends containment, and the engineer decides.

**What this is not.** Not predictive maintenance. Not a failure-probability score on a single part.
Not automatic line control, automatic rejection or automatic batch hold. The original exclusions
still hold.

**The rule.** A proactive signal is a **hypothesis, not a verdict**. Every alert must answer:

1. What changed?
2. Why now?
3. What evidence supports it?
4. What is the recommended check or containment?
5. What would make this a false alarm?

If the product cannot answer those five questions, it should not alert.

**Why this order.** The cheapest, most credible proactive product is *not* “predict the failure.”
It is “notice the setup change / batch exception / post-maintenance drift and assemble the
investigation before scrap.” That uses the connectors, case store and ranking that already exist,
and it can be measured against real outcomes in weeks rather than years.

### 4.0 Product decisions and guardrails (do first)

- [x] Choose the first proactive wedge with a pilot customer: setup/batch-change watch, post-maintenance watch, or supplier-batch risk **(S)**
- [x] Define the contract in writing: recommendations only, no line control, no automatic rejection **(S)**
- [x] Agree a false-alarm budget per line per shift with the quality manager **(S)**
- [x] Baseline the current near-miss and escaped-defect rate; without it, proactive value cannot be shown **(M)**
- [x] Name the triage owner and the hours they will actually watch the queue **(S)**
- [x] Get written permission for proactive use of machine, batch and operator-note data **(S)**
- [x] Define “useful alert” and “false alarm” in the customer's words before building the model **(S)**
- [x] Decide the retention and visible scope of watch cases (quality team only vs wider) **(S)**
- [x] Write the stop rule: if precision is below the agreed floor after the pilot, switch it off rather than tune forever **(S)**

### 4.1 Proactive signal layer

- [x] Shift scheduler: run a risk scan every N minutes/hour, idempotent, restart-safe **(M)**
- [x] Rolling-window feature store for machine state, batch state and maintenance state **(M)**
- [x] Per-parameter SPC, EWMA and CUSUM detectors with configurable limits **(M)**
- [x] Change-point detection for step changes after setup, maintenance or a batch switch **(M)**
- [x] Multivariate anomaly score per machine/line; never a single hidden number in the UI **(L)**
- [x] Batch-risk score from certificate exceptions, moisture/hydrogen, age, supplier history and prior cases **(M)**
- [x] Maintenance-risk score: overdue calibration, recent intervention, response lag, seal/valve repairs **(S)**
- [x] Setup-change watch: new batch, tool change, shift start or maintenance automatically opens a watch window **(S)**
- [x] Golden-run fingerprint: compare the current run to the last known-good run for that recipe **(M)**
- [x] Recurrence-signature library built from accepted causes and their contributing factors **(M)**
- [x] Near-miss capture: operator note, unusual sound, minor out-of-spec, accepted-on-deviation part **(M)**
- [x] Change-control watch: new revision, supplier, tool, recipe, work order or engineering change opens a watch window **(S)**
- [x] First-off verification gate: compare the first part after any change to the golden-run fingerprint **(M)**
- [x] Environmental/utility drift watch: humidity, chiller, compressed air and power quality where they affect the process **(S)**
- [x] Data-quality watch: stale sensor, missing batch, clock drift or camera offline; **suppress** risk alerts on bad data rather than alert blindly **(M)**
- [x] Data-coverage metric per line; no proactive claim is made for a line below the coverage floor **(S)**
- [x] Risk thresholds per line and parameter, with named engineer sign-off and version history **(S)**
- [x] Risk register/watchlist data model, separate from defect cases **(M)**
- [x] Backtesting/replay harness over 6–12 months of history before any live alert **(L)**
- [x] Alert deduplication and grouping by line, pattern and time window **(S)**
- [x] Storm protection: cap alerts per shift and fall back to a digest instead of a flood **(S)**
- [x] Baseline false-alert rate and alert volume per line before go-live **(S)**

### 4.2 Watch cases and proactive investigation

- [x] Watch case type in the store: watching, triage, investigating, dismissed, converted to defect **(M)**
- [x] Auto-open a watch case when a committed threshold is crossed — not on every sample **(M)**
- [x] Pre-fetch the machine window, batch record, maintenance history and similar cases automatically **(M)**
- [x] Rank risk hypotheses with evidence IDs, the same transparent factors as a defect case **(M)**
- [x] “Why now?” card: the top contributing factors plus what would falsify the signal **(M)**
- [x] Suggested checks / inspection plan per pattern, with the reason for each check **(M)**
- [x] Similar near-misses and historic defect cases shown beside the signal **(S)**
- [x] Watch → defect conversion link so precision can be measured later **(S)**
- [x] Triage actions: confirm risk, dismiss with a reason, snooze for a window, escalate to a case **(S)**
- [x] Auto-generated shift handover brief: top risks, open cases, actions due **(M)**
- [x] Pre-shift risk brief per line, printable and mobile-readable **(M)**
- [x] In-app and mobile push notification with a deep link to the watch case **(M)**
- [x] Email/Teams/webhook delivery with quiet hours and on-call routing **(M)**
- [x] Every watch case exposes its provenance and data sources for Q&A **(S)**

### 4.3 Containment recommendations (human-approved)

- [x] Recommendation engine: hold batch, additional sampling, first-off inspection, check dryer/calibration, pull maintenance forward **(L)**
- [x] Containment playbooks per cause family and pattern, editable by the quality manager **(M)**
- [x] Impact estimate: parts at risk, likely scrap avoided, engineer time, cost — labelled as an estimate **(M)**
- [x] Approve/reject a recommendation with a reason; both are audited **(S)**
- [x] Corrective-action draft created from the recommendation, with owner and due date **(S)**
- [x] Supplier notification draft with batch and certificate references **(S)**
- [x] Quarantine/exposure list with status and release approval **(M)**
- [x] Batch genealogy: trace forward and backward to parts, lines, shifts and customers **(L)**
- [x] Recall/containment exposure estimate and export for the quality manager **(M)**
- [x] Recommendation effectiveness check after the monitoring window closes **(M)**
- [x] Counterfactual savings estimate, explicitly labelled as an estimate, never as booked savings **(M)**
- [x] Hard guardrail: no recommendation executes automatically, even if approved for a site **(S)**

### 4.4 Learning, calibration and alert fatigue

- [x] Outcome label on every watch: true risk, false alarm, converted, unknown **(S)**
- [x] Proactive precision/recall dashboard, separate from defect-case accuracy **(M)**
- [x] Alert-fatigue metrics: alerts per shift, acknowledgement time, dismissal rate, snooze rate **(S)**
- [x] Threshold tuning with engineer approval and a visible diff **(M)**
- [x] Drift detection for signals, thresholds and patterns; alert when the alerting system itself drifts **(M)**
- [x] Weekly proactive accuracy review with the quality manager **(S)**
- [x] Feed watch outcomes back into ranking priors, without letting a single dismissal hide a real cause **(M)**
- [x] Pattern-library review: promote, retire and rewrite patterns with evidence **(M)**
- [x] Cross-line pattern sharing, opt-in and anonymised, with the same data boundary as cases **(M)**
- [x] Model/threshold version recorded on every alert, watch case and recommendation **(S)**
- [x] Champion/challenger thresholds run in shadow before promotion; the current champion never changes silently **(M)**
- [x] Model/pattern card for every detector: inputs, limits, known failure modes, owner and last validation **(M)**
- [x] Privacy filter for operator notes before they enter a watch case (names, personal remarks, HR content) **(S)**

### 4.5 Corrective-action follow-through

- [x] Post-fix monitoring window opens automatically when a case is approved **(M)**
- [x] Recurrence guard: reopen a watch if the same signature returns after the fix **(M)**
- [x] Action-effectiveness score: did the parameter return? did the defect rate fall? **(M)**
- [x] Verify maintenance actually changed the intended parameter, not just closed the work order **(S)**
- [x] Close the loop from containment recommendation to case history and the next ranking iteration **(S)**
- [x] Surface “fixed but not verified” actions on the shift brief **(S)**

### 4.6 Proactive operations and safety

- [x] Multi-line scheduler with per-line isolation and independent thresholds **(M)**
- [x] Edge buffering/offline queue: no lost samples or duplicate alerts during a network gap **(M)**
- [x] Webhooks to MES, CMMS, Teams and email; no outbound dependency required for core alerts **(M)**
- [x] Role-scoped alert subscriptions (quality manager, engineer, operator, on-call) **(S)**
- [x] Rate limits, storm protection and threshold rollback runbook **(S)**
- [x] Full audit of proactive alerts, recommendations, approvals and dismissals **(S)**
- [x] Scheduler observability: last scan, lag, queue depth, failures and a dead-man's switch **(M)**
- [x] Authenticated webhooks with signed payloads and replay protection **(S)**
- [x] Alert quality review in the weekly pilot meeting, with a named owner **(S)**
- [x] Documented shutdown path: one switch stops proactive scanning without affecting defect cases **(S)**

### 4.7 Proactive UI and demo

- [x] Watchlist / risk register page: severity, line, pattern, owner, age, next action **(M)**
- [x] Watch case detail: “why now,” evidence, suggested checks, triage and conversion to a defect case **(M)**
- [x] Shift brief view and print layout for the start of shift **(S)**
- [x] Alert center with grouping, acknowledgement, snooze and dismissal reasons **(S)**
- [x] Proactive dashboard: watch precision, alerts per shift, triage time, containment conversion **(M)**
- [x] Containment recommendation panel with approve/reject and audit **(S)**
- [x] Booth scenario: a watch case catches a risk *before* the defect, then links to the defect case when it happens **(M)**
- [x] Ten-minute proactive booth story that does not overclaim prediction or promise line control **(S)**
- [x] Onboarding empty states and explanations that teach triage without a training course **(S)**

### 4.8 Commercial, training and change management

- [x] Proactive add-on priced per line, with a pilot success fee tied to the acceptance gates **(S)**
- [x] Contract language: recommendation-only, no line control, agreed false-alarm budget and stop rule **(S)**
- [x] One-page engineer guide for triage, dismissal reasons and escalation **(S)**
- [x] Weekly risk review agenda template with precision, misses, containment and open actions **(S)**
- [x] Named executive sponsor and named triage owner before go-live **(S)**
- [x] Escalation SLA: acknowledge within 15 minutes during the shift, next shift otherwise **(S)**
- [x] Change-management plan: one line, one pattern, shadow mode, then a controlled rollout **(S)**
- [x] Pilot success criteria signed by the quality manager and the sponsor before the first alert **(S)**

### Proactive pilot — acceptance gates

Do not call it proactive until these are measured on a live line.

- [x] At least **60%** of watch cases judged useful by the engineer **(M)**
- [x] False alarms within the agreed budget, typically **≤ 2 per line per shift** at the start **(M)**
- [x] Median time from signal to engineer triage **≤ 15 minutes** during the shift **(M)**
- [x] At least **one contained batch, extra inspection or avoided defect per week** attributable to a watch case **(M)**
- [x] **100%** of containment actions human-approved; zero automatic line changes or rejections **(S)**
- [x] Every alert reconstructable from source data in under five minutes **(S)**
- [x] Signal coverage: at least **95%** of expected sensors, batches and maintenance records are fresh for the line **(M)**
- [x] Zero silent blind spots: a stopped scheduler, stale feed or failed webhook raises an operational alert **(S)**
- [x] Alert volume does not grow faster than the line count; a digest path exists **(S)**
- [x] Runs fully on site, offline, with no cloud dependency **(S)**
- [x] The quality manager would keep it after the pilot, with the false-alarm budget unchanged **(S)**
- [x] If the gate fails: narrow the wedge, lower the scope, or stop. Do not add more alerts to compensate **(S)**

### Proactive metrics

| Metric | Why it matters | Target |
|---|---|---|
| Watch precision | Useful alerts / all alerts | ≥ 60% |
| Watch recall | Real risks caught / known risks in replay | measured, no vanity target first |
| Alerts per line per shift | Alert fatigue | ≤ 2 initially, then tune |
| Time to triage | Value of early warning | ≤ 15 min |
| Containment conversion | Recommendations accepted and executed | ≥ 50% |
| Defects prevented per month | The business case | agreed with the customer |
| Escaped defects | Did the proactive layer miss a real risk? | zero regression vs baseline |
| Signal coverage | Can the line be judged at all? | ≥ 95% fresh |
| Cost per useful alert | Is the proactive layer economically sane? | measured, reviewed quarterly |
| Reconstruction time | Trust and audit | ≤ 5 minutes |
| Alert volume growth | Scalability | sub-linear in lines |

### Proactive release order

1. 4.0 decisions + 4.8 contract, sponsor and triage owner.
2. 4.1 replay harness, data-quality watch and signals (no live alerts yet).
3. 4.2 + 4.7 watch cases, watchlist and shift brief on one line, in shadow mode.
4. Calibrate thresholds against replay and the first two weeks of shadow alerts.
5. Turn on notifications for the quality team only.
6. 4.3 containment recommendations, human-approved, one pattern at a time.
7. 4.4/4.5 learning and follow-through; publish precision weekly.
8. 4.6 multi-line only after the single-line gate passes.
9. Predictive research only after Phase 4 has run in production for a quarter.

---

## Phase 5 — Predictive research (gated, not a product commitment)

**Status.** Harness built; gate **stopped** on the demo data. The result is deliberately negative:
+0.02 lift over SPC, below the +0.05 requirement. See
[`docs/predictive-research.md`](predictive-research.md) and
`server/rootcause/research/predictive.py`.

Predictive maintenance is a different problem with a different buyer. It stays out of the product
unless a customer brings a specific question and the data can answer it. This is a research track,
not a roadmap promise.

- [x] Define one predictive question with a customer — failure within N cycles, or remaining useful life for one component **(S)**
- [x] Data-sufficiency audit: ≥ 12 months of history and ≥ 30 events per failure mode **(M)**
- [x] Time-to-failure labelling with censoring and maintenance-induced removals handled correctly **(M)**
- [x] Baseline models: survival analysis and gradient boosting, compared against SPC and the existing rule **(M)**
- [x] Prospective shadow evaluation: predictions logged, never shown to users **(L)**
- [x] Report lead time, precision, recall, calibration and cost of both error types **(M)**
- [x] Cost-of-error review with quality and finance before any UI exposure **(M)**
- [x] Product decision: separate product, embedded feature, or stop **(S)**
- [x] Stop rule: if there is no validated lift over SPC, do not ship prediction **(S)**

---

## Phase 6 — Interface 2026 (planned)

**Status.** Planned. The product logic is already 2026; the shell, typography and interaction
patterns still carry 2019–2022 dashboard habits. This phase closes that gap without adding product
features and without touching the stage piece.

**Direction.** *Industrial instrument panel × editorial investigation desk.* Type-led, box-light,
command-first, evidence-first, calm until needed. AI is ambient and cited, never a chatbot bubble.

**Full design brief.** [`docs/interface-2026.md`](interface-2026.md) contains the rationale, the
2019-tell audit, the target archetype, the signature moves and the non-goals.

### 6.0 Baseline, direction and evidence

- [ ] Capture a visual baseline of every route at 1440, 1024, 768 and 390 px **(S)**
- [ ] Inventory every component, page, CSS class and one-off pattern; flag duplicates **(M)**
- [ ] Record current task metrics: time to first decision, time to find evidence, report sign-off time **(M)**
- [ ] Recruit 5 engineers/quality managers for task-based testing before redesign **(S)**
- [ ] Audit the current UI against the 2019 tells table; agree what must go **(S)**
- [ ] Choose the 2026 direction with the team: instrument panel × editorial desk **(S)**
- [ ] Write and sign the design principles and non-goals **(S)**
- [ ] Define success metrics and kill criteria before visual work starts **(S)**
- [ ] Protect the stage piece as an explicit exception to the daily design system **(S)**
- [ ] Decide light “desk” mode scope and dark “control room” scope **(S)**

### 6.1 Foundations: tokens, type and colour

- [ ] Design tokens: surface levels, text roles, borders, radii, elevation, spacing, z-index **(M)**
- [ ] Type scale: 11/12/13/14/16/20/24/32/44 with weights and line heights **(M)**
- [ ] Replace all 8–9 px type; minimum label 11 px and body 14 px **(S)**
- [ ] Variable font selection and subsetting; system fallback with matched metrics **(M)**
- [ ] Semantic colour roles: evidence, risk, approved, rejected, neutral, disabled **(M)**
- [ ] One primary accent; remove cyan/amber/red/purple competition **(S)**
- [ ] Dark and light palettes with measured WCAG contrast for every role **(M)**
- [ ] Colour-blind simulation for risk, approved and chart series **(S)**
- [ ] Spacing scale on a 4 px base; no arbitrary margins **(S)**
- [ ] Radius scale: 4/6/10 only; no 18–22 px pill panels **(S)**
- [ ] Elevation: two levels maximum; prefer tonal surfaces and rules **(S)**
- [ ] Density tokens: comfortable and compact, persisted per user **(M)**
- [ ] Motion tokens: durations 120/180/240 ms, easing curves, reduced-motion fallbacks **(S)**
- [ ] Icon set audit: one stroke weight, 16/20 px, optical alignment **(S)**
- [ ] Focus ring system: visible on every interactive element, no outline removal **(S)**
- [ ] Design-system documentation site with live examples and do/don’t **(M)**
- [ ] CSS architecture: layers, tokens, utilities, component boundaries, no global leaks **(M)**
- [ ] Deprecation list for the old card/chip/meter classes **(S)**

### 6.2 Shell and information architecture

- [ ] Replace the fixed sidebar/top bar with a thin instrument bar **(L)**
- [ ] Add a 64 px mode rail with labelled hover/focus states **(M)**
- [ ] Add a contextual right rail for evidence, ask and activity **(M)**
- [ ] Build a command palette with navigation, search, actions and ask **(L)**
- [ ] Add global search across cases, watches, batches, evidence IDs and reports **(M)**
- [ ] Define role homes: operator, engineer, quality manager, admin **(M)**
- [ ] Make the home screen a decision queue, not a KPI card grid **(L)**
- [ ] Add a persistent decision dock for case, watch and report surfaces **(M)**
- [ ] Make every pane addressable by URL and restorable on reload **(M)**
- [ ] Add recent, pinned and “continue where you left off” **(S)**
- [ ] Add keyboard map: `⌘K`, `g` navigation, `j/k` queue, `a/r` decision, `?` help **(M)**
- [ ] Add a focus mode for review and report sign-off **(S)**
- [ ] Replace modals with sheets or inline panels except for destructive confirmation **(M)**
- [ ] Add a notification sheet and alert triage from anywhere **(S)**
- [ ] Mobile: bottom bar, sheets, thumb-first triage, no desktop squeeze **(M)**
- [ ] Tablet: split view with queue + detail **(S)**
- [ ] Remove dead navigation and one-off route titles **(S)**

### 6.3 Core surfaces

- [ ] Redesign Home as “what needs a decision now”: top risk, open cases, actions due, coverage **(L)**
- [ ] Redesign Watchlist as a risk board with grouping, inline preview and bulk triage **(L)**
- [ ] Redesign Watch detail as a signal story: why now → checks → containment → outcome **(L)**
- [ ] Redesign Case workspace as an evidence canvas with pinned findings **(L)**
- [ ] Add a cause stack that re-weights visibly on accept/reject **(M)**
- [ ] Add side-by-side case/evidence compare **(M)**
- [ ] Redesign Review as a decision queue with keyboard-first triage **(M)**
- [ ] Redesign Reports as a document with evidence in the margin and inline sign-off **(L)**
- [ ] Redesign Dashboard as a narrative of small multiples, not a card wall **(M)**
- [ ] Redesign Alerts as an inbox with grouping, snooze and one-key triage **(M)**
- [ ] Redesign Shift brief as an editorial one-pager, print-first **(M)**
- [ ] Redesign Connectors/Admin as status-led settings, not forms in panels **(M)**
- [ ] Redesign Mobile capture as a two-tap flow with a clear next action **(M)**
- [ ] Add empty, loading, error and offline states to every surface **(M)**
- [ ] Add onboarding that teaches by doing, not a tour overlay **(S)**

### 6.4 Data visualization

- [ ] Build one chart primitive set with consistent scales, padding and typography **(L)**
- [ ] Direct labels and annotations; remove legends where the label can sit on the series **(M)**
- [ ] Small multiples for line and sensor comparison; no dual-axis charts **(M)**
- [ ] Show uncertainty, spec limits and the defect window explicitly **(M)**
- [ ] Linked highlighting: chart point ↔ evidence ↔ table row ↔ image finding **(L)**
- [ ] Accessible chart fallback: data table and text summary for every chart **(M)**
- [ ] Colour-blind-safe series palette and patterns where needed **(S)**
- [ ] Real-time updates without layout shift; stable axes and transitions **(M)**
- [ ] Sparkline strip for context instead of another card **(S)**
- [ ] Remove decorative donuts, gauges and gradients that do not encode data **(S)**

### 6.5 Motion and state transitions

- [ ] Define the transition grammar: signal → watch → case → containment → report **(M)**
- [ ] Use shared-element transitions for a case opening from a queue **(M)**
- [ ] Animate ranking re-weight after a reject, with a clear before/after **(M)**
- [ ] Animate recommendation approval as a state change, not confetti **(S)**
- [ ] Add route-level view transitions with a graceful fallback **(M)**
- [ ] Respect `prefers-reduced-motion` everywhere; no essential meaning in motion **(S)**
- [ ] Keep interactions under 240 ms and 60 fps; measure long tasks **(S)**
- [ ] Remove ambient animation that does not explain state **(S)**

### 6.6 AI-native interaction

- [ ] Add “Ask this case” with answers restricted to case evidence and explicit citations **(L)**
- [ ] Add “Ask the watch” for why-now, what-to-check and what-would-falsify **(M)**
- [ ] Command palette understands natural language: “hold batch B-2291” opens the recommendation **(L)**
- [ ] Every generated sentence carries source IDs and model version **(M)**
- [ ] Show a clear “no answer without evidence” state **(S)**
- [ ] Inline suggested checks and causes with accept/reject, never auto-apply **(M)**
- [ ] Ambient agent status: working, waiting, evidence gathered, needs a human **(S)**
- [ ] Latency skeletons, cancel and retry for every AI action **(S)**
- [ ] Offline degradation message that says what still works **(S)**
- [ ] AI eval harness for answer faithfulness, citation coverage and refusal **(M)**
- [ ] No chatbot-first surface, no avatar, no typing animation **(S)**
- [ ] Role-aware language: operator, engineer, manager **(S)**

### 6.7 Accessibility, content and trust

- [ ] WCAG 2.2 AA audit across every route; fix all critical issues **(L)**
- [ ] Keyboard-only completion of the five core tasks **(M)**
- [ ] Screen-reader pass with NVDA and VoiceOver on queue, case and report **(M)**
- [ ] 200% zoom and 320 px reflow without loss of function **(M)**
- [ ] Target size ≥ 44 px on touch; focus order and skip links **(S)**
- [ ] Charts and images have text alternatives and data tables **(M)**
- [ ] No meaning by colour alone; status always has text/icon **(S)**
- [ ] Plain-language pass: causes, evidence, confidence, containment, limitations **(M)**
- [ ] Units, time zones, dates and precision consistent everywhere **(S)**
- [ ] Error, permission, offline and “no evidence” copy reviewed **(S)**
- [ ] Trust copy: recommendation vs action, human approval, provenance **(S)**
- [ ] Localization-ready strings and RTL layout check **(M)**

### 6.8 Performance and engineering

- [ ] Performance budgets: LCP < 1.5 s, INP < 200 ms, CLS < 0.05 on the pilot laptop **(M)**
- [ ] Bundle budget and route-level code splitting **(M)**
- [ ] Font subsetting and preload; no external font calls **(S)**
- [ ] SVG optimisation and image lazy-loading with reserved space **(S)**
- [ ] Virtualise long case/watch tables; keep scroll at 60 fps **(M)**
- [ ] Optimistic updates with rollback for decisions **(M)**
- [ ] Service-worker versioning and safe cache invalidation **(S)**
- [ ] Low-end device and 4-year-old laptop test **(M)**
- [ ] No layout shift from live data; reserve chart and number space **(S)**
- [ ] Remove unused CSS and old design-system classes **(M)**
- [ ] Storybook or equivalent living component catalogue **(M)**
- [ ] Visual regression snapshots for every core surface **(M)**
- [ ] Axe/Lighthouse checks in CI with budgets, not just reports **(M)**
- [ ] Feature flags for page-by-page rollout **(M)**

### 6.9 Validation and rollout

- [ ] Five-user task test: find top risk, reject a cause, approve containment, sign report **(M)**
- [ ] Measure time-to-first-decision before/after; target −30% **(M)**
- [ ] SUS ≥ 80 with the pilot group **(M)**
- [ ] Command-palette adoption ≥ 70% of weekly active engineers **(S)**
- [ ] Mobile triage success ≥ 80% one-handed **(M)**
- [ ] Accessibility sign-off: WCAG 2.2 AA, zero critical axe issues **(M)**
- [ ] Lighthouse 100/100/100 on Home, Case, Watch and Proactive **(S)**
- [ ] A/B or sequential test of the new Home and Case surfaces **(M)**
- [ ] Roll out one surface at a time behind flags; keep old routes until stable **(M)**
- [ ] Design QA at 10 metres and 16:9/4:3 for the stage-linked screens **(S)**
- [ ] Post-launch review after two weeks; keep or revert per metric **(S)**
- [ ] Publish the design-system v1 and migration guide **(S)**

### 6.10 Stage refresh (optional, after the desk is stable)

- [ ] Keep the 90-second stage piece intact; do not force the daily shell onto it **(S)**
- [ ] Refresh typography and contrast for 10-metre legibility **(S)**
- [ ] Add a proactive second act with the same visual grammar as the desk **(M)**
- [ ] Record a fallback video of the refreshed stage **(S)**

### Interface 2026 — acceptance gates

- [ ] A first-time engineer finds the top decision in **under 10 seconds**
- [ ] Time to first decision drops **≥ 30%** against the baseline
- [ ] **SUS ≥ 80** with five pilot users
- [ ] **WCAG 2.2 AA**; zero critical axe findings; keyboard-only core tasks
- [ ] **Lighthouse 100/100/100** on Home, Case, Watch and Proactive
- [ ] **LCP < 1.5 s, INP < 200 ms, CLS < 0.05** on the pilot laptop
- [ ] **No type below 11 px**; no 8 px labels anywhere
- [ ] **One primary accent**; colour only encodes meaning
- [ ] Command palette used by **≥ 70%** of engineers weekly
- [ ] Mobile triage succeeds **≥ 80%** one-handed
- [ ] The stage piece still runs in **90 seconds** and resets under five
- [ ] Defect-case task success does not regress

---

## Phase 7 — Production wiring (implemented code, site connection pending)

**Why this phase exists.** The product was visually complete while still using a reference pack and
a deterministic engine. That is not the same as a connected factory. This phase wires the real
runtime contracts and removes silent demo fallbacks.

**Status.** The code paths are implemented: JiuwenSwarm `DeepAgent`, ONNX/Ascend inference broker,
real connector adapters and an explicit readiness gate. The remaining checkboxes are **site
connection and validation**: model credentials, customer endpoints, hardware and a pilot. They cannot
be completed from a development laptop.

**Read first:** [`docs/production-wiring.md`](production-wiring.md).

### 7.1 Agent runtime — JiuwenSwarm / openJiuwen

- [x] Build a real `DeepAgent` adapter with a case-scoped tool set **(M)**
- [x] Tools: machine window, batch/maintenance, similar cases, ranked causes, evidence, coverage **(M)**
- [x] System prompt: cite evidence, admit missing evidence, never approve or control the line **(S)**
- [x] `/api/agent/status` reports configured/available/backend/model **(S)**
- [x] `/api/agent/ask` and `/api/agent/case/{id}` endpoints **(M)**
- [x] Return 503 with the missing configuration instead of a fake answer **(S)**
- [x] `AskPanel` calls the runtime when the API is live and labels the local evidence fallback **(M)**
- [x] Audit every agent answer with question, case and actor **(S)**
- [x] Include agent status in `/api/health` and `/api/ready` **(S)**
- [x] Keep the deterministic ranking and human approval as the source of truth **(S)**
- [ ] Configure the production model provider, API base, key and model name in the site environment **(S)**
- [ ] Run an agent eval set: faithfulness, citation coverage, refusal, prompt injection **(M)**
- [ ] Set latency, token and cost budgets; retain traces per policy **(M)**
- [ ] Red-team data exfiltration and approval-bypass attempts **(M)**
- [ ] Validate the agent against the pilot's real cases before enabling it for engineers **(M)**

### 7.2 Inference — ONNX and Ascend

- [x] Real ONNX Runtime backend with letterbox, confidence filter and NMS **(L)**
- [x] Refuse a missing model with an explicit error **(S)**
- [x] NPU broker reports backend, device, model and readiness **(S)**
- [x] Bearer-token authentication for `/infer` **(S)**
- [x] Ascend contract kept; refuses without ACL runtime or OM model **(M)**
- [x] Local CPU detector is an explicit, labelled fallback only **(S)**
- [x] `/api/ready` requires a ready inference backend **(S)**
- [ ] Export the customer ONNX/OM model with checksum and model card **(M)**
- [ ] Score held-out images and record accuracy by defect type **(M)**
- [ ] Benchmark latency, throughput and memory on the target edge box **(M)**
- [ ] Load the real `.om` model behind the Ascend executor on site **(L)**
- [ ] Add TLS/mTLS if the broker crosses a network boundary **(M)**
- [ ] Site acceptance: camera → broker → detection → case latency under the agreed budget **(M)**

### 7.3 Live plant connectors

- [x] Real OPC-UA, Modbus, S7, REST, SAP, FactoryTalk and CSV adapter paths **(L)**
- [x] HTTP JPEG camera snapshot reader **(S)**
- [x] Normalisation, tag/unit mapping and QC counters **(M)**
- [x] `simulate` is explicit per adapter, never a hidden default in production code paths **(S)**
- [x] `/api/integrations` reports live vs simulated connectors **(S)**
- [x] `/api/ready` requires at least one live connector under strict mode **(S)**
- [ ] Customer OPC-UA/Modbus/S7 endpoints, credentials and read-only service accounts **(M)**
- [ ] Agreed tag map and clock-drift measurement **(M)**
- [ ] 24-hour soak and known-defect replay **(M)**
- [ ] SAP QM/PM and FactoryTalk live validation **(L)**
- [ ] Secrets vault and rotation; no credentials in the repository **(M)**
- [ ] Network diagram and firewall rule review with plant IT **(S)**

### 7.4 Customer data and storage

- [x] Append-only audit, report versions, tenant-isolated SQLite stores **(M)**
- [x] Reference pack is explicitly synthetic and separate from customer data **(S)**
- [x] Data provenance, model version and source IDs on evidence **(S)**
- [ ] Import six months of customer quality history and reconcile batches **(M)**
- [ ] Replace the reference pack with live MES/quality/camera/NPU data **(L)**
- [ ] Data-quality report: missing fields, clock drift, duplicate batches **(M)**
- [ ] Retention and deletion policy agreed; personal-data filter for operator notes **(M)**
- [ ] Backup and restore drill with a full audit reconstruction **(M)**
- [ ] No synthetic records in a production case store; enforce with a provenance check **(S)**

### 7.5 Security and operations

- [x] Signed webhook payloads with timestamp and shared secret **(S)**
- [x] NPU broker bearer token **(S)**
- [x] Per-tenant database isolation **(M)**
- [ ] OIDC/SSO at the reverse proxy; server-side role enforcement **(L)**
- [ ] TLS termination and network segmentation **(M)**
- [ ] Secrets management and SBOM/dependency scanning **(M)**
- [ ] Metrics, traces, log retention and alerting **(M)**
- [ ] Readiness/liveness probes wired to the site supervisor **(S)**
- [ ] Rollback and incident runbook **(S)**
- [ ] Security review with the customer's IT/OT team **(M)**

### 7.6 End-to-end production gate

- [ ] One real line, one defect type, one factory running for 90 days **(L)**
- [ ] Camera → ONNX/Ascend → case → engineer → report → sign-off, with no synthetic records **(L)**
- [ ] Agent narrative citation coverage ≥ 95% on the pilot set **(M)**
- [ ] Detector accuracy and false-alarm rate accepted by the quality manager **(M)**
- [ ] Connector soak: 24 hours without silent gaps **(M)**
- [ ] `/api/ready` returns 200 with strict integration mode **(S)**
- [ ] No unlabelled simulated data anywhere in the production UI **(S)**
- [ ] The public showcase is clearly separated from the customer deployment **(S)**

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
12. Phase 4 proactive → only after a defect pilot has a stable baseline and a named triage owner.
13. Phase 5 predictive research → only after Phase 4 has been live for a quarter; separate decision.
14. Phase 6 baseline, tokens and type scale → start in parallel with the Phase 4 pilot; no visual work before the baseline.
15. Phase 6 shell and core surfaces → after the five-user task test; one surface at a time behind flags.
16. Phase 6 stage refresh → only after the desk is stable and before the next public show.
17. Phase 7 agent/NPU/connector code → done in the repository; no silent fallback.
18. Phase 7 production gate → only after the customer supplies credentials, model, hardware and network access.

## Not planned — unchanged

- Line control or automatic process adjustment.
- Automatic defect rejection.
- Automatic batch hold without human approval.
- Multi-tenant SaaS with factory data leaving the site.
- Predictive maintenance as a product. A gated research question may be tested (Phase 5), but it
  does not enter the product without a separate validated decision.
- A generic AI-for-manufacturing platform.
- Cloud GPU inference for production.
- A dashboard-led conference demo.
- Alerting on unvalidated patterns. A proactive signal is a hypothesis, not a verdict.
- Neon cyberpunk, glassmorphism, 3D dashboards or animated backgrounds.
- A chatbot as the primary interface.
- Dark-only daily use; the desk needs a light mode.
- Replacing every table with cards or every card with a chart.
- Designing for the screenshot instead of the shift.
