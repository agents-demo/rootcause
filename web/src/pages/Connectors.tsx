import { useMemo, useState } from "react";
import { useStore } from "../lib/store";
import { fmtDateTime, timeAgo } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead, StatusBadge } from "../components/UI";

const GROUPS = ["Machine", "Vision", "MES", "Quality", "Maintenance", "SCADA", "PLC", "Integration", "Supplier"];

export default function Connectors() {
  const { pack, say } = useStore();
  const [tests, setTests] = useState<Record<string, "testing" | "ok">>({});
  const [category, setCategory] = useState("all");

  const connectors = useMemo(
    () => (pack?.connectors ?? []).filter((c) => category === "all" || c.category === category),
    [pack, category],
  );

  if (!pack) return <div className="empty">Loading connectors…</div>;

  function test(id: string) {
    setTests((t) => ({ ...t, [id]: "testing" }));
    window.setTimeout(() => {
      setTests((t) => ({ ...t, [id]: "ok" }));
      say("Handshake simulated — no hardware attached to the public demo");
    }, 750);
  }

  return (
    <div>
      <PageHead
        kicker="Phase 1.1 · integration"
        title="The hard part is the connections"
        subtitle="A camera can see a defect in a second. Finding the cause means reading the machine, the material, the maintenance record and the old cases. RootCause ships adapters, a normalisation pipeline and a provenance record for each source."
        actions={
          <>
            <span className="chip green"><span className="dot live" /> 6 sources connected</span>
            <span className="chip amber"><Icon name="cpu" size={11} /> NPU 310P</span>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Sources</div><div className="value">{pack.connectors.length}</div><div className="foot">machine · vision · MES · quality · CMMS</div></div>
        <div className="stat"><div className="label">Live points</div><div className="value">{pack.connectors.reduce((n, c) => n + c.points, 0).toLocaleString()}</div><div className="foot">parameters and records</div></div>
        <div className="stat"><div className="label">Connector library</div><div className="value">{pack.connector_library.length}</div><div className="foot">top MES / SCADA / CMMS systems</div></div>
        <div className="stat"><div className="label">Outbound network</div><div className="value">0</div><div className="foot">required after setup</div></div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.7fr 1fr", alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head">
            <h3>Site connectors</h3>
            <div className="row gap4" style={{ flexWrap: "wrap" }}>
              <button className={`chip ${category === "all" ? "amber" : ""}`} onClick={() => setCategory("all")}>All</button>
              {GROUPS.filter((g) => pack.connectors.some((c) => c.category === g)).map((g) => (
                <button key={g} className={`chip ${category === g ? "amber" : ""}`} onClick={() => setCategory(g)}>{g}</button>
              ))}
            </div>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead><tr><th>Source</th><th>Protocol</th><th>Endpoint</th><th>Points</th><th>Last sync</th><th>Status</th><th /></tr></thead>
              <tbody>
                {connectors.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div className="small" style={{ color: "var(--ink-2)", fontWeight: 600 }}>{c.name}</div>
                      <div className="xsmall soft">{c.detail}</div>
                    </td>
                    <td><span className="tag">{c.protocol}</span></td>
                    <td className="mono xsmall muted" style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }}>{c.endpoint || "—"}</td>
                    <td className="mono small">{c.points || "—"}</td>
                    <td className="xsmall muted nowrap">{c.last_sync ? timeAgo(c.last_sync) : "not paired"}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>
                      <button className="btn sm ghost" onClick={() => test(c.id)} disabled={tests[c.id] === "testing"}>
                        {tests[c.id] === "testing" ? "…" : tests[c.id] === "ok" ? <><Icon name="check" size={11} /> ok</> : "Test"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="row between" style={{ padding: "8px 12px", borderTop: "1px solid var(--line)" }}>
            <span className="xsmall soft">Demo handshakes are simulated. Configure an endpoint to run the adapter against live hardware.</span>
            <span className="xsmall mono soft">phase 1.1 / 2.2</span>
          </div>
        </div>

        <div className="col gap12">
          <div className="panel">
            <div className="panel-head"><h3>On-site NPU</h3><span className="sub">image inference</span></div>
            <div className="panel-body">
              <div className="row between">
                <div>
                  <div className="mono small" style={{ color: "var(--cyan)" }}>Ascend 310P</div>
                  <div className="xsmall soft">npu-broker · 8 TOPS INT8 · 1 card</div>
                </div>
                <span className="dot live" />
              </div>
              <div className="divider" />
              <div className="col gap6">
                <div className="row between"><span className="xsmall muted">Model</span><span className="xsmall mono">rootcause-detector-0.9</span></div>
                <div className="row between"><span className="xsmall muted">Median latency</span><span className="xsmall mono">38 ms</span></div>
                <div className="row between"><span className="xsmall muted">Throughput</span><span className="xsmall mono">24 fps · 4 cameras</span></div>
                <div className="row between"><span className="xsmall muted">Data path</span><span className="xsmall mono green">stays on site</span></div>
                <div className="row between"><span className="xsmall muted">Fallback</span><span className="xsmall mono">CPU detector</span></div>
              </div>
              <div className="meter cyan mt12"><i style={{ width: "62%" }} /></div>
              <div className="xsmall soft mt8">62% of one NPU across four cameras. A second line fits without new hardware.</div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Normalisation</h3><span className="sub">tag map + QC</span></div>
            <div className="panel-body">
              <pre className="mono xsmall" style={{ margin: 0, background: "#0b0d10", border: "1px solid var(--line)", borderRadius: 6, padding: 10, color: "var(--muted)", overflowX: "auto", lineHeight: 1.6 }}>
{`raw:  TAG_01=712.4  TAG_02=bad  TAG_03=58.2
map:  TAG_01→pour_temp  TAG_03→quench_temp
out:  pour_temp=712.4  quench_temp=58.2
drop: TAG_02 (not numeric)  quality=partial`}
              </pre>
              <p className="xsmall soft mt8">Out-of-range values are dropped, never quietly averaged. The connector record keeps the QC counters.</p>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Provenance</h3><span className="sub">per source</span></div>
            <div className="panel-body">
              <p className="xsmall muted" style={{ lineHeight: 1.55 }}>
                Every evidence item names its source and timestamp. When a factory asks “where did this number come from?”, the answer is on the case sheet, not in a chat.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>Connector library</h3><span className="sub">deployment time comes down with every connector</span></div>
        <div className="panel-body grid g4">
          {pack.connector_library.map((c) => (
            <div key={c.id} className="feature">
              <div className="row between">
                <span className="num">{c.phase}</span>
                <span className={`chip ${c.status === "shipped" ? "green" : c.status === "beta" ? "amber" : ""}`} style={{ fontSize: 8 }}>{c.status}</span>
              </div>
              <h3>{c.name}</h3>
              <p>{c.systems}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>Data rights</h3><span className="sub">what we will and will not use</span></div>
        <div className="panel-body grid g3">
          <div className="feature">
            <h3>MVTec AD is non-commercial</h3>
            <p>CC BY-NC-SA 4.0. Internal R&amp;D only. The public demo uses synthetic, in-house images instead.</p>
          </div>
          <div className="feature">
            <h3>Customer images need written permission</h3>
            <p>A pilot NDA is not a demo licence. The provenance sheet stays with every data pack.</p>
          </div>
          <div className="feature">
            <h3>No cloud inference in production</h3>
            <p>The NPU and the case store sit on the factory network. No outbound network is required after setup.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
