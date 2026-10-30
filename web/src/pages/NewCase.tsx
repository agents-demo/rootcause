import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../lib/store";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";
import type { CaseAttachment } from "../types";

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
  const [attachments, setAttachments] = useState<CaseAttachment[]>([]);
  const [fileError, setFileError] = useState("");

  async function addFiles(list: FileList | null) {
    if (!list) return;
    setFileError("");
    const next = [...attachments];
    for (const file of Array.from(list)) {
      const image = /^image\/(png|jpeg|webp)$/.test(file.type);
      const csv = file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv");
      if (!image && !csv) {
        setFileError(`${file.name}: use PNG, JPEG, WebP or CSV.`);
        continue;
      }
      if (file.size > 1.5 * 1024 * 1024) {
        setFileError(`${file.name} is larger than 1.5 MB.`);
        continue;
      }
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("read failed"));
        reader.readAsDataURL(file);
      }).catch(() => "");
      if (!dataUrl) {
        setFileError(`${file.name} could not be read.`);
        continue;
      }
      next.push({ id: `att-${Date.now()}-${next.length}`, name: file.name, mime: file.type || (csv ? "text/csv" : "application/octet-stream"), size: file.size, data_url: dataUrl });
    }
    setAttachments(next);
  }

  const valid = defect.trim() && part.trim() && description.trim();

  function submit() {
    if (!valid) {
      setError("Defect, part and what you observed are required.");
      return;
    }
    setError("");
    const id = addOwnCase({ defect, part, lineId, batchId, severity, station, shift, description, cause, attachments });
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
              <label htmlFor="nc-files">Evidence files (optional)</label>
              <input
                id="nc-files"
                className="input"
                type="file"
                multiple
                accept="image/png,image/jpeg,image/webp,text/csv,.csv"
                onChange={(e) => { void addFiles(e.target.files); e.currentTarget.value = ""; }}
              />
              <div className="xsmall soft" style={{ marginTop: 4 }}>PNG, JPEG, WebP or CSV, up to 1.5 MB each. Stored in this browser only.</div>
              {fileError && <div className="xsmall" style={{ color: "var(--risk)", marginTop: 4 }}>{fileError}</div>}
              {attachments.length > 0 && (
                <div className="attach-list">
                  {attachments.map((a) => (
                    <span key={a.id} className="attach-chip">
                      <Icon name={a.mime.startsWith("image/") ? "camera" : "file"} size={11} />
                      <span>{a.name}</span>
                      <button type="button" aria-label={`Remove ${a.name}`} onClick={() => setAttachments((prev) => prev.filter((x) => x.id !== a.id))}>
                        <Icon name="x" size={10} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
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
            <li>A case with the evidence note you wrote, any uploaded image or CSV, a working cause, and a draft report.</li>
            <li>Reject the cause or add another; the reason is stored in the audit trail.</li>
            <li>Accept a cause, sign the report, then download the case JSON.</li>
            <li>Switch to the reference workspace at any time to see the sensor, batch and proactive flows.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
