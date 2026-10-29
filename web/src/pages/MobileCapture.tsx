import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";

export default function MobileCapture() {
  const { pack, say } = useStore();
  const [scenarioId, setScenarioId] = useState("bracket");
  const [preview, setPreview] = useState<string | null>(null);
  const [state, setState] = useState<"idle" | "scanning" | "done">("idle");
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const scenario = pack?.scenarios.find((s) => s.id === scenarioId) ?? pack?.scenarios[0];
  if (!scenario || !pack) return <div className="empty">Loading…</div>;

  function runPreview(url: string | null) {
    if (url) setPreview(url);
    setState("scanning");
    setProgress(0);
    let p = 0;
    const t = window.setInterval(() => {
      p += 18;
      setProgress(Math.min(100, p));
      if (p >= 100) {
        window.clearInterval(t);
        setState("done");
        say("Defect detected on site — image not retained");
      }
    }, 130);
  }

  function onFile(file?: File | null) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    runPreview(url);
  }

  return (
    <div>
      <PageHead
        kicker="Mobile · field capture"
        title="Photograph the defect. Start the investigation."
        subtitle="A supervisor on the line points a phone at the part. The image is checked on site, the case is opened with the machine window already attached, and the engineer gets it in the review queue."
        actions={<span className="chip green"><Icon name="lock" size={11} /> On-site inference</span>}
      />

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", alignItems: "start" }}>
        <div className="panel">
          <div className="panel-head"><h3>Capture</h3><span className="sub">camera or file</span></div>
          <div className="panel-body">
            <div
              style={{
                border: "1px dashed rgba(255,255,255,.2)",
                borderRadius: 10,
                minHeight: 300,
                display: "grid",
                placeItems: "center",
                position: "relative",
                overflow: "hidden",
                background: "#0b0d10",
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); onFile(e.dataTransfer.files?.[0]); }}
            >
              {preview ? (
                <img src={preview} alt="Captured defect" style={{ width: "100%", height: "100%", objectFit: "cover", position: "absolute", inset: 0 }} />
              ) : (
                <div className="center" style={{ padding: 24 }}>
                  <div style={{ fontSize: 30, opacity: 0.35 }}><Icon name="camera" size={34} /></div>
                  <div className="small mt8" style={{ color: "var(--ink-2)" }}>Take a photo or drop an image</div>
                  <div className="xsmall soft mt8">The image is processed on the site NPU and not retained by the demo.</div>
                  <button className="btn primary mt12" onClick={() => inputRef.current?.click()}><Icon name="camera" size={13} /> Use camera</button>
                  <input ref={inputRef} type="file" accept="image/*" capture="environment" style={{ display: "none" }} onChange={(e) => onFile(e.target.files?.[0])} />
                </div>
              )}
              {state === "done" && (
                <div className="bbox" data-label={`${scenario.defect} · ${(scenario.case.detection_confidence * 100).toFixed(0)}%`} style={{ left: `${scenario.case.bbox[0]}%`, top: `${scenario.case.bbox[1]}%`, width: `${scenario.case.bbox[2]}%`, height: `${scenario.case.bbox[3]}%` }} />
              )}
            </div>
            {state === "scanning" && (
              <div className="mt12">
                <div className="row between xsmall muted"><span>On-site inference</span><span className="mono">{progress}%</span></div>
                <div className="meter tall mt8"><i style={{ width: `${progress}%` }} /></div>
              </div>
            )}
            {state === "done" && (
              <div className="row gap8 mt12">
                <Link className="btn primary" to={`/cases/${scenario.case.id}`}><Icon name="arrow" size={12} /> Open the investigation</Link>
                <button className="btn" onClick={() => { setPreview(null); setState("idle"); }}>Retake</button>
              </div>
            )}
            <div className="divider" />
            <div className="row between" style={{ flexWrap: "wrap", gap: 8 }}>
              <span className="xsmall soft">No photo handy?</span>
              <div className="row gap4">
                {pack.scenarios.map((s) => (
                  <button
                    key={s.id}
                    className={`chip ${scenarioId === s.id ? "amber" : ""}`}
                    onClick={() => { setScenarioId(s.id); setPreview(`${import.meta.env.BASE_URL}assets/${s.image_keys[0]}.svg`); setState("idle"); }}
                  >
                    {s.id}
                  </button>
                ))}
              </div>
              <button className="btn sm" onClick={() => { setPreview(`${import.meta.env.BASE_URL}assets/${scenario.image_keys[0]}.svg`); runPreview(null); }}>
                Use sample image
              </button>
            </div>
          </div>
        </div>

        <div className="col gap12">
          {state === "done" ? (
            <div className="panel" style={{ borderColor: "rgba(94,234,212,.35)" }}>
              <div className="panel-head"><h3>Case opened</h3><span className="sub">review queue</span></div>
              <div className="panel-body">
                <div className="row between">
                  <span className="chip green"><span className="dot live" /> defect confirmed</span>
                  <span className="xsmall mono soft">38 ms · Ascend 310P</span>
                </div>
                <div className="mt12">
                  <div className="xsmall soft">Case</div>
                  <div className="mono" style={{ fontSize: 18, color: "var(--amber-2)" }}>{scenario.case.id}</div>
                  <div className="small muted mt8">{scenario.case.defect_type} · {scenario.case.part}</div>
                </div>
                <div className="divider" />
                <div className="col gap6">
                  <div className="row between"><span className="xsmall muted">Confidence</span><span className="mono small">{(scenario.case.detection_confidence * 100).toFixed(1)}%</span></div>
                  <div className="row between"><span className="xsmall muted">Machine</span><span className="mono xsmall">{scenario.case.machine_id}</span></div>
                  <div className="row between"><span className="xsmall muted">Batch linked</span><span className="mono xsmall">{scenario.case.batch_id}</span></div>
                  <div className="row between"><span className="xsmall muted">Machine window</span><span className="mono xsmall">6 h attached</span></div>
                  <div className="row between"><span className="xsmall muted">Image retained</span><span className="mono xsmall green">no</span></div>
                </div>
                <Link className="btn primary block mt12" to={`/cases/${scenario.case.id}`}>Review the evidence <Icon name="arrow" size={12} /></Link>
              </div>
            </div>
          ) : (
            <div className="panel">
              <div className="panel-head"><h3>What happens next</h3><span className="sub">the workflow</span></div>
              <div className="panel-body">
                <div className="trace">
                  {[
                    ["Capture", "Photo on the line, no laptop."],
                    ["Detect", "NPU returns the defect and confidence."],
                    ["Join", "Machine window, batch and maintenance attach automatically."],
                    ["Rank", "Causes are ranked with evidence before the engineer looks."],
                    ["Review", "The engineer accepts, rejects or adds a cause."],
                  ].map(([t, d], i) => (
                    <div key={t} className="trace-step done">
                      <div className="trace-ico">{i + 1}</div>
                      <div><div className="tt">{t}</div><div className="td">{d}</div></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-head"><h3>Why this matters</h3><span className="sub">the first touch</span></div>
            <div className="panel-body">
              <p className="small muted" style={{ lineHeight: 1.6 }}>
                The person who sees the defect is usually not the person who investigates it. A photo in the
                first minute, with the machine state already attached, removes the “I'll come back to it”
                gap where evidence goes cold. The engineer still decides.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
