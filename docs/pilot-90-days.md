# Pilot in 90 days

**One factory. One line. One defect type.** Run alongside the existing process; do not replace it.
No line control. No automatic rejection. The engineer decides.

## Week 0 — the gate

- The stage piece has passed the acceptance sheet (`docs/stage-acceptance.md`).
- A quality manager has signed the pilot scope.
- A line with a high-value defect, existing inspection cameras and machine data is available.
- Written data-use permission is on file.

## Days 1–15 — baseline and connections

| Work | Acceptance |
|---|---|
| Record the current investigation time per case | At least 20 historical cases, median and range |
| Connect OPC-UA (10–20 parameters) | Values match the SCADA screen; 24 h stable |
| Connect the inspection camera | Frames arrive; a manual trigger produces a detection |
| Import six months of quality history | Batch and cause fields mapped; row count reconciled |
| Import batches and maintenance | Batch ids join cleanly; maintenance dates parse |
| Deploy on site (Docker or systemd) | `GET /api/health` returns `ok`; no outbound network |
| Load the detector | A held-out image set is scored; latency recorded |

## Days 16–45 — the investigation loop

Run 10–20 real investigations with an engineer in the loop.

- Each case: defect → evidence → ranked causes → engineer decision → report.
- Rejections record a reason and feed the next ranking iteration.
- Weekly accuracy review: first-cause acceptance, misses, time to cause.
- The engineer can add a cause the AI missed. That is data, not failure.

**Gate:** median time to cause is at least 5× lower than the baseline, and the engineer would keep
using it.

## Days 46–75 — the report and the money

- Report exports in the customer's format (PDF/Word). Sign-off recorded.
- Baseline vs pilot: scrap, rework, engineer hours, time to cause.
- Corrective actions tracked with owner and due date.
- A second defect type on the same line, if the first is stable.

**Gate:** the quality manager can show a named saving and a signed report to the plant manager.

## Days 76–90 — the repeatable deployment

- Document the connector map, tag normalisation and any customer-specific quirks.
- Hand over runbooks: backup, restore, model update, user onboarding.
- Agree the expansion: second line, second defect type, or a second factory.
- Publish the weekly accuracy report for the pilot sponsor.

## Metrics

| Metric | Target | Source |
|---|---|---|
| Time to cause | ≤ 10% of baseline | case timestamps |
| First-cause acceptance | ≥ 75% | engineer decision |
| False alarms | ≤ 15% | rejected cases |
| Report cycle time | same day | report approval |
| Engineer hours saved | ≥ 50 per month | case count × saved hours |
| Scrap + rework prevented | agreed with finance | corrective actions |
| Cases with complete evidence | 100% | audit trail |

## Roles

- **Quality manager** — owns the pilot, signs reports, reviews accuracy weekly.
- **Manufacturing engineer** — uses the case workspace, accepts/rejects causes.
- **Plant IT** — network, OPC-UA credentials, camera access, on-site server.
- **RootCause** — connectors, ranking, deployment, weekly review, model update.
- **Sponsor** — plant manager; sees the savings and the gate decision.

## What we will not do

- Control the line, change setpoints or reject parts automatically.
- Send images or process data to a cloud service.
- Claim a single accuracy number without provenance.
- Replace the existing quality system or the inspection camera vendor.
- Start a second site before the first has three months of production use.
