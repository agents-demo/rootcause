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
  Hypothesis,
  Pack,
  Report,
  Scenario,
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
        const data = (await packRes.json()) as Pack;
        if (cancelled) return;
        setPack(data);
        setLoading(false);

        // If the on-site API is serving this page, hydrate the human decisions from SQLite.
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
      toast,
      say,
    }),
    [
      pack, loading, error, live, scenarioFor, caseStatus, reportFor, investigation, audits,
      state.rejected, accept, reject, addManual, patchReport, approveReport, acknowledge,
      completeAction, setSharing, setBaseline, reset, resetCase, toast, say, state.actionsDone, state.alertsAck,
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
