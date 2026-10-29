import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, factorRows, fmtDateTime, fmtTime, hours } from "../lib/engine";
import type { Evidence, Hypothesis, SensorSeries } from "../types";
import { Icon } from "../components/Icon";
import { AgentTrace, ChainViz, EvidenceList, Modal, PageHead, ProvenanceBlock, SeverityBadge, StatusBadge } from "../components/UI";
import { LineChart } from "../components/Charts";
import { AskPanel } from "../components/AskPanel";

export default function CaseWorkspace() {
  const { caseId = "RC-0417" } = useParams();
  const [params, setParams] = useSearchParams();
  const booth = params.get("booth") === "1";
  const focusMode = params.get("focus") === "1";
  const [boothSeconds, setBoothSeconds] = useState(0);
  const { scenarioFor, investigation, reportFor, caseStatus, accept, reject, addManual, approveReport, audits, say } = useStore();
  const scenario = scenarioFor(caseId);
  const inv = investigation(caseId);
  const report = reportFor(caseId);
  const status = caseStatus(caseId);

  const [selectedEvidence, setSelectedEvidenceState] = useState<string | null>(params.get("evidence"));
  const [imageTab, setImageTabState] = useState<"surface" | "xray">(params.get("tab") === "xray" ? "xray" : "surface");
  const [depth, setDepth] = useState(0);
  const [showBbox, setShowBbox] = useState(true);
  const [sensorId, setSensorId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<Hypothesis | null>(null);
  const [rejectReason, setRejectReason] = useState("Crack starts below the surface; tool marks are surface-only.");
  const [rejectNote, setRejectNote] = useState("");
  const [manualOpen, setManualOpen] = useState(false);
  const [manualLabel, setManualLabel] = useState("");
  const [manualSummary, setManualSummary] = useState("");

  useEffect(() => {
    if (!booth) return;
    const t = window.setInterval(() => setBoothSeconds((s) => s + 1), 1000);
    return () => window.clearInterval(t);
  }, [booth]);

  const selectEvidence = (id: string) => {
    setSelectedEvidenceState(id);
    const next = new URLSearchParams(params);
    next.set("evidence", id);
    setParams(next, { replace: true });
  };
  const selectTab = (tab: "surface" | "xray") => {
    setImageTabState(tab);
    const next = new URLSearchParams(params);
    next.set("tab", tab);
    setParams(next, { replace: true });
  };
  const toggleFocus = () => {
    const next = new URLSearchParams(params);
    if (focusMode) next.delete("focus");
    else next.set("focus", "1");
    setParams(next, { replace: true });
  };

  const sensors = scenario?.sensors ?? [];
  const selectedSensor: SensorSeries | undefined = useMemo(
    () => sensors.find((s) => s.id === sensorId) ?? [...sensors].sort((a, b) => Math.abs(b.deviation_z) - Math.abs(a.deviation_z))[0],
    [sensors, sensorId],
  );

  const evidence = scenario?.evidence ?? [];
  const activeEvidence: Evidence | undefined = evidence.find((e) => e.id === selectedEvidence) ?? evidence[0];
  const highlighted = useMemo(() => {
    const ids = new Set<string>();
    inv?.hypotheses.forEach((h) => {
      if (h.status !== "rejected") h.evidence_ids.forEach((id) => ids.add(id));
    });
    return [...ids];
  }, [inv]);

  if (!scenario || !inv || !report) {
    return (
      <div>
        <PageHead title="Case not found" subtitle={`No case ${caseId} in this demo pack.`} />
        <Link className="btn" to="/cases">Back to cases</Link>
      </div>
    );
  }

  const accepted = inv.hypotheses.find((h) => h.status === "accepted") ?? null;
  const top = inv.hypotheses[0];
  const hasXray = scenario.image_keys.length > 1;
  const imageKey = imageTab === "xray" && hasXray ? scenario.image_keys[1] : scenario.image_keys[0];
  const surfaceFindings = scenario.findings.filter((f) => f.kind === "surface");
  const subFindings = scenario.findings.filter((f) => f.kind === "subsurface");

  function confirmReject() {
    if (!rejectTarget) return;
    reject(caseId, rejectTarget.id, `${rejectReason}${rejectNote ? ` ${rejectNote}` : ""}`);
    setRejectTarget(null);
    setRejectNote("");
    setExpanded(null);
  }

  function submitManual() {
    if (!manualLabel.trim() || !manualSummary.trim()) return;
    addManual(caseId, manualLabel.trim(), manualSummary.trim());
    setManualOpen(false);
    setManualLabel("");
    setManualSummary("");
  }

  function exportCase() {
    if (!scenario || !inv) return;
    const blob = new Blob([JSON.stringify({ scenario, investigation: inv, report }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${scenario.case.id}-case.json`;
    a.click();
    URL.revokeObjectURL(url);
    say("Case exported as JSON");
  }

  const savedHours = Math.max(0, scenario.baseline_hours - scenario.current_hours);

  return (
    <div className={focusMode ? "case-focus" : ""}>
      {booth && (
        <div className="panel mb12" style={{ borderColor: "rgba(255,180,84,.32)", background: "rgba(255,180,84,.05)" }}>
          <div className="panel-body" style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
            <span className="chip amber"><Icon name="play" size={10} /> Booth run</span>
            <span className="mono small" style={{ color: "var(--amber-2)" }}>
              {String(Math.floor(boothSeconds / 60)).padStart(1, "0")}:{String(boothSeconds % 60).padStart(2, "0")} / 3:00
            </span>
            <span className="small muted" style={{ flex: 1 }}>
              {boothSeconds < 20 ? "Open the case. Point at the part and the bounding box." : boothSeconds < 50 ? "The first answer is tool mark. Ask the room whether it starts at the surface." : boothSeconds < 80 ? "Reject it. Watch the ranking recompute." : boothSeconds < 140 ? "Open the evidence: x-ray, hydrogen, batch." : "Edit the report and sign it off."}
            </span>
            <button className="btn sm ghost" onClick={() => setBoothSeconds(0)}><Icon name="reset" size={11} /> Restart timer</button>
            <Link className="btn sm" to="/booth"><Icon name="x" size={11} /> Exit booth</Link>
          </div>
        </div>
      )}
      <div className="case-banner">
        <div>
          <div className="kicker">{scenario.case.id} · {scenario.process}</div>
          <h1>{scenario.case.defect_type}</h1>
          <div className="meta">
            <span><SeverityBadge severity={scenario.case.severity} /></span>
            <span><b>{scenario.case.part}</b></span>
            <span>Serial <b className="mono">{scenario.case.serial}</b></span>
            <span>Line <b>{scenario.case.line_id.replace("line-", "L")}</b></span>
            <span>Detected <b>{fmtDateTime(scenario.case.detected_at)}</b></span>
            <span>Shift <b>{scenario.case.shift}</b></span>
            {scenario.case.hours_in_service ? <span><b>{scenario.case.hours_in_service.toLocaleString()} h</b> in service</span> : null}
          </div>
        </div>
        <div className="actions">
          <StatusBadge status={status} />
          <span className="chip amber"><Icon name="clock" size={11} /> {hours(scenario.current_hours)} to cause</span>
          <span className="chip green"><Icon name="bolt" size={11} /> {hours(savedHours)} saved</span>
          <button className="btn sm" onClick={exportCase}><Icon name="download" size={12} /> Case JSON</button>
          <button className="btn sm" onClick={toggleFocus}><Icon name="zoom" size={12} /> {focusMode ? "Exit focus" : "Focus"}</button>
          <Link className="btn primary sm" to={`/reports?case=${caseId}`}>
            <Icon name="report" size={12} /> {report.status === "approved" ? "View report" : "Review report"}
          </Link>
        </div>
      </div>

      <div className="workspace case-workspace-2026">
        <h2 className="sr-only">Case evidence, causes and decision</h2>
        {/* ---------------------------------------------------- left: evidence on the part */}
        <div className="col-stack">
          <div className="viewer evidence-canvas">
            <div className="canvas" style={{ "--depth": depth } as CSSProperties}>
              <img src={`${import.meta.env.BASE_URL}assets/${imageKey}.svg`} alt={`${scenario.part} inspection image`} />
              {hasXray && (depth > 0 || imageTab === "xray") && (
                <img
                  className="xray show"
                  src={`${import.meta.env.BASE_URL}assets/${scenario.image_keys[1]}.svg`}
                  alt=""
                  style={{ opacity: imageTab === "xray" ? 1 : depth / 100 }}
                />
              )}
              {showBbox && (
                <div
                  className="bbox"
                  data-label={`${scenario.defect} · ${(scenario.case.detection_confidence * 100).toFixed(0)}%`}
                  style={{
                    left: `${scenario.case.bbox[0]}%`,
                    top: `${scenario.case.bbox[1]}%`,
                    width: `${scenario.case.bbox[2]}%`,
                    height: `${scenario.case.bbox[3]}%`,
                  }}
                />
              )}
              {surfaceFindings.map((f) => (
                <span key={f.id} className="finding-pin" style={{ left: `${f.x}%`, top: `${f.y}%` }} title={f.title} />
              ))}
              {subFindings.map((f) => (
                <span
                  key={f.id}
                  className={classNames("finding-pin sub", (depth >= 40 || imageTab === "xray") && "visible")}
                  style={{ left: `${f.x}%`, top: `${f.y}%` }}
                  title={f.title}
                />
              ))}
            </div>
            <div className="viewer-bar">
              <div className="seg">
                <button className={imageTab === "surface" ? "on" : ""} onClick={() => selectTab("surface")}>Optical</button>
                {hasXray && <button className={imageTab === "xray" ? "on" : ""} onClick={() => selectTab("xray")}>X-ray</button>}
                <button className={showBbox ? "on" : ""} onClick={() => setShowBbox((v) => !v)}>Box</button>
              </div>
              <span className="xsmall mono soft">{imageKey} · {(scenario.case.detection_confidence * 100).toFixed(0)}%</span>
            </div>
            {hasXray && (
              <div className="row gap8" style={{ padding: "7px 10px", borderTop: "1px solid var(--line)" }}>
                <span className="xsmall soft nowrap">Depth</span>
                <input type="range" min={0} max={100} value={depth} onChange={(e) => setDepth(Number(e.target.value))} aria-label="Image depth" />
                <span className="xsmall mono cyan" style={{ width: 38, textAlign: "right" }}>{depth}%</span>
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panel-head">
              <h3>Machine window</h3>
              <span className="sub">3 h around defect</span>
            </div>
            <div className="panel-body">
              <div className="row wrap gap4 mb12">
                {sensors.map((s) => (
                  <button
                    key={s.id}
                    className={classNames("chip", selectedSensor?.id === s.id && "amber", s.out_of_spec > 0 && selectedSensor?.id !== s.id && "red")}
                    onClick={() => setSensorId(s.id)}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
              {selectedSensor && (
                <>
                  <div className="row between mb8">
                    <div className="small" style={{ color: "var(--ink-2)" }}>
                      {selectedSensor.name} <span className="soft">· {selectedSensor.unit}</span>
                    </div>
                    <div className="row gap6">
                      <span className={classNames("chip", Math.abs(selectedSensor.deviation_z) >= 2 ? "red" : "green")}>
                        {selectedSensor.deviation_z > 0 ? "+" : ""}{selectedSensor.deviation_z.toFixed(1)}σ
                      </span>
                      <span className="chip">{selectedSensor.out_of_spec} out of spec</span>
                    </div>
                  </div>
                  <LineChart
                    series={[
                      {
                        name: selectedSensor.name,
                        color: Math.abs(selectedSensor.deviation_z) >= 2 ? "#f87171" : "#5eead4",
                        values: selectedSensor.points.map((p) => p.v),
                      },
                    ]}
                    labels={selectedSensor.points.map((p) => fmtTime(p.t))}
                    height={150}
                    refLow={selectedSensor.spec_low}
                    refHigh={selectedSensor.spec_high}
                    decimals={selectedSensor.unit === "ppm" || selectedSensor.unit === "%" || selectedSensor.unit === "%RH" ? 2 : 1}
                    area
                    dots
                  />
                  <div className="row between mt8">
                    <span className="xsmall soft">Baseline {selectedSensor.baseline} {selectedSensor.unit}</span>
                    <span className="xsmall soft">Defect at {fmtTime(scenario.case.detected_at)}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <h3>Material batch</h3>
              <span className="sub">
                {scenario.batch.notes.toLowerCase().includes("exception") || (scenario.batch.moisture_pct ?? 0) > 0.12 ? (
                  <span className="chip red" style={{ fontSize: 11 }}>exception</span>
                ) : (
                  <span className="chip green" style={{ fontSize: 11 }}>in spec</span>
                )}
              </span>
            </div>
            <div className="panel-body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div><div className="xsmall soft">Batch</div><div className="mono small">{scenario.batch.id}</div></div>
              <div><div className="xsmall soft">Material</div><div className="small">{scenario.batch.material}</div></div>
              <div><div className="xsmall soft">Supplier</div><div className="small">{scenario.batch.supplier}</div></div>
              <div><div className="xsmall soft">Lot</div><div className="mono small">{scenario.batch.lot}</div></div>
              {scenario.batch.hydrogen_ppm != null && (
                <div><div className="xsmall soft">Hydrogen</div><div className="small amber">{scenario.batch.hydrogen_ppm} ppm</div></div>
              )}
              {scenario.batch.moisture_pct != null && (
                <div><div className="xsmall soft">Moisture</div><div className="small amber">{scenario.batch.moisture_pct} %</div></div>
              )}
              <div style={{ gridColumn: "1 / -1" }}><div className="xsmall soft">Note</div><div className="small muted">{scenario.batch.notes}</div></div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Maintenance & operator</h3><span className="sub">{scenario.maintenance.length} events</span></div>
            <div className="panel-body col gap8">
              {scenario.maintenance.map((m) => (
                <div key={m.id} className="row" style={{ alignItems: "flex-start", gap: 9 }}>
                  <span className="dot warn" style={{ marginTop: 5 }} />
                  <div style={{ flex: 1 }}>
                    <div className="small"><b>{m.kind}</b> <span className="soft">· {m.machine}</span></div>
                    <div className="xsmall soft">{m.note}</div>
                    <div className="xsmall mono soft">{m.id} · {m.days_before_defect} d before defect · {m.technician}</div>
                  </div>
                </div>
              ))}
              <div className="divider" />
              <div className="small muted"><span className="chip" style={{ marginRight: 7 }}>operator</span>{scenario.operator_note}</div>
            </div>
          </div>
        </div>

        {/* ---------------------------------------------------- middle: reasoning and decision */}
        <div className="col-stack">
          <div className="panel">
            <div className="panel-head">
              <h3>Ranked causes</h3>
              <span className="sub">
                {inv.hypotheses.filter((h) => h.status === "rejected").length} rejected · {inv.unknown.toFixed(0)}% “none of these”
              </span>
            </div>
            <div className="panel-body">
              <div className="cause-list cause-stack">
                {inv.hypotheses.map((h) => (
                  <div
                    key={h.id}
                    className={classNames(
                      "cause",
                      h.rank === 1 && h.status !== "rejected" && "lead",
                      h.status === "rejected" && "rejected",
                      h.status === "accepted" && "accepted",
                      h.status === "manual" && "manual",
                    )}
                  >
                    <div className="cause-head">
                      <div className="cause-title">
                        <span className="cause-rank">{h.rank}</span>
                        <div>
                          <h4>{h.label}</h4>
                          <div className="row gap4 mt8">
                            <span className="tag">{h.category}</span>
                            {h.status === "accepted" && <span className="chip green" style={{ fontSize: 11 }}>approved cause</span>}
                            {h.status === "rejected" && <span className="chip red" style={{ fontSize: 11 }}>rejected</span>}
                            {h.status === "manual" && <span className="chip amber" style={{ fontSize: 11 }}>engineer</span>}
                          </div>
                        </div>
                      </div>
                      <div className="conf">
                        {h.confidence.toFixed(0)}%
                        <small>confidence</small>
                      </div>
                    </div>
                    <div className="meter">
                      <i style={{ width: `${h.confidence}%`, background: h.status === "rejected" ? "#5d5a54" : h.status === "accepted" ? "var(--cyan)" : h.rank === 1 ? "var(--amber)" : "var(--cyan)" }} />
                    </div>
                    <p className="summary">{h.summary}</p>
                    <div className="chips">
                      {h.evidence_ids.map((id) => (
                        <button key={id} className="tag" style={{ background: "transparent", cursor: "pointer" }} onClick={() => selectEvidence(id)}>
                          {id}
                        </button>
                      ))}
                    </div>
                    {expanded === h.id && (
                      <div className="factor-grid">
                        {factorRows(h).map((f) => (
                          <div key={f.key} className="factor">
                            <span style={{ flex: 1 }}>{f.label}</span>
                            <span className="meter"><i style={{ width: `${f.value * 100}%` }} /></span>
                            <b>{(f.value * 100).toFixed(0)}</b>
                          </div>
                        ))}
                        <div className="xsmall soft" style={{ gridColumn: "1 / -1" }}>
                          Score {h.score.toFixed(3)} · weights: deviation 30%, frequency 28%, batch 18%, similarity 18%, recurrence 6%
                        </div>
                      </div>
                    )}
                    <div className="cause-actions">
                      {h.status === "rejected" ? (
                        <span className="xsmall soft">Weight reduced. The ranking is recomputed live.</span>
                      ) : h.status === "accepted" ? (
                        <>
                          <span className="xsmall cyan">Accepted by the engineer. This is the cause that will be reported.</span>
                          <Link className="btn sm cyan" to={`/reports?case=${caseId}`}>Edit report</Link>
                        </>
                      ) : (
                        <>
                          <button className="btn sm cyan" onClick={() => accept(caseId, h.id)}>
                            <Icon name="check" size={11} /> Accept
                          </button>
                          <button className="btn sm danger" onClick={() => setRejectTarget(h)}>
                            <Icon name="x" size={11} /> Reject
                          </button>
                        </>
                      )}
                      <button className="btn sm ghost" onClick={() => setExpanded(expanded === h.id ? null : h.id)}>
                        <Icon name="chart" size={11} /> Why?
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <button className="btn sm mt12" onClick={() => setManualOpen(true)}>
                <Icon name="plus" size={11} /> Add a cause the AI missed
              </button>
            </div>
          </div>

          {accepted && (
            <div className="panel">
              <div className="panel-head">
                <h3>Causal chain</h3>
                <span className="sub">confidence {(inv.chain.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="panel-body">
                <ChainViz chain={inv.chain} />
                <p className="small amber mt12" style={{ fontStyle: "italic" }}>“{inv.chain.verdict}”</p>
                <div className="row gap8 mt12">
                  <Link className="btn primary sm" to={`/reports?case=${caseId}`}><Icon name="report" size={12} /> Draft quality report</Link>
                  <button className="btn sm" onClick={() => approveReport(caseId)} disabled={report.status === "approved"}>
                    <Icon name="check" size={12} /> {report.status === "approved" ? "Approved" : "Sign off report"}
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-head">
              <h3>Agent trace</h3>
              <span className="sub">every tool call is citable</span>
            </div>
            <div className="panel-body">
              <AgentTrace steps={inv.trace} onEvidence={(id) => selectEvidence(id)} />
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <h3>Report</h3>
              <StatusBadge status={report.status} />
            </div>
            <div className="panel-body">
              <div className="small" style={{ color: "var(--ink-2)", lineHeight: 1.55 }}>{report.summary}</div>
              <div className="row between mt12">
                <span className="xsmall soft">v{report.version} · {report.edits} edits</span>
                <Link className="btn sm" to={`/reports?case=${caseId}`}>Open report</Link>
              </div>
            </div>
          </div>
        </div>

        {/* ---------------------------------------------------- right: evidence and provenance */}
        <div className="col-stack">
          <AskPanel scenario={scenario} />
          <div className="panel">
            <div className="panel-head">
              <h3>Evidence</h3>
              <span className="sub">{evidence.length} items</span>
            </div>
            <div className="panel-body tight">
              <EvidenceList
                evidence={evidence}
                selected={selectedEvidence ?? activeEvidence?.id}
                onSelect={selectEvidence}
                highlight={highlighted}
              />
            </div>
          </div>

          {activeEvidence && (
            <div className="panel">
              <div className="panel-head">
                <h3>{activeEvidence.id} · detail</h3>
                <span className="sub">{activeEvidence.kind}</span>
              </div>
              <div className="panel-body">
                <div className="small strong">{activeEvidence.title}</div>
                <p className="small muted mt8" style={{ lineHeight: 1.55 }}>{activeEvidence.detail}</p>
                <div className="divider" />
                <div className="row between">
                  <span className="xsmall mono soft">{activeEvidence.source}</span>
                  <span className="xsmall amber">{Math.round(activeEvidence.strength * 100)}% strength</span>
                </div>
                {Object.keys(activeEvidence.payload).length > 0 && (
                  <div className="mt12" style={{ background: "#0c0e11", border: "1px solid var(--line)", borderRadius: 6, padding: 8 }}>
                    {Object.entries(activeEvidence.payload).map(([k, v]) => (
                      <div key={k} className="row between" style={{ padding: "2px 0" }}>
                        <span className="xsmall soft">{k}</span>
                        <span className="xsmall mono" style={{ color: "var(--ink-2)" }}>{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-head"><h3>Similar cases</h3><span className="sub">6 months</span></div>
            <div className="panel-body tight">
              <div className="col gap6">
                {scenario.history.slice(0, 4).map((h) => (
                  <div key={h.id} className="ev-card">
                    <div className="row between">
                      <span className="eid">{h.id}</span>
                      <span className="chip cyan" style={{ fontSize: 11 }}>{(h.similarity * 100).toFixed(0)}% match</span>
                    </div>
                    <h4>{h.cause}</h4>
                    <p>{h.notes}</p>
                    <div className="src">{h.line} · {h.batch} · resolved in {h.resolution_hours} h</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Provenance</h3><span className="sub">for Q&A</span></div>
            <div className="panel-body">
              <ProvenanceBlock
                items={scenario.provenance}
                note="The public demo runs fully offline from a fixed seed. The pilot runs the same workflow against factory systems on site."
              />
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Audit trail</h3><span className="sub">append-only</span></div>
            <div className="panel-body">
              <div className="col gap6">
                {audits(caseId).slice(0, 5).map((a) => (
                  <div key={a.id} className="xsmall" style={{ color: "var(--muted)" }}>
                    <span className="mono soft">{fmtTime(a.at)}</span> · <b style={{ color: "var(--ink-2)" }}>{a.actor}</b> {a.action}
                    <div className="soft" style={{ paddingLeft: 42 }}>{a.detail}</div>
                  </div>
                ))}
              </div>
              <Link className="btn ghost sm mt8" to={`/cases?audit=${caseId}`}>Full audit trail</Link>
            </div>
          </div>
        </div>
      </div>

      <Modal
        open={!!rejectTarget}
        title={`Reject “${rejectTarget?.label}”`}
        onClose={() => setRejectTarget(null)}
        actions={
          <>
            <button className="btn ghost" onClick={() => setRejectTarget(null)}>Cancel</button>
            <button className="btn danger" onClick={confirmReject}>Reject and re-rank</button>
          </>
        }
      >
        <p>The rejection is saved with a reason. It reduces this cause's weight and feeds the next ranking iteration.</p>
        <div className="field mb12">
          <label>Reason</label>
          <select className="select" value={rejectReason} onChange={(e) => setRejectReason(e.target.value)}>
            <option>Crack starts below the surface; tool marks are surface-only.</option>
            <option>Machine data does not support this cause.</option>
            <option>Batch evidence does not match this case.</option>
            <option>Similar cases resolved to a different cause.</option>
            <option>Engineer has direct process knowledge that rules it out.</option>
          </select>
        </div>
        <div className="field">
          <label>Note (optional)</label>
          <textarea className="textarea" value={rejectNote} onChange={(e) => setRejectNote(e.target.value)} placeholder="What did you see that the system missed?" />
        </div>
      </Modal>

      <Modal
        open={manualOpen}
        title="Add a cause"
        onClose={() => setManualOpen(false)}
        actions={
          <>
            <button className="btn ghost" onClick={() => setManualOpen(false)}>Cancel</button>
            <button className="btn primary" onClick={submitManual} disabled={!manualLabel.trim() || !manualSummary.trim()}>Add to ranking</button>
          </>
        }
      >
        <p>If the cause is not on the list, the engineer can add it. The case keeps the record of who added it and why.</p>
        <div className="field mb12">
          <label>Cause</label>
          <input className="input" value={manualLabel} onChange={(e) => setManualLabel(e.target.value)} placeholder="e.g. Furnace atmosphere" />
        </div>
        <div className="field">
          <label>Evidence / reasoning</label>
          <textarea className="textarea" value={manualSummary} onChange={(e) => setManualSummary(e.target.value)} placeholder="What points to this cause?" />
        </div>
      </Modal>

      <div className="decision-dock">
        <div className="context">
          <b>{scenario.case.id}</b> · {accepted ? `accepted: ${accepted.label}` : "no cause accepted"} · report v{report.version} {report.status}
        </div>
        {!accepted && top && <button className="btn cyan" onClick={() => accept(caseId, top.id)}>Accept top cause</button>}
        {!accepted && top && <button className="btn danger" onClick={() => setRejectTarget(top)}>Reject</button>}
        <button className="btn" onClick={() => setManualOpen(true)}>Add cause</button>
        <Link className="btn primary" to={`/reports?case=${caseId}`}>{report.status === "approved" ? "View report" : "Review report"}</Link>
      </div>

      <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link className="btn ghost sm" to="/cases"><Icon name="arrow" size={12} style={{ transform: "rotate(180deg)" }} /> Back to cases</Link>
        <span className="xsmall mono soft">Evidence first · engineer approves · no line control</span>
      </div>
    </div>
  );
}
