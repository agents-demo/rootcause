import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, fmtDateTime } from "../lib/engine";
import { Icon } from "../components/Icon";
import type { Finding } from "../types";

const SUBSURFACE_DEPTH = 45;
const ZOOM = 2.6;

export default function Stage() {
  const { pack, investigation, accept, reject, resetCase, toast } = useStore();
  const scenario = pack?.scenarios.find((s) => s.id === "bracket");
  const [depth, setDepth] = useState(0);
  const [lens, setLens] = useState({ x: 0.5, y: 0.45 });
  const [benchSize, setBenchSize] = useState({ w: 900, h: 520 });
  const [collected, setCollected] = useState<string[]>([]);
  const [audience, setAudience] = useState<"surface" | "subsurface">("surface");
  const [rejected, setRejected] = useState(false);
  const [step, setStep] = useState<"observe" | "causes" | "verdict">("observe");
  const [elapsed, setElapsed] = useState(0);
  const [started, setStarted] = useState(false);
  const [near, setNear] = useState<string | null>(null);
  const [detail, setDetail] = useState<Finding | null>(null);
  const [auto, setAuto] = useState(false);
  const benchRef = useRef<HTMLDivElement>(null);
  const loupeRef = useRef<HTMLDivElement>(null);
  const [lensHalf, setLensHalf] = useState(77);
  const autoRef = useRef<number | null>(null);

  const findings = scenario?.findings ?? [];
  const visible = useMemo(
    () => findings.filter((f) => f.kind === "surface" || depth >= SUBSURFACE_DEPTH),
    [findings, depth],
  );
  const allCollected = findings.length > 0 && findings.every((f) => collected.includes(f.id));
  const totalFindings = findings.length;
  const inv = scenario ? investigation(scenario.case.id) : null;
  const top = inv?.hypotheses[0];
  const gas = inv?.hypotheses.find((h) => h.id === "gas_porosity");

  useEffect(() => {
    if (!started || step === "verdict") return;
    const timer = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => window.clearInterval(timer);
  }, [started, step]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "r") reset();
      if (e.key === " ") {
        e.preventDefault();
        if (step === "observe" && allCollected) reconstruct();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  useEffect(() => {
    const el = benchRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      const r = el.getBoundingClientRect();
      setBenchSize({ w: r.width, h: r.height });
      if (loupeRef.current) setLensHalf(loupeRef.current.offsetWidth / 2);
    });
    ro.observe(el);
    const r = el.getBoundingClientRect();
    setBenchSize({ w: r.width, h: r.height });
    return () => ro.disconnect();
  }, []);

  useEffect(
    () => () => {
      if (autoRef.current) window.clearInterval(autoRef.current);
    },
    [],
  );

  const collectAt = useCallback(
    (nx: number, ny: number, currentDepth = depth) => {
      if (!scenario) return;
      let closest: Finding | null = null;
      let best = 0.09;
      scenario.findings.forEach((f) => {
        if (f.kind === "subsurface" && currentDepth < SUBSURFACE_DEPTH) return;
        const d = Math.hypot(f.x / 100 - nx, f.y / 100 - ny);
        if (d < best) {
          best = d;
          closest = f;
        }
      });
      if (closest) {
        const found = closest as Finding;
        setNear(found.id);
        setCollected((prev) => (prev.includes(found.id) ? prev : [...prev, found.id]));
        setDetail(found);
      } else {
        setNear(null);
      }
    },
    [depth, scenario],
  );

  const moveTo = useCallback(
    (clientX: number, clientY: number) => {
      const el = benchRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const nx = Math.max(0.02, Math.min(0.98, (clientX - r.left) / r.width));
      const ny = Math.max(0.02, Math.min(0.98, (clientY - r.top) / r.height));
      setLens({ x: nx, y: ny });
      collectAt(nx, ny);
      if (!started) setStarted(true);
    },
    [collectAt, started],
  );

  const reset = useCallback(() => {
    if (scenario) resetCase(scenario.case.id);
    setDepth(0);
    setLens({ x: 0.5, y: 0.45 });
    setCollected([]);
    setRejected(false);
    setStep("observe");
    setElapsed(0);
    setStarted(false);
    setAudience("surface");
    setDetail(null);
    setAuto(false);
    if (autoRef.current) window.clearInterval(autoRef.current);
  }, [resetCase, scenario]);

  const autoScan = useCallback(() => {
    if (!scenario || auto) return;
    setAuto(true);
    setStarted(true);
    const targets = [...scenario.findings].sort((a, b) => (a.kind === "surface" ? -1 : 1) - (b.kind === "surface" ? -1 : 1));
    let i = 0;
    if (autoRef.current) window.clearInterval(autoRef.current);
    autoRef.current = window.setInterval(() => {
      if (i >= targets.length) {
        if (autoRef.current) window.clearInterval(autoRef.current);
        setAuto(false);
        setDepth(60);
        setStep("causes");
        return;
      }
      const t = targets[i];
      if (t.kind === "subsurface") setDepth((d) => Math.max(d, 60));
      setLens({ x: t.x / 100, y: t.y / 100 });
      setCollected((prev) => (prev.includes(t.id) ? prev : [...prev, t.id]));
      setDetail(t);
      setNear(t.id);
      i += 1;
    }, 900);
  }, [auto, scenario]);

  const reconstruct = useCallback(() => {
    setStep("causes");
    setStarted(true);
  }, []);

  const rejectTool = useCallback(() => {
    if (!scenario) return;
    setRejected(true);
    setDepth((d) => Math.max(d, 60));
    reject(scenario.case.id, "tool_mark", "Crack starts below the surface; tool marks are surface-only.");
  }, [reject, scenario]);

  const approve = useCallback(() => {
    if (scenario) {
      const current = investigation(scenario.case.id);
      const chosen = current?.hypotheses.find((h) => h.id === "gas_porosity") ?? current?.hypotheses[0];
      if (chosen && chosen.status !== "rejected") accept(scenario.case.id, chosen.id);
    }
    setStep("verdict");
  }, [accept, investigation, scenario]);

  if (!scenario) {
    return (
      <div className="stage">
        <div className="stage-wrap">
          <div className="empty">Loading stage…</div>
        </div>
      </div>
    );
  }

  const evidenceFor = (ids: string[]) =>
    ids
      .map((id) => scenario.evidence.find((e) => e.id === id))
      .filter((e): e is NonNullable<typeof e> => Boolean(e))
      .slice(0, 3);
  const shownCauses = inv?.hypotheses.slice(0, 4) ?? [];

  return (
    <div className="stage">
      <div className="stage-wrap">
        <header className="stage-head">
          <div className="brand">
            <div className="brand-mark" />
            <div>
              <h1>
                ROOTCAUSE
                <small>FAILURE INVESTIGATION · STAGE MODE</small>
              </h1>
            </div>
          </div>
          <div className="right">
            CASE <b>{scenario.case.id.replace("RC-", "")}</b> · TURBINE BRACKET
            <br />
            UNIT 6 · {scenario.case.hours_in_service?.toLocaleString()} HOURS IN SERVICE
            <br />
            <span className="stage-timer">
              RUN <b>{String(Math.floor(elapsed / 60)).padStart(1, "0")}:{String(elapsed % 60).padStart(2, "0")}</b> / 1:30
            </span>
          </div>
        </header>

        <div className="stage-sub">
          <p>
            The bracket cracked in service. The report said <em>metal fatigue</em>. Drag the lens
            across the part, go <em>under the surface</em>, and find what actually started it.
          </p>
          <div className="row gap8">
            <div className="stage-audience">
              <span>THE ROOM:</span>
              <button
                className={audience === "surface" ? "on" : ""}
                onClick={() => {
                  setAudience("surface");
                  setDepth(0);
                }}
              >
                A · surface first
              </button>
              <button
                className={audience === "subsurface" ? "on" : ""}
                onClick={() => {
                  setAudience("subsurface");
                  setDepth(60);
                  setStarted(true);
                }}
              >
                B · under the surface
              </button>
            </div>
            <button className="btn ghost sm" onClick={() => (window.location.hash = "#/cases")}>
              <Icon name="arrow" size={12} /> Exit stage
            </button>
          </div>
        </div>

        <div
          className="bench"
          ref={benchRef}
          style={{ "--depth": depth } as CSSProperties}
          onPointerMove={(e) => moveTo(e.clientX, e.clientY)}
          onPointerDown={(e) => moveTo(e.clientX, e.clientY)}
        >
          <img src={`${import.meta.env.BASE_URL}assets/bracket-surface.svg`} alt="Failed turbine bracket under inspection" />
          <img className="xray" src={`${import.meta.env.BASE_URL}assets/bracket-xray.svg`} alt="" aria-hidden="true" />
          <div className="scanline" />

          {findings.map((f) => (
            <button
              key={f.id}
              className={classNames(
                "finding-pin",
                f.kind === "subsurface" && "sub",
                f.kind === "subsurface" && depth >= SUBSURFACE_DEPTH && "visible",
                near === f.id && "near",
                collected.includes(f.id) && "collected",
              )}
              style={{ left: `${f.x}%`, top: `${f.y}%` }}
              onClick={(e) => {
                e.stopPropagation();
                if (f.kind === "subsurface" && depth < SUBSURFACE_DEPTH) return;
                setLens({ x: f.x / 100, y: f.y / 100 });
                setCollected((prev) => (prev.includes(f.id) ? prev : [...prev, f.id]));
                setDetail(f);
                setStarted(true);
              }}
              aria-label={f.title}
            />
          ))}

          <div
            className="loupe"
            ref={loupeRef}
            style={{ left: `${lens.x * 100}%`, top: `${lens.y * 100}%` }}
          >
            <img
              src={`${import.meta.env.BASE_URL}assets/bracket-surface.svg`}
              alt=""
              style={{
                width: benchSize.w * ZOOM,
                height: benchSize.h * ZOOM,
                transform: `translate(${-lens.x * benchSize.w * ZOOM + lensHalf}px, ${-lens.y * benchSize.h * ZOOM + lensHalf}px)`,
              }}
            />
            <img
              src={`${import.meta.env.BASE_URL}assets/bracket-xray.svg`}
              alt=""
              style={{
                width: benchSize.w * ZOOM,
                height: benchSize.h * ZOOM,
                opacity: depth / 100,
                mixBlendMode: "screen",
                transform: `translate(${-lens.x * benchSize.w * ZOOM + lensHalf}px, ${-lens.y * benchSize.h * ZOOM + lensHalf}px)`,
              }}
            />
            <div className="cross" />
          </div>

          <div className="hud hint">
            {step === "observe" ? (
              <>
                <b>Drag the lens.</b> Go under the surface.
              </>
            ) : (
              <>
                <b>The evidence is in.</b> Decide, then stamp the verdict.
              </>
            )}
          </div>
          <div className="hud readout">
            DEPTH <b>{depth}%</b>
            <br />
            MAG <b>2.6x</b>
            <br />
            EVIDENCE <b>{collected.length}/{totalFindings}</b>
          </div>
          <div className="hud north">SAMPLE 0417-B · ROOT FILLET · XR-02</div>
        </div>

        <div className="stage-console">
          <div className="ctl">
            <label>
              Depth of view
              <span className="val">
                {depth}% · {depth < SUBSURFACE_DEPTH ? "optical" : "x-ray"}
              </span>
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={depth}
              onChange={(e) => {
                setDepth(Number(e.target.value));
                setStarted(true);
              }}
              aria-label="Depth of view from optical to x-ray"
            />
          </div>
          <div className="findings-chips">
            {findings.map((f, i) => (
              <button
                key={f.id}
                className={classNames(
                  "fchip",
                  collected.includes(f.id) && "on",
                  f.kind === "subsurface" && depth < SUBSURFACE_DEPTH && "hidden",
                )}
                onClick={() => {
                  if (f.kind === "subsurface" && depth < SUBSURFACE_DEPTH) {
                    setDepth(60);
                  }
                  setLens({ x: f.x / 100, y: f.y / 100 });
                  setCollected((prev) => (prev.includes(f.id) ? prev : [...prev, f.id]));
                  setDetail(f);
                  setStarted(true);
                }}
              >
                <i>{collected.includes(f.id) ? "✓" : i + 1}</i>
                {f.title}
              </button>
            ))}
          </div>
          {step === "observe" ? (
            <div className="row gap8">
              <button className="btn ghost sm" onClick={autoScan} disabled={auto}>
                <Icon name="zoom" size={12} /> Auto-scan
              </button>
              <button
                className={classNames("stage-cta", allCollected && "ready")}
                disabled={!allCollected}
                onClick={reconstruct}
              >
                Reconstruct the cause
              </button>
            </div>
          ) : (
            <Link className="stage-cta ready" to={`/cases/${scenario.case.id}`} style={{ textDecoration: "none" }}>
              Open the case file
            </Link>
          )}
        </div>

        {step === "causes" && (
          <div className="grid g2 mt12" style={{ alignItems: "start" }}>
            <div className="panel">
              <div className="panel-head">
                <h3>Ranked causes</h3>
                <span className="sub">{rejected ? "Re-ranked after engineer rejection" : "First answer"}</span>
              </div>
              <div className="panel-body">
                <div className="stage-rail">
                  {shownCauses.map((h) => (
                    <div
                      key={h.id}
                      className={classNames("stage-cause", h.rank === 1 && "lead", h.status === "rejected" && "rejected")}
                    >
                      <div className="top">
                        <span className="label">{h.label}</span>
                        <span className="c">{h.confidence.toFixed(0)}%</span>
                      </div>
                      <div className="meter">
                        <i style={{ width: `${h.confidence}%`, background: h.status === "rejected" ? "#5d5a54" : h.rank === 1 ? "var(--amber)" : "var(--cyan)" }} />
                      </div>
                      <div className="why">
                        {h.status === "rejected" ? "Rejected by the engineer. Weight reduced." : h.note || h.summary}
                      </div>
                      <div className="row gap4 mt8">
                        {h.evidence_ids.slice(0, 3).map((id) => (
                          <span key={id} className="tag">{id}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="xsmall soft mt8">
                  {inv?.unknown.toFixed(0)}% of the probability is left for “none of these”. The system is not allowed to be certain on its own.
                </p>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h3>Engineer decision</h3>
                <span className="sub">Human in control</span>
              </div>
              <div className="panel-body">
                {!rejected ? (
                  <>
                    <p className="small" style={{ color: "var(--ink-2)", lineHeight: 1.6 }}>
                      The AI proposes <b className="amber">{top?.label}</b> at {top?.confidence.toFixed(0)}%. It is plausible:
                      there is a machining ridge near the crack. Is it the initiator?
                    </p>
                    <div className="row gap8 mt12">
                      <button className="btn danger" onClick={rejectTool}>
                        <Icon name="x" size={13} /> Reject: crack starts below the surface
                      </button>
                      <Link className="btn ghost" to={`/cases/${scenario.case.id}`}>
                        Inspect the evidence
                      </Link>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="trust-note">
                      <b>It was confident. It was wrong.</b> This is why the engineer stays in charge.
                      The correction is saved to the case and the ranking is recomputed in the same scene.
                    </div>
                    <div className="mt12" style={{ color: "var(--ink-2)", fontSize: 12, lineHeight: 1.6 }}>
                      Now leading: <b className="cyan">{top?.label}</b> at {top?.confidence.toFixed(0)}%.
                      The x-ray shows a porosity cluster aligned with the crack path.
                    </div>
                    <div className="row gap8 mt12">
                      <button className="btn cyan" onClick={approve}>
                        <Icon name="check" size={13} /> Accept {gas ? "gas porosity" : "cause"} and stamp
                      </button>
                      <Link className="btn ghost" to={`/cases/${scenario.case.id}`}>
                        Inspect the evidence
                      </Link>
                    </div>
                  </>
                )}
                <div className="row between mt16" style={{ paddingTop: 10, borderTop: "1px solid var(--line)" }}>
                  <span className="xsmall soft">Keyboard: R resets · Space reconstructs</span>
                  <span className="xsmall mono soft">{fmtDateTime(scenario.case.detected_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {detail && step === "observe" && (
          <div className="row between" style={{ padding: "8px 2px 0", gap: 12 }}>
            <div className="small" style={{ color: "var(--ink-2)" }}>
              <span className="chip cyan" style={{ marginRight: 8 }}>{detail.id.toUpperCase()}</span>
              {detail.detail}
            </div>
            <button className="btn ghost sm" onClick={reset} title="Reset (R)">
              <Icon name="reset" size={12} /> R
            </button>
          </div>
        )}
      </div>

      {step === "verdict" && (
        <div className="stage-verdict" role="dialog" aria-modal="true">          <div className="stage-sheet">
            <div className="stamp">APPROVED</div>
            <div className="kicker">Case {scenario.case.id} · cause report</div>
            <h2>{scenario.chain.verdict}</h2>
            <p className="verdict">{scenario.report.summary}</p>
            <div className="chain" style={{ marginTop: 16 }}>
              {scenario.chain.nodes.map((n, i) => (
                <div key={n.id} style={{ display: "flex", gap: 4, flex: 1, minWidth: 80 }}>
                  <div className={classNames("chain-node", n.kind, "show")} style={{ flex: 1 }}>
                    <b>{n.label}</b>
                    <span>{n.detail}</span>
                  </div>
                  {i < scenario.chain.nodes.length - 1 && <div className="chain-arrow">→</div>}
                </div>
              ))}
            </div>
            <div className="ev">
              {evidenceFor(["EV-11", "EV-02", "EV-04", "EV-06"]).map((e) => (
                <div key={e.id}>
                  <i>{e.id}</i>
                  <span>
                    <b>{e.title}</b> — {e.detail}
                  </span>
                </div>
              ))}
            </div>
            <div className="actions">
              <button onClick={reset}>Run it again (R)</button>
              <Link to={`/cases/${scenario.case.id}`} style={{ textDecoration: "none" }}>
                <button className="ghost">Open case file</button>
              </Link>
              <Link to="/dashboard" style={{ textDecoration: "none" }}>
                <button className="ghost">Quality dashboard</button>
              </Link>
            </div>
            <div className="row between" style={{ marginTop: 14, fontSize: 9, color: "#8a7f6c", fontFamily: "var(--mono)" }}>
              <span>RUN TIME {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")} · 3 findings · 1 correction</span>
              <span>SCAN THE ROOM · SCAN THE PART</span>
            </div>
          </div>
        </div>
      )}
      <div className={`toast${toast ? " show" : ""}`}>{toast}</div>
    </div>
  );
}
