"""NPU broker for on-site image inference.

The broker keeps the inference contract stable across hardware: a request names an image and a
model, the broker returns detections and timing. ``AscendBroker`` is the optional production path
for Ascend hardware; the demo uses ``LocalBroker`` on the CPU and labels itself accordingly.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..engine.detection import detect


@dataclass
class InferenceResult:
    request_id: str
    model: str
    label: str
    bbox: list[float]
    confidence: float
    latency_ms: float
    device: str
    backend: str
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "label": self.label,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "device": self.device,
            "backend": self.backend,
            **self.meta,
        }


class LocalBroker:
    name = "local-cpu"
    device = "CPU"

    def __init__(self, model: str = "rootcause-detector-0.9") -> None:
        self.model = model

    def health(self) -> dict[str, Any]:
        return {"backend": self.name, "device": self.device, "model": self.model, "ready": True}

    def infer(self, image_path: str | Path, label: str = "defect") -> InferenceResult:
        started = time.perf_counter()
        det = detect(image_path, label=label)
        elapsed = (time.perf_counter() - started) * 1000
        return InferenceResult(
            request_id=f"inf-{uuid.uuid4().hex[:10]}",
            model=self.model,
            label=det.label,
            bbox=det.bbox,
            confidence=det.confidence,
            latency_ms=round(elapsed, 1),
            device=self.device,
            backend=self.name,
            meta={"area_px": det.area_px, "threshold": round(det.threshold, 1)},
        )


class AscendBroker:
    """Optional Ascend NPU path.

    When a site has the Ascend runtime and a compiled OM model, this broker forwards the image to
    the on-site ``npu-broker`` service. Without those pieces it refuses loudly instead of silently
    falling back to CPU, so an operator always knows which silicon produced a detection.
    """

    name = "ascend"
    device = "Ascend 310P"

    def __init__(self, endpoint: str = "http://127.0.0.1:7788", model: str = "yolov8n-defect.om") -> None:
        self.endpoint = endpoint
        self.model = model

    def health(self) -> dict[str, Any]:
        try:
            import urllib.request

            with urllib.request.urlopen(self.endpoint.rstrip("/") + "/health", timeout=2) as resp:
                return {"backend": self.name, "device": self.device, "model": self.model, "ready": resp.status == 200}
        except Exception as exc:
            return {"backend": self.name, "device": self.device, "model": self.model, "ready": False, "error": str(exc)}

    def infer(self, image_path: str | Path, label: str = "defect") -> InferenceResult:
        import json
        import urllib.request

        body = json.dumps({"image": str(image_path), "model": self.model}).encode()
        req = urllib.request.Request(
            self.endpoint.rstrip("/") + "/infer",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        elapsed = (time.perf_counter() - started) * 1000
        return InferenceResult(
            request_id=data.get("request_id", f"inf-{uuid.uuid4().hex[:10]}"),
            model=data.get("model", self.model),
            label=data.get("label", label),
            bbox=data.get("bbox", [0, 0, 0, 0]),
            confidence=float(data.get("confidence", 0)),
            latency_ms=round(elapsed, 1),
            device=self.device,
            backend=self.name,
        )


def broker_from_env():
    import os

    backend = os.getenv("ROOTCAUSE_NPU_BACKEND", "").lower()
    if backend == "onnx":
        from .onnx_backend import OnnxBroker

        return OnnxBroker(os.getenv("ROOTCAUSE_NPU_MODEL", "models/defect.onnx"), imgsz=int(os.getenv("ROOTCAUSE_NPU_IMGSZ", "640")))
    if os.getenv("ROOTCAUSE_NPU", "").lower() in {"1", "true", "ascend"}:
        return AscendBroker(os.getenv("ROOTCAUSE_NPU_ENDPOINT", "http://127.0.0.1:7788"))
    return LocalBroker()
