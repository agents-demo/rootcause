import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, fmtDateTime, fmtDate } from "../lib/engine";
import type { Report } from "../types";
import { Icon } from "../components/Icon";
import { ChainViz, PageHead, ProvenanceBlock, StatusBadge } from "../components/UI";

function escapeHtml(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function download(name: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const { pack, investigation, reportFor, patchReport, approveReport, audits, say, live } = useStore();
  const [params] = useSearchParams();
  const initial = params.get("case") ?? pack?.scenarios[0]?.case.id ?? "RC-0417";
  const [caseId, setCaseId] = useState(initial);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Report | null>(null);

  const rows = useMemo(() => {
    if (!pack) return [];
    return pack.scenarios.map((s) => {
      const rep = reportFor(s.case.id);
      const inv = investigation(s.case.id);
      return { s, rep, inv, top: inv?.hypotheses.find((h) => h.status !== "rejected") };
    });
  }, [pack, reportFor, investigation]);

  const current = rows.find((r) => r.s.case.id === caseId) ?? rows[0];
  if (!pack || !current || !current.rep) return <div className="empty">Loading reports…</div>;

  const report = current.rep;
  const scenario = current.s;
  const inv = current.inv!;
  const causeAccepted = inv.hypotheses.some((h) => h.status === "accepted");

  const apiUrl = (path: string) => new URL(`api/${path}`, document.baseURI).toString();

  function liveDownload(kind: string, extension: string) {
    const a = document.createElement("a");
    a.href = apiUrl(`reports/${caseId}/${kind}`);
    a.download = `${report.id}.${extension}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    say(`Downloading ${extension.toUpperCase()} from the on-site API`);
  }

  function startEdit() {
    setDraft(JSON.parse(JSON.stringify(report)) as Report);
    setEditing(true);
  }

  function saveEdit() {
    if (!draft) return;
    patchReport(caseId, { title: draft.title, summary: draft.summary, sections: draft.sections });
    setEditing(false);
    setDraft(null);
  }

  function buildHtml() {
    const evidence = scenario.evidence
      .filter((e) => inv.hypotheses[0]?.evidence_ids.includes(e.id) || ["EV-01", "EV-02", "EV-04"].includes(e.id))
      .slice(0, 6);
    const sections = report.sections
      .map((s) => `<h2>${escapeHtml(s.heading)}</h2><p>${escapeHtml(s.body).replace(/\n/g, "<br>")}</p>`)
      .join("");
    return `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(report.title)}</title>
<style>body{margin:0;background:#e9e4d8;color:#22211d;font:15px/1.6 system-ui,sans-serif}.sheet{max-width:820px;margin:28px auto;background:#f7f3ea;padding:46px 52px;border-left:5px solid #b07a25;position:relative}h1{font-size:31px;letter-spacing:-.02em;margin:8px 0}.kicker{font:11px monospace;letter-spacing:.2em;text-transform:uppercase;color:#8a7f6c}.meta{color:#6a6357;font-size:12px;margin-bottom:20px}.summary{font-size:16px;border-left:2px solid #d8cfbd;padding-left:14px;margin:18px 0}h2{font-size:12px;text-transform:uppercase;letter-spacing:.14em;color:#8a7f6c;margin:24px 0 6px}li{font-size:13px;margin:8px 0}.chain span{border:1px solid #d8cfbd;background:#fffdf8;padding:6px 9px;border-radius:4px;font-size:12px;margin-right:6px}.stamp{position:absolute;right:46px;top:36px;border:2px solid #2f6b4f;color:#2f6b4f;padding:8px 12px;transform:rotate(-6deg);font:700 12px monospace;letter-spacing:.16em}.foot{margin-top:28px;border-top:1px solid #d8cfbd;padding-top:12px;font-size:10px;color:#8a7f6c}</style>
</head><body><main class="sheet"><div class="kicker">${escapeHtml(report.case_id)} · quality report · v${report.version}</div>
<h1>${escapeHtml(report.title)}</h1><div class="meta">Status: ${report.status.replace("_", " ")} · Generated ${new Date().toLocaleString()}</div>
${report.status === "approved" ? '<div class="stamp">APPROVED</div>' : ""}
<div class="summary">${escapeHtml(report.summary)}</div>${sections}
<div class="chain">${scenario.chain.nodes.map((n) => `<span>${escapeHtml(n.label)}</span>`).join(" → ")}</div>
<h2>Evidence appendix</h2><ul>${evidence.map((e) => `<li><b>${escapeHtml(e.id)} ${escapeHtml(e.title)}</b> — ${escapeHtml(e.detail)} <i>(${escapeHtml(e.source)})</i></li>`).join("")}</ul>
<div class="foot">Prepared with RootCause. The engineer owns the approved cause; no automatic line control is performed.</div></main></body></html>`;
  }

  function buildMarkdown() {
    return [
      `# ${report.title}`,
      "",
      `*Case ${report.case_id} · report v${report.version} · ${report.status}*`,
      "",
      report.summary,
      "",
      ...report.sections.flatMap((s) => [`## ${s.heading}`, "", s.body, ""]),
      "## Evidence appendix",
      "",
      ...scenario.evidence.slice(0, 6).map((e) => `- **${e.id} · ${e.title}** — ${e.detail} *(${e.source})*`),
      "",
      "---",
      "Prepared with RootCause. The engineer owns the approved cause; no automatic line control is performed.",
    ].join("\n");
  }

  function buildRtf() {
    const esc = (t: string) => t.replace(/\\/g, "\\\\").replace(/{/g, "\\{").replace(/}/g, "\\}").replace(/\n/g, "\\par ");
    const body = [
      "{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Segoe UI;}}",
      `\\fs36\\b ${esc(report.title)}\\b0\\par`,
      `\\fs20 ${esc(`${report.case_id} · v${report.version} · ${report.status}`)}\\par`,
      `${esc(report.summary)}\\par`,
      ...report.sections.map((s) => `\\fs26\\b ${esc(s.heading)}\\b0\\fs20\\par ${esc(s.body)}\\par`),
      "}",
    ].join("\n");
    return body;
  }

  return (
    <div>
      <PageHead
        kicker="Quality reports"
        title="The report is the deliverable"
        subtitle="The cause is the climax; the signed report is what the quality system keeps. Edit inline, version every change, export in the customer's format."
        actions={
          <>
            <span className="chip green"><Icon name="shield" size={11} /> Human sign-off</span>
            <span className="chip">{report.status === "approved" ? "Signed" : "Draft"}</span>
          </>
        }
      />

      <div className="grid" style={{ gridTemplateColumns: "280px 1fr", alignItems: "start" }}>
        <div className="panel noprint">
          <div className="panel-head"><h3>Reports</h3><span className="sub">{rows.length}</span></div>
          <div className="panel-body tight">
            <div className="col gap6">
              {rows.map((r) => (
                <button
                  key={r.s.case.id}
                  className={classNames("ev-card", r.s.case.id === caseId && "sel")}
                  style={{ textAlign: "left", font: "inherit" }}
                  onClick={() => { setCaseId(r.s.case.id); setEditing(false); setDraft(null); }}
                >
                  <div className="row between">
                    <span className="eid">{r.s.case.id}</span>
                    <StatusBadge status={r.rep?.status ?? "draft"} />
                  </div>
                  <h5>{r.s.case.defect_type}</h5>
                  <p>{r.top?.label} · v{r.rep?.version}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="col-stack">
          <div className="panel noprint">
            <div className="panel-body" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <StatusBadge status={report.status} />
              <span className="xsmall soft">v{report.version} · {report.edits} edits</span>
              {report.approved_by && <span className="chip green"><Icon name="check" size={10} /> {report.approved_by} · {fmtDateTime(report.approved_at)}</span>}
              <div style={{ flex: 1 }} />
              {!editing ? (
                <>
                  <button className="btn sm" onClick={startEdit}><Icon name="file" size={12} /> Edit inline</button>
                  <button className="btn sm primary" onClick={() => { approveReport(caseId); }} disabled={report.status === "approved" || !causeAccepted} title={!causeAccepted ? "Accept a cause in the case before signing the report" : "Sign off"}>
                    <Icon name="check" size={12} /> {report.status === "approved" ? "Signed off" : "Sign off"}
                  </button>
                </>
              ) : (
                <>
                  <button className="btn sm ghost" onClick={() => { setEditing(false); setDraft(null); }}>Cancel</button>
                  <button className="btn sm primary" onClick={saveEdit}><Icon name="check" size={12} /> Save new version</button>
                </>
              )}
              <button className="btn sm" onClick={() => (live ? liveDownload("pdf", "pdf") : window.print())}><Icon name="download" size={12} /> Print / PDF</button>
              <button className="btn sm" onClick={() => { if (live) { window.open(apiUrl(`reports/${caseId}/html`), "_blank"); } else { download(`${report.id}.html`, buildHtml(), "text/html"); say("HTML report downloaded"); } }}>HTML</button>
              <button className="btn sm" onClick={() => { if (live) { liveDownload("markdown", "md"); } else { download(`${report.id}.md`, buildMarkdown(), "text/markdown"); say("Markdown report downloaded"); } }}>MD</button>
              <button className="btn sm" onClick={() => { if (live) { liveDownload("docx", "docx"); } else { download(`${report.id}.rtf`, buildRtf(), "application/rtf"); say("Word-compatible RTF downloaded"); } }}>Word</button>
            </div>
          </div>

          {editing && draft ? (
            <div className="panel report-edit">
              <div className="panel-head"><h3>Edit report</h3><span className="sub">a new version is created on save</span></div>
              <div className="panel-body">
                <div className="field mb12"><label>Title</label><input className="input doc" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} /></div>
                <div className="field mb12"><label>Summary</label><textarea className="textarea doc" value={draft.summary} onChange={(e) => setDraft({ ...draft, summary: e.target.value })} /></div>
                {draft.sections.map((s, i) => (
                  <div key={s.id} className="mb12">
                    <div className="field mb8"><label>{s.heading}</label><input className="input doc" value={s.heading} onChange={(e) => { const sections = [...draft.sections]; sections[i] = { ...s, heading: e.target.value }; setDraft({ ...draft, sections }); }} /></div>
                    <textarea className="textarea doc" value={s.body} onChange={(e) => { const sections = [...draft.sections]; sections[i] = { ...s, body: e.target.value }; setDraft({ ...draft, sections }); }} />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="report-preview" style={{ position: "relative" }}>
              {report.status === "approved" && <div className="stamp">APPROVED</div>}
              <div className="kicker">{report.case_id} · quality report · v{report.version}</div>
              <h1>{report.title}</h1>
              <div className="meta">
                Status: {report.status.replace("_", " ")} · Generated {fmtDate(new Date().toISOString())} · {" "}
                {report.approved_by ? `Approved by ${report.approved_by}` : "Awaiting engineer sign-off"}
              </div>
              <div className="summary">{report.summary}</div>
              <div style={{ margin: "12px 0 18px" }}><ChainViz chain={inv.chain} compact /></div>
              {report.sections.map((s) => (
                <section key={s.id}>
                  <h2>{s.heading}</h2>
                  <p style={{ whiteSpace: "pre-line" }}>{s.body}</p>
                </section>
              ))}
              <h2>Evidence appendix</h2>
              <div className="ev" style={{ borderTop: "1px solid #ddd4c2" }}>
                {scenario.evidence.slice(0, 6).map((e) => (
                  <div key={e.id} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: "1px solid #e6ddcc", fontSize: 10.5, color: "#4b463c" }}>
                    <i style={{ fontFamily: "var(--mono)", color: "#b07a25", fontStyle: "normal", minWidth: 44 }}>{e.id}</i>
                    <span><b>{e.title}</b> — {e.detail} <i>({e.source})</i></span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 20, borderTop: "1px solid #d8cfbd", paddingTop: 10, fontSize: 9.5, color: "#8a7f6c", display: "flex", justifyContent: "space-between" }}>
                <span>Prepared with RootCause · engineer owns the decision · no line control</span>
                <span>{report.approved_at ? fmtDateTime(report.approved_at) : "DRAFT · not signed"}</span>
              </div>
            </div>
          )}

          <div className="grid g2 noprint">
            <div className="panel">
              <div className="panel-head"><h3>Report versions</h3><span className="sub">append-only store</span></div>
              <div className="panel-body">
                <div className="row between" style={{ padding: "6px 0" }}>
                  <span className="small">v{report.version} · current</span>
                  <span className="xsmall soft">{report.status}</span>
                </div>
                <div className="row between" style={{ padding: "6px 0", borderTop: "1px solid var(--line)" }}>
                  <span className="small muted">v{Math.max(1, report.version - 1)} · prior</span>
                  <span className="xsmall soft">superseded</span>
                </div>
                <p className="xsmall soft mt8">Every save creates a version. The API stores them side by side; the audit trail records who saved and when.</p>
              </div>
            </div>
            <div className="panel">
              <div className="panel-head"><h3>Sign-off record</h3><span className="sub">audit</span></div>
              <div className="panel-body">
                {report.approved_by ? (
                  <>
                    <div className="row" style={{ gap: 8 }}><span className="dot live" /><span className="small"><b>{report.approved_by}</b> approved the report</span></div>
                    <div className="xsmall soft mt8">{fmtDateTime(report.approved_at)} · RPT v{report.version} · model rootcause-0.9.0</div>
                  </>
                ) : (
                  <div className="small muted">Not signed yet. The AI cannot sign; the engineer must.</div>
                )}
                <div className="divider" />
                <ProvenanceBlock items={{ case: report.case_id, model: "rootcause-0.9.0", retention: "local, append-only" }} compact />
                {!causeAccepted && <div className="xsmall amber mt8">Accept a cause in the case first. The report cannot be signed before the engineer decides.</div>}
                <Link className="btn ghost sm mt8" to={`/cases?audit=${caseId}`}>Open audit trail <Icon name="arrow" size={11} /></Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
