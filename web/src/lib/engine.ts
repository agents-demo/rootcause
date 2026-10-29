import type {
  CausalChain,
  FactorRow,
  Factors,
  Hypothesis,
  Scenario,
  TraceStep,
} from "../types";

export const WEIGHTS: Record<keyof Factors, number> = {
  frequency: 0.28,
  deviation: 0.3,
  batch_match: 0.18,
  similarity: 0.18,
  recurrence: 0.06,
};

export const FACTOR_LABELS: Record<keyof Factors, string> = {
  frequency: "Known failure-mode frequency",
  deviation: "Machine deviation magnitude",
  batch_match: "Batch / material match",
  similarity: "Similar-case match",
  recurrence: "Recurrence on this line",
};

const REJECTION_FACTOR = 0.16;
const UNKNOWN_SCORE = 0.3;

const clamp = (v: number) => Math.max(0, Math.min(1, Number(v) || 0));

export function rawScore(h: Hypothesis): number {
  let score = 0;
  (Object.keys(WEIGHTS) as (keyof Factors)[]).forEach((key) => {
    score += WEIGHTS[key] * clamp(h.factors[key]);
  });
  score /= Object.values(WEIGHTS).reduce((a, b) => a + b, 0);
  if (h.status === "rejected") score *= REJECTION_FACTOR;
  if (h.status === "manual") score = Math.max(score, 0.34);
  return Math.round(score * 10000) / 10000;
}

export function rankHypotheses(
  hypotheses: Hypothesis[],
  rejected: string[] = [],
): Hypothesis[] {
  const rejectedSet = new Set(rejected);
  const ranked = hypotheses.map((h) => {
    const next: Hypothesis = { ...h, factors: { ...h.factors } };
    if (rejectedSet.has(h.id)) next.status = "rejected";
    else if (next.status === "rejected") next.status = "proposed";
    next.score = rawScore(next);
    return next;
  });
  ranked.sort((a, b) => b.score - a.score || a.label.localeCompare(b.label));
  const max = Math.max(...ranked.map((h) => h.score), 0);
  const temperature = Math.max(0.11, 0.22 * max);
  const exps = ranked.map((h) => Math.exp(h.score / temperature));
  const unknown = Math.exp(UNKNOWN_SCORE / temperature);
  const total = exps.reduce((a, b) => a + b, 0) + unknown;
  ranked.forEach((h, i) => {
    h.rank = i + 1;
    h.confidence = Math.round((100 * exps[i]) / total * 10) / 10;
  });
  return ranked;
}

export function unknownConfidence(hyps: Hypothesis[]): number {
  return Math.max(0, Math.round((100 - hyps.reduce((a, h) => a + h.confidence, 0)) * 10) / 10);
}

export function factorRows(h: Hypothesis): FactorRow[] {
  return (Object.keys(WEIGHTS) as (keyof Factors)[]).map((key) => ({
    key,
    label: FACTOR_LABELS[key],
    value: h.factors[key],
    weight: WEIGHTS[key],
  }));
}

function byKind(s: Scenario, kind: string) {
  return s.evidence.filter((e) => e.kind === kind).map((e) => e.id);
}

