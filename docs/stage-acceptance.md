# Stage acceptance test sheet

Run three times: a normal room, a hostile audience, and with the network cable unplugged.

## Before the room

- [ ] Venue contrast test at 10 metres: the 9px mono labels still read; the 16:9 and 4:3 crops both
  keep the crack and the evidence rail visible.
- [ ] Sound cue at the reveal; silence under the trust beat.
- [ ] Reset `R` under five seconds, three times in a row.
- [ ] Backup laptop has the built static site and a 90-second recording.
- [ ] Network cable unplugged; page reloaded from cache.
- [ ] `APPROVED` stamp and printed case sheet on the bench.

## Five strangers

Ask each person, after the 90 seconds, without prompting:

1. “What does it do?” — pass if they say the product finds the cause and writes the report.
2. “What was wrong with the first answer?” — pass if they mention the crack starts below the
  surface / tool marks are surface-only.
3. “Who decides?” — pass if they say the engineer.

Target: four of five can explain the product in one sentence. Seven of ten can repeat the closing
line.

## Interaction

- [ ] First touch within 15 seconds without instruction.
- [ ] The x-ray reveal lands by 30 seconds.
- [ ] Full arc in 90 seconds.
- [ ] Two volunteers complete the lens-and-depth interaction unassisted.
- [ ] Auto-scan path works as the accessibility/fallback path.

## Hostile Q&A

| Question | Answer |
|---|---|
| “Is this a real AI or a video?” | “The workflow is real; the data is a synthetic pack. Drag the lens anywhere — the findings are live, the ranking recomputes when you reject a cause.” |
| “Did you train a model on customer images?” | “No. The public demo uses synthetic images and a deterministic detector. Fine-tuning is a pilot step with written permission.” |
| “What is the accuracy number?” | “We do not put a single number on stage. The pilot measures first-cause acceptance by an engineer and publishes it weekly.” |
| “Why did it get it wrong?” | “Because it is evidence-weighted, not omniscient. It had surface evidence; the subsurface evidence only arrived after the depth reveal. The engineer caught it. That is the product.” |
| “Can it control the line?” | “No. No automatic line control, no automatic rejection. The engineer decides.” |
| “Where does the data go?” | “Nowhere. The NPU and the case store sit on the factory network. There is no cloud inference.” |
| “Is MVTec used?” | “No. MVTec AD is non-commercial; the public pack is generated in-house.” |
| “What if the customer has no labelled data?” | “Start with one defect type and a small labelled set from the existing inspection camera. The workflow is useful even before a fine-tuned model beats the current rule.” |

## Metrics to record

- Time to first touch (target ≤ 15 s)
- Time to the reveal (≤ 30 s)
- Full run (≤ 90 s)
- Volunteer success (≥ 80%)
- Qualified conversations (≥ 20)
- Pilot intros booked (≥ 5)

## Reset

`R` clears the case state: rejected causes, accepted cause, manual causes, report edits and approval.
The next run starts from the cold open with the same seeded pack.
