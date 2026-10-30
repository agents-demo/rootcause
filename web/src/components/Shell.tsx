import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState, type ReactNode } from "react";
import { useStore } from "../lib/store";
import { useUI, type Role } from "../lib/ui";
import { Icon } from "./Icon";
import { CommandPalette } from "./CommandPalette";
import { DataSourceNote } from "./UI";

const modes = [
  { to: "/", label: "Now", icon: "target", end: true },
  { to: "/watchlist", label: "Watch", icon: "activity" },
  { to: "/cases", label: "Cases", icon: "cases" },
  { to: "/review", label: "Decide", icon: "review" },
  { to: "/reports", label: "Report", icon: "report" },
  { to: "/brief", label: "Brief", icon: "calendar" },
  { to: "/alerts", label: "Alerts", icon: "alert" },
];

const bottomModes = [
  { to: "/", label: "Now", icon: "target", match: [""] },
  { to: "/watchlist", label: "Watch", icon: "activity", match: ["/watchlist", "/watch"] },
  { to: "/cases", label: "Cases", icon: "cases", match: ["/cases"] },
  { to: "/review", label: "Decide", icon: "review", match: ["/review"] },
  { to: "/alerts", label: "Alerts", icon: "alert", match: ["/alerts"] },
];

const moreModes = [
  { to: "/brief", label: "Shift brief", icon: "calendar" },
  { to: "/reports", label: "Reports", icon: "report" },
  { to: "/dashboard", label: "Quality dashboard", icon: "dashboard" },
  { to: "/proof", label: "Manager proof", icon: "chart" },
  { to: "/cut", label: "10-minute demo cut", icon: "play" },
  { to: "/proactive", label: "Proactive room", icon: "gauge" },
  { to: "/capture", label: "Photo capture", icon: "camera" },
  { to: "/connectors", label: "Connectors", icon: "connectors" },
  { to: "/admin", label: "Site administration", icon: "admin" },
  { to: "/about", label: "About RootCause", icon: "about" },
];

const titles: Record<string, string> = {
  "/": "Now",
  "/about": "About RootCause",
  "/stage": "The 90-second teardown",
  "/booth": "Functional demo",
  "/booth/proactive": "Proactive story",
  "/watchlist": "Watchlist",
  "/watch": "Watch case",
  "/brief": "Shift brief",
  "/alerts": "Alert center",
  "/proactive": "Proactive control room",
  "/cases": "Case history",
  "/dashboard": "Quality dashboard",
  "/proof": "Manager proof",
  "/cut": "Manager cut",
  "/review": "Engineer review",
  "/reports": "Quality reports",
  "/capture": "Mobile capture",
  "/connectors": "Connectors",
  "/admin": "Site administration",
};

