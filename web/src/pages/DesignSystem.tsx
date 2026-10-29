import { useUI } from "../lib/ui";
import { Icon } from "../components/Icon";
import { LineChart } from "../components/Charts";

export default function DesignSystem() {
  const ui = useUI();
  return (
    <div>
      <div className="page-header-2026">
        <div>
          <div className="page-kicker">Living catalogue</div>
          <h1 className="page-title">Interface 2026</h1>
          <p className="page-sub">Type-led, box-light, one accent, semantic colour, command-first. This page is the reference for the daily product — the stage piece is a deliberate exception.</p>
        </div>
        <div className="page-actions-2026">
          <button className="btn" onClick={ui.toggleTheme}>Toggle {ui.theme === "dark" ? "desk" : "control room"}</button>
          <button className="btn" onClick={() => ui.setDensity(ui.density === "compact" ? "comfortable" : "compact")}>{ui.density === "compact" ? "Comfortable" : "Compact"}</button>
        </div>
      </div>

      <div className="small-multiples mb16">
        <div className="small-multiple"><div className="label">Type scale</div><div className="value">44/31/24</div><div className="note">No type below 11 px</div></div>
        <div className="small-multiple"><div className="label">Accent</div><div className="value" style={{ color: "var(--accent)" }}>Amber</div><div className="note">One primary accent</div></div>
        <div className="small-multiple"><div className="label">Semantic</div><div className="value" style={{ color: "var(--ok)" }}>Green</div><div className="note">Approved / verified</div></div>
        <div className="small-multiple"><div className="label">Density</div><div className="value" style={{ fontSize: 18 }}>{ui.density}</div><div className="note">Persisted per user</div></div>
      </div>

      <div className="grid g2">
        <div className="panel">
          <div className="panel-head"><h3>Typography</h3><span className="sub">Inter + JetBrains Mono</span></div>
          <div className="panel-body">
            <h1 style={{ fontSize: 44 }}>It wasn't fatigue.</h1>
            <h2 style={{ fontSize: 31, marginTop: 6 }}>It started in the casting.</h2>
            <h3 style={{ fontSize: 19, marginTop: 8 }}>The engineer decides.</h3>
            <p className="small muted mt12">Body copy is 14–15 px with 1.5 line height. Labels are 11–12 px. Mono is reserved for IDs, numbers and code. There is no 8–9 px text.</p>
            <div className="row gap8 mt12"><span className="mono small">RC-0417</span><span className="tag">EV-04</span><span className="kbd">⌘K</span></div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Controls</h3><span className="sub">44 px touch target</span></div>
          <div className="panel-body">
            <div className="row gap8 wrap mb12">
              <button className="btn primary"><Icon name="check" size={13} /> Approve</button>
              <button className="btn"><Icon name="clock" size={13} /> Snooze</button>
              <button className="btn danger"><Icon name="x" size={13} /> Reject</button>
              <button className="btn ghost">Ghost</button>
            </div>
            <div className="row gap6 wrap mb12">
              <span className="chip amber">evidence</span>
              <span className="chip green">approved</span>
              <span className="chip red">rejected</span>
              <span className="chip">neutral</span>
            </div>
            <div className="grid g2" style={{ gap: 8 }}>
              <div className="field"><label>Threshold</label><input className="input" defaultValue="1.4" aria-label="Demo threshold" /></div>
              <div className="field"><label>Line</label><select className="select" aria-label="Demo line"><option>Line 6</option><option>Line 2</option></select></div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Decision row</h3><span className="sub">queue, not card grid</span></div>
          <div className="panel-body">
            <button className="decision-row" style={{ width: "100%" }}>
              <span className="severity critical" />
              <span><span className="kind">Risk watch · first</span><h3>Hydrogen drift after furnace seal repair</h3><p>4 signals · 88% confidence · M. Weber</p></span>
              <span className="meta"><b>94</b>risk</span>
            </button>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Chart</h3><span className="sub">direct labels, accessible table</span></div>
          <div className="panel-body">
            <LineChart
              series={[{ name: "Hydrogen", color: "var(--accent)", values: [1.1, 1.18, 1.2, 1.4, 1.7, 2.04, 1.9, 1.7], dots: true }]}
              labels={["-30", "-20", "-10", "0", "10", "20", "30", "40"]}
              height={150}
              refHigh={1.4}
              decimals={2}
            />
            <p className="xsmall soft mt8">The spec line is explicit; the series is labelled; a table fallback is available in the product.</p>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Evidence row</h3><span className="sub">margin, not a card</span></div>
          <div className="panel-body">
            <div className="evidence-margin">
              <div className="ev-row"><span className="ev-id">EV-04</span><span><span className="ev-title">Hydrogen above baseline</span><span className="ev-detail">9.6σ through the cast window.</span></span><span className="tag">chart</span></div>
              <div className="ev-row"><span className="ev-id">EV-02</span><span><span className="ev-title">Porosity cluster</span><span className="ev-detail">Six voids, largest 0.8 mm.</span></span><span className="tag">image</span></div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>Ask with evidence</h3><span className="sub">ambient AI, no chatbot</span></div>
          <div className="panel-body">
            <div className="ask-panel">
              <h3>Ask this case</h3>
              <div className="ask-answer-live">The leading cause is gas porosity at 30%, supported by EV-02 and EV-04. The engineer must accept or reject it. <span className="ask-cite">EV-02</span><span className="ask-cite">EV-04</span></div>
              <div className="ask-input"><input className="input" placeholder="Why hydrogen?" aria-label="Ask example" /><button className="btn primary">Ask</button></div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>2026 rules</h3><span className="sub">non-negotiable</span></div>
        <div className="panel-body grid g3">
          {[
            ["No type below 11 px", "Readability over density theatre."],
            ["One accent", "Amber carries action and evidence; green approves; red rejects."],
            ["Boxes recede", "Sections, rules and space before another rounded panel."],
            ["Motion explains", "Signal → watch → case → report. No ambient decoration."],
            ["AI is ambient", "Suggestions and citations, not a chat window."],
            ["Accessible by default", "Focus, keyboard, contrast, reduced motion, 200% zoom."],
          ].map(([t, d]) => (
            <div key={t} className="feature"><h3>{t}</h3><p>{d}</p></div>
          ))}
        </div>
      </div>
    </div>
  );
}
