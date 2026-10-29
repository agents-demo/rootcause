"""Build the deterministic RootCause demo pack.

Everything in this module is synthetic and seeded. The same pack is served by the API and
exported to ``web/public/demo-pack.json`` so the public site can run with no backend and no
network.
"""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from ..engine.ranking import rank_hypotheses
from ..models import (
    Alert,
    AuditEvent,
    BatchRecord,
    Billing,
    CausalChain,
    ChainNode,
    CompliancePack,
    Connector,
    CorrectiveAction,
    Dashboard,
    DefectCase,
    Evidence,
    Finding,
    HistoricalCase,
    Hypothesis,
    HypothesisFactor,
    Line,
    MaintenanceRecord,
    Pack,
    Plant,
    Report,
    ReportSection,
    Scenario,
    SensorPoint,
    SensorSeries,
    User,
)

TZ = UTC
ANCHOR = datetime(2026, 10, 22, 6, 42, tzinfo=TZ)


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_series(
    sid: str,
    name: str,
    unit: str,
    baseline: float,
    std: float,
    *,
    spec_low: float | None,
    spec_high: float | None,
    anomaly: float,
    seed: int,
    noise: float = 1.0,
    anomaly_from: int = 20,
    anomaly_to: int = 31,
    points: int = 37,
    start_min: int = -180,
    step_min: int = 5,
    decimals: int = 2,
) -> SensorSeries:
    rng = random.Random(seed)
    pts: list[SensorPoint] = []
    for i in range(points):
        t = ANCHOR + timedelta(minutes=start_min + i * step_min)
        shape = 0.0
        if anomaly_from <= i <= anomaly_to:
            # ramps up quickly, holds, then recovers
            span = anomaly_to - anomaly_from
            progress = (i - anomaly_from) / max(1, span)
            shape = math.sin(min(1.0, progress * 1.15) * math.pi * 0.92)
        v = baseline + rng.gauss(0, std * noise) + anomaly * shape
        v = round(v, decimals)
        pts.append(SensorPoint(t=iso(t), v=v))
    window = [p.v for p in pts[anomaly_from : anomaly_to + 1]]
    dev = (sum(window) / len(window) - baseline) / std if window else 0.0
    out = sum(1 for p in pts if (spec_low is not None and p.v < spec_low) or (spec_high is not None and p.v > spec_high))
    return SensorSeries(
        id=sid,
        name=name,
        unit=unit,
        spec_low=spec_low,
        spec_high=spec_high,
        baseline=baseline,
        std=std,
        points=pts,
        deviation_z=round(dev, 2),
        out_of_spec=out,
    )


def ev(
    eid: str,
    kind: str,
    title: str,
    detail: str,
    source: str,
    at: str | None = None,
    strength: float = 0.5,
    **payload: Any,
) -> Evidence:
    return Evidence(
        id=eid,
        kind=kind,  # type: ignore[arg-type]
        title=title,
        detail=detail,
        source=source,
        at=at,
        strength=strength,
        payload=payload,
    )


def hist(
    cid: str,
    days: int,
    defect: str,
    cause: str,
    line: str,
    batch: str,
    similarity: float,
    hours: float,
    notes: str,
) -> HistoricalCase:
    return HistoricalCase(
        id=cid,
        at=iso(ANCHOR - timedelta(days=days)),
        defect=defect,
        cause=cause,
        line=line,
        batch=batch,
        similarity=similarity,
        resolution_hours=hours,
        notes=notes,
    )


def report_for(
    rid: str,
    case_id: str,
    title: str,
    summary: str,
    chain: CausalChain,
    *,
    context: str,
    actions: str,
    limitations: str,
    version: int = 1,
    status: str = "draft",
    approved_by: str | None = None,
    approved_at: str | None = None,
) -> Report:
    chain_text = " -> ".join(n.label for n in chain.nodes)
    return Report(
        id=rid,
        case_id=case_id,
        version=version,
        status=status,  # type: ignore[arg-type]
        title=title,
        summary=summary,
        sections=[
            ReportSection(
                id="s1",
                heading="Finding",
                body=f"{summary}\n\nCausal chain: {chain_text}.",
            ),
            ReportSection(
                id="s2",
                heading="Evidence reviewed",
                body=context,
            ),
            ReportSection(
                id="s3",
                heading="Corrective action",
                body=actions,
            ),
            ReportSection(
                id="s4",
                heading="Limitations",
                body=limitations,
            ),
        ],
        approved_by=approved_by,
        approved_at=approved_at,
    )


