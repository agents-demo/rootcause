from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rootcause.demo.build_pack import build_pack
from rootcause.models import WatchCase
from rootcause.proactive import brief, containment, notifications, scheduler, signals
from rootcause.proactive import watch as watch_engine
from rootcause.proactive.queue import OfflineQueue
from rootcause.research import predictive

TZ = UTC
NOW = datetime(2026, 10, 22, 6, 42, tzinfo=TZ)


def pack() -> dict:
    return build_pack().model_dump(mode="json")


def test_signal_detectors_are_deterministic():
    values = [1.0, 1.02, 0.99, 1.01, 1.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7]
    e = signals.ewma(values)
    assert len(e) == len(values)
    assert e[-1] > e[0]
    c = signals.cusum(values, target=1.0, sigma=0.1)
    assert c["high"] > 5
    cp = signals.change_point(values)
    assert cp["shift"] > 1.5


def test_scan_scenario_finds_the_hydrogen_pattern():
    p = pack()
    found = signals.scan_scenario(p["scenarios"][0])
    assert any("hydrogen" in s.parameter.lower() for s in found)
    assert any(s.kind in {"ewma", "spc", "change_point"} for s in found)
    assert signals.signal_risk(found) > 0.4
    deduped = signals.dedupe(found)
    assert len(deduped) <= len(found)


def test_watch_lifecycle_and_storm_guard():
    p = pack()
    pattern = p["proactive"]["patterns"][0]
    sigs = signals.scan_scenario(p["scenarios"][0])
    w = watch_engine.build_watch(watch_id="W-T", signals=sigs, pattern=pattern, owner="M. Weber", now=NOW)
    assert w.status == "watching"
    w = watch_engine.triage(w, actor="M. Weber", note="checking", now=NOW)
    assert w.status == "triage"
    w = watch_engine.dismiss(w, actor="M. Weber", reason="test", now=NOW)
    assert w.status == "dismissed" and w.outcome == "false_alarm"
    w = watch_engine.convert(w, case_id="RC-0417", actor="M. Weber", reason="converted", now=NOW)
    assert w.status == "converted" and w.useful is True

    many = [w]
    kept, suppressed = watch_engine.storm_guard(many * 4, max_alerts=2)
    assert len(kept) == 2
    assert suppressed == 2


def test_containment_recommendation_and_exposure():
    p = pack()
    pattern = p["proactive"]["patterns"][0]
    w = WatchCase.model_validate(p["proactive"]["watches"][0])
    rec = containment.build_recommendation(
        rec_id="REC-T", watch=w, kind="hold_batch", pattern=pattern, parts_at_risk=8, now=NOW, batch_id="B-2291"
    )
    assert rec.status == "proposed"
    assert rec.impact.scrap_avoided_eur > 0
    rec = containment.approve(rec, actor="M. Weber", now=NOW)
    assert rec.status == "approved"
    rec = containment.execute(rec, actor="M. Weber", now=NOW)
    assert rec.status == "executed"
    rec = containment.verify(rec, actor="M. Weber", note="ok", now=NOW)
    assert rec.status == "verified"

    exp = containment.exposure_for(
        exposure_id="EXP-T", watch=w, batch_id="B-2291",
        parts=[{"serial": "A", "part": "Bracket", "customer": "X"}], now=NOW,
    )
    assert exp.customers == 1 and exp.parts[0].containment == "hold"


def test_shift_brief_and_notifications():
    p = pack()
    watches = [WatchCase.model_validate(w) for w in p["proactive"]["watches"]]
    b = brief.build_brief(
        brief_id="BRIEF-T", watches=watches, cases=[],
        actions=p["actions"], followups=p["proactive"]["followups"], coverage=p["proactive"]["coverage"],
        lines=["line-6"], shift="B", now=NOW,
    )
    assert "Shift B" in b.title
    assert b.top_risks
    md = brief.render_brief_markdown(b)
    assert "Recommendations only" in md

    n = notifications.build_notification(
        notification_id="NT-T", watch=watches[0], kind="watch", severity="critical",
        title="Test", detail="Test detail", now=NOW,
    )
    assert notifications.dedupe([{**n.model_dump(), "read": False}], n) is True
    assert notifications.in_quiet_hours(datetime(2026, 10, 22, 23, 0, tzinfo=TZ)) is True
    assert notifications.in_quiet_hours(NOW) is False
    assert notifications.sign_payload(b"{}", "secret").startswith("sha256=")


def test_scheduler_scan_is_deduplicated():
    p = pack()
    first = scheduler.run_scan(pack=p, existing=[], now=NOW, max_alerts=10)
    assert first["run"].status == "ok"
    assert first["signals"]
    assert first["candidates"]
    existing = [WatchCase.model_validate(c) for c in first["candidates"]]
    second = scheduler.run_scan(pack=p, existing=existing, now=NOW + timedelta(minutes=15), max_alerts=10)
    assert second["candidates"] == []
    assert second["run"].suppressed >= 1
    replay = scheduler.replay(p)
    assert replay["precision"] >= 0
    assert len(replay["rows"]) == 4


def test_research_gate_stops_without_sufficient_data():
    audit = predictive.data_audit(3, 4)
    assert audit["sufficient"] is False
    y, baseline, model, _ = predictive.synthetic_events()
    result = predictive.run("test", y, baseline, model, 3, 4, 8.0)
    assert result.status == "data_audit"
    assert "Stopped at data audit" in result.decision


def test_research_gate_reports_a_decision():
    y, baseline, model, _ = predictive.synthetic_events()
    result = predictive.run("test", y, baseline, model, 14, 34, 8.0)
    assert result.status in {"stopped", "shadow"}
    assert 0 <= result.model_auc <= 1
    assert result.cost_of_errors_eur >= 0


def test_survival_and_censoring():
    prepared = predictive.prepare_survival([10, 20, 30, 40], [1, 0, 1, 0])
    assert prepared["failures"] == 2
    assert prepared["censored"] == 2
    curve = predictive.kaplan_meier([10, 20, 30, 40], [1, 0, 1, 0])
    assert curve[-1]["survival"] <= curve[0]["survival"]
    assert predictive.c_index([1, 2, 3, 4], [1, 1, 1, 1], [4, 3, 2, 1]) == 1.0


def test_offline_queue_is_bounded_and_deduplicated():
    q = OfflineQueue(max_items=2)
    assert q.push({"v": 1}, key="a") is True
    assert q.push({"v": 2}, key="a") is False
    assert q.push({"v": 2}, key="b") is True
    assert q.push({"v": 3}, key="c") is True
    assert q.summary()["queued"] == 2
    assert q.summary()["dropped"] == 1
    assert len(q.drain()) == 2
    assert q.summary()["queued"] == 0
