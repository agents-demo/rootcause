"""Runtime configuration. All paths stay on the site; nothing is fetched from the internet."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SERVER_DIR / "rootcause" / "data"
RUNTIME_DIR = Path(os.getenv("ROOTCAUSE_RUNTIME", REPO_ROOT / "runtime"))
WEB_DIST = REPO_ROOT / "web" / "dist"

DATA_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("ROOTCAUSE_DB", RUNTIME_DIR / "rootcause.sqlite3"))
PACK_PATH = Path(os.getenv("ROOTCAUSE_PACK", DATA_DIR / "demo_pack.json"))
MODEL_VERSION = os.getenv("ROOTCAUSE_MODEL", "rootcause-0.9.0")


def cors_origins() -> list[str]:
    raw = os.getenv("ROOTCAUSE_CORS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000")
    return [o.strip() for o in raw.split(",") if o.strip()]
