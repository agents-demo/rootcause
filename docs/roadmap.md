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

## Phase 4 — Proactive quality (planned)

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

- [ ] Choose the first proactive wedge with a pilot customer: setup/batch-change watch, post-maintenance watch, or supplier-batch risk **(S)**
- [ ] Define the contract in writing: recommendations only, no line control, no automatic rejection **(S)**
- [ ] Agree a false-alarm budget per line per shift with the quality manager **(S)**
- [ ] Baseline the current near-miss and escaped-defect rate; without it, proactive value cannot be shown **(M)**
- [ ] Name the triage owner and the hours they will actually watch the queue **(S)**
- [ ] Get written permission for proactive use of machine, batch and operator-note data **(S)**
- [ ] Define “useful alert” and “false alarm” in the customer's words before building the model **(S)**
- [ ] Decide the retention and visible scope of watch cases (quality team only vs wider) **(S)**
- [ ] Write the stop rule: if precision is below the agreed floor after the pilot, switch it off rather than tune forever **(S)**

### 4.1 Proactive signal layer

- [ ] Shift scheduler: run a risk scan every N minutes/hour, idempotent, restart-safe **(M)**
- [ ] Rolling-window feature store for machine state, batch state and maintenance state **(M)**
- [ ] Per-parameter SPC, EWMA and CUSUM detectors with configurable limits **(M)**
- [ ] Change-point detection for step changes after setup, maintenance or a batch switch **(M)**
- [ ] Multivariate anomaly score per machine/line; never a single hidden number in the UI **(L)**
- [ ] Batch-risk score from certificate exceptions, moisture/hydrogen, age, supplier history and prior cases **(M)**
- [ ] Maintenance-risk score: overdue calibration, recent intervention, response lag, seal/valve repairs **(S)**
- [ ] Setup-change watch: new batch, tool change, shift start or maintenance automatically opens a watch window **(S)**
- [ ] Golden-run fingerprint: compare the current run to the last known-good run for that recipe **(M)**
- [ ] Recurrence-signature library built from accepted causes and their contributing factors **(M)**
- [ ] Near-miss capture: operator note, unusual sound, minor out-of-spec, accepted-on-deviation part **(M)**
- [ ] Change-control watch: new revision, supplier, tool, recipe, work order or engineering change opens a watch window **(S)**
- [ ] First-off verification gate: compare the first part after any change to the golden-run fingerprint **(M)**
- [ ] Environmental/utility drift watch: humidity, chiller, compressed air and power quality where they affect the process **(S)**
- [ ] Data-quality watch: stale sensor, missing batch, clock drift or camera offline; **suppress** risk alerts on bad data rather than alert blindly **(M)**
- [ ] Data-coverage metric per line; no proactive claim is made for a line below the coverage floor **(S)**
- [ ] Risk thresholds per line and parameter, with named engineer sign-off and version history **(S)**
- [ ] Risk register/watchlist data model, separate from defect cases **(M)**
- [ ] Backtesting/replay harness over 6–12 months of history before any live alert **(L)**
- [ ] Alert deduplication and grouping by line, pattern and time window **(S)**
- [ ] Storm protection: cap alerts per shift and fall back to a digest instead of a flood **(S)**
- [ ] Baseline false-alert rate and alert volume per line before go-live **(S)**

### 4.2 Watch cases and proactive investigation

- [ ] Watch case type in the store: watching, triage, investigating, dismissed, converted to defect **(M)**
- [ ] Auto-open a watch case when a committed threshold is crossed — not on every sample **(M)**
- [ ] Pre-fetch the machine window, batch record, maintenance history and similar cases automatically **(M)**
- [ ] Rank risk hypotheses with evidence IDs, the same transparent factors as a defect case **(M)**
- [ ] “Why now?” card: the top contributing factors plus what would falsify the signal **(M)**
- [ ] Suggested checks / inspection plan per pattern, with the reason for each check **(M)**
- [ ] Similar near-misses and historic defect cases shown beside the signal **(S)**
- [ ] Watch → defect conversion link so precision can be measured later **(S)**
- [ ] Triage actions: confirm risk, dismiss with a reason, snooze for a window, escalate to a case **(S)**
- [ ] Auto-generated shift handover brief: top risks, open cases, actions due **(M)**
- [ ] Pre-shift risk brief per line, printable and mobile-readable **(M)**
- [ ] In-app and mobile push notification with a deep link to the watch case **(M)**
- [ ] Email/Teams/webhook delivery with quiet hours and on-call routing **(M)**
- [ ] Every watch case exposes its provenance and data sources for Q&A **(S)**

