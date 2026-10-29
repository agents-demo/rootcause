import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { eur, fmtDate, hours, pct } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";
import { BarList, Donut, LineChart, Sparkline } from "../components/Charts";

const LINE_COLORS: Record<string, string> = {
  "line-6": "#ffb454",
  "line-2": "#5eead4",
  "line-4": "#7dd3fc",
  "line-3": "#c4b5fd",
};

export default function Dashboard() {
  const { pack, actionsDone, completeAction, acknowledge, alertsAck, setBaseline, audits, say, baselines } = useStore();
  const [baselineLine, setBaselineLine] = useState("line-6");
  const [baselineValue, setBaselineValue] = useState("62");

  const data = pack?.dashboard;
  const actions = useMemo(
    () => (pack?.actions ?? []).map((a) => (actionsDone.includes(a.id) ? { ...a, status: "done" as const } : a)),
    [pack, actionsDone],
  );

  if (!pack || !data) return <div className="empty">Loading dashboard…</div>;

  const weeks = data.weekly.map((w) => w.week);
  const savings = actions.filter((a) => a.status === "done").reduce((sum, a) => sum + a.saving_eur, 0);
  const pipeline = actions.filter((a) => a.status !== "done").reduce((sum, a) => sum + a.saving_eur, 0);
  const speedup = data.baseline_hours_to_cause / data.median_hours_to_cause;

  const localStats = {
    cases: pack.scenarios.length,
    approved: pack.scenarios.filter((s) => s.report.status === "approved").length,
    corrections: pack.audits.filter((a) => a.action.includes("reject")).length,
  };

  return (
    <div>
      <PageHead
        kicker="Pilot measurement"
        title="Quality dashboard"
        subtitle="For the quality manager, not the stage. What changed since the pilot started: time to cause, accuracy, scrap, engineer hours and the corrective actions still open."
        actions={
          <>
            <span className="chip"><Icon name="calendar" size={11} /> Week 43 · 2026</span>
            <span className="chip green"><span className="dot live" /> Live on 4 lines</span>
            <button className="btn sm" onClick={() => say("Pilot report queued for PDF export")}><Icon name="download" size={12} /> Weekly report</button>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat">
          <div className="label">Investigations this week</div>
          <div className="value">{data.investigations_this_week}</div>
          <div className="foot"><span className="delta up">↑ {pct(data.investigations_delta)}</span> vs last week</div>
        </div>
        <div className="stat">
          <div className="label">Median time to cause</div>
          <div className="value">{data.median_hours_to_cause}<small>h</small></div>
          <div className="foot"><span className="delta up">−{pct(1 - data.median_hours_to_cause / data.baseline_hours_to_cause)}</span> · {speedup.toFixed(1)}× faster</div>
        </div>
        <div className="stat">
          <div className="label">Cause accuracy</div>
          <div className="value">{pct(data.cause_accuracy)}</div>
          <div className="foot">engineer-accepted first cause · weekly review</div>
        </div>
        <div className="stat">
          <div className="label">Scrap + rework prevented</div>
          <div className="value">{eur(data.scrap_prevented_eur + data.rework_prevented_eur)}</div>
          <div className="foot"><span className="delta up">↑</span> {data.engineer_hours_saved} engineer hours saved</div>
        </div>
      </div>

      <div className="grid g2 mb16">
        <div className="panel">
          <div className="panel-head">
            <h3>Time to cause</h3>
            <span className="sub">hours per investigation</span>
          </div>
          <div className="panel-body">
            <LineChart
              series={[
                { name: "RootCause", color: "#5eead4", values: data.weekly.map((w) => w.hours), dots: true },
                { name: "Before (baseline)", color: "#5d5a54", values: data.weekly.map((w) => w.baseline), dashed: true },
              ]}
              labels={weeks}
              height={190}
              unit=" h"
              area
              decimals={1}
            />
            <div className="chart-legend mt8">
              <span><i style={{ background: "#5eead4" }} /> RootCause</span>
              <span><i style={{ background: "#5d5a54" }} /> Baseline (recorded, not modelled)</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h3>Defect rate by line</h3>
            <span className="sub">% of production</span>
          </div>
          <div className="panel-body">
            <LineChart
              series={pack.lines
                .filter((l) => l.plant_id === "plant-de")
                .map((l) => ({
                  name: l.name,
                  color: LINE_COLORS[l.id] ?? "#888",
                  values: data.defect_rate_pct.map((row) => Number(row[l.id] ?? 0)),
                }))}
              labels={data.defect_rate_pct.map((row) => String(row.week))}
              height={190}
              unit="%"
              decimals={1}
            />
            <div className="chart-legend mt8">
              {pack.lines.filter((l) => l.plant_id === "plant-de").map((l) => (
                <span key={l.id}><i style={{ background: LINE_COLORS[l.id] }} /> {l.name}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid g3 mb16">
        <div className="panel">
          <div className="panel-head"><h3>Top causes</h3><span className="sub">last 8 weeks</span></div>
          <div className="panel-body">
            <BarList
              items={data.top_causes.map((c) => ({ label: c.cause, value: c.count, sub: `${pct(c.share)}` }))}
            />
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Resolution by line</h3><span className="sub">median hours</span></div>
          <div className="panel-body">
            <BarList
              color="#5eead4"
              items={data.resolution_by_line.map((r) => ({ label: r.line, value: r.hours, sub: `${r.cases} cases` }))}
              suffix=" h"
            />
            <div className="divider" />
            <div className="row between">
              <span className="xsmall soft">Pilot store</span>
              <span className="xsmall mono">{localStats.cases} cases · {localStats.approved} approved</span>
            </div>
            <div className="row between mt8">
              <span className="xsmall soft">Corrections captured</span>
              <span className="xsmall mono">{localStats.corrections} rejection(s) in this session</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Pilot scorecard</h3><span className="sub">90-day gate</span></div>
          <div className="panel-body">
            <div className="row gap12" style={{ alignItems: "center" }}>
              <Donut value={data.cause_accuracy} label={pct(data.cause_accuracy)} />
              <div style={{ flex: 1 }}>
                <div className="small" style={{ color: "var(--ink-2)" }}>First-cause acceptance</div>
                <div className="xsmall soft">Target 75% · measured against engineer acceptance</div>
                <div className="meter green mt8"><i style={{ width: `${data.cause_accuracy * 100}%` }} /></div>
              </div>
            </div>
            <div className="divider" />
            <div className="col gap6">
              <div className="row between"><span className="xsmall muted">Speed-up</span><b className="mono" style={{ color: "var(--cyan)" }}>{speedup.toFixed(1)}×</b></div>
              <div className="row between"><span className="xsmall muted">Engineer hours saved</span><b className="mono">{data.engineer_hours_saved}</b></div>
              <div className="row between"><span className="xsmall muted">Realised savings</span><b className="mono">{eur(savings)}</b></div>
              <div className="row between"><span className="xsmall muted">In pipeline</span><b className="mono">{eur(pipeline)}</b></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid g2 mb16" style={{ alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head"><h3>Alerts & trends</h3><span className="sub">threshold watch</span></div>
          <div className="panel-body col gap8">
            {pack.alerts.map((a) => {
              const ack = a.acknowledged || alertsAck.includes(a.id);
              return (
                <div key={a.id} className="row" style={{ alignItems: "flex-start", gap: 9, padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,.05)", opacity: ack ? 0.5 : 1 }}>
                  <span className={`dot ${a.level === "critical" ? "bad" : a.level === "warning" ? "warn" : "live"}`} style={{ marginTop: 5 }} />
                  <div style={{ flex: 1 }}>
                    <div className="small" style={{ color: "var(--ink-2)", fontWeight: 600 }}>{a.title}</div>
                    <div className="xsmall soft">{a.detail}</div>
                  </div>
                  {ack ? <span className="chip" style={{ fontSize: 8 }}>acknowledged</span> : (
                    <button className="btn sm ghost" onClick={() => acknowledge(a.id)}>Ack</button>
                  )}
                </div>
              );
            })}
            <div className="divider" />
            <div className="xsmall soft" style={{ letterSpacing: ".1em", textTransform: "uppercase" }}>Trend alerts</div>
            <div className="small muted">Defect rate on Line 6 is 1.8σ above its own 8-week mean. The dashboard flags it before it becomes a case.</div>
            <div className="row gap8 mt8">
              <span className="chip red">Line 6 · warning</span>
              <span className="chip amber">Line 2 · moisture</span>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Corrective actions</h3><span className="sub">{actions.filter((a) => a.status !== "done").length} open</span></div>
          <div className="panel-body" style={{ padding: 0 }}>
            <table className="table">
              <thead><tr><th>Action</th><th>Owner</th><th>Due</th><th>Saving</th><th /></tr></thead>
              <tbody>
                {actions.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div className="small" style={{ color: "var(--ink-2)" }}>{a.title}</div>
                      <div className="xsmall soft mono">{a.case_id} · {a.id}</div>
                    </td>
                    <td className="small muted">{a.owner}</td>
                    <td className="xsmall muted nowrap">{fmtDate(a.due)}</td>
                    <td className="small mono">{eur(a.saving_eur)}</td>
                    <td>
                      {a.status === "done" ? <span className="chip green" style={{ fontSize: 8 }}>done</span> : (
                        <button className="btn sm ghost" onClick={() => completeAction(a.id)}>Done</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="grid g3">
        <div className="panel">
          <div className="panel-head"><h3>Baseline on day one</h3><span className="sub">per line</span></div>
          <div className="panel-body">
            <p className="small muted">The pilot starts by measuring the existing investigation time. No baseline, no claim.</p>
            <div className="field mt12">
              <label>Line</label>
              <select className="select" value={baselineLine} onChange={(e) => setBaselineLine(e.target.value)}>
                {pack.lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div className="field mt8">
              <label>Current median hours per case</label>
              <input className="input" type="number" min={1} value={baselineValue} onChange={(e) => setBaselineValue(e.target.value)} />
            </div>
            <button className="btn primary sm mt12" onClick={() => setBaseline(baselineLine, Number(baselineValue) || 1)}>
              <Icon name="check" size={11} /> Record baseline
            </button>
            <div className="divider" />
            <div className="xsmall mono soft">Recorded at kick-off: {hours(pack.dashboard.baseline_hours_to_cause)} median · 4 lines</div>
            {Object.keys(baselines).length > 0 && (
              <div className="col gap4 mt8">
                {Object.entries(baselines).map(([lineId, value]) => (
                  <div key={lineId} className="row between">
                    <span className="xsmall soft">{pack.lines.find((l) => l.id === lineId)?.name ?? lineId}</span>
                    <span className="xsmall mono">{hours(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Cross-line patterns</h3><span className="sub">same cause, different line</span></div>
          <div className="panel-body">
            {["Gas porosity", "Material moisture", "Tool wear"].map((cause, i) => (
              <div key={cause} className="row between" style={{ padding: "7px 0", borderBottom: i < 2 ? "1px solid rgba(255,255,255,.05)" : "none" }}>
                <div>
                  <div className="small" style={{ color: "var(--ink-2)" }}>{cause}</div>
                  <div className="xsmall soft">seen on {i + 2} lines · shared pattern</div>
                </div>
                <Sparkline values={[3, 4, 3, 5, 4, 6, 5, 7]} color={i === 0 ? "#ffb454" : "#5eead4"} width={70} height={26} />
              </div>
            ))}
            <Link className="btn ghost sm mt12" to="/admin">Anonymised sharing settings <Icon name="arrow" size={11} /></Link>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>This week, in one line</h3><span className="sub">for the plant manager</span></div>
          <div className="panel-body">
            <p style={{ fontSize: 14, lineHeight: 1.55, color: "var(--ink-2)" }}>
              “RootCause cut time to cause from <b className="amber">{hours(pack.dashboard.baseline_hours_to_cause)}</b> to{" "}
              <b className="cyan">{hours(pack.dashboard.median_hours_to_cause)}</b> across four lines, with{" "}
              <b>{pct(pack.dashboard.cause_accuracy)}</b> of first causes accepted by the engineer and{" "}
              <b>{eur(savings + pipeline)}</b> of scrap and rework in motion.”
            </p>
            <div className="row between mt16">
              <span className="xsmall soft">Audit events</span>
              <span className="xsmall mono">{audits().length}</span>
            </div>
            <div className="row between mt8">
              <span className="xsmall soft">Data leaves the site</span>
              <span className="xsmall mono green">never</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
