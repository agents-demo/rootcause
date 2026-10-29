import { NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useStore } from "../lib/store";
import { Icon } from "./Icon";

const groups = [
  {
    label: "Operate",
    items: [
      { to: "/stage", label: "Stage piece", icon: "stage" },
      { to: "/booth", label: "Booth demo", icon: "booth" },
      { to: "/cases", label: "Cases", icon: "cases", pill: "4" },
      { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
    ],
  },
  {
    label: "Work",
    items: [
      { to: "/review", label: "Review queue", icon: "review", pill: "2" },
      { to: "/reports", label: "Reports", icon: "report" },
      { to: "/capture", label: "Mobile capture", icon: "camera" },
    ],
  },
  {
    label: "Site",
    items: [
      { to: "/connectors", label: "Connectors", icon: "connectors" },
      { to: "/admin", label: "Admin", icon: "admin" },
      { to: "/about", label: "About", icon: "about" },
    ],
  },
];

const titles: Record<string, { section: string; page: string; crumb?: string }> = {
  "/": { section: "Product", page: "About RootCause" },
  "/about": { section: "Product", page: "About RootCause" },
  "/stage": { section: "Stage", page: "The 90-second teardown" },
  "/booth": { section: "Booth", page: "Functional demo" },
  "/cases": { section: "Cases", page: "Case history" },
  "/dashboard": { section: "Pilot", page: "Quality dashboard" },
  "/review": { section: "Work", page: "Engineer review" },
  "/reports": { section: "Work", page: "Quality reports" },
  "/capture": { section: "Work", page: "Mobile capture" },
  "/connectors": { section: "Site", page: "Data connectors" },
  "/admin": { section: "Site", page: "Site administration" },
};

export function Shell({ children }: { children: ReactNode }) {
  const { pack, toast, reset, live } = useStore();
  const location = useLocation();
  const base = location.pathname === "/" ? "/" : `/${location.pathname.split("/")[1] || "about"}`;
  const meta = titles[base] ?? titles["/about"];
  const alertCount = pack?.alerts.filter((a) => !a.acknowledged).length ?? 0;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>ROOTCAUSE</h1>
            <small>QUALITY INTELLIGENCE</small>
          </div>
        </div>
        <nav className="nav">
          {groups.map((group) => (
            <div key={group.label}>
              <div className="nav-group">{group.label}</div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  aria-label={item.label}
                  title={item.label}
                  className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
                >
                  <Icon name={item.icon} />
                  <span className="label">{item.label}</span>
                  {item.pill && <span className="pill chip" style={{ fontSize: 8, padding: "2px 6px" }}>{item.pill}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="site-card">
            <div className="row between"><span>Werk Süd</span><b>On-site</b></div>
            <div className="row between" style={{ marginTop: 4 }}>
              <span className="xsmall">NPU 310P · 4 lines</span>
              <span className="dot live" />
            </div>
            <div className="bar"><i /></div>
            <div className="row between" style={{ marginTop: 6 }}>
              <span className="xsmall soft">No outbound network</span>
              <span className="xsmall mono soft">v0.9</span>
            </div>
          </div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="crumbs">
            <span>Werk Süd</span>
            <Icon name="chevron" size={10} />
            <span>{meta.section}</span>
            <Icon name="chevron" size={10} />
            <b>{meta.page}</b>
          </div>
          <div className="spacer" />
          <div className="top-status">
            <span className="item hide-md">
              {live ? <span className="dot live" /> : <span className="dot warn" />} {live ? "On-site API" : "Offline pack"}
            </span>
            <span className="item hide-md">
              <Icon name="alert" size={13} />
              {alertCount} open
            </span>
            <span className="item hide-md mono xsmall">22 Oct · 06:42</span>
            <button className="btn ghost sm" onClick={reset} title="Reset demo state">
              <Icon name="reset" size={13} /> Reset
            </button>
            <div className="avatar">MW</div>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>

      <div className={`toast${toast ? " show" : ""}`}>{toast}</div>
    </div>
  );
}