### 4.3 Containment recommendations (human-approved)

- [ ] Recommendation engine: hold batch, additional sampling, first-off inspection, check dryer/calibration, pull maintenance forward **(L)**
- [ ] Containment playbooks per cause family and pattern, editable by the quality manager **(M)**
- [ ] Impact estimate: parts at risk, likely scrap avoided, engineer time, cost — labelled as an estimate **(M)**
- [ ] Approve/reject a recommendation with a reason; both are audited **(S)**
- [ ] Corrective-action draft created from the recommendation, with owner and due date **(S)**
- [ ] Supplier notification draft with batch and certificate references **(S)**
- [ ] Quarantine/exposure list with status and release approval **(M)**
- [ ] Batch genealogy: trace forward and backward to parts, lines, shifts and customers **(L)**
- [ ] Recall/containment exposure estimate and export for the quality manager **(M)**
- [ ] Recommendation effectiveness check after the monitoring window closes **(M)**
- [ ] Counterfactual savings estimate, explicitly labelled as an estimate, never as booked savings **(M)**
- [ ] Hard guardrail: no recommendation executes automatically, even if approved for a site **(S)**

### 4.4 Learning, calibration and alert fatigue

- [ ] Outcome label on every watch: true risk, false alarm, converted, unknown **(S)**
- [ ] Proactive precision/recall dashboard, separate from defect-case accuracy **(M)**
- [ ] Alert-fatigue metrics: alerts per shift, acknowledgement time, dismissal rate, snooze rate **(S)**
- [ ] Threshold tuning with engineer approval and a visible diff **(M)**
- [ ] Drift detection for signals, thresholds and patterns; alert when the alerting system itself drifts **(M)**
- [ ] Weekly proactive accuracy review with the quality manager **(S)**
- [ ] Feed watch outcomes back into ranking priors, without letting a single dismissal hide a real cause **(M)**
- [ ] Pattern-library review: promote, retire and rewrite patterns with evidence **(M)**
- [ ] Cross-line pattern sharing, opt-in and anonymised, with the same data boundary as cases **(M)**
- [ ] Model/threshold version recorded on every alert, watch case and recommendation **(S)**
- [ ] Champion/challenger thresholds run in shadow before promotion; the current champion never changes silently **(M)**
- [ ] Model/pattern card for every detector: inputs, limits, known failure modes, owner and last validation **(M)**
- [ ] Privacy filter for operator notes before they enter a watch case (names, personal remarks, HR content) **(S)**

### 4.5 Corrective-action follow-through

- [ ] Post-fix monitoring window opens automatically when a case is approved **(M)**
- [ ] Recurrence guard: reopen a watch if the same signature returns after the fix **(M)**
- [ ] Action-effectiveness score: did the parameter return? did the defect rate fall? **(M)**
- [ ] Verify maintenance actually changed the intended parameter, not just closed the work order **(S)**
- [ ] Close the loop from containment recommendation to case history and the next ranking iteration **(S)**
- [ ] Surface “fixed but not verified” actions on the shift brief **(S)**

### 4.6 Proactive operations and safety

- [ ] Multi-line scheduler with per-line isolation and independent thresholds **(M)**
- [ ] Edge buffering/offline queue: no lost samples or duplicate alerts during a network gap **(M)**
- [ ] Webhooks to MES, CMMS, Teams and email; no outbound dependency required for core alerts **(M)**
- [ ] Role-scoped alert subscriptions (quality manager, engineer, operator, on-call) **(S)**
- [ ] Rate limits, storm protection and threshold rollback runbook **(S)**
- [ ] Full audit of proactive alerts, recommendations, approvals and dismissals **(S)**
- [ ] Scheduler observability: last scan, lag, queue depth, failures and a dead-man's switch **(M)**
- [ ] Authenticated webhooks with signed payloads and replay protection **(S)**
- [ ] Alert quality review in the weekly pilot meeting, with a named owner **(S)**
- [ ] Documented shutdown path: one switch stops proactive scanning without affecting defect cases **(S)**

