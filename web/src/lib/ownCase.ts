import type {
  CaseAttachment,
  CausalChain,
  DashboardData,
  Evidence,
  Hypothesis,
  Pack,
  ProactiveMetrics,
  ProactivePack,
  Report,
  Scenario,
} from "../types";

export type DataMode = "own" | "reference";

export interface OwnCaseInput {
  defect: string;
  part: string;
  lineId: string;
  batchId: string;
  severity: "low" | "medium" | "high" | "critical";
  station: string;
  shift: string;
  description: string;
  cause: string;
  attachments?: CaseAttachment[];
}

function slug(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 40);
}

export function nextCaseId(existing: Scenario[]): string {
  const year = new Date().getFullYear();
  const used = existing
    .map((s) => Number(new RegExp(`^RC-${year}-(\\d+)$`).exec(s.case.id)?.[1] ?? 0))
    .filter((n) => Number.isFinite(n));
  const next = Math.max(0, ...used) + 1;
  return `RC-${year}-${String(next).padStart(4, "0")}`;
}

export function buildOwnCase(input: OwnCaseInput, pack: Pack, existing: Scenario[], actor = "you"): Scenario {
  const id = nextCaseId(existing);
  const now = new Date().toISOString();
  const line = pack.lines.find((l) => l.id === input.lineId) ?? pack.lines[0];
  const lineName = line?.name ?? input.lineId ?? "Line";
  const plantId = line?.plant_id ?? pack.plants[0]?.id ?? "plant-local";
  const causeLabel = input.cause.trim();

  const attachments = input.attachments ?? [];
  const attachmentEvidence: Evidence[] = attachments.map((a, i) => ({
    id: `EV-${String(i + 2).padStart(2, "0")}`,
    kind: a.mime.startsWith("image/") ? "image" : "record",
    title: a.name,
    detail: a.mime.startsWith("image/")
      ? `Uploaded inspection image (${Math.round(a.size / 1024)} kB).`
      : `Uploaded data file (${Math.round(a.size / 1024)} kB).`,
    source: `Uploaded by ${actor}`,
    at: now,
    strength: a.mime.startsWith("image/") ? 0.7 : 0.6,
    payload: { name: a.name, mime: a.mime, size: a.size },
  }));

  const evidence: Evidence = {
    id: "EV-01",
    kind: "finding",
    title: "Engineer note",
    detail: input.description.trim(),
    source: `Entered by ${actor}`,
    at: now,
    strength: 0.5,
    payload: {},
  };

  const hypothesis: Hypothesis = {
    id: causeLabel ? `own_${slug(causeLabel)}` : "undetermined",
    label: causeLabel || "Undetermined — add a cause",
    category: "manual",
    summary: causeLabel
      ? "Entered by the engineer. No machine series, image or batch data is attached yet."
      : "No candidate cause yet. Add a cause with the reasoning, then accept or reject it.",
    score: 0.2,
    confidence: 0,
    rank: 1,
    status: "proposed",
    factors: { frequency: 0.1, deviation: 0.1, batch_match: 0.05, similarity: 0.05, recurrence: 0.05 },
    evidence_ids: ["EV-01", ...attachmentEvidence.map((e) => e.id)],
    note: "User-entered case",
  };

  const chain: CausalChain = {
    nodes: [
      { id: "root", label: causeLabel || "Under investigation", detail: causeLabel ? "Working hypothesis" : "No cause yet", kind: "root" },
      { id: "failure", label: input.defect.trim(), detail: input.part.trim(), kind: "failure" },
    ],
    edges: [["root", "failure"]],
    verdict: causeLabel ? "Working hypothesis, not a verdict" : "Insufficient evidence",
    confidence: 0.3,
  };

  const report: Report = {
    id: `RPT-${id}`,
    case_id: id,
    version: 1,
    status: "draft",
    title: `${input.defect.trim()} — ${input.part.trim()}`,
    summary: input.description.trim(),
    sections: [
      { id: "s1", heading: "What happened", body: input.description.trim() },
      {
        id: "s2",
        heading: "Evidence",
        body: attachments.length
          ? `One engineer note and ${attachments.length} uploaded file${attachments.length === 1 ? "" : "s"} are attached. ${attachments.map((a) => a.name).join(", ")}.`
          : "One engineer note is attached. Add machine, batch or image evidence before sign-off.",
      },
      {
        id: "s3",
        heading: "Decision",
        body: causeLabel ? `Working hypothesis: ${causeLabel}. The engineer signs.` : "No cause accepted yet.",
      },
    ],
    edits: 0,
  };

  return {
    id,
    title: input.defect.trim(),
    subtitle: `${input.part.trim()} · ${lineName}`,
    process: lineName,
    defect: input.defect.trim(),
    part: input.part.trim(),
    image_keys: [],
    case: {
      id,
      scenario_id: id,
      plant_id: plantId,
      line_id: line?.id ?? input.lineId,
      part: input.part.trim(),
      serial: "",
      defect_type: input.defect.trim(),
      severity: input.severity,
      detected_at: now,
      machine_id: "",
      batch_id: input.batchId.trim() || "—",
      image_key: "",
      bbox: [0, 0, 0, 0],
      detection_confidence: 0,
      status: "investigating",
      hours_in_service: null,
      station: input.station.trim() || "Entered manually",
      shift: input.shift,
    },
    findings: [],
    sensors: [],
    batch: {
      id: input.batchId.trim() || "—",
      material: "",
      supplier: "",
      lot: input.batchId.trim(),
      received: now.slice(0, 10),
      certificate: "",
      moisture_pct: null,
      hydrogen_ppm: null,
      notes: "Entered by hand. No supplier record imported.",
    },
    maintenance: [],
    history: [],
    hypotheses: [hypothesis],
    evidence: [evidence, ...attachmentEvidence],
    attachments,
    chain,
    trace: [],
    report,
    operator_note: input.description.trim(),
    provenance: {
      data: `Entered by ${actor} in this browser`,
      model: "manual entry — no synthetic records",
      date: now,
      note: "No plant connection. This case lives in your workspace, not the reference pack.",
    },
    baseline_hours: 0,
    current_hours: 0,
  };
}

