"""On-site NPU broker service.

Run this next to the NPU card. The RootCause host only knows the broker URL; it never talks to
the accelerator directly. When the Ascend runtime or a compiled .om model is missing, the broker
returns 503 instead of silently using the CPU, so provenance stays truthful.

    uvicorn rootcause.npu.service:app --host 127.0.0.1 --port 7788
    ROOTCAUSE_NPU_SIMULATE=1 uvicorn rootcause.npu.service:app --port 7788   # laptop demo
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..engine.detection import detect

app = FastAPI(title="RootCause NPU broker", version="0.9.0")


class InferRequest(BaseModel):
    image: str
    model: str = "defect.om"


def _simulate() -> bool:
    return os.getenv("ROOTCAUSE_NPU_SIMULATE", "").lower() in {"1", "true", "yes"}


def _ascend_ready() -> bool:
    try:
        import acl  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


@app.get("/health")
def health() -> dict[str, Any]:
    mode = "simulated" if _simulate() else "ascend" if _ascend_ready() else "unavailable"
    return {
        "backend": mode,
        "device": "Ascend 310P" if mode == "ascend" else "CPU (demo)",
        "ready": mode in {"simulated", "ascend"},
        "model": os.getenv("ROOTCAUSE_NPU_MODEL", "defect.om"),
    }


@app.post("/infer")
def infer(req: InferRequest) -> dict[str, Any]:
    image = Path(req.image)
    if not image.exists():
        raise HTTPException(404, f"image not found: {image}")
    if _simulate():
        det = detect(image)
        return {
            "request_id": f"inf-{uuid.uuid4().hex[:10]}",
            "model": "rootcause-detector-0.9",
            "label": det.label,
            "bbox": det.bbox,
            "confidence": det.confidence,
            "device": "CPU (demo)",
            "backend": "simulated",
        }
    if not _ascend_ready():
        raise HTTPException(503, "Ascend runtime not available; refusing to pretend the NPU ran")
    # The production implementation binds to the ACL OM executor here. See docs/deployment.md.
    raise HTTPException(501, "ACL executor not compiled into this build; install the site NPU package")
