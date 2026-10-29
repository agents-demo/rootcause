import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, eur, fmtDateTime, pct, timeAgo } from "../lib/engine";
import { Icon } from "../components/Icon";
import { AgentTrace, Modal, PageHead, StatusBadge } from "../components/UI";
import { AskPanel } from "../components/AskPanel";
import type { Recommendation } from "../types";

const REC_LABELS: Record<string, string> = {
  hold_batch: "Hold batch",
  extra_sampling: "Extra sampling",
  first_off: "First-off hold",
  check_dryer: "Check dryer",
  check_calibration: "Check calibration",
  pull_maintenance: "Pull maintenance",
  supplier_notice: "Supplier notice",
  verify_parameter: "Verify parameter",
};

function SignalIcon({ kind }: { kind: string }) {
  const map: Record<string, string> = {
    spc: "chart", ewma: "activity", cusum: "activity", change_point: "activity",
    batch: "grid", maintenance: "refresh", setup: "target", data_quality: "alert",
    first_off: "target", recurrence: "refresh", environment: "therm", near_miss: "camera", golden_run: "spark",
  };
  return <Icon name={map[kind] ?? "activity"} size={12} />;
}

export default function WatchDetail() {
  const { watchId = "" } = useParams();
  const { proactive, pack, triageWatch, snoozeWatch, dismissWatch, convertWatch, trueRiskWatch, markCheck, releaseExposure, actOnRecommendation, audits, say } = useStore();
  const watch = proactive?.watches.find((w) => w.id === watchId);
  const [dismissOpen, setDismissOpen] = useState(false);
  const [convertOpen, setConvertOpen] = useState(false);
  const [reason, setReason] = useState("Crash starts below the surface; not this pattern.");
  const [convertCase, setConvertCase] = useState("RC-0417");

  if (!proactive || !watch) {
    return (
      <div>
        <PageHead title="Watch not found" subtitle={`No watch ${watchId} in this pack.`} />
        <Link className="btn" to="/watchlist">Back to watchlist</Link>
      </div>
    );
  }

  const pattern = proactive.patterns.find((p) => p.id === watch.pattern_id);
  const recs = proactive.recommendations.filter((r) => r.watch_id === watch.id);
  const exposure = proactive.exposures.find((e) => e.watch_id === watch.id);
  const linked = pack?.scenarios.find((s) => s.case.id === watch.linked_case_id);
  const modelCard = proactive.model_cards.find((c) => c.id.toLowerCase().includes(watch.pattern_id.toLowerCase().replace("p-", "")));
  const notifications = proactive.notifications.filter((n) => n.watch_id === watch.id);
  const openChecks = watch.suggested_checks.filter((c) => !c.done).length;
  const demoNow = new Date(pack?.meta.anchor ?? new Date().toISOString()).getTime();

  function draft(rec: Recommendation) {
    const text = `Corrective action draft\n\nCase/watch: ${watch!.id} — ${watch!.title}\nAction: ${rec.title}\nOwner: ${watch!.owner}\nDue: ${new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10)}\n\n${rec.detail}\n\nApproved by: ____________________   Date: __________\nThis is a recommendation; no line control is performed.`;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${watch!.id}-${rec.id}-corrective-action.txt`;
    a.click();
    URL.revokeObjectURL(url);
    say("Corrective-action draft downloaded");
  }

  function supplierNotice(rec: Recommendation) {
    const text = `Subject: containment request for batch ${exposure?.batch_id ?? "affected batch"}\n\nWatch ${watch!.id} on ${watch!.line_id} identified a risk. Recommended action: ${rec.title}.\n\n${rec.detail}\n\nPlease confirm containment, certificate traceability and the next delivery batch. This is a quality notification, not an automatic rejection.`;
    void navigator.clipboard?.writeText(text);
    say("Supplier notice copied to clipboard");
  }

  return (
    <div>
      <PageHead
        kicker={`${watch.id} · ${watch.pattern_name}`}
        title={watch.title}
        subtitle={watch.summary}
        actions={
          <>
            <span className={`chip ${watch.severity === "critical" ? "red" : watch.severity === "high" ? "amber" : ""}`}>{watch.severity}</span>
            <span className="chip">{watch.status}</span>
            <span className="chip cyan"><Icon name="target" size={11} /> risk {Math.round(watch.risk_score * 100)}</span>
            <span className="chip"><Icon name="clock" size={11} /> {watch.confidence.toFixed(0)}% confidence</span>
          </>
        }
      />

      <div className="case-banner" style={{ padding: "13px 16px" }}>
        <div className="meta" style={{ marginTop: 0 }}>
          <span>Line <b>{watch.line_id.replace("line-", "L")}</b></span>
          <span>Owner <b>{watch.owner}</b></span>
          <span>Opened <b>{fmtDateTime(watch.opened_at)}</b></span>
          <span>SLA <b>{new Date(watch.sla_due).getTime() < demoNow && ["watching", "triage"].includes(watch.status) ? <span className="red">overdue</span> : fmtDateTime(watch.sla_due)}</b></span>
          {watch.linked_case_id && <span>Linked case <Link to={`/cases/${watch.linked_case_id}`} className="amber mono">{watch.linked_case_id}</Link></span>}
        </div>
        <div className="actions">
          {["watching", "snoozed"].includes(watch.status) && (
            <button className="btn sm primary" onClick={() => triageWatch(watch.id)}><Icon name="check" size={11} /> Start triage</button>
          )}
          {watch.status !== "dismissed" && watch.status !== "converted" && (
            <>
              <button className="btn sm" onClick={() => snoozeWatch(watch.id, 4)}><Icon name="clock" size={11} /> Snooze 4 h</button>
              <button className="btn sm danger" onClick={() => setDismissOpen(true)}><Icon name="x" size={11} /> Dismiss</button>
              <button className="btn sm" onClick={() => trueRiskWatch(watch.id)}>True risk</button>
              <button className="btn sm" onClick={() => setConvertOpen(true)}><Icon name="cases" size={11} /> Convert to case</button>
            </>
          )}
          {watch.status === "converted" && <span className="chip green"><Icon name="check" size={11} /> Converted</span>}
          {watch.status === "dismissed" && <span className="chip red">Dismissed · {watch.outcome_reason}</span>}
        </div>
      </div>

      <div className="workspace" style={{ gridTemplateColumns: "1.15fr 1.15fr 0.9fr" }}>
        <div className="col-stack">
          <div className="panel">
            <div className="panel-head"><h3>Why now?</h3><span className="sub">{watch.signals.length} signals · grouped</span></div>
            <div className="panel-body">
              <div className="trace">
                {watch.signals.map((s) => (
                  <div key={s.id} className="trace-step done">
                    <div className="trace-ico"><SignalIcon kind={s.kind} /></div>
                    <div>
                      <div className="tt">
                        {s.parameter}
                        <span className={`chip ${s.severity === "critical" ? "red" : s.severity === "high" ? "amber" : ""}`} style={{ fontSize: 8, marginLeft: 7 }}>{s.severity}</span>
                      </div>
                      <div className="td">{s.detail}</div>
                      <div className="tm">
                        <span className="tool">{s.kind}</span>
                        {s.z !== null && s.z !== undefined && <span className="ms">{s.z > 0 ? "+" : ""}{s.z}σ</span>}
                        {s.evidence_id && <span className="chip amber" style={{ fontSize: 8, padding: "1px 5px" }}>{s.evidence_id}</span>}
                        <span className="ms">{fmtDateTime(s.at)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="trust-note mt12">
                <b>What would falsify this?</b> {pattern?.card?.failure_modes ? String((pattern.card.failure_modes as string[]).join("; ")) : "A normal post-change settling period or a sensor artefact would make this a false alarm."}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Suggested checks</h3><span className="sub">{openChecks} open</span></div>
            <div className="panel-body col gap8">
              {watch.suggested_checks.map((c) => (
                <div key={c.id} className="row" style={{ alignItems: "flex-start", gap: 9 }}>
                  <button
                    className={`switch ${c.done ? "on" : ""}`}
                    style={{ width: 18, height: 18, borderRadius: 4 }}
                    onClick={() => markCheck(watch.id, c.id)}
                    aria-label={`Mark ${c.label} done`}
                  />
                  <div style={{ flex: 1 }}>
                    <div className="small" style={{ color: c.done ? "var(--soft)" : "var(--ink-2)", textDecoration: c.done ? "line-through" : "none" }}>{c.label}</div>
                    <div className="xsmall soft">{c.why} · {c.owner}</div>
                  </div>
                </div>
              ))}
              {watch.suggested_checks.length === 0 && <div className="empty">No checks defined for this watch.</div>}
            </div>
          </div>

          {exposure && (
            <div className="panel">
              <div className="panel-head"><h3>Exposure & genealogy</h3><span className="sub">batch {exposure.batch_id}</span></div>
              <div className="panel-body" style={{ padding: 0 }}>
                <div className="row between" style={{ padding: "8px 12px", borderBottom: "1px solid var(--line)" }}>
                  <span className="xsmall muted">{exposure.parts.length} parts · {exposure.customers} customers</span>
                  <span className="chip amber" style={{ fontSize: 8 }}>{exposure.status}</span>
                  <span className="small mono">{eur(exposure.estimated_eur)}</span>
                </div>
                <div className="row gap4" style={{ padding: "7px 12px", borderBottom: "1px solid var(--line)" }}>
                  <button className="btn sm" onClick={() => releaseExposure(watch.id, "contained")}>Mark contained</button>
                  <button className="btn sm cyan" onClick={() => releaseExposure(watch.id, "released")}>Release after coupon</button>
                  <button
                    className="btn sm ghost"
                    onClick={() => {
                      const rows = [["serial", "part", "line", "shift", "customer", "status", "containment"], ...exposure.parts.map((p) => [p.serial, p.part, p.line_id, p.shift, p.customer, p.status, p.containment])];
                      const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
                      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${watch.id}-exposure.csv`;
                      a.click();
                      URL.revokeObjectURL(url);
                      say("Exposure list exported");
                    }}
                  >
                    Export CSV
                  </button>
                </div>
                <table className="table">
                  <thead><tr><th>Serial</th><th>Customer</th><th>Status</th><th>Containment</th></tr></thead>
                  <tbody>
                    {exposure.parts.map((p) => (
                      <tr key={p.serial}>
                        <td className="mono xsmall">{p.serial}</td>
                        <td className="xsmall muted">{p.customer}</td>
                        <td><span className="xsmall">{p.status.replace("_", " ")}</span></td>
                        <td><span className={`chip ${p.containment === "hold" ? "amber" : p.containment === "inspect" ? "cyan" : "green"}`} style={{ fontSize: 8 }}>{p.containment}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="xsmall soft" style={{ padding: "7px 12px" }}>{exposure.note}</div>
              </div>
            </div>
          )}
        </div>

        <div className="col-stack">
          <div className="panel">
            <div className="panel-head"><h3>Containment recommendations</h3><span className="sub">human-approved</span></div>
            <div className="panel-body col gap8">
              {recs.map((r) => (
                <div key={r.id} className={classNames("cause", r.status === "approved" && "lead", r.status === "rejected" && "rejected", r.status === "verified" && "accepted")} style={{ padding: 11 }}>
                  <div className="row between">
                    <div>
                      <div className="xsmall soft mono">{r.id} · {REC_LABELS[r.kind] ?? r.kind}</div>
                      <h4 style={{ fontSize: 12.5, marginTop: 4 }}>{r.title}</h4>
                    </div>
                    <span className={`chip ${r.status === "approved" ? "amber" : r.status === "executed" ? "cyan" : r.status === "verified" ? "green" : r.status === "rejected" ? "red" : ""}`} style={{ fontSize: 8 }}>{r.status}</span>
                  </div>
                  <p className="summary">{r.detail}</p>
                  <div className="row gap12 mt8" style={{ flexWrap: "wrap" }}>
                    <span className="xsmall soft">{r.impact.parts_at_risk} parts at risk</span>
                    <span className="xsmall amber">{eur(r.impact.scrap_avoided_eur)} scrap avoided</span>
                    <span className="xsmall soft">{r.impact.engineer_hours} h</span>
                  </div>
                  <div className="cause-actions">
                    {r.status === "proposed" && (
                      <>
                        <button className="btn sm cyan" onClick={() => actOnRecommendation(r.id, "approve")}><Icon name="check" size={11} /> Approve</button>
                        <button className="btn sm danger" onClick={() => actOnRecommendation(r.id, "reject", "Not the right containment for this shift")}><Icon name="x" size={11} /> Reject</button>
                      </>
                    )}
                    {r.status === "approved" && <button className="btn sm cyan" onClick={() => actOnRecommendation(r.id, "execute")}><Icon name="play" size={11} /> Mark executed</button>}
                    {r.status === "executed" && <button className="btn sm" onClick={() => actOnRecommendation(r.id, "verify", "Parameter returned and defect rate stable")}><Icon name="check" size={11} /> Verify effectiveness</button>}
                    <button className="btn sm ghost" onClick={() => draft(r)}>Draft action</button>
                    {(["hold_batch", "check_dryer", "check_calibration"] as string[]).includes(r.kind) && <button className="btn sm ghost" onClick={() => supplierNotice(r)}>Supplier notice</button>}
                  </div>
                  {r.approved_by && <div className="xsmall soft mt8">Approved by {r.approved_by} · {fmtDateTime(r.approved_at)}</div>}
                </div>
              ))}
              {recs.length === 0 && <div className="empty">No containment recommendation. Use the checks and the case workflow.</div>}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Pattern card</h3><span className="sub">{pattern?.version}</span></div>
            <div className="panel-body">
              <div className="row between"><span className="small strong">{pattern?.name}</span><span className="chip" style={{ fontSize: 8 }}>{pattern?.status}</span></div>
              <p className="xsmall muted mt8" style={{ lineHeight: 1.5 }}>{pattern?.description}</p>
              <div className="divider" />
              <div className="row between"><span className="xsmall muted">Historical precision</span><span className="small mono">{pct(pattern?.historical_precision ?? 0, 0)}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Last validated</span><span className="xsmall mono">{pattern?.last_validated?.slice(0, 10)}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Owner</span><span className="xsmall">{pattern?.owner}</span></div>
              <div className="divider" />
              <div className="xsmall soft">Inputs: {modelCard?.inputs.join(", ") ?? "—"}</div>
              <div className="xsmall soft mt8">Known failure modes: {modelCard?.failure_modes.join("; ") ?? "—"}</div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Activity</h3><span className="sub">append-only</span></div>
            <div className="panel-body">
              <div className="col gap6">
                {audits(watch.id).slice(0, 6).map((a) => (
                  <div key={a.id} className="xsmall" style={{ color: "var(--muted)" }}>
                    <span className="mono soft">{new Date(a.at).toLocaleTimeString()}</span> · <b style={{ color: "var(--ink-2)" }}>{a.actor}</b> {a.action}
                    <div className="soft" style={{ paddingLeft: 42 }}>{a.detail}</div>
                  </div>
                ))}
                {audits(watch.id).length === 0 && <div className="empty">No activity yet.</div>}
              </div>
            </div>
          </div>
        </div>

        <div className="col-stack">
          <AskPanel watch={watch} />
          <div className="panel">
            <div className="panel-head"><h3>Decision</h3><span className="sub">human in control</span></div>
            <div className="panel-body">
              <div className="trust-note" style={{ fontSize: 10 }}>
                A watch is a hypothesis. The system never changes a setpoint, rejects a part or holds a batch by itself.
              </div>
              <div className="col gap6 mt12">
                <button className="btn block" onClick={() => triageWatch(watch.id, "Risk confirmed at triage; checks assigned.")}>Confirm risk · start checks</button>
                <button className="btn block" onClick={() => setConvertOpen(true)}>Convert to defect case</button>
                <button className="btn block" onClick={() => trueRiskWatch(watch.id)}>Useful risk · no defect</button>
                <button className="btn block danger" onClick={() => setDismissOpen(true)}>False alarm</button>
              </div>
              <div className="divider" />
              <div className="xsmall soft" style={{ lineHeight: 1.55 }}>
                Dismissal is not a failure. It is a labelled outcome used to tune thresholds and report precision.
              </div>
            </div>
          </div>

          {linked && (
            <div className="panel">
              <div className="panel-head"><h3>Linked case</h3><span className="sub">converted</span></div>
              <div className="panel-body">
                <div className="mono small amber">{linked.case.id}</div>
                <div className="small mt8" style={{ color: "var(--ink-2)" }}>{linked.case.defect_type}</div>
                <div className="xsmall soft">{linked.case.part}</div>
                <Link className="btn sm mt12 block" to={`/cases/${linked.case.id}`}>Open the case file <Icon name="arrow" size={11} /></Link>
                {linked.history.length > 0 && (
                  <div className="mt12">
                    <div className="xsmall soft" style={{ letterSpacing: ".1em", textTransform: "uppercase" }}>Similar history</div>
                    {linked.history.slice(0, 3).map((h) => (
                      <div key={h.id} className="row between mt8">
                        <span className="xsmall muted">{h.cause}</span>
                        <span className="xsmall mono">{Math.round(h.similarity * 100)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-head"><h3>Evidence</h3><span className="sub">{watch.evidence_ids.length} IDs</span></div>
            <div className="panel-body">
              <div className="row gap4" style={{ flexWrap: "wrap" }}>
                {watch.evidence_ids.map((id) => <span key={id} className="tag">{id}</span>)}
                {watch.evidence_ids.length === 0 && <span className="xsmall soft">Signals only; no case image attached.</span>}
              </div>
              {linked && (
                <div className="mt12">
                  <div className="xsmall soft">From the linked case</div>
                  <div className="row gap4 mt8" style={{ flexWrap: "wrap" }}>
                    {linked.evidence.slice(0, 4).map((e) => <span key={e.id} className="tag">{e.id}</span>)}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Notifications</h3><span className="sub">{notifications.length}</span></div>
            <div className="panel-body col gap6">
              {notifications.slice(0, 4).map((n) => (
                <div key={n.id} className="xsmall" style={{ color: "var(--muted)" }}>
                  <b style={{ color: "var(--ink-2)" }}>{n.title}</b>
                  <div className="soft">{n.detail}</div>
                </div>
              ))}
              {notifications.length === 0 && <span className="xsmall soft">No notification for this watch.</span>}
              <Link className="btn ghost sm mt8" to="/alerts">Alert center <Icon name="arrow" size={11} /></Link>
            </div>
          </div>
        </div>
      </div>

      <div className="decision-dock">
        <div className="context"><b>Watch {watch.id}</b> · {watch.status} · risk {Math.round(watch.risk_score * 100)} · owner {watch.owner}</div>
        {["watching", "snoozed"].includes(watch.status) && <button className="btn primary" onClick={() => triageWatch(watch.id)}>Start triage</button>}
        <button className="btn" onClick={() => snoozeWatch(watch.id, 4)}>Snooze 4 h</button>
        <button className="btn" onClick={() => trueRiskWatch(watch.id)}>True risk</button>
        <button className="btn" onClick={() => setConvertOpen(true)}>Convert</button>
        <button className="btn danger" onClick={() => setDismissOpen(true)}>False alarm</button>
      </div>

      <div className="row between mt16">
        <Link className="btn ghost sm" to="/watchlist"><Icon name="arrow" size={12} style={{ transform: "rotate(180deg)" }} /> Watchlist</Link>
        <span className="xsmall mono soft">Watch {watch.id} · pattern {watch.pattern_id} · {watch.signal_count} signals</span>
      </div>

      <Modal
        open={dismissOpen}
        title="Dismiss this watch"
        onClose={() => setDismissOpen(false)}
        actions={<><button className="btn ghost" onClick={() => setDismissOpen(false)}>Cancel</button><button className="btn danger" onClick={() => { dismissWatch(watch.id, reason); setDismissOpen(false); }}>Record false alarm</button></>}
      >
        <p>The reason is stored as an outcome and feeds threshold tuning. It is not a failure; it is a label.</p>
        <div className="field">
          <label>Reason</label>
          <select className="select" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option>Normal post-change settling.</option>
            <option>Sensor or probe artefact.</option>
            <option>Maintenance explains the signal.</option>
            <option>Engineering change already approved.</option>
            <option>Crash starts below the surface; not this pattern.</option>
          </select>
        </div>
      </Modal>

      <Modal
        open={convertOpen}
        title="Convert to a defect case"
        onClose={() => setConvertOpen(false)}
        actions={<><button className="btn ghost" onClick={() => setConvertOpen(false)}>Cancel</button><button className="btn primary" onClick={() => { convertWatch(watch.id, convertCase); setConvertOpen(false); }}>Convert and link</button></>}
      >
        <p>Use this when the risk has become a real defect. The watch keeps the early signal; the case keeps the investigation.</p>
        <div className="field">
          <label>Case</label>
          <select className="select" value={convertCase} onChange={(e) => setConvertCase(e.target.value)}>
            {pack?.scenarios.map((s) => <option key={s.case.id} value={s.case.id}>{s.case.id} · {s.case.defect_type}</option>)}
          </select>
        </div>
      </Modal>
    </div>
  );
}
