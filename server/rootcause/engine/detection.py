"""On-site defect detection.

The public demo ships synthetic images. The detector is a real, deterministic image routine
(Otsu threshold + largest connected dark region), so the bounding box shown in the UI is computed
from pixels rather than hard-coded. A pilot swaps in a fine-tuned model behind the same interface.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

try:  # numpy is a hard runtime dependency for detection; the rest of the API degrades without it
    import numpy as np
except Exception:  # pragma: no cover - exercised only on minimal installs
    np = None  # type: ignore[assignment]


@dataclass
class Detection:
    label: str
    bbox: list[float]  # normalised x, y, w, h
    confidence: float
    area_px: int
    threshold: float

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "bbox": self.bbox,
            "confidence": round(self.confidence, 4),
            "area_px": self.area_px,
            "threshold": round(self.threshold, 2),
        }


def otsu_threshold(values: np.ndarray) -> float:
    hist, _ = np.histogram(values, bins=256, range=(0, 256))
    total = values.size
    sum_all = float(np.dot(np.arange(256), hist))
    sum_bg = 0.0
    weight_bg = 0.0
    best_var = -1.0
    best_t = 127.0
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_all - sum_bg) / weight_fg
        var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var > best_var:
            best_var = var
            best_t = float(t)
    return best_t


def _components(mask: np.ndarray) -> Iterable[tuple[int, int, int, int, int]]:
    """Yield (x0, y0, x1, y1, area) for 4-connected components, largest first."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps: list[tuple[int, int, int, int, int]] = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        minx = maxx = x0
        miny = maxy = y0
        area = 0
        while stack:
            y, x = stack.pop()
            area += 1
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if area >= 12:
            comps.append((minx, miny, maxx, maxy, area))
    comps.sort(key=lambda c: -c[4])
    return comps


def detect(image_path: str | Path, label: str = "defect") -> Detection:
    if np is None:
        raise RuntimeError("numpy is required for detection")
    img = Image.open(image_path).convert("L")
    img.thumbnail((720, 720))
    arr = np.asarray(img, dtype=np.float32)
    # Suppress the frame so a dark border does not win as the defect.
    h, w = arr.shape
    border = max(2, min(h, w) // 40)
    arr[:border, :] = np.median(arr)
    arr[-border:, :] = np.median(arr)
    arr[:, :border] = np.median(arr)
    arr[:, -border:] = np.median(arr)
    t = otsu_threshold(arr)
    mask = arr < (t * 0.82)
    comps = list(_components(mask))
    if not comps:
        return Detection(label=label, bbox=[0.0, 0.0, 0.0, 0.0], confidence=0.0, area_px=0, threshold=t)
    x0, y0, x1, y1, area = comps[0]
    bw = max(1, x1 - x0 + 1)
    bh = max(1, y1 - y0 + 1)
    fill = area / (bw * bh)
    contrast = max(0.0, (float(arr.mean()) - float(arr[y0 : y1 + 1, x0 : x1 + 1].mean())) / 255.0)
    confidence = max(0.5, min(0.99, 0.55 + contrast * 2.1 + min(0.18, area / (h * w) * 4)))
    if fill < 0.04:
        confidence *= 0.8
    return Detection(
        label=label,
        bbox=[round(x0 / w, 4), round(y0 / h, 4), round(bw / w, 4), round(bh / h, 4)],
        confidence=round(confidence, 4),
        area_px=area,
        threshold=t,
    )


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        f = y / max(1, h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return base


def generate_part_image(kind: str, out_path: str | Path, *, seed: int = 417) -> Path:
    """Generate a synthetic part image with a visible defect. Deterministic for a seed."""
    import random

    rng = random.Random(seed)
    w, h = 960, 600
    if kind == "bracket":
        img = _gradient((w, h), (78, 82, 88), (39, 42, 47))
    elif kind == "housing":
        img = _gradient((w, h), (106, 110, 118), (58, 61, 67))
    elif kind == "weld":
        img = _gradient((w, h), (92, 88, 82), (45, 43, 40))
    else:
        img = _gradient((w, h), (62, 86, 82), (24, 40, 38))
    draw = ImageDraw.Draw(img)
    # machining texture
    for _ in range(260):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        length = rng.randint(20, 140)
        shade = rng.randint(-18, 18)
        draw.line([(x, y), (x + length, y + rng.randint(-3, 3))], fill=(clamp(70 + shade), clamp(74 + shade), clamp(80 + shade)), width=1)
    # part outline
    draw.rounded_rectangle([70, 60, w - 70, h - 60], radius=36, outline=(120, 124, 132), width=3)
    draw.ellipse([210, 160, 400, 350], outline=(135, 140, 148), width=4)
    draw.ellipse([245, 195, 365, 315], outline=(70, 74, 80), width=3)
    for cx, cy in ((795, 145), (150, 470), (840, 470)):
        draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline=(120, 124, 132), width=2)
    # defect
    if kind == "bracket":
        pts = [(365, 210), (383, 240), (376, 278), (397, 310), (389, 344), (420, 372)]
        draw.line(pts, fill=(24, 22, 22), width=5)
        draw.line(pts, fill=(160, 148, 132), width=1)
        # tool mark
        draw.line([(250, 388), (332, 376)], fill=(178, 166, 146), width=3)
    elif kind == "housing":
        draw.polygon([(520, 270), (690, 270), (690, 360), (610, 390), (520, 360)], fill=(34, 36, 40))
        draw.line([(520, 270), (690, 270)], fill=(190, 194, 200), width=2)
    elif kind == "weld":
        draw.ellipse([420, 240, 560, 380], fill=(38, 36, 34))
        draw.line([(470, 280), (495, 330), (525, 350), (545, 330)], fill=(18, 18, 18), width=6)
    else:
        draw.ellipse([450, 270, 540, 350], fill=(30, 44, 42))
        for _ in range(7):
            cx = rng.randint(470, 520)
            cy = rng.randint(290, 330)
            r = rng.randint(3, 9)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 18, 17))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def clamp(v: int) -> int:
    return max(0, min(255, v))


def generate_xray(out_path: str | Path, *, seed: int = 417) -> Path:
    import random

    rng = random.Random(seed)
    w, h = 960, 600
    img = Image.new("RGB", (w, h), (6, 18, 20))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([70, 60, w - 70, h - 60], radius=36, outline=(60, 190, 180), width=2)
    draw.ellipse([210, 160, 400, 350], outline=(40, 130, 124), width=3)
    draw.line([(365, 210), (383, 240), (376, 278), (397, 310), (389, 344), (420, 372)], fill=(220, 255, 249), width=4)
    for _ in range(9):
        cx = rng.randint(555, 690)
        cy = rng.randint(300, 400)
        r = rng.randint(6, 34)
        for i in range(r, 0, -2):
            a = int(90 * (1 - i / r))
            draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(20 + a, 90 + a, 88 + a))
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def bundle_demo_images(out_dir: str | Path) -> list[str]:
    d = Path(out_dir)
    paths = [
        generate_part_image("bracket", d / "bracket.png"),
        generate_xray(d / "bracket-xray.png"),
        generate_part_image("housing", d / "housing.png"),
        generate_part_image("weld", d / "weld.png"),
        generate_part_image("solder", d / "solder.png"),
    ]
    return [str(p) for p in paths]


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))
