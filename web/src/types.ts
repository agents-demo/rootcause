export interface Plant {
  id: string;
  name: string;
  site: string;
  country: string;
  timezone: string;
}

export interface Line {
  id: string;
  plant_id: string;
  name: string;
  process: string;
  part: string;
  cameras: number;
  machines: number;
}

export interface SensorPoint {
  t: string;
  v: number;
}

export interface SensorSeries {
  id: string;
  name: string;
  unit: string;
  spec_low: number | null;
  spec_high: number | null;
  baseline: number;
  std: number;
  points: SensorPoint[];
  deviation_z: number;
  out_of_spec: number;
}

export interface BatchRecord {
  id: string;
  material: string;
  supplier: string;
  lot: string;
  received: string;
  certificate: string;
  moisture_pct?: number | null;
  hydrogen_ppm?: number | null;
  notes: string;
}

export interface MaintenanceRecord {
  id: string;
  machine: string;
  kind: string;
  at: string;
  technician: string;
  note: string;
  days_before_defect: number;
}

export interface HistoricalCase {
  id: string;
  at: string;
  defect: string;
  cause: string;
  line: string;
  batch: string;
  similarity: number;
  resolution_hours: number;
  notes: string;
}

export interface SignalFinding {
  id: string;
  label: string;
  unit: string;
  from: number;
  to: number;
  change_pct: number;
  direction: "up" | "down" | "stable";
  monotonic: number;
  z: number;
  verdict: string;
}

export interface CaseAnalysis {
  summary: string;
  signals: SignalFinding[];
  prevention: string[];
  falsifiers: string[];
  csv_count: number;
}

export interface CaseAttachment {
  id: string;
  name: string;
  mime: string;
  size: number;
  data_url: string;
}

export interface Evidence {
  id: string;
  kind: "image" | "chart" | "record" | "similar" | "trace" | "finding";
  title: string;
  detail: string;
  source: string;
  at?: string | null;
  strength: number;
  payload: Record<string, unknown>;
}

export interface Factors {
  frequency: number;
  deviation: number;
  batch_match: number;
  similarity: number;
  recurrence: number;
}

export type HypothesisStatus = "proposed" | "accepted" | "rejected" | "manual";

export interface Hypothesis {
  id: string;
  label: string;
  category: string;
  summary: string;
  score: number;
  confidence: number;
  rank: number;
  status: HypothesisStatus;
  factors: Factors;
  evidence_ids: string[];
  note: string;
}

export interface ChainNode {
  id: string;
  label: string;
  detail: string;
  kind: "root" | "mechanism" | "growth" | "failure";
}

export interface CausalChain {
  nodes: ChainNode[];
  edges: string[][];
  verdict: string;
  confidence: number;
}

export interface ReportSection {
  id: string;
  heading: string;
  body: string;
}

export interface Report {
  id: string;
  case_id: string;
  version: number;
  status: "draft" | "in_review" | "approved";
  title: string;
  summary: string;
  sections: ReportSection[];
  approved_by?: string | null;
  approved_at?: string | null;
  edits: number;
}

export type CaseStatus = "new" | "investigating" | "awaiting_review" | "approved" | "closed";

export interface DefectCase {
  id: string;
  scenario_id: string;
  plant_id: string;
  line_id: string;
  part: string;
  serial: string;
  defect_type: string;
  severity: "low" | "medium" | "high" | "critical";
  detected_at: string;
  machine_id: string;
  batch_id: string;
  image_key: string;
  bbox: number[];
  detection_confidence: number;
  status: CaseStatus;
  hours_in_service?: number | null;
  station: string;
  shift: string;
}

export interface Finding {
  id: string;
  x: number;
  y: number;
  depth: number;
  title: string;
  detail: string;
  evidence_id: string;
  kind: "surface" | "subsurface";
}

export interface TraceStep {
  step: number;
  agent: string;
  tool: string;
  title: string;
  detail: string;
  status: "done" | "waiting" | "running";
  evidence: string[];
  ms: number;
}

