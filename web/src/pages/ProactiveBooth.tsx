import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDateTime, pct } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead, ProvenanceBlock } from "../components/UI";

export default function ProactiveBooth() {
  const { proactive, pack } = useStore();
  if (!proactive) return <div className="empty">Loading…</div>;
  const m = proactive.metrics;
  const featured = ["W-1042", "W-1043", "W-1044", "W-1045"].map((id) => proactive.watches.find((w) => w.id === id)).filter(Boolean);

  return (
    <div>
      <PageHead
        kicker="Booth · proactive story"
        title="Catch it before the scrap"
        subtitle="The second act, ten minutes. A risk is visible before the defect, the evidence is already assembled, containment is recommended and a human approves it. No prediction, no line control."
        actions={
          <>
            <Link className="btn sm" to="/watchlist"><Icon name="target" size={11} /> Watchlist</Link>
            <Link className="btn sm primary" to="/watch/W-1042"><Icon name="play" size={11} /> Open the first watch</Link>
          </>
        }
      />

      <div className="panel mb16" style={{ background: "radial-gradient(80% 120% at 0% 0%, rgba(94,234,212,.07), transparent 55%), rgba(255,255,255,.018)" }}>
        <div className="panel-body" style={{ padding: "clamp(18px, 3vw, 30px)" }}>
          <div className="xsmall mono cyan" style={{ letterSpacing: ".18em" }}>THE PROACTIVE STORY</div>
          <h2 style={{ fontSize: "clamp(24px, 3.5vw, 38px)", letterSpacing: "-.03em", margin: "8px 0 10px" }}>
            The defect is late. The signal was early.
          </h2>
          <p className="small" style={{ color: "var(--ink-2)", maxWidth: 780, lineHeight: 1.6 }}>
            On 22 October, hydrogen crossed 1.4 ppm five hours before the bracket fractured. Batch B-2291
            was already in the plant. The watch assembled the trend, the seal repair, the batch exception and
            the quench step change. The engineer approved a hold at 04:10. The fracture still happened at
            06:42 — but the rest of the batch did not ship.
          </p>
          <div className="row gap8 mt16" style={{ flexWrap: "wrap" }}>
            <span className="chip green"><span className="dot live" /> {pct(m.watch_precision, 0)} precision</span>
            <span className="chip amber">{m.alerts_per_line_shift}/line/shift</span>
            <span className="chip">{m.median_triage_min} min triage</span>
            <span className="chip cyan">{m.defects_prevented_month}/mo prevented</span>
          </div>
        </div>
      </div>

      <div className="grid g2 mb16" style={{ alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head"><h3>The ten-minute run</h3><span className="sub">say this, in order</span></div>
          <div className="panel-body">
            <div className="trace">
              {[
                ["0:00", "The watch is already open", "Hydrogen is above baseline; the seal was replaced 12 days ago. No defect yet."],
                ["1:30", "Why now?", "Open the signals: EWMA, maintenance, batch exception, quench step. Each cites evidence."],
                ["3:00", "The checks", "X-ray the first three castings. Pull a hydrogen sample. Verify the seal."],
                ["4:30", "The recommendation", "Hold B-2291. Twelve parts, three customers. The engineer approves; nobody touches the line."],
                ["6:30", "The defect still happens", "At 06:42 the bracket fractures. The watch converts to RC-0417; the early signal stays attached."],
                ["8:30", "The follow-through", "The seal fix is monitored. The same signature returning reopens a watch."],
                ["9:30", "The line", "It was confident. It was wrong. This is why the engineer stays in charge — and why the batch was already held."],
              ].map(([t, title, body], i) => (
                <div key={title} className="trace-step done">
                  <div className="trace-ico">{i + 1}</div>
                  <div><div className="tt"><span className="mono cyan" style={{ marginRight: 7 }}>{t}</span>{title}</div><div className="td">{body}</div></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col gap12">
          {featured.map((w) => w && (
            <div key={w.id} className="panel">
              <div className="panel-body" style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <div style={{ width: 44, height: 44, borderRadius: 8, background: w.severity === "critical" ? "rgba(248,113,113,.15)" : "rgba(255,180,84,.13)", display: "grid", placeItems: "center", flex: "none", border: "1px solid rgba(255,255,255,.1)" }}>
                  <span className="mono small" style={{ color: w.severity === "critical" ? "var(--red)" : "var(--amber)" }}>{Math.round(w.risk_score * 100)}</span>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="row between"><span className="xsmall mono amber">{w.id} · {w.status}</span><span className="xsmall soft">{fmtDateTime(w.opened_at)}</span></div>
                  <div className="small" style={{ color: "var(--ink-2)", fontWeight: 600 }}>{w.title}</div>
                  <div className="xsmall soft">{w.pattern_name} · {w.signal_count} signals · {w.confidence.toFixed(0)}%</div>
                </div>
                <Link className="btn sm" to={`/watch/${w.id}`}>Open</Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid g3">
        <div className="panel"><div className="panel-body">
          <h3 style={{ fontSize: 15 }}>What is real</h3>
          <p className="small muted">The signal maths, watch workflow, containment approval, audit trail, coverage rules, false-alarm capture and research gate all run in the repo.</p>
        </div></div>
        <div className="panel"><div className="panel-body">
          <h3 style={{ fontSize: 15 }}>What is simulated</h3>
          <p className="small muted">The sensors, watches, exposures, customers and webhook endpoint are synthetic. No factory hardware is attached to the public demo.</p>
        </div></div>
        <div className="panel"><div className="panel-body">
          <h3 style={{ fontSize: 15 }}>What it will not do</h3>
          <p className="small muted">No automatic line control, rejection or batch hold. No prediction unless the research gate validates a lift over SPC.</p>
        </div></div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>Provenance</h3><span className="sub">for Q&A</span></div>
        <div className="panel-body">
          <ProvenanceBlock
            items={pack?.proactive ? {
              data: "Synthetic watches, signals, exposures and notifications, fixed seed 417",
              schedule: `${proactive.settings.schedule.mode} · every ${proactive.settings.schedule.interval_minutes} min`,
              coverage: `${pct(m.coverage_pct, 1)} · floor ${pct(proactive.settings.schedule.coverage_floor, 0)}`,
              guardrail: proactive.settings.contract_note,
            } : {}}
            note="Every alert is a hypothesis with evidence and a falsification note. The engineer decides."
          />
          <div className="row gap8 mt12">
            <Link className="btn sm" to="/brief">Shift brief</Link>
            <Link className="btn sm" to="/proactive">Calibration and research gate</Link>
            <Link className="btn sm" to="/watchlist">Full watchlist</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
