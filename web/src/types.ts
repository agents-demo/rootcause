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
}

export interface FactorRow {
  key: keyof Factors;
  label: string;
  value: number;
  weight: number;
}
