"""Fine-tune a defect detector on customer images and export it for on-site inference.

This is the pilot path, not part of the public demo. It expects a YOLO-format dataset:

    dataset/
      images/train/*.jpg
      images/val/*.jpg
      labels/train/*.txt
      labels/val/*.txt
      data.yaml

Usage (on the training box, never on the factory floor):

    python -m rootcause.training.finetune --data dataset/data.yaml --epochs 120
    python -m rootcause.training.finetune --data dataset/data.yaml --export om

The export step prints the exact commands for Ascend ATC. RootCause's NPU broker loads the .om
model; the CPU detector remains the fallback.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def validate_dataset(root: Path) -> dict[str, object]:
    images = list((root / "images").rglob("*.jpg")) + list((root / "images").rglob("*.png"))
    labels = list((root / "labels").rglob("*.txt"))
    if not images:
        raise SystemExit(f"No images found under {root / 'images'}")
    missing = []
    for img in images:
        split = img.parent.name
        label = root / "labels" / split / f"{img.stem}.txt"
        if not label.exists():
            missing.append(str(label))
    if missing:
        raise SystemExit(f"{len(missing)} image(s) have no label. First: {missing[0]}")
    data_yaml = root / "data.yaml"
    if not data_yaml.exists():
        (root / "data.yaml").write_text(
            "path: .\ntrain: images/train\nval: images/val\nnames:\n  0: defect\n", encoding="utf-8"
        )
    return {"images": len(images), "labels": len(labels), "data": str(data_yaml), "classes": ["defect"]}


def train(data: Path, epochs: int, imgsz: int, model: str) -> Path:
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:  # pragma: no cover - optional training extra
        raise SystemExit("ultralytics is not installed. pip install -e '.[train]'") from exc
    yolo = YOLO(model)
    result = yolo.train(data=str(data), epochs=epochs, imgsz=imgsz, project="runtime/training", name="defect")
    save_dir = Path(getattr(result, "save_dir", "runtime/training/defect"))
    print(json.dumps({"save_dir": str(save_dir), "weights": str(save_dir / "weights" / "best.pt")}, indent=2))
    return save_dir


def export_onnx(weights: Path, imgsz: int = 640) -> Path:
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit("ultralytics is not installed") from exc
    yolo = YOLO(str(weights))
    path = yolo.export(format="onnx", imgsz=imgsz, simplify=True, opset=12, dynamic=False)
    print(path)
    return Path(path)


def print_ascend_instructions(onnx: Path, output: Path) -> None:
    print(
        "\n".join(
            [
                "Ascend ATC export (run on the NPU server):",
                f"  atc --model={onnx} --framework=5 --output={output.with_suffix('')} \\",
                "      --input_format=NCHW --input_shape='input:1,3,640,640' \\",
                "      --soc_version=Ascend310P3 --precision_mode=allow_fp32_to_fp16",
                "",
                "Then set on the RootCause host:",
                "  ROOTCAUSE_NPU=ascend",
                "  ROOTCAUSE_NPU_ENDPOINT=http://127.0.0.1:7788",
                "  ROOTCAUSE_NPU_MODEL=/models/defect.om",
                "",
                "Validate on 200 held-out images before switching the line over. Keep the CPU detector",
                "as the fallback and log which backend produced every detection.",
            ]
        )
    )


def evaluate(weights: Path, data: Path, imgsz: int = 640) -> None:
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit("ultralytics is not installed") from exc
    metrics = YOLO(str(weights)).val(data=str(data), imgsz=imgsz)
    print(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="RootCause defect detector fine-tuning")
    parser.add_argument("--data", type=Path, required=True, help="dataset root or data.yaml")
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--export", choices=["onnx", "om", "none"], default="none")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--weights", type=Path)
    args = parser.parse_args()

    root = args.data.parent if args.data.name == "data.yaml" else args.data
    info = validate_dataset(root)
    print(json.dumps(info, indent=2))

    weights = args.weights
    if not weights:
        save_dir = train(args.data if args.data.name == "data.yaml" else root / "data.yaml", args.epochs, args.imgsz, args.model)
        weights = save_dir / "weights" / "best.pt"
    if args.eval:
        evaluate(weights, args.data, args.imgsz)
    if args.export != "none":
        onnx = export_onnx(weights, args.imgsz)
        if args.export == "om":
            print_ascend_instructions(onnx, Path("runtime/models/defect.om"))
        else:
            target = Path("runtime/models")
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(onnx, target / "defect.onnx")
            print(f"copied to {target / 'defect.onnx'}")


if __name__ == "__main__":
    main()
