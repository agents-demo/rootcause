import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type {
  AuditEvent,
  FollowUp,
  Hypothesis,
  Notification,
  Pack,
  ProactivePack,
  Recommendation,
  Report,
  Scenario,
  ShiftBrief,
  WatchCase,
} from "../types";
import { investigationFor, rankHypotheses } from "./engine";

const STORAGE_KEY = "rootcause.demo.v1";

interface Persisted {
  rejected: Record<string, string[]>;
  accepted: Record<string, string>;
  manual: Record<string, Hypothesis[]>;
  reports: Record<string, Report>;
  approvals: Record<string, { actor: string; at: string }>;
  actionsDone: string[];
  alertsAck: string[];
  sharing: boolean;
  baselines: Record<string, number>;
  events: AuditEvent[];
  proactive?: ProactivePack;
}

const EMPTY: Persisted = {
  rejected: {},
  accepted: {},
  manual: {},
  reports: {},
  approvals: {},
  actionsDone: [],
  alertsAck: [],
  sharing: false,
  baselines: {},
  events: [],
};

function loadPersisted(): Persisted {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    return { ...EMPTY, ...(JSON.parse(raw) as Partial<Persisted>) };
  } catch {
    return EMPTY;
  }
}

interface StoreValue {
  pack: Pack | null;
  loading: boolean;
  error: string | null;
  live: boolean;
  scenarioFor: (caseId: string) => Scenario | undefined;
  caseStatus: (caseId: string) => string;
  reportFor: (caseId: string) => Report | undefined;
  investigation: (caseId: string) => ReturnType<typeof investigationFor> | null;
  audits: (caseId?: string) => AuditEvent[];
  rejected: (caseId: string) => string[];
  actionsDone: string[];
  alertsAck: string[];
  baselines: Record<string, number>;
  proactive: ProactivePack | null;
  accept: (caseId: string, hypothesisId: string, actor?: string) => void;
  reject: (caseId: string, hypothesisId: string, reason: string, actor?: string) => void;
  addManual: (caseId: string, label: string, summary: string, actor?: string) => void;
  patchReport: (caseId: string, patch: Partial<Pick<Report, "title" | "summary" | "sections">>, actor?: string) => void;
  approveReport: (caseId: string, actor?: string, note?: string) => void;
  acknowledge: (alertId: string) => void;
  completeAction: (actionId: string) => void;
  setSharing: (enabled: boolean) => void;
  setBaseline: (lineId: string, hours: number) => void;
  reset: () => void;
  resetCase: (caseId: string) => void;
  scanProactive: () => void;
  triageWatch: (watchId: string, note?: string) => void;
  snoozeWatch: (watchId: string, hours?: number) => void;
  dismissWatch: (watchId: string, reason: string, operational?: boolean) => void;
  convertWatch: (watchId: string, caseId: string, reason?: string) => void;
  trueRiskWatch: (watchId: string, reason?: string) => void;
  markCheck: (watchId: string, checkId: string) => void;
  captureNearMiss: (lineId: string, note: string, parameter?: string) => void;
  releaseExposure: (watchId: string, status: "open" | "contained" | "released", note?: string) => void;
  actOnRecommendation: (recId: string, action: "approve" | "reject" | "execute" | "verify", reason?: string) => void;
  readNotification: (id: string) => void;
  readAllNotifications: () => void;
  updateSchedule: (patch: Partial<ProactivePack["settings"]["schedule"]>) => void;
  updateThreshold: (id: string, patch: { limit?: number; active?: boolean; notes?: string }) => void;
  stopProactive: (reason: string) => void;
  startProactive: () => void;
  reviewPattern: (id: string, status: "active" | "shadow" | "retired", note?: string) => void;
  runResearch: () => void;
  verifyFollowup: (id: string, returned: boolean, delta: number) => void;
  generateBrief: (shift: string, lineIds: string[]) => ShiftBrief | null;
  toast: string | null;
  say: (message: string) => void;
}

