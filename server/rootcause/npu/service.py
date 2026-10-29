"""On-site NPU broker service.

The RootCause host only knows the broker URL. The broker reports exactly which backend produced a
detection. It never silently uses the CPU when the configured NPU/ONNX path is unavailable.

    # ONNX Runtime (production path without Ascend)
    ROOTCAUSE_NPU_BACKEND=onnx ROOTCAUSE_NPU_MODEL=/models/defect.onnx uvicorn rootcause.npu.service:app --port 7788

    # Ascend OM model (site package)
    ROOTCAUSE_NPU_BACKEND=ascend ROOTCAUSE_NPU_MODEL=/models/defect.om uvicorn rootcause.npu.service:app --port 7788

    # Laptop-only synthetic detector, explicitly labelled
    ROOTCAUSE_NPU_SIMULATE=1 uvicorn rootcause.npu.service:app --port 7788
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from ..engine.detection import detect
from .onnx_backend import OnnxBroker

app = FastAPI(title="RootCause NPU broker", version="1.0.0")


class InferRequest(BaseModel):
    image: str
    model: str = ""


def _simulate() -> bool:
    return os.getenv("ROOTCAUSE_NPU_SIMULATE", "").lower() in {"1", "true", "yes"}


def _backend() -> str:
    if _simulate():
        return "simulated"
    return os.getenv("ROOTCAUSE_NPU_BACKEND", "onnx").lower()


def _ascend_ready() -> bool:
    try:
        import acl  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def _onnx_broker() -> OnnxBroker:
    return OnnxBroker(
        os.getenv("ROOTCAUSE_NPU_MODEL", "models/defect.onnx"),
        imgsz=int(os.getenv("ROOTCAUSE_NPU_IMGSZ", "640")),
        conf=float(os.getenv("ROOTCAUSE_NPU_CONF", "0.25")),
    )


def _check_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("ROOTCAUSE_NPU_TOKEN", "")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(401, "invalid NPU broker token")


@app.get("/health")
def health() -> dict[str, Any]:
    backend = _backend()
    if backend == "simulated":
        return {"backend": "simulated", "device": "CPU (explicit demo)", "ready": True, "model": "synthetic"}
    if backend == "onnx":
        return _onnx_broker().health()
    if backend == "ascend":
        return {
            "backend": "ascend",
            "device": "Ascend 310P",
            "ready": _ascend_ready(),
            "model": os.getenv("ROOTCAUSE_NPU_MODEL", "defect.om"),
            "detail": "acl runtime present" if _ascend_ready() else "acl runtime not installed",
        }
    return {"backend": backend, "ready": False, "detail": "unknown backend"}


@app.post("/infer")
def infer(req: InferRequest, _: None = Depends(_check_token)) -> dict[str, Any]:
    image = Path(req.image)
    if not image.exists():
        raise HTTPException(404, f"image not found: {image}")
    backend = _backend()
    if backend == "simulated":
        det = detect(image)
        return {
            "request_id": f"inf-{uuid.uuid4().hex[:10]}",
            "model": "rootcause-detector-0.9",
            "label": det.label,
            "bbox": det.bbox,
            "confidence": det.confidence,
            "device": "CPU (explicit demo)",
            "backend": "simulated",
        }
    if backend == "onnx":
        try:
            return _onnx_broker().infer(image).as_dict()
        except FileNotFoundError as exc:
            raise HTTPException(503, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(500, f"ONNX inference failed: {exc}") from exc
    if backend == "ascend":
        if not _ascend_ready():
            raise HTTPException(503, "Ascend runtime not available; refusing to pretend the NPU ran")
        raise HTTPException(501, "Ascend ACL executor is site-specific; install the customer OM runtime")
    raise HTTPException(503, f"unknown NPU backend: {backend}")