export interface Scenario {
  id: string;
  title: string;
  subtitle: string;
  process: string;
  defect: string;
  part: string;
  image_keys: string[];
  case: DefectCase;
  findings: Finding[];
  sensors: SensorSeries[];
  batch: BatchRecord;
  maintenance: MaintenanceRecord[];
  history: HistoricalCase[];
  hypotheses: Hypothesis[];
  evidence: Evidence[];
  chain: CausalChain;
  trace: TraceStep[];
  report: Report;
  operator_note: string;
  provenance: Record<string, string>;
  attachments?: CaseAttachment[];
  analysis?: CaseAnalysis;
  baseline_hours: number;
  current_hours: number;
}

export interface AuditEvent {
  id: string;
  at: string;
  actor: string;
  action: string;
  object: string;
  detail: string;
  model_version: string;
  data_sources: string[];
}

export interface Connector {
  id: string;
  name: string;
  protocol: string;
  category: string;
  status: "connected" | "available" | "simulated" | "error";
  endpoint: string;
  detail: string;
  points: number;
  last_sync?: string | null;
  phase: string;
}

export interface Alert {
  id: string;
  level: "info" | "warning" | "critical";
  title: string;
  detail: string;
  at: string;
  line_id: string;
  acknowledged: boolean;
}

export interface CorrectiveAction {
  id: string;
  case_id: string;
  title: string;
  owner: string;
  due: string;
  status: "open" | "in_progress" | "done";
  saving_eur: number;
}

export interface DashboardData {
  investigations_this_week: number;
  investigations_delta: number;
  median_hours_to_cause: number;
  baseline_hours_to_cause: number;
  cause_accuracy: number;
  scrap_prevented_eur: number;
  rework_prevented_eur: number;
  engineer_hours_saved: number;
  defect_rate_pct: Record<string, number | string>[];
  top_causes: { cause: string; count: number; share: number }[];
  weekly: { week: string; investigations: number; hours: number; baseline: number }[];
  resolution_by_line: { line: string; hours: number; cases: number }[];
}

export interface Billing {
  plan: string;
  lines: number;
  per_line_month_eur: number;
  proactive_per_line_eur?: number;
  setup_fee_eur: number;
  npu_option_eur: number;
  npu_enabled: boolean;
  mrr_eur: number;
  next_invoice: string;
  invoices: { id: string; date: string; amount: number; status: string }[];
}

export interface CompliancePack {
  id: string;
  name: string;
  standard: string;
  status: "ready" | "in_progress" | "planned";
  controls: number;
  covered: number;
  detail: string;
}

export interface User {
  id: string;
  name: string;
  role: "quality_manager" | "engineer" | "operator" | "admin";
  line_ids: string[];
  initials: string;
}

export interface Pack {
  meta: {
    version: string;
    generated: string;
    anchor: string;
    seed: number;
    scenario_ids: string[];
    model: string;
    note: string;
  };
  plants: Plant[];
  lines: Line[];
  scenarios: Scenario[];
  connectors: Connector[];
  audits: AuditEvent[];
  dashboard: DashboardData;
  alerts: Alert[];
  actions: CorrectiveAction[];
  billing: Billing;
  compliance: CompliancePack[];
  users: User[];
  connector_library: {
    id: string;
    name: string;
    systems: string;
    status: string;
    phase: string;
  }[];
  sharing: {
    enabled: boolean;
    scope: string;
    factories: number;
    shared_causes: number;
    note: string;
  };
  proactive: ProactivePack;
}

// ------------------------------------------------------------------ proactive quality
export type SignalKind =
  | "spc"
  | "ewma"
  | "cusum"
  | "change_point"
  | "batch"
  | "maintenance"
  | "setup"
  | "golden_run"
  | "recurrence"
  | "data_quality"
  | "coverage"
  | "environment"
  | "near_miss"
  | "first_off";

export interface RiskSignal {
  id: string;
  kind: SignalKind;
  at: string;
  line_id: string;
  parameter: string;
  value?: number | null;
  baseline?: number | null;
  z?: number | null;
  severity: "info" | "warning" | "high" | "critical";
  detail: string;
  evidence_id: string;
  cleared: boolean;
}

export interface SuggestedCheck {
  id: string;
  label: string;
  why: string;
  owner: string;
  done: boolean;
}

