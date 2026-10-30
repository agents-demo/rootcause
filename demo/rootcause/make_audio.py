"""Generate the English voiceover and per-scene subtitles for the RootCause walkthrough.

Run from the repository root (needs network for Edge TTS):

    python demo/rootcause/make_audio.py

Uses `uvx edge-tts`, the same tool as the CoachMe demo.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
FFMPEG = Path(r"C:\Workspace\openjiuwendemos\coachme\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
VOICE = "en-US-AndrewNeural"
RATE = "+6%"

SCENES = {
    "01_intro": "This is RootCause. It is not a case log. It reads the evidence you attach, challenges your first guess, and names what to fix next. It opens blank, on your own cases, in this browser.",
    "02_case": "Start with what happened: a porosity cluster at the bearing boss of a die-cast pump housing. Line four, batch B-7781. Your first guess is ejector-pin over-travel.",
    "03_evidence": "Attach what you already have: the loupe image, the sensor window, and the batch record. The app reads the numbers, not just the text.",
    "04_analysis": "Cavity vacuum rose fifty-seven percent across the shift. Hydrogen is 1.9 ppm against a 1.4 limit. RootCause ranks gas porosity at eighty-six percent, and puts your ejector-pin guess below it.",
    "05_review": "That is the disagreement. The crack starts below the surface; the ejector marks are on the opposite face. The app shows why the first guess is weak and what would prove it wrong.",
    "06_sign": "Accept the evidence-backed cause, then sign the report. The ranking, the reason and the sign-off are recorded. The app also names the prevention checks: die venting, the door seal, and the rest of the batch.",
    "07_report": "The signed report carries the evidence, the signals and the files. This is the deliverable the quality system keeps.",
    "08_settings": "Admin switches between your workspace and the synthetic reference workspace. Both are clearly labelled. Your case is still here when you come back.",
    "09_close": "Evidence first. The engineer decides. That's RootCause.",
}


def duration(path: Path) -> float:
    proc = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", proc.stderr)
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for name, text in SCENES.items():
        txt = AUDIO / f"{name}.txt"
        mp3 = AUDIO / f"{name}.mp3"
        srt = AUDIO / f"{name}.srt"
        txt.write_text(text, encoding="utf-8")
        cmd = [
            "uvx", "edge-tts", "--voice", VOICE, "--rate", RATE,
            "--file", str(txt), "--write-media", str(mp3), "--write-subtitles", str(srt),
            "--no-progress",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f"edge-tts failed for {name}:\n{result.stderr[-800:]}")
        length = duration(mp3)
        total += length
        print(f"{name}: {length:.2f}s")
    print(f"TOTAL: {total:.2f}s")


if __name__ == "__main__":
    main()
