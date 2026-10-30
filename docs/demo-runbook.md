# Manager demo runbook

Two cuts, one product. Run the 90-second teardown at the booth and the 10-minute cut in a room.
Both start from **Now**, both end on a human signature, and neither claims a number the reference
pack does not support.

- 90 seconds, on stage: `/stage`
- 10 minutes, guided in-app: `/cut`
- Proof sheet: `/proof`
- Weekly series: `/dashboard`

## Before the run: pick the workspace

The app opens in **My workspace** by default: blank, with cases you enter in this browser. For the manager
cut, switch to **Reference data** first — Admin → Workspace data, the command palette, the More sheet, or the
button on the My cases screen. The choice persists.

## Reality check before the run

| Claim | State |
|---|---|
| Daily shell | Interface 2026 is **shipped** (Phase 6, 0 unchecked): instrument bar, command palette, decision queue, evidence canvas, light desk mode |
| Now is the home | **Shipped**: `/` is the decision queue, not a dashboard |
| Agent | **Live** openjiuwen `DeepAgent` with `deepseek-v4-pro` on the local/on-site API; `/api/agent/ask` verified |
| ONNX / NPU | **Code only**; no model or Ascend hardware installed — do not claim it |
| Plant connectors | **Adapters only**; no OPC-UA/Modbus/MES endpoint configured — the UI labels them simulated |
| Data | **Synthetic reference pack, fixed seed 417**; no customer data |
| Public site | Static reference build; no backend calls |

If someone asks “is this real?”, the answer is the table, not a slogan.

## The 10-minute cut

Open `/cut` and start the clock. Each step has a link and a proof point; tick it when done.

| Time | Step | Say | Proof |
|---|---|---|---|
| 0:00 | Now | Five kinds of decision need a human: watch triage, cause decisions, report drafts, corrective actions, coverage. One queue, one job. | The queue is the daily workspace |
| 1:30 | Case `RC-0417` | A turbine bracket failed at the root fillet. Defect, machine window, batch and evidence before any AI opinion. | Evidence first |
| 3:30 | Reject the top cause | RootCause ranks tool mark first. The crack starts 0.4 mm below the surface. Reject it and give the reason. | Human judgement re-ranks the case; the reason is stored |
| 5:00 | Sign the report | The report is drafted from the evidence you just reviewed. Sign it; the version is recorded. | Engineer sign-off time is measured |
| 6:30 | Shift brief | What the next shift inherits: open watches, building risk, checks that would prove a false alarm. | Prevention is a named watch |
| 7:30 | Watchlist / watch case | A watch is a hypothesis: what changed, why now, what to check, what would make it false. | Proactive logic over signals |
| 8:30 | Manager proof | Baseline to current, acceptance, prevented scrap, engineer hours. One line, one defect type, 90 days. | The numbers the manager is accountable for |

Close on the sentence:

> “From 51 hours to 3.6 hours; the engineer still signs.”

Then name the pilot target explicitly: **three days to 90 minutes on the customer's own baseline**,
measured weekly. Do not present the target as a result.

## The 90-second stage cut

Physical, not a screen tour. Props: failed bracket, loupe or macro lens, x-ray print, printed case
sheet, stamp.

| Time | Beat |
|---|---|
| 0:00 | Put the failed bracket on the table. Say nothing. |
| 0:10 | Now: five decisions, one queue. |
| 0:20 | Case: the defect and the machine window. |
| 0:35 | AI proposes tool mark / operator error. |
| 0:45 | Loupe on the fracture: the crack starts below the surface. |
| 1:00 | Reject the cause with the reason. The ranking moves. |
| 1:15 | X-ray, batch hydrogen, the same supplier heat. |
| 1:25 | Stamp the verdict. The engineer signs. |
| 1:30 | “Pilot target: three days to 90 minutes. The engineer still signs.” |

## What changes for the quality manager

Use `/proof` as the slide:

- **Fewer repeated causes.** A rejected cause is stored with the reason and re-ranks the next case.
- **Faster reports.** The report is drafted from the same evidence the engineer reviewed.
- **Fewer escalations.** The shift brief names open watches before the defect.
- **Audit-ready evidence.** Evidence, corrections, versions and approvals are append-only.

Buyer: plant quality manager; the plant manager signs the pilot. Start with one line and one defect
type for 90 days. Success is engineer-accepted causes, time to cause, report sign-off time and
prevented scrap, reviewed weekly against baseline.

## Reset and fallback

- `Reset the run` on `/cut` clears the checklist and the reference store.
- Reset must take under five seconds; rehearse it before every session.
- The static build runs with the network cable unplugged. Keep a local copy of the proof sheet.
- If the model is slow (p50 ~28 s), narrate the evidence instead of waiting on a spinner.
- Never claim the NPU, a live connector or customer data unless the screen shows it.

## Definition of done for the demo

- Five strangers: four can explain RootCause in one sentence.
- First touch within 15 seconds; the reveal lands by 30; the full arc in 90.
- Reset under five seconds; works offline.
- A manager can state the proof metric and the buyer without prompting.
- Now, the case, the report and the watchlist feel like one job, not four screens.