export interface ImpactEstimate {
  parts_at_risk: number;
  scrap_avoided_eur: number;
  engineer_hours: number;
  cost_eur: number;
  note: string;
}

export type RecommendationKind =
  | "hold_batch"
  | "extra_sampling"
  | "first_off"
  | "check_dryer"
  | "check_calibration"
  | "pull_maintenance"
  | "supplier_notice"
  | "verify_parameter";

export interface Recommendation {
  id: string;
  watch_id: string;
  kind: RecommendationKind;
  title: string;
  detail: string;
  impact: ImpactEstimate;
  status: "proposed" | "approved" | "rejected" | "executed" | "verified";
  approved_by?: string | null;
  approved_at?: string | null;
  executed_at?: string | null;
  verified_at?: string | null;
  reason: string;
  pattern_id: string;
}

export type WatchStatus = "watching" | "triage" | "investigating" | "snoozed" | "dismissed" | "converted";

export interface WatchCase {
  id: string;
  plant_id: string;
  line_id: string;
  title: string;
  summary: string;
  status: WatchStatus;
  severity: "info" | "warning" | "high" | "critical";
  risk_score: number;
  confidence: number;
  opened_at: string;
  updated_at: string;
  owner: string;
  sla_due: string;
  group_key: string;
  pattern_id: string;
  pattern_name: string;
  pattern_version?: string;
  signal_count: number;
  signals: RiskSignal[];
  evidence_ids: string[];
  suggested_checks: SuggestedCheck[];
  recommendation_ids: string[];
  linked_case_id?: string | null;
  triage_note: string;
  outcome: "pending" | "converted" | "true_risk" | "false_alarm" | "operational";
  outcome_reason: string;
  outcome_at?: string | null;
  outcome_actor?: string | null;
  useful?: boolean | null;
}

export interface RiskPattern {
  id: string;
  version: string;
  name: string;
  cause_family: string;
  description: string;
  trigger: string;
  historical_precision: number;
  checks: string[];
  recommendation_kinds: string[];
  status: "active" | "shadow" | "retired";
  owner: string;
  last_validated: string;
  card: Record<string, unknown>;
}

export interface ThresholdRule {
  id: string;
  line_id: string;
  parameter: string;
  method: "spc" | "ewma" | "cusum" | "change_point" | "batch" | "maintenance" | "data_quality";
  limit: number;
  direction: "above" | "below" | "either";
  owner: string;
  version: string;
  active: boolean;
  notes: string;
}

export interface ScheduleSettings {
  enabled: boolean;
  stop_switch: boolean;
  interval_minutes: number;
  mode: "shadow" | "live";
  false_alarm_budget: number;
  max_alerts_per_shift: number;
  quiet_hours: string;
  digest_mode: boolean;
  coverage_floor: number;
  triage_sla_min: number;
  reconstruction_target_min: number;
  webhook_url: string;
  webhook_secret?: string;
  notification_roles: string[];
  champion: string;
  challenger: string;
}

export interface ProactiveSettings {
  schedule: ScheduleSettings;
  thresholds: ThresholdRule[];
  stop_reasons: string[];
  contract_note: string;
  escalation_sla: string;
}

export interface ScanRun {
  id: string;
  at: string;
  mode: string;
  lines_scanned: number;
  signals: number;
  watches_opened: number;
  suppressed: number;
  duration_ms: number;
  status: "ok" | "degraded" | "failed";
  lag_seconds: number;
  note: string;
}

export interface ShiftBrief {
  id: string;
  at: string;
  shift: string;
  line_ids: string[];
  title: string;
  summary: string;
  top_risks: { watch_id: string; title: string; severity: string; action: string }[];
  open_cases: { case_id: string; title: string; status: string }[];
  actions_due: { action_id: string; title: string; owner: string; due: string }[];
  fixed_not_verified: { case_id: string; title: string; note: string }[];
  coverage_note: string;
  generated_by: string;
}

export interface Notification {
  id: string;
  at: string;
  kind: "watch" | "recommendation" | "followup" | "data_quality" | "system";
  severity: "info" | "warning" | "high" | "critical";
  title: string;
  detail: string;
  watch_id?: string | null;
  role: string;
  delivered: boolean;
  read: boolean;
  dedup_key: string;
}