def build_bracket() -> Scenario:
    sensors = [
        make_series("pour_temp", "Pour temperature", "°C", 712, 6, spec_low=700, spec_high=725, anomaly=31, seed=11),
        make_series("mould_temp", "Mould temperature", "°C", 184, 3, spec_low=170, spec_high=200, anomaly=-9, seed=12),
        make_series(
            "quench_temp", "Quench bath temperature", "°C", 58, 2.5, spec_low=45, spec_high=65, anomaly=-16, seed=13
        ),
        make_series("hold_time", "Furnace hold time", "min", 96, 4, spec_low=90, spec_high=110, anomaly=-14, seed=14),
        make_series("hydrogen", "Melt hydrogen", "ppm", 1.18, 0.09, spec_low=0.0, spec_high=1.4, anomaly=0.86, seed=15, decimals=2),
        make_series("die_cycles", "Die thermal cycles", "k", 41.2, 0.8, spec_low=None, spec_high=None, anomaly=2.4, seed=16),
    ]
    finding_surface = Finding(
        id="origin",
        x=37.2,
        y=43.5,
        depth=0,
        title="Crack origin",
        detail="The fracture begins 0.4 mm below the root fillet, not at the surface. The initiation site is a casting void.",
        evidence_id="EV-01",
        kind="surface",
    )
    finding_tool = Finding(
        id="tool",
        x=27.5,
        y=64.5,
        depth=0,
        title="Tool mark",
        detail="A machining ridge from pass 3 sits 7 mm from the crack. It is a real surface defect, but the crack path ignores it.",
        evidence_id="EV-03",
        kind="surface",
    )
    finding_poro = Finding(
        id="porosity",
        x=62.4,
        y=56.6,
        depth=55,
        title="Gas porosity cluster",
        detail="Six voids under the fillet. Largest void 0.8 mm, aligned with the crack path. Hydrogen level ran 0.86 ppm above baseline.",
        evidence_id="EV-02",
        kind="subsurface",
    )

    evidence = [
        ev(
            "EV-01",
            "image",
            "Crack origin at the root fillet",
            "Optical macro, 2.6x. The beach marks radiate from a point 0.4 mm below the surface.",
            "Inspection camera CAM-06 / case image",
            iso(ANCHOR),
            0.82,
            image="bracket-surface",
            finding="origin",
        ),
        ev(
            "EV-02",
            "image",
            "Porosity cluster under the fillet",
            "X-ray CT slice. Six voids, largest 0.8 mm, aligned with the crack path.",
            "X-ray station XR-02 / case image",
            iso(ANCHOR),
            0.94,
            image="bracket-xray",
            finding="porosity",
            largest_void_mm=0.8,
            voids=6,
        ),
        ev(
            "EV-03",
            "image",
            "Machining ridge, pass 3",
            "Surface topography. 0.05 mm deep, 7 mm from the crack origin. Surface-only feature.",
            "Inspection camera CAM-06",
            iso(ANCHOR),
            0.61,
            image="bracket-surface",
            finding="tool",
        ),
        ev(
            "EV-04",
            "chart",
            "Hydrogen above baseline",
            "Melt hydrogen averaged 2.04 ppm through the cast window against a 1.18 ppm baseline (9.6 sigma).",
            "OPC-UA / furnace 2 / 6-hour window",
            iso(ANCHOR - timedelta(hours=2)),
            0.9,
            sensor="hydrogen",
            z=9.6,
        ),
        ev(
            "EV-05",
            "chart",
            "Quench bath ran cold",
            "Quench temperature fell to 42 °C against a 58 °C setpoint. Cold quench raises the thermal gradient at the fillet.",
            "OPC-UA / quench line / 6-hour window",
            iso(ANCHOR - timedelta(hours=1)),
            0.74,
            sensor="quench_temp",
            z=-6.4,
        ),
        ev(
            "EV-06",
            "record",
            "Material batch B-2291",
            "Supplier certificate reports 1.9 ppm hydrogen at the ingot. Batch was accepted on a 1.4 ppm limit exception.",
            "MES batch record / B-2291",
            iso(ANCHOR - timedelta(days=9)),
            0.86,
            lot="B-2291",
            supplier="Rheinmetall Casting",
            hydrogen_ppm=1.9,
        ),
        ev(
            "EV-07",
            "record",
            "Furnace door seal replaced",
            "Seal replaced 12 days before the failure. Degraded seal explains the hydrogen pick-up during the hold.",
            "CMMS / WO-88231",
            iso(ANCHOR - timedelta(days=12)),
            0.58,
            work_order="WO-88231",
        ),
        ev(
            "EV-08",
            "record",
            "Operator note, shift B",
            "Operator flagged a 'different pour sound' at 05:50 and logged no alarm. No process change was made.",
            "Shift log / line 6",
            iso(ANCHOR - timedelta(hours=1)),
            0.44,
        ),
        ev(
            "EV-09",
            "similar",
            "Case 0398 — same batch family",
            "Hydrogen porosity initiated a quench crack on the same fillet. Approved cause: gas porosity. 4.1 h to resolve.",
            "Case history / 6 months",
            iso(ANCHOR - timedelta(days=47)),
            0.79,
            case="RC-0398",
            cause="gas_porosity",
        ),
        ev(
            "EV-10",
            "similar",
            "Case 0361 — tool mark false lead",
            "A machining ridge was proposed and rejected: the crack origin was subsurface. Confirmed gas porosity.",
            "Case history / 6 months",
            iso(ANCHOR - timedelta(days=88)),
            0.72,
            case="RC-0361",
            cause="gas_porosity",
        ),
        ev(
            "EV-11",
            "finding",
            "Crack starts below the surface",
            "Depth measurement: initiation at 0.4 mm. Tool marks are surface-only and cannot initiate this crack.",
            "Engineer measurement / loupe",
            iso(ANCHOR),
            0.92,
            depth_mm=0.4,
        ),
    ]

    history = [
        hist("RC-0398", 47, "Bracket fracture", "Gas porosity", "Line 6", "B-2277", 0.91, 4.1, "Same fillet, same supplier heat."),
        hist("RC-0361", 88, "Bracket fracture", "Gas porosity", "Line 6", "B-2204", 0.87, 3.6, "Tool mark proposed and rejected."),
        hist("RC-0352", 103, "Bracket fracture", "Quench crack", "Line 6", "B-2191", 0.71, 5.2, "Quench bath control valve stuck."),
        hist("RC-0330", 142, "Bracket fracture", "Gas porosity", "Line 4", "B-2148", 0.78, 6.8, "Hydrogen 2.2 ppm, seal leak."),
        hist("RC-0301", 190, "Porosity", "Gas porosity", "Line 4", "B-2090", 0.73, 2.9, "Detected before machining."),
        hist("RC-0288", 224, "Bracket fracture", "Tool mark", "Line 6", "B-2055", 0.34, 8.4, "Confirmed surface crack from tooling."),
        hist("RC-0264", 267, "Bracket fracture", "Material mix-up", "Line 4", "B-2011", 0.41, 11.0, "Wrong alloy supplied."),
        hist("RC-0241", 311, "Bracket fracture", "Quench crack", "Line 6", "B-1977", 0.55, 7.3, "Cold quench after maintenance."),
        hist("RC-0219", 356, "Porosity", "Gas porosity", "Line 6", "B-1930", 0.8, 3.2, "Degassed late in the shift."),
        hist("RC-0198", 402, "Bracket fracture", "Tool mark", "Line 6", "B-1881", 0.29, 6.0, "Ridge at the fillet, surface crack."),
        hist("RC-0177", 448, "Bracket fracture", "Gas porosity", "Line 4", "B-1840", 0.68, 4.8, "Long hold, hydrogen pick-up."),
        hist("RC-0150", 503, "Bracket fracture", "Quench crack", "Line 6", "B-1796", 0.5, 5.9, "Quench delay 22 s."),
    ]

    hyp = [
        Hypothesis(
            id="tool_mark",
            label="Tool mark / operator error",
            category="process",
            summary=(
                "A machining ridge sits near the root fillet and the previous shift changed the finishing insert. "
                "This is the most common answer for a fillet crack and the strongest match to surface evidence."
            ),
            score=0,
            confidence=0,
            rank=1,
            factors=HypothesisFactor(frequency=0.82, deviation=0.2, batch_match=0.05, similarity=0.74, recurrence=0.72),
            evidence_ids=["EV-03", "EV-08", "EV-11"],
            note="Plausible because a real ridge is visible 7 mm from the crack.",
        ),
        Hypothesis(
            id="gas_porosity",
            label="Gas porosity in the casting",
            category="material",
            summary=(
                "Hydrogen picked up during the hold formed a void cluster under the fillet. The largest void sits on the "
                "crack path. Batch B-2291 was accepted on a hydrogen exception."
            ),
            score=0,
            confidence=0,
            rank=2,
            factors=HypothesisFactor(frequency=0.44, deviation=0.18, batch_match=0.88, similarity=0.52, recurrence=0.35),
            evidence_ids=["EV-02", "EV-04", "EV-06", "EV-09", "EV-10", "EV-11"],
            note="Evidence is subsurface; it only appears after the depth reveal.",
        ),
        Hypothesis(
            id="quench_crack",
            label="Quench cracking",
            category="process",
            summary=(
                "Quench bath temperature dropped 16 °C below setpoint. The steep thermal gradient can open a hairline "
                "crack from any existing void."
            ),
            score=0,
            confidence=0,
            rank=3,
            factors=HypothesisFactor(frequency=0.3, deviation=0.72, batch_match=0.2, similarity=0.25, recurrence=0.18),
            evidence_ids=["EV-05", "EV-07"],
            note="A contributing mechanism, not the initiator.",
        ),
        Hypothesis(
            id="batch_contamination",
            label="Contaminated material batch",
            category="supplier",
            summary=(
                "Batch B-2291 came in at 1.9 ppm hydrogen against a 1.4 ppm limit. The supplier granted a deviation. "
                "Other parts from the batch have not failed, which weakens this as a standalone cause."
            ),
            score=0,
            confidence=0,
            rank=4,
            factors=HypothesisFactor(frequency=0.18, deviation=0.3, batch_match=0.55, similarity=0.15, recurrence=0.08),
            evidence_ids=["EV-06", "EV-07"],
        ),
    ]

    case = DefectCase(
        id="RC-0417",
        scenario_id="bracket",
        plant_id="plant-de",
        line_id="line-6",
        part="Turbine bracket, cast AlSi7Mg",
        serial="BRK-0417-B",
        defect_type="Fracture at root fillet",
        severity="critical",
        detected_at=iso(ANCHOR),
        machine_id="FURNACE-2",
        batch_id="B-2291",
        image_key="bracket-surface",
        bbox=[33.0, 36.0, 17.0, 20.0],
        detection_confidence=0.97,
        status="investigating",
        hours_in_service=1842,
        station="Final inspection",
        shift="B",
    )

    chain = CausalChain(
        nodes=[
            ChainNode(id="n1", label="Gas porosity", detail="Hydrogen voids under the fillet, largest 0.8 mm", kind="root"),
            ChainNode(id="n2", label="Quench crack", detail="Cold quench opens a hairline from the largest void", kind="mechanism"),
            ChainNode(id="n3", label="Service growth", detail="1,842 hours of cyclic load grows the crack", kind="growth"),
            ChainNode(id="n4", label="Failure", detail="Bracket fractures at the root fillet", kind="failure"),
        ],
        edges=[["n1", "n2"], ["n2", "n3"], ["n3", "n4"]],
        verdict="It was not fatigue. It started in the casting.",
        confidence=0.86,
    )

    batch = BatchRecord(
        id="B-2291",
        material="AlSi7Mg",
        supplier="Rheinmetall Casting",
        lot="HX-88211",
        received=iso(ANCHOR - timedelta(days=9)),
        certificate="CERT-88211-3",
        hydrogen_ppm=1.9,
        notes="Accepted on a 1.4 ppm hydrogen deviation. Supplier note: 'within measurement tolerance'.",
    )
    maintenance = [
        MaintenanceRecord(
            id="WO-88231",
            machine="FURNACE-2",
            kind="Door seal replacement",
            at=iso(ANCHOR - timedelta(days=12)),
            technician="A. Novak",
            note="Seal showed heat damage. Furnace not re-validated for hydrogen pick-up after the repair.",
            days_before_defect=12,
        ),
        MaintenanceRecord(
            id="WO-88104",
            machine="QUENCH-1",
            kind="Control valve calibration",
            at=iso(ANCHOR - timedelta(days=31)),
            technician="J. Silva",
            note="Valve response lag logged at 4 s. No follow-up measurement.",
            days_before_defect=31,
        ),
        MaintenanceRecord(
            id="WO-87998",
            machine="LINE-6",
            kind="Finishing insert change",
            at=iso(ANCHOR - timedelta(days=2)),
            technician="L. Brandt",
            note="Insert changed on schedule. Surface finish in tolerance.",
            days_before_defect=2,
        ),
    ]

    trace = [
        {
            "step": 1,
            "agent": "Intake",
            "tool": "detector.detect",
            "title": "Defect confirmed on camera 06",
            "detail": "Fracture at the root fillet, confidence 0.97. Case RC-0417 opened.",
            "status": "done",
            "evidence": ["EV-01"],
            "ms": 240,
        },
        {
            "step": 2,
            "agent": "Data",
            "tool": "opcua.read_window",
            "title": "Pulled 6 hours of machine state",
            "detail": "37 samples across 6 parameters around the defect timestamp. Two parameters out of spec.",
            "status": "done",
            "evidence": ["EV-04", "EV-05"],
            "ms": 610,
        },
        {
            "step": 3,
            "agent": "Data",
            "tool": "mes.batch",
            "title": "Linked batch B-2291",
            "detail": "Supplier certificate flagged hydrogen at 1.9 ppm. Accepted on deviation.",
            "status": "done",
            "evidence": ["EV-06"],
            "ms": 180,
        },
        {
            "step": 4,
            "agent": "Data",
            "tool": "cmms.history",
            "title": "Found 2 relevant maintenance events",
            "detail": "Furnace door seal replaced 12 days earlier; quench valve calibration overdue.",
            "status": "done",
            "evidence": ["EV-07"],
            "ms": 150,
        },
        {
            "step": 5,
            "agent": "Reasoner",
            "tool": "similar.search",
            "title": "Matched 2 of 12 historical cases",
            "detail": "RC-0398 (0.91) and RC-0361 (0.87) both resolved to gas porosity on the same fillet.",
            "status": "done",
            "evidence": ["EV-09", "EV-10"],
            "ms": 320,
        },
        {
            "step": 6,
            "agent": "Reasoner",
            "tool": "cause.rank",
            "title": "Ranked 4 causes",
            "detail": "Tool mark / operator error leads on surface evidence. Subsurface evidence is not yet reviewed.",
            "status": "done",
            "evidence": ["EV-03", "EV-11"],
            "ms": 430,
        },
        {
            "step": 7,
            "agent": "Guard",
            "tool": "engineer.check",
            "title": "Waiting for engineer",
            "detail": "No cause is approved automatically. The engineer must accept or reject each candidate.",
            "status": "waiting",
            "evidence": [],
            "ms": 0,
        },
    ]

    rpt = report_for(
        "RPT-0417",
        case.id,
        "Root cause report — RC-0417",
        "Gas porosity in the casting initiated a quench crack, which grew in service to a brittle fracture of the root fillet.",
        chain,
        context=(
            "Reviewed: camera 06 macro image, x-ray CT slice, 6-hour machine window for furnace 2 and the quench line, "
            "batch B-2291 certificate, 12 matching historical cases, and the last 90 days of maintenance records."
        ),
        actions=(
            "1. Quarantine the remainder of batch B-2291 and re-test hydrogen on three sample castings.\n"
            "2. Replace the furnace door seal and add a post-repair hydrogen validation step.\n"
            "3. Bring the quench control valve back inside 2 °C of setpoint and log response lag weekly.\n"
            "4. Add an x-ray check on the first part of every pour for the next 30 days."
        ),
        limitations=(
            "Synthetic demo data. The ranking is evidence-weighted, not a physical simulation. "
            "No automatic line control is performed; the engineer owns the decision."
        ),
        status="draft",
    )

    return Scenario(
        id="bracket",
        title="Turbine bracket — service fracture",
        subtitle="Casting · hydrogen porosity · the stage story",
        process="Aluminium casting / machining",
        defect="Fracture at root fillet",
        part="Turbine bracket, cast AlSi7Mg",
        image_keys=["bracket-surface", "bracket-xray"],
        case=case,
        findings=[finding_surface, finding_tool, finding_poro],
        sensors=sensors,
        batch=batch,
        maintenance=maintenance,
        history=history,
        hypotheses=rank_hypotheses(hyp),
        evidence=evidence,
        chain=chain,
        trace=trace,
        report=rpt,
        operator_note=(
            "Operator flagged a different pour sound at 05:50. No alarm was raised and no process change was made."
        ),
        provenance={
            "data": "Synthetic, generated in-house with a fixed seed",
            "model": "RootCause detector v0.9 (synthetic weights) + evidence ranking",
            "date": iso(ANCHOR),
            "licence": "MIT — no third-party image data",
            "note": "No MVTec AD or customer data is used in this public demo.",
        },
        baseline_hours=62.0,
        current_hours=3.2,
    )


