# RootCause walkthrough video

A 1:40 narrated walkthrough of the **pump housing porosity** example, built from real app states.

## Deliverables

| File | What it is |
|---|---|
| `rootcause-walkthrough-burned.mp4` | Voiceover + burned-in subtitles (1:39) |
| `rootcause-walkthrough.mp4` | Voiceover, no subtitles |
| `rootcause-walkthrough-silent.mp4` | Same visuals, no audio (for your own voice) |
| `rootcause-captions.srt` | Sentence-level captions |
| `thumbnail.png` | Poster frame (case analysis) |
| `SCRIPT.md` | Timed script |
| `timing.json` | Scene starts and durations |
| `build_slides.py` | Reproducible build |
| `make_audio.py` | Edge TTS narration and per-scene SRT |

The public copies are in `web/public/demo/`.

## What the video shows

1. **My workspace, blank** — your own cases, no synthetic records.
2. **Create a real case** — the pump-housing defect, line 4, batch B-7781, initial guess: ejector-pin over-travel.
3. **Attach the evidence** — the loupe image, the sensor window and the batch record.
4. **The app reads the data** — cavity vacuum +56.7% (sustained), hydrogen 1.9 ppm vs a 1.4 limit. It ranks gas porosity at 86% and the initial guess at 2%.
5. **The disagreement** — the crack starts below the surface; the app shows the evidence and what would prove it wrong.
6. **Accept and sign** — the engineer accepts, signs, and the app names the prevention checks.
7. **The signed report** — evidence, signals and files.
8. **Two workspaces** — my cases vs the synthetic reference workspace.
9. **Close** — evidence first, the engineer decides.

## How it is built

The app is driven with Playwright and captured as 1600×900 states (not a real-time screen
recording — the machine is too slow for a clean capture, and the result is deterministic). Edge TTS
(`en-US-AndrewNeural`) generates the narration. ffmpeg assembles the scenes with the voice track and
burns the subtitles.

```powershell
# TTS (needs network; uses uvx edge-tts)
python demo/rootcause/make_audio.py

# capture + assemble (preview server on :4187)
python demo/rootcause/build_slides.py
```

The build copies `rootcause-walkthrough.mp4`, `rootcause-walkthrough-silent.mp4`,
`rootcause-walkthrough.srt` and `rootcause-walkthrough.jpg` into `web/public/demo/`.

## Guardrails

- One case, one trust beat: the app challenges the engineer's first guess.
- Do not claim a live plant, NPU, ONNX model or customer data.
- The analysis is deterministic CSV/batch signal extraction, not a trained model.
- The reference workspace remains clearly labelled synthetic.
