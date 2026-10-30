import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDateTime, hours } from "../lib/engine";
import { Icon } from "../components/Icon";
import { AuditTrail, PageHead, SeverityBadge, StatusBadge } from "../components/UI";

export default function Cases() {
  const { pack, investigation, caseStatus, audits, say, dataMode } = useStore();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const auditCase = params.get("audit");
  const [query, setQuery] = useState("");
  const [line, setLine] = useState("all");
  const [status, setStatus] = useState("all");

  const rows = useMemo(() => {
    if (!pack) return [];
    return pack.scenarios.map((s) => {
      const inv = investigation(s.case.id);
      const top = inv?.hypotheses.find((h) => h.status !== "rejected");
      return {
        ...s.case,
        scenario: s,
        topCause: top?.label ?? "—",
        confidence: top?.confidence ?? 0,
        status: caseStatus(s.case.id),
        report: s.report.status,
        hoursToCause: s.current_hours,
        baseline: s.baseline_hours,
      };
    });
  }, [pack, investigation, caseStatus]);

  const filtered = rows.filter((r) => {
    const hay = `${r.id} ${r.part} ${r.defect_type} ${r.serial} ${r.batch_id} ${r.topCause}`.toLowerCase();
    return (
      hay.includes(query.toLowerCase()) &&
      (line === "all" || r.line_id === line) &&
      (status === "all" || r.status === status)
    );
  });

  function exportCsv() {
    const header = ["case_id", "line", "part", "defect", "detected_at", "status", "top_cause", "confidence", "hours_to_cause"];
    const lines = filtered.map((r) => [r.id, r.line_id, r.part, r.defect_type, r.detected_at, r.status, r.topCause, r.confidence, r.hoursToCause]);
    const blob = new Blob([[header, ...lines].map((l) => l.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "rootcause-cases.csv";
    a.click();
    URL.revokeObjectURL(url);
    say("Cases exported as CSV");
  }

  const counts = {
    open: rows.filter((r) => r.status !== "approved").length,
    approved: rows.filter((r) => r.status === "approved").length,
    critical: rows.filter((r) => r.severity === "critical").length,
  };

  return (
    <div>
      <PageHead
        kicker="Case history"
        title="Every defect, with the evidence"
        subtitle="A case is a record, not a chat. The images, machine window, batch, maintenance, hypotheses, corrections, report versions and approvals stay together."
        actions={
          <>
            <button className="btn sm" onClick={exportCsv}><Icon name="download" size={12} /> Export CSV</button>
            <Link className="btn primary sm" to="/capture"><Icon name="camera" size={12} /> Start from a photo</Link>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Cases</div><div className="value">{rows.length}</div><div className="foot">{dataMode === "own" ? "my workspace" : "across 4 lines"}</div></div>
        <div className="stat"><div className="label">Open</div><div className="value">{counts.open}</div><div className="foot">need a decision</div></div>
        <div className="stat"><div className="label">Approved</div><div className="value">{counts.approved}</div><div className="foot">signed by an engineer</div></div>
        <div className="stat"><div className="label">Critical</div><div className="value">{counts.critical}</div><div className="foot">containment first</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: auditCase ? "1.6fr 1fr" : "1fr", alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head">
            <h3>Cases</h3>
            <div className="row gap6">
              <Link className="btn sm" to="/cases/new"><Icon name="plus" size={11} /> New</Link>
              <div className="search">
                <Icon name="search" size={12} />
                <input className="input" style={{ width: 190, padding: "5px 8px 5px 27px", fontSize: 11 }} placeholder="Search case, part, batch…" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
              <select aria-label="Case line filter" className="select" style={{ width: 110, padding: "5px 7px", fontSize: 11 }} value={line} onChange={(e) => setLine(e.target.value)}>
                <option value="all">All lines</option>
                {pack?.lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
              <select aria-label="Case status filter" className="select" style={{ width: 120, padding: "5px 7px", fontSize: 11 }} value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="all">Any status</option>
                <option value="investigating">Investigating</option>
                <option value="awaiting_review">Awaiting review</option>
                <option value="approved">Approved</option>
              </select>
            </div>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Case</th><th>Part / defect</th><th>Line</th><th>Detected</th><th>Top cause</th><th>Conf.</th><th>Time</th><th>Status</th><th />
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id} className="clickable" onClick={() => navigate(`/cases/${r.id}`)}>
                    <td>
                      <div className="id">{r.id}</div>
                      <SeverityBadge severity={r.severity} />
                    </td>
                    <td>
                      <div style={{ color: "var(--ink-2)", fontWeight: 600 }}>{r.defect_type}</div>
                      <div className="xsmall soft">{r.part} · {r.serial}</div>
                    </td>
                    <td className="small muted">{r.line_id.replace("line-", "L")}</td>
                    <td className="small muted nowrap">{fmtDateTime(r.detected_at)}</td>
                    <td className="small" style={{ color: "var(--amber-2)" }}>{r.topCause}</td>
                    <td className="mono small">{r.confidence.toFixed(0)}%</td>
                    <td className="small nowrap">{hours(r.hoursToCause)} <span className="soft">/ {hours(r.baseline)}</span></td>
                    <td><StatusBadge status={r.status} /></td>
                    <td><Icon name="chevron" size={13} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && <div className="empty">No cases match. Try clearing the filters.</div>}
          <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
            <span className="xsmall soft">{filtered.length} of {rows.length} cases</span>
            <span className="xsmall soft">Local record · append-only audit</span>
          </div>
        </div>

        {auditCase && (
          <div className="panel">
            <div className="panel-head">
              <h3>Audit trail · {auditCase}</h3>
              <Link className="btn ghost sm" to="/cases">Close</Link>
            </div>
            <div className="panel-body">
              <AuditTrail events={audits(auditCase)} limit={30} />
            </div>
          </div>
        )}
      </div>

      <div className="panel mt16">
        <div className="panel-head">
          <h3>Case history, not a chat log</h3>
          <span className="sub">what is kept</span>
        </div>
        <div className="panel-body grid g4">
          {[
            ["Evidence", "Images, bounding boxes, sensor windows, batch certificates, maintenance records."],
            ["Reasoning", "Every tool call, every cause, every factor weight, every similar case."],
            ["Human decisions", "Who rejected what and why; who added a manual cause; who approved the report."],
            ["Versions", "Report edits create versions. The audit trail is append-only at the database level."],
          ].map(([title, body]) => (
            <div key={title} className="feature">
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