export function Shell({ children }: { children: ReactNode }) {
  const { pack, proactive, toast, reset, live, readNotification, readAllNotifications } = useStore();
  const location = useLocation();
  const navigate = useNavigate();
  const ui = useUI();
  const [cmdOpen, setCmdOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [updateReady, setUpdateReady] = useState(false);
  const unread = proactive?.notifications.filter((n) => !n.read).length ?? 0;
  const base = location.pathname === "/" ? "/" : `/${location.pathname.split("/")[1] || "about"}`;
  const title = titles[base] ?? "RootCause";

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onUpdate = () => setUpdateReady(true);
    window.addEventListener("rootcause:update-ready", onUpdate);
    return () => window.removeEventListener("rootcause:update-ready", onUpdate);
  }, []);

  useEffect(() => {
    let gPressed = false;
    let gTimer: number | undefined;
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdOpen((v) => !v);
        return;
      }
      if (typing) return;
      if (e.key === "?") { e.preventDefault(); setShortcutsOpen(true); return; }
      if (e.key.toLowerCase() === "g") {
        gPressed = true;
        window.clearTimeout(gTimer);
        gTimer = window.setTimeout(() => { gPressed = false; }, 900);
        return;
      }
      if (gPressed) {
        gPressed = false;
        const map: Record<string, string> = { n: "/", w: "/watchlist", c: "/cases", r: "/review", b: "/brief", a: "/alerts", p: "/proactive", d: "/dashboard" };
        const to = map[e.key.toLowerCase()];
        if (to) { e.preventDefault(); navigate(to); }
      }
      if (e.key.toLowerCase() === "t") { ui.toggleTheme(); }
    };
    window.addEventListener("keydown", onKey);
    const openShortcuts = () => setShortcutsOpen(true);
    window.addEventListener("rootcause:shortcuts", openShortcuts);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("rootcause:shortcuts", openShortcuts);
      window.clearTimeout(gTimer);
    };
  }, [navigate, ui]);

  return (
    <div className="app-2026">
      <a href="#main-content" className="skip-link">Skip to content</a>

      <header className="instrument-bar">
        <NavLink to="/" className="brand-2026" aria-label="RootCause home">
          <span className="mark" />
          <span><b>ROOTCAUSE</b><small>QUALITY INTELLIGENCE</small></span>
        </NavLink>
        <span className="site-pill"><span className="dot live" /> Werk Süd · 4 lines</span>
        <button className="cmd-trigger" onClick={() => setCmdOpen(true)} aria-label="Open command palette">
          <Icon name="search" size={14} />
          <span>Search, jump or ask…</span>
          <span className="kbd">⌘K</span>
        </button>
        <span className="instrument-spacer" />
        <div className="instrument-actions">
          <span className="site-pill" title={live ? "Connected to the on-site API" : "Offline demo pack"}>
            <span className={`dot ${live ? "live" : "warn"}`} /> {live ? "On-site" : "Offline"}
          </span>
          <button className="icon-btn" onClick={() => setNotifOpen(true)} aria-label={`Notifications, ${unread} unread`}>
            <Icon name="alert" size={16} />
            {unread > 0 && <span className="dot warn" />}
          </button>
          <button className="icon-btn" onClick={ui.toggleTheme} aria-label={ui.theme === "dark" ? "Switch to light desk mode" : "Switch to dark control room"}>
            <Icon name={ui.theme === "dark" ? "spark" : "bolt"} size={16} />
          </button>
          <select
            className="role-select"
            value={ui.role}
            aria-label="View as role"
            onChange={(e) => ui.setRole(e.target.value as Role)}
          >
            <option value="quality_manager">Quality manager</option>
            <option value="engineer">Engineer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          <button className="icon-btn" onClick={reset} aria-label="Reset demo state" title="Reset demo state">
            <Icon name="reset" size={15} />
          </button>
          <div className="avatar" title="M. Weber">MW</div>
        </div>
      </header>

      <nav className="mode-rail" aria-label="Primary">
        {modes.map((m) => (
          <NavLink key={m.to} to={m.to} end={m.end} className={({ isActive }) => `rail-item${isActive ? " active" : ""}`}>
            <Icon name={m.icon} size={18} />
            <span>{m.label}</span>
          </NavLink>
        ))}
        <div className="rail-sep" />
        <button className="rail-item" onClick={() => setCmdOpen(true)}>
          <Icon name="grid" size={18} />
          <span>More</span>
        </button>
        <div className="rail-bottom">
          <button className="rail-item" onClick={() => setShortcutsOpen(true)} aria-label="Keyboard shortcuts">
            <Icon name="about" size={18} />
            <span>Keys</span>
          </button>
        </div>
      </nav>

      <nav className="bottom-nav-2026" aria-label="Primary mobile">
        {bottomModes.map((m) => {
          const active = m.match.includes(base);
          return (
            <NavLink
              key={m.to}
              to={m.to}
              end={m.to === "/"}
              className={`bottom-item${active ? " active" : ""}`}
              aria-current={active ? "page" : undefined}
            >
              <span className="bottom-icon">
                <Icon name={m.icon} size={20} />
                {m.to === "/alerts" && unread > 0 && <span className="bottom-badge">{unread > 9 ? "9+" : unread}</span>}
              </span>
              <span className="bottom-label">{m.label}</span>
            </NavLink>
          );
        })}
        <button
          type="button"
          className={`bottom-item${moreOpen ? " active" : ""}`}
          onClick={() => setMoreOpen((v) => !v)}
          aria-haspopup="dialog"
          aria-expanded={moreOpen}
        >
          <span className="bottom-icon"><Icon name="grid" size={20} /></span>
          <span className="bottom-label">More</span>
        </button>
      </nav>

      {moreOpen && (
        <div className="modal-back more-back" onClick={() => setMoreOpen(false)}>
          <div className="modal more-sheet" role="dialog" aria-modal="true" aria-label="More destinations" onClick={(e) => e.stopPropagation()}>
            <div className="row between mb12">
              <div>
                <div className="page-kicker">Navigate</div>
                <h3 style={{ fontSize: 19 }}>More of RootCause</h3>
              </div>
              <button className="btn ghost sm" onClick={() => setMoreOpen(false)} aria-label="Close"><Icon name="x" size={13} /></button>
            </div>
            <div className="more-grid">
              {moreModes.map((m) => (
                <button key={m.to} type="button" className="more-item" onClick={() => navigate(m.to)}>
                  <Icon name={m.icon} size={18} />
                  <span>{m.label}</span>
                </button>
              ))}
            </div>
            <div className="row gap8" style={{ marginTop: 14 }}>
              <button className="btn sm" onClick={() => { setMoreOpen(false); setCmdOpen(true); }}>
                <Icon name="search" size={13} /> Ask or jump
              </button>
              <button className="btn sm ghost" onClick={reset}><Icon name="reset" size={13} /> Reset reference data</button>
            </div>
          </div>
        </div>
      )}

      <div className="main-2026">
        <main className="content-2026" id="main-content" aria-label={title}>
          {ui.showDataSource && pack && <DataSourceNote seed={pack.meta.seed} live={live} />}
          {children}
        </main>
      </div>

      <div className={`toast${toast ? " show" : ""}`}>{toast}</div>

      {updateReady && (
        <div className="update-banner" role="status">
          <span>A new version of RootCause is ready.</span>
          <button className="btn sm" onClick={() => window.location.reload()}>Reload</button>
          <button className="icon-btn" aria-label="Dismiss update notice" onClick={() => setUpdateReady(false)}>
            <Icon name="x" size={12} />
          </button>
        </div>
      )}

      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} />

      {notifOpen && (
        <div className="modal-back" onClick={() => setNotifOpen(false)}>
          <div className="modal" style={{ width: "min(620px,100%)", maxHeight: "82vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
            <div className="row between mb12">
              <div>
                <div className="page-kicker">Notifications</div>
                <h3 style={{ fontSize: 20 }}>What needs attention</h3>
              </div>
              <button className="btn ghost sm" onClick={() => setNotifOpen(false)} aria-label="Close notifications"><Icon name="x" size={13} /></button>
            </div>
            <div className="row gap8 mb12">
              <button className="btn sm" onClick={readAllNotifications}>Mark all read</button>
              <NavLink to="/alerts" className="btn sm ghost" onClick={() => setNotifOpen(false)}>Open alert center</NavLink>
            </div>
            <div className="inbox">
              {(proactive?.notifications ?? []).slice(0, 8).map((n) => (
                <button key={n.id} className={`inbox-row${n.read ? "" : " unread"}`} style={{ width: "100%", textAlign: "left", background: "transparent", border: 0 }} onClick={() => { readNotification(n.id); if (n.watch_id) navigate(`/watch/${n.watch_id}`); setNotifOpen(false); }}>
                  <span className="marker" />
                  <span>
                    <h3>{n.title}</h3>
                    <p>{n.detail}</p>
                  </span>
                  <span className="meta">{new Date(n.at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}</span>
                </button>
              ))}
              {(proactive?.notifications.length ?? 0) === 0 && <div className="empty">No notifications.</div>}
            </div>
          </div>
        </div>
      )}

      {shortcutsOpen && (
        <div className="modal-back" onClick={() => setShortcutsOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="row between mb12">
              <h3>Keyboard & command</h3>
              <button className="btn ghost sm" onClick={() => setShortcutsOpen(false)} aria-label="Close shortcuts"><Icon name="x" size={13} /></button>
            </div>
            <div className="col gap6">
              {[
                ["⌘K / Ctrl K", "Command palette, search, ask"],
                ["G then N", "Now — decision queue"],
                ["G then W", "Watchlist"],
                ["G then C", "Cases"],
                ["G then R", "Review queue"],
                ["G then B", "Shift brief"],
                ["G then A", "Alert center"],
                ["G then P", "Proactive control room"],
                ["J / K", "Move down / up a queue"],
                ["A / R", "Accept / reject on a focused decision"],
                ["T", "Toggle desk / control-room theme"],
                ["?", "This sheet"],
              ].map(([k, v]) => (
                <div key={k} className="row between">
                  <span className="kbd" style={{ minWidth: 90 }}>{k}</span>
                  <span className="small muted">{v}</span>
                </div>
              ))}
            </div>
            <p className="xsmall soft mt12">The command palette also answers questions with evidence citations. It never controls the line.</p>
          </div>
        </div>
      )}
    </div>
  );
}
