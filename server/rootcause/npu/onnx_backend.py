"""Real ONNX inference backend for defect detection.

This is the production path when no Ascend runtime is present. It expects a YOLO-style ONNX model
exported from the customer fine-tune (see `training/finetune.py`) and performs the same letterbox +
NMS contract as the NPU broker. It never silently falls back to the synthetic CPU detector; a
missing model is an explicit error.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ..engine.detection import Detection
from .broker import InferenceResult


def letterbox(image: Image.Image, size: int = 640) -> tuple[np.ndarray, float, int, int]:
    width, height = image.size
    scale = min(size / width, size / height)
    new_w, new_h = int(round(width * scale)), int(round(height * scale))
    resized = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (size, size), (114, 114, 114))
    pad_x, pad_y = (size - new_w) // 2, (size - new_h) // 2
    canvas.paste(resized, (pad_x, pad_y))
    array = np.asarray(canvas, dtype=np.float32) / 255.0
    array = np.transpose(array, (2, 0, 1))[None, ...]
    return array, scale, pad_x, pad_y


def nms(boxes: list[list[float]], scores: list[float], iou_threshold: float = 0.45) -> list[int]:
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    keep: list[int] = []
    while order:
        i = order.pop(0)
        keep.append(i)
        xi1, yi1, xi2, yi2 = boxes[i]
        remaining = []
        for j in order:
            xj1, yj1, xj2, yj2 = boxes[j]
            inter = max(0.0, min(xi2, xj2) - max(xi1, xj1)) * max(0.0, min(yi2, yj2) - max(yi1, yj1))
            area_i = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
            area_j = max(0.0, xj2 - xj1) * max(0.0, yj2 - yj1)
            union = area_i + area_j - inter
            if union <= 0 or inter / union <= iou_threshold:
                remaining.append(j)
        order = remaining
    return keep


class OnnxBroker:
    name = "onnx"
    device = "CPU (ONNX Runtime)"

    def __init__(self, model_path: str | Path, *, imgsz: int = 640, conf: float = 0.25) -> None:
        self.model_path = Path(model_path)
        self.imgsz = imgsz
        self.conf = conf
        self._session = None

    def _load(self):
        if self._session is None:
            import onnxruntime as ort

            if not self.model_path.exists():
                raise FileNotFoundError(f"ONNX model not found: {self.model_path}")
            providers = ["CPUExecutionProvider"]
            if "CUDAExecutionProvider" in ort.get_available_providers():
                providers.insert(0, "CUDAExecutionProvider")
            self._session = ort.InferenceSession(str(self.model_path), providers=providers)
        return self._session

    def health(self) -> dict[str, Any]:
        try:
            session = self._load()
            return {
                "backend": self.name,
                "device": self.device,
                "model": str(self.model_path),
                "ready": True,
                "inputs": [i.name for i in session.get_inputs()],
                "providers": session.get_providers(),
            }
        except Exception as exc:
            return {"backend": self.name, "device": self.device, "model": str(self.model_path), "ready": False, "error": str(exc)}

    def infer(self, image_path: str | Path, label: str = "defect") -> InferenceResult:
        started = time.perf_counter()
        session = self._load()
        image = Image.open(image_path).convert("RGB")
        array, scale, pad_x, pad_y = letterbox(image, self.imgsz)
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: array})[0]
        pred = np.squeeze(output)
        if pred.ndim == 2 and pred.shape[0] < pred.shape[1]:
            pred = pred.T
        boxes: list[list[float]] = []
        scores: list[float] = []
        classes: list[int] = []
        for row in pred:
            if len(row) < 5:
                continue
            objectness = float(row[4])
            if len(row) >= 6:
                cls_scores = row[5:]
                cls = int(np.argmax(cls_scores))
                score = objectness * float(cls_scores[cls])
            else:
                cls = 0
                score = objectness
            if score < self.conf:
                continue
            cx, cy, w, h = [float(v) for v in row[:4]]
            x1 = (cx - w / 2 - pad_x) / scale
            y1 = (cy - h / 2 - pad_y) / scale
            x2 = (cx + w / 2 - pad_x) / scale
            y2 = (cy + h / 2 - pad_y) / scale
            width, height = image.size
            x1, y1 = max(0.0, x1), max(0.0, y1)
            x2, y2 = min(float(width), x2), min(float(height), y2)
            boxes.append([x1, y1, x2, y2])
            scores.append(score)
            classes.append(cls)
        keep = nms(boxes, scores) if boxes else []
        elapsed = (time.perf_counter() - started) * 1000
        if not keep:
            det = Detection(label=label, bbox=[0, 0, 0, 0], confidence=0.0, area_px=0, threshold=0.0)
            return InferenceResult(
                request_id=f"inf-{uuid.uuid4().hex[:10]}", model=self.model_path.name, label=label,
                bbox=det.bbox, confidence=0.0, latency_ms=round(elapsed, 1), device=self.device, backend=self.name,
            )
        best = keep[0]
        x1, y1, x2, y2 = boxes[best]
        width, height = image.size
        return InferenceResult(
            request_id=f"inf-{uuid.uuid4().hex[:10]}",
            model=self.model_path.name,
            label=f"class-{classes[best]}" if classes[best] else label,
            bbox=[round(x1 / width, 4), round(y1 / height, 4), round((x2 - x1) / width, 4), round((y2 - y1) / height, 4)],
            confidence=round(scores[best], 4),
            latency_ms=round(elapsed, 1),
            device=self.device,
            backend=self.name,
            meta={"detections": len(keep)},
        )
