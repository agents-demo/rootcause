# Compliance evidence maps

The admin screen ships three maps. They are **evidence maps for a pilot review, not certificates**.
A notified body performs the audit. The UI can export each map as Markdown.

## ISO 9001:2015

| Control | How RootCause supports it |
|---|---|
| Case ownership and responsibility | Every case has a line, an engineer and a quality owner; assignment is audited. |
| Documented investigation method | Five visible factors, tool trace, evidence IDs. |
| Approval before closure | The AI cannot approve. A named engineer signs the report. |
| Corrective action loop | Actions have owner, due date, status and saving estimate. |
| Record retention | Local SQLite store, report versions, append-only audit triggers. |
| Management review | Weekly accuracy, time-to-cause and savings reporting. |

## IATF 16949:2016

| Control | How RootCause supports it |
|---|---|
| Part traceability | Serial, batch and line on every case. |
| Supplier quality evidence | Batch certificate, incoming checks and deviations attached. |
| Process change control | Maintenance events and process deviations in the evidence package. |
| PPAP evidence export | Report and evidence appendix as PDF/Word. |
| Control plan linkage | Defect type mapped to inspection station/line. |
| Containment record | Quarantine actions with owner and due date. |

Gaps before a real automotive audit: control-plan identifiers, customer-specific PPAP templates and
a validated training matrix. Those are site configuration, not code.

## FDA 21 CFR Part 11

| Requirement | Where it lives |
|---|---|
| Electronic signature | Report approval with actor name, scope and timestamp. |
| Immutable audit trail | `audits` triggers reject UPDATE/DELETE; report versions are insert-only. |
| Reason for change | Rejection and manual-cause actions record a reason. |
| Access control | Role-based UI today; put the API behind the site SSO before production. |
| Data integrity | Append-only case store, versioned reports, provenance per evidence item. |
| Retention | On-site store; export package for the quality record. |

**Validation is not included.** A pharma/medtech deployment needs an IQ/OQ/PQ package, a validated
identity provider and a written retention policy. The demo shows the audit mechanism, not a
validated system.

## Data retention

- Case records: 7 years (configurable).
- Report versions: 7 years; superseded versions are retained.
- Audit events: append-only, never deleted by the application.
- Images: stay on site; the demo deletes uploads after inference.
- Cross-factory sharing: off by default; cause labels and factor ranges only.

## Export

`GET /api/compliance/{iso9001|iatf|fda}` returns the control map as JSON. The admin UI exports it as
Markdown, which can be attached to a pilot review pack.
