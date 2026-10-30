import { useRef, useState } from "react";
import { useStore } from "../lib/store";
import { askLocal } from "../lib/ask";
import type { AskResult } from "../lib/ask";
import type { Scenario, WatchCase } from "../types";
import { Icon } from "./Icon";

export function AskPanel({ scenario, watch }: { scenario?: Scenario; watch?: WatchCase }) {
  const { live, dataMode, proactive, say } = useStore();
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<AskResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [backend, setBackend] = useState("Local evidence engine");
  const controller = useRef<AbortController | null>(null);
  const caseId = watch?.linked_case_id ?? scenario?.case.id;
  const localOnly = dataMode === "own";

  async function ask() {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setAnswer(null);
    controller.current?.abort();
    controller.current = new AbortController();
    if (live && dataMode === "reference") {
      try {
        const res = await fetch(new URL("api/agent/ask", document.baseURI).toString(), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q, case_id: caseId }),
          signal: controller.current.signal,
        });
        if (res.ok) {
          const data = (await res.json()) as { answer: string; citations?: string[]; model?: string; backend?: string };
          setAnswer({ answer: data.answer, citations: data.citations ?? [] });
          setBackend(`${data.backend ?? "jiuwenswarm"} · ${data.model ?? "model"}`);
          setLoading(false);
          return;
        }
        if (res.status === 503) {
          setBackend("Local evidence engine · JiuwenSwarm not configured");
        } else {
          say("Agent runtime error; using the local evidence engine");
          setBackend("Local evidence engine · runtime error");
        }
      } catch (e) {
        if ((e as Error).name === "AbortError") { setLoading(false); return; }
        setBackend("Local evidence engine · offline");
      }
    }
    setAnswer(askLocal(q, { scenario, watch, proactive: proactive ?? undefined, role: "engineer" }));
    setLoading(false);
  }

  return (
    <div className="ask-panel">
      <div className="row between">
        <h3>Ask {watch ? "this watch" : "this case"}</h3>
        <span className="chip" style={{ fontSize: 11 }}>{localOnly ? "Local evidence engine · my workspace" : backend}</span>
      </div>
      <div className="ask-input">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") ask(); }}
          placeholder={watch ? "Why now? What should I check?" : "Why gas porosity? Show the evidence."}
          aria-label="Ask about this case or watch"
        />
        {loading ? (
          <button className="btn" onClick={() => { controller.current?.abort(); setLoading(false); }} aria-label="Cancel answer">Cancel</button>
        ) : (
          <button className="btn primary" onClick={ask}><Icon name="spark" size={12} /> Ask</button>
        )}
      </div>
      {loading && <div className="ask-skeleton" role="status" aria-label="Searching evidence"><i /></div>}
      {answer && (
        <div className="ask-answer-live">
          {answer.answer}
          <div className="mt8">
            {answer.citations.map((c) => <span key={c} className="ask-cite">{c}</span>)}
            {answer.refused && <span className="chip" style={{ fontSize: 11, marginLeft: 6 }}>no evidence / no action</span>}
          </div>
        </div>
      )}
      <p className="xsmall soft mt8">
        {localOnly
          ? "Your case is answered locally. It is not sent to the model or to a plant system."
          : "Answers cite evidence. They never approve a cause or control the line."}
      </p>
    </div>
  );
}
