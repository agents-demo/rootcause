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
    proactive_per_line_eur: float = 0.0
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


# --------------------------------------------------------------------------- proactive quality
class RiskSignal(BaseModel):
    id: str
    kind: Literal[
        "spc",
        "ewma",
        "cusum",
        "change_point",
        "batch",
        "maintenance",
        "setup",
        "golden_run",
        "recurrence",
        "data_quality",
        "coverage",
        "environment",
        "near_miss",
        "first_off",
    ]
    at: str
    line_id: str
    parameter: str
    value: float | None = None
    baseline: float | None = None
    z: float | None = None
    severity: Literal["info", "warning", "high", "critical"] = "warning"
    detail: str
    evidence_id: str = ""
    cleared: bool = False


class SuggestedCheck(BaseModel):
    id: str
    label: str
    why: str
    owner: str = "Manufacturing engineer"
    done: bool = False


class ImpactEstimate(BaseModel):
    parts_at_risk: int = 0
    scrap_avoided_eur: float = 0.0
    engineer_hours: float = 0.0
    cost_eur: float = 0.0
    note: str = "Estimate only, not booked savings."


class Recommendation(BaseModel):
    id: str
    watch_id: str
    kind: Literal[
        "hold_batch",
        "extra_sampling",
        "first_off",
        "check_dryer",
        "check_calibration",
        "pull_maintenance",
        "supplier_notice",
        "verify_parameter",
    ]
    title: str
    detail: str
    impact: ImpactEstimate = Field(default_factory=ImpactEstimate)
    status: Literal["proposed", "approved", "rejected", "executed", "verified"] = "proposed"
    approved_by: str | None = None
    approved_at: str | None = None
    executed_at: str | None = None
    verified_at: str | None = None
    reason: str = ""
    pattern_id: str = ""


class WatchCase(BaseModel):
    id: str
    plant_id: str
    line_id: str
    title: str
    summary: str
    status: Literal["watching", "triage", "investigating", "snoozed", "dismissed", "converted"] = "watching"
    severity: Literal["info", "warning", "high", "critical"] = "warning"
    risk_score: float
    confidence: float
    opened_at: str
    updated_at: str
    owner: str
    sla_due: str
    group_key: str
    pattern_id: str
    pattern_name: str
    pattern_version: str = ""
    signal_count: int
    signals: list[RiskSignal] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    suggested_checks: list[SuggestedCheck] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)
    linked_case_id: str | None = None
    triage_note: str = ""
    outcome: Literal["pending", "converted", "true_risk", "false_alarm", "operational"] = "pending"
    outcome_reason: str = ""
    outcome_at: str | None = None
    outcome_actor: str | None = None
    useful: bool | None = None


class RiskPattern(BaseModel):
    id: str
    version: str
    name: str
    cause_family: str
    description: str
    trigger: str
    historical_precision: float
    checks: list[str] = Field(default_factory=list)
    recommendation_kinds: list[str] = Field(default_factory=list)
    status: Literal["active", "shadow", "retired"] = "active"
    owner: str = "Quality engineering"
    last_validated: str
    card: dict[str, Any] = Field(default_factory=dict)


class ThresholdRule(BaseModel):
    id: str
    line_id: str
    parameter: str
    method: Literal["spc", "ewma", "cusum", "change_point", "batch", "maintenance", "data_quality"]
    limit: float
    direction: Literal["above", "below", "either"] = "either"
    owner: str
    version: str
    active: bool = True
    notes: str = ""


class ScheduleSettings(BaseModel):
    enabled: bool = True
    stop_switch: bool = False
    interval_minutes: int = 15
    mode: Literal["shadow", "live"] = "shadow"
    false_alarm_budget: float = 2.0
    max_alerts_per_shift: int = 10
    quiet_hours: str = "22:00-06:00"
    digest_mode: bool = False
    coverage_floor: float = 0.95
    triage_sla_min: int = 15
    reconstruction_target_min: int = 5
    webhook_url: str = ""
    webhook_secret: str = ""
    notification_roles: list[str] = Field(default_factory=list)
    champion: str = "v1.4"
    challenger: str = "v1.5-shadow"


class ProactiveSettings(BaseModel):
    schedule: ScheduleSettings
    thresholds: list[ThresholdRule]
    stop_reasons: list[str] = Field(default_factory=list)
    contract_note: str = ""
    escalation_sla: str = ""
    pattern_reviews: list[dict[str, Any]] = Field(default_factory=list)


