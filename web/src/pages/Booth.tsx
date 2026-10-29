import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDate, hours, severityRank } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead, ProvenanceBlock, SeverityBadge } from "../components/UI";

export default function Booth() {
  const { pack, investigation } = useStore();
  const navigate = useNavigate();
  if (!pack) return <div className="empty">Loading demo pack…</div>;

  const scenarios = [...pack.scenarios].sort((a, b) => severityRank(b.case.severity) - severityRank(a.case.severity));

  return (
    <div>
      <PageHead
        kicker="Booth · functional demo"
        title="Is this real?"
        subtitle="Same story as the stage piece, with the whole data trail exposed. Pick a scenario and run it in three minutes. Everything is local, deterministic and offline."
        actions={
          <>
            <span className="chip green"><span className="dot live" /> Offline pack</span>
            <span className="chip"><Icon name="lock" size={11} /> No model calls</span>
            <Link className="btn primary" to={`/cases/${scenarios[0]?.case.id}?booth=1`}>
              <Icon name="play" size={13} /> Run the first scenario
            </Link>
          </>
        }
      />

      <div className="grid g4 mb16">
        <div className="stat"><div className="label">Run time</div><div className="value">3:00</div><div className="foot">scenario picker · reset</div></div>
        <div className="stat"><div className="label">Scenarios</div><div className="value">{scenarios.length}</div><div className="foot">casting · moulding · weld · SMT</div></div>
        <div className="stat"><div className="label">Data</div><div className="value">100<small>%</small></div><div className="foot">synthetic · fixed seed</div></div>
        <div className="stat"><div className="label">Network</div><div className="value">0<small> calls</small></div><div className="foot">runs with the cable out</div></div>
      </div>

      <Link to="/booth/proactive" className="panel mb16" style={{ display: "block", borderColor: "rgba(94,234,212,.32)", background: "radial-gradient(70% 140% at 0% 0%, rgba(94,234,212,.07), transparent 60%), rgba(255,255,255,.016)" }}>
        <div className="panel-body" style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{ width: 42, height: 42, borderRadius: 9, border: "1px solid rgba(94,234,212,.4)", display: "grid", placeItems: "center", flex: "none" }}>
            <Icon name="target" size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <div className="xsmall mono cyan" style={{ letterSpacing: ".16em" }}>THE SECOND ACT · 10 MINUTES</div>
            <h3 style={{ fontSize: 19, margin: "4px 0 3px" }}>Catch it before the scrap</h3>
            <p className="small muted">A watch opens before the defect, the evidence is assembled, containment is recommended and a human approves it. Proactive about risk — never in control of the line.</p>
          </div>
          <span className="btn primary">Run the proactive story <Icon name="arrow" size={12} /></span>
        </div>
      </Link>

      <div className="grid g2 mb16" style={{ alignItems: "stretch" }}>
        {scenarios.map((s) => {
          const inv = investigation(s.case.id);
          const top = inv?.hypotheses[0];
          return (
            <div key={s.id} className="panel" style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ position: "relative", aspectRatio: "16 / 7.4", overflow: "hidden", borderBottom: "1px solid var(--line)" }}>
                <img src={`${import.meta.env.BASE_URL}assets/${s.image_keys[0]}.svg`} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, transparent 35%, rgba(8,9,11,.88))" }} />
                <div style={{ position: "absolute", left: 14, bottom: 10, right: 14, display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 10 }}>
                  <div>
                    <div className="xsmall mono amber" style={{ letterSpacing: ".12em" }}>{s.case.id}</div>
                    <div style={{ fontSize: 17, fontWeight: 700 }}>{s.title}</div>
                  </div>
                  <SeverityBadge severity={s.case.severity} />
                </div>
              </div>
              <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
                <div className="row between">
                  <span className="small muted">{s.subtitle}</span>
                  <span className="chip">{s.process}</span>
                </div>
                <div className="grid g3" style={{ gap: 6 }}>
                  <div><div className="xsmall soft">Defect</div><div className="xsmall" style={{ color: "var(--ink-2)" }}>{s.defect}</div></div>
                  <div><div className="xsmall soft">Leading cause</div><div className="xsmall" style={{ color: "var(--amber-2)" }}>{top?.label}</div></div>
                  <div><div className="xsmall soft">Time to cause</div><div className="xsmall" style={{ color: "var(--ink-2)" }}>{hours(s.current_hours)} <span className="soft">/ {hours(s.baseline_hours)} before</span></div></div>
                </div>
                <div className="row between mt8" style={{ marginTop: "auto" }}>
                  <span className="xsmall soft">Batch {s.batch.id} · {s.batch.supplier}</span>
                  <button className="btn sm primary" onClick={() => navigate(`/cases/${s.case.id}?booth=1`)}>
                    <Icon name="play" size={11} /> Run scenario
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid g2">
        <div className="panel">
          <div className="panel-head"><h3>The three-minute run</h3><span className="sub">what to say, in order</span></div>
          <div className="panel-body">
            <div className="trace">
              {[
                ["0:00", "Open the case", "Defect image, bounding box, machine and batch. The part is real; the data is labelled synthetic."],
                ["0:20", "The first answer", "The ranking puts tool mark first. It is plausible. Reject it because the crack starts 0.4 mm below the surface."],
                ["0:50", "The re-rank", "Gas porosity takes the lead. The correction is in the audit trail immediately."],
                ["1:20", "The evidence", "Open the x-ray, the hydrogen chart and batch B-2291. Each cause cites evidence IDs."],
                ["1:50", "The report", "Edit the draft inline, sign it off, export PDF or Word. The engineer name and model version are recorded."],
                ["2:30", "The close", "It wasn't fatigue. It started in the casting. The next case starts in seconds."],
              ].map(([t, title, body], i) => (
                <div key={title} className="trace-step done">
                  <div className="trace-ico">{i + 1}</div>
                  <div>
                    <div className="tt"><span className="mono amber" style={{ marginRight: 7 }}>{t}</span>{title}</div>
                    <div className="td">{body}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col gap12">
          <div className="panel">
            <div className="panel-head"><h3>What is simulated</h3><span className="sub">say it out loud</span></div>
            <div className="panel-body">
              <div className="col gap8">
                <div className="row" style={{ alignItems: "flex-start", gap: 8 }}><span className="dot warn" style={{ marginTop: 5 }} /><div><b className="small">Synthetic data</b><div className="xsmall muted">Images, sensor series, batches and cases are generated in-house with a fixed seed. No customer or MVTec AD data.</div></div></div>
                <div className="row" style={{ alignItems: "flex-start", gap: 8 }}><span className="dot warn" style={{ marginTop: 5 }} /><div><b className="small">Precomputed detection</b><div className="xsmall muted">The bounding box is fixed for the demo. The detector in the repo is real and deterministic; the fine-tuned model is pilot work.</div></div></div>
                <div className="row" style={{ alignItems: "flex-start", gap: 8 }}><span className="dot warn" style={{ marginTop: 5 }} /><div><b className="small">Connectors are simulated</b><div className="xsmall muted">The OPC-UA, Modbus and camera adapters are in the repo. No factory hardware is attached to the public demo.</div></div></div>
                <div className="row" style={{ alignItems: "flex-start", gap: 8 }}><span className="dot live" style={{ marginTop: 5 }} /><div><b className="small">The workflow is real</b><div className="xsmall muted">Evidence-weighted ranking, human rejection, audit trail, report versions and sign-off run exactly as they do in a pilot.</div></div></div>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>Provenance</h3><span className="sub">{fmtDate(pack.meta.generated)}</span></div>
            <div className="panel-body">
              <ProvenanceBlock
                items={{
                  data: pack.meta.note,
                  model: pack.meta.model,
                  seed: String(pack.meta.seed),
                  licence: "MIT · synthetic assets generated in-house",
                }}
                note="The pack is shipped as a single JSON file and loaded with no network. The provenance sheet stays with the data pack."
              />
            </div>
          </div>

          <div className="panel">
            <div className="panel-head"><h3>After the booth</h3><span className="sub">motion</span></div>
            <div className="panel-body col gap8">
              <Link className="row between" to="/dashboard" style={{ fontSize: 12 }}>Quality dashboard <Icon name="arrow" size={12} /></Link>
              <Link className="row between" to="/reports" style={{ fontSize: 12 }}>Reports and exports <Icon name="arrow" size={12} /></Link>
              <Link className="row between" to="/connectors" style={{ fontSize: 12 }}>The connectors that make it real <Icon name="arrow" size={12} /></Link>
              <a className="row between" href="https://github.com/jiuwendemos/rootcause" target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>Repository <Icon name="external" size={12} /></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
