import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";

export default function NewCase() {
  const { pack, addOwnCase, setDataMode, say } = useStore();
  const navigate = useNavigate();
  const [defect, setDefect] = useState("");
  const [part, setPart] = useState("");
  const [lineId, setLineId] = useState(pack?.lines[0]?.id ?? "line-6");
  const [batchId, setBatchId] = useState("");
  const [severity, setSeverity] = useState<"low" | "medium" | "high" | "critical">("high");
  const [station, setStation] = useState("");
  const [shift, setShift] = useState("B");
  const [description, setDescription] = useState("");
  const [cause, setCause] = useState("");
  const [error, setError] = useState("");

  const valid = defect.trim() && part.trim() && description.trim();

  function submit() {
    if (!valid) {
      setError("Defect, part and what you observed are required.");
      return;
    }
    setError("");
    const id = addOwnCase({ defect, part, lineId, batchId, severity, station, shift, description, cause });
    setDataMode("own");
    say(`Case ${id} created in my workspace`);
    navigate(`/cases/${id}`);
  }

  return (
    <div>
      <PageHead
        kicker="My workspace · new case"
        title="Start from what happened."
        subtitle="Enter a real case from your line. You can rank a working cause, reject it, draft the report and sign it. No machine or batch record is attached yet."
        actions={<Link className="btn sm" to="/"><Icon name="arrow" size={12} /> Back to my cases</Link>}
      />

      <div className="panel">
        <div className="panel-body">
          <div className="newcase-grid">
            <div className="field">
              <label htmlFor="nc-defect">Defect</label>
              <input id="nc-defect" className="input" value={defect} onChange={(e) => setDefect(e.target.value)} placeholder="e.g. Fracture at root fillet" />
            </div>
            <div className="field">
              <label htmlFor="nc-part">Part</label>
              <input id="nc-part" className="input" value={part} onChange={(e) => setPart(e.target.value)} placeholder="e.g. Turbine bracket, cast AlSi7Mg" />
            </div>
            <div className="field">
              <label htmlFor="nc-line">Line</label>
              <select id="nc-line" className="select" value={lineId} onChange={(e) => setLineId(e.target.value)}>
                {(pack?.lines ?? []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="nc-batch">Batch / lot (optional)</label>
              <input id="nc-batch" className="input" value={batchId} onChange={(e) => setBatchId(e.target.value)} placeholder="e.g. B-2291" />
            </div>
            <div className="field">
              <label htmlFor="nc-severity">Severity</label>
              <select id="nc-severity" className="select" value={severity} onChange={(e) => setSeverity(e.target.value as typeof severity)}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="nc-station">Station (optional)</label>
              <input id="nc-station" className="input" value={station} onChange={(e) => setStation(e.target.value)} placeholder="e.g. Final inspection" />
            </div>
            <div className="field">
              <label htmlFor="nc-shift">Shift</label>
              <select id="nc-shift" className="select" value={shift} onChange={(e) => setShift(e.target.value)}>
                <option value="A">Shift A</option>
                <option value="B">Shift B</option>
                <option value="C">Shift C</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="nc-cause">Working cause (optional)</label>
              <input id="nc-cause" className="input" value={cause} onChange={(e) => setCause(e.target.value)} placeholder="e.g. Gas porosity in the casting" />
            </div>
            <div className="field newcase-wide">
              <label htmlFor="nc-desc">What did you observe?</label>
              <textarea
                id="nc-desc"
                className="textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="The crack starts below the surface. The machine log was not pulled yet. The batch was accepted on a hydrogen exception."
                rows={5}
              />
            </div>
          </div>

          {error && <div className="xsmall" style={{ color: "var(--risk)", marginTop: 10 }}>{error}</div>}

          <div className="row between mt16" style={{ flexWrap: "wrap", gap: 10 }}>
            <span className="xsmall soft">
              Stored in this browser. No synthetic records, no plant connection.
            </span>
            <div className="row gap8">
              <Link className="btn ghost" to="/">Cancel</Link>
              <button className="btn primary" onClick={submit} disabled={!valid}>
                <Icon name="plus" size={12} /> Create case
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>What you get</h3><span className="sub">same flow, your data</span></div>
        <div className="panel-body">
          <ul className="proof-list">
            <li>A case with the evidence note you wrote, a working cause, and a draft report.</li>
            <li>Reject the cause or add another; the reason is stored in the audit trail.</li>
            <li>Accept a cause, sign the report, then download the case JSON.</li>
            <li>Switch to the reference workspace at any time to see the sensor, batch and proactive flows.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
