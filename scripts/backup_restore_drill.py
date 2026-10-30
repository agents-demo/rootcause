"""Backup and restore drill for the on-site SQLite store.

Proves that an approved case and its append-only audit trail survive a backup/restore, and that the
restored audit table still rejects UPDATE and DELETE.

Run from the repository root:

    python scripts/backup_restore_drill.py

Exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from rootcause.demo.build_pack import build_pack
from rootcause.store.db import Store

CASE = "RC-0417"


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"{'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    return condition


def main() -> int:
    pack = build_pack().model_dump(mode="json")
    with tempfile.TemporaryDirectory() as tmp:
        live = Path(tmp) / "rootcause.sqlite3"
        backup = Path(tmp) / "rootcause-backup.sqlite3"
        restored = Path(tmp) / "rootcause-restored.sqlite3"

        store = Store(live)
        store.seed(pack)
        store.approve(CASE, actor="M. Weber", scope="report", note="drill")
        before_status = store.get_case(CASE)["status"]
        before_audits = store.audits(limit=1000)
        store.close()

        src = sqlite3.connect(live)
        dst = sqlite3.connect(backup)
        src.backup(dst)
        dst.close()
        src.close()

        live.unlink()  # simulate the working copy being lost
        backup.replace(restored)

        revived = Store(restored)
        after = revived.get_case(CASE)
        after_audits = revived.audits(limit=1000)
        revived.close()

        checks = [
            check("backup file exists", restored.exists()),
            check("case survived with approved status", after is not None and after["status"] == before_status, before_status),
            check("audit trail survived", len(after_audits) == len(before_audits), f"{len(before_audits)} events"),
            check(
                "audit events reconstruct identically",
                json.dumps(after_audits, sort_keys=True) == json.dumps(before_audits, sort_keys=True),
            ),
        ]

        conn = sqlite3.connect(restored)
        try:
            conn.execute("UPDATE audits SET actor='tampered' WHERE rowid=1")
            conn.commit()
            checks.append(check("restored audit trail rejects UPDATE", False))
        except sqlite3.IntegrityError as exc:
            checks.append(check("restored audit trail rejects UPDATE", "append-only" in str(exc)))
        try:
            conn.execute("DELETE FROM audits WHERE rowid=1")
            conn.commit()
            checks.append(check("restored audit trail rejects DELETE", False))
        except sqlite3.IntegrityError as exc:
            checks.append(check("restored audit trail rejects DELETE", "append-only" in str(exc)))
        conn.close()

        ok = all(checks)
        print("drill:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
