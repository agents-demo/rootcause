import { useMemo, useState, type CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { useUI, navigateWithTransition } from "../lib/ui";
import { fmtDateTime, pct, timeAgo } from "../lib/engine";
import { Icon } from "../components/Icon";
import { DataSourceNote } from "../components/UI";

interface Decision {
  id: string;
  kind: string;
  title: string;
  detail: string;
  meta: string;
  metaValue: string;
  to: string;
  severity: "critical" | "high" | "warning" | "info";
}

export default function Home() {
  const { pack, proactive, caseStatus, reportFor, actionsDone, live } = useStore();
  const ui = useUI();
  const navigate = useNavigate();
  const [onboarding, setOnboarding] = useState(() => localStorage.getItem("rootcause.onboarded") !== "1");

  const decisions = useMemo<Decision[]>(() => {
    if (!pack || !proactive) return [];
    const list: Decision[] = [];
    proactive.watches
      .filter((w) => ["watching", "triage", "investigating"].includes(w.status))
      .forEach((w) => list.push({
        id: w.id,
        kind: w.status === "triage" ? "Watch triage" : "Risk watch",
        title: w.title,
        detail: `${w.pattern_name} · ${w.signal_count} signals · ${w.owner}`,
        meta: "risk",
        metaValue: String(Math.round(w.risk_score * 100)),
        to: `/watch/${w.id}`,
        severity: w.severity === "critical" ? "critical" : w.severity === "high" ? "high" : "warning",
      }));
    pack.scenarios.forEach((s) => {
      const status = caseStatus(s.case.id);
      const report = reportFor(s.case.id);
      if (status === "awaiting_review" || (report?.status === "draft" && status !== "approved")) {
        list.push({
          id: s.case.id,
          kind: status === "awaiting_review" ? "Cause decision" : "Report draft",
          title: `${s.case.defect_type}`,
          detail: `${s.case.id} · ${s.case.part} · batch ${s.case.batch_id}`,
          meta: "case",
          metaValue: s.case.id.replace("RC-", "#"),
          to: status === "awaiting_review" ? `/cases/${s.case.id}` : `/reports?case=${s.case.id}`,
          severity: s.case.severity === "critical" ? "critical" : "high",
        });
      }
    });
    pack.actions
      .filter((a) => a.status !== "done" && !actionsDone.includes(a.id))
      .forEach((a) => list.push({
        id: a.id,
        kind: "Corrective action",
        title: a.title,
        detail: `${a.owner} · due ${fmtDateTime(a.due)}`,
        meta: "action",
        metaValue: a.case_id,
        to: "/dashboard",
        severity: "warning",
      }));
    proactive.notifications
      .filter((n) => !n.read && n.kind === "data_quality")
      .forEach((n) => list.push({
        id: n.id,
        kind: "Coverage",
        title: n.title,
        detail: n.detail,
        meta: "alert",
        metaValue: "data",
        to: "/alerts",
        severity: "info",
      }));
    const rank = { critical: 0, high: 1, warning: 2, info: 3 };
    return list.sort((a, b) => rank[a.severity] - rank[b.severity]);
  }, [pack, proactive, caseStatus, reportFor, actionsDone]);

  if (!pack || !proactive) return <div className="empty">Loading the decision queue…</div>;
  const m = proactive.metrics;
  const openWatches = proactive.watches.filter((w) => ["watching", "triage", "investigating"].includes(w.status)).length;
  const openCases = pack.scenarios.filter((s) => caseStatus(s.case.id) !== "approved").length;
  const actions = pack.actions.filter((a) => a.status !== "done" && !actionsDone.includes(a.id)).length;
  const top = decisions[0];
  const roleCopy =
    ui.role === "operator" ? "Capture what you see. The engineer investigates." :
    ui.role === "engineer" ? "The watches and cases that need your judgement now." :
    ui.role === "admin" ? "Coverage, scheduler health and site controls." :
    "The decisions that protect this week's quality.";

  return (
    <div>
      <div className="page-header-2026" style={{ marginBottom: 12 }}>
        <div>
          <div className="page-kicker">{new Date(pack.meta.anchor).toLocaleDateString(undefined, { weekday: "long", day: "2-digit", month: "long" })} · shift B</div>
          <h1 className="page-title">Now</h1>
          <p className="page-sub">{roleCopy}</p>
        </div>
        <div className="page-actions-2026">
          <button className="btn" onClick={() => navigateWithTransition(navigate, "/brief")}><Icon name="calendar" size={13} /> Shift brief</button>
          <button className="btn primary" onClick={() => setCmdOpenHint()}><Icon name="search" size={13} /> Ask or jump <span className="kbd">⌘K</span></button>
        </div>
      </div>

      <DataSourceNote seed={pack.meta.seed} live={live} />

      <div className="now-grid">
        <div>
          <div className="metric-inline" style={{ marginBottom: 22 }}>
            <div>Open watches <b>{openWatches}</b></div>
            <div>Unresolved cases <b>{openCases}</b></div>
            <div>Actions due <b>{actions}</b></div>
            <div>Coverage <b>{pct(m.coverage_pct, 1)}</b></div>
            <div>Watch precision <b>{pct(m.watch_precision, 0)}</b></div>
          </div>

          <div className="now-lead">
            <h2>{decisions.length ? `${decisions.length} decision${decisions.length === 1 ? "" : "s"} need a human.` : "Nothing needs a decision. Keep watching."}</h2>
            <p>
              {top
                ? `The first is ${top.title.toLowerCase()} on ${top.metaValue === "case" ? "the case queue" : "the watchlist"}. RootCause has assembled the evidence; you decide.`
                : "The scheduler is healthy and no watch is waiting. The next shift brief will show what changed."}
            </p>
          </div>

          {onboarding && (
            <div className="panel" style={{ margin: "18px 0", borderColor: "rgba(242,180,92,.24)", background: "var(--accent-dim)" }}>
              <div className="panel-body" style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                <Icon name="target" size={20} />
                <div style={{ flex: 1 }}>
                  <b className="small">This is a decision queue, not a dashboard.</b>
                  <p className="small muted" style={{ marginTop: 3 }}>
                    Watches are risks before a defect. Cases are defects under investigation. The command palette (`⌘K`) can jump or answer a question with evidence. Nothing here changes the line.
                  </p>
                </div>
                <button className="btn sm ghost" onClick={() => { setOnboarding(false); localStorage.setItem("rootcause.onboarded", "1"); }}>Got it</button>
              </div>
            </div>
          )}

          <div className="queue-section-title"><span>Decision queue</span><span>{decisions.length} open</span></div>
          <div className="decision-queue">
            {decisions.map((d, i) => (
              <button
                key={`${d.kind}-${d.id}`}
                className="decision-row"
                onClick={() => navigateWithTransition(navigate, d.to)}
                style={{ viewTransitionName: `decision-${d.id}` } as CSSProperties}
              >
                <span className={`severity ${d.severity}`} />
                <span>
                  <span className="kind">{d.kind} · {i === 0 ? "first" : `#${i + 1}`}</span>
                  <h3>{d.title}</h3>
                  <p>{d.detail}</p>
                </span>
                <span className="meta"><b>{d.metaValue}</b>{d.meta}</span>
              </button>
            ))}
            {decisions.length === 0 && <div className="queue-empty">No open decision. The next scan runs every {proactive.settings.schedule.interval_minutes} minutes.</div>}
          </div>
        </div>

        <aside aria-label="Context">
          <div className="rail-card" style={{ borderTop: 0, paddingTop: 0 }}>
            <h3>Shift brief</h3>
            <p>{proactive.briefs[0]?.summary ?? "No brief generated yet."}</p>
            <button className="btn sm mt12" onClick={() => navigateWithTransition(navigate, "/brief")}>Open the brief</button>
          </div>
          <div className="rail-card">
            <h3>Top risk</h3>
            {top ? (
              <button className="rail-link" onClick={() => navigateWithTransition(navigate, top.to)} style={{ background: "transparent", border: 0, width: "100%" }}>
                <span>{top.title}</span><Icon name="arrow" size={12} />
              </button>
            ) : <p>No active risk.</p>}
            <div className="row between mt8"><span className="xsmall soft">Median triage</span><span className="xsmall mono">{m.median_triage_min} min</span></div>
            <div className="row between mt8"><span className="xsmall soft">False-alarm budget</span><span className="xsmall mono">{proactive.settings.schedule.false_alarm_budget}/line/shift</span></div>
          </div>
          <div className="rail-card">
            <h3>Coverage</h3>
            {proactive.coverage.map((c) => (
              <div key={c.line_id} style={{ marginBottom: 9 }}>
                <div className="row between"><span className="xsmall muted">{pack.lines.find((l) => l.id === c.line_id)?.name ?? c.line_id}</span><span className={`xsmall mono ${c.pct < 0.95 ? "amber" : "green"}`}>{pct(c.pct, 0)}</span></div>
                <div className="meter mt8" style={{ height: 3 }}><i style={{ width: `${c.pct * 100}%`, background: c.pct < 0.95 ? "var(--accent)" : "var(--ok)" }} /></div>
              </div>
            ))}
            <p className="xsmall soft mt8">Below the floor, no quality risk is scored.</p>
          </div>
          <div className="rail-card">
            <h3>Quick actions</h3>
            <button className="rail-link" onClick={() => navigateWithTransition(navigate, "/capture")} style={{ background: "transparent", border: 0, width: "100%" }}><span>Capture a defect</span><Icon name="camera" size={12} /></button>
            <button className="rail-link" onClick={() => navigateWithTransition(navigate, "/watchlist")} style={{ background: "transparent", border: 0, width: "100%" }}><span>Open the watchlist</span><Icon name="target" size={12} /></button>
            <button className="rail-link" onClick={() => navigateWithTransition(navigate, "/proactive")} style={{ background: "transparent", border: 0, width: "100%" }}><span>Calibrate the scheduler</span><Icon name="gauge" size={12} /></button>
          </div>
          <div className="rail-card">
            <h3>Last scan</h3>
            <div className="row between"><span className="xsmall muted">Scheduler</span><span className={`chip ${proactive.health?.status === "ok" ? "green" : "red"}`} style={{ fontSize: 11 }}>{proactive.health?.status ?? "unknown"}</span></div>
            <div className="row between mt8"><span className="xsmall soft">Last scan</span><span className="xsmall mono">{proactive.health?.last_scan ? timeAgo(proactive.health.last_scan) : "—"}</span></div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function setCmdOpenHint() {
  window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true }));
}
