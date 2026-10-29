import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { eur, fmtDate } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead, StatusBadge } from "../components/UI";

export default function Admin() {
  const { pack, setSharing, say, live } = useStore();
  const [plant, setPlant] = useState("plant-de");
  const [openPack, setOpenPack] = useState<string | null>("iso9001");
  const [npu, setNpu] = useState(true);
  const [sharing, setSharingLocal] = useState(false);
  const [integrations, setIntegrations] = useState<{
    ready: boolean;
    agent: { configured: boolean; backend: string; model?: string; detail: string };
    npu: { ready: boolean; backend: string; device?: string; error?: string };
    connectors: { total: number; live: number; simulated: number };
  } | null>(null);

  useEffect(() => {
    if (!live) return;
    fetch(new URL("api/integrations", document.baseURI).toString())
      .then((r) => (r.ok ? r.json() : null))
      .then(setIntegrations)
      .catch(() => setIntegrations(null));
  }, [live]);

  if (!pack) return <div className="empty">Loading site…</div>;
  const lines = pack.lines.filter((l) => l.plant_id === plant);
  const plantInfo = pack.plants.find((p) => p.id === plant);
  const active = plantInfo?.id ?? "plant-de";

  function toggleSharing() {
    const next = !sharing;
    setSharingLocal(next);
    setSharing(next);
  }

  function exportCompliance(id: string) {
    const c = pack!.compliance.find((x) => x.id === id);
    if (!c) return;
    const text = [
      `# ${c.name} — evidence map`,
      "",
      `Standard: ${c.standard}`,
      `Status: ${c.status} · ${c.covered}/${c.controls} controls covered`,
      `Generated: ${new Date().toISOString()}`,
      "",
      "| Control | Evidence | State |",
      "|---|---|---|",
      ...["Case ownership", "Documented method", "Approval before closure", "Corrective action loop", "Record retention", "Management review"].map(
        (control) => `| ${control} | RootCause case store and audit trail | covered |`,
      ),
      "",
      "This is an evidence map for a pilot review, not a certificate. A notified body performs the audit.",
    ].join("\n");
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rootcause-${id}-evidence-map.md`;
    a.click();
    URL.revokeObjectURL(url);
    say("Compliance evidence map downloaded");
  }

  return (
    <div>
      <PageHead
        kicker="Site administration"
        title="One factory, four lines, one record"
        subtitle="The pilot is deliberately single-site. Users, lines, billing, the NPU option and the compliance evidence map live here. Sharing with other factories is opt-in and anonymised."
        actions={
          <>
            <span className="chip green"><span className="dot live" /> Pilot · day 34</span>
            <Link className="btn sm" to="/proactive">Proactive controls <Icon name="gauge" size={12} /></Link>
            <button className="btn sm" onClick={() => say("Site settings saved")}><Icon name="check" size={12} /> Save</button>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Plant</div><div className="value" style={{ fontSize: 21 }}>{plantInfo?.name}</div><div className="foot">{plantInfo?.site}, {plantInfo?.country}</div></div>
        <div className="stat"><div className="label">Lines</div><div className="value">{pack.billing.lines}</div><div className="foot">single-site pilot</div></div>
        <div className="stat"><div className="label">MRR</div><div className="value">{eur(pack.billing.mrr_eur)}</div><div className="foot">{pack.billing.plan}</div></div>
        <div className="stat"><div className="label">Next invoice</div><div className="value" style={{ fontSize: 21 }}>{fmtDate(pack.billing.next_invoice)}</div><div className="foot">per line + NPU option</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.35fr 1fr", alignItems: "start" }}>
        <div className="col-stack">
          <div className="panel">
            <div className="panel-head">
              <h3>Production lines</h3>
              <div className="row gap4">
                {pack.plants.map((p) => (
                  <button key={p.id} className={`chip ${active === p.id ? "amber" : ""}`} onClick={() => setPlant(p.id)}>{p.name}</button>
                ))}
              </div>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead><tr><th>Line</th><th>Process</th><th>Part</th><th>Cameras</th><th>Machines</th><th>Phase</th><th /></tr></thead>
                <tbody>
                  {lines.map((l) => (
                    <tr key={l.id}>
                      <td className="small" style={{ color: "var(--ink-2)", fontWeight: 600 }}>{l.name}</td>
                      <td className="small muted">{l.process}</td>
                      <td className="xsmall muted">{l.part}</td>
                      <td className="mono small">{l.cameras}</td>
                      <td className="mono small">{l.machines}</td>
                      <td><span className="chip green" style={{ fontSize: 11 }}>production</span></td>
                      <td><Icon name="chevron" size={12} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
              <span className="xsmall soft">Each line has separate data channels and its own case scope.</span>
              <span className="xsmall mono soft">{lines.length} lines</span>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Users & roles</h3><span className="sub">engineer in charge</span></div>
            <div className="panel-body" style={{ padding: 0 }}>
              <table className="table">
                <thead><tr><th>Name</th><th>Role</th><th>Access</th><th /></tr></thead>
                <tbody>
                  {pack.users.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <div className="row gap8">
                          <span className="avatar" style={{ width: 26, height: 26, fontSize: 11 }}>{u.initials}</span>
                          <span className="small" style={{ color: "var(--ink-2)" }}>{u.name}</span>
                        </div>
                      </td>
                      <td><span className="tag">{u.role.replace("_", " ")}</span></td>
                      <td className="xsmall muted">{u.line_ids.length ? u.line_ids.map((l) => l.replace("line-", "L")).join(", ") : "site"}</td>
                      <td><button className="btn sm ghost">Edit</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Compliance packs</h3><span className="sub">evidence maps, not certificates</span></div>
            <div className="panel-body col gap8">
              {pack.compliance.map((c) => (
                <div key={c.id} style={{ border: "1px solid var(--line)", borderRadius: 8, padding: "9px 11px" }}>
                  <div className="row between" style={{ cursor: "pointer" }} onClick={() => setOpenPack(openPack === c.id ? null : c.id)}>
                    <div>
                      <div className="small" style={{ color: "var(--ink-2)", fontWeight: 600 }}>{c.name}</div>
                      <div className="xsmall soft">{c.standard} · {c.detail}</div>
                    </div>
                    <div className="row gap8">
                      <span className="xsmall mono">{c.covered}/{c.controls}</span>
                      <StatusBadge status={c.status === "ready" ? "approved" : c.status === "in_progress" ? "investigating" : "new"} />
                      <Icon name={openPack === c.id ? "chevronDown" : "chevron"} size={13} />
                    </div>
                  </div>
                  <div className="meter mt8"><i style={{ width: `${(c.covered / c.controls) * 100}%`, background: c.status === "ready" ? "var(--green)" : "var(--amber)" }} /></div>
                  {openPack === c.id && (
                    <div className="mt12">
                      <div className="col gap4">
                        {["Electronic signature", "Immutable audit trail", "Reason for change", "Access control", "Record retention"].map((ctrl) => (
                          <div key={ctrl} className="row between">
                            <span className="xsmall muted">{ctrl}</span>
                            <span className="chip green" style={{ fontSize: 11 }}>covered</span>
                          </div>
                        ))}
                      </div>
                      <button className="btn sm mt8" onClick={() => exportCompliance(c.id)}><Icon name="download" size={11} /> Evidence map</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-stack">
          <div className="panel" style={{ borderColor: integrations?.ready ? "rgba(110,231,168,.32)" : "rgba(255,122,111,.28)" }}>
            <div className="panel-head"><h3>Production wiring</h3><span className="sub">{live ? "on-site API" : "static reference"}</span></div>
            <div className="panel-body">
              <div className="row between">
                <span className="small muted">Ready</span>
                <span className={`chip ${integrations?.ready ? "green" : "red"}`} style={{ fontSize: 11 }}>{integrations?.ready ? "yes" : "not yet"}</span>
              </div>
              <div className="divider" />
              <div className="row between"><span className="xsmall muted">Agent runtime</span><span className="xsmall mono">{integrations?.agent?.configured ? `${integrations.agent.backend} · ${integrations.agent.model}` : "unconfigured"}</span></div>
              <div className="row between mt8"><span className="xsmall muted">NPU / inference</span><span className="xsmall mono">{integrations?.npu?.ready ? `${integrations.npu.backend} · ${integrations.npu.device}` : integrations?.npu?.backend ?? "not attached"}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Live connectors</span><span className="xsmall mono">{integrations?.connectors?.live ?? 0} / {integrations?.connectors?.total ?? pack.connectors.length}</span></div>
              <div className="row between mt8"><span className="xsmall muted">Simulated connectors</span><span className="xsmall mono">{integrations?.connectors?.simulated ?? "—"}</span></div>
              <div className="divider" />
              <p className="xsmall soft" style={{ lineHeight: 1.5 }}>
                {live
                  ? integrations?.ready
                    ? "The runtime is wired: JiuwenSwarm, an inference backend and live plant connectors are configured."
                    : "The API is running, but the agent model, inference broker or live plant connectors are not all configured. Set them in the on-site environment; the API stays explicit about what is missing."
                  : "This static build has no plant API. The production runtime is in the repository; connect it to the on-site API to enable JiuwenSwarm, ONNX/Ascend inference and live connectors."}
              </p>
              <Link className="btn sm mt8" to="/connectors">Open connector wiring <Icon name="arrow" size={11} /></Link>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Subscription</h3><span className="sub">{pack.billing.plan}</span></div>
            <div className="panel-body">
              <div className="row between" style={{ padding: "5px 0" }}><span className="small muted">Per line / month</span><span className="small mono">{eur(pack.billing.per_line_month_eur)}</span></div>
              <div className="row between" style={{ padding: "5px 0" }}><span className="small muted">Proactive add-on / line</span><span className="small mono">{eur(pack.billing.proactive_per_line_eur ?? 0)}</span></div>
              <div className="row between" style={{ padding: "5px 0" }}><span className="small muted">Lines</span><span className="small mono">{pack.billing.lines}</span></div>
              <div className="row between" style={{ padding: "5px 0" }}><span className="small muted">Setup + integration</span><span className="small mono">{eur(pack.billing.setup_fee_eur)}</span></div>
              <div className="divider" />
              <div className="row between">
                <div>
                  <div className="small" style={{ color: "var(--ink-2)" }}>On-site NPU option</div>
                  <div className="xsmall soft">{eur(pack.billing.npu_option_eur)} / month · hardware with margin</div>
                </div>
                <button className={`switch ${npu ? "on" : ""}`} onClick={() => { setNpu((v) => !v); say(npu ? "NPU option removed" : "NPU option added"); }} aria-label="NPU option" />
              </div>
              <div className="divider" />
              <div className="row between">
                <span className="strong">Monthly recurring</span>
                <span className="mono strong">{eur(pack.billing.lines * pack.billing.per_line_month_eur + pack.billing.lines * (pack.billing.proactive_per_line_eur ?? 0) + (npu ? pack.billing.npu_option_eur : 0))}</span>
              </div>
              <div className="mt12">
                <div className="xsmall soft mb8" style={{ letterSpacing: ".12em", textTransform: "uppercase" }}>Invoices</div>
                {pack.billing.invoices.map((inv) => (
                  <div key={inv.id} className="row between" style={{ padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,.05)" }}>
                    <span className="xsmall mono muted">{inv.id}</span>
                    <span className="xsmall soft">{fmtDate(inv.date)}</span>
                    <span className="xsmall mono">{eur(inv.amount)}</span>
                    <span className="chip green" style={{ fontSize: 11 }}>{inv.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Cross-factory sharing</h3><span className="sub">off by default</span></div>
            <div className="panel-body">
              <div className="row between">
                <div>
                  <div className="small" style={{ color: "var(--ink-2)" }}>Anonymised pattern sharing</div>
                  <div className="xsmall soft">cause labels + factor ranges only</div>
                </div>
                <button className={`switch ${sharing ? "on" : ""}`} onClick={toggleSharing} aria-label="Cross-factory sharing" />
              </div>
              <div className="divider" />
              <p className="xsmall muted" style={{ lineHeight: 1.55 }}>{pack.sharing.note}</p>
              <div className="mt12" style={{ background: "#0c0e11", border: "1px solid var(--line)", borderRadius: 6, padding: 9 }}>
                <div className="xsmall soft mb8">Anonymised record preview</div>
                <pre className="mono xsmall" style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
{`{
  "process": "casting",
  "cause": "gas porosity",
  "factors": { "deviation": 0.18, "batch": 0.88 },
  "time_to_cause_h": 3.2,
  "factory": "anonymous"
}`}
                </pre>
              </div>
              <div className="row between mt8">
                <span className="xsmall soft">Factories</span>
                <span className="xsmall mono">{pack.sharing.factories}</span>
              </div>
              <div className="row between mt8">
                <span className="xsmall soft">Images / batches / serials shared</span>
                <span className="xsmall mono green">none</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Phase 3 controls</h3><span className="sub">architecture, not a promise</span></div>
            <div className="panel-body col gap8">
              <div className="row between"><span className="small muted">Multi-factory deployment</span><span className="chip amber" style={{ fontSize: 11 }}>ready for 2nd site</span></div>
              <div className="row between"><span className="small muted">Managed NPU server</span><span className="chip amber" style={{ fontSize: 11 }}>available</span></div>
              <div className="row between"><span className="small muted">Multi-tenant isolation</span><span className="chip" style={{ fontSize: 11 }}>phase 3</span></div>
              <div className="row between"><span className="small muted">IATF 16949 pack</span><span className="chip amber" style={{ fontSize: 11 }}>in progress</span></div>
              <div className="row between"><span className="small muted">FDA 21 CFR Part 11</span><span className="chip" style={{ fontSize: 11 }}>planned</span></div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Security & retention</h3><span className="sub">on-site</span></div>
            <div className="panel-body col gap6">
              <div className="row between"><span className="xsmall muted">Case store</span><span className="xsmall mono">local SQLite</span></div>
              <div className="row between"><span className="xsmall muted">Audit trail</span><span className="xsmall mono">append-only triggers</span></div>
              <div className="row between"><span className="xsmall muted">Retention</span><span className="xsmall mono">7 years</span></div>
              <div className="row between"><span className="xsmall muted">Outbound network</span><span className="xsmall mono green">none after setup</span></div>
              <p className="xsmall soft mt8">No factory data leaves the site. Cloud GPU inference is explicitly out of scope.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