export function buildTrace(s: Scenario, rejected: string[]): TraceStep[] {
  const outOfSpec = s.sensors.filter((x) => x.out_of_spec > 0).length;
  const charts = byKind(s, "chart");
  const records = byKind(s, "record");
  const similar = byKind(s, "similar");
  const images = byKind(s, "image");

  const steps: TraceStep[] = [
    {
      step: 1,
      agent: "Intake",
      tool: "detector.detect",
      title: `Defect confirmed: ${s.case.defect_type}`,
      detail: `Camera confidence ${s.case.detection_confidence.toFixed(2)}. Case ${s.case.id} opened at ${s.case.station}.`,
      status: "done",
      evidence: images.slice(0, 1),
      ms: 240,
    },
    {
      step: 2,
      agent: "Data",
      tool: "opcua.read_window",
      title: `Pulled ${s.sensors.length} machine parameters`,
      detail: `${outOfSpec} parameters out of spec in the window around the defect.`,
      status: "done",
      evidence: charts,
      ms: 610,
    },
    {
      step: 3,
      agent: "Data",
      tool: "mes.batch",
      title: `Linked batch ${s.batch.id}`,
      detail: `${s.batch.material} from ${s.batch.supplier}. ${s.batch.notes || "No material exception."}`,
      status: "done",
      evidence: records.slice(0, 1),
      ms: 180,
    },
    {
      step: 4,
      agent: "Data",
      tool: "cmms.history",
      title: `Found ${s.maintenance.length} maintenance events`,
      detail: "Recent maintenance is included when it can explain a process change.",
      status: "done",
      evidence: records,
      ms: 150,
    },
    {
      step: 5,
      agent: "Reasoner",
      tool: "similar.search",
      title: `Matched ${s.history.length} historical cases`,
      detail: "Similarity uses cause, material batch and time-to-resolution features.",
      status: "done",
      evidence: similar,
      ms: 320,
    },
  ];

  const ranked = rankHypotheses(s.hypotheses, rejected);
  steps.push({
    step: 6,
    agent: "Reasoner",
    tool: "cause.rank",
    title: `Ranked ${ranked.length} causes`,
    detail: `Leading cause: ${ranked[0]?.label ?? "none"} at ${ranked[0]?.confidence ?? 0}%. Subsurface evidence is still unreviewed.`,
    status: "done",
    evidence: ranked[0]?.evidence_ids.slice(0, 2) ?? [],
    ms: 430,
  });

  let step = 7;
  rejected.forEach((id) => {
    const h = s.hypotheses.find((x) => x.id === id);
    steps.push({
      step: step++,
      agent: "Engineer",
      tool: "engineer.reject",
      title: `Rejected: ${h?.label ?? id}`,
      detail: "The engineer rejected this cause; its weight is reduced and the ranking is recomputed.",
      status: "done",
      evidence: [],
      ms: 1200,
    });
    const top = rankHypotheses(s.hypotheses, rejected)[0];
    steps.push({
      step: step++,
      agent: "Reasoner",
      tool: "cause.rerank",
      title: `Re-ranked: ${top?.label ?? "no candidate"} now leads`,
      detail: `${top?.label} at ${top?.confidence}% confidence. The correction is saved to the case.`,
      status: "done",
      evidence: top?.evidence_ids.slice(0, 2) ?? [],
      ms: 520,
    });
  });

  steps.push({
    step: step++,
    agent: "Guard",
    tool: "engineer.check",
    title: "Engineer sign-off required",
    detail: "No cause is approved automatically. Accept or reject the remaining candidates.",
    status: "waiting",
    evidence: [],
    ms: 0,
  });
  return steps;
}

export function chainFor(s: Scenario, hyps: Hypothesis[]): CausalChain {
  const top = hyps[0];
  return {
    ...s.chain,
    confidence:
      top && top.status !== "rejected"
        ? Math.round(Math.min(0.95, top.confidence / 100 + 0.36) * 100) / 100
        : s.chain.confidence,
  };
}

export function investigationFor(
  s: Scenario,
  rejected: string[],
  acceptedId: string | null,
  manual: Hypothesis[],
) {
  const base = [...s.hypotheses, ...manual];
  const ranked = rankHypotheses(base, rejected);
  if (acceptedId) {
    const h = ranked.find((x) => x.id === acceptedId);
    if (h && h.status !== "rejected") h.status = "accepted";
  }
  return {
    hypotheses: ranked,
    unknown: unknownConfidence(ranked),
    trace: buildTrace(s, rejected),
    chain: chainFor(s, ranked),
  };
}

export function acceptedHypothesis(hyps: Hypothesis[]): Hypothesis | null {
  return hyps.find((h) => h.status === "accepted") ?? null;
}

// ------------------------------------------------------------------ formatting
export function fmtDateTime(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}

export function fmtTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const diff = Date.now() - t;
  const mins = Math.round(diff / 60000);
  if (Math.abs(mins) < 1) return "just now";
  if (Math.abs(mins) < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (Math.abs(hours) < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}

export function eur(value: number): string {
  return new Intl.NumberFormat("en-IE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function hours(value: number): string {
  if (value < 1) return `${Math.round(value * 60)} min`;
  if (value < 24) return `${value.toFixed(1)} h`;
  return `${(value / 24).toFixed(1)} d`;
}

export function pct(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function assetUrl(key: string): string {
  return `${import.meta.env.BASE_URL}assets/${key}.svg`;
}

export function classNames(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function severityRank(s: string): number {
  return { low: 0, medium: 1, high: 2, critical: 3 }[s] ?? 0;
}
