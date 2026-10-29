"""Synthetic proactive layer for the demo.

The watches are curated to tell a coherent story: risk was visible before the defect, the evidence
was assembled, containment was recommended and a human decided. The metrics are honest about a
real-looking alert budget rather than a perfect precision score.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..models import (
    Coverage,
    Exposure,
    ExposurePart,
    FollowUp,
    ImpactEstimate,
    ModelCard,
    Notification,
    ProactiveMetrics,
    ProactivePack,
    ProactiveSettings,
    Recommendation,
    ResearchGate,
    RiskPattern,
    RiskSignal,
    ScanRun,
    ScheduleSettings,
    ShiftBrief,
    SuggestedCheck,
    ThresholdRule,
    WatchCase,
)

TZ = UTC
ANCHOR = datetime(2026, 10, 22, 6, 42, tzinfo=TZ)


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_proactive() -> ProactivePack:
    signals = {
        "SIG-4101": RiskSignal(
            id="SIG-4101", kind="ewma", at=iso(ANCHOR - timedelta(hours=5, minutes=20)), line_id="line-6",
            parameter="Melt hydrogen", value=2.04, baseline=1.18, z=9.6, severity="critical",
            detail="EWMA crossed the 1.4 ppm limit 5 h before the fracture; the trend started after the door-seal work.",
            evidence_id="EV-04",
        ),
        "SIG-4102": RiskSignal(
            id="SIG-4102", kind="maintenance", at=iso(ANCHOR - timedelta(days=12)), line_id="line-6",
            parameter="Furnace door seal", value=None, baseline=None, z=None, severity="high",
            detail="Door seal replaced 12 days earlier; no post-repair hydrogen validation was recorded.",
            evidence_id="EV-07",
        ),
        "SIG-4103": RiskSignal(
            id="SIG-4103", kind="batch", at=iso(ANCHOR - timedelta(days=9)), line_id="line-6",
            parameter="Batch B-2291", value=1.9, baseline=1.4, z=3.4, severity="high",
            detail="Incoming hydrogen 1.9 ppm against a 1.4 ppm limit, accepted on a supplier deviation.",
            evidence_id="EV-06",
        ),
        "SIG-4104": RiskSignal(
            id="SIG-4104", kind="change_point", at=iso(ANCHOR - timedelta(hours=2, minutes=10)), line_id="line-6",
            parameter="Quench bath temperature", value=42.0, baseline=58.0, z=-6.4, severity="high",
            detail="A step change of −16 °C appears 2 h before the defect; the control valve is responding slowly.",
            evidence_id="EV-05",
        ),
        "SIG-4201": RiskSignal(
            id="SIG-4201", kind="ewma", at=iso(ANCHOR + timedelta(minutes=8) - timedelta(hours=3, minutes=40)), line_id="line-2",
            parameter="Resin moisture", value=0.151, baseline=0.08, z=5.9, severity="high",
            detail="Moisture rose above 0.12 % for 47 minutes after the dryer missed regeneration.",
            evidence_id="H-EV-02",
        ),
        "SIG-4202": RiskSignal(
            id="SIG-4202", kind="maintenance", at=iso(ANCHOR - timedelta(days=8)), line_id="line-2",
            parameter="Dryer 3", value=None, baseline=None, z=None, severity="high",
            detail="Dryer regeneration overdue by 38 h; no alarm fired.",
            evidence_id="H-EV-05",
        ),
        "SIG-4203": RiskSignal(
            id="SIG-4203", kind="batch", at=iso(ANCHOR + timedelta(minutes=8) - timedelta(days=6)), line_id="line-2",
            parameter="Batch PL-8840", value=0.151, baseline=0.12, z=2.6, severity="warning",
            detail="Resin lot PL-8840 opened 6 days ago; moisture is above the drying window.",
            evidence_id="H-EV-04",
        ),
        "SIG-4301": RiskSignal(
            id="SIG-4301", kind="cusum", at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=42)), line_id="line-4",
            parameter="Laser power", value=1.64, baseline=1.82, z=-4.5, severity="high",
            detail="CUSUM detects a sustained 10 % power loss; the power monitor calibration is 41 days overdue.",
            evidence_id="B-EV-02",
        ),
        "SIG-4302": RiskSignal(
            id="SIG-4302", kind="maintenance", at=iso(ANCHOR + timedelta(minutes=16) - timedelta(days=41)), line_id="line-4",
            parameter="Welder 7 calibration", value=None, baseline=None, z=None, severity="warning",
            detail="Power monitor calibration overdue; no certificate on file.",
            evidence_id="B-EV-03",
        ),
        "SIG-4401": RiskSignal(
            id="SIG-4401", kind="change_point", at=iso(ANCHOR + timedelta(minutes=23) - timedelta(minutes=31)), line_id="line-3",
            parameter="Reflow zone 3", value=206.0, baseline=217.0, z=-5.2, severity="high",
            detail="A step change of −11 °C follows the heater-element check; the profile was not re-validated.",
            evidence_id="E-EV-02",
        ),
        "SIG-4402": RiskSignal(
            id="SIG-4402", kind="first_off", at=iso(ANCHOR + timedelta(minutes=23) - timedelta(minutes=28)), line_id="line-3",
            parameter="First-off X-ray", value=0.31, baseline=0.25, z=2.1, severity="warning",
            detail="First-off voiding is 31 % against a 25 % limit, but the part was released on a visual check only.",
            evidence_id="E-EV-01",
        ),
        "SIG-4501": RiskSignal(
            id="SIG-4501", kind="data_quality", at=iso(ANCHOR - timedelta(hours=2, minutes=30)), line_id="line-2",
            parameter="Camera CAM-02", value=None, baseline=None, z=None, severity="warning",
            detail="Camera 2 stopped sending frames for 26 minutes. Quality risk is unknown for that window.",
            evidence_id="",
        ),
        "SIG-4502": RiskSignal(
            id="SIG-4502", kind="setup", at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=55)), line_id="line-4",
            parameter="New foil lot F-771", value=None, baseline=None, z=None, severity="info",
            detail="New foil lot and a supplier process change; watch window opened for the first 40 welds.",
            evidence_id="B-EV-06",
        ),
        "SIG-4601": RiskSignal(
            id="SIG-4601", kind="maintenance",
            at=iso(ANCHOR - timedelta(days=12)), line_id="line-6", parameter="Post-seal window",
            value=None, baseline=None, z=None, severity="warning",
            detail="Post-maintenance watch is still open: hydrogen has not returned to the 1.18 ppm baseline.",
            evidence_id="EV-07",
        ),
    }

    checks = {
        "hydrogen": [
            SuggestedCheck(id="CH-1", label="Pull the melt hydrogen sample now", why="Hydrogen crossed 1.4 ppm and is still above baseline."),
            SuggestedCheck(id="CH-2", label="X-ray the first three castings of the next pour", why="The porosity signature is subsurface; visual inspection will miss it.", owner="Quality technician"),
            SuggestedCheck(id="CH-3", label="Verify the furnace door seal after the repair", why="A post-repair gas check was not recorded.", owner="Maintenance"),
        ],
        "moisture": [
            SuggestedCheck(id="CH-4", label="Regenerate dryer 3 and verify dew point", why="Regeneration is overdue by 38 h."),
            SuggestedCheck(id="CH-5", label="Run a moisture coupon on lot PL-8840", why="Incoming moisture is above the 0.12 % window.", owner="Quality technician"),
            SuggestedCheck(id="CH-6", label="Inspect the next 20 parts at rib 4", why="Short shot appears at the last rib.", owner="Operator"),
        ],
        "laser": [
            SuggestedCheck(id="CH-7", label="Recalibrate the welder 7 power monitor", why="Calibration is 41 days overdue and power is down 10 %."),
            SuggestedCheck(id="CH-8", label="Weld a verification coupon before production", why="A coupon proves the energy at the joint, not just the setpoint."),
        ],
        "reflow": [
            SuggestedCheck(id="CH-9", label="Re-validate the zone 3 profile", why="The heater check changed the thermal response."),
            SuggestedCheck(id="CH-10", label="X-ray the first five boards", why="Voiding is above the 25 % limit and visual inspection cannot see it.", owner="Quality technician"),
        ],
        "seal": [
            SuggestedCheck(id="CH-11", label="Take a hydrogen sample after the seal replacement", why="The post-repair validation step is missing."),
        ],
    }

    recs = {
        "REC-2201": Recommendation(
            id="REC-2201", watch_id="W-1042", kind="hold_batch", title="Hold the remainder of batch B-2291",
            detail="Twelve castings from the batch are in the plant or in transit. Hold pending hydrogen re-test.",
            impact=ImpactEstimate(parts_at_risk=12, scrap_avoided_eur=18400, engineer_hours=6, cost_eur=2400, note="Estimate only; based on 12 parts and the current scrap value."),
            status="executed", approved_by="M. Weber", approved_at=iso(ANCHOR - timedelta(hours=4, minutes=30)),
            executed_at=iso(ANCHOR - timedelta(hours=4)), pattern_id="P-H2", reason="Contain before the next pour.",
        ),
        "REC-2202": Recommendation(
            id="REC-2202", watch_id="W-1042", kind="extra_sampling", title="X-ray the first three castings of every pour",
            detail="Add x-ray sampling at the root fillet for 30 days; the defect is subsurface.",
            impact=ImpactEstimate(parts_at_risk=0, scrap_avoided_eur=9200, engineer_hours=3, cost_eur=1800, note="Estimate only."),
            status="approved", approved_by="M. Weber", approved_at=iso(ANCHOR - timedelta(hours=3, minutes=50)), pattern_id="P-H2",
        ),
        "REC-2203": Recommendation(
            id="REC-2203", watch_id="W-1043", kind="check_dryer", title="Regenerate dryer 3 and verify dew point",
            detail="Stop the press for the regeneration and run a moisture coupon on the current lot.",
            impact=ImpactEstimate(parts_at_risk=40, scrap_avoided_eur=6400, engineer_hours=2, cost_eur=400, note="Estimate only."),
            status="executed", approved_by="M. Weber", approved_at=iso(ANCHOR - timedelta(hours=1, minutes=20)),
            executed_at=iso(ANCHOR - timedelta(hours=1)), pattern_id="P-MOIST",
        ),
        "REC-2204": Recommendation(
            id="REC-2204", watch_id="W-1043", kind="hold_batch", title="Hold lot PL-8840 pending a moisture coupon",
            detail="Forty moulded parts and the remaining resin are at risk; hold until the coupon passes.",
            impact=ImpactEstimate(parts_at_risk=40, scrap_avoided_eur=5200, engineer_hours=1, cost_eur=600),
            status="executed", approved_by="M. Weber", approved_at=iso(ANCHOR - timedelta(hours=1, minutes=30)),
            executed_at=iso(ANCHOR - timedelta(hours=1, minutes=5)), pattern_id="P-MOIST",
        ),
        "REC-2205": Recommendation(
            id="REC-2205", watch_id="W-1044", kind="check_calibration", title="Recalibrate welder 7 and weld a coupon",
            detail="Calibration is overdue. Recalibrate, weld a coupon, and hold the last four hours of cells.",
            impact=ImpactEstimate(parts_at_risk=24, scrap_avoided_eur=11200, engineer_hours=4, cost_eur=900),
            status="proposed", pattern_id="P-LASER",
        ),
        "REC-2206": Recommendation(
            id="REC-2206", watch_id="W-1045", kind="first_off", title="Hold first-off and X-ray five boards",
            detail="Zone 3 changed after the heater check; do not release the first pallet on a visual check.",
            impact=ImpactEstimate(parts_at_risk=18, scrap_avoided_eur=3100, engineer_hours=2, cost_eur=350),
            status="proposed", pattern_id="P-REFLOW",
        ),
        "REC-2207": Recommendation(
            id="REC-2207", watch_id="W-1045", kind="verify_parameter", title="Re-validate the zone 3 profile",
            detail="Run a profiled coupon and compare it to the golden reflow fingerprint.",
            impact=ImpactEstimate(parts_at_risk=0, scrap_avoided_eur=2100, engineer_hours=1.5, cost_eur=120),
            status="approved", approved_by="T. Keller", approved_at=iso(ANCHOR + timedelta(minutes=10)), pattern_id="P-REFLOW",
        ),
        "REC-2208": Recommendation(
            id="REC-2208", watch_id="W-1046", kind="verify_parameter", title="Confirm hydrogen returned to baseline",
            detail="The post-seal watch stays open until three consecutive pours are below 1.18 ppm.",
            impact=ImpactEstimate(parts_at_risk=0, scrap_avoided_eur=0, engineer_hours=1, cost_eur=0),
            status="proposed", pattern_id="P-SEAL",
        ),
    }

    watches = [
        WatchCase(
            id="W-1042", plant_id="plant-de", line_id="line-6",
            title="Hydrogen drift after furnace seal repair",
            summary="Melt hydrogen has been above baseline for five hours, two pours after the door-seal replacement. Batch B-2291 is already in the plant. The pattern is the same one that preceded cases RC-0398 and RC-0361.",
            status="converted", severity="critical", risk_score=0.94, confidence=88,
            opened_at=iso(ANCHOR - timedelta(hours=5, minutes=40)), updated_at=iso(ANCHOR - timedelta(hours=3)),
            owner="M. Weber", sla_due=iso(ANCHOR - timedelta(hours=5, minutes=25)), group_key="line-6:hydrogen",
            pattern_id="P-H2", pattern_name="Hydrogen-to-porosity signature",
            signal_count=4, signals=[signals["SIG-4101"], signals["SIG-4102"], signals["SIG-4103"], signals["SIG-4104"]],
            evidence_ids=["EV-04", "EV-06", "EV-07", "EV-11"],
            suggested_checks=checks["hydrogen"], recommendation_ids=["REC-2201", "REC-2202"],
            linked_case_id="RC-0417", triage_note="Triage confirmed 5 h before the defect. Containment approved the same shift.",
            outcome="converted", outcome_reason="The risk converted to RC-0417; the containment held the rest of the batch.", useful=True,
            outcome_at=iso(ANCHOR - timedelta(hours=3)), outcome_actor="M. Weber",
        ),
        WatchCase(
            id="W-1043", plant_id="plant-de", line_id="line-2",
            title="Dryer 3 overdue; moisture climbing",
            summary="Resin moisture crossed 0.12 % after dryer 3 missed regeneration by 38 hours. The wet-resin pattern precedes a short shot at rib 4. Lot PL-8840 is still in the dryer and 40 parts are already moulded.",
            status="converted", severity="high", risk_score=0.88, confidence=84,
            opened_at=iso(ANCHOR + timedelta(minutes=8) - timedelta(hours=3, minutes=50)),
            updated_at=iso(ANCHOR + timedelta(minutes=8) - timedelta(hours=1)),
            owner="P. Nair", sla_due=iso(ANCHOR + timedelta(minutes=8) - timedelta(hours=3, minutes=35)),
            group_key="line-2:moisture", pattern_id="P-MOIST", pattern_name="Wet-resin short-shot signature",
            signal_count=3, signals=[signals["SIG-4201"], signals["SIG-4202"], signals["SIG-4203"]],
            evidence_ids=["H-EV-02", "H-EV-04", "H-EV-05"], suggested_checks=checks["moisture"],
            recommendation_ids=["REC-2203", "REC-2204"], linked_case_id="RC-0431",
            triage_note="Containment executed; the short shot still occurred but was contained to one shot.",
            outcome="converted", outcome_reason="Converted to RC-0431; 40 parts held and released after coupon.", useful=True,
            outcome_at=iso(ANCHOR + timedelta(minutes=30)), outcome_actor="P. Nair",
        ),
        WatchCase(
            id="W-1044", plant_id="plant-de", line_id="line-4",
            title="Laser power loss; calibration overdue",
            summary="CUSUM shows a sustained 10 % drop in laser power. The power monitor calibration is 41 days overdue. A new foil lot is also in the first 40 welds. No defect yet.",
            status="triage", severity="high", risk_score=0.81, confidence=79,
            opened_at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=50)), updated_at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=10)),
            owner="S. Ito", sla_due=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=35)), group_key="line-4:laser-power",
            pattern_id="P-LASER", pattern_name="Laser-power drift signature", signal_count=2,
            signals=[signals["SIG-4301"], signals["SIG-4302"]], evidence_ids=["B-EV-02", "B-EV-03"],
            suggested_checks=checks["laser"], recommendation_ids=["REC-2205"], triage_note="Waiting for the welder technician; coupon is queued.",
        ),
        WatchCase(
            id="W-1045", plant_id="plant-de", line_id="line-3",
            title="Zone 3 step change after heater check",
            summary="A heater-element check changed zone 3 by −11 °C. First-off X-ray is at 31 % voiding, just above the 25 % limit. The profile has not been re-validated.",
            status="investigating", severity="high", risk_score=0.76, confidence=74,
            opened_at=iso(ANCHOR + timedelta(minutes=23) - timedelta(minutes=40)), updated_at=iso(ANCHOR + timedelta(minutes=23) - timedelta(minutes=8)),
            owner="T. Keller", sla_due=iso(ANCHOR + timedelta(minutes=23) - timedelta(minutes=25)), group_key="line-3:reflow-zone3",
            pattern_id="P-REFLOW", pattern_name="Reflow zone-3 drift signature", signal_count=2,
            signals=[signals["SIG-4401"], signals["SIG-4402"]], evidence_ids=["E-EV-01", "E-EV-02"],
            suggested_checks=checks["reflow"], recommendation_ids=["REC-2206", "REC-2207"],
            triage_note="First-off held; the technician is running a profiled coupon.",
        ),
        WatchCase(
            id="W-1046", plant_id="plant-de", line_id="line-6",
            title="Post-maintenance watch: door seal",
            summary="The door-seal replacement has a 30-day post-repair window. Hydrogen is falling but has not returned to the 1.18 ppm baseline for three consecutive pours.",
            status="watching", severity="warning", risk_score=0.47, confidence=62,
            opened_at=iso(ANCHOR - timedelta(days=11, hours=20)), updated_at=iso(ANCHOR - timedelta(hours=3, minutes=10)),
            owner="M. Weber", sla_due=iso(ANCHOR + timedelta(hours=1)), group_key="line-6:seal-followup",
            pattern_id="P-SEAL", pattern_name="Post-maintenance seal watch", signal_count=1,
            signals=[signals["SIG-4601"]], evidence_ids=["EV-07"], suggested_checks=checks["seal"],
            recommendation_ids=["REC-2208"], triage_note="Monitoring; no new containment needed.",
        ),
        WatchCase(
            id="W-1047", plant_id="plant-de", line_id="line-2",
            title="Camera 2 offline for 26 minutes",
            summary="The inspection camera stopped sending frames. The line kept running. Coverage for the window is unknown, so no quality risk can be scored for 26 minutes.",
            status="dismissed", severity="warning", risk_score=0.35, confidence=100,
            opened_at=iso(ANCHOR - timedelta(hours=2, minutes=40)), updated_at=iso(ANCHOR - timedelta(hours=2, minutes=10)),
            owner="P. Nair", sla_due=iso(ANCHOR - timedelta(hours=2, minutes=25)), group_key="line-2:camera-offline",
            pattern_id="P-DQ", pattern_name="Data-quality blind spot", signal_count=1,
            signals=[signals["SIG-4501"]], evidence_ids=[], suggested_checks=[
                SuggestedCheck(id="CH-12", label="Restore CAM-02 and backfill the shift", why="Coverage is below the floor; a risk score would be misleading.", done=True),
            ], recommendation_ids=[], triage_note="Camera restored. Operational issue, not a quality risk; counted separately from false alarms.",
            outcome="operational", outcome_reason="Data-quality watch, not a quality false alarm.", useful=False,
            outcome_at=iso(ANCHOR - timedelta(hours=2, minutes=10)), outcome_actor="P. Nair",
        ),
        WatchCase(
            id="W-1048", plant_id="plant-de", line_id="line-4",
            title="New foil lot F-771",
            summary="A supplier process change and a new foil lot opened a setup watch for the first 40 welds. No parameter deviation after 18 welds.",
            status="watching", severity="info", risk_score=0.22, confidence=55,
            opened_at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=55)), updated_at=iso(ANCHOR + timedelta(minutes=16) - timedelta(minutes=20)),
            owner="S. Ito", sla_due=iso(ANCHOR + timedelta(hours=2)), group_key="line-4:foil-setup",
            pattern_id="P-LASER", pattern_name="Laser-power drift signature", signal_count=1,
            signals=[signals["SIG-4502"]], evidence_ids=["B-EV-06"], suggested_checks=[
                SuggestedCheck(id="CH-13", label="Inspect the first 40 welds", why="New lot and supplier process change."),
            ], recommendation_ids=[], triage_note="Setup watch; no action unless a parameter moves.",
        ),
        WatchCase(
            id="W-1038", plant_id="plant-de", line_id="line-6",
            title="Hydrogen drift before RC-0398",
            summary="The same hydrogen pattern opened a watch four days before RC-0398. The team held the batch and x-rayed the first castings.",
            status="converted", severity="high", risk_score=0.86, confidence=83,
            opened_at=iso(ANCHOR - timedelta(days=51)), updated_at=iso(ANCHOR - timedelta(days=50)),
            owner="M. Weber", sla_due=iso(ANCHOR - timedelta(days=51) + timedelta(minutes=15)), group_key="line-6:hydrogen", pattern_id="P-H2",
            pattern_name="Hydrogen-to-porosity signature", signal_count=2,
            signals=[signals["SIG-4101"], signals["SIG-4102"]], evidence_ids=["EV-04", "EV-07"],
            suggested_checks=checks["hydrogen"], recommendation_ids=[], linked_case_id="RC-0398",
            triage_note="Contained; the defect still occurred but the batch was already held.",
            outcome="converted", outcome_reason="Converted to RC-0398; batch contained.", useful=True,
            outcome_at=iso(ANCHOR - timedelta(days=50)), outcome_actor="M. Weber",
        ),
        WatchCase(
            id="W-1039", plant_id="plant-de", line_id="line-2",
            title="Wet resin before RC-0402",
            summary="Dryer regeneration was overdue and moisture was above the window. The watch converted to RC-0402 the next shift.",
            status="converted", severity="high", risk_score=0.84, confidence=81,
            opened_at=iso(ANCHOR - timedelta(days=41)), updated_at=iso(ANCHOR - timedelta(days=40)),
            owner="P. Nair", sla_due=iso(ANCHOR - timedelta(days=41) + timedelta(minutes=15)), group_key="line-2:moisture", pattern_id="P-MOIST",
            pattern_name="Wet-resin short-shot signature", signal_count=2,
            signals=[signals["SIG-4201"], signals["SIG-4202"]], evidence_ids=["H-EV-02", "H-EV-05"],
            suggested_checks=checks["moisture"], recommendation_ids=[], linked_case_id="RC-0402",
            triage_note="Dryer restored; one shot contained.", outcome="converted",
            outcome_reason="Converted to RC-0402; useful.", useful=True,
            outcome_at=iso(ANCHOR - timedelta(days=40)), outcome_actor="P. Nair",
        ),
        WatchCase(
            id="W-1040", plant_id="plant-de", line_id="line-4",
            title="Laser drift contained before a defect",
            summary="Power drift was caught on a coupon, the welder was recalibrated and no cell was scrapped. No defect case was needed.",
            status="converted", severity="high", risk_score=0.78, confidence=77,
            opened_at=iso(ANCHOR - timedelta(days=17)), updated_at=iso(ANCHOR - timedelta(days=16)),
            owner="S. Ito", sla_due=iso(ANCHOR - timedelta(days=17) + timedelta(minutes=15)), group_key="line-4:laser-power", pattern_id="P-LASER",
            pattern_name="Laser-power drift signature", signal_count=2,
            signals=[signals["SIG-4301"], signals["SIG-4302"]], evidence_ids=["B-EV-02", "B-EV-03"],
            suggested_checks=checks["laser"], recommendation_ids=[], triage_note="Recalibrated on the coupon; no parts at risk.",
            outcome="true_risk", outcome_reason="True risk; containment prevented a defect case.", useful=True,
            outcome_at=iso(ANCHOR - timedelta(days=16)), outcome_actor="S. Ito",
        ),
        WatchCase(
            id="W-1049", plant_id="plant-de", line_id="line-6",
            title="Seal settling after replacement",
            summary="Hydrogen was slightly high two days after the seal replacement. The samples returned to baseline without intervention.",
            status="dismissed", severity="warning", risk_score=0.44, confidence=58,
            opened_at=iso(ANCHOR - timedelta(days=10)), updated_at=iso(ANCHOR - timedelta(days=9)),
            owner="M. Weber", sla_due=iso(ANCHOR - timedelta(days=10) + timedelta(minutes=15)), group_key="line-6:seal-settling", pattern_id="P-SEAL",
            pattern_name="Post-maintenance seal watch", signal_count=1, signals=[signals["SIG-4601"]], evidence_ids=["EV-07"],
            suggested_checks=checks["seal"], recommendation_ids=[], triage_note="Normal post-repair settling; dismissed with reason.",
            outcome="false_alarm", outcome_reason="Settling after a new seal; three later pours were at baseline.", useful=False,
            outcome_at=iso(ANCHOR - timedelta(days=9)), outcome_actor="M. Weber",
        ),
        WatchCase(
            id="W-1050", plant_id="plant-de", line_id="line-2",
            title="Moisture probe spike",
            summary="A single moisture spike was traced to a probe cleaning, not to the resin. No process change was made.",
            status="dismissed", severity="warning", risk_score=0.38, confidence=54,
            opened_at=iso(ANCHOR - timedelta(days=24)), updated_at=iso(ANCHOR - timedelta(days=24)),
            owner="P. Nair", sla_due=iso(ANCHOR - timedelta(days=24) + timedelta(minutes=15)), group_key="line-2:moisture-probe", pattern_id="P-MOIST",
            pattern_name="Wet-resin short-shot signature", signal_count=1, signals=[signals["SIG-4201"]], evidence_ids=["H-EV-02"],
            suggested_checks=[], recommendation_ids=[], triage_note="Probe maintenance; dismissed.",
            outcome="false_alarm", outcome_reason="Instrument artefact, not resin moisture.", useful=False,
            outcome_at=iso(ANCHOR - timedelta(days=24)), outcome_actor="P. Nair",
        ),
        WatchCase(
            id="W-1051", plant_id="plant-de", line_id="line-3",
            title="Thermocouple step change",
            summary="Zone 3 changed when the thermocouple was swapped. The profile was already re-validated; no voiding followed.",
            status="dismissed", severity="warning", risk_score=0.36, confidence=52,
            opened_at=iso(ANCHOR - timedelta(days=31)), updated_at=iso(ANCHOR - timedelta(days=30)),
            owner="T. Keller", sla_due=iso(ANCHOR - timedelta(days=31) + timedelta(minutes=15)), group_key="line-3:thermocouple", pattern_id="P-REFLOW",
            pattern_name="Reflow zone-3 drift signature", signal_count=1, signals=[signals["SIG-4401"]], evidence_ids=["E-EV-02"],
            suggested_checks=[], recommendation_ids=[], triage_note="Sensor replacement; dismissed.",
            outcome="false_alarm", outcome_reason="Thermocouple replacement; profile unchanged.", useful=False,
            outcome_at=iso(ANCHOR - timedelta(days=30)), outcome_actor="T. Keller",
        ),
    ]

    patterns = [
        RiskPattern(
            id="P-H2", version="v1.4", name="Hydrogen-to-porosity signature", cause_family="Gas porosity",
            description="Hydrogen above 1.4 ppm, a recent furnace seal intervention and a batch hydrogen exception. Historically precedes a subsurface porosity cluster and a quench crack.",
            trigger="EWMA hydrogen > 1.4 ppm or batch hydrogen > limit + maintenance event in the last 30 days",
            historical_precision=0.71, checks=[c.label for c in checks["hydrogen"]],
            recommendation_kinds=["hold_batch", "extra_sampling"], status="active", owner="Quality engineering",
            last_validated=iso(ANCHOR - timedelta(days=21)),
            card={"inputs": ["melt hydrogen", "batch certificate", "furnace maintenance"], "limits": ["1.4 ppm"], "failure_modes": ["false alarm when the seal is new and the sample is contaminated"]},
        ),
        RiskPattern(
            id="P-MOIST", version="v1.2", name="Wet-resin short-shot signature", cause_family="Material moisture",
            description="Resin moisture above 0.12 %, missed dryer regeneration and a batch open longer than the drying window.",
            trigger="moisture EWMA > 0.12 % or dryer overdue > 24 h",
            historical_precision=0.68, checks=[c.label for c in checks["moisture"]],
            recommendation_kinds=["check_dryer", "hold_batch", "extra_sampling"], status="active",
            last_validated=iso(ANCHOR - timedelta(days=34)),
            card={"inputs": ["resin moisture", "dryer log", "batch age"], "limits": ["0.12 %"], "failure_modes": ["sensor drift in the moisture probe"]},
        ),
        RiskPattern(
            id="P-LASER", version="v1.4", name="Laser-power drift signature", cause_family="Laser power drift",
            description="A sustained CUSUM drop in laser power plus an overdue power-monitor calibration.",
            trigger="CUSUM power drop > 5 % or calibration overdue > 30 days",
            historical_precision=0.74, checks=[c.label for c in checks["laser"]],
            recommendation_kinds=["check_calibration", "extra_sampling"], status="active",
            last_validated=iso(ANCHOR - timedelta(days=12)),
            card={"inputs": ["laser power", "calibration age", "weld speed"], "limits": ["1.75 W"], "failure_modes": ["a genuine process change after a recipe update"]},
        ),
        RiskPattern(
            id="P-REFLOW", version="v1.3", name="Reflow zone-3 drift signature", cause_family="Reflow profile",
            description="A step change in zone 3 after maintenance, with first-off voiding above the limit.",
            trigger="zone 3 change > 8 °C or first-off void > 25 %",
            historical_precision=0.66, checks=[c.label for c in checks["reflow"]],
            recommendation_kinds=["first_off", "verify_parameter"], status="active",
            last_validated=iso(ANCHOR - timedelta(days=18)),
            card={"inputs": ["zone 3", "first-off X-ray", "maintenance log"], "limits": ["217 °C"], "failure_modes": ["oven thermocouple drift"]},
        ),
        RiskPattern(
            id="P-SEAL", version="v1.0", name="Post-maintenance seal watch", cause_family="Maintenance effect",
            description="A 30-day watch after a furnace seal or gas-path intervention; requires three consecutive pours at baseline.",
            trigger="seal replacement or gas-path maintenance",
            historical_precision=0.61, checks=[c.label for c in checks["seal"]],
            recommendation_kinds=["verify_parameter"], status="shadow",
            last_validated=iso(ANCHOR - timedelta(days=7)),
            card={"inputs": ["maintenance event", "hydrogen"], "limits": ["1.18 ppm"], "failure_modes": ["normal post-repair settling"]},
        ),
        RiskPattern(
            id="P-DQ", version="v1.0", name="Data-quality blind spot", cause_family="Data quality",
            description="A camera, sensor or batch feed is stale. No quality risk is scored while coverage is below the floor.",
            trigger="coverage < 95 % or source stale > 5 min",
            historical_precision=1.0, checks=["Restore the source and backfill the window"],
            recommendation_kinds=[], status="active", last_validated=iso(ANCHOR - timedelta(days=3)),
            card={"inputs": ["source heartbeat", "last sample", "coverage"], "limits": ["95 %"], "failure_modes": ["network partition"]},
        ),
    ]

    scan_runs = [
        ScanRun(id=f"SCAN-{i}", at=iso(ANCHOR - timedelta(minutes=5 * (6 - i))), mode="live" if i > 3 else "shadow",
                lines_scanned=4, signals=[3, 2, 4, 1, 3, 2][i], watches_opened=[1, 0, 0, 1, 0, 0][i],
                suppressed=[2, 1, 3, 0, 1, 0][i], duration_ms=[820, 760, 910, 690, 800, 740][i],
                status="ok", lag_seconds=[3, 4, 2, 5, 3, 4][i],
                note="On-site scheduler. No outbound network." if i == 5 else "")
        for i in range(6)
    ]

    briefs = [
        ShiftBrief(
            id="BRIEF-1042", at=iso(ANCHOR - timedelta(hours=6)), shift="B", line_ids=["line-6", "line-2", "line-4", "line-3"],
            title="Shift B risk brief — 22 Oct",
            summary="One critical watch is active on Line 6: hydrogen is above baseline after the furnace seal repair. Line 2 has an overdue dryer; Line 4 has a laser power drift; Line 3 has a zone 3 step change. Containment has been approved for Line 6 and Line 2.",
            top_risks=[
                {"watch_id": "W-1042", "title": "Hydrogen drift after furnace seal repair", "severity": "critical", "action": "Hold B-2291; x-ray first three castings"},
                {"watch_id": "W-1043", "title": "Dryer 3 overdue; moisture climbing", "severity": "high", "action": "Regenerate dryer; hold PL-8840"},
                {"watch_id": "W-1044", "title": "Laser power loss; calibration overdue", "severity": "high", "action": "Recalibrate and weld a coupon"},
            ],
            open_cases=[
                {"case_id": "RC-0417", "title": "Bracket fracture", "status": "awaiting_review"},
                {"case_id": "RC-0431", "title": "Short shot at rib 4", "status": "investigating"},
            ],
            actions_due=[
                {"action_id": "CA-118", "title": "Quarantine B-2291", "owner": "M. Weber", "due": iso(ANCHOR + timedelta(days=2))},
                {"action_id": "CA-116", "title": "Regenerate dryer 3", "owner": "K. Meier", "due": iso(ANCHOR + timedelta(days=1))},
            ],
            fixed_not_verified=[
                {"case_id": "RC-0416", "title": "Cooling time restored", "note": "Parameter returned; defect rate still under observation"},
            ],
            coverage_note="Coverage 97% on Line 6, 94% on Line 2, 98% on Line 4, 92% on Line 3. Camera 2 was offline for 26 minutes; no quality risk scored for that window.",
        ),
        ShiftBrief(
            id="BRIEF-1043", at=iso(ANCHOR - timedelta(hours=2)), shift="A", line_ids=["line-2", "line-3"],
            title="Shift A risk brief — 22 Oct",
            summary="Line 2 moisture is contained after the dryer regeneration. Line 3 first-off is held pending a profile coupon. Watch precision this week is 62%; no alert storm observed.",
            top_risks=[
                {"watch_id": "W-1045", "title": "Zone 3 step change after heater check", "severity": "high", "action": "Hold first-off; X-ray five boards"},
            ],
            open_cases=[{"case_id": "RC-0452", "title": "Solder void", "status": "investigating"}],
            actions_due=[{"action_id": "CA-114", "title": "Recalibrate welder 7", "owner": "S. Ito", "due": iso(ANCHOR + timedelta(days=3))}],
            fixed_not_verified=[],
            coverage_note="Line 3 coverage 92%; the first-off X-ray is the only complete gate for the current window.",
        ),
    ]

    coverage = [
        Coverage(line_id="line-6", expected_sources=18, fresh_sources=17, pct=0.97, stale=["CAM-06 last frame 4 min"], status="ok", last_scan=iso(ANCHOR - timedelta(minutes=5))),
        Coverage(line_id="line-2", expected_sources=16, fresh_sources=15, pct=0.94, stale=["CAM-02 restored 2 h ago", "dryer dew point 11 min"], status="degraded", last_scan=iso(ANCHOR - timedelta(minutes=5))),
        Coverage(line_id="line-4", expected_sources=20, fresh_sources=20, pct=1.0, stale=[], status="ok", last_scan=iso(ANCHOR - timedelta(minutes=5))),
        Coverage(line_id="line-3", expected_sources=14, fresh_sources=13, pct=0.92, stale=["zone 3 thermocouple 9 min"], status="degraded", last_scan=iso(ANCHOR - timedelta(minutes=5))),
    ]

    exposures = [
        Exposure(
            id="EXP-41", watch_id="W-1042", batch_id="B-2291", generated_at=iso(ANCHOR - timedelta(hours=4)),
            customers=3, estimated_eur=18400, status="open",
            parts=[
                ExposurePart(serial="BRK-0417-B", part="Turbine bracket", line_id="line-6", shift="B", customer="Volt Motors", status="in_plant", containment="hold"),
                ExposurePart(serial="BRK-0418-A", part="Turbine bracket", line_id="line-6", shift="B", customer="Volt Motors", status="in_plant", containment="hold"),
                ExposurePart(serial="BRK-0419-C", part="Turbine bracket", line_id="line-6", shift="B", customer="Nord Drive", status="in_transit", containment="hold"),
                ExposurePart(serial="BRK-0420-A", part="Turbine bracket", line_id="line-6", shift="A", customer="Nord Drive", status="at_customer", containment="inspect"),
                ExposurePart(serial="BRK-0421-B", part="Turbine bracket", line_id="line-6", shift="A", customer="Asterics", status="fitted", containment="inspect"),
            ],
            note="Trace based on batch MES records. Customer names are fictional in the demo.",
        ),
        Exposure(
            id="EXP-42", watch_id="W-1043", batch_id="PL-8840", generated_at=iso(ANCHOR - timedelta(hours=2, minutes=30)),
            customers=2, estimated_eur=5200, status="contained",
            parts=[
                ExposurePart(serial="HSG-0431-A", part="Housing", line_id="line-2", shift="A", customer="Volt Motors", status="in_plant", containment="hold"),
                ExposurePart(serial="HSG-0432-A", part="Housing", line_id="line-2", shift="A", customer="Volt Motors", status="in_plant", containment="hold"),
                ExposurePart(serial="HSG-0433-B", part="Housing", line_id="line-2", shift="A", customer="Nord Drive", status="in_transit", containment="hold"),
            ],
            note="Forty moulded parts held; three shown for the demo.",
        ),
    ]

    followups = [
        FollowUp(id="FU-101", case_id="RC-0416", action_id="CA-115", title="Cooling time restoration", pattern_id="P-MOIST", window_start=iso(ANCHOR - timedelta(days=7)), window_end=iso(ANCHOR - timedelta(days=1)), status="verified", parameter_returned=True, defect_rate_delta=-0.42, note="Cooling time back to 22.5 s; defect rate fell from 1.9% to 1.1%."),
        FollowUp(id="FU-102", case_id="RC-0417", action_id="CA-117", title="Furnace door seal follow-up", pattern_id="P-SEAL", window_start=iso(ANCHOR - timedelta(days=12)), window_end=iso(ANCHOR + timedelta(days=18)), status="monitoring", parameter_returned=False, defect_rate_delta=0.0, recurrence_watch_id="W-1046", note="Hydrogen is falling but has not held three consecutive pours at baseline."),
        FollowUp(id="FU-103", case_id="RC-0431", action_id="CA-116", title="Dryer 3 regeneration follow-up", pattern_id="P-MOIST", window_start=iso(ANCHOR - timedelta(hours=1)), window_end=iso(ANCHOR + timedelta(days=7)), status="monitoring", parameter_returned=False, note="Moisture coupon is queued; no release until it passes."),
    ]

    notifications = [
        Notification(id="NT-9001", at=iso(ANCHOR - timedelta(hours=5, minutes=38)), kind="watch", severity="critical", title="Critical watch: hydrogen drift on Line 6", detail="W-1042 opened; 4 signals grouped. Triage due within 15 minutes.", watch_id="W-1042", role="quality_manager", dedup_key="line-6:hydrogen:2026-10-22"),
        Notification(id="NT-9002", at=iso(ANCHOR - timedelta(hours=4, minutes=31)), kind="recommendation", severity="high", title="Containment approved: hold B-2291", detail="M. Weber approved REC-2201. Twelve parts are being held.", watch_id="W-1042", role="quality_manager", read=True, dedup_key="REC-2201"),
        Notification(id="NT-9003", at=iso(ANCHOR - timedelta(hours=1, minutes=25)), kind="recommendation", severity="high", title="Dryer 3 regeneration approved", detail="P. Nair approved REC-2203 for W-1043.", watch_id="W-1043", role="engineer", read=True, dedup_key="REC-2203"),
        Notification(id="NT-9004", at=iso(ANCHOR - timedelta(minutes=14)), kind="watch", severity="high", title="Watch waiting: laser power drift", detail="W-1044 is in triage; calibration is overdue. Triage SLA in 1 minute.", watch_id="W-1044", role="engineer", dedup_key="line-4:laser-power:2026-10-22"),
        Notification(id="NT-9005", at=iso(ANCHOR - timedelta(hours=1)), kind="data_quality", severity="warning", title="Coverage below floor on Line 3", detail="Zone 3 thermocouple stale for 9 minutes. No risk score will be issued until it is fresh.", role="quality_manager", dedup_key="line-3:coverage"),
        Notification(id="NT-9006", at=iso(ANCHOR - timedelta(days=1)), kind="followup", severity="info", title="Fixed but not verified: door seal", detail="FU-102 is still monitoring; hydrogen has not held baseline for three pours.", watch_id="W-1046", role="quality_manager", read=True, dedup_key="FU-102"),
    ]

    metrics = ProactiveMetrics(
        watch_precision=0.625, watch_recall=0.75, alerts_per_line_shift=1.6, median_triage_min=11.0,
        containment_conversion=0.58, defects_prevented_month=3, escaped_defects=0, coverage_pct=0.9575,
        reconstruction_min=3.5, alert_volume_growth=0.8, cost_per_useful_alert_eur=41.0,
        useful_watches=5, total_watches=8,
        weekly=[
            {"week": "W36", "precision": 0.42, "alerts": 3.4, "triage": 24, "conversion": 0.31, "useful": 3, "total": 7},
            {"week": "W37", "precision": 0.48, "alerts": 3.0, "triage": 21, "conversion": 0.36, "useful": 4, "total": 8},
            {"week": "W38", "precision": 0.51, "alerts": 2.7, "triage": 18, "conversion": 0.40, "useful": 5, "total": 9},
            {"week": "W39", "precision": 0.55, "alerts": 2.4, "triage": 16, "conversion": 0.44, "useful": 5, "total": 9},
            {"week": "W40", "precision": 0.58, "alerts": 2.1, "triage": 14, "conversion": 0.49, "useful": 6, "total": 10},
            {"week": "W41", "precision": 0.60, "alerts": 1.9, "triage": 13, "conversion": 0.53, "useful": 6, "total": 10},
            {"week": "W42", "precision": 0.61, "alerts": 1.7, "triage": 12, "conversion": 0.56, "useful": 6, "total": 10},
            {"week": "W43", "precision": 0.625, "alerts": 1.6, "triage": 11, "conversion": 0.58, "useful": 5, "total": 8},
        ],
        channels=[
            {"name": "In-app", "delivered": 42, "opened": 39, "note": "Default for the quality team"},
            {"name": "Teams", "delivered": 18, "opened": 17, "note": "On-call channel"},
            {"name": "Email digest", "delivered": 8, "opened": 6, "note": "Shift boundary"},
        ],
    )

    model_cards = [
        ModelCard(id="MC-H2", name="Hydrogen-to-porosity pattern", version="v1.4", kind="threshold", inputs=["melt hydrogen", "batch certificate", "furnace seal maintenance"], limits=["1.4 ppm", "30-day maintenance window"], failure_modes=["new seal settling", "sample contamination"], owner="Quality engineering", last_validated=iso(ANCHOR - timedelta(days=21)), status="champion"),
        ModelCard(id="MC-MOIST", name="Wet-resin pattern", version="v1.2", kind="ewma", inputs=["resin moisture", "dryer log", "batch age"], limits=["0.12 %"], failure_modes=["probe drift", "humid ambient"], owner="Process engineering", last_validated=iso(ANCHOR - timedelta(days=34)), status="champion"),
        ModelCard(id="MC-LASER", name="Laser-power CUSUM", version="v1.4", kind="spc", inputs=["laser power", "calibration age", "weld speed"], limits=["1.75 W"], failure_modes=["recipe change", "mirror contamination"], owner="Welding engineering", last_validated=iso(ANCHOR - timedelta(days=12)), status="champion"),
        ModelCard(id="MC-REFLOW", name="Zone-3 change point", version="v1.3", kind="change_point", inputs=["zone 3", "first-off X-ray", "maintenance"], limits=["8 °C"], failure_modes=["thermocouple drift"], owner="SMT engineering", last_validated=iso(ANCHOR - timedelta(days=18)), status="champion"),
        ModelCard(id="MC-SEAL", name="Post-maintenance seal watch", version="v1.0", kind="threshold", inputs=["seal work order", "hydrogen"], limits=["1.18 ppm"], failure_modes=["normal settling"], owner="Quality engineering", last_validated=iso(ANCHOR - timedelta(days=7)), status="challenger"),
        ModelCard(id="MC-RUL", name="Remaining-useful-life research", version="v0.1", kind="research", inputs=["cycle count", "vibration", "temperature"], limits=["12 months", "30 events"], failure_modes=["censoring bias", "maintenance confound", "no lift over SPC"], owner="Research", last_validated=iso(ANCHOR - timedelta(days=4)), status="research"),
    ]

    research = ResearchGate(
        question="Can the next 200 cycles of the Line 6 furnace door seal be predicted with a validated lift over SPC?",
        status="stopped", decision="Stopped: the shadow model showed no validated lift over SPC on the available history. Prediction is not shipped.",
        data_months=14, events=34, required_events=30, model_lift=0.02, lead_time_hours=8.0,
        false_alarm_rate=0.31, cost_of_errors_eur=41000, updated_at=iso(ANCHOR - timedelta(days=4)),
        note="Synthetic demo data. The point of the gate is that a negative result is a valid result.",
        checks=[
            {"id": "R1", "label": "Define one predictive question with a customer", "done": True, "note": "Furnace door seal, 200-cycle horizon."},
            {"id": "R2", "label": "Data sufficiency: ≥ 12 months and ≥ 30 events", "done": True, "note": "14 months, 34 seal-related events; censoring reviewed."},
            {"id": "R3", "label": "Time-to-failure labelling with censoring", "done": True, "note": "Maintenance removals handled as censored."},
            {"id": "R4", "label": "Baseline survival / gradient boosting vs SPC", "done": True, "note": "SPC baseline AUC 0.79; model 0.81, but calibration is poor."},
            {"id": "R5", "label": "Prospective shadow evaluation", "done": True, "note": "Six weeks shadow; 0.02 lift, 31% false alarms."},
            {"id": "R6", "label": "Lead time, precision, recall and cost of errors", "done": True, "note": "8 h lead, 31% false alarms, €41k annualised cost of errors."},
            {"id": "R7", "label": "Cost-of-error review with quality and finance", "done": True, "note": "No business case at this lift."},
            {"id": "R8", "label": "Product decision: separate, embedded, or stop", "done": True, "note": "Stop. Revisit only with more events and a new maintenance-confound strategy."},
            {"id": "R9", "label": "Stop rule: no validated lift over SPC → do not ship", "done": True, "note": "Applied."},
        ],
    )

    settings = ProactiveSettings(
        schedule=ScheduleSettings(
            enabled=True, stop_switch=False, interval_minutes=15, mode="shadow",
            false_alarm_budget=2.0, max_alerts_per_shift=10, quiet_hours="22:00-06:00",
            digest_mode=False, coverage_floor=0.95, triage_sla_min=15, reconstruction_target_min=5,
            webhook_url="https://hooks.example.invalid/rootcause", notification_roles=["quality_manager", "engineer"],
            champion="v1.4", challenger="v1.5-shadow",
        ),
        thresholds=[
            ThresholdRule(id="TH-1", line_id="line-6", parameter="Melt hydrogen", method="ewma", limit=1.4, direction="above", owner="M. Weber", version="v1.4", notes="Engineering limit; supplier deviation does not raise it."),
            ThresholdRule(id="TH-2", line_id="line-6", parameter="Quench bath temperature", method="change_point", limit=8.0, direction="either", owner="M. Weber", version="v1.4", notes="Step change in °C."),
            ThresholdRule(id="TH-3", line_id="line-2", parameter="Resin moisture", method="ewma", limit=0.12, direction="above", owner="P. Nair", version="v1.2", notes="Drying window limit."),
            ThresholdRule(id="TH-4", line_id="line-2", parameter="Dryer regeneration age", method="maintenance", limit=24.0, direction="above", owner="P. Nair", version="v1.2", notes="Hours since regeneration."),
            ThresholdRule(id="TH-5", line_id="line-4", parameter="Laser power", method="cusum", limit=5.0, direction="below", owner="S. Ito", version="v1.4", notes="Percent drop from setpoint."),
            ThresholdRule(id="TH-6", line_id="line-3", parameter="Reflow zone 3", method="change_point", limit=8.0, direction="either", owner="T. Keller", version="v1.3", notes="°C step change."),
            ThresholdRule(id="TH-7", line_id="line-3", parameter="First-off X-ray void", method="spc", limit=25.0, direction="above", owner="T. Keller", version="v1.3", notes="Percent void under the thermal pad."),
            ThresholdRule(id="TH-8", line_id="all", parameter="Source coverage", method="data_quality", limit=95.0, direction="below", owner="Site admin", version="v1.0", notes="No quality risk score below this floor."),
        ],
        stop_reasons=[],
        contract_note="Recommendations only. No automatic line control, rejection or batch hold. False-alarm budget agreed per line per shift.",
        escalation_sla="Acknowledge within 15 minutes during the shift; next shift otherwise.",
    )

    pattern_versions = {p.id: p.version for p in patterns}
    for w in watches:
        w.pattern_version = pattern_versions.get(w.pattern_id, "")

    return ProactivePack(
        settings=settings, watches=watches, patterns=patterns, recommendations=list(recs.values()),
        scan_runs=scan_runs, briefs=briefs, notifications=notifications, exposures=exposures,
        followups=followups, coverage=coverage, metrics=metrics, model_cards=model_cards, research=research,        health={"status": "ok", "last_scan": iso(ANCHOR - timedelta(minutes=5)), "lag_seconds": 300, "detail": "Scheduler healthy; shadow mode."},
        replay={
            "rows": [
                {"scenario": "bracket", "signals": 4, "expected_risk": True, "opened": True, "line": "line-6"},
                {"scenario": "housing", "signals": 3, "expected_risk": True, "opened": True, "line": "line-2"},
                {"scenario": "battery", "signals": 2, "expected_risk": True, "opened": True, "line": "line-4"},
                {"scenario": "electronics", "signals": 0, "expected_risk": False, "opened": False, "line": "line-3"},
            ],
            "precision": 1.0, "recall": 1.0, "true_positive": 3, "false_positive": 0, "false_negative": 0,
            "note": "Replay on the seeded pack only. A pilot backtests six to twelve months of history before any live alert.",
        },
        tuning=[{"action": "hold", "reason": "Precision 62.5% is above the 60% pilot gate on the recent watch set.", "suggestion": "Keep the champion; evaluate v1.5 in shadow for two more weeks.", "requires_approval": True}],
    )