def build_housing() -> Scenario:
    sensors = [
        make_series("barrel_temp", "Barrel zone 4", "°C", 238, 2.4, spec_low=230, spec_high=245, anomaly=8.4, seed=21),
        make_series("injection_pressure", "Injection pressure", "bar", 1120, 24, spec_low=1050, spec_high=1200, anomaly=-96, seed=22),
        make_series("cooling_time", "Cooling time", "s", 22.5, 0.8, spec_low=20, spec_high=30, anomaly=-3.6, seed=23),
        make_series("mould_temp", "Mould temperature", "°C", 68, 2.0, spec_low=55, spec_high=80, anomaly=-6.2, seed=24),
        make_series("moisture", "Resin moisture", "%", 0.08, 0.012, spec_low=0.0, spec_high=0.12, anomaly=0.071, seed=25, decimals=3),
        make_series("clamp_force", "Clamp force", "kN", 640, 12, spec_low=600, spec_high=700, anomaly=-28, seed=26),
    ]
    evidence = [
        ev("H-EV-01", "image", "Short shot at the rib", "Glossy unfilled area at the last rib. 18.4 mm of missing fill.", "Camera CAM-02", iso(ANCHOR), 0.91, image="housing-surface", finding="short"),
        ev("H-EV-02", "chart", "Resin moisture above limit", "Moisture averaged 0.151 % against a 0.12 % upper limit for 47 minutes before the defect.", "MES / dryer 3", iso(ANCHOR - timedelta(hours=1)), 0.88, sensor="moisture", z=5.9),
        ev("H-EV-03", "chart", "Cooling time short", "Cooling time dropped to 18.9 s. Short cooling raises warpage, but does not cause a short shot.", "OPC-UA / press 4", iso(ANCHOR - timedelta(hours=1)), 0.6, sensor="cooling_time", z=-4.5),
        ev("H-EV-04", "record", "Resin batch PL-8840", "Lot opened 6 days ago. Dryer 3 regeneration overdue by 38 hours.", "MES batch / PL-8840", iso(ANCHOR - timedelta(days=6)), 0.86, lot="PL-8840", supplier="SABIC", moisture=0.151),
        ev("H-EV-05", "record", "Dryer 3 regeneration overdue", "Regeneration due 2026-10-20. Last completed 2026-10-14 06:00.", "CMMS / WO-88412", iso(ANCHOR - timedelta(days=8)), 0.78, work_order="WO-88412"),
        ev("H-EV-06", "similar", "Case 0402 — moisture short shot", "Same press, same resin family. Drying restored the process. Approved cause: material moisture.", "Case history", iso(ANCHOR - timedelta(days=38)), 0.84, case="RC-0402", cause="moisture"),
        ev("H-EV-07", "similar", "Case 0344 — cooling time", "Warpage, not short shot. Cooling time restored. Approved cause: cooling deviation.", "Case history", iso(ANCHOR - timedelta(days=124)), 0.61, case="RC-0344", cause="cooling"),
    ]
    hyp = [
        Hypothesis(
            id="moisture",
            label="Resin moisture above limit",
            category="material",
            summary="Dryer 3 missed regeneration. Resin moisture reached 0.151 %, causing hydrolysis and a short shot at the last rib.",
            score=0, confidence=0, rank=1,
            factors=HypothesisFactor(frequency=0.68, deviation=0.92, batch_match=0.78, similarity=0.8, recurrence=0.55),
            evidence_ids=["H-EV-02", "H-EV-04", "H-EV-05", "H-EV-06"],
        ),
        Hypothesis(
            id="cooling",
            label="Cooling time too short",
            category="process",
            summary="Cooling time fell 3.6 s below setpoint. This explains the warpage seen on the same shift, but not the unfilled rib.",
            score=0, confidence=0, rank=2,
            factors=HypothesisFactor(frequency=0.42, deviation=0.7, batch_match=0.1, similarity=0.48, recurrence=0.3),
            evidence_ids=["H-EV-03", "H-EV-07"],
        ),
        Hypothesis(
            id="pressure",
            label="Injection pressure drift",
            category="machine",
            summary="Pressure ran 96 bar low for 40 minutes. A contributing factor, likely secondary to the moisture-driven viscosity change.",
            score=0, confidence=0, rank=3,
            factors=HypothesisFactor(frequency=0.36, deviation=0.58, batch_match=0.05, similarity=0.35, recurrence=0.22),
            evidence_ids=["H-EV-03"],
        ),
    ]
    chain = CausalChain(
        nodes=[
            ChainNode(id="n1", label="Wet resin", detail="Dyer 3 regeneration overdue; moisture 0.151 %", kind="root"),
            ChainNode(id="n2", label="Hydrolysis", detail="Viscosity rise and gas generation during plastification", kind="mechanism"),
            ChainNode(id="n3", label="Short shot", detail="Last rib does not fill at 1120 bar", kind="failure"),
        ],
        edges=[["n1", "n2"], ["n2", "n3"]],
        verdict="The dryer, not the mould, made the short shot.",
        confidence=0.82,
    )
    case = DefectCase(
        id="RC-0431", scenario_id="housing", plant_id="plant-de", line_id="line-2",
        part="Housing, PA66-GF30", serial="HSG-0431-A", defect_type="Short shot at rib 4",
        severity="high", detected_at=iso(ANCHOR + timedelta(minutes=8)), machine_id="PRESS-4",
        batch_id="PL-8840", image_key="housing-surface", bbox=[52.0, 44.0, 21.0, 17.0],
        detection_confidence=0.96, status="investigating", station="Vision cell 2", shift="A",
    )
    rpt = report_for(
        "RPT-0431", case.id, "Root cause report — RC-0431",
        "Moisture in resin batch PL-8840 caused hydrolysis and a short shot at rib 4. Cooling deviation is a secondary finding.",
        chain,
        context="Reviewed dryer 3 logs, resin batch certificate, 6 hours of press data, vision cell 2, and two similar cases.",
        actions="Regenerate dryer 3, quarantine PL-8840 until moisture is verified, restore cooling time to 22.5 s, re-run first-off inspection.",
        limitations="Synthetic demo data. Moisture is inferred from the dryer log and process response, not from a lab sample.",
    )
    return Scenario(
        id="housing", title="Housing — short shot", subtitle="Injection moulding · wet resin · 3 minutes",
        process="Injection moulding", defect="Short shot at rib 4", part="Housing, PA66-GF30",
        image_keys=["housing-surface"], case=case,
        findings=[], sensors=sensors,
        batch=BatchRecord(id="PL-8840", material="PA66-GF30", supplier="SABIC", lot="PL-8840", received=iso(ANCHOR - timedelta(days=6)), certificate="CERT-PL-8840", moisture_pct=0.151, notes="Dryer 3 regeneration overdue."),
        maintenance=[MaintenanceRecord(id="WO-88412", machine="DRYER-3", kind="Regeneration", at=iso(ANCHOR - timedelta(days=8)), technician="K. Meier", note="Regeneration overdue by 38 h.", days_before_defect=8)],
        history=[hist("RC-0402", 38, "Short shot", "Moisture", "Line 2", "PL-8691", 0.84, 3.1, "Drying restored the process."), hist("RC-0344", 124, "Warpage", "Cooling deviation", "Line 2", "PL-8320", 0.61, 4.8, "Cooling time restored.")],
        hypotheses=rank_hypotheses(hyp), evidence=evidence, chain=chain, trace=[], report=rpt,
        operator_note="Visual alarm at rib 4. Press ran normally otherwise.", provenance={"data": "Synthetic", "model": "RootCause detector v0.9", "date": iso(ANCHOR), "licence": "MIT"},
        baseline_hours=41.0, current_hours=2.4,
    )


