import type { ProactivePack, Scenario, WatchCase } from "../types";

export interface AskResult {
  answer: string;
  citations: string[];
  refused?: boolean;
}

interface AskContext {
  scenario?: Scenario;
  watch?: WatchCase;
  proactive?: ProactivePack;
  role?: string;
}

const CONTROL = /stop the line|change the setpoint|adjust the setpoint|reject the part automatically|control the line|disable the safety/i;
const PREDICT = /predict|failure probability|remaining useful life|when will it fail/i;
const CAUSE = /why|root cause|cause|start|initiat|explain/i;
const EVIDENCE = /evidence|proof|data|show me|chart|x-ray|porosity/i;
const NEXT = /what should|next|check|do now|recommend|action/i;
const BATCH = /batch|hold|contain|quarantine|exposure/i;
const COVERAGE = /coverage|blind|data quality|camera offline/i;

const STOP = "I cannot control the line, change a setpoint or reject parts. RootCause recommends; the engineer decides. I can show the evidence or the containment options.";

export function askLocal(query: string, ctx: AskContext): AskResult {
  const q = query.trim();
  if (!q) return { answer: "Ask about a cause, evidence, a check or a containment recommendation.", citations: [] };
  if (CONTROL.test(q)) return { answer: STOP, citations: [], refused: true };

  if (PREDICT.test(q)) {
    return {
      answer: `Prediction is not shipped. The research gate is stopped: the shadow model showed +${(ctx.proactive?.research.model_lift ?? 0.02).toFixed(2)} lift over SPC, below the required +0.05. Use the watchlist for risk signals instead.`,
      citations: ["RG-1", "RG-4", "RG-8"],
      refused: true,
    };
  }

  const watch = ctx.watch;
  if (watch) {
    if (CAUSE.test(q)) {
      return {
        answer: `The watch is “${watch.title}”. ${watch.summary} It is a hypothesis, not a verdict. The strongest signals are ${watch.signals.slice(0, 3).map((s) => s.parameter).join(", ")}. What would falsify it: normal post-change settling or a sensor artefact.`,
        citations: watch.signals.slice(0, 3).map((s) => s.id).concat(watch.evidence_ids.slice(0, 2)),
      };
    }
    if (EVIDENCE.test(q)) {
      return {
        answer: `The watch cites ${watch.evidence_ids.length} evidence ID(s). The clearest are ${watch.evidence_ids.slice(0, 3).join(", ") || "the signals themselves"}. The source and model version are recorded on the watch.`,
        citations: watch.evidence_ids.slice(0, 3),
      };
    }
    if (NEXT.test(q)) {
      return {
        answer: watch.suggested_checks.length
          ? `Next checks: ${watch.suggested_checks.map((c) => c.label).join("; ")}. The engineer owns the decision.`
          : "No checks are defined. Start triage and add a check, or dismiss the watch with a reason.",
        citations: watch.suggested_checks.map((c) => c.id),
      };
    }
    if (BATCH.test(q)) {
      const rec = ctx.proactive?.recommendations.find((r) => r.watch_id === watch.id && (r.kind === "hold_batch" || r.kind === "check_dryer"));
      return rec
        ? { answer: `Recommended containment: ${rec.title}. ${rec.detail} It is ${rec.status}; nothing executes without a named engineer.`, citations: [rec.id] }
        : { answer: "No batch containment is attached to this watch. Use the checks or open the linked case.", citations: [watch.id] };
    }
  }

  const scenario = ctx.scenario;
  if (scenario && (CAUSE.test(q) || EVIDENCE.test(q))) {
    const top = scenario.hypotheses[0];
    return {
      answer: `Leading cause in ${scenario.case.id}: ${top.label} at ${top.confidence.toFixed(0)}%. ${top.summary} Citation: ${top.evidence_ids.slice(0, 3).join(", ")}. The engineer must accept or reject it.`,
      citations: top.evidence_ids.slice(0, 3),
    };
  }

  if (COVERAGE.test(q) && ctx.proactive) {
    const below = ctx.proactive.coverage.filter((c) => c.pct < 0.95);
    return {
      answer: below.length
        ? `Coverage is below the floor on ${below.map((c) => `${c.line_id} (${Math.round(c.pct * 100)}%)`).join(", ")}. No quality risk is scored for stale sources; a data-quality watch is opened instead.`
        : "All lines are above the 95% coverage floor. The scheduler is healthy.",
      citations: below.map((c) => `COV-${c.line_id}`),
    };
  }

  if (ctx.proactive) {
    const open = ctx.proactive.watches.filter((w) => ["watching", "triage", "investigating"].includes(w.status));
    return {
      answer: open.length
        ? `There are ${open.length} open watch(es). The highest risk is ${open[0].title} on ${open[0].line_id.replace("line-", "Line ")}. Ask about a specific watch, or open the watchlist.`
        : "No open watch. Ask about a case, a batch or coverage.",
      citations: open.slice(0, 2).map((w) => w.id),
      refused: true,
    };
  }

  return {
    answer: "I do not have evidence for that in this case. I will not guess. Try asking about a cause, an evidence ID, a suggested check or a containment recommendation.",
    citations: [],
    refused: true,
  };
}