const StoreContext = createContext<StoreValue | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [pack, setPack] = useState<Pack | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [live, setLive] = useState(false);
  const liveRef = useRef(false);
  const [state, setState] = useState<Persisted>(() => loadPersisted());
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<number | null>(null);

  const apiUrl = useCallback((path: string) => new URL(`api/${path}`, document.baseURI).toString(), []);

  const call = useCallback(
    (path: string, body?: unknown, method = "POST") => {
      if (!liveRef.current) return;
      void fetch(apiUrl(path), {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      }).catch(() => {
        /* the local case remains usable if the connection drops mid-review */
      });
    },
    [apiUrl],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const packRes = await fetch(`${import.meta.env.BASE_URL}demo-pack.json`);
        if (!packRes.ok) throw new Error(`demo pack returned ${packRes.status}`);
        let data = (await packRes.json()) as Pack;
        if (!data.proactive) {
          // A stale service-worker cache may still hold the pre-proactive pack. Fetch around it.
          const fresh = await fetch(`${import.meta.env.BASE_URL}demo-pack.json?refresh=${Date.now()}`);
          if (fresh.ok) data = (await fresh.json()) as Pack;
        }
        if (cancelled) return;
        setPack(data);
        setState((prev) => ({ ...prev, proactive: prev.proactive ?? data.proactive }));
        setLoading(false);

        // If the on-site API is serving this page, hydrate the human decisions from SQLite.
        // The public Pages build is static; probing /api there would only add a 404 to the console.
        const staticHost = location.hostname.endsWith("github.io") || location.protocol === "file:";
        if (staticHost) return;
        try {
          const proactiveRes = await fetch(apiUrl("proactive"));
          if (proactiveRes.ok) {
            const proactive = (await proactiveRes.json()) as ProactivePack;
            if (!cancelled) setState((prev) => ({ ...prev, proactive }));
          }
        } catch {
          /* keep the pack copy */
        }
        try {
          const health = await fetch(apiUrl("health"));
          if (!health.ok) return;
          const results = await Promise.all(
            data.scenarios.map(async (s) => {
              const res = await fetch(apiUrl(`cases/${s.case.id}`));
              if (!res.ok) return null;
              return (await res.json()) as {
                investigation: {
                  hypotheses: Hypothesis[];
                  report: Report;
                };
              };
            }),
          );
          if (cancelled) return;
          const rejected: Record<string, string[]> = {};
          const accepted: Record<string, string> = {};
          const manual: Record<string, Hypothesis[]> = {};
          const reports: Record<string, Report> = {};
          const approvals: Record<string, { actor: string; at: string }> = {};
          results.forEach((result, i) => {
            if (!result) return;
            const caseId = data.scenarios[i].case.id;
            const hyps = result.investigation.hypotheses;
            const rej = hyps.filter((h) => h.status === "rejected").map((h) => h.id);
            if (rej.length) rejected[caseId] = rej;
            const acc = hyps.find((h) => h.status === "accepted");
            if (acc) accepted[caseId] = acc.id;
            const man = hyps.filter((h) => h.status === "manual");
            if (man.length) manual[caseId] = man;
            if (result.investigation.report) {
              reports[caseId] = result.investigation.report;
              if (result.investigation.report.status === "approved" && result.investigation.report.approved_by) {
                approvals[caseId] = {
                  actor: result.investigation.report.approved_by,
                  at: result.investigation.report.approved_at ?? new Date().toISOString(),
                };
              }
            }
          });
          liveRef.current = true;
          setLive(true);
          setState((prev) => ({
            ...prev,
            rejected,
            accepted,
            manual,
            reports,
            approvals,
          }));
        } catch {
          /* static demo: stay offline-first */
        }
      } catch (e: unknown) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiUrl]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* storage may be unavailable in private mode */
    }
  }, [state]);

  useEffect(
    () => () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    },
    [],
  );

  const say = useCallback((message: string) => {
    setToast(message);
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 3200);
  }, []);

  const scenarioFor = useCallback(
    (caseId: string) => pack?.scenarios.find((s) => s.case.id === caseId),
    [pack],
  );

  const eventsFor = useCallback(
    (caseId: string): AuditEvent[] => {
      const current = state.events.filter((e) => e.object === caseId);
      const base = pack?.audits.filter((a) => a.object === caseId) ?? [];
      return [...current, ...base].sort((a, b) => b.at.localeCompare(a.at));
    },
    [pack, state.events],
  );

  const pushEvent = useCallback((event: Omit<AuditEvent, "id" | "at" | "model_version">) => {
    const at = new Date().toISOString();
    const audit: AuditEvent = {
      ...event,
      id: `local-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      at,
      model_version: "rootcause-0.9.0",
    };
    setState((prev) => ({ ...prev, events: [audit, ...prev.events].slice(0, 200) }));
  }, []);

  const accept = useCallback(
    (caseId: string, hypothesisId: string, actor = "M. Weber") => {
      const scenario = scenarioFor(caseId);
      const label =
        scenario?.hypotheses.find((h) => h.id === hypothesisId)?.label ??
        state.manual[caseId]?.find((h) => h.id === hypothesisId)?.label ??
        hypothesisId;
      setState((prev) => ({ ...prev, accepted: { ...prev.accepted, [caseId]: hypothesisId } }));
      call(`cases/${caseId}/accept`, { hypothesis_id: hypothesisId, actor });
      pushEvent({
        actor,
        action: "cause.accepted",
        object: caseId,
        detail: `Accepted cause: ${label}`,
        data_sources: ["opcua", "mes", "quality-history"],
      });
      say(`Cause accepted — ${label}`);
    },
    [call, pushEvent, say, scenarioFor, state.manual],
  );

  const reject = useCallback(
    (caseId: string, hypothesisId: string, reason: string, actor = "M. Weber") => {
      const scenario = scenarioFor(caseId);
      const label =
        scenario?.hypotheses.find((h) => h.id === hypothesisId)?.label ??
        state.manual[caseId]?.find((h) => h.id === hypothesisId)?.label ??
        hypothesisId;
      setState((prev) => {
        const existing = prev.rejected[caseId] ?? [];
        return {
          ...prev,
          rejected: {
            ...prev.rejected,
            [caseId]: existing.includes(hypothesisId) ? existing : [...existing, hypothesisId],
          },
        };
      });
      call(`cases/${caseId}/reject`, { hypothesis_id: hypothesisId, reason, actor });
      pushEvent({
        actor,
        action: "cause.rejected",
        object: caseId,
        detail: `Rejected ${label}: ${reason}`,
        data_sources: ["evidence-review"],
      });
      say(`${label} rejected — the ranking was recomputed`);
    },
    [call, pushEvent, say, scenarioFor, state.manual],
  );

  const addManual = useCallback(
    (caseId: string, label: string, summary: string, actor = "M. Weber") => {
      const id = `manual-${Date.now()}`;
      const manual: Hypothesis = {
        id,
        label,
        category: "manual",
        summary,
        score: 0.34,
        confidence: 0,
        rank: 99,
        status: "manual",
        factors: { frequency: 0.5, deviation: 0.5, batch_match: 0.5, similarity: 0.5, recurrence: 0.5 },
        evidence_ids: [],
        note: "Added by the engineer during review.",
      };
      setState((prev) => ({
        ...prev,
        manual: { ...prev.manual, [caseId]: [...(prev.manual[caseId] ?? []), manual] },
      }));
      call(`cases/${caseId}/manual`, { label, summary, actor });
      pushEvent({
        actor,
        action: "cause.manual",
        object: caseId,
        detail: `Engineer added manual cause: ${label}. ${summary}`,
        data_sources: ["engineer"],
      });
      say(`Manual cause added — ${label}`);
    },
    [call, pushEvent, say],
  );

  const reportFor = useCallback(
    (caseId: string) => {
      return state.reports[caseId] ?? pack?.scenarios.find((s) => s.case.id === caseId)?.report;
    },
    [pack, state.reports],
  );

  const patchReport = useCallback(
    (
      caseId: string,
      patch: Partial<Pick<Report, "title" | "summary" | "sections">>,
      actor = "M. Weber",
    ) => {
      const scenario = scenarioFor(caseId);
      const current = state.reports[caseId] ?? scenario?.report;
      if (!current) return;
      const next: Report = {
        ...current,
        ...patch,
        version: current.version + 1,
        edits: current.edits + 1,
        status: current.status === "approved" ? "in_review" : "in_review",
      };
      setState((prev) => ({ ...prev, reports: { ...prev.reports, [caseId]: next } }));
      call(`reports/${caseId}`, {
        title: next.title,
        summary: next.summary,
        sections: next.sections,
        actor,
      }, "PATCH");
      pushEvent({
        actor,
        action: "report.edited",
        object: caseId,
        detail: `Report v${next.version} edited and sent to review`,
        data_sources: ["case", "evidence"],
      });
      say(`Report v${next.version} saved`);
    },
    [call, pushEvent, say, scenarioFor, state.reports],
  );

  const approveReport = useCallback(
    (caseId: string, actor = "M. Weber", note = "") => {
      const scenario = scenarioFor(caseId);
      const current = state.reports[caseId] ?? scenario?.report;
      if (!current) return;
      const at = new Date().toISOString();
      const next: Report = {
        ...current,
        version: current.version + 1,
        status: "approved",
        approved_by: actor,
        approved_at: at,
      };
      setState((prev) => ({
        ...prev,
        reports: { ...prev.reports, [caseId]: next },
        approvals: { ...prev.approvals, [caseId]: { actor, at } },
      }));
      call(`cases/${caseId}/approve`, { actor, scope: "report", note });
      pushEvent({
        actor,
        action: "report.approved",
        object: caseId,
        detail: `Report v${next.version} approved. ${note}`.trim(),
        data_sources: ["case", "evidence"],
      });
      say("Report approved and stamped");
    },
    [call, pushEvent, say, scenarioFor, state.reports],
  );

  const acknowledge = useCallback(
    (alertId: string) => {
      setState((prev) => ({
        ...prev,
        alertsAck: prev.alertsAck.includes(alertId) ? prev.alertsAck : [...prev.alertsAck, alertId],
      }));
      call(`alerts/${alertId}/ack`);
      say("Alert acknowledged");
    },
    [call, say],
  );

  const completeAction = useCallback(
    (actionId: string) => {
      setState((prev) => ({
        ...prev,
        actionsDone: prev.actionsDone.includes(actionId) ? prev.actionsDone : [...prev.actionsDone, actionId],
      }));
      call(`actions/${actionId}`, undefined, "PATCH");
      say("Corrective action marked complete");
    },
    [call, say],
  );

  const setSharing = useCallback(
    (enabled: boolean) => {
      setState((prev) => ({ ...prev, sharing: enabled }));
      call("sharing", { enabled });
      pushEvent({
        actor: "Site Admin",
        action: enabled ? "sharing.enabled" : "sharing.disabled",
        object: "site",
        detail: enabled
          ? "Cross-factory anonymised pattern sharing enabled. No images, batches or serials leave the site."
          : "Cross-factory sharing disabled.",
        data_sources: ["settings"],
      });
      say(enabled ? "Pattern sharing enabled (anonymised)" : "Pattern sharing disabled");
    },
    [call, pushEvent, say],
  );

  const setBaseline = useCallback(
    (lineId: string, hoursValue: number) => {
      setState((prev) => ({ ...prev, baselines: { ...prev.baselines, [lineId]: hoursValue } }));
      call("baselines", { line_id: lineId, baseline_hours: hoursValue });
      pushEvent({
        actor: "M. Weber",
        action: "baseline.recorded",
        object: lineId,
        detail: `Baseline investigation time set to ${hoursValue} h`,
        data_sources: ["pilot"],
      });
      say("Baseline recorded");
    },
    [call, pushEvent, say],
  );

  const reset = useCallback(() => {
    setState(EMPTY);
    say("Demo reset");
  }, [say]);

  const resetCase = useCallback(
    (caseId: string) => {
      setState((prev) => {
        const rejected = { ...prev.rejected };
        const accepted = { ...prev.accepted };
        const manual = { ...prev.manual };
        const reports = { ...prev.reports };
        const approvals = { ...prev.approvals };
        delete rejected[caseId];
        delete accepted[caseId];
        delete manual[caseId];
        delete reports[caseId];
        delete approvals[caseId];
        return { ...prev, rejected, accepted, manual, reports, approvals };
      });
    },
    [],
  );

  // ---------------------------------------------------------------- proactive actions
  const updateProactive = useCallback(
    (fn: (p: ProactivePack) => void) => {
      setState((prev) => {
        const base = prev.proactive ?? pack?.proactive;
        if (!base) return prev;
        const next = structuredClone(base);
        fn(next);
        return { ...prev, proactive: next };
      });
    },
    [pack],
  );

  const scanProactive = useCallback(() => {
    const base = state.proactive ?? pack?.proactive;
    if (!base) return;
    const now = new Date().toISOString();
    const activeSignals = base.watches.reduce((n, w) => n + (w.status === "watching" || w.status === "triage" ? w.signals.length : 0), 0);
    const run = {
      id: `SCAN-${Date.now()}`,
      at: now,
      mode: base.settings.schedule.mode,
      lines_scanned: pack?.lines.length ?? 4,
      signals: activeSignals || 6,
      watches_opened: 0,
      suppressed: Math.max(0, (activeSignals || 6) - 1),
      duration_ms: 740,
      status: "ok" as const,
      lag_seconds: 0,
      note: "Scan completed. Existing watches were deduplicated by group key; no new watch committed.",
    };
    updateProactive((p) => {
      p.scan_runs = [run, ...p.scan_runs].slice(0, 20);
      p.health = { status: "ok", last_scan: now, lag_seconds: 0, detail: "Scheduler healthy; shadow mode." };
    });
    call("proactive/scan", { mode: base.settings.schedule.mode });
    say(`Scan complete — ${run.signals} signals, ${run.watches_opened} new, ${run.suppressed} suppressed`);
  }, [call, pack, say, state.proactive, updateProactive]);

  const triageWatch = useCallback(
    (watchId: string, note = "Triage started from the watchlist.") => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        if (w) {
          w.status = "triage";
          w.triage_note = note;
          w.updated_at = now;
        }
      });
      call(`watch/${watchId}/triage`, { actor: "M. Weber", note });
      say(`${watchId} is in triage`);
    },
    [call, say, updateProactive],
  );

  const snoozeWatch = useCallback(
    (watchId: string, hours = 4) => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        if (w) {
          w.status = "snoozed";
          w.updated_at = now;
          w.sla_due = new Date(Date.now() + hours * 3600_000).toISOString();
          w.triage_note = `Snoozed for ${hours} h by M. Weber.`;
        }
      });
      call(`watch/${watchId}/snooze`, { hours, actor: "M. Weber" });
      say(`${watchId} snoozed for ${hours} h`);
    },
    [call, say, updateProactive],
  );

  const dismissWatch = useCallback(
    (watchId: string, reason: string, operational = false) => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        if (w) {
          w.status = "dismissed";
          w.outcome = operational ? "operational" : "false_alarm";
          w.outcome_reason = reason;
          w.outcome_at = now;
          w.outcome_actor = "M. Weber";
          w.useful = false;
          w.updated_at = now;
        }
      });
      call(`watch/${watchId}/dismiss`, { actor: "M. Weber", reason, operational });
      say(`${watchId} dismissed — outcome recorded`);
    },
    [call, say, updateProactive],
  );

  const convertWatch = useCallback(
    (watchId: string, caseId: string, reason = "Risk converted to a defect case") => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        if (w) {
          w.status = "converted";
          w.linked_case_id = caseId;
          w.outcome = "converted";
          w.outcome_reason = reason;
          w.outcome_at = now;
          w.outcome_actor = "M. Weber";
          w.useful = true;
          w.updated_at = now;
        }
      });
      call(`watch/${watchId}/convert`, { case_id: caseId, actor: "M. Weber", reason });
      say(`${watchId} converted to ${caseId}`);
    },
    [call, say, updateProactive],
  );

  const trueRiskWatch = useCallback(
    (watchId: string, reason = "Confirmed risk; containment prevented a defect") => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        if (w) {
          w.outcome = "true_risk";
          w.outcome_reason = reason;
          w.outcome_at = now;
          w.outcome_actor = "M. Weber";
          w.useful = true;
          w.updated_at = now;
          if (!w.linked_case_id) w.status = "investigating";
        }
      });
      call(`watch/${watchId}/true-risk`, { actor: "M. Weber", reason });
      say(`${watchId} marked as true risk`);
    },
    [call, say, updateProactive],
  );

  const markCheck = useCallback(
    (watchId: string, checkId: string) => {
      updateProactive((p) => {
        const w = p.watches.find((x) => x.id === watchId);
        const c = w?.suggested_checks.find((x) => x.id === checkId);
        if (c) c.done = true;
      });
      call(`watch/${watchId}/checks/${checkId}`, undefined, "POST");
      say("Check completed");
    },
    [call, say, updateProactive],
  );

  const captureNearMiss = useCallback(
    (lineId: string, note: string, parameter = "Operator observation") => {
      const now = new Date().toISOString();
      const id = `W-NM-${Date.now()}`;
      const signal = {
        id: `NM-${Date.now()}`,
        kind: "near_miss" as const,
        at: now,
        line_id: lineId,
        parameter,
        value: null,
        baseline: null,
        z: null,
        severity: "warning" as const,
        detail: note,
        evidence_id: "",
        cleared: false,
      };
      const pattern = pack?.proactive.patterns.find((p) => p.id === "P-SEAL") ?? pack?.proactive.patterns[0];
      const watch: WatchCase = {
        id,
        plant_id: "plant-de",
        line_id: lineId,
        title: `Near-miss: ${parameter}`,
        summary: note,
        status: "watching",
        severity: "warning",
        risk_score: 0.36,
        confidence: 55,
        opened_at: now,
        updated_at: now,
        owner: "M. Weber",
        sla_due: new Date(Date.now() + 15 * 60000).toISOString(),
        group_key: `${lineId}:near-miss`,
        pattern_id: pattern?.id ?? "P-SEAL",
        pattern_name: pattern?.name ?? "Near-miss watch",
        pattern_version: pattern?.version ?? "",
        signal_count: 1,
        signals: [signal],
        evidence_ids: [],
        suggested_checks: [
          { id: `CH-${Date.now()}`, label: "Inspect the condition and the surrounding parts", why: "A near-miss has no defective part to anchor the investigation.", owner: "Operator", done: false },
        ],
        recommendation_ids: [],
        linked_case_id: null,
        triage_note: "Captured from an operator observation.",
        outcome: "pending",
        outcome_reason: "",
        outcome_at: null,
        outcome_actor: null,
        useful: null,
      };
      updateProactive((p) => {
        p.watches = [watch, ...p.watches];
        p.metrics.open_watches = (p.metrics.open_watches ?? 0) + 1;
      });
      call("proactive/near-miss", { line_id: lineId, note, parameter, actor: "M. Weber" });
      say("Near-miss watch captured");
    },
    [call, pack, say, updateProactive],
  );

  const releaseExposure = useCallback(
    (watchId: string, status: "open" | "contained" | "released", note = "") => {
      updateProactive((p) => {
        const exposure = p.exposures.find((e) => e.watch_id === watchId);
        if (!exposure) return;
        exposure.status = status;
        if (status === "released") exposure.parts.forEach((part) => { part.containment = "release"; });
      });
      call(`exposures/${watchId}/release`, { status, note, actor: "M. Weber" });
      say(`Exposure ${status}`);
    },
    [call, say, updateProactive],
  );

  const actOnRecommendation = useCallback(    (recId: string, action: "approve" | "reject" | "execute" | "verify", reason = "") => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        const r = p.recommendations.find((x) => x.id === recId);
        if (!r) return;
        if (action === "approve") {
          r.status = "approved";
          r.approved_by = "M. Weber";
          r.approved_at = now;
        } else if (action === "reject") {
          r.status = "rejected";
          r.reason = `M. Weber: ${reason}`;
        } else if (action === "execute") {
          r.status = "executed";
          r.executed_at = now;
        } else {
          r.status = "verified";
          r.verified_at = now;
          r.reason = (r.reason + ` Verified: ${reason}`).trim();
        }
      });
      call(`recommendations/${recId}/${action}`, { actor: "M. Weber", reason, note: reason });
      say(`Recommendation ${action}d — ${recId}`);
    },
    [call, say, updateProactive],
  );

  const readNotification = useCallback(
    (id: string) => {
      updateProactive((p) => {
        const n = p.notifications.find((x) => x.id === id);
        if (n) n.read = true;
      });
      call(`notifications/${id}/read`);
    },
    [call, updateProactive],
  );

  const readAllNotifications = useCallback(() => {
    updateProactive((p) => p.notifications.forEach((n) => { n.read = true; }));
    call("notifications/read-all");
    say("All notifications marked read");
  }, [call, say, updateProactive]);

  const updateSchedule = useCallback(
    (patch: Partial<ProactivePack["settings"]["schedule"]>) => {
      updateProactive((p) => {
        p.settings.schedule = { ...p.settings.schedule, ...patch };
      });
      call("proactive/settings", { schedule: patch, actor: "Site Admin" });
      say("Schedule settings saved");
    },
    [call, say, updateProactive],
  );

  const updateThreshold = useCallback(
    (id: string, patch: { limit?: number; active?: boolean; notes?: string }) => {
      updateProactive((p) => {
        const rule = p.settings.thresholds.find((x) => x.id === id);
        if (rule) {
          if (patch.limit !== undefined) rule.limit = patch.limit;
          if (patch.active !== undefined) rule.active = patch.active;
          if (patch.notes !== undefined) rule.notes = patch.notes;
        }
      });
      call(`proactive/thresholds/${id}`, { ...patch, actor: "Site Admin" });
      say("Threshold updated — requires engineer sign-off");
    },
    [call, say, updateProactive],
  );

  const stopProactive = useCallback(
    (reason: string) => {
      const now = new Date().toISOString();
      updateProactive((p) => {
        p.settings.schedule.stop_switch = true;
        p.settings.schedule.enabled = false;
        p.settings.stop_reasons = [...p.settings.stop_reasons, `${now}: ${reason}`];
      });
      call("proactive/stop", { actor: "Site Admin", reason });
      say("Proactive scanning stopped — defect cases are unaffected");
    },
    [call, say, updateProactive],
  );

  const startProactive = useCallback(() => {
    updateProactive((p) => {
      p.settings.schedule.stop_switch = false;
      p.settings.schedule.enabled = true;
    });
    call("proactive/start");
    say("Proactive scanning started");
  }, [call, say, updateProactive]);

  const reviewPattern = useCallback(
    (id: string, status: "active" | "shadow" | "retired", note = "") => {
      updateProactive((p) => {
        const pattern = p.patterns.find((x) => x.id === id);
        if (pattern) pattern.status = status;
      });
      call(`proactive/patterns/${id}`, { status, note, actor: "Quality manager" });
      say(`Pattern ${id} set to ${status}`);
    },
    [call, say, updateProactive],
  );

  const runResearch = useCallback(() => {
    updateProactive((p) => {
      p.research = {
        ...p.research,
        status: "stopped",
        decision: "Re-run stopped: the shadow model still shows no validated lift over SPC. Prediction is not shipped.",
        model_lift: 0.02,
        updated_at: new Date().toISOString(),
        checks: p.research.checks.map((c) => ({ ...c, done: true })),
      };
    });
    call("proactive/research/run");
    say("Research gate re-run — no lift; prediction remains stopped");
  }, [call, say, updateProactive]);

  const verifyFollowup = useCallback(
    (id: string, returned: boolean, delta: number) => {
      updateProactive((p) => {
        const f = p.followups.find((x) => x.id === id);
        if (!f) return;
        f.parameter_returned = returned;
        f.defect_rate_delta = delta;
        f.status = returned && delta <= 0 ? "verified" : "monitoring";
        f.note = returned && delta <= 0
          ? "Parameter returned and defect rate did not regress. Verified."
          : "Parameter or defect rate is not yet stable; the watch stays open.";
      });
      call(`followups/${id}/verify`, { parameter_returned: returned, defect_rate_delta: delta, actor: "M. Weber" });
      say("Follow-up updated");
    },
    [call, say, updateProactive],
  );

  const generateBrief = useCallback(
    (shift: string, lineIds: string[]): ShiftBrief | null => {
      const base = state.proactive ?? pack?.proactive;
      if (!base) return null;
      const active = base.watches.filter((w) => ["watching", "triage", "investigating", "snoozed"].includes(w.status));
      const now = new Date();
      const brief: ShiftBrief = {
        id: `BRIEF-${Date.now()}`,
        at: now.toISOString(),
        shift,
        line_ids: lineIds,
        title: `Shift ${shift} risk brief — ${now.toLocaleDateString(undefined, { day: "2-digit", month: "short" })}`,
        summary: active.length
          ? `${active.length} active watch(es). Top risk: ${active[0].title} on ${active[0].line_id.replace("line-", "Line ")} (${active[0].confidence.toFixed(0)}% confidence). ${base.followups.filter((f) => f.status !== "verified").length} follow-up(s) still open.`
          : `No active watch. Coverage ${(base.metrics.coverage_pct * 100).toFixed(0)}%.`,
        top_risks: active.slice(0, 5).map((w) => ({
          watch_id: w.id,
          title: w.title,
          severity: w.severity,
          action: w.suggested_checks[0]?.label ?? "Triage the watch",
        })),
        open_cases: (pack?.scenarios ?? [])
          .filter((s) => s.case.status !== "approved")
          .slice(0, 6)
          .map((s) => ({ case_id: s.case.id, title: s.case.defect_type, status: s.case.status })),
        actions_due: (pack?.actions ?? [])
          .filter((a) => !state.actionsDone.includes(a.id))
          .slice(0, 6)
          .map((a) => ({ action_id: a.id, title: a.title, owner: a.owner, due: a.due })),
        fixed_not_verified: base.followups
          .filter((f) => f.status === "monitoring" && !f.parameter_returned)
          .map((f) => ({ case_id: f.case_id, title: f.title, note: f.note }))
          .slice(0, 4),
        coverage_note: base.metrics.coverage?.below_floor?.length
          ? `Below the 95% floor: ${base.metrics.coverage.below_floor.join(", ")}. No quality risk is scored for stale sources.`
          : "All sources above the coverage floor.",
        generated_by: "RootCause proactive scheduler",
      };
      updateProactive((p) => {
        p.briefs = [brief, ...p.briefs].slice(0, 10);
      });
      call("briefs/generate", { shift, line_ids: lineIds });
      say("Shift brief generated");
      return brief;
    },
    [call, pack, say, state.actionsDone, state.proactive, updateProactive],
  );

  const investigation = useCallback(
    (caseId: string) => {
      const scenario = scenarioFor(caseId);
      if (!scenario) return null;
      return investigationFor(
        scenario,
        state.rejected[caseId] ?? [],
        state.accepted[caseId] ?? null,
        state.manual[caseId] ?? [],
      );
    },
    [scenarioFor, state.accepted, state.manual, state.rejected],
  );

  const caseStatus = useCallback(
    (caseId: string) => {
      if (state.approvals[caseId]) return "approved";
      if (state.accepted[caseId]) return "awaiting_review";
      if ((state.rejected[caseId]?.length ?? 0) > 0) return "awaiting_review";
      return scenarioFor(caseId)?.case.status ?? "new";
    },
    [scenarioFor, state.accepted, state.approvals, state.rejected],
  );

  const audits = useCallback(
    (caseId?: string) => (caseId ? eventsFor(caseId) : [...state.events, ...(pack?.audits ?? [])].sort((a, b) => b.at.localeCompare(a.at))),
    [eventsFor, pack, state.events],
  );

  const value = useMemo<StoreValue>(
    () => ({
      pack,
      loading,
      error,
      live,
      scenarioFor,
      caseStatus,
      reportFor,
      investigation,
      audits,
      rejected: (caseId) => state.rejected[caseId] ?? [],
      actionsDone: state.actionsDone,
      alertsAck: state.alertsAck,
      baselines: state.baselines,
      proactive: state.proactive ?? pack?.proactive ?? null,
      accept,
      reject,
      addManual,
      patchReport,
      approveReport,
      acknowledge,
      completeAction,
      setSharing,
      setBaseline,
      reset,
      resetCase,
      scanProactive,
      triageWatch,
      snoozeWatch,
      dismissWatch,
      convertWatch,
      trueRiskWatch,
      markCheck,
      captureNearMiss,
      releaseExposure,
      actOnRecommendation,
      readNotification,
      readAllNotifications,
      updateSchedule,
      updateThreshold,
      stopProactive,
      startProactive,
      reviewPattern,
      runResearch,
      verifyFollowup,
      generateBrief,
      toast,
      say,
    }),
    [
      pack, loading, error, live, scenarioFor, caseStatus, reportFor, investigation, audits,
      state.rejected, accept, reject, addManual, patchReport, approveReport, acknowledge,
      completeAction, setSharing, setBaseline, reset, resetCase, toast, say, state.actionsDone, state.alertsAck, state.baselines,
      state.proactive, scanProactive, triageWatch, snoozeWatch, dismissWatch, convertWatch, trueRiskWatch,
      markCheck, captureNearMiss, releaseExposure, actOnRecommendation, readNotification, readAllNotifications, updateSchedule,
      updateThreshold, stopProactive, startProactive, reviewPattern, runResearch, verifyFollowup, generateBrief,
    ],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore(): StoreValue {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used inside StoreProvider");
  return ctx;
}

export function useRanked(caseId: string) {
  const store = useStore();
  return useMemo(() => {
    const scenario = store.scenarioFor(caseId);
    if (!scenario) return null;
    const inv = store.investigation(caseId);
    return { scenario, inv, report: store.reportFor(caseId), status: store.caseStatus(caseId) };
  }, [caseId, store]);
}
