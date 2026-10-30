import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { useUI, navigateWithTransition } from "../lib/ui";
import { askLocal } from "../lib/ask";
import { Icon } from "./Icon";

interface Item {
  id: string;
  label: string;
  hint?: string;
  group: string;
  icon: string;
  run: () => void;
}

const RECENT_KEY = "rootcause.recent.v1";

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const { pack, proactive, scanProactive, say, dataMode, setDataMode } = useStore();
  const ui = useUI();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const [recent, setRecent] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]") as string[];
    } catch {
      return [];
    }
  });

  const go = (to: string, id?: string) => {
    if (id) {
      const next = [id, ...recent.filter((x) => x !== id)].slice(0, 6);
      setRecent(next);
      localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    }
    onClose();
    navigateWithTransition(navigate, to);
  };

  const items = useMemo<Item[]>(() => {
    const nav: Item[] = [
      { id: "nav-now", label: "Now — decision queue", group: "Navigate", icon: "target", hint: "G N", run: () => go("/") },
      { id: "nav-watch", label: "Watchlist", group: "Navigate", icon: "target", hint: "G W", run: () => go("/watchlist") },
      { id: "nav-cases", label: "Cases", group: "Navigate", icon: "cases", hint: "G C", run: () => go("/cases") },
      { id: "nav-review", label: "Review queue", group: "Navigate", icon: "review", hint: "G R", run: () => go("/review") },
      { id: "nav-reports", label: "Reports", group: "Navigate", icon: "report", run: () => go("/reports") },
      { id: "nav-brief", label: "Shift brief", group: "Navigate", icon: "calendar", run: () => go("/brief") },
      { id: "nav-alerts", label: "Alert center", group: "Navigate", icon: "alert", run: () => go("/alerts") },
      { id: "nav-proactive", label: "Proactive control room", group: "Navigate", icon: "gauge", run: () => go("/proactive") },
      { id: "nav-dashboard", label: "Quality dashboard", group: "Navigate", icon: "dashboard", run: () => go("/dashboard") },
      { id: "nav-proof", label: "Manager proof", group: "Navigate", icon: "chart", run: () => go("/proof") },
      { id: "nav-cut", label: "10-minute manager cut", group: "Navigate", icon: "play", run: () => go("/cut") },
      { id: "nav-newcase", label: "New case", group: "Navigate", icon: "plus", run: () => go("/cases/new") },
      { id: "nav-connectors", label: "Connectors", group: "Navigate", icon: "connectors", run: () => go("/connectors") },
      { id: "nav-admin", label: "Admin", group: "Navigate", icon: "admin", run: () => go("/admin") },
      { id: "nav-about", label: "About RootCause", group: "Navigate", icon: "about", run: () => go("/about") },
      { id: "nav-stage", label: "Stage piece", group: "Navigate", icon: "stage", run: () => go("/stage") },
      { id: "nav-booth", label: "Booth demo", group: "Navigate", icon: "booth", run: () => go("/booth") },
    ];
    const actions: Item[] = [
      { id: "act-scan", label: "Run a proactive scan", group: "Actions", icon: "refresh", run: () => { scanProactive(); onClose(); } },
      { id: "act-theme", label: ui.theme === "dark" ? "Switch to light desk mode" : "Switch to dark control room", group: "Actions", icon: "spark", run: () => { ui.toggleTheme(); onClose(); } },
      { id: "act-density", label: ui.density === "comfortable" ? "Use compact density" : "Use comfortable density", group: "Actions", icon: "grid", run: () => { ui.setDensity(ui.density === "comfortable" ? "compact" : "comfortable"); onClose(); } },
      { id: "act-datasource", label: ui.showDataSource ? "Hide the data notice" : "Show the data notice", group: "Actions", icon: "shield", run: () => { ui.setShowDataSource(!ui.showDataSource); onClose(); } },
      { id: "act-mode", label: dataMode === "own" ? "Open the reference workspace" : "Open my workspace", group: "Actions", icon: "grid", run: () => { setDataMode(dataMode === "own" ? "reference" : "own"); go("/"); }, hint: dataMode },
      { id: "act-help", label: "Keyboard shortcuts", group: "Actions", icon: "about", hint: "?", run: () => { onClose(); window.dispatchEvent(new CustomEvent("rootcause:shortcuts")); } },
      { id: "act-capture", label: "Start from a photo", group: "Actions", icon: "camera", run: () => go("/capture") },
    ];
    const cases: Item[] = (pack?.scenarios ?? []).map((s) => ({
      id: `case-${s.case.id}`,
      label: `${s.case.id} · ${s.case.defect_type}`,
      hint: s.case.part,
      group: "Cases",
      icon: "cases",
      run: () => go(`/cases/${s.case.id}`, `case-${s.case.id}`),
    }));
    const watches: Item[] = (proactive?.watches ?? [])
      .filter((w) => !["dismissed"].includes(w.status))
      .map((w) => ({
        id: `watch-${w.id}`,
        label: `${w.id} · ${w.title}`,
        hint: w.status,
        group: "Watches",
        icon: "target",
        run: () => go(`/watch/${w.id}`, `watch-${w.id}`),
      }));
    return [...nav, ...actions, ...watches, ...cases];
  }, [pack, proactive, ui, recent, scanProactive]); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      const recentItems = items.filter((i) => recent.includes(i.id));
      return [...recentItems, ...items.filter((i) => !recent.includes(i.id))].slice(0, 18);
    }
    return items
      .filter((i) => `${i.label} ${i.hint ?? ""} ${i.group}`.toLowerCase().includes(q))
      .slice(0, 16);
  }, [items, query, recent]);

  const answer = useMemo(() => {
    if (query.trim().length < 4) return null;
    const q = query.toLowerCase();
    const candidates = proactive?.watches.filter((w) => !["dismissed", "converted"].includes(w.status)) ?? [];
    const watch =
      candidates.find((w) => q.includes("hydrogen") && w.title.toLowerCase().includes("hydrogen")) ??
      candidates.find((w) => (q.includes("moist") || q.includes("dry")) && w.title.toLowerCase().includes("dryer")) ??
      candidates.find((w) => q.includes("laser") && w.title.toLowerCase().includes("laser")) ??
      candidates[0];
    return askLocal(query, { proactive: proactive ?? undefined, watch, role: ui.role });
  }, [query, proactive, ui.role]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setSelected(0);
    window.setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key === "ArrowDown") { e.preventDefault(); setSelected((s) => Math.min(filtered.length - 1, s + 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setSelected((s) => Math.max(0, s - 1)); }
      if (e.key === "Enter") {
        e.preventDefault();
        filtered[selected]?.run();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, filtered, selected, onClose]);

  if (!open) return null;
  return (
    <div className="command-back" role="dialog" aria-modal="true" aria-label="Command palette" onClick={onClose}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        <div className="command-input">
          <Icon name="search" size={16} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelected(0); }}
            placeholder="Search, jump, or ask a case…"
            aria-label="Search, jump, or ask a case"
          />
          <span className="kbd">esc</span>
        </div>
        <div className="command-list">
          {filtered.map((item, i) => (
            <button
              key={item.id}
              className={`command-item${i === selected ? " sel" : ""}`}
              onMouseEnter={() => setSelected(i)}
              onClick={item.run}
            >
              <Icon name={item.icon} size={14} />
              <span>{item.label}</span>
              {item.hint && <span className="hint">{item.hint}</span>}
            </button>
          ))}
          {filtered.length === 0 && <div className="command-empty">No actions match. Try “why hydrogen” or “hold batch”.</div>}
          {answer && (
            <div className="ask-answer">
              <div className="row between mb8">
                <span className="xsmall" style={{ letterSpacing: ".08em", textTransform: "uppercase", color: "var(--soft)" }}>Ask RootCause</span>
                {answer.refused && <span className="chip" style={{ fontSize: 11 }}>no evidence / no action</span>}
              </div>
              {answer.answer}
              <div className="mt8">
                {answer.citations.map((c) => <span key={c} className="ask-cite">{c}</span>)}
              </div>
            </div>
          )}
        </div>
        <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)", fontSize: 11.5, color: "var(--soft)" }}>
          <span>↑↓ navigate · ↵ open · esc close</span>
          <span>Answers cite evidence. The engineer decides.</span>
        </div>
      </div>
    </div>
  );
}
