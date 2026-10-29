"""Domain models for RootCause.

The models are deliberately small and serialisable: the same shapes are exposed by the
HTTP API and embedded in the offline demo pack consumed by the web client.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Plant(BaseModel):
    id: str
    name: str
    site: str
    country: str
    timezone: str = "Europe/Berlin"


class Line(BaseModel):
    id: str
    plant_id: str
    name: str
    process: str
    part: str
    cameras: int = 2
    machines: int = 3


class SensorPoint(BaseModel):
    t: str
    v: float


class SensorSeries(BaseModel):
    id: str
    name: str
    unit: str
    spec_low: float | None = None
    spec_high: float | None = None
    baseline: float
    std: float
    points: list[SensorPoint]
    deviation_z: float = 0.0
    out_of_spec: int = 0


class BatchRecord(BaseModel):
    id: str
    material: str
    supplier: str
    lot: str
    received: str
    certificate: str
    moisture_pct: float | None = None
    hydrogen_ppm: float | None = None
    notes: str = ""


class MaintenanceRecord(BaseModel):
    id: str
    machine: str
    kind: str
    at: str
    technician: str
    note: str
    days_before_defect: int


class HistoricalCase(BaseModel):
    id: str
    at: str
    defect: str
    cause: str
    line: str
    batch: str
    similarity: float = 0.0
    resolution_hours: float = 0.0
    notes: str = ""


class Evidence(BaseModel):
    id: str
    kind: Literal["image", "chart", "record", "similar", "trace", "finding"]
    title: str
    detail: str
    source: str
    at: str | None = None
    strength: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)


class HypothesisFactor(BaseModel):
    frequency: float = 0.0
    deviation: float = 0.0
    batch_match: float = 0.0
    similarity: float = 0.0
    recurrence: float = 0.0


class Hypothesis(BaseModel):
    id: str
    label: str
    category: str
    summary: str
    score: float
    confidence: float
    rank: int
    status: Literal["proposed", "accepted", "rejected", "manual"] = "proposed"
    factors: HypothesisFactor
    evidence_ids: list[str] = Field(default_factory=list)
    note: str = ""


class ChainNode(BaseModel):
    id: str
    label: str
    detail: str
    kind: Literal["root", "mechanism", "growth", "failure"] = "mechanism"


class CausalChain(BaseModel):
    nodes: list[ChainNode]
    edges: list[list[str]]
    verdict: str
    confidence: float


class ReportSection(BaseModel):
    id: str
    heading: str
    body: str


class Report(BaseModel):
    id: str
    case_id: str
    version: int = 1
    status: Literal["draft", "in_review", "approved"] = "draft"
    title: str
    summary: str
    sections: list[ReportSection]
    approved_by: str | None = None
    approved_at: str | None = None
    edits: int = 0


class DefectCase(BaseModel):
    id: str
    scenario_id: str
    plant_id: str
    line_id: str
    part: str
    serial: str
    defect_type: str
    severity: Literal["low", "medium", "high", "critical"]
    detected_at: str
    machine_id: str
    batch_id: str
    image_key: str
    bbox: list[float]
    detection_confidence: float
    status: Literal["new", "investigating", "awaiting_review", "approved", "closed"] = "new"
    hours_in_service: float | None = None
    station: str = ""
    shift: str = ""


class Finding(BaseModel):
    id: str
    x: float
    y: float
    depth: int
    title: str
    detail: str
    evidence_id: str
    kind: Literal["surface", "subsurface"]


class Scenario(BaseModel):
    id: str
    title: str
    subtitle: str
    process: str
    defect: str
    part: str
    image_keys: list[str]
    case: DefectCase
    findings: list[Finding]
    sensors: list[SensorSeries]
    batch: BatchRecord
    maintenance: list[MaintenanceRecord]
    history: list[HistoricalCase]
    hypotheses: list[Hypothesis]
    evidence: list[Evidence]
    chain: CausalChain
    trace: list[dict[str, Any]]
    report: Report
    operator_note: str
    provenance: dict[str, Any]
    baseline_hours: float
    current_hours: float


class AuditEvent(BaseModel):
    id: str
    at: str
    actor: str
    action: str
    object: str
    detail: str
    model_version: str = "rootcause-0.9.0"
    data_sources: list[str] = Field(default_factory=list)


class Connector(BaseModel):
    id: str
    name: str
    protocol: str
    category: str
    status: Literal["connected", "available", "simulated", "error"] = "available"
    endpoint: str = ""
    detail: str = ""
    points: int = 0
    last_sync: str | None = None
    phase: str = "1.1"


class Alert(BaseModel):
    id: str
    level: Literal["info", "warning", "critical"]
    title: str
    detail: str
    at: str
    line_id: str
    acknowledged: bool = False


class CorrectiveAction(BaseModel):
    id: str
    case_id: str
    title: str
    owner: str
    due: str
    status: Literal["open", "in_progress", "done"] = "open"
    saving_eur: float = 0.0


class Dashboard(BaseModel):
    investigations_this_week: int
    investigations_delta: float
    median_hours_to_cause: float
    baseline_hours_to_cause: float
    cause_accuracy: float
    scrap_prevented_eur: float
    rework_prevented_eur: float
    engineer_hours_saved: float
    defect_rate_pct: list[dict[str, Any]]
    top_causes: list[dict[str, Any]]
    weekly: list[dict[str, Any]]
    resolution_by_line: list[dict[str, Any]]


class Billing(BaseModel):
    plan: str
    lines: int
    per_line_month_eur: float
    setup_fee_eur: float
    npu_option_eur: float
    npu_enabled: bool
    mrr_eur: float
    next_invoice: str
    invoices: list[dict[str, Any]]


class CompliancePack(BaseModel):
    id: str
    name: str
    standard: str
    status: Literal["ready", "in_progress", "planned"]
    controls: int
    covered: int
    detail: str


class User(BaseModel):
    id: str
    name: str
    role: Literal["quality_manager", "engineer", "operator", "admin"] = "engineer"
    line_ids: list[str] = Field(default_factory=list)
    initials: str = ""


class Pack(BaseModel):
    meta: dict[str, Any]
    plants: list[Plant]
    lines: list[Line]
    scenarios: list[Scenario]
    connectors: list[Connector]
    audits: list[AuditEvent]
    dashboard: Dashboard
    alerts: list[Alert]
    actions: list[CorrectiveAction]
    billing: Billing
    compliance: list[CompliancePack]
    users: list[User]
    connector_library: list[dict[str, Any]]
    sharing: dict[str, Any]


class RejectRequest(BaseModel):
    hypothesis_id: str
    reason: str
    actor: str = "M. Weber"
    note: str = ""


class AcceptRequest(BaseModel):
    hypothesis_id: str
    actor: str = "M. Weber"
    note: str = ""


class ManualCauseRequest(BaseModel):
    label: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    actor: str = "M. Weber"


class ApprovalRequest(BaseModel):
    actor: str = "M. Weber"
    scope: str = "report"
    note: str = ""


class ReportPatch(BaseModel):
    title: str | None = None
    summary: str | None = None
    sections: list[ReportSection] | None = None
    actor: str = "M. Weber"


class InvestigationResult(BaseModel):
    case: DefectCase
    hypotheses: list[Hypothesis]
    chain: CausalChain
    trace: list[dict[str, Any]]
    evidence: list[Evidence]
    report: Report


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()
