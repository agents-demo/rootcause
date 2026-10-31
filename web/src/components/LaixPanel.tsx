import { useCallback, useEffect, useState } from "react";
import { useStore } from "../lib/store";
import { Icon } from "./Icon";

interface LaixStatus {
  policy: string;
  enabled: boolean;
  auto_record: boolean;
  baseline_rate: number;
  window_days: number;
  interrupt_cost?: number;
  miss_cost?: number;
}

interface LaixOutcome {
  action_id: string;
  action: string;
  case_id: string;
  line_id: string;
  treated: number;
  recurred: number;
  baseline_rate: number;
  treated_rate: number;
  effect: number;
  confidence: number;
  window_days: number;
  note: string;
  causal: boolean;
  next_check_at?: string | null;
  due?: boolean;
}

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

function effect(value: number) {
  return `${value > 0 ? "+" : ""}${Math.round(value * 100)}%`;
}

export function LaixPanel() {
  const { live, say } = useStore();
  const [status, setStatus] = useState<LaixStatus | null>(null);
  const [outcomes, setOutcomes] = useState<LaixOutcome[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!live) return;
    try {
      const [statusRes, outcomeRes] = await Promise.all([
        fetch(new URL("api/laix/status", document.baseURI).toString()),
        fetch(new URL("api/laix/outcomes", document.baseURI).toString()),
      ]);
      if (statusRes.ok) setStatus((await statusRes.json()) as LaixStatus);
      if (outcomeRes.ok) {
        const data = (await outcomeRes.json()) as { outcomes?: LaixOutcome[] };
        setOutcomes(data.outcomes ?? []);
      }
    } catch {
      setStatus(null);
    }
  }, [live]);

  useEffect(() => {
    void load();
  }, [load]);

  async function record(outcome: LaixOutcome, recurrence: boolean) {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(
        new URL(`api/followups/${encodeURIComponent(outcome.action_id)}/verify`, document.baseURI).toString(),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parameter_returned: recurrence, defect_rate_delta: 0, actor: "M. Weber" }),
        },
      );
      if (!res.ok) throw new Error(`verify returned ${res.status}`);
      say(recurrence ? "Recurrence recorded" : "No recurrence recorded");
      await load();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel mb16">
      <div className="panel-head">
        <h3>Decision layer · LAIX</h3>
        <span className="sub">{live ? status?.policy ?? "on-site API" : "on-site API only"}</span>
      </div>
      <div className="panel-body">
        {!live ? (
          <p className="small muted" style={{ margin: 0 }}>
            The portable decision layer is available when the on-site API is serving this page. It decides
            wait / ask / guide / act / escalate, records its reasoning, and measures whether a prevention
            action reduced recurrence.
          </p>
        ) : (
          <>
            <div className="row gap8" style={{ flexWrap: "wrap" }}>
              <span className={`chip ${status?.enabled ? "green" : ""}`}>
                <span className={`dot ${status?.enabled ? "live" : "warn"}`} /> {status?.enabled ? "Enabled" : "Disabled"}
              </span>
              <span className="chip">Auto-record {status?.auto_record ? "on" : "off"}</span>
              <span className="chip">Baseline {status ? pct(status.baseline_rate) : "—"}</span>
              <span className="chip">Window {status?.window_days ?? 30} days</span>
              <span className="chip">Interrupt cost {status?.interrupt_cost ?? 1}</span>
              <span className="chip">Miss cost {status?.miss_cost ?? 10}</span>
            </div>

            {outcomes.length === 0 ? (
              <p className="small muted mt12" style={{ marginBottom: 0 }}>
                No prevention outcomes yet. Enable <code className="mono">ROOTCAUSE_LAIX=1</code> and set a
                baseline (<code className="mono">ROOTCAUSE_LAIX_BASELINE</code>), then approve a report; the
                post-fix follow-up becomes an outcome.
              </p>
            ) : (
              <div className="col gap6 mt12">
                {outcomes.map((outcome) => (
                  <div key={outcome.action_id} className="ev-card">
                    <div className="row between" style={{ flexWrap: "wrap", gap: 8 }}>
                      <div>
                        <div className="eid">{outcome.case_id || outcome.action_id} · {outcome.line_id || "line"}</div>
                        <h4 style={{ margin: "3px 0 2px" }}>{outcome.action}</h4>
                        <p style={{ margin: 0 }}>
                          {outcome.treated} follow-up{outcome.treated === 1 ? "" : "s"} · {outcome.recurred} recurred ·{" "}
                          baseline {pct(outcome.baseline_rate)} → {pct(outcome.treated_rate)}
                        </p>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div className="mono" style={{ fontSize: 18, color: outcome.effect >= 0 ? "var(--ok)" : "var(--risk)" }}>
                          {effect(outcome.effect)}
                        </div>
                        <div className="xsmall soft">confidence {Math.round(outcome.confidence * 100)}%</div>
                        <div className="xsmall soft">observational</div>
                      </div>
                    </div>
                    <div className="row between mt8" style={{ flexWrap: "wrap", gap: 8 }}>
                      <span className="xsmall soft">
                        {outcome.next_check_at
                          ? `Next check ${new Date(outcome.next_check_at).toLocaleDateString()}${outcome.due ? " · due" : ""}`
                          : "No check date"}
                      </span>
                      <span className="row gap6">
                        <button className="btn sm" disabled={busy} onClick={() => void record(outcome, false)}>
                          <Icon name="check" size={11} /> No recurrence
                        </button>
                        <button className="btn sm danger" disabled={busy} onClick={() => void record(outcome, true)}>
                          <Icon name="alert" size={11} /> Recurred
                        </button>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {error && <div className="xsmall mt8" style={{ color: "var(--risk)" }}>{error}</div>}
            <p className="xsmall soft mt8" style={{ marginBottom: 0 }}>
              Recurrence is compared with the supplied baseline. This is an observational estimate, not a
              causal claim; the policy still never approves a cause or controls a line.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
