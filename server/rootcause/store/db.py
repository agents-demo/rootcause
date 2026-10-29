"""Local, on-site store.

SQLite is deliberate: a pilot must run with no outbound network. The audit trail is append-only at
the database level (triggers reject UPDATE and DELETE), so "who approved what" survives every app
bug and every operator with a SQL console.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  status TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hypotheses (
  case_id TEXT NOT NULL,
  id TEXT NOT NULL,
  status TEXT NOT NULL,
  score REAL NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (case_id, id)
);
CREATE TABLE IF NOT EXISTS reports (
  id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  status TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (id, version)
);
CREATE TABLE IF NOT EXISTS audits (
  id TEXT PRIMARY KEY,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  object TEXT NOT NULL,
  detail TEXT NOT NULL,
  model_version TEXT NOT NULL,
  data_sources TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audits_no_update BEFORE UPDATE ON audits
BEGIN SELECT RAISE(ABORT, 'audit trail is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audits_no_delete BEFORE DELETE ON audits
BEGIN SELECT RAISE(ABORT, 'audit trail is append-only'); END;
CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  case_id TEXT NOT NULL,
  hypothesis_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS baselines (
  line_id TEXT PRIMARY KEY,
  baseline_hours REAL NOT NULL,
  recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------ seeding
    def seed(self, pack: dict[str, Any]) -> None:
        cur = self._conn.cursor()
        for scenario in pack["scenarios"]:
            case = scenario["case"]
            cur.execute(
                "INSERT OR IGNORE INTO cases(id, scenario_id, status, payload, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (case["id"], scenario["id"], case["status"], json.dumps(scenario), case["detected_at"], case["detected_at"]),
            )
            for h in scenario["hypotheses"]:
                cur.execute(
                    "INSERT OR IGNORE INTO hypotheses(case_id, id, status, score, payload, updated_at) VALUES (?,?,?,?,?,?)",
                    (case["id"], h["id"], h["status"], h["score"], json.dumps(h), utcnow()),
                )
            r = scenario["report"]
            cur.execute(
                "INSERT OR IGNORE INTO reports(id, case_id, version, status, payload, updated_at) VALUES (?,?,?,?,?,?)",
                (r["id"], case["id"], r["version"], r["status"], json.dumps(r), utcnow()),
            )
        for a in pack.get("audits", []):
            cur.execute(
                "INSERT OR IGNORE INTO audits(id, at, actor, action, object, detail, model_version, data_sources) VALUES (?,?,?,?,?,?,?,?)",
                (a["id"], a["at"], a["actor"], a["action"], a["object"], a["detail"], a.get("model_version", ""), json.dumps(a.get("data_sources", []))),
            )
        for line in pack.get("lines", []):
            cur.execute(
                "INSERT OR IGNORE INTO baselines(line_id, baseline_hours, recorded_at) VALUES (?,?,?)",
                (line["id"], pack["dashboard"]["baseline_hours_to_cause"], utcnow()),
            )
        self._conn.commit()

    # ------------------------------------------------------------------ reads
    def list_cases(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT payload FROM cases ORDER BY updated_at DESC").fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT payload FROM cases WHERE id=?", (case_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def get_report(self, case_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM reports WHERE case_id=? ORDER BY version DESC LIMIT 1", (case_id,)
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def decisions(self) -> dict[str, dict[str, Any]]:
        """Restore per-case human decisions after a restart."""
        rows = self._conn.execute("SELECT * FROM corrections ORDER BY at ASC").fetchall()
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            entry = out.setdefault(row["case_id"], {"rejected": [], "accepted": None, "manual": []})
            action = row["action"]
            if action == "cause.rejected" and row["hypothesis_id"] not in entry["rejected"]:
                entry["rejected"].append(row["hypothesis_id"])
            elif action == "cause.accepted":
                entry["accepted"] = row["hypothesis_id"]
            elif action == "cause.manual":
                payload = json.loads(row["payload"])
                for h in payload.get("hypotheses", []):
                    if h.get("status") == "manual" and not any(m["id"] == h["id"] for m in entry["manual"]):
                        entry["manual"].append(h)
        return out

    def report_versions(self, report_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT payload FROM reports WHERE id=? ORDER BY version DESC", (report_id,)
        ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def audits(self, object_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if object_id:
            rows = self._conn.execute(
                "SELECT * FROM audits WHERE object=? ORDER BY at DESC LIMIT ?", (object_id, limit)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM audits ORDER BY at DESC LIMIT ?", (limit,)).fetchall()
        return [
            {
                "id": r["id"],
                "at": r["at"],
                "actor": r["actor"],
                "action": r["action"],
                "object": r["object"],
                "detail": r["detail"],
                "model_version": r["model_version"],
                "data_sources": json.loads(r["data_sources"]),
            }
            for r in rows
        ]

    def corrections(self, case_id: str | None = None) -> list[dict[str, Any]]:
        if case_id:
            rows = self._conn.execute(
                "SELECT * FROM corrections WHERE case_id=? ORDER BY at DESC", (case_id,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM corrections ORDER BY at DESC").fetchall()
        return [
            {
                "id": r["id"],
                "at": r["at"],
                "case_id": r["case_id"],
                "hypothesis_id": r["hypothesis_id"],
                "action": r["action"],
                "actor": r["actor"],
                "reason": r["reason"],
                "payload": json.loads(r["payload"]),
            }
            for r in rows
        ]

    def metrics(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) c FROM cases").fetchone()["c"]
        approved = self._conn.execute("SELECT COUNT(*) c FROM cases WHERE status='approved'").fetchone()["c"]
        corrections = self._conn.execute("SELECT COUNT(*) c FROM corrections").fetchone()["c"]
        return {
            "cases": total,
            "approved": approved,
            "corrections": corrections,
            "approval_rate": round(approved / total, 3) if total else 0.0,
        }

    # ------------------------------------------------------------------ writes
    def _audit(self, actor: str, action: str, obj: str, detail: str, sources: Iterable[str] = ()) -> None:
        c = self._conn.cursor()
        n = c.execute("SELECT COUNT(*) c FROM audits").fetchone()["c"]
        c.execute(
            "INSERT INTO audits(id, at, actor, action, object, detail, model_version, data_sources) VALUES (?,?,?,?,?,?,?,?)",
            (f"A-{2000 + n}", utcnow(), actor, action, obj, detail, "rootcause-0.9.0", json.dumps(list(sources))),
        )

    def update_hypotheses(self, case_id: str, hypotheses: list[dict[str, Any]], *, actor: str, action: str, detail: str, reason: str = "", hid: str = "") -> None:
        c = self._conn.cursor()
        for h in hypotheses:
            c.execute(
                "INSERT INTO hypotheses(case_id, id, status, score, payload, updated_at) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(case_id, id) DO UPDATE SET status=excluded.status, score=excluded.score, payload=excluded.payload, updated_at=excluded.updated_at",
                (case_id, h["id"], h["status"], h["score"], json.dumps(h), utcnow()),
            )
        if hid:
            c.execute(
                "INSERT INTO corrections(at, case_id, hypothesis_id, action, actor, reason, payload) VALUES (?,?,?,?,?,?,?)",
                (utcnow(), case_id, hid, action, actor, reason, json.dumps({"hypotheses": hypotheses})),
            )
        case = self.get_case(case_id)
        if case:
            case["hypotheses"] = hypotheses
            case["status"] = "awaiting_review"
            c.execute("UPDATE cases SET payload=?, status=?, updated_at=? WHERE id=?", (json.dumps(case), case["status"], utcnow(), case_id))
        self._audit(actor, action, case_id, detail)
        self._conn.commit()

    def save_report(self, case_id: str, report: dict[str, Any], *, actor: str, action: str, detail: str) -> None:
        c = self._conn.cursor()
        c.execute(
            "INSERT INTO reports(id, case_id, version, status, payload, updated_at) VALUES (?,?,?,?,?,?)",
            (report["id"], case_id, report["version"], report["status"], json.dumps(report), utcnow()),
        )
        case = self.get_case(case_id)
        if case:
            case["report"] = report
            if report["status"] == "approved":
                case["status"] = "approved"
            c.execute("UPDATE cases SET payload=?, status=?, updated_at=? WHERE id=?", (json.dumps(case), case.get("status", "investigating"), utcnow(), case_id))
        self._audit(actor, action, case_id, detail)
        self._conn.commit()

    def approve(self, case_id: str, *, actor: str, scope: str, note: str = "") -> dict[str, Any] | None:
        case = self.get_case(case_id)
        if not case:
            return None
        report = self.get_report(case_id)
        if report:
            report["status"] = "approved"
            report["approved_by"] = actor
            report["approved_at"] = utcnow()
            report["version"] = report.get("version", 1) + 1
            self.save_report(case_id, report, actor=actor, action="report.approved", detail=f"{scope} approved. {note}".strip())
        case = self.get_case(case_id)
        if case:
            case["status"] = "approved"
            self._conn.execute("UPDATE cases SET status=?, payload=?, updated_at=? WHERE id=?", ("approved", json.dumps(case), utcnow(), case_id))
            self._audit(actor, "case.approved", case_id, f"Engineer sign-off. {note}".strip())
            self._conn.commit()
        return case

    def set_status(self, case_id: str, status: str, *, actor: str, detail: str) -> None:
        case = self.get_case(case_id)
        if not case:
            return
        case["status"] = status
        self._conn.execute("UPDATE cases SET status=?, payload=?, updated_at=? WHERE id=?", (status, json.dumps(case), utcnow(), case_id))
        self._audit(actor, "case.status", case_id, detail)
        self._conn.commit()

    def set_baseline(self, line_id: str, hours: float) -> None:
        self._conn.execute(
            "INSERT INTO baselines(line_id, baseline_hours, recorded_at) VALUES (?,?,?) "
            "ON CONFLICT(line_id) DO UPDATE SET baseline_hours=excluded.baseline_hours, recorded_at=excluded.recorded_at",
            (line_id, hours, utcnow()),
        )
        self._conn.commit()

    def baselines(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM baselines").fetchall()
        return [dict(r) for r in rows]
