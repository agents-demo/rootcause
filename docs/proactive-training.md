# Proactive quality — one-page engineer guide

**A watch is a hypothesis, not a verdict.** You decide. The system never touches the line.

## When you see a watch

1. **Read “Why now?”** It lists the signals, the parameter, the deviation and the evidence.
2. **Read “What would falsify this?”** If the explanation is benign, dismiss it with the reason.
3. **Start triage** if it is plausible. The watch gets an owner and an SLA.
4. **Run the suggested checks.** Tick them off; the case records who did what.
5. **Approve, reject or change the containment recommendation.**
   - Hold batch, extra sampling, first-off, check dryer/calibration, pull maintenance.
   - Approving a recommendation does **not** execute it. The team executes; the system records.
6. **Label the outcome** when you know:
   - **Converted** — it became a defect case.
   - **True risk** — useful, but containment prevented a defect.
   - **False alarm** — benign explanation.
   - **Operational** — a data-quality or camera issue, not a quality false alarm.

## The five questions you should be able to answer

- What changed?
- Why now?
- What evidence supports it?
- What should I check or contain?
- What would make this a false alarm?

If any answer is missing, do not act on the alert; tell the quality manager.

## What not to do

- Do not treat a watch as a defect. It may never become one.
- Do not ignore a critical watch because the alarms were noisy last week; use the dismissal reason and
  the weekly review to fix the threshold.
- Do not execute a containment that was not approved by a named engineer.
- Do not edit the threshold to “make the alert go away”. Propose the change; the quality manager
  signs it.

## Shift brief

At the start of the shift, open **Shift brief**. It lists the top risks, open cases, actions due and
“fixed but not verified”. If the brief says coverage is below 95%, treat the line as partially blind
and rely on the physical inspection gate.

## Escalation

- Critical/high: acknowledge within 15 minutes.
- Medium/low: next shift or the digest.
- Scheduler stopped or stale coverage: operational alert; call plant IT.
- A containment that cannot be executed: reject it with a reason and escalate to the quality manager.

## The sentence

> The defect is late. The signal was early. I still decide.
