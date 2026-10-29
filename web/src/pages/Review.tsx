import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, fmtDateTime, hours } from "../lib/engine";
import type { Hypothesis } from "../types";
import { Icon } from "../components/Icon";
import { ChainViz, Modal, PageHead, ProvenanceBlock, SeverityBadge, StatusBadge } from "../components/UI";

export default function Review() {
  const { pack, investigation, reportFor, caseStatus, accept, reject, addManual, approveReport, audits, say } = useStore();
  const [params] = useSearchParams();
  const [selected, setSelected] = useState(params.get("case") ?? pack?.scenarios[0]?.case.id ?? "RC-0417");
  const [rejectTarget, setRejectTarget] = useState<Hypothesis | null>(null);
  const [rejectReason, setRejectReason] = useState("Machine data does not support this cause.");
  const [manualOpen, setManualOpen] = useState(false);
  const [manualLabel, setManualLabel] = useState("");
  const [manualSummary, setManualSummary] = useState("");

  const rows = useMemo(() => {
    if (!pack) return [];
    return pack.scenarios.map((s) => {
      const inv = investigation(s.case.id);
      const top = inv?.hypotheses.find((h) => h.status !== "rejected");
      return { s, inv, top, status: caseStatus(s.case.id), report: reportFor(s.case.id) };
    });
  }, [pack, investigation, caseStatus, reportFor]);

  const current = rows.find((r) => r.s.case.id === selected) ?? rows[0];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || !current) return;
      const index = rows.findIndex((r) => r.s.case.id === current.s.case.id);
      if (e.key.toLowerCase() === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setSelected(rows[Math.min(rows.length - 1, index + 1)].s.case.id);
      }
      if (e.key.toLowerCase() === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setSelected(rows[Math.max(0, index - 1)].s.case.id);
      }
      const top = current.inv?.hypotheses.find((h) => h.status !== "rejected");
      if (e.key.toLowerCase() === "a" && top && !current.inv?.hypotheses.some((h) => h.status === "accepted")) {
        e.preventDefault();
        accept(current.s.case.id, top.id);
      }
      if (e.key.toLowerCase() === "r" && top && !current.inv?.hypotheses.some((h) => h.status === "accepted")) {
        e.preventDefault();
        setRejectTarget(top);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [rows, current, accept]);

  if (!pack || !current) return <div className="empty">Loading review queue…</div>;

  const inv = current.inv!;
  const accepted = inv.hypotheses.find((h) => h.status === "accepted");
  const report = current.report!;
  const queue = rows.filter((r) => r.status !== "approved");

  return (
    <div>
      <PageHead
        kicker="Engineer review"
        title="Decide, on the floor"
        subtitle="The phone version. One case at a time: the top cause, the evidence behind it, and three buttons — accept, reject, or add what the AI missed. The report follows."
        actions={
          <>
            <span className="chip amber"><Icon name="review" size={11} /> {queue.length} waiting</span>
            <span className="chip"><Icon name="grid" size={11} /> J/K move · A accept · R reject</span>
            <Link className="btn sm" to={`/cases/${current.s.case.id}`}><Icon name="external" size={11} /> Full case</Link>
          </>
        }
      />

      <div className="grid" style={{ gridTemplateColumns: "300px 1fr", alignItems: "start", gap: 12 }}>
        <div className="panel">
          <div className="panel-head"><h3>Queue</h3><span className="sub">{queue.length} open</span></div>
          <div className="panel-body tight">
            <div className="col gap6">
              {rows.map((r) => (
                <button
                  key={r.s.case.id}
                  className={classNames("ev-card", r.s.case.id === current.s.case.id && "sel")}
                  style={{ textAlign: "left", font: "inherit" }}
                  onClick={() => setSelected(r.s.case.id)}
                >
                  <div className="row between">
                    <span className="eid">{r.s.case.id}</span>
                    <StatusBadge status={r.status} />
                  </div>
                  <h4>{r.s.case.defect_type}</h4>
                  <p>{r.s.case.part} · {fmtDateTime(r.s.case.detected_at)}</p>
                  <div className="row between mt8">
                    <span className="xsmall" style={{ color: "var(--amber-2)" }}>{r.top?.label}</span>
                    <span className="xsmall mono muted">{r.top?.confidence.toFixed(0)}%</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="col-stack">
          <div className="case-banner" style={{ margin: 0 }}>
            <div>
              <div className="kicker">{current.s.case.id} · {current.s.case.line_id.replace("line-", "Line ")} · shift {current.s.case.shift}</div>
              <h1 style={{ fontSize: 20 }}>{current.s.case.defect_type}</h1>
              <div className="meta">
                <span><SeverityBadge severity={current.s.case.severity} /></span>
                <span>{current.s.case.part}</span>
                <span>Batch <b>{current.s.case.batch_id}</b></span>
                <span>{hours(current.s.current_hours)} to cause</span>
              </div>
            </div>
            <div className="actions">
              <StatusBadge status={current.status} />
            </div>
          </div>

          <div className="grid g2" style={{ alignItems: "start" }}>
            <div className="panel">
              <div className="panel-head"><h3>Top cause</h3><span className="sub">{inv.unknown.toFixed(0)}% “none of these”</span></div>
              <div className="panel-body">
                <div className="cause lead" style={{ padding: 12 }}>
                  <div className="cause-head">
                    <div className="cause-title">
                      <span className="cause-rank">1</span>
                      <div><h4>{inv.hypotheses[0]?.label}</h4></div>
                    </div>
                    <div className="conf">{inv.hypotheses[0]?.confidence.toFixed(0)}%<small>confidence</small></div>
                  </div>
                  <div className="meter"><i style={{ width: `${inv.hypotheses[0]?.confidence}%` }} /></div>
                  <p className="summary">{inv.hypotheses[0]?.summary}</p>
                  <div className="chips">
                    {inv.hypotheses[0]?.evidence_ids.slice(0, 4).map((id) => <span key={id} className="tag">{id}</span>)}
                  </div>
                </div>
                <div className="col gap6 mt12">
                  {inv.hypotheses.slice(1, 4).map((h) => (
                    <div key={h.id} className={classNames("cause", h.status === "rejected" && "rejected")} style={{ padding: "8px 10px" }}>
                      <div className="row between">
                        <span className="small" style={{ color: "var(--ink-2)" }}>{h.label}</span>
                        <span className="mono xsmall">{h.confidence.toFixed(0)}%</span>
                      </div>
                      <div className="meter mt8" style={{ height: 3 }}><i style={{ width: `${h.confidence}%`, background: "var(--cyan)" }} /></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head"><h3>Decision</h3><span className="sub">saved to the audit trail</span></div>
              <div className="panel-body">
                {accepted ? (
                  <>
                    <span className="chip green"><Icon name="check" size={11} /> Accepted: {accepted.label}</span>
                    <div className="mt12"><ChainViz chain={inv.chain} compact /></div>
                    <button className="btn primary block mt12" onClick={() => { approveReport(current.s.case.id); say(`${current.s.case.id} approved`); }} disabled={report.status === "approved"}>
                      <Icon name="check" size={12} /> {report.status === "approved" ? "Report approved" : "Approve report and close"}
                    </button>
                    <Link className="btn block mt8" to={`/reports?case=${current.s.case.id}`}>Edit the report first</Link>
                  </>
                ) : (
                  <>
                    <div className="row gap6" style={{ flexWrap: "wrap" }}>
                      <button className="btn cyan" onClick={() => accept(current.s.case.id, inv.hypotheses[0].id)}>
                        <Icon name="check" size={12} /> Accept top cause
                      </button>
                      <button className="btn danger" onClick={() => setRejectTarget(inv.hypotheses[0])}>
                        <Icon name="x" size={12} /> Reject
                      </button>
                      <button className="btn" onClick={() => setManualOpen(true)}>
                        <Icon name="plus" size={12} /> Add cause
                      </button>
                    </div>
                    <div className="divider" />
                    <div className="col gap6">
                      {inv.hypotheses.slice(1, 3).map((h) => (
                        <div key={h.id} className="row between">
                          <span className="xsmall muted">{h.label}</span>
                          <button className="btn sm ghost" onClick={() => accept(current.s.case.id, h.id)}>Accept</button>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <div className="divider" />
                <ProvenanceBlock
                  items={{ model: "rootcause-0.9.0", data: "on-site", approver: "M. Weber" }}
                  compact
                />
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Evidence behind the decision</h3><span className="sub">{inv.hypotheses[0]?.evidence_ids.length} cited</span></div>
            <div className="panel-body">
              <div className="col gap6">
                {current.s.evidence.filter((e) => inv.hypotheses[0]?.evidence_ids.includes(e.id)).slice(0, 5).map((e) => (
                  <div key={e.id} className="ev-card">
                    <div className="row between"><span className="eid">{e.id}</span><span className="kind">{e.kind}</span></div>
                    <h4>{e.title}</h4>
                    <p>{e.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Recent decisions</h3><span className="sub">this session</span></div>
            <div className="panel-body">
              {audits(current.s.case.id).slice(0, 5).map((a) => (
                <div key={a.id} className="row between" style={{ padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,.05)" }}>
                  <span className="xsmall muted"><b style={{ color: "var(--ink-2)" }}>{a.actor}</b> · {a.action}</span>
                  <span className="xsmall soft mono">{new Date(a.at).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Modal
        open={!!rejectTarget}
        title={`Reject ${rejectTarget?.label ?? ""}`}
        onClose={() => setRejectTarget(null)}
        actions={
          <>
            <button className="btn ghost" onClick={() => setRejectTarget(null)}>Cancel</button>
            <button className="btn danger" onClick={() => { if (rejectTarget) reject(current.s.case.id, rejectTarget.id, rejectReason); setRejectTarget(null); }}>Reject and re-rank</button>
          </>
        }
      >
        <p>The reason is stored with the correction. The next ranking uses it.</p>
        <select className="select" value={rejectReason} onChange={(e) => setRejectReason(e.target.value)}>
          <option>Machine data does not support this cause.</option>
          <option>Crack starts below the surface; tool marks are surface-only.</option>
          <option>Batch evidence does not match this case.</option>
          <option>Similar cases resolved to a different cause.</option>
          <option>Engineer has direct process knowledge that rules it out.</option>
        </select>
      </Modal>

      <Modal
        open={manualOpen}
        title="Add a cause"
        onClose={() => setManualOpen(false)}
        actions={
          <>
            <button className="btn ghost" onClick={() => setManualOpen(false)}>Cancel</button>
            <button className="btn primary" disabled={!manualLabel.trim() || !manualSummary.trim()} onClick={() => { addManual(current.s.case.id, manualLabel, manualSummary); setManualOpen(false); setManualLabel(""); setManualSummary(""); }}>Add</button>
          </>
        }
      >
        <div className="field mb12"><label>Cause</label><input className="input" value={manualLabel} onChange={(e) => setManualLabel(e.target.value)} placeholder="e.g. Furnace atmosphere" /></div>
        <div className="field"><label>Reasoning</label><textarea className="textarea" value={manualSummary} onChange={(e) => setManualSummary(e.target.value)} /></div>
      </Modal>
    </div>
  );
}
