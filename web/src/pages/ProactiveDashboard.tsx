import { useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDate, pct } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";
import { LineChart } from "../components/Charts";

export default function ProactiveDashboard() {
  const {
    proactive, pack, scanProactive, updateSchedule, updateThreshold, stopProactive, startProactive,
    verifyFollowup, runResearch, reviewPattern, say,
  } = useStore();
  const [stopReason, setStopReason] = useState("Alert quality review requested a pause.");

  if (!proactive) return <div className="empty">Loading proactive operations…</div>;
  const m = proactive.metrics;
  const s = proactive.settings.schedule;
  const weekly = m.weekly;

  return (
    <div>
      <PageHead
        kicker="Phase 4 · proactive operations"
        title="Proactive control room"
        subtitle="Precision, alert fatigue, coverage, thresholds, pattern cards and the research gate. This is where the proactive layer is calibrated — and where it can be switched off."
        actions={
          <>
            <span className={`chip ${s.stop_switch ? "red" : "green"}`}><span className={`dot ${s.stop_switch ? "bad" : "live"}`} /> {s.stop_switch ? "stopped" : s.mode}</span>
            <button className="btn sm" onClick={scanProactive} disabled={s.stop_switch}><Icon name="refresh" size={11} /> Run scan</button>
            <button className="btn sm" onClick={() => say("Weekly proactive review pack exported to Markdown")}>Review pack</button>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Watch precision</div><div className="value">{pct(m.watch_precision, 1)}</div><div className="foot">gate 60% · {m.useful_watches} useful / {m.total_watches} · <span className={m.drift?.status === "warning" ? "amber" : "green"}>{m.drift?.status ?? "stable"}</span></div></div>
        <div className="stat"><div className="label">Median triage</div><div className="value">{m.median_triage_min}<small>min</small></div><div className="foot">SLA {s.triage_sla_min} min · alert fatigue watched</div></div>
        <div className="stat"><div className="label">Containment conversion</div><div className="value">{pct(m.containment_conversion, 0)}</div><div className="foot">recommendations approved / executed</div></div>
        <div className="stat"><div className="label">Defects prevented</div><div className="value">{m.defects_prevented_month}<small>/mo</small></div><div className="foot">{m.escaped_defects} escaped · coverage {pct(m.coverage_pct, 1)}</div></div>
      </div>

      <div className="grid g2 mb16">
        <div className="panel">
          <div className="panel-head"><h3>Precision and alert volume</h3><span className="sub">last 8 weeks</span></div>
          <div className="panel-body">
            <LineChart
              series={[
                { name: "Precision", color: "#5eead4", values: weekly.map((w) => w.precision * 100), dots: true },
                { name: "Alerts / line / shift", color: "#ffb454", values: weekly.map((w) => w.alerts), dashed: true },
              ]}
              labels={weekly.map((w) => w.week)}
              height={200}
              decimals={1}
            />
            <div className="chart-legend mt8">
              <span><i style={{ background: "#5eead4" }} /> Precision %</span>
              <span><i style={{ background: "#ffb454" }} /> Alerts / line / shift</span>
            </div>
            <div className="xsmall soft mt8">The system is improving when precision rises and alert volume does not.</div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Triage time and containment</h3><span className="sub">last 8 weeks</span></div>
          <div className="panel-body">
            <LineChart
              series={[
                { name: "Triage minutes", color: "#7dd3fc", values: weekly.map((w) => w.triage), dots: true },
                { name: "Containment conversion %", color: "#c4b5fd", values: weekly.map((w) => w.conversion * 100), dashed: true },
              ]}
              labels={weekly.map((w) => w.week)}
              height={200}
              decimals={1}
            />
            <div className="chart-legend mt8">
              <span><i style={{ background: "#7dd3fc" }} /> Median triage (min)</span>
              <span><i style={{ background: "#c4b5fd" }} /> Conversion %</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.2fr 1fr", alignItems: "start" }}>
        <div className="col-stack">
          <div className="panel">
            <div className="panel-head"><h3>Calibration</h3><span className="sub">requires engineer sign-off</span></div>
            <div className="panel-body">
              <div className="grid g3" style={{ gap: 9 }}>
                <div className="field"><label>Mode</label><select className="select" value={s.mode} onChange={(e) => updateSchedule({ mode: e.target.value as "shadow" | "live" })}><option value="shadow">shadow</option><option value="live">live</option></select></div>
                <div className="field"><label>Interval (min)</label><input className="input" type="number" defaultValue={s.interval_minutes} onBlur={(e) => updateSchedule({ interval_minutes: Number(e.target.value) })} /></div>
                <div className="field"><label>False-alarm budget</label><input className="input" type="number" step="0.1" defaultValue={s.false_alarm_budget} onBlur={(e) => updateSchedule({ false_alarm_budget: Number(e.target.value) })} /></div>
                <div className="field"><label>Max alerts / shift</label><input className="input" type="number" defaultValue={s.max_alerts_per_shift} onBlur={(e) => updateSchedule({ max_alerts_per_shift: Number(e.target.value) })} /></div>
                <div className="field"><label>Quiet hours</label><input className="input" defaultValue={s.quiet_hours} onBlur={(e) => updateSchedule({ quiet_hours: e.target.value })} /></div>
                <div className="field"><label>Coverage floor</label><input className="input" type="number" step="0.01" defaultValue={s.coverage_floor} onBlur={(e) => updateSchedule({ coverage_floor: Number(e.target.value) })} /></div>
                <div className="field"><label>Champion</label><input className="input" defaultValue={s.champion} onBlur={(e) => updateSchedule({ champion: e.target.value })} /></div>
                <div className="field"><label>Challenger</label><input className="input" defaultValue={s.challenger} onBlur={(e) => updateSchedule({ challenger: e.target.value })} /></div>
                <div className="field"><label>Webhook</label><input className="input" defaultValue={s.webhook_url} onBlur={(e) => updateSchedule({ webhook_url: e.target.value })} /></div>
              </div>
              <div className="divider" />
              <div className="row between">
                <div>
                  <div className="small" style={{ color: "var(--ink-2)" }}>Proactive scanning</div>
                  <div className="xsmall soft">Stopping this never affects defect cases, review or reports.</div>
                </div>
                {s.stop_switch ? (
                  <button className="btn sm cyan" onClick={startProactive}><Icon name="play" size={11} /> Start</button>
                ) : (
                  <button className="btn sm danger" onClick={() => stopProactive(stopReason)}><Icon name="x" size={11} /> Stop</button>
                )}
              </div>
              <input className="input mt8" value={stopReason} onChange={(e) => setStopReason(e.target.value)} aria-label="Stop reason" />
              {s.stop_switch && (
                <div className="xsmall red mt8">Stopped: {proactive.settings.stop_reasons.at(-1) ?? "reason not recorded"}</div>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Thresholds</h3><span className="sub">{proactive.settings.thresholds.length} rules · versioned</span></div>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead><tr><th>Rule</th><th>Line</th><th>Parameter</th><th>Method</th><th>Limit</th><th>Owner / version</th><th>Active</th></tr></thead>
                <tbody>
                  {proactive.settings.thresholds.map((r) => (
                    <tr key={r.id}>
                      <td className="mono xsmall">{r.id}</td>
                      <td className="xsmall muted">{r.line_id.replace("line-", "L")}</td>
                      <td className="small" style={{ color: "var(--ink-2)" }}>{r.parameter}</td>
                      <td><span className="tag">{r.method}</span></td>
                      <td>
                        <input
                          className="input"
                          style={{ width: 76, padding: "3px 6px", fontSize: 10 }}
                          type="number"
                          step="0.01"
                          defaultValue={r.limit}
                          onBlur={(e) => updateThreshold(r.id, { limit: Number(e.target.value) })}
                        />
                      </td>
                      <td className="xsmall muted">{r.owner} · {r.version}</td>
                      <td><button className={`switch ${r.active ? "on" : ""}`} onClick={() => updateThreshold(r.id, { active: !r.active })} aria-label="Threshold active" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
              <span className="xsmall soft">Every change is audited; the champion never changes without sign-off.</span>
              <span className="xsmall mono soft">{proactive.tuning?.[0]?.action ?? "hold"}</span>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Replay and tuning</h3><span className="sub">before live alerts</span></div>
            <div className="panel-body">
              <div className="row between">
                <span className="small muted">Replay precision</span>
                <span className="mono small cyan">{pct(proactive.replay?.precision ?? 0, 0)}</span>
              </div>
              <div className="row between mt8">
                <span className="small muted">Replay recall</span>
                <span className="mono small cyan">{pct(proactive.replay?.recall ?? 0, 0)}</span>
              </div>
              <div className="divider" />
              <div className="col gap6">
                {(proactive.replay?.rows ?? []).map((r) => (
                  <div key={r.scenario} className="row between">
                    <span className="xsmall muted">{r.scenario} · {r.signals} signals</span>
                    <span className={`chip ${r.opened === r.expected_risk ? "green" : "amber"}`} style={{ fontSize: 8 }}>{r.opened ? "opened" : "quiet"} / expected {r.expected_risk ? "risk" : "none"}</span>
                  </div>
                ))}
              </div>
              <div className="divider" />
              <div className="trust-note">
                <b>{proactive.tuning?.[0]?.action === "tighten" ? "Tighten the threshold." : "Hold the champion."}</b>{" "}
                {proactive.tuning?.[0]?.reason} {proactive.tuning?.[0]?.suggestion}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Data quality & coverage</h3><span className="sub">below floor suppresses alerts</span></div>
            <div className="panel-body" style={{ padding: 0 }}>
              <table className="table">
                <thead><tr><th>Line</th><th>Fresh / expected</th><th>Coverage</th><th>Stale</th><th>Status</th></tr></thead>
                <tbody>
                  {proactive.coverage.map((c) => (
                    <tr key={c.line_id}>
                      <td className="small muted">{pack?.lines.find((l) => l.id === c.line_id)?.name ?? c.line_id}</td>
                      <td className="xsmall mono">{c.fresh_sources}/{c.expected_sources}</td>
                      <td className="mono small">{pct(c.pct, 0)}</td>
                      <td className="xsmall muted">{c.stale[0] ?? "—"}</td>
                      <td><span className={`chip ${c.status === "ok" ? "green" : c.status === "degraded" ? "amber" : "red"}`} style={{ fontSize: 8 }}>{c.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="col-stack">
          <div className="panel">
            <div className="panel-head"><h3>Follow-through</h3><span className="sub">fixed but verified</span></div>
            <div className="panel-body col gap8">
              {proactive.followups.map((f) => (
                <div key={f.id} style={{ borderBottom: "1px solid rgba(255,255,255,.05)", paddingBottom: 8 }}>
                  <div className="row between">
                    <span className="small" style={{ color: "var(--ink-2)" }}>{f.title}</span>
                    <span className={`chip ${f.status === "verified" ? "green" : f.status === "reopened" ? "red" : "amber"}`} style={{ fontSize: 8 }}>{f.status}</span>
                  </div>
                  <div className="xsmall soft mt8">{f.case_id} · {f.note}</div>
                  <div className="row between mt8">
                    <span className="xsmall soft">window ends {fmtDate(f.window_end)}</span>
                    <div className="row gap4">
                      <button className="btn sm ghost" onClick={() => verifyFollowup(f.id, true, -0.2)}>Verify</button>
                      <button className="btn sm ghost" onClick={() => verifyFollowup(f.id, false, 0)}>Still open</button>
                    </div>
                  </div>
                </div>
              ))}
              {proactive.followups.length === 0 && <div className="empty">No follow-up windows.</div>}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Pattern governance</h3><span className="sub">champion / challenger</span></div>
            <div className="panel-body" style={{ padding: 0 }}>
              <table className="table">
                <thead><tr><th>Pattern</th><th>Version</th><th>Precision</th><th>Status</th><th>Review</th></tr></thead>
                <tbody>
                  {proactive.patterns.map((p) => (
                    <tr key={p.id}>
                      <td className="xsmall" style={{ color: "var(--ink-2)" }}>{p.name}</td>
                      <td className="xsmall mono">{p.version}</td>
                      <td className="xsmall mono">{pct(p.historical_precision, 0)}</td>
                      <td><span className={`chip ${p.status === "active" ? "green" : p.status === "shadow" ? "amber" : ""}`} style={{ fontSize: 8 }}>{p.status}</span></td>
                      <td>
                        <div className="row gap4">
                          <button className="btn sm ghost" onClick={() => reviewPattern(p.id, "active")} disabled={p.status === "active"}>Promote</button>
                          <button className="btn sm ghost" onClick={() => reviewPattern(p.id, "shadow")} disabled={p.status === "shadow"}>Shadow</button>
                          <button className="btn sm ghost" onClick={() => reviewPattern(p.id, "retired")} disabled={p.status === "retired"}>Retire</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Model cards</h3><span className="sub">inputs, limits, owner</span></div>
            <div className="panel-body col gap8">
              {proactive.model_cards.map((c) => (
                <div key={c.id}>
                  <div className="row between">
                    <span className="small" style={{ color: "var(--ink-2)" }}>{c.name}</span>
                    <span className={`chip ${c.status === "champion" ? "green" : c.status === "challenger" ? "amber" : ""}`} style={{ fontSize: 8 }}>{c.status}</span>
                  </div>
                  <div className="xsmall soft">{c.version} · {c.kind} · {c.owner} · validated {fmtDate(c.last_validated)}</div>
                  <div className="xsmall soft">Limits: {c.limits.join("; ")} · Failure modes: {c.failure_modes.join("; ")}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel" style={{ borderColor: "rgba(248,113,113,.3)" }}>
            <div className="panel-head"><h3>Predictive research gate</h3><span className="sub">{proactive.research.status}</span></div>
            <div className="panel-body">
              <p className="small" style={{ color: "var(--ink-2)", lineHeight: 1.5 }}>{proactive.research.question}</p>
              <div className="trust-note mt12" style={{ borderColor: "rgba(248,113,113,.35)", background: "rgba(248,113,113,.06)", color: "#fecaca" }}>
                <b>Decision: {proactive.research.status}.</b> {proactive.research.decision}
              </div>
              <div className="grid g2 mt12" style={{ gap: 8 }}>
                <div><div className="xsmall soft">History</div><div className="small mono">{proactive.research.data_months} mo</div></div>
                <div><div className="xsmall soft">Events</div><div className="small mono">{proactive.research.events} / {proactive.research.required_events}</div></div>
                <div><div className="xsmall soft">Lift over SPC</div><div className="small mono">{proactive.research.model_lift >= 0 ? "+" : ""}{proactive.research.model_lift.toFixed(3)}</div></div>
                <div><div className="xsmall soft">False alarms</div><div className="small mono">{pct(proactive.research.false_alarm_rate, 0)}</div></div>
                <div><div className="xsmall soft">Lead time</div><div className="small mono">{proactive.research.lead_time_hours} h</div></div>
                <div><div className="xsmall soft">Cost of errors</div><div className="small mono">€{proactive.research.cost_of_errors_eur.toLocaleString()}</div></div>
              </div>
              <div className="mt12">
                {proactive.research.checks.map((c) => (
                  <div key={c.id} className="row between" style={{ padding: "3px 0" }}>
                    <span className="xsmall muted">{c.done ? "✓" : "○"} {c.label}</span>
                  </div>
                ))}
              </div>
              <button className="btn sm mt12" onClick={runResearch}><Icon name="refresh" size={11} /> Re-run gate</button>
              <div className="xsmall soft mt8">Prediction stays off the product path. A negative result is a valid result.</div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Scheduler</h3><span className="sub">observability</span></div>
            <div className="panel-body">
              <div className="row between"><span className="small muted">Status</span><span className={`chip ${proactive.health?.status === "ok" ? "green" : "red"}`} style={{ fontSize: 8 }}>{proactive.health?.status}</span></div>
              <div className="row between mt8"><span className="small muted">Lag</span><span className="mono small">{proactive.health?.lag_seconds ?? 0} s</span></div>
              <div className="row between mt8"><span className="small muted">Next run</span><span className="mono small">in {s.interval_minutes} min</span></div>
              <div className="row between mt8"><span className="small muted">Offline buffer</span><span className="mono small">{proactive.queue?.queued ?? 0} / {proactive.queue?.max_items ?? 500}</span></div>
              <div className="row between mt8"><span className="small muted">Dropped</span><span className="mono small">{proactive.queue?.dropped ?? 0}</span></div>
              <div className="divider" />
              {proactive.scan_runs.slice(0, 5).map((r) => (
                <div key={r.id} className="row between" style={{ padding: "3px 0" }}>
                  <span className="xsmall mono soft">{new Date(r.at).toLocaleTimeString()}</span>
                  <span className="xsmall muted">{r.signals} signals · {r.suppressed} suppressed</span>
                  <span className={`dot ${r.status === "ok" ? "live" : "warn"}`} />
                </div>
              ))}
              <div className="xsmall soft mt8">{proactive.health?.detail}</div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Contract</h3><span className="sub">what the buyer signs</span></div>
            <div className="panel-body">
              <p className="xsmall muted" style={{ lineHeight: 1.55 }}>{proactive.settings.contract_note}</p>
              <div className="divider" />
              <div className="row between"><span className="xsmall soft">Reconstruction target</span><span className="xsmall mono">{s.reconstruction_target_min} min</span></div>
              <div className="row between mt8"><span className="xsmall soft">Triage SLA</span><span className="xsmall mono">{s.triage_sla_min} min</span></div>
              <div className="row between mt8"><span className="xsmall soft">Stop switch</span><span className="xsmall mono">{s.stop_switch ? "on" : "off"}</span></div>
              <Link className="btn ghost sm mt8" to="/brief">Shift brief <Icon name="arrow" size={11} /></Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
