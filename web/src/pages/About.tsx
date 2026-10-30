import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { Icon } from "../components/Icon";

export default function About() {
  const { pack, proactive } = useStore();
  return (
    <div>
      <div className="panel" style={{ padding: "clamp(24px, 4vw, 46px)", position: "relative", overflow: "hidden", background: "radial-gradient(80% 120% at 0% 0%, rgba(255,180,84,.09), transparent 55%), rgba(255,255,255,.016)" }}>
        <div style={{ maxWidth: 800 }}>
          <div className="xsmall mono amber" style={{ letterSpacing: ".22em", textTransform: "uppercase" }}>RootCause · AI quality engineer</div>
          <h1 style={{ fontSize: "clamp(30px, 4.6vw, 54px)", letterSpacing: "-.04em", lineHeight: 1.02, margin: "12px 0 14px" }}>
            It wasn't fatigue.<br />It started in the casting.
          </h1>
          <p style={{ color: "var(--ink-2)", fontSize: 15, lineHeight: 1.6, maxWidth: 680 }}>
            When a factory finds a bad part, RootCause gathers the machine, material, maintenance and
            history evidence, ranks the likely causes, and writes the quality report — in hours, not days.
            The engineer stays in charge.
          </p>
          <div className="row gap8 mt16" style={{ flexWrap: "wrap" }}>
            <Link className="btn primary lg" to="/stage"><Icon name="play" size={14} /> Play the 90-second piece</Link>
            <Link className="btn lg" to="/booth"><Icon name="booth" size={14} /> Open the functional demo</Link>
            <a className="btn lg ghost" href="https://github.com/jiuwendemos/rootcause" target="_blank" rel="noreferrer">Repository <Icon name="external" size={12} /></a>
          </div>
          <div className="row gap6 mt16" style={{ flexWrap: "wrap" }}>
            <span className="chip"><span className="dot" /> Runs offline · no outbound network</span>
            <span className="chip">Evidence first</span>
            <span className="chip">Human-approved</span>
            <span className="chip">Synthetic public data</span>
          </div>
        </div>
        <div style={{ position: "absolute", right: -60, bottom: -80, width: 340, height: 340, borderRadius: "50%", border: "1px solid rgba(255,180,84,.16)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", right: 10, bottom: -120, width: 240, height: 240, borderRadius: "50%", border: "1px dashed rgba(94,234,212,.18)", pointerEvents: "none" }} />
      </div>

      <div className="grid g3 mt16">
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">THE PROBLEM</div>
          <h3 style={{ margin: "8px 0 6px", fontSize: 18 }}>A camera sees the defect in a second. The cause takes days.</h3>
          <p className="small muted" style={{ lineHeight: 1.6 }}>Engineers dig through machine settings, material batches, maintenance logs, old defects and operator notes. Then they meet, guess, test and write a report. Knowledge walks out when they do.</p>
        </div></div>
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">THE PRODUCT</div>
          <h3 style={{ margin: "8px 0 6px", fontSize: 18 }}>A case file, not a dashboard.</h3>
          <p className="small muted" style={{ lineHeight: 1.6 }}>Photos, charts, likely causes, evidence, a draft quality report and a record of who approved what. The unit of work is the case, and the case is auditable.</p>
        </div></div>
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">THE DIFFERENCE</div>
          <h3 style={{ margin: "8px 0 6px", fontSize: 18 }}>Evidence-weighted, not a confident chatbot.</h3>
          <p className="small muted" style={{ lineHeight: 1.6 }}>Every cause cites evidence IDs. A “none of these” bucket keeps confidence honest. The engineer can reject the AI and watch the ranking recompute.</p>
        </div></div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>How it works</h3><span className="sub">on-site, in the factory network</span></div>
        <div className="panel-body grid g3">
          {[
            ["01", "A camera sees a defect", "The NPU checks the image on site. The bounding box and confidence are saved with the case."],
            ["02", "The agent gathers facts", "Machine window, material batch, maintenance record, similar past defects. Every read is logged with its source."],
            ["03", "The causes are ranked", "Frequency, deviation magnitude, batch match, similar-case match and recurrence. Each factor is visible."],
            ["04", "The evidence is shown", "Photos, charts and similar cases. The x-ray is one depth control away from the surface."],
            ["05", "The engineer decides", "Accept, reject or add a cause. Rejections lower the weight and feed the next ranking iteration."],
            ["06", "The report is signed", "Inline edit, version every save, export PDF or Word. The approval carries a name, a time and a model version."],
          ].map(([n, t, b]) => (
            <div key={n} className="feature">
              <div className="num">{n}</div>
              <h3>{t}</h3>
              <p>{b}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel mt16" style={{ background: "radial-gradient(80% 120% at 0% 0%, rgba(94,234,212,.06), transparent 55%), rgba(255,255,255,.016)" }}>
        <div className="panel-body" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
          <div style={{ maxWidth: 720 }}>
            <div className="xsmall mono cyan" style={{ letterSpacing: ".16em" }}>PHASE 4 · PROACTIVE QUALITY</div>
            <h3 style={{ fontSize: 22, margin: "6px 0 5px" }}>The defect is late. The signal was early.</h3>
            <p className="small muted" style={{ lineHeight: 1.6 }}>
              RootCause now watches process changes, drift, batch risk and coverage, opens a watch case
              before the next bad part, assembles the evidence and recommends containment. The engineer
              approves. No line control, no automatic rejection. Prediction stays behind a stopped
              research gate.
            </p>
            <div className="row gap6 mt12" style={{ flexWrap: "wrap" }}>
              <span className="chip amber">{proactive?.watches.length ?? 0} watches</span>
              <span className="chip green">{proactive ? Math.round(proactive.metrics.watch_precision * 100) : 0}% precision</span>
              <span className="chip cyan">{proactive?.metrics.median_triage_min ?? 0} min triage</span>
              <span className="chip red">prediction stopped</span>
            </div>
          </div>
          <div className="row gap8">
            <Link className="btn primary" to="/watchlist">Open the watchlist</Link>
            <Link className="btn" to="/booth/proactive">Run the proactive story</Link>
          </div>
        </div>
      </div>

      <div className="grid g2 mt16" style={{ alignItems: "stretch" }}>
        <div className="panel">
          <div className="panel-head"><h3>The trust beat</h3><span className="sub">mandatory, not a nice-to-have</span></div>
          <div className="panel-body">
            <p className="small" style={{ color: "var(--ink-2)", lineHeight: 1.65 }}>
              The first hypothesis is <b className="amber">tool mark / operator error</b>. It is plausible: there is a
              machining ridge near the crack, and it is the kind of answer a quality manager hears every week.
            </p>
            <p className="small muted mt8" style={{ lineHeight: 1.65 }}>
              The engineer rejects it for a visible reason: the crack starts <b>0.4 mm below the surface</b>;
              tool marks are surface-only. The system re-ranks in the same scene to <b className="cyan">gas porosity</b>,
              aligned with the crack path. The correction is saved. It was confident. It was wrong.
            </p>
            <Link className="btn mt12" to="/stage"><Icon name="play" size={12} /> See it run</Link>
          </div>
        </div>
        <div className="panel">
          <div className="panel-head"><h3>What the customer gets</h3><span className="sub">per defect</span></div>
          <div className="panel-body grid g2" style={{ gap: 8 }}>
            {[
              ["Photos", "Optical and x-ray, with findings"],
              ["Charts", "The machine window, not a screenshot"],
              ["Causes", "Ranked, with confidence and factors"],
              ["Evidence", "Every claim cites an ID"],
              ["Draft report", "Editable, versioned, exportable"],
              ["Approvals", "Who approved what, and when"],
              ["Similar cases", "The 6-month history"],
              ["Audit trail", "Append-only at the database"],
            ].map(([t, b]) => (
              <div key={t} className="row" style={{ alignItems: "flex-start", gap: 7 }}>
                <Icon name="check" size={12} />
                <div><b className="small" style={{ color: "var(--ink-2)" }}>{t}</b><div className="xsmall soft">{b}</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>What is built, honestly</h3><span className="sub">status: public proof · pilot-ready workflow · not a production line</span></div>
        <div className="panel-body grid g4">
          <div className="feature"><div className="num">DEMO</div><h3>Fully playable</h3><p>Stage piece, four scenarios, case workspace, review, report exports, dashboard, connectors, admin. Runs offline from a fixed seed.</p></div>
          <div className="feature"><div className="num">CODE</div><h3>Real engine</h3><p>FastAPI + SQLite, evidence ranking, append-only audit, OPC-UA/Modbus/camera adapters, deterministic detector, PDF/Word export.</p></div>
          <div className="feature"><div className="num">PILOT</div><h3>90 days</h3><p>One line, one defect type, one factory. Baseline on day one, weekly accuracy review, on-site deployment. Not automatic line control.</p></div>
          <div className="feature"><div className="num">NEXT</div><h3>The connections</h3><p>The first pilot should start with a quality manager in injection moulding or electronics who already has Keyence cameras and OPC-UA SCADA.</p></div>
        </div>
      </div>

      <div className="grid g3 mt16">
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">WHO BUYS</div>
          <h3 style={{ margin: "7px 0 5px", fontSize: 15 }}>Quality manager, plant manager, manufacturing engineer</h3>
          <p className="small muted">The budget comes from less scrap, less rework, fewer recalls, less downtime and fewer engineer hours.</p>
        </div></div>
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">BUSINESS MODEL</div>
          <h3 style={{ margin: "7px 0 5px", fontSize: 15 }}>Per line, per month</h3>
          <p className="small muted">Setup and integration fee. Optional on-site NPU server. Start with one line, one defect type, one factory.</p>
          <Link className="btn ghost sm mt8" to="/admin">See the commercial model <Icon name="arrow" size={11} /></Link>
        </div></div>
        <div className="panel"><div className="panel-body">
          <div className="xsmall mono soft">NOT PLANNED</div>
          <h3 style={{ margin: "7px 0 5px", fontSize: 15 }}>No line control. No automatic rejection.</h3>
          <p className="small muted">The engineer decides. The existing rejection system stays. Factory data does not leave the site. RootCause only investigates.</p>
        </div></div>
      </div>

      <div className="panel mt16" style={{ background: "linear-gradient(180deg, rgba(94,234,212,.04), rgba(255,255,255,.01))" }}>
        <div className="panel-body" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div>
            <div className="xsmall mono cyan" style={{ letterSpacing: ".16em" }}>PILOT IN 90 DAYS</div>
            <h3 style={{ fontSize: 21, margin: "6px 0 4px" }}>One line. One defect type. One factory.</h3>
            <p className="small muted">Baseline the current investigation time, connect OPC-UA and the inspection camera, prove the hours saved.</p>
          </div>
          <div className="row gap8">
            <Link className="btn primary" to="/dashboard">Open the pilot dashboard</Link>
            <a className="btn" href="mailto:hello@rootcause.example?subject=RootCause%20pilot">Book a pilot</a>
          </div>
        </div>
      </div>

      <div className="row between mt24" style={{ paddingTop: 14, borderTop: "1px solid var(--line)", flexWrap: "wrap", gap: 10 }}>
        <span className="xsmall soft">© 2026 RootCause · public demo data is synthetic · MIT licence</span>
        <span className="xsmall mono soft">
          pack {pack?.meta.version ?? "0.9.0"} · seed {pack?.meta.seed ?? 417} · {pack?.meta.model ?? "rootcause-detector-0.9"}
        </span>
      </div>
    </div>
  );
}