def build_battery() -> Scenario:
    sensors = [
        make_series("laser_power", "Laser power", "W", 1.82, 0.04, spec_low=1.75, spec_high=1.9, anomaly=-0.17, seed=31, decimals=3),
        make_series("weld_speed", "Weld speed", "mm/s", 210, 4.2, spec_low=195, spec_high=225, anomaly=-9, seed=32),
        make_series("shield_gas", "Shield gas flow", "l/min", 18.0, 0.6, spec_low=15, spec_high=22, anomaly=-1.3, seed=33),
        make_series("fixture_force", "Fixture force", "N", 420, 12, spec_low=380, spec_high=460, anomaly=-18, seed=34),
        make_series("ambient_humidity", "Cell room humidity", "%RH", 41, 2.0, spec_low=30, spec_high=50, anomaly=6, seed=35),
    ]
    evidence = [
        ev("B-EV-01", "image", "Weld crack at tab", "CT slice shows incomplete fusion at the tab root. Crack length 1.9 mm.", "CT station CT-01", iso(ANCHOR), 0.93, image="weld-surface", finding="crack"),
        ev("B-EV-02", "chart", "Laser power drift", "Laser power fell from 1.82 W to 1.64 W over 22 minutes. Power monitor calibration was 41 days overdue.", "OPC-UA / welder 7", iso(ANCHOR - timedelta(minutes=30)), 0.9, sensor="laser_power", z=-4.5),
        ev("B-EV-03", "record", "Calibration overdue", "Power monitor calibration due 2026-09-11. Last completed 2026-08-01.", "CMMS / WO-87111", iso(ANCHOR - timedelta(days=41)), 0.8),
        ev("B-EV-04", "chart", "Fixture force low", "Fixture force ran 18 N low. Could contribute to gap variation at the tab root.", "OPC-UA / fixture 7", iso(ANCHOR - timedelta(minutes=20)), 0.64, sensor="fixture_force", z=-1.5),
        ev("B-EV-05", "similar", "Case 0391 — laser drift", "Same welder, same tab design. Approved cause: laser power drift.", "Case history", iso(ANCHOR - timedelta(days=61)), 0.88, case="RC-0391", cause="laser"),
        ev("B-EV-06", "record", "Foil batch F-771", "Supplier changed foil surface treatment in August. Incoming checks pass.", "MES / F-771", iso(ANCHOR - timedelta(days=4)), 0.42),
      ]
    hyp = [
        Hypothesis(id="laser", label="Laser power drift", category="machine", summary="Power fell 10 % as the monitor drifted out of calibration. Incomplete fusion matches the energy deficit.", score=0, confidence=0, rank=1, factors=HypothesisFactor(frequency=0.72, deviation=0.88, batch_match=0.08, similarity=0.84, recurrence=0.6), evidence_ids=["B-EV-02", "B-EV-03", "B-EV-05"]),
        Hypothesis(id="fixture", label="Fixture force variation", category="tooling", summary="Force ran low, but the gap stays inside the weld qualification window. A secondary contributor at most.", score=0, confidence=0, rank=2, factors=HypothesisFactor(frequency=0.38, deviation=0.36, batch_match=0.05, similarity=0.42, recurrence=0.24), evidence_ids=["B-EV-04"]),
        Hypothesis(id="foil", label="Foil surface variation", category="supplier", summary="A supplier process change is documented, but incoming checks and the timing do not line up with this failure.", score=0, confidence=0, rank=3, factors=HypothesisFactor(frequency=0.22, deviation=0.12, batch_match=0.3, similarity=0.2, recurrence=0.1), evidence_ids=["B-EV-06"]),
    ]
    chain = CausalChain(nodes=[ChainNode(id="n1", label="Laser power drift", detail="1.82 W to 1.64 W as calibration aged", kind="root"), ChainNode(id="n2", label="Incomplete fusion", detail="Energy deficit at the tab root", kind="mechanism"), ChainNode(id="n3", label="Tab crack", detail="1.9 mm crack found at end-of-line CT", kind="failure")], edges=[["n1", "n2"], ["n2", "n3"]], verdict="The welder lost power before the part lost strength.", confidence=0.85)
    case = DefectCase(id="RC-0440", scenario_id="battery", plant_id="plant-de", line_id="line-4", part="Cell tab weld, 21700", serial="CELL-0440-07", defect_type="Incomplete fusion at tab weld", severity="critical", detected_at=iso(ANCHOR + timedelta(minutes=16)), machine_id="WELDER-7", batch_id="F-771", image_key="weld-surface", bbox=[42.0, 39.0, 18.0, 22.0], detection_confidence=0.94, status="investigating", station="CT station 1", shift="B")
    rpt = report_for("RPT-0440", case.id, "Root cause report — RC-0440", "Laser power drifted 10 % below setpoint because the power monitor was out of calibration. The weld did not fuse at the tab root.", chain, context="Reviewed CT slice, welder 7 telemetry, calibration record and two similar cases.", actions="Recalibrate the power monitor, re-qualify the weld recipe, add a daily power verification coupon, quarantine cells from the last 4 hours.", limitations="Synthetic demo data. CT interpretation is precomputed for the demo.", status="draft")
    return Scenario(id="battery", title="Cell tab weld — incomplete fusion", subtitle="Battery cell · laser drift · high value", process="Laser welding", defect="Incomplete fusion", part="Cell tab weld, 21700", image_keys=["weld-surface"], case=case, findings=[], sensors=sensors, batch=BatchRecord(id="F-771", material="Ni-plated steel foil", supplier="Nippon Steel", lot="F-771", received=iso(ANCHOR - timedelta(days=4)), certificate="CERT-F-771", notes="Incoming checks pass."), maintenance=[MaintenanceRecord(id="WO-87111", machine="WELDER-7", kind="Power monitor calibration", at=iso(ANCHOR - timedelta(days=41)), technician="S. Ito", note="Calibration overdue.", days_before_defect=41)], history=[hist("RC-0391", 61, "Weld crack", "Laser power drift", "Line 4", "F-702", 0.88, 2.7, "Recalibrated."), hist("RC-0350", 118, "Weld crack", "Fixture force", "Line 4", "F-688", 0.51, 5.4, "Fixture shim replaced.")], hypotheses=rank_hypotheses(hyp), evidence=evidence, chain=chain, trace=[], report=rpt, operator_note="CT alarm at the end-of-line station.", provenance={"data": "Synthetic", "model": "RootCause detector v0.9", "date": iso(ANCHOR), "licence": "MIT"}, baseline_hours=36.0, current_hours=2.9)