export interface ExposurePart {
  serial: string;
  part: string;
  line_id: string;
  shift: string;
  customer: string;
  status: "in_plant" | "in_transit" | "at_customer" | "fitted";
  containment: "hold" | "inspect" | "release" | "unknown";
}

export interface Exposure {
  id: string;
  watch_id: string;
  batch_id: string;
  generated_at: string;
  parts: ExposurePart[];
  customers: number;
  estimated_eur: number;
  status: "open" | "contained" | "released";
  note: string;
}

export interface FollowUp {
  id: string;
  case_id: string;
  action_id: string;
  title: string;
  window_start: string;
  window_end: string;
  status: "monitoring" | "verified" | "reopened" | "closed";
  parameter_returned: boolean;
  defect_rate_delta: number;
  recurrence_watch_id?: string | null;
  pattern_id?: string;
  note: string;
}

export interface Coverage {
  line_id: string;
  expected_sources: number;
  fresh_sources: number;
  pct: number;
  stale: string[];
  status: "ok" | "degraded" | "blind";
  last_scan: string;
}

export interface ProactiveMetrics {
  watch_precision: number;
  watch_recall: number;
  alerts_per_line_shift: number;
  median_triage_min: number;
  containment_conversion: number;
  defects_prevented_month: number;
  escaped_defects: number;
  coverage_pct: number;
  reconstruction_min: number;
  alert_volume_growth: number;
  cost_per_useful_alert_eur: number;
  useful_watches: number;
  total_watches: number;
  open_watches?: number;
  alerts_open?: number;
  dismissal_rate?: number;
  snooze_rate?: number;
  followups?: {
    total: number;
    verified: number;
    reopened: number;
    monitoring: number;
    verification_rate: number;
    reopened_ids: (string | null)[];
  };
  coverage?: { floor: number; coverage_pct: number; below_floor: string[]; status: string };
  store?: { watches: number; useful: number; outcomes: number; precision: number };
  drift?: { status: string; delta?: number; detail: string };
  weekly: { week: string; precision: number; alerts: number; triage: number; conversion: number; useful: number; total: number }[];
  channels: { name: string; delivered: number; opened: number; note: string }[];
}

export interface ModelCard {
  id: string;
  name: string;
  version: string;
  kind: "threshold" | "spc" | "ewma" | "cusum" | "change_point" | "risk_score" | "research";
  inputs: string[];
  limits: string[];
  failure_modes: string[];
  owner: string;
  last_validated: string;
  status: "champion" | "challenger" | "retired" | "research";
}

export interface ResearchGate {
  question: string;
  status: "not_started" | "data_audit" | "shadow" | "stopped" | "approved";
  decision: string;
  data_months: number;
  events: number;
  required_events: number;
  model_lift: number;
  lead_time_hours: number;
  false_alarm_rate: number;
  cost_of_errors_eur: number;
  checks: { id: string; label: string; done: boolean; note: string }[];
  updated_at: string;
  note: string;
  baseline_auc?: number;
  model_auc?: number;
  precision?: number;
  recall?: number;
}

export interface ProactivePack {
  settings: ProactiveSettings;
  watches: WatchCase[];
  patterns: RiskPattern[];
  recommendations: Recommendation[];
  scan_runs: ScanRun[];
  briefs: ShiftBrief[];
  notifications: Notification[];
  exposures: Exposure[];
  followups: FollowUp[];
  coverage: Coverage[];
  metrics: ProactiveMetrics;
  model_cards: ModelCard[];
  research: ResearchGate;
  health?: { status: string; last_scan: string | null; lag_seconds: number | null; detail: string };
  replay?: {
    rows: { scenario: string; signals: number; expected_risk: boolean; opened: boolean; line: string }[];
    precision: number;
    recall: number;
    true_positive: number;
    false_positive: number;
    false_negative: number;
    note: string;
  };
  tuning?: { action: string; reason: string; suggestion: string; requires_approval: boolean }[];
  queue?: { queued: number; dropped: number; max_items: number };
}

export interface FactorRow {
  key: keyof Factors;
  label: string;
  value: number;
  weight: number;
}
