"""Generate the deterministic demo pack consumed by the API and the static web build."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from rootcause.demo.build_pack import build_pack


def main() -> None:
    pack = build_pack().model_dump(mode="json")
    targets = [
        ROOT / "server" / "rootcause" / "data" / "demo_pack.json",
        ROOT / "web" / "public" / "demo-pack.json",
    ]
    blob = json.dumps(pack, indent=2, ensure_ascii=False)
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)} ({len(blob):,} bytes)")


if __name__ == "__main__":
    main()
