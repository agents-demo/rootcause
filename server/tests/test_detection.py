from __future__ import annotations

from pathlib import Path

from rootcause.engine.detection import bundle_demo_images, detect, generate_part_image, generate_xray


def test_generated_image_has_a_detectable_defect(tmp_path: Path):
    img = generate_part_image("bracket", tmp_path / "bracket.png")
    det = detect(img, label="fracture")
    assert 0.5 <= det.confidence <= 0.99
    assert det.area_px > 20
    x, y, w, h = det.bbox
    assert 0 < x < 1 and 0 < y < 1 and 0 < w <= 1 and 0 < h <= 1


def test_xray_generates(tmp_path: Path):
    img = generate_xray(tmp_path / "xray.png")
    assert img.exists() and img.stat().st_size > 1000


def test_detection_is_deterministic(tmp_path: Path):
    img = generate_part_image("weld", tmp_path / "weld.png", seed=9)
    a = detect(img)
    b = detect(img)
    assert a.bbox == b.bbox
    assert a.confidence == b.confidence


def test_bundle(tmp_path: Path):
    paths = bundle_demo_images(tmp_path / "images")
    assert len(paths) == 5
    assert all(Path(p).exists() for p in paths)