def build_electronics() -> Scenario:
    sensors = [
        make_series("zone3_temp", "Reflow zone 3", "°C", 217, 2.1, spec_low=210, spec_high=225, anomaly=-11, seed=41),
        make_series("conveyor", "Conveyor speed", "cm/min", 72, 1.2, spec_low=68, spec_high=76, anomaly=0.6, seed=42),
        make_series("paste_age", "Paste open time", "h", 3.2, 0.5, spec_low=0, spec_high=6, anomaly=2.9, seed=43),
        make_series("stencil_cycles", "Stencil print cycles", "k", 82, 2.0, spec_low=None, spec_high=None, anomaly=7.5, seed=44),
        make_series("humidity", "Assembly humidity", "%RH", 44, 2.0, spec_low=30, spec_high=55, anomaly=2.0, seed=45),
    ]
    evidence = [
        ev("E-EV-01", "image", "Solder void under QFN", "X-ray shows 31 % voiding under the thermal pad against a 25 % limit.", "X-ray cell XR-04", iso(ANCHOR), 0.9, image="solder-surface", finding="void"),
        ev("E-EV-02", "chart", "Reflow zone 3 low", "Zone 3 fell to 206 °C, 11 °C below setpoint, for 19 minutes.", "OPC-UA / oven 2", iso(ANCHOR - timedelta(minutes=25)), 0.86, sensor="zone3_temp", z=-5.2),
        ev("E-EV-03", "record", "Solder paste open time", "Paste exceeded open time by 2.9 h before print.", "Line 3 paste log", iso(ANCHOR - timedelta(hours=5)), 0.7),
        ev("E-EV-04", "record", "Stencil wear", "Stencil at 89.5 k cycles against a 100 k limit. Aperture inspection passed.", "Tooling / ST-118", iso(ANCHOR - timedelta(days=3)), 0.35),
        ev("E-EV-05", "similar", "Case 0376 — reflow profile", "Same oven, similar void signature. Approved cause: reflow zone 3 deviation.", "Case history", iso(ANCHOR - timedelta(days=79)), 0.86, case="RC-0376", cause="reflow"),
      ]
    hyp = [
        Hypothesis(id="reflow", label="Reflow zone 3 under-temperature", category="process", summary="Zone 3 ran 11 °C low, reducing flux activation and leaving voids under the thermal pad.", score=0, confidence=0, rank=1, factors=HypothesisFactor(frequency=0.62, deviation=0.86, batch_match=0.08, similarity=0.82, recurrence=0.5), evidence_ids=["E-EV-01", "E-EV-02", "E-EV-05"]),
        Hypothesis(id="paste", label="Solder paste past open time", category="material", summary="Paste exceeded open time. It raises void risk, but similar pastes passed at this void level.", score=0, confidence=0, rank=2, factors=HypothesisFactor(frequency=0.34, deviation=0.42, batch_match=0.25, similarity=0.38, recurrence=0.2), evidence_ids=["E-EV-03"]),
        Hypothesis(id="stencil", label="Stencil aperture wear", category="tooling", summary="High cycle count, but aperture inspection passed and print volume is in tolerance.", score=0, confidence=0, rank=3, factors=HypothesisFactor(frequency=0.28, deviation=0.24, batch_match=0.02, similarity=0.22, recurrence=0.12), evidence_ids=["E-EV-04"]),
    ]
    chain = CausalChain(nodes=[ChainNode(id="n1", label="Zone 3 under-temperature", detail="206 °C against a 217 °C setpoint", kind="root"), ChainNode(id="n2", label="Poor flux activation", detail="Oxide not removed at the thermal pad", kind="mechanism"), ChainNode(id="n3", label="Solder voiding", detail="31 % voiding, above the 25 % limit", kind="failure")], edges=[["n1", "n2"], ["n2", "n3"]], verdict="The oven cooled the joint before the flux could clean it.", confidence=0.8)
    case = DefectCase(id="RC-0452", scenario_id="electronics", plant_id="plant-de", line_id="line-3", part="Control board, QFN-32", serial="PCB-0452-11", defect_type="Solder void under QFN", severity="medium", detected_at=iso(ANCHOR + timedelta(minutes=23)), machine_id="OVEN-2", batch_id="PST-2291", image_key="solder-surface", bbox=[46.0, 41.0, 16.0, 18.0], detection_confidence=0.92, status="investigating", station="X-ray 4", shift="A")
    rpt = report_for("RPT-0452", case.id, "Root cause report — RC-0452", "Reflow zone 3 under-temperature reduced flux activation and left 31 % voiding under the QFN thermal pad.", chain, context="Reviewed X-ray, oven telemetry, paste log, stencil record and a similar case.", actions="Recover oven zone 3, verify profile with a coupon, tighten paste open-time control, re-X-ray the last 2 hours of boards.", limitations="Synthetic demo data. X-ray void measurement is precomputed.", status="draft")
    return Scenario(id="electronics", title="Control board — solder void", subtitle="Electronics assembly · reflow profile · 4 minutes", process="SMT reflow", defect="Solder void under QFN", part="Control board, QFN-32", image_keys=["solder-surface"], case=case, findings=[], sensors=sensors, batch=BatchRecord(id="PST-2291", material="SAC305 solder paste", supplier="MacDermid", lot="PST-2291", received=iso(ANCHOR - timedelta(days=2)), certificate="CERT-PST-2291", notes="Open time exceeded before print."), maintenance=[MaintenanceRecord(id="WO-87008", machine="OVEN-2", kind="Heating element check", at=iso(ANCHOR - timedelta(days=17)), technician="R. Patel", note="Zone 3 element within specification at check.", days_before_defect=17)], history=[hist("RC-0376", 79, "Solder void", "Reflow profile", "Line 3", "PST-2201", 0.86, 3.4, "Zone 3 recovered."), hist("RC-0321", 156, "Solder void", "Paste open time", "Line 3", "PST-2144", 0.55, 4.1, "Paste control tightened.")], hypotheses=rank_hypotheses(hyp), evidence=evidence, chain=chain, trace=[], report=rpt, operator_note="X-ray flagged 31 % voiding on the thermal pad.", provenance={"data": "Synthetic", "model": "RootCause detector v0.9", "date": iso(ANCHOR), "licence": "MIT"}, baseline_hours=28.0, current_hours=2.1)


