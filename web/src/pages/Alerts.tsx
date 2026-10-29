import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { classNames, fmtDateTime, timeAgo } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";

const KIND_ICON: Record<string, string> = { watch: "target", recommendation: "check", followup: "refresh", data_quality: "alert", system: "cpu" };

export default function Alerts() {
  const { proactive, readNotification, readAllNotifications, updateSchedule, say } = useStore();
  const [filter, setFilter] = useState("all");
  const [webhook, setWebhook] = useState("");
  if (!proactive) return <div className="empty">Loading alert center…</div>;

  const notifications = useMemo(
    () => proactive.notifications.filter((n) => filter === "unread" ? !n.read : filter === "all" || n.kind === filter),
    [proactive.notifications, filter],
  );
  const unread = proactive.notifications.filter((n) => !n.read).length;
  const schedule = proactive.settings.schedule;

  return (
    <div>
      <PageHead
        kicker="Proactive · notifications"
        title="Alert center"
        subtitle="Grouped, deduplicated and quiet by default. An alert is a request for a human decision, not a control action. Every alert links back to its watch case."
        actions={
          <>
            <span className="chip amber"><Icon name="alert" size={11} /> {unread} unread</span>
            <button className="btn sm" onClick={readAllNotifications}>Mark all read</button>
            <Link className="btn primary sm" to="/watchlist">Open watchlist</Link>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Delivered</div><div className="value">{proactive.notifications.length}</div><div className="foot">in-app + Teams + digest</div></div>
        <div className="stat"><div className="label">Unread</div><div className="value">{unread}</div><div className="foot">triage SLA {schedule.triage_sla_min} min</div></div>
        <div className="stat"><div className="label">Alerts / line / shift</div><div className="value">{proactive.metrics.alerts_per_line_shift}</div><div className="foot">budget {schedule.false_alarm_budget} · no storm</div></div>
        <div className="stat"><div className="label">Quiet hours</div><div className="value" style={{ fontSize: 20 }}>{schedule.quiet_hours}</div><div className="foot">{schedule.digest_mode ? "digest on" : "digest off"} · on-call routing</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.5fr 1fr", alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head">
            <h3>Notifications</h3>
            <div className="row gap4" style={{ flexWrap: "wrap" }}>
              {["all", "unread", "watch", "recommendation", "data_quality", "followup"].map((f) => (
                <button key={f} className={`chip ${filter === f ? "amber" : ""}`} onClick={() => setFilter(f)}>{f}</button>
              ))}
            </div>
          </div>
          <div className="panel-body tight">
            <div className="col gap6">
              {notifications.map((n) => (
                <div key={n.id} className={classNames("ev-card", !n.read && "sel")} style={{ cursor: "default" }}>
                  <div className="row between">
                    <div className="row gap6">
                      <span className={`dot ${n.severity === "critical" ? "bad" : n.severity === "high" ? "warn" : "live"}`} />
                      <span className="kind">{n.kind}</span>
                      {!n.read && <span className="chip amber" style={{ fontSize: 7 }}>new</span>}
                    </div>
                    <span className="xsmall soft">{timeAgo(n.at)}</span>
                  </div>
                  <h4 style={{ fontSize: 11.5 }}>{n.title}</h4>
                  <p>{n.detail}</p>
                  <div className="row between mt8" style={{ gap: 8 }}>
                    <span className="src">{n.role} · {n.dedup_key}</span>
                    <div className="row gap4">
                      {n.watch_id && <Link className="btn sm ghost" to={`/watch/${n.watch_id}`}><Icon name={KIND_ICON[n.kind] ?? "alert"} size={10} /> {n.watch_id}</Link>}
                      {!n.read && <button className="btn sm ghost" onClick={() => readNotification(n.id)}>Mark read</button>}
                    </div>
                  </div>
                </div>
              ))}
              {notifications.length === 0 && <div className="empty">No notifications in this filter.</div>}
            </div>
          </div>
          <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
            <span className="xsmall soft">Deduplicated by watch group and kind.</span>
            <span className="xsmall mono soft">{notifications.length} shown</span>
          </div>
        </div>

        <div className="col-stack">
          <div className="panel">
            <div className="panel-head"><h3>Routing</h3><span className="sub">quiet hours + on-call</span></div>
            <div className="panel-body">
              <div className="row between">
                <div><div className="small" style={{ color: "var(--ink-2)" }}>Digest outside the shift</div><div className="xsmall soft">Collect low-priority alerts into one brief.</div></div>
                <button className={`switch ${schedule.digest_mode ? "on" : ""}`} onClick={() => updateSchedule({ digest_mode: !schedule.digest_mode })} aria-label="Digest mode" />
              </div>
              <div className="divider" />
              <div className="row between"><span className="small muted">Roles</span><span className="xsmall mono">{schedule.notification_roles.join(", ")}</span></div>
              <div className="row between mt8"><span className="small muted">Max alerts / shift</span><span className="xsmall mono">{schedule.max_alerts_per_shift}</span></div>
              <div className="row between mt8"><span className="small muted">Quiet hours</span><span className="xsmall mono">{schedule.quiet_hours}</span></div>
              <div className="row between mt8"><span className="small muted">Escalation SLA</span><span className="xsmall mono">{proactive.settings.escalation_sla}</span></div>
              <div className="divider" />
              <div className="xsmall soft" style={{ lineHeight: 1.5 }}>Alerts never carry a control command. Approving containment is a separate, named human action on the watch.</div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Channels</h3><span className="sub">delivered / opened</span></div>
            <div className="panel-body col gap8">
              {proactive.metrics.channels.map((c) => (
                <div key={c.name}>
                  <div className="row between"><span className="small muted">{c.name}</span><span className="xsmall mono">{c.opened}/{c.delivered}</span></div>
                  <div className="meter mt8" style={{ height: 3 }}><i style={{ width: `${(c.opened / c.delivered) * 100}%`, background: "var(--cyan)" }} /></div>
                  <div className="xsmall soft mt8">{c.note}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Webhook</h3><span className="sub">signed payloads</span></div>
            <div className="panel-body">
              <div className="field">
                <label>Endpoint</label>
                <input className="input" placeholder={schedule.webhook_url || "https://…"} value={webhook} onChange={(e) => setWebhook(e.target.value)} />
              </div>
              <button className="btn sm mt8" onClick={() => { updateSchedule({ webhook_url: webhook || schedule.webhook_url }); say("Webhook saved; test delivery is in-app only until the endpoint is reachable"); }}>Save endpoint</button>
              <div className="xsmall soft mt8">Payloads are signed with a shared secret; failed deliveries never block the in-app alert. The demo endpoint is intentionally invalid.</div>
              <button className="btn ghost sm mt8" onClick={() => say("Test webhook: in-app-only in the public demo")}>Send test</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