function zeroMetrics(metrics: ProactiveMetrics): ProactiveMetrics {
  const out: Record<string, unknown> = { ...metrics };
  for (const key of Object.keys(out)) {
    if (typeof out[key] === "number") out[key] = 0;
  }
  if (out.followups && typeof out.followups === "object") {
    out.followups = { total: 0, verified: 0, reopened: 0 };
  }
  return out as unknown as ProactiveMetrics;
}

function emptyDashboard(caseCount: number): DashboardData {
  return {
    investigations_this_week: caseCount,
    investigations_delta: 0,
    median_hours_to_cause: 0,
    baseline_hours_to_cause: 0,
    cause_accuracy: 0,
    scrap_prevented_eur: 0,
    rework_prevented_eur: 0,
    engineer_hours_saved: 0,
    defect_rate_pct: [],
    top_causes: [],
    weekly: [],
    resolution_by_line: [],
  };
}

function emptyProactive(ref: ProactivePack): ProactivePack {
  return {
    ...ref,
    watches: [],
    notifications: [],
    exposures: [],
    recommendations: [],
    briefs: [],
    followups: [],
    scan_runs: [],
    coverage: [],
    metrics: zeroMetrics(ref.metrics),
    health: {
      status: "ok",
      last_scan: null,
      lag_seconds: null,
      detail: "My workspace: no proactive scan runs without a connected line.",
    },
  };
}

export function buildOwnPack(reference: Pack, ownCases: Scenario[]): Pack {
  return {
    ...reference,
    meta: {
      ...reference.meta,
      seed: 0,
      note: "User-entered cases in this browser. No plant connection.",
    },
    scenarios: ownCases,
    alerts: [],
    actions: [],
    audits: [],
    dashboard: emptyDashboard(ownCases.length),
    proactive: emptyProactive(reference.proactive),
  };
}
