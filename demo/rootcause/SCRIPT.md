# RootCause — end-to-end walkthrough

**Example:** pump housing porosity (`web/public/examples/pump-housing`)  
**Runtime:** 1:39  
**Built from:** real app states captured with Playwright, narration by Edge TTS, subtitles burned in.

| Time | On screen | Voiceover |
|---|---|---|
| **0:01–0:13** | My workspace, blank | This is RootCause. It is not a case log. It reads the evidence you attach, challenges your first guess, and names what to fix next. It opens blank, on your own cases, in this browser. |
| **0:13–0:27** | Create a real case | Start with what happened: a porosity cluster at the bearing boss of a die-cast pump housing. Line four, batch B-7781. Your first guess is ejector-pin over-travel. |
| **0:27–0:36** | Attach the evidence | Attach what you already have: the loupe image, the sensor window, and the batch record. The app reads the numbers, not just the text. |
| **0:36–0:51** | The app reads the data | Cavity vacuum rose fifty-seven percent across the shift. Hydrogen is 1.9 ppm against a 1.4 limit. RootCause ranks gas porosity at eighty-six percent, and puts your ejector-pin guess below it. |
| **0:51–1:02** | The disagreement | That is the disagreement. The crack starts below the surface; the ejector marks are on the opposite face. The app shows why the first guess is weak and what would prove it wrong. |
| **1:02–1:16** | Accept and sign | Accept the evidence-backed cause, then sign the report. The ranking, the reason and the sign-off are recorded. The app also names the prevention checks: die venting, the door seal, and the rest of the batch. |
| **1:16–1:24** | The signed report | The signed report carries the evidence, the signals and the files. This is the deliverable the quality system keeps. |
| **1:24–1:34** | Switch workspaces | Admin switches between your workspace and the synthetic reference workspace. Both are clearly labelled. Your case is still here when you come back. |
| **1:34–1:39** | Close | Evidence first. The engineer decides. That's RootCause. |

## Guardrails

- One case, one trust beat.
- Do not claim a live plant, NPU or customer data.