class ScanRun(BaseModel):
    id: str
    at: str
    mode: str
    lines_scanned: int
    signals: int
    watches_opened: int
    suppressed: int
    duration_ms: int
    status: Literal["ok", "degraded", "failed"] = "ok"
    lag_seconds: int = 0
    note: str = ""


class ShiftBrief(BaseModel):
    id: str
    at: str
    shift: str
    line_ids: list[str]
    title: str
    summary: str
    top_risks: list[dict[str, Any]] = Field(default_factory=list)
    open_cases: list[dict[str, Any]] = Field(default_factory=list)
    actions_due: list[dict[str, Any]] = Field(default_factory=list)
    fixed_not_verified: list[dict[str, Any]] = Field(default_factory=list)
    coverage_note: str = ""
    generated_by: str = "RootCause scheduler"


class Notification(BaseModel):
    id: str
    at: str
    kind: Literal["watch", "recommendation", "followup", "data_quality", "system"] = "watch"
    severity: Literal["info", "warning", "high", "critical"] = "warning"
    title: str
    detail: str
    watch_id: str | None = None
    role: str = "quality_manager"
    delivered: bool = True
    read: bool = False
    dedup_key: str = ""


class ExposurePart(BaseModel):
    serial: str
    part: str
    line_id: str
    shift: str
    customer: str
    status: Literal["in_plant", "in_transit", "at_customer", "fitted"] = "in_plant"
    containment: Literal["hold", "inspect", "release", "unknown"] = "hold"


class Exposure(BaseModel):
    id: str
    watch_id: str
    batch_id: str
    generated_at: str
    parts: list[ExposurePart]
    customers: int
    estimated_eur: float
    status: Literal["open", "contained", "released"] = "open"
    note: str = ""


class FollowUp(BaseModel):
    id: str
    case_id: str
    action_id: str
    title: str
    window_start: str
    window_end: str
    status: Literal["monitoring", "verified", "reopened", "closed"] = "monitoring"
    parameter_returned: bool = False
    defect_rate_delta: float = 0.0
    recurrence_watch_id: str | None = None
    pattern_id: str = ""
    note: str = ""


class Coverage(BaseModel):
    line_id: str
    expected_sources: int
    fresh_sources: int
    pct: float
    stale: list[str] = Field(default_factory=list)
    status: Literal["ok", "degraded", "blind"] = "ok"
    last_scan: str = ""


class ProactiveMetrics(BaseModel):
    watch_precision: float
    watch_recall: float
    alerts_per_line_shift: float
    median_triage_min: float
    containment_conversion: float
    defects_prevented_month: int
    escaped_defects: int
    coverage_pct: float
    reconstruction_min: float
    alert_volume_growth: float
    cost_per_useful_alert_eur: float
    useful_watches: int
    total_watches: int
    weekly: list[dict[str, Any]] = Field(default_factory=list)
    channels: list[dict[str, Any]] = Field(default_factory=list)
    drift: dict[str, Any] = Field(default_factory=dict)


class ModelCard(BaseModel):
    id: str
    name: str
    version: str
    kind: Literal["threshold", "spc", "ewma", "cusum", "change_point", "risk_score", "research"] = "threshold"
    inputs: list[str]
    limits: list[str]
    failure_modes: list[str]
    owner: str
    last_validated: str
    status: Literal["champion", "challenger", "retired", "research"] = "champion"


class ResearchGate(BaseModel):
    question: str
    status: Literal["not_started", "data_audit", "shadow", "stopped", "approved"] = "stopped"
    decision: str
    data_months: int
    events: int
    required_events: int
    model_lift: float
    lead_time_hours: float
    false_alarm_rate: float
    cost_of_errors_eur: float
    checks: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: str = ""
    note: str = ""


class ProactivePack(BaseModel):
    settings: ProactiveSettings
    watches: list[WatchCase]
    patterns: list[RiskPattern]
    recommendations: list[Recommendation]
    scan_runs: list[ScanRun]
    briefs: list[ShiftBrief]
    notifications: list[Notification]
    exposures: list[Exposure]
    followups: list[FollowUp]
    coverage: list[Coverage]
    metrics: ProactiveMetrics
    model_cards: list[ModelCard]
    research: ResearchGate
    health: dict[str, Any] = Field(default_factory=dict)
    replay: dict[str, Any] = Field(default_factory=dict)
    tuning: list[dict[str, Any]] = Field(default_factory=list)


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
    proactive: ProactivePack


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
