# The 90-second teardown — stage script and kit

**Goal.** Make a standing audience lean forward. No narration required after the first 20 seconds.
The physical part is the anchor; the screen is the lens.

Live: [`/#/stage`](https://jiuwendemos.github.io/rootcause/#/stage)

---

## Beat sheet

| Time | Beat | Action | Screen |
|---|---|---|---|
| 0:00–0:10 | Cold open | Hold the failed bracket. “Line 6. 1,842 hours. The report said metal fatigue.” | Case header, part photo |
| 0:10–0:25 | First touch | Put the part down; drag the lens | Loupe over the root fillet |
| 0:25–0:38 | Surface evidence | Find the crack origin and the tool mark | Finding markers, evidence chips |
| 0:38–0:52 | Trust beat | AI proposes tool mark / operator error; the engineer rejects it | Ranking flips; confidence bars re-weight |
| 0:52–1:08 | The reveal | Push depth to x-ray; porosity cluster appears; chain assembles | X-ray, causal chain |
| 1:08–1:20 | Verdict | Cause approved; the case sheet prints and stamps | White case sheet, `APPROVED` |
| 1:20–1:30 | The line | “It wasn't fatigue. It started in the casting.” | QR/link to the playable demo; reset |

The live piece shows a **RUN** timer against 1:30. Reset is `R` (under five seconds, back to the
cold open).

---

## Word-for-word, first 20 seconds

> “This bracket came off Line 6 after 1,842 hours in service. The quality report said metal
> fatigue. That is a description of how it broke, not why it started. We have one minute and
> thirty seconds to find out what actually happened.”
>
> *(place the part, pick up the loupe, drag across the screen)*
>
> “The camera sees a defect in a second. The investigation is the hard part. Watch the surface.”

Then stop narrating. Let the interaction carry the next 40 seconds.

---

## The trust beat, in detail

- The first hypothesis is **tool mark / operator error**. There is a real machining ridge near the
  crack; it is the kind of answer a quality manager hears every week.
- The engineer rejects it for a visible reason: **the crack starts 0.4 mm below the surface; tool
  marks are surface-only.**
- The system re-ranks in the same scene: **gas porosity, largest void 0.8 mm, aligned with the crack
  path.** Tool mark falls from 38% to 1.6%; gas porosity rises from 30% to 48%.
- Say one sentence: *“It was confident. It was wrong. This is why the engineer stays in charge.”*
- The correction is saved to the case and the audit trail immediately. That is the learning story
  without a fake accuracy number.

## Audience agency

Let the room choose which evidence to open first:

- **A — surface:** crack origin and tool mark.
- **B — under the surface:** porosity cluster.

Either order works. B is the reveal. Commit to the room's choice, then: *“The tool mark is real. It
is also a decoy.”* In the UI the choice is the two pills above the bench; choosing B sets depth to
60% so the x-ray is available.

---

## Kit list

- One failed bracket with a visible crack and a believable root fillet. The 3D-print/CAD spec and
  the paint/taping notes are in `docs/props.md`.
- A macro camera or phone on a stable stand. The screen is the lens for the audience; the physical
  loupe is used once, on a lanyard, so the metaphor is not only digital.
- One large screen, 16:9 preferred, 4:3 tested. Run the contrast test in the venue at 10 metres.
- A printed case sheet and an `APPROVED` stamp. The stamp is the sound cue.
- One low industrial hum; one impact at the reveal; silence under the trust beat.
- Red key light for the failure claim, amber for the reveal, white for the verdict.
- Backup laptop with the static build; network cable unplugged on purpose.

## Fallback

If the projector or laptop fails, the story still works with the physical part and the printed case
sheet. Keep a 90-second screen recording from the last rehearsal on the backup laptop and on a
phone. The page is a PWA and works offline after first load; the static build is in `web/dist`.

## Rehearsal and acceptance

- [x] Five strangers: at least four can explain the product in one sentence. *(test sheet in
  `docs/stage-acceptance.md`)*
- [x] First touch within 15 seconds without instruction. *(the hint is on the bench; auto-scan is
  the accessibility fallback)*
- [x] The x-ray reveal lands by 30 seconds. *(auto-scan path is 4.5 s; manual path is presenter-led)*
- [x] The full arc runs in 90 seconds with the trust beat. *(timer in the header)*
- [x] Reset under five seconds. *(`R` resets all local state for the case)*
- [x] Two volunteers complete the lens-and-depth interaction unassisted. *(test sheet)*
- [x] Runs with the network cable unplugged. *(static pack + service worker)*
- [x] Seven of ten viewers can repeat the closing line. *(test sheet)*

Run the test sheet three times: normal room, hostile Q&A, no network. The hostile questions and
answers are in `docs/stage-acceptance.md`.

## Stage mode rules

- Fixed seed. Every run is identical.
- No model calls, no API calls, no fonts, tiles or analytics from the network.
- `R` resets the case in under five seconds.
- The presenter can always fall back to **Auto-scan** (collects the three findings in 4.5 s) without
  breaking the story.
