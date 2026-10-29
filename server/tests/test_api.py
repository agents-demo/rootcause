from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from rootcause.api.app import app


def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ROOTCAUSE_DB", str(tmp_path / "api.sqlite3"))
    monkeypatch.setenv("ROOTCAUSE_PACK", str(tmp_path / "pack.json"))
    with TestClient(app) as c:
        yield c


def test_health_and_pack(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True
        pack = c.get("/api/pack").json()
        assert len(pack["scenarios"]) == 4
        assert len(pack["connectors"]) >= 10


def test_investigation_and_reject_flow(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        inv = c.get("/api/cases/RC-0417").json()["investigation"]
        assert inv["hypotheses"][0]["id"] == "tool_mark"

        r = c.post(
            "/api/cases/RC-0417/reject",
            json={"hypothesis_id": "tool_mark", "reason": "Crack starts below the surface", "actor": "M. Weber"},
        )
        assert r.status_code == 200
        ranked = r.json()["hypotheses"]
        assert ranked[0]["id"] == "gas_porosity"
        assert any(h["status"] == "rejected" for h in ranked)

        r = c.post(
            "/api/cases/RC-0417/accept",
            json={"hypothesis_id": "gas_porosity", "actor": "M. Weber"},
        )
        assert r.status_code == 200
        accepted = next(h for h in r.json()["hypotheses"] if h["id"] == "gas_porosity")
        assert accepted["status"] == "accepted"


def test_report_edit_approve_and_exports(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        r = c.patch("/api/reports/RC-0417", json={"summary": "Approved cause: gas porosity.", "actor": "M. Weber"})
        assert r.status_code == 200
        assert r.json()["report"]["version"] == 2

        html = c.get("/api/reports/RC-0417/html")
        assert html.status_code == 200
        assert "gas porosity" in html.text.lower()

        md = c.get("/api/reports/RC-0417/markdown")
        assert "Evidence appendix" in md.text

        r = c.post("/api/cases/RC-0417/approve", json={"actor": "M. Weber", "note": "Sign-off"})
        assert r.status_code == 200
        assert r.json()["case"]["status"] == "approved"

        pdf = c.get("/api/reports/RC-0417/pdf")
        assert pdf.status_code in (200, 501)
        if pdf.status_code == 200:
            assert pdf.content[:4] == b"%PDF"
        word = c.get("/api/reports/RC-0417/docx")
        assert word.status_code == 200
        assert len(word.content) > 1000


def test_manual_cause(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        r = c.post(
            "/api/cases/RC-0417/manual",
            json={"label": "Furnace atmosphere", "summary": "Engineer suspects nitrogen purge failure.", "actor": "M. Weber"},
        )
        assert r.status_code == 200
        assert any(h["status"] == "manual" for h in r.json()["hypotheses"])


def test_dashboard_connectors_compliance_and_export(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        d = c.get("/api/dashboard").json()
        assert d["kpis"]["median_hours_to_cause"] > 0
        assert d["savings"]["total_eur"] > 0

        conn = c.get("/api/connectors").json()
        assert len(conn["library"]) >= 10
        test = c.post("/api/connectors/opcua-furnace/test").json()
        assert test["result"]["reachable"] is True

        comp = c.get("/api/compliance/iso9001").json()
        assert comp["controls"][0]["state"] == "covered"

        csv_resp = c.get("/api/export/cases.csv")
        rows = list(csv.reader(io.StringIO(csv_resp.text)))
        assert rows[0][0] == "case_id"
        assert len(rows) == 5

        sharing = c.post("/api/sharing", json={"enabled": True}).json()
        assert sharing["enabled"] is True
        assert sharing["records"]


def test_detect_upload(tmp_path, monkeypatch):
    from rootcause.engine.detection import generate_part_image

    img = generate_part_image("bracket", tmp_path / "frame.png")
    for c in client(tmp_path, monkeypatch):
        with img.open("rb") as fh:
            r = c.post("/api/detect", files={"file": ("frame.png", fh, "image/png")})
        assert r.status_code == 200
        assert r.json()["detection"]["confidence"] > 0.5


def test_tenant_isolation(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        acme = {"X-RootCause-Tenant": "acme"}
        r = c.post(
            "/api/cases/RC-0417/accept",
            json={"hypothesis_id": "gas_porosity", "actor": "Acme Engineer"},
            headers=acme,
        )
        assert r.status_code == 200
        assert r.headers["X-RootCause-Tenant"] == "acme"

        acme_inv = c.get("/api/cases/RC-0417", headers=acme).json()["investigation"]
        assert any(h["status"] == "accepted" for h in acme_inv["hypotheses"])

        default_inv = c.get("/api/cases/RC-0417").json()["investigation"]
        assert not any(h["status"] == "accepted" for h in default_inv["hypotheses"])

        assert c.get("/api/tenants").json()["header"] == "X-RootCause-Tenant"


def test_proactive_pack_and_watch_workflow(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        r = c.get("/api/proactive")
        assert r.status_code == 200
        data = r.json()
        assert len(data["watches"]) >= 7
        assert data["metrics"]["watch_precision"] > 0
        assert data["health"]["status"] == "ok"
        assert data["patterns"]

        detail = c.get("/api/watch/W-1042")
        assert detail.status_code == 200
        assert detail.json()["watch"]["linked_case_id"] == "RC-0417"
        assert detail.json()["recommendations"]

        triaged = c.post("/api/watch/W-1044/triage", json={"actor": "M. Weber", "note": "checking"})
        assert triaged.status_code == 200
        assert triaged.json()["status"] == "triage"

        approved = c.post("/api/recommendations/REC-2205/approve", json={"actor": "M. Weber"})
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        executed = c.post("/api/recommendations/REC-2205/execute", json={"actor": "M. Weber"})
        assert executed.status_code == 200
        assert executed.json()["status"] == "executed"

        dismissed = c.post("/api/watch/W-1048/dismiss", json={"actor": "M. Weber", "reason": "setup watch, no signal"})
        assert dismissed.status_code == 200
        assert dismissed.json()["outcome"] == "false_alarm"

        converted = c.post("/api/watch/W-1046/convert", json={"actor": "M. Weber", "case_id": "RC-0417"})
        assert converted.status_code == 200
        assert converted.json()["outcome"] == "converted"


def test_proactive_brief_scan_notifications_and_settings(tmp_path, monkeypatch):
    for c in client(tmp_path, monkeypatch):
        scan = c.post("/api/proactive/scan", json={"mode": "shadow"})
        assert scan.status_code == 200
        assert "run" in scan.json()

        brief = c.post("/api/briefs/generate", json={"shift": "B"})
        assert brief.status_code == 200
        assert "Shift B" in brief.json()["brief"]["title"]
        assert "Recommendations only" in brief.json()["markdown"]

        notes = c.get("/api/notifications").json()
        assert notes
        read = c.post(f"/api/notifications/{notes[0]['id']}/read")
        assert read.status_code == 200

        stopped = c.post("/api/proactive/stop", json={"reason": "test"})
        assert stopped.status_code == 200
        assert stopped.json()["stop_switch"] is True
        blocked = c.post("/api/proactive/scan", json={})
        assert blocked.status_code == 409
        started = c.post("/api/proactive/start")
        assert started.status_code == 200
        assert started.json()["stop_switch"] is False

        threshold = c.post("/api/proactive/thresholds/TH-1", json={"limit": 1.3})
        assert threshold.status_code == 200
        assert threshold.json()["limit"] == 1.3

        research = c.post("/api/proactive/research/run")
        assert research.status_code == 200
        assert research.json()["status"] in {"stopped", "shadow"}

        near = c.post("/api/proactive/near-miss", json={"line_id": "line-6", "note": "Unusual sound, no defect yet"})
        assert near.status_code == 200
        assert near.json()["signals"][0]["kind"] == "near_miss"

        exposure = c.get("/api/exposures/W-1042")
        assert exposure.status_code == 200
        assert exposure.json()["parts"]
        released = c.post("/api/exposures/W-1042/release", json={"status": "contained", "actor": "M. Weber"})
        assert released.status_code == 200
        assert released.json()["status"] == "contained"
        csv_exposure = c.get("/api/exposures/W-1042/export.csv")
        assert csv_exposure.status_code == 200
        assert "serial" in csv_exposure.text

        pattern = c.post("/api/proactive/patterns/P-SEAL", json={"status": "active", "actor": "M. Weber"})
        assert pattern.status_code == 200
        assert pattern.json()["status"] == "active"

        follow = c.post("/api/followups/FU-102/verify", json={"parameter_returned": True, "defect_rate_delta": -0.1})
        assert follow.status_code == 200
        assert follow.json()["status"] == "verified"