### 4.7 Proactive UI and demo

- [ ] Watchlist / risk register page: severity, line, pattern, owner, age, next action **(M)**
- [ ] Watch case detail: “why now,” evidence, suggested checks, triage and conversion to a defect case **(M)**
- [ ] Shift brief view and print layout for the start of shift **(S)**
- [ ] Alert center with grouping, acknowledgement, snooze and dismissal reasons **(S)**
- [ ] Proactive dashboard: watch precision, alerts per shift, triage time, containment conversion **(M)**
- [ ] Containment recommendation panel with approve/reject and audit **(S)**
- [ ] Booth scenario: a watch case catches a risk *before* the defect, then links to the defect case when it happens **(M)**
- [ ] Ten-minute proactive booth story that does not overclaim prediction or promise line control **(S)**
- [ ] Onboarding empty states and explanations that teach triage without a training course **(S)**

### 4.8 Commercial, training and change management

- [ ] Proactive add-on priced per line, with a pilot success fee tied to the acceptance gates **(S)**
- [ ] Contract language: recommendation-only, no line control, agreed false-alarm budget and stop rule **(S)**
- [ ] One-page engineer guide for triage, dismissal reasons and escalation **(S)**
- [ ] Weekly risk review agenda template with precision, misses, containment and open actions **(S)**
- [ ] Named executive sponsor and named triage owner before go-live **(S)**
- [ ] Escalation SLA: acknowledge within 15 minutes during the shift, next shift otherwise **(S)**
- [ ] Change-management plan: one line, one pattern, shadow mode, then a controlled rollout **(S)**
- [ ] Pilot success criteria signed by the quality manager and the sponsor before the first alert **(S)**

### Proactive pilot — acceptance gates

Do not call it proactive until these are measured on a live line.

- [ ] At least **60%** of watch cases judged useful by the engineer **(M)**
- [ ] False alarms within the agreed budget, typically **≤ 2 per line per shift** at the start **(M)**
- [ ] Median time from signal to engineer triage **≤ 15 minutes** during the shift **(M)**
- [ ] At least **one contained batch, extra inspection or avoided defect per week** attributable to a watch case **(M)**
- [ ] **100%** of containment actions human-approved; zero automatic line changes or rejections **(S)**
- [ ] Every alert reconstructable from source data in under five minutes **(S)**
- [ ] Signal coverage: at least **95%** of expected sensors, batches and maintenance records are fresh for the line **(M)**
- [ ] Zero silent blind spots: a stopped scheduler, stale feed or failed webhook raises an operational alert **(S)**
- [ ] Alert volume does not grow faster than the line count; a digest path exists **(S)**
- [ ] Runs fully on site, offline, with no cloud dependency **(S)**
- [ ] The quality manager would keep it after the pilot, with the false-alarm budget unchanged **(S)**
- [ ] If the gate fails: narrow the wedge, lower the scope, or stop. Do not add more alerts to compensate **(S)**

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

Predictive maintenance is a different problem with a different buyer. It stays out of the product
unless a customer brings a specific question and the data can answer it. This is a research track,
not a roadmap promise.

- [ ] Define one predictive question with a customer — failure within N cycles, or remaining useful life for one component **(S)**
- [ ] Data-sufficiency audit: ≥ 12 months of history and ≥ 30 events per failure mode **(M)**
- [ ] Time-to-failure labelling with censoring and maintenance-induced removals handled correctly **(M)**
- [ ] Baseline models: survival analysis and gradient boosting, compared against SPC and the existing rule **(M)**
- [ ] Prospective shadow evaluation: predictions logged, never shown to users **(L)**
- [ ] Report lead time, precision, recall, calibration and cost of both error types **(M)**
- [ ] Cost-of-error review with quality and finance before any UI exposure **(M)**
- [ ] Product decision: separate product, embedded feature, or stop **(S)**
- [ ] Stop rule: if there is no validated lift over SPC, do not ship prediction **(S)**

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
