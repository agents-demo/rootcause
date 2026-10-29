import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, fmtDateTime, pct, timeAgo } from "../lib/engine";
import { Icon } from "../components/Icon";
import { Modal, PageHead } from "../components/UI";
import { BarList, Sparkline } from "../components/Charts";

const SEV_ORDER: Record<string, number> = { critical: 0, high: 1, warning: 2, info: 3 };

function WatchStatus({ status }: { status: string }) {
  const map: Record<string, string> = {
    watching: "",
    triage: "amber",
    investigating: "cyan",
    snoozed: "",
    dismissed: "red",
    converted: "green",
  };
  return <span className={`chip ${map[status] ?? ""}`} style={{ fontSize: 8 }}>{status}</span>;
}

export default function Watchlist() {
  const { proactive, scanProactive, pack, triageWatch, captureNearMiss } = useStore();
  const navigate = useNavigate();
  const [status, setStatus] = useState("open");
  const [line, setLine] = useState("all");
  const [query, setQuery] = useState("");
  const [nearMissOpen, setNearMissOpen] = useState(false);
  const [nearMissLine, setNearMissLine] = useState("line-6");
  const [nearMissNote, setNearMissNote] = useState("");
  const [nearMissParameter, setNearMissParameter] = useState("Unusual sound at the press");

  const watches = useMemo(() => {
    if (!proactive) return [];
    return proactive.watches
      .filter((w) => (status === "open" ? ["watching", "triage", "investigating", "snoozed"].includes(w.status) : status === "all" || w.status === status))
      .filter((w) => line === "all" || w.line_id === line)
      .filter((w) => `${w.id} ${w.title} ${w.pattern_name} ${w.owner}`.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => (SEV_ORDER[a.severity] ?? 4) - (SEV_ORDER[b.severity] ?? 4) || b.risk_score - a.risk_score);
  }, [proactive, status, line, query]);

  if (!proactive) return <div className="empty">Loading proactive layer…</div>;
  const m = proactive.metrics;
  const demoNow = new Date(pack?.meta.anchor ?? new Date().toISOString()).getTime();
  const openCount = proactive.watches.filter((w) => ["watching", "triage", "investigating", "snoozed"].includes(w.status)).length;
  const overdue = proactive.watches.filter((w) => ["watching", "triage"].includes(w.status) && new Date(w.sla_due).getTime() < demoNow).length;
  const unread = proactive.notifications.filter((n) => !n.read).length;

  return (
    <div>
      <PageHead
        kicker="Phase 4 · proactive quality"
        title="Risk before the next defect"
        subtitle="A watch is a hypothesis, not a verdict. Every entry answers what changed, why now, what check to run and what would make it a false alarm. The engineer decides; nothing touches the line."
        actions={
          <>
            <span className={classNames("chip", proactive.settings.schedule.stop_switch ? "red" : "green")}>
              <span className={`dot ${proactive.settings.schedule.stop_switch ? "bad" : "live"}`} />
              {proactive.settings.schedule.stop_switch ? "Scanning stopped" : `Scheduler ${proactive.settings.schedule.mode}`}
            </span>
            <Link className="btn sm" to="/booth/proactive"><Icon name="play" size={11} /> Proactive demo</Link>
            <button className="btn sm" onClick={() => setNearMissOpen(true)}><Icon name="plus" size={11} /> Near-miss</button>
            <button className="btn sm primary" onClick={scanProactive} disabled={proactive.settings.schedule.stop_switch}>
              <Icon name="refresh" size={12} /> Scan now
            </button>
          </>
        }
      />

      {proactive.settings.schedule.stop_switch && (
        <div className="panel mb12" style={{ borderColor: "rgba(248,113,113,.4)", background: "rgba(248,113,113,.06)" }}>
          <div className="panel-body small" style={{ color: "#fca5a5" }}>
            <b>Proactive scanning is stopped.</b> Defect cases, review and reports are unaffected. Start it again from Proactive operations. Reason: {proactive.settings.stop_reasons.at(-1) ?? "not recorded"}.
          </div>
        </div>
      )}

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Open watches</div><div className="value">{openCount}</div><div className="foot">{overdue} past triage SLA · {proactive.watches.length} total</div></div>
        <div className="stat"><div className="label">Watch precision</div><div className="value">{pct(m.watch_precision, 1)}</div><div className="foot"><span className="delta up">↑</span> {m.useful_watches}/{m.total_watches} useful · target 60%</div></div>
        <div className="stat"><div className="label">Alerts / line / shift</div><div className="value">{m.alerts_per_line_shift}</div><div className="foot">budget {proactive.settings.schedule.false_alarm_budget} · alert fatigue watched</div></div>
        <div className="stat"><div className="label">Signal coverage</div><div className="value">{pct(m.coverage_pct, 1)}</div><div className="foot">{m.coverage?.below_floor?.length ? `${m.coverage.below_floor.length} line below floor` : "all sources above floor"}</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.65fr 1fr", alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head">
            <h3>Watchlist</h3>
            <div className="row gap6" style={{ flexWrap: "wrap" }}>
              <div className="search">
                <Icon name="search" size={12} />
                <input className="input" style={{ width: 170, padding: "5px 8px 5px 27px", fontSize: 10 }} placeholder="Search watch, pattern…" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
              <select className="select" style={{ width: 120, padding: "5px 7px", fontSize: 10 }} value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="open">Open</option>
                <option value="all">All</option>
                <option value="watching">Watching</option>
                <option value="triage">Triage</option>
                <option value="investigating">Investigating</option>
                <option value="converted">Converted</option>
                <option value="dismissed">Dismissed</option>
              </select>
              <select className="select" style={{ width: 110, padding: "5px 7px", fontSize: 10 }} value={line} onChange={(e) => setLine(e.target.value)}>
                <option value="all">All lines</option>
                {pack?.lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead><tr><th>Watch</th><th>Risk</th><th>Pattern</th><th>Line</th><th>Owner</th><th>Age / SLA</th><th>Status</th><th /></tr></thead>
              <tbody>
                {watches.map((w) => {
                  const late = ["watching", "triage"].includes(w.status) && new Date(w.sla_due).getTime() < demoNow;
                  return (
                    <tr key={w.id} className="clickable" onClick={() => navigate(`/watch/${w.id}`)}>
                      <td>
                        <div className="row gap6">
                          <span className="id">{w.id}</span>
                          <span className={`dot ${w.severity === "critical" ? "bad" : w.severity === "high" ? "warn" : "live"}`} />
                        </div>
                        <div className="small" style={{ color: "var(--ink-2)", fontWeight: 600, maxWidth: 260 }}>{w.title}</div>
                        <div className="xsmall soft">{w.signal_count} signal(s) · {w.confidence.toFixed(0)}% confidence</div>
                      </td>
                      <td>
                        <div className="mono small" style={{ color: w.risk_score >= 0.8 ? "var(--red)" : w.risk_score >= 0.6 ? "var(--amber)" : "var(--cyan)" }}>{Math.round(w.risk_score * 100)}</div>
                        <div className="meter" style={{ width: 48, height: 3 }}><i style={{ width: `${w.risk_score * 100}%`, background: w.risk_score >= 0.8 ? "var(--red)" : "var(--amber)" }} /></div>
                      </td>
                      <td className="xsmall muted" style={{ maxWidth: 150 }}>{w.pattern_name}</td>
                      <td className="small muted">{w.line_id.replace("line-", "L")}</td>
                      <td className="xsmall muted">{w.owner}</td>
                      <td>
                        <div className="xsmall">{timeAgo(w.opened_at)}</div>
                        {late ? <div className="xsmall red">SLA overdue</div> : <div className="xsmall soft">due {new Date(w.sla_due).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}</div>}                      </td>
                      <td><WatchStatus status={w.status} /></td>
                      <td>{["watching"].includes(w.status) && <button className="btn sm ghost" onClick={(e) => { e.stopPropagation(); triageWatch(w.id); }}>Triage</button>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {watches.length === 0 && <div className="empty">No watches match. Try “All” or clear the search.</div>}
          <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
            <span className="xsmall soft">{watches.length} shown · {proactive.settings.schedule.mode} mode</span>
            <span className="xsmall soft">A signal is a hypothesis, not a verdict.</span>
          </div>
        </div>

        <div className="col-stack">
          <div className="panel" style={{ borderColor: "rgba(255,180,84,.28)" }}>
            <div className="panel-head"><h3>Shift brief</h3><span className="sub">start of shift</span></div>
            <div className="panel-body">
              <p className="small" style={{ color: "var(--ink-2)", lineHeight: 1.55 }}>
                {proactive.briefs[0]?.summary ?? "No brief yet. Generate one from the shift brief page."}
              </p>
              <div className="row gap8 mt12">
                <Link className="btn primary sm" to="/brief"><Icon name="report" size={11} /> Open shift brief</Link>
                <span className="chip amber"><Icon name="alert" size={10} /> {unread} unread</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Scheduler health</h3><span className="sub">dead-man's switch</span></div>
            <div className="panel-body">
              <div className="row between">
                <span className="small muted">Status</span>
                <span className={`chip ${proactive.health?.status === "ok" ? "green" : "red"}`} style={{ fontSize: 8 }}>{proactive.health?.status ?? "unknown"}</span>
              </div>
              <div className="row between mt8"><span className="xsmall muted">Last scan</span><span className="xsmall mono">{proactive.health?.last_scan ? timeAgo(proactive.health.last_scan) : "—"}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Interval</span><span className="xsmall mono">{proactive.settings.schedule.interval_minutes} min</span></div>
              <div className="row between mt8"><span className="xsmall muted">Next run</span><span className="xsmall mono">in {proactive.settings.schedule.interval_minutes} min</span></div>
              <div className="divider" />
              <div className="xsmall soft" style={{ lineHeight: 1.5 }}>{proactive.health?.detail ?? "No scan run yet."}</div>
              <div className="mt12">
                <div className="xsmall soft mb8" style={{ letterSpacing: ".1em", textTransform: "uppercase" }}>Recent scans</div>
                {proactive.scan_runs.slice(0, 3).map((r) => (
                  <div key={r.id} className="row between" style={{ padding: "4px 0" }}>
                    <span className="xsmall mono soft">{new Date(r.at).toLocaleTimeString()}</span>
                    <span className="xsmall muted">{r.signals} signals</span>
                    <span className="xsmall mono">{r.watches_opened} opened</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Coverage</h3><span className="sub">below-floor sources suppress alerts</span></div>
            <div className="panel-body col gap8">
              {proactive.coverage.map((c) => (
                <div key={c.line_id}>
                  <div className="row between">
                    <span className="xsmall muted">{pack?.lines.find((l) => l.id === c.line_id)?.name ?? c.line_id}</span>
                    <span className={classNames("xsmall mono", c.pct < 0.95 ? "amber" : "green")}>{pct(c.pct, 0)}</span>
                  </div>
                  <div className="meter mt8" style={{ height: 3 }}><i style={{ width: `${c.pct * 100}%`, background: c.pct < 0.95 ? "var(--amber)" : "var(--green)" }} /></div>
                  {c.stale.length > 0 && <div className="xsmall soft mt8">{c.stale[0]}</div>}
                </div>
              ))}
              <div className="divider" />
              <div className="row between"><span className="xsmall soft">Floor</span><span className="xsmall mono">{pct(proactive.settings.schedule.coverage_floor, 0)}</span></div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Pressure test</h3><span className="sub">this week</span></div>
            <div className="panel-body">
              <div className="row between"><span className="xsmall muted">Median triage</span><span className="small mono">{m.median_triage_min} min</span></div>
              <div className="row between mt8"><span className="xsmall muted">Containment conversion</span><span className="small mono">{pct(m.containment_conversion, 0)}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Escaped defects</span><span className="small mono green">{m.escaped_defects}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Cost / useful alert</span><span className="small mono">€{m.cost_per_useful_alert_eur.toFixed(0)}</span></div>
              <div className="divider" />
              <div className="row between">
                <span className="xsmall soft">7-week precision</span>
                <Sparkline values={m.weekly.map((w) => w.precision)} width={110} height={28} color="#5eead4" />
              </div>
              <Link className="btn ghost sm mt8" to="/proactive">Calibrate and audit <Icon name="arrow" size={11} /></Link>
            </div>
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>What “proactive” means here</h3><span className="sub">guardrails</span></div>
        <div className="panel-body grid g4">
          {[
            ["Risk before defect", "A watch can open before any bad part exists. The evidence is assembled before the shift, not after the scrap."],
            ["Human decides", "Every containment action is approved by a named engineer. No automatic line control, rejection or batch hold."],
            ["Why now?", "Every watch cites signals and evidence IDs, and says what would make it a false alarm."],
            ["False alarms are data", "Dismissals are recorded with a reason and fed into threshold tuning and precision reporting."],
          ].map(([t, b]) => (
            <div key={t} className="feature"><h3>{t}</h3><p>{b}</p></div>
          ))}
        </div>
      </div>

      <Modal
        open={nearMissOpen}
        title="Capture a near-miss"
        onClose={() => setNearMissOpen(false)}
        actions={<><button className="btn ghost" onClick={() => setNearMissOpen(false)}>Cancel</button><button className="btn primary" disabled={!nearMissNote.trim()} onClick={() => { captureNearMiss(nearMissLine, nearMissNote, nearMissParameter); setNearMissOpen(false); setNearMissNote(""); }}>Open a watch</button></>}
      >
        <p>A near-miss has no defective part yet. The observation becomes a watch with a reason, an owner and an SLA — not a forgotten notebook line.</p>
        <div className="field mb12">
          <label>Line</label>
          <select className="select" value={nearMissLine} onChange={(e) => setNearMissLine(e.target.value)}>
            {pack?.lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
        <div className="field mb12">
          <label>Observation</label>
          <input className="input" value={nearMissParameter} onChange={(e) => setNearMissParameter(e.target.value)} />
        </div>
        <div className="field">
          <label>What did you see?</label>
          <textarea className="textarea" value={nearMissNote} onChange={(e) => setNearMissNote(e.target.value)} placeholder="e.g. A different sound from the press, no defective part yet." />
        </div>
      </Modal>
    </div>
  );
}
