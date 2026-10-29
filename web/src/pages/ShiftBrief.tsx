import { useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDateTime } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";
import type { ShiftBrief } from "../types";

function briefMarkdown(b: ShiftBrief) {
  return [
    `# ${b.title}`,
    "",
    b.summary,
    "",
    "## Top risks",
    "",
    ...(b.top_risks.length ? b.top_risks.map((r) => `- **${r.title}** (${r.severity}) — ${r.action} · \`${r.watch_id}\``) : ["- None."]),
    "",
    "## Open cases",
    "",
    ...(b.open_cases.length ? b.open_cases.map((c) => `- ${c.case_id} · ${c.title} · ${c.status}`) : ["- None."]),
    "",
    "## Actions due",
    "",
    ...(b.actions_due.length ? b.actions_due.map((a) => `- ${a.title} · ${a.owner} · due ${a.due}`) : ["- None."]),
    "",
    "## Fixed but not verified",
    "",
    ...(b.fixed_not_verified.length ? b.fixed_not_verified.map((f) => `- ${f.title} · ${f.note}`) : ["- None."]),
    "",
    "## Coverage",
    "",
    b.coverage_note,
    "",
    "---",
    "Recommendations only. No automatic line control, rejection or batch hold.",
  ].join("\n");
}

export default function ShiftBriefPage() {
  const { proactive, pack, generateBrief, say } = useStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [shift, setShift] = useState("B");
  const [lines, setLines] = useState<string[]>(pack?.lines.map((l) => l.id) ?? []);

  if (!proactive) return <div className="empty">Loading shift brief…</div>;
  const briefs = proactive.briefs;
  const current = briefs.find((b) => b.id === selectedId) ?? briefs[0];

  function download(b: ShiftBrief) {
    const blob = new Blob([briefMarkdown(b)], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${b.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
    say("Shift brief downloaded");
  }

  return (
    <div>
      <PageHead
        kicker="Proactive · shift handover"
        title="Start the shift with the risks, not the inbox"
        subtitle="A generated brief for the quality team: top watches, open cases, actions due, and fixes that are not verified yet. Printable, mobile-readable, and generated from the same evidence as the cases."
        actions={
          <>
            <button className="btn sm" onClick={() => current && window.print()}><Icon name="download" size={11} /> Print</button>
            <button className="btn sm" onClick={() => current && download(current)}>Markdown</button>
            <button
              className="btn primary sm"
              onClick={() => {
                const b = generateBrief(shift, lines);
                if (b) setSelectedId(b.id);
              }}
            >
              <Icon name="refresh" size={11} /> Generate brief
            </button>
          </>
        }
      />

      <div className="grid" style={{ gridTemplateColumns: "260px 1fr", alignItems: "start" }}>
        <div className="col gap12 noprint">
          <div className="panel">
            <div className="panel-head"><h3>Briefs</h3><span className="sub">{briefs.length}</span></div>
            <div className="panel-body tight">
              <div className="col gap6">
                {briefs.map((b) => (
                  <button key={b.id} className={`ev-card ${current?.id === b.id ? "sel" : ""}`} style={{ textAlign: "left", font: "inherit" }} onClick={() => setSelectedId(b.id)}>
                    <div className="row between"><span className="eid">{b.id}</span><span className="chip" style={{ fontSize: 11 }}>shift {b.shift}</span></div>
                    <h4>{b.title}</h4>
                    <p>{fmtDateTime(b.at)} · {b.top_risks.length} risks</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Generate</h3><span className="sub">same data, new shift</span></div>
            <div className="panel-body">
              <div className="field">
                <label>Shift</label>
                <select className="select" value={shift} onChange={(e) => setShift(e.target.value)}>
                  <option value="A">Shift A</option>
                  <option value="B">Shift B</option>
                  <option value="C">Shift C</option>
                </select>
              </div>
              <div className="field mt8">
                <label>Lines</label>
                <div className="col gap4 mt8">
                  {pack?.lines.map((l) => (
                    <label key={l.id} className="row xsmall muted" style={{ cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={lines.includes(l.id)}
                        onChange={(e) => setLines((prev) => e.target.checked ? [...prev, l.id] : prev.filter((x) => x !== l.id))}
                      />
                      {l.name}
                    </label>
                  ))}
                </div>
              </div>
              <button className="btn primary block mt12" onClick={() => { const b = generateBrief(shift, lines); if (b) setSelectedId(b.id); }}>Generate</button>
              <div className="xsmall soft mt8">The brief is generated from the current watchlist, cases, actions and follow-ups.</div>
            </div>
          </div>
        </div>

        {current ? (
          <div className="report-preview" style={{ background: "#f7f3ea", color: "#22211d" }}>
            <div className="kicker">{current.id} · shift {current.shift} · {fmtDateTime(current.at)}</div>
            <h1>{current.title}</h1>
            <div className="summary" style={{ marginTop: 10 }}>{current.summary}</div>

            <h2>Top risks</h2>
            {current.top_risks.length ? current.top_risks.map((r) => (
              <div key={r.watch_id} className="row between" style={{ padding: "7px 0", borderBottom: "1px solid #e6ddcc", gap: 10, alignItems: "flex-start" }}>
                <div>
                  <b style={{ fontSize: 12 }}>{r.title}</b>
                  <div style={{ fontSize: 11, color: "#6d6558" }}>{r.action}</div>
                </div>
                <div className="row gap6">
                  <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "#b07a25" }}>{r.watch_id}</span>
                  <span style={{ fontSize: 11, border: "1px solid #d8cfbd", borderRadius: 4, padding: "2px 5px", textTransform: "uppercase" }}>{r.severity}</span>
                </div>
              </div>
            )) : <p style={{ fontSize: 11 }}>No active watch.</p>}

            <h2>Open cases</h2>
            {current.open_cases.length ? current.open_cases.map((c) => (
              <div key={c.case_id} style={{ fontSize: 11, padding: "5px 0", borderBottom: "1px solid #e6ddcc" }}>
                <b>{c.case_id}</b> · {c.title} · {c.status}
              </div>
            )) : <p style={{ fontSize: 11 }}>None.</p>}

            <h2>Actions due</h2>
            {current.actions_due.length ? current.actions_due.map((a) => (
              <div key={a.action_id} style={{ fontSize: 11, padding: "5px 0", borderBottom: "1px solid #e6ddcc" }}>
                {a.title} · {a.owner} · due {a.due.slice(0, 10)}
              </div>
            )) : <p style={{ fontSize: 11 }}>None.</p>}

            <h2>Fixed but not verified</h2>
            {current.fixed_not_verified.length ? current.fixed_not_verified.map((f) => (
              <div key={f.case_id} style={{ fontSize: 11, padding: "5px 0", borderBottom: "1px solid #e6ddcc" }}>
                <b>{f.title}</b> · {f.note}
              </div>
            )) : <p style={{ fontSize: 11 }}>Nothing waiting.</p>}

            <h2>Coverage</h2>
            <p style={{ fontSize: 11 }}>{current.coverage_note}</p>

            <div style={{ marginTop: 20, borderTop: "1px solid #d8cfbd", paddingTop: 9, fontSize: 11, color: "#8a7f6c", display: "flex", justifyContent: "space-between" }}>
              <span>{current.generated_by}</span>
              <span>Recommendations only · no line control</span>
            </div>
          </div>
        ) : <div className="empty">No brief yet.</div>}
      </div>

      <div className="row between mt16">
        <Link className="btn ghost sm" to="/watchlist"><Icon name="arrow" size={11} style={{ transform: "rotate(180deg)" }} /> Watchlist</Link>
        <span className="xsmall mono soft">Print layout fits one page</span>
      </div>
    </div>
  );
}
