import type { ReactNode } from "react";
import type { AuditEvent, CausalChain, Evidence, TraceStep } from "../types";
import { classNames } from "../lib/engine";
import { Icon } from "./Icon";

export function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === "critical" || severity === "high" ? "red" : severity === "medium" ? "amber" : "cyan";
  return <span className={`chip ${cls}`}>{severity}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { cls: string; label: string }> = {
    new: { cls: "", label: "New" },
    investigating: { cls: "amber", label: "Investigating" },
    awaiting_review: { cls: "cyan", label: "Awaiting review" },
    approved: { cls: "green", label: "Approved" },
    closed: { cls: "", label: "Closed" },
    draft: { cls: "amber", label: "Draft" },
    in_review: { cls: "cyan", label: "In review" },
    connected: { cls: "green", label: "Connected" },
    simulated: { cls: "amber", label: "Simulated" },
    available: { cls: "", label: "Available" },
    error: { cls: "red", label: "Error" },
  };
  const entry = map[status] ?? { cls: "", label: status };
  return (
    <span className={`chip ${entry.cls}`}>
      <i className={`dot ${entry.cls === "green" ? "live" : entry.cls === "red" ? "bad" : entry.cls === "amber" ? "warn" : ""}`} />
      {entry.label}
    </span>
  );
}

export function ChainViz({
  chain,
  revealed = true,
  compact = false,
}: {
  chain: CausalChain;
  revealed?: boolean;
  compact?: boolean;
}) {
  return (
    <div className="chain">
      {chain.nodes.map((node, i) => (
        <div key={node.id} style={{ display: "flex", gap: 4, alignItems: "stretch", flex: 1, minWidth: compact ? 70 : 90 }}>
          <div className={classNames("chain-node", node.kind, revealed && "show")} style={{ transitionDelay: `${i * 120}ms`, flex: 1 }}>
            <b>{node.label}</b>
            {!compact && <span>{node.detail}</span>}
          </div>
          {i < chain.nodes.length - 1 && <div className="chain-arrow">→</div>}
        </div>
      ))}
    </div>
  );
}

export function AgentTrace({ steps, onEvidence }: { steps: TraceStep[]; onEvidence?: (id: string) => void }) {
  return (
    <div className="trace">
      {steps.map((step) => (
        <div key={step.step} className={classNames("trace-step", step.status)}>
          <div className="trace-ico">{step.status === "waiting" ? "!" : step.step}</div>
          <div>
            <div className="tt">{step.title}</div>
            <div className="td">{step.detail}</div>
            <div className="tm">
              <span className="tool">{step.tool}</span>
              {step.ms > 0 && <span className="ms">{step.ms} ms</span>}
              {step.evidence.map((id) => (
                <button
                  key={id}
                  className="chip amber"
                  style={{ padding: "1px 5px", fontSize: 8 }}
                  onClick={() => onEvidence?.(id)}
                >
                  {id}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function EvidenceList({
  evidence,
  selected,
  onSelect,
  highlight = [],
  limit,
}: {
  evidence: Evidence[];
  selected?: string | null;
  onSelect?: (id: string) => void;
  highlight?: string[];
  limit?: number;
}) {
  const list = limit ? evidence.slice(0, limit) : evidence;
  return (
    <div className="evidence-list">
      {list.map((e) => (
        <button
          key={e.id}
          className={classNames("ev-card", selected === e.id && "sel")}
          onClick={() => onSelect?.(e.id)}
          style={{ textAlign: "left", font: "inherit" }}
        >
          <div className="top">
            <span className="eid">
              {e.id}
              {highlight.includes(e.id) && <span style={{ color: "var(--cyan)" }}> ●</span>}
            </span>
            <span className="kind">{e.kind}</span>
          </div>
          <h5>{e.title}</h5>
          <p>{e.detail}</p>
          <div className="row between" style={{ marginTop: 5 }}>
            <span className="src">{e.source}</span>
            <span className="strength" title={`Evidence strength ${Math.round(e.strength * 100)}%`}>
              {Array.from({ length: 5 }).map((_, i) => (
                <i key={i} className={i < Math.round(e.strength * 5) ? "on" : ""} />
              ))}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

export function ProvenanceBlock({ items, note, compact = false }: { items: Record<string, string>; note?: string; compact?: boolean }) {
  return (
    <div className="col gap6">
      {Object.entries(items).map(([k, v]) => (
        <div key={k} className="row between" style={{ alignItems: "flex-start", gap: 10 }}>
          <span className="xsmall soft" style={{ textTransform: "capitalize", minWidth: 58 }}>{k.replace(/_/g, " ")}</span>
          <span className="xsmall" style={{ color: "var(--ink-2)", textAlign: "right", lineHeight: 1.45 }}>{v}</span>
        </div>
      ))}
      {!compact && note && <p className="xsmall soft" style={{ marginTop: 4, lineHeight: 1.5 }}>{note}</p>}
    </div>
  );
}

export function AuditTrail({ events, limit = 8 }: { events: AuditEvent[]; limit?: number }) {
  if (!events.length) return <div className="empty">No audit events yet.</div>;
  return (
    <div className="col gap6">
      {events.slice(0, limit).map((e) => (
        <div key={e.id} className="row" style={{ alignItems: "flex-start", gap: 9, padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,.05)" }}>
          <span className="mono xsmall soft" style={{ minWidth: 92 }}>{new Date(e.at).toLocaleString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
          <span className="xsmall" style={{ color: "var(--ink-2)", flex: 1 }}>
            <b style={{ fontWeight: 600 }}>{e.actor}</b> · {e.action} <span className="soft">· {e.object}</span>
            <span className="xsmall soft" style={{ display: "block", marginTop: 1 }}>{e.detail}</span>
          </span>
          <span className="chip" style={{ fontSize: 7.5 }}>{e.model_version}</span>
        </div>
      ))}
    </div>
  );
}

export function Modal({
  open,
  title,
  children,
  onClose,
  actions,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  actions?: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="row between">
          <h3>{title}</h3>
          <button className="btn ghost sm" onClick={onClose} aria-label="Close"><Icon name="x" size={14} /></button>
        </div>
        {children}
        {actions && <div className="actions">{actions}</div>}
      </div>
    </div>
  );
}

export function PageHead({
  kicker,
  title,
  subtitle,
  actions,
}: {
  kicker?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div>
        {kicker && <div className="xsmall mono amber" style={{ letterSpacing: "0.16em", textTransform: "uppercase", marginBottom: 5 }}>{kicker}</div>}
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}
