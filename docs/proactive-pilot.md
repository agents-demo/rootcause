# Proactive pilot — contract, roles and change management

This is the one-page agreement for a proactive pilot. It is deliberately separate from the defect
pilot: proactive alerting changes how people spend their attention, so it needs its own contract,
owner and stop rule.

## The contract in one paragraph

> RootCause may scan the agreed line for risk signals and open **watch cases**. It may recommend
> containment, inspection or maintenance. It will not control the line, reject a part or hold a
> batch automatically. Every recommendation is approved by a named engineer. The site may stop
> proactive scanning at any time without affecting defect cases. The false-alarm budget and the
> stop rule are agreed before the first alert.

## Product decisions before go-live

- **First wedge:** choose one — setup/batch-change watch, post-maintenance watch, or supplier-batch
  risk. The demo uses post-maintenance seal + hydrogen on Line 6.
- **Useful alert:** an engineer judges that the watch saved a check, a containment or a case; the
  reason is recorded.
- **False alarm:** the signal had a benign explanation (settling, sensor artefact, approved change).
- **False-alarm budget:** typically ≤ 2 per line per shift at the start.
- **Triage owner:** a named engineer and the hours they actually watch the queue.
- **Stop rule:** if precision is below 50% after four weeks, narrow the wedge or stop. Do not add
  alerts to compensate.
- **Retention:** watch cases and outcomes follow the case retention policy; operator notes are
  filtered for personal data.
- **Permission:** written permission for proactive use of machine, batch and operator-note data.

## Roles

| Role | Responsibility |
|---|---|
| Quality manager | Owns the pilot, the false-alarm budget and the weekly review; signs off threshold changes |
| Manufacturing engineer | Triages watches, runs checks, approves/rejects containment |
| Operator | Captures near-misses and unusual conditions; does not need to interpret the model |
| Plant IT | Network, OPC-UA/camera/MES access, on-site deployment, scheduler health |
| RootCause | Connectors, signal layer, calibration, training, weekly review, stop/start |
| Executive sponsor | Sees the containment and cost outcome; owns the decision to expand |

## Escalation SLA

- Critical/high: acknowledge within **15 minutes** during the shift.
- Medium/low: next shift, or the quiet-hours digest.
- A stopped scheduler or stale coverage raises an **operational** alert, not a quality risk.

## Training — one page

See [proactive-training.md](proactive-training.md). The engineer learns three actions: triage,
approve/reject containment, and label the outcome. Nothing else is required to start.

## Weekly risk review — 30 minutes

1. Precision this week: useful / all outcomes; compare with the budget.
2. Misses and escaped defects: what did the layer not see?
3. Alert fatigue: alerts per line per shift, dismissal rate, snooze rate.
4. Containment: what was approved, executed, verified; what did it save?
5. Follow-ups: what is “fixed but not verified”?
6. Threshold/pattern changes proposed; who signs?
7. Decision: continue, narrow, expand, or stop.

## Change management

1. **Shadow mode:** one line, one pattern, no notifications. The team sees the watches in the UI.
2. **Calibrate:** replay + two weeks of shadow; set thresholds and false-alarm budget.
3. **Quality team only:** in-app + Teams; no operator push.
4. **One containment pattern:** approve/execute by the engineer; measure.
5. **Expand:** second pattern, then second line. Never both at once.
6. **Stop switch test:** prove the stop works and defect cases still work before go-live.

## Success criteria (signed before the first alert)

- ≥ 60% of watches judged useful by the engineer.
- False alarms within the agreed budget.
- Median triage ≤ 15 minutes during the shift.
- ≥ 1 contained batch / extra inspection / avoided defect per week attributable to a watch.
- 100% human-approved containment; zero automatic line changes or rejections.
- Coverage ≥ 95%; zero silent blind spots.
- The quality manager would keep it after the pilot at the same false-alarm budget.

## Commercial model

- Proactive add-on per line, in addition to the defect-case plan.
- Pilot success fee tied to the gates above.
- No charge for the research gate; it is explicitly not a product commitment.

## What we will not do

- Automatic line control, rejection or batch hold.
- Ship prediction without a validated lift over SPC.
- Alert on a line below the coverage floor.
- Let an alert become a notification without a watch case, evidence and a falsification note.
- Hide false alarms; they are the data that makes the layer usable.
