"""Build the RootCause walkthrough from real app states.

The app is driven with Playwright and captured as high-resolution states; the narration and
subtitles come from Edge TTS. ffmpeg assembles the scenes with a slow zoom, the voice track and
burned captions. The result is deterministic and does not depend on real-time screen capture.

Run from the repository root, with the preview server on :4187:

    python demo/rootcause/build_slides.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio"
SHOTS = ROOT / "shots"
CLIPS = ROOT / "clips"
PUBLIC = ROOT.parents[1] / "web" / "public" / "demo"

FFMPEG = Path(r"C:\Workspace\openjiuwendemos\coachme\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
BASE = "http://127.0.0.1:4187/"
EXAMPLES = ROOT.parents[1] / "web" / "public" / "examples" / "pump-housing"

LEAD = 1.0
GAP = 1.6
FPS = 25
W, H = 1600, 900

SCENES = [
    ("01_intro", "My workspace, blank", "01_home.png"),
    ("02_case", "Create a real case", "02_form.png"),
    ("03_evidence", "Attach the evidence", "03_form_files.png"),
    ("04_analysis", "The app reads the data", "04_case.png"),
    ("05_review", "The disagreement", "05_review.png"),
    ("06_sign", "Accept and sign", "06_accept.png"),
    ("07_report", "The signed report", "07_report.png"),
    ("08_settings", "Switch workspaces", "08_admin.png"),
    ("09_close", "Close", "09_end.png"),
]

CALLOUTS = {
    "01_home.png": [],
    "02_form.png": [],
    "03_form_files.png": [],
    "04_case.png": [],
    "05_review.png": [],
    "06_accept.png": [],
    "07_report.png": [],
    "08_admin.png": [],
    "09_end.png": [],
}


def ffmpeg(*args: str, cwd: Path | None = None) -> None:
    cmd = [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{' '.join(cmd)}\n{proc.stderr[-2500:]}")


def audio_duration(path: Path) -> float:
    proc = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", proc.stderr)
    if not match:
        raise RuntimeError(f"could not read duration: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def wav_frames(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path), "rb") as handle:
        if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            raise RuntimeError(f"unexpected WAV format: {path}")
        return handle.readframes(handle.getnframes()), handle.getframerate()


def build_voice() -> tuple[list[dict], Path]:
    scene_info: list[dict] = []
    for name, label, image in SCENES:
        mp3 = AUDIO / f"{name}.mp3"
        wav = AUDIO / f"{name}.wav"
        if not mp3.exists():
            raise FileNotFoundError(f"missing narration: {mp3} (run make_audio.py)")
        ffmpeg("-i", str(mp3), "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav))
        length = audio_duration(wav)
        scene_info.append(
            {"name": name, "label": label, "image": image, "audio": round(length, 3), "duration": round(length + GAP, 3)}
        )

    rate = 24000
    silence = lambda seconds: b"\x00\x00" * int(seconds * rate)
    chunks = [silence(LEAD)]
    for info in scene_info:
        frames, sample_rate = wav_frames(AUDIO / f"{info['name']}.wav")
        if sample_rate != rate:
            raise RuntimeError(f"unexpected sample rate {sample_rate}")
        chunks.append(frames)
        chunks.append(silence(GAP))

    clock = LEAD
    for info in scene_info:
        info["start"] = round(clock, 3)
        info["end"] = round(clock + info["duration"], 3)
        clock += info["duration"]
    total = round(clock, 3)

    voice = ROOT / "voice.wav"
    with wave.open(str(voice), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"".join(chunks))
    return scene_info, voice


def rect(page: Page, locator) -> list[float]:
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    box = locator.bounding_box()
    if not box:
        raise RuntimeError("no bounding box")
    return [round(box["x"], 1), round(box["y"], 1), round(box["width"], 1), round(box["height"], 1)]


def capture() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    CALLOUTS.clear()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(CHROME), headless=True)
        context = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        page = context.new_page()
        page.set_default_timeout(15000)
        page.goto(BASE, wait_until="networkidle")
        page.evaluate("localStorage.removeItem('rootcause.demo.v1')")
        page.evaluate(
            "localStorage.setItem('rootcause.ui.v1', JSON.stringify({theme:'light',density:'comfortable',role:'quality_manager',showDataSource:true}))"
        )
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(800)

        page.screenshot(path=str(SHOTS / "01_home.png"))
        CALLOUTS["01_home.png"] = [rect(page, page.get_by_role("link", name="Create my first case"))]

        page.get_by_role("link", name="Create my first case").click()
        page.wait_for_selector("#nc-defect")
        page.fill("#nc-defect", "Porosity cluster at the bearing boss")
        page.fill("#nc-part", "Pump housing, die-cast AlSi9Cu3")
        page.fill("#nc-batch", "B-7781")
        page.select_option("#nc-line", "line-4")
        page.select_option("#nc-severity", "high")
        page.select_option("#nc-shift", "B")
        page.fill("#nc-station", "End-of-line inspection")
        page.fill("#nc-cause", "Ejector pin over-travel")
        page.fill(
            "#nc-desc",
            "Hairline crack at the bearing boss on the clamp side. The crack starts about 0.4 mm below "
            "the surface and does not follow the ejector-pin witness marks. Vacuum drifted from 118 to "
            "221 mbar across the shift. The batch was accepted on a 1.9 ppm hydrogen deviation.",
        )
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_timeout(400)
        page.screenshot(path=str(SHOTS / "02_form.png"))
        CALLOUTS["02_form.png"] = [rect(page, page.locator("#nc-defect"))]

        page.set_input_files(
            "#nc-files",
            [
                str(EXAMPLES / "casting-ct.jpg"),
                str(EXAMPLES / "sensor-window.csv"),
                str(EXAMPLES / "batch-record.csv"),
            ],
        )
        page.wait_for_timeout(600)
        create = page.get_by_role("button", name="Create case")
        create.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "03_form_files.png"))
        CALLOUTS["03_form_files.png"] = [rect(page, create)]

        create.click()
        page.wait_for_url("**/#/cases/**")
        page.wait_for_selector("h1")
        page.wait_for_timeout(900)
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.screenshot(path=str(SHOTS / "04_case.png"))
        CALLOUTS["04_case.png"] = [rect(page, page.locator(".analysis-strip"))]

        page.get_by_role("link", name="Decide").click()
        page.wait_for_selector(".review-decision")
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "05_review.png"))
        CALLOUTS["05_review.png"] = [rect(page, page.locator(".cause.lead"))]

        page.locator(".review-decision button", has_text="Accept top cause").click()
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "06_accept.png"))
        CALLOUTS["06_accept.png"] = [rect(page, page.locator(".review-decision button", has_text="Approve report"))]

        page.locator(".review-decision button", has_text="Approve report").click()
        page.wait_for_timeout(700)
        page.get_by_role("link", name="Edit the report first").click()
        page.wait_for_selector(".report-preview")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOTS / "07_report.png"))
        CALLOUTS["07_report.png"] = []

        page.goto(BASE + "#/admin", wait_until="domcontentloaded")
        page.wait_for_timeout(900)
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "08_admin.png"))
        CALLOUTS["08_admin.png"] = [rect(page, page.get_by_role("button", name=re.compile(r"Reference data")))]

        page.set_content(
            """<!doctype html><html><head><meta charset="utf-8"></head>
            <body style="margin:0;height:100vh;display:grid;place-items:center;background:#f4f1ea;color:#22211d;font-family:Inter,system-ui,sans-serif">
              <div style="text-align:center;max-width:780px;padding:0 24px">
                <div style="font:700 11px ui-monospace,monospace;letter-spacing:.22em;text-transform:uppercase;color:#a86418">RootCause</div>
                <h1 style="margin:14px 0 12px;font-size:46px;letter-spacing:-.03em">Evidence first.<br>Engineer signs.</h1>
                <p style="margin:0;color:#5d574b;font-size:18px;line-height:1.6">Your cases live in this browser.<br>The synthetic reference workspace is one switch away.</p>
              </div>
            </body></html>"""
        )
        page.wait_for_timeout(400)
        page.screenshot(path=str(SHOTS / "09_end.png"))
        CALLOUTS["09_end.png"] = []

        context.close()
        browser.close()
    (ROOT / "callouts.json").write_text(json.dumps(CALLOUTS, indent=2), encoding="utf-8")


def decorate(name: str) -> None:
    path = SHOTS / name
    image = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    for x, y, w, h in CALLOUTS.get(name, []):
        pad = 6
        draw.rounded_rectangle(
            [x - pad, y - pad, x + w + pad, y + h + pad],
            radius=10, outline=(242, 180, 92, 255), width=4,
        )
        draw.rounded_rectangle(
            [x - pad - 2, y - pad - 2, x + w + pad + 2, y + h + pad + 2],
            radius=12, outline=(20, 18, 14, 90), width=1,
        )
        cx, cy = x + w / 2, y + h / 2
        arrow = [
            (cx, cy), (cx, cy + 20), (cx + 6, cy + 15), (cx + 11, cy + 25),
            (cx + 16, cy + 22), (cx + 11, cy + 13), (cx + 19, cy + 13),
        ]
        draw.polygon(arrow, fill=(255, 255, 255, 255), outline=(20, 18, 14, 255))
        draw.line(arrow + [arrow[0]], fill=(20, 18, 14, 255), width=2)
    image.save(path)


def make_clips(scene_info: list[dict]) -> Path:
    CLIPS.mkdir(parents=True, exist_ok=True)
    for old in CLIPS.glob("*.mp4"):
        old.unlink()
    concat_lines: list[str] = []
    for i, info in enumerate(scene_info):
        source = SHOTS / info["image"]
        clip = CLIPS / f"{i:02}_{info['name']}.mp4"
        ffmpeg(
            "-loop", "1", "-i", str(source), "-t", f"{info['duration']:.3f}",
            "-vf", "format=yuv420p", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            str(clip),
        )
        concat_lines.append(f"file '{clip.as_posix()}'")
    concat = CLIPS / "concat.txt"
    concat.write_text("\n".join(concat_lines), encoding="utf-8")
    joined = CLIPS / "joined.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(joined))
    return joined


def encode(scene_info: list[dict], joined: Path, voice: Path) -> tuple[Path, Path, Path, Path]:
    total = scene_info[-1]["end"]
    tts = ROOT / "rootcause-walkthrough.mp4"
    silent = ROOT / "rootcause-walkthrough-silent.mp4"
    burned = ROOT / "rootcause-walkthrough-burned.mp4"
    poster = ROOT / "thumbnail.png"

    ffmpeg(
        "-i", str(joined), "-i", str(voice), "-t", f"{total:.3f}",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(tts),
    )
    ffmpeg("-i", str(joined), "-t", f"{total:.3f}", "-c", "copy", "-movflags", "+faststart", str(silent))
    ffmpeg(
        "-i", str(tts), "-vf",
        "subtitles=rootcause-captions.srt:force_style='FontName=Arial,FontSize=9,Outline=1.2,Shadow=0.5,MarginV=16'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", str(burned), cwd=ROOT,
    )
    shutil.copyfile(SHOTS / "04_case.png", poster)
    return tts, silent, burned, poster


def _parse_srt(path: Path) -> list[tuple[float, float, str]]:
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    out: list[tuple[float, float, str]] = []
    for block in re.split(r"\n\s*\n", raw):
        lines = block.split("\n")
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->")]

        def seconds(value: str) -> float:
            hours, minutes, rest = value.split(":")
            secs, millis = rest.split(",")
            return int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000

        out.append((seconds(start), seconds(end), "\n".join(lines[2:]).strip()))
    return out


def write_captions(scene_info: list[dict]) -> Path:
    def stamp(value: float) -> str:
        millis_total = int(round(value * 1000))
        hours, millis_total = divmod(millis_total, 3600000)
        minutes, millis_total = divmod(millis_total, 60000)
        secs, millis = divmod(millis_total, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    lines: list[str] = []
    index = 1
    for info in scene_info:
        offset = info["start"]
        for start, end, text in _parse_srt(AUDIO / f"{info['name']}.srt"):
            lines += [str(index), f"{stamp(offset + start)} --> {stamp(offset + end)}", text, ""]
            index += 1
    target = ROOT / "rootcause-captions.srt"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def write_script(scene_info: list[dict]) -> Path:
    lines = [
        "# RootCause — end-to-end walkthrough",
        "",
        "**Example:** pump housing porosity (`web/public/examples/pump-housing`)  ",
        f"**Runtime:** {int(scene_info[-1]['end'] // 60)}:{int(scene_info[-1]['end'] % 60):02}  ",
        "**Built from:** real app states captured with Playwright, narration by Edge TTS, subtitles burned in.",
        "",
        "| Time | On screen | Voiceover |",
        "|---|---|---|",
    ]
    for info in scene_info:
        text = (AUDIO / f"{info['name']}.txt").read_text(encoding="utf-8").strip()
        lines.append(f"| **{int(info['start']//60)}:{int(info['start']%60):02}–{int(info['end']//60)}:{int(info['end']%60):02}** | {info['label']} | {text} |")
    lines += ["", "## Guardrails", "", "- One case, one trust beat.", "- Do not claim a live plant, NPU or customer data.", ""]
    target = ROOT / "SCRIPT.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def main() -> None:
    if not FFMPEG.exists():
        raise SystemExit(f"ffmpeg not found: {FFMPEG}")
    capture()
    for name in CALLOUTS:
        decorate(name)
    scene_info, voice = build_voice()
    captions = write_captions(scene_info)
    joined = make_clips(scene_info)
    tts, silent, burned, poster = encode(scene_info, joined, voice)
    script = write_script(scene_info)

    PUBLIC.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(burned, PUBLIC / "rootcause-walkthrough.mp4")
    shutil.copyfile(silent, PUBLIC / "rootcause-walkthrough-silent.mp4")
    shutil.copyfile(captions, PUBLIC / "rootcause-walkthrough.srt")
    shutil.copyfile(poster, PUBLIC / "rootcause-walkthrough.jpg")

    for path in (burned, silent, captions, poster):
        print(f"{path.name}: {path.stat().st_size / 1_000_000:.2f} MB")
    print(f"runtime: {scene_info[-1]['end']:.1f}s")
    print(f"published: {PUBLIC}")


if __name__ == "__main__":
    main()
