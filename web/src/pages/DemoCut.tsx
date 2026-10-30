import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";

const KEY = "rootcause.cut.v1";

const steps = [
  {
    id: "now",
    at: "0:00",
    title: "Open on Now, not a dashboard",
    to: "/",
    say: "Five kinds of decision need a human: watch triage, cause decisions, report drafts, corrective actions and coverage. One queue, one job.",
    proof: "The queue is the daily workspace, not a demo page.",
  },
  {
    id: "case",
    at: "1:30",
    title: "Open the live case",
    to: "/cases/RC-0417",
    say: "A turbine bracket failed at the root fillet. Here is the defect, the machine window, the batch and the evidence — before any AI opinion.",
    proof: "Evidence first, not a chat answer.",
  },
  {
    id: "reject",
    at: "3:30",
    title: "Reject the wrong cause",
    to: "/cases/RC-0417",
    say: "RootCause ranks tool mark first. The engineer knows the crack starts 0.4 mm below the surface. Reject it and give the reason.",
    proof: "Human judgement changes the ranking; the reason is stored.",
  },
  {
    id: "sign",
    at: "5:00",
    title: "Sign the report",
    to: "/reports?case=RC-0417",
    say: "The report is already drafted from the evidence. Review it, sign it, and the next version is recorded.",
    proof: "Report sign-off time is measured, and the signature is the engineer's.",
  },
  {
    id: "brief",
    at: "6:30",
    title: "Show the shift brief",
    to: "/brief",
    say: "This is what the next shift inherits: the open watches, the risk that is still building, and the checks that would prove it false.",
    proof: "Prevention is a named watch, not a promise.",
  },
  {
    id: "watch",
    at: "7:30",
    title: "Open a watch case",
    to: "/watchlist",
    say: "A watch is a hypothesis before a defect: what changed, why now, what to check, and what would make it a false alarm.",
    proof: "The proactive layer is real logic over signals, not a second dashboard.",
  },
  {
    id: "proof",
    at: "8:30",
    title: "Close on the manager proof",
    to: "/proof",
    say: "Baseline days to hours, first-cause acceptance, prevented scrap, engineer hours. One line, one defect type, 90 days.",
    proof: "Reference pack: 51h to 3.6h. Pilot target: three days to 90 minutes.",
  },
];

const stageBeats = [
  ["0:00", "Put the failed bracket on the table. Say nothing."],
  ["0:10", "Now: five decisions, one queue."],
  ["0:20", "Case: the defect and the machine window."],
  ["0:35", "AI proposes tool mark / operator error."],
  ["0:45", "Loupe on the fracture: the crack starts below the surface."],
  ["1:00", "Reject the cause with the reason. The ranking moves."],
  ["1:15", "X-ray, batch hydrogen, the same supplier heat."],
  ["1:25", "Stamp the verdict. The engineer signs."],
  ["1:30", "“Pilot target: three days to 90 minutes. The engineer still signs.”"],
];

function fmt(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function DemoCut() {
  const { reset } = useStore();
  const [left, setLeft] = useState(600);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as string[]) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    if (!running) return;
    const t = window.setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          setRunning(false);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => window.clearInterval(t);
  }, [running]);

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(done));
    } catch {
      /* ignore */
    }
  }, [done]);

  const complete = useMemo(() => steps.filter((s) => done.includes(s.id)).length, [done]);
  const toggle = (id: string) => setDone((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="cut-page">
      <PageHead
        kicker="Presenter runbook · 10 minutes"
        title="The manager cut."
        subtitle="One path through the product: the queue, one real case, a human rejection, a signed report, a watch that prevents the next defect, and the proof. Reset before every run."
        actions={
          <>
            <button className="btn sm" onClick={() => setRunning((v) => !v)}>
              <Icon name={running ? "x" : "play"} size={12} /> {running ? "Pause" : "Start clock"}
            </button>
            <button className="btn sm ghost" onClick={() => { setLeft(600); setRunning(false); }}>Reset clock</button>
          </>
        }
      />

      <div className="cut-timer">
        <div>
          <div className="label">Time remaining</div>
          <div className={`value${left <= 60 ? " low" : ""}`}>{fmt(left)}</div>
        </div>
        <div className="cut-progress">
          <div className="label">{complete} of {steps.length} steps done</div>
          <div className="meter mt8"><i style={{ width: `${(complete / steps.length) * 100}%` }} /></div>
          <div className="xsmall soft mt8">Every step ends with a proof point, not a feature tour.</div>
        </div>
        <button className="btn sm" onClick={() => { setDone([]); reset(); }}><Icon name="reset" size={12} /> Reset the run</button>
      </div>

      <div className="cut-steps">
        {steps.map((step, i) => {
          const isDone = done.includes(step.id);
          return (
            <div key={step.id} className={`cut-step${isDone ? " done" : ""}`}>
              <button
                className={`cut-check${isDone ? " on" : ""}`}
                aria-label={`Mark ${step.title} ${isDone ? "not done" : "done"}`}
                aria-pressed={isDone}
                onClick={() => toggle(step.id)}
              >
                {isDone && <Icon name="check" size={12} />}
              </button>
              <div className="cut-step-body">
                <div className="cut-step-meta"><span className="mono">{step.at}</span><span>step {i + 1}</span></div>
                <h3>{step.title}</h3>
                <p>{step.say}</p>
                <div className="cut-proof"><Icon name="check" size={11} /> {step.proof}</div>
              </div>
              <Link className="btn sm" to={step.to}>Open <Icon name="arrow" size={11} /></Link>
            </div>
          );
        })}
      </div>

      <div className="grid g2 mt16">
        <div className="panel">
          <div className="panel-head"><h3>90-second stage cut</h3><span className="sub">physical bracket</span></div>
          <div className="panel-body">
            <ol className="cut-beats">
              {stageBeats.map(([t, line]) => (
                <li key={t}><span className="mono">{t}</span> {line}</li>
              ))}
            </ol>
          </div>
        </div>
        <div className="panel">
          <div className="panel-head"><h3>Props, reset and fallback</h3><span className="sub">rehearse this</span></div>
          <div className="panel-body">
            <ul className="proof-list">
              <li>Failed bracket, loupe or macro lens, x-ray print, printed case sheet, stamp.</li>
              <li>Reset under five seconds: “Reset the run” clears progress and the reference store.</li>
              <li>Offline fallback: the static build keeps working with the cable unplugged.</li>
              <li>If the model is slow, narrate the evidence; do not wait on a spinner.</li>
              <li>Do not claim the NPU or a live connector unless the screen actually shows it.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