def build_pack() -> Pack:
    scenarios = [build_bracket(), build_housing(), build_battery(), build_electronics()]
    plants = [
        Plant(id="plant-de", name="Werk Süd", site="Stuttgart", country="Germany"),
        Plant(id="plant-cn", name="Werk East", site="Suzhou", country="China"),
    ]
    lines = [
        Line(id="line-6", plant_id="plant-de", name="Line 6 · casting", process="Casting / machining", part="Turbine bracket", cameras=3, machines=4),
        Line(id="line-2", plant_id="plant-de", name="Line 2 · moulding", process="Injection moulding", part="Housing PA66", cameras=2, machines=3),
        Line(id="line-4", plant_id="plant-de", name="Line 4 · cell weld", process="Laser welding", part="21700 cell tab", cameras=4, machines=3),
        Line(id="line-3", plant_id="plant-de", name="Line 3 · SMT", process="Reflow", part="Control board", cameras=2, machines=2),
        Line(id="line-8", plant_id="plant-cn", name="Line 8 · moulding", process="Injection moulding", part="Housing PA66", cameras=2, machines=3),
    ]

    connectors = [
        Connector(id="opcua-furnace", name="Furnace 2 · OPC-UA", protocol="OPC-UA", category="Machine", status="connected", endpoint="opc.tcp://10.8.4.21:4840", detail="6 parameters, 1 s poll", points=6, last_sync=iso(ANCHOR - timedelta(minutes=1)), phase="1.1"),
        Connector(id="opcua-quench", name="Quench line · OPC-UA", protocol="OPC-UA", category="Machine", status="connected", endpoint="opc.tcp://10.8.4.22:4840", detail="3 parameters, 1 s poll", points=3, last_sync=iso(ANCHOR - timedelta(minutes=1)), phase="1.1"),
        Connector(id="modbus-old-press", name="Press 9 · Modbus TCP", protocol="Modbus", category="Machine", status="simulated", endpoint="10.8.4.39:502", detail="Older PLC fallback, 12 registers", points=12, last_sync=iso(ANCHOR - timedelta(minutes=4)), phase="1.1"),
        Connector(id="camera-keyence", name="Keyence CV-X · camera feed", protocol="TCP/IP", category="Vision", status="connected", endpoint="10.8.4.51:9000", detail="Generic frame reader, 30 fps", points=0, last_sync=iso(ANCHOR - timedelta(seconds=34)), phase="1.1"),
        Connector(id="camera-cognex", name="Cognex In-Sight · camera feed", protocol="TCP/IP", category="Vision", status="available", endpoint="10.8.4.52:9000", detail="Ready to pair", points=0, phase="1.1"),
        Connector(id="mes-batch", name="MES batch records", protocol="CSV import", category="MES", status="connected", endpoint="\\fileshare\\mes\\batches", detail="Nightly import, 1,284 records", points=1284, last_sync=iso(ANCHOR - timedelta(hours=7)), phase="1.1"),
        Connector(id="qm-history", name="Quality system history", protocol="CSV import", category="Quality", status="connected", endpoint="\\fileshare\\qm\\cases", detail="6 months, 312 cases", points=312, last_sync=iso(ANCHOR - timedelta(hours=7)), phase="1.1"),
        Connector(id="cmms", name="Maintenance · CMMS", protocol="REST", category="Maintenance", status="available", endpoint="https://cmms.local/api", detail="Read-only service account", points=0, phase="2.2"),
        Connector(id="sap-qm", name="SAP QM", protocol="SAP QM", category="Quality", status="available", endpoint="SAP-PRD / QM", detail="Inspection lots and notifications", points=0, phase="2.2"),
        Connector(id="sap-pm", name="SAP PM", protocol="SAP PM", category="Maintenance", status="available", endpoint="SAP-PRD / PM", detail="Work orders and equipment history", points=0, phase="2.2"),
        Connector(id="factorytalk", name="Rockwell FactoryTalk", protocol="FactoryTalk", category="SCADA", status="available", endpoint="FTVW / line 6", detail="Tag browser", points=0, phase="2.2"),
        Connector(id="s7", name="Siemens S7 / TIA", protocol="S7", category="PLC", status="available", endpoint="10.8.4.61 / rack 0 slot 1", detail="ISO-on-TCP", points=0, phase="2.2"),
        Connector(id="generic-rest", name="Generic REST / GraphQL", protocol="REST", category="Integration", status="available", endpoint="configure", detail="Bring your own system", points=0, phase="2.2"),
        Connector(id="supplier-cert", name="Supplier certificates", protocol="CSV / PDF import", category="Supplier", status="simulated", endpoint="\\fileshare\\supplier", detail="Certificate parser", points=64, last_sync=iso(ANCHOR - timedelta(days=1)), phase="2.2"),
    ]

    audits = [
        AuditEvent(id="A-1042", at=iso(ANCHOR - timedelta(minutes=4)), actor="rootcause-agent", action="case.created", object="RC-0417", detail="Defect detected on camera 06, confidence 0.97", data_sources=["camera-keyence"]),
        AuditEvent(id="A-1041", at=iso(ANCHOR - timedelta(minutes=3)), actor="rootcause-agent", action="evidence.pulled", object="RC-0417", detail="6 h machine window, batch B-2291, 2 maintenance records, 12 similar cases", data_sources=["opcua-furnace", "mes-batch", "qm-history"]),
        AuditEvent(id="A-1040", at=iso(ANCHOR - timedelta(minutes=2)), actor="M. Weber", action="case.reviewed", object="RC-0416", detail="Approved cause: cooling deviation", data_sources=["opcua-quench"]),
        AuditEvent(id="A-1039", at=iso(ANCHOR - timedelta(hours=2)), actor="M. Weber", action="report.approved", object="RPT-0416", detail="Report version 2 signed off", data_sources=["opcua-furnace"]),
    ]

    dashboard = Dashboard(
        investigations_this_week=14,
        investigations_delta=0.27,
        median_hours_to_cause=3.6,
        baseline_hours_to_cause=51.0,
        cause_accuracy=0.81,
        scrap_prevented_eur=38400,
        rework_prevented_eur=12600,
        engineer_hours_saved=174,
        defect_rate_pct=[
            {"week": "W36", "line-6": 2.8, "line-2": 1.9, "line-4": 1.2, "line-3": 0.9},
            {"week": "W37", "line-6": 2.6, "line-2": 2.1, "line-4": 1.3, "line-3": 0.8},
            {"week": "W38", "line-6": 3.1, "line-2": 1.7, "line-4": 1.1, "line-3": 1.0},
            {"week": "W39", "line-6": 2.4, "line-2": 2.0, "line-4": 1.4, "line-3": 0.7},
            {"week": "W40", "line-6": 2.2, "line-2": 1.6, "line-4": 1.0, "line-3": 0.9},
            {"week": "W41", "line-6": 2.5, "line-2": 1.8, "line-4": 1.2, "line-3": 0.8},
            {"week": "W42", "line-6": 2.0, "line-2": 1.4, "line-4": 0.9, "line-3": 0.7},
            {"week": "W43", "line-6": 1.8, "line-2": 1.5, "line-4": 0.8, "line-3": 0.6},
        ],
        top_causes=[
            {"cause": "Gas porosity", "count": 11, "share": 0.26},
            {"cause": "Cooling deviation", "count": 8, "share": 0.19},
            {"cause": "Laser power drift", "count": 7, "share": 0.17},
            {"cause": "Material moisture", "count": 6, "share": 0.14},
            {"cause": "Tool wear", "count": 5, "share": 0.12},
            {"cause": "Reflow profile", "count": 5, "share": 0.12},
        ],
        weekly=[
            {"week": "W36", "investigations": 6, "hours": 9.1, "baseline": 52},
            {"week": "W37", "investigations": 7, "hours": 7.8, "baseline": 50},
            {"week": "W38", "investigations": 8, "hours": 6.4, "baseline": 48},
            {"week": "W39", "investigations": 9, "hours": 5.2, "baseline": 49},
            {"week": "W40", "investigations": 11, "hours": 4.6, "baseline": 51},
            {"week": "W41", "investigations": 12, "hours": 4.1, "baseline": 47},
            {"week": "W42", "investigations": 13, "hours": 3.8, "baseline": 50},
            {"week": "W43", "investigations": 14, "hours": 3.6, "baseline": 51},
        ],
        resolution_by_line=[
            {"line": "Line 6", "hours": 3.4, "cases": 12},
            {"line": "Line 2", "hours": 2.9, "cases": 9},
            {"line": "Line 4", "hours": 4.1, "cases": 8},
            {"line": "Line 3", "hours": 3.2, "cases": 6},
        ],
    )

    alerts = [
        Alert(id="AL-31", level="warning", title="Hydrogen trending up on Line 6", detail="Melt hydrogen 1.6 ppm average over 3 pours. Limit 1.4 ppm.", at=iso(ANCHOR - timedelta(hours=1)), line_id="line-6"),
        Alert(id="AL-30", level="critical", title="Dryer 3 regeneration overdue", detail="Line 2 dryer is 38 h past regeneration. Moisture at 0.151 %.", at=iso(ANCHOR - timedelta(hours=3)), line_id="line-2"),
        Alert(id="AL-29", level="info", title="Case RC-0417 assigned to M. Weber", detail="Investigation started 4 minutes ago.", at=iso(ANCHOR - timedelta(minutes=4)), line_id="line-6"),
    ]

    actions = [
        CorrectiveAction(id="CA-118", case_id="RC-0417", title="Quarantine batch B-2291 and re-test hydrogen", owner="M. Weber", due=iso(ANCHOR + timedelta(days=2)), status="in_progress", saving_eur=18400),
        CorrectiveAction(id="CA-117", case_id="RC-0417", title="Replace furnace door seal, add post-repair gas check", owner="A. Novak", due=iso(ANCHOR + timedelta(days=5)), status="open", saving_eur=9200),
        CorrectiveAction(id="CA-116", case_id="RC-0431", title="Regenerate dryer 3 and verify resin moisture", owner="K. Meier", due=iso(ANCHOR + timedelta(days=1)), status="open", saving_eur=6400),
        CorrectiveAction(id="CA-115", case_id="RC-0416", title="Restore cooling time on press 2", owner="J. Silva", due=iso(ANCHOR - timedelta(days=1)), status="done", saving_eur=2100),
        CorrectiveAction(id="CA-114", case_id="RC-0440", title="Recalibrate welder 7 power monitor", owner="S. Ito", due=iso(ANCHOR + timedelta(days=3)), status="in_progress", saving_eur=11200),
    ]

    billing = Billing(
        plan="Pilot · 90 days",
        lines=4,
        per_line_month_eur=2400,
        setup_fee_eur=28000,
        npu_option_eur=1150,
        npu_enabled=True,
        mrr_eur=4 * 2400 + 1150,
        next_invoice=iso(ANCHOR + timedelta(days=18)),
        invoices=[
            {"id": "INV-2026-09", "date": iso(ANCHOR - timedelta(days=30)), "amount": 10750, "status": "paid"},
            {"id": "INV-2026-08", "date": iso(ANCHOR - timedelta(days=60)), "amount": 10750, "status": "paid"},
            {"id": "INV-SETUP", "date": iso(ANCHOR - timedelta(days=75)), "amount": 28000, "status": "paid"},
        ],
    )

    compliance = [
        CompliancePack(id="iso9001", name="ISO 9001 quality workflow", standard="ISO 9001:2015", status="ready", controls=24, covered=24, detail="Case ownership, approval, record retention and corrective-action loop."),
        CompliancePack(id="iatf", name="IATF 16949 pack", standard="IATF 16949:2016", status="in_progress", controls=31, covered=24, detail="Automotive traceability and PPAP evidence export."),
        CompliancePack(id="fda", name="FDA 21 CFR Part 11 audit trail", standard="21 CFR Part 11", status="planned", controls=18, covered=6, detail="Electronic signature and immutable audit trail for pharma/medtech."),
    ]

    users = [
        User(id="u1", name="Mara Weber", role="quality_manager", line_ids=["line-6", "line-2", "line-4", "line-3"], initials="MW"),
        User(id="u2", name="Tomas Keller", role="engineer", line_ids=["line-6"], initials="TK"),
        User(id="u3", name="Priya Nair", role="engineer", line_ids=["line-2", "line-4"], initials="PN"),
        User(id="u4", name="Lars Brandt", role="operator", line_ids=["line-6"], initials="LB"),
        User(id="u5", name="Site Admin", role="admin", line_ids=[], initials="SA"),
    ]

    connector_library = [
        {"id": "opcua", "name": "OPC-UA", "systems": "Kepware, Siemens, Beckhoff", "status": "shipped", "phase": "1.1"},
        {"id": "modbus", "name": "Modbus TCP/RTU", "systems": "Legacy PLCs, power meters", "status": "shipped", "phase": "1.1"},
        {"id": "keyence", "name": "Keyence CV-X / IV", "systems": "Inspection cameras", "status": "shipped", "phase": "1.1"},
        {"id": "cognex", "name": "Cognex In-Sight", "systems": "Inspection cameras", "status": "shipped", "phase": "1.1"},
        {"id": "mes-csv", "name": "MES / ERP CSV", "systems": "SAP, Oracle, custom", "status": "shipped", "phase": "1.1"},
        {"id": "sap-qm", "name": "SAP QM", "systems": "Inspection lots, notifications", "status": "shipped", "phase": "2.2"},
        {"id": "sap-pm", "name": "SAP PM", "systems": "Work orders, equipment", "status": "shipped", "phase": "2.2"},
        {"id": "factorytalk", "name": "Rockwell FactoryTalk", "systems": "Logix, tags", "status": "shipped", "phase": "2.2"},
        {"id": "s7", "name": "Siemens S7 / TIA", "systems": "S7-1200/1500", "status": "shipped", "phase": "2.2"},
        {"id": "rest", "name": "Generic REST / GraphQL", "systems": "Anything with an API", "status": "shipped", "phase": "2.2"},
        {"id": "supplier", "name": "Supplier certificates", "systems": "CoA, CoC PDF/CSV", "status": "shipped", "phase": "2.2"},
        {"id": "iso", "name": "ISO 9001 workflow", "systems": "Document control", "status": "beta", "phase": "3"},
        {"id": "iatf", "name": "IATF 16949", "systems": "Automotive evidence", "status": "beta", "phase": "3"},
        {"id": "fda", "name": "FDA 21 CFR Part 11", "systems": "E-signature, audit trail", "status": "planned", "phase": "3"},
    ]

    sharing = {
        "enabled": False,
        "scope": "cross-factory anonymised patterns, opt-in",
        "factories": 2,
        "shared_causes": 0,
        "note": "Off by default. Only aggregated cause labels and factor ranges are shared; images, batches and machine identifiers never leave the site.",
    }

    return Pack(
        meta={
            "version": "0.9.0",
            "generated": iso(ANCHOR),
            "anchor": iso(ANCHOR),
            "seed": 417,
            "scenario_ids": [s.id for s in scenarios],
            "model": "rootcause-detector-0.9 (synthetic weights)",
            "note": "Deterministic synthetic data pack. No customer data, no network calls.",
        },
        plants=plants,
        lines=lines,
        scenarios=scenarios,
        connectors=connectors,
        audits=audits,
        dashboard=dashboard,
        alerts=alerts,
        actions=actions,
        billing=billing,
        compliance=compliance,
        users=users,
        connector_library=connector_library,
        sharing=sharing,
    )
