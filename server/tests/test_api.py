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
