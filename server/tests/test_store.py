from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rootcause.demo.build_pack import build_pack
from rootcause.store.db import Store


@pytest.fixture()
def store(tmp_path: Path):
    s = Store(tmp_path / "test.sqlite3")
    s.seed(build_pack().model_dump(mode="json"))
    yield s
    s.close()


def test_seeded_cases_and_reports(store: Store):
    cases = store.list_cases()
    assert {c["case"]["id"] for c in cases} == {"RC-0417", "RC-0431", "RC-0440", "RC-0452"}
    assert store.get_report("RC-0417")["status"] == "draft"


def test_audit_trail_is_append_only(store: Store):
    before = len(store.audits())
    with pytest.raises(sqlite3.IntegrityError):
        store._conn.execute("UPDATE audits SET actor='tamper' WHERE id='A-1042'")
    with pytest.raises(sqlite3.IntegrityError):
        store._conn.execute("DELETE FROM audits WHERE id='A-1042'")
    assert len(store.audits()) == before


def test_rejection_is_recorded_as_correction(store: Store):
    pack = build_pack().model_dump(mode="json")
    scenario = pack["scenarios"][0]
    from rootcause.engine.ranking import rank_hypotheses
    from rootcause.models import Hypothesis

    ranked = rank_hypotheses([Hypothesis.model_validate(h) for h in scenario["hypotheses"]], rejected=["tool_mark"])
    store.update_hypotheses(
        "RC-0417",
        [h.model_dump(mode="json") for h in ranked],
        actor="M. Weber",
        action="cause.rejected",
        detail="Rejected tool mark",
        reason="Crack starts below the surface",
        hid="tool_mark",
    )
    corrections = store.corrections("RC-0417")
    assert corrections[0]["hypothesis_id"] == "tool_mark"
    assert corrections[0]["action"] == "cause.rejected"
    assert any(a["action"] == "cause.rejected" for a in store.audits("RC-0417"))


def test_report_versioning_and_approval(store: Store):
    report = store.get_report("RC-0417")
    report["summary"] = "Edited by engineer"
    report["version"] += 1
    store.save_report("RC-0417", report, actor="M. Weber", action="report.edited", detail="Edit")
    versions = store.report_versions(report["id"])
    assert len(versions) == 2

    approved = store.approve("RC-0417", actor="M. Weber", scope="report", note="Sign-off")
    assert approved["status"] == "approved"
    latest = store.get_report("RC-0417")
    assert latest["status"] == "approved"
    assert latest["approved_by"] == "M. Weber"
    assert any(a["action"] == "case.approved" for a in store.audits())


def test_baseline(store: Store):
    store.set_baseline("line-6", 48.5)
    row = next(b for b in store.baselines() if b["line_id"] == "line-6")
    assert row["baseline_hours"] == 48.5


def test_decisions_are_restored(store: Store):
    pack = build_pack().model_dump(mode="json")
    scenario = pack["scenarios"][0]
    from rootcause.engine.ranking import rank_hypotheses
    from rootcause.models import Hypothesis

    ranked = rank_hypotheses([Hypothesis.model_validate(h) for h in scenario["hypotheses"]], rejected=["tool_mark"])
    store.update_hypotheses(
        "RC-0417",
        [h.model_dump(mode="json") for h in ranked],
        actor="M. Weber",
        action="cause.rejected",
        detail="Rejected tool mark",
        reason="Below surface",
        hid="tool_mark",
    )
    decisions = store.decisions()
    assert decisions["RC-0417"]["rejected"] == ["tool_mark"]

