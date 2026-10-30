import type { CaseAnalysis, CaseAttachment, Evidence, Hypothesis, SignalFinding } from "../types";

interface ParsedCsv {
  name: string;
  header: string[];
  rows: string[][];
}

const UNIT_WORDS: Array<[RegExp, string]> = [
  [/_mbar$/i, "mbar"],
  [/_bar$/i, "bar"],
  [/_ppm$/i, "ppm"],
  [/_c$/i, "°C"],
  [/_s$/i, "s"],
  [/_mm$/i, "mm"],
  [/_pct$/i, "%"],
];

function decodeDataUrl(dataUrl: string): string {
  const base64 = dataUrl.split(",")[1] ?? "";
  const binary = atob(base64);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}

function parseCsv(name: string, text: string): ParsedCsv | null {
  const lines = text.replace(/\r/g, "").split("\n").filter((line) => line.trim());
  if (lines.length < 3) return null;
  const delimiter = (lines[0].match(/;/g)?.length ?? 0) > (lines[0].match(/,/g)?.length ?? 0) ? ";" : ",";
  const header = lines[0].split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, ""));
  const rows = lines.slice(1).map((line) => line.split(delimiter).map((cell) => cell.trim().replace(/^"|"$/g, "")));
  return { name, header, rows };
}

function numeric(rows: string[][], index: number): number[] {
  return rows
    .map((row) => Number(row[index]))
    .filter((value) => Number.isFinite(value));
}

function humanise(header: string): { label: string; unit: string } {
  let unit = "";
  let label = header;
  for (const [pattern, suffix] of UNIT_WORDS) {
    if (pattern.test(label)) {
      unit = suffix;
      label = label.replace(pattern, "");
      break;
    }
  }
  return { label: label.replace(/_/g, " ").replace(/\s+/g, " ").trim(), unit };
}

function mean(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length);
}

function std(values: number[]): number {
  const m = mean(values);
  return Math.sqrt(values.reduce((sum, value) => sum + (value - m) ** 2, 0) / Math.max(1, values.length));
}

function analyseSeries(header: string, values: number[]): SignalFinding | null {
  if (values.length < 5) return null;
  const third = Math.max(1, Math.floor(values.length / 3));
  const from = mean(values.slice(0, third));
  const to = mean(values.slice(-third));
  const changePct = from === 0 ? 0 : (to - from) / Math.abs(from);
  const diffs = values.slice(1).map((value, index) => value - values[index]);
  const up = diffs.filter((diff) => diff > 0).length;
  const down = diffs.filter((diff) => diff < 0).length;
  const monotonic = Math.max(up, down) / Math.max(1, up + down);
  const z = std(values) === 0 ? 0 : (values[values.length - 1] - mean(values)) / std(values);
  const direction = to > from ? "up" : to < from ? "down" : "stable";
  const sustained = Math.abs(changePct) > 0.2 && monotonic > 0.62;
  const verdict = sustained
    ? `sustained ${direction === "up" ? "rise" : "fall"}`
    : Math.abs(z) > 3
      ? "late spike"
      : "within normal variation";
  if (!sustained && Math.abs(z) <= 3) return null;
  const { label, unit } = humanise(header);
  return {
    id: `signal-${header}`,
    label,
    unit,
    from: Math.round(from * 100) / 100,
    to: Math.round(to * 100) / 100,
    change_pct: Math.round(changePct * 1000) / 10,
    direction,
    monotonic: Math.round(monotonic * 100) / 100,
    z: Math.round(z * 10) / 10,
    verdict,
  };
}

export function analyseCase(input: {
  attachments: CaseAttachment[];
  description: string;
  workingCause: string;
}): { analysis: CaseAnalysis; findings: Evidence[]; hypotheses: Hypothesis[] } {
  const signals: SignalFinding[] = [];
  const findings: Evidence[] = [];
  const detected: { hydrogen?: { value: number; limit: number; batch: string } } = {};
  let csvCount = 0;

  for (const file of input.attachments) {
    if (!/csv|text/i.test(file.mime) && !file.name.toLowerCase().endsWith(".csv")) continue;
    const parsed = parseCsv(file.name, decodeDataUrl(file.data_url));
    if (!parsed) continue;
    csvCount += 1;
    parsed.header.forEach((header, index) => {
      if (/time|date|batch|lot|material|supplier|note/i.test(header)) return;
      const values = numeric(parsed.rows, index);
      const signal = analyseSeries(header, values);
      if (signal) signals.push(signal);
      if (/hydrogen/i.test(header) && values.length) {
        const limitCell = parsed.header.findIndex((cell) => /limit/i.test(cell));
        const noteCell = parsed.header.findIndex((cell) => /note/i.test(cell));
        const noteText = parsed.rows[0]?.[noteCell] ?? "";
        const limitText =
          /limit\s*([\d.]+)/i.exec(noteText)?.[1] ??
          /([\d.]+)\s*ppm/i.exec(noteText)?.[1] ??
          /limit\s*([\d.]+)/i.exec(input.description)?.[1];
        const limit = limitCell >= 0 ? Number(parsed.rows[0]?.[limitCell]) : Number(limitText ?? NaN);
        if (Number.isFinite(limit)) {
          detected.hydrogen = { value: values[0], limit, batch: parsed.rows[0]?.[0] ?? "" };
        }
      }
    });
  }

  const hydrogen = detected.hydrogen ?? null;
  const desc = input.description.toLowerCase();
  const cause = input.workingCause.toLowerCase();
  const vacuum = signals.find((signal) => /vacuum/i.test(signal.label));
  const temperatureFall = signals.find((signal) => /temp|quench/i.test(signal.label) && signal.direction === "down");
  const hydrogenExceeded = Boolean(hydrogen && hydrogen.value > hydrogen.limit);
  const porosityEvidence = /porosity|void|hydrogen|gas/i.test(desc) || hydrogenExceeded || Boolean(vacuum);
  const toolEvidence = /ejector|tool|mark/i.test(desc) || /ejector|tool|mark/i.test(cause);
  const quenchEvidence = /quench/i.test(desc) || Boolean(temperatureFall);

  const evidenceIds: string[] = [];
  const pushFinding = (id: string, title: string, detail: string, source: string, strength: number, kind: Evidence["kind"], payload: Record<string, unknown>) => {
    findings.push({ id, kind, title, detail, source, at: new Date().toISOString(), strength, payload });
    evidenceIds.push(id);
  };

  if (vacuum) {
    pushFinding(
      "EV-10",
      `${vacuum.label} ${vacuum.direction === "up" ? "rose" : "fell"} ${Math.abs(vacuum.change_pct)}%`,
      `${vacuum.from}${vacuum.unit ? ` ${vacuum.unit}` : ""} → ${vacuum.to}${vacuum.unit ? ` ${vacuum.unit}` : ""} across the window; ${vacuum.verdict}, monotonic ${vacuum.monotonic}, z ${vacuum.z}.`,
      "Uploaded sensor CSV",
      0.86,
      "chart",
      { signal: vacuum.label, from: vacuum.from, to: vacuum.to, change_pct: vacuum.change_pct, z: vacuum.z },
    );
  }
  if (hydrogen) {
    pushFinding(
      "EV-11",
      `Hydrogen ${hydrogen.value} ppm vs ${hydrogen.limit} limit`,
      `${hydrogen.batch || "Batch"} is ${hydrogenExceeded ? "over" : "within"} the hydrogen limit; the certificate exception is ${hydrogenExceeded ? "the strongest batch signal" : "not a breach"}.`,
      "Uploaded batch record",
      hydrogenExceeded ? 0.9 : 0.4,
      "record",
      { hydrogen_ppm: hydrogen.value, limit: hydrogen.limit },
    );
  }
  if (signals.length) {
    const extra = signals.filter((signal) => signal !== vacuum).slice(0, 2);
    extra.forEach((signal, index) => {
      pushFinding(
        `EV-${12 + index}`,
        `${signal.label} ${signal.direction === "up" ? "rose" : "fell"} ${Math.abs(signal.change_pct)}%`,
        `${signal.from} → ${signal.to}${signal.unit ? ` ${signal.unit}` : ""}; ${signal.verdict}.`,
        "Uploaded sensor CSV",
        0.6,
        "chart",
        { signal: signal.label, change_pct: signal.change_pct },
      );
    });
  }

  const hypotheses: Hypothesis[] = [];
  const clamp = (value: number) => Math.max(0, Math.min(1, value));
  if (porosityEvidence) {
    hypotheses.push({
      id: "gas_porosity",
      label: "Gas porosity from insufficient die venting",
      category: "material",
      summary: [
        hydrogenExceeded ? `Hydrogen ${hydrogen!.value} ppm against a ${hydrogen!.limit} limit.` : "",
        vacuum ? `${vacuum.label} rose ${Math.abs(vacuum.change_pct)}% (${vacuum.from} → ${vacuum.to} ${vacuum.unit}).` : "",
        "Subsurface voids on the crack path; surface marks cannot initiate this crack.",
      ].filter(Boolean).join(" "),
      score: 0,
      confidence: 0,
      rank: 1,
      status: "proposed",
      factors: {
        frequency: 0.55,
        deviation: clamp((Math.abs(vacuum?.z ?? 0) + (hydrogenExceeded ? 3 : 0)) / 8),
        batch_match: hydrogenExceeded ? 0.95 : 0.35,
        similarity: 0.25,
        recurrence: 0.2,
      },
      evidence_ids: evidenceIds,
      note: "Derived from the uploaded sensor window and batch record.",
    });
  }
  if (quenchEvidence) {
    hypotheses.push({
      id: "quench_crack",
      label: "Quench cracking",
      category: "process",
      summary: "A thermal gradient at the fillet can open a crack from an existing void. The quench temperature is the check.",
      score: 0,
      confidence: 0,
      rank: 1,
      status: "proposed",
      factors: { frequency: 0.35, deviation: temperatureFall ? 0.55 : 0.2, batch_match: 0.15, similarity: 0.15, recurrence: 0.1 },
      evidence_ids: evidenceIds,
      note: "A contributing mechanism unless the quench series shows a fall.",
    });
  }
  if (!toolEvidence && porosityEvidence) {
    hypotheses.push({
      id: "tool_mark",
      label: "Tool mark / operator error",
      category: "process",
      summary: "Surface marks are common at the fillet, but a surface-only feature cannot initiate a subsurface crack.",
      score: 0,
      confidence: 0,
      rank: 1,
      status: "proposed",
      factors: { frequency: 0.7, deviation: 0.08, batch_match: 0.05, similarity: 0.1, recurrence: 0.15 },
      evidence_ids: evidenceIds.slice(0, 1),
      note: "Keep as a challenge; the depth finding should reject it.",
    });
  }

  const topLabel = porosityEvidence ? "gas porosity" : quenchEvidence ? "quench cracking" : "the uploaded signal";
  const prevention = porosityEvidence
    ? [
        "Verify die venting and keep cavity vacuum below 180 mbar.",
        "Revalidate hydrogen pick-up after a door-seal change.",
        "Hold the rest of the batch until the hydrogen exception is reviewed.",
      ]
    : quenchEvidence
      ? ["Check the quench bath temperature against the setpoint.", "Check the transfer delay after the quench."]
      : ["Add a sensor window that covers the suspected process step."];
  const falsifiers = porosityEvidence
    ? [
        "A CT without voids on the crack path, or hydrogen below 1.4 ppm, would weaken gas porosity.",
        "A crack origin at the surface with a matching tool mark would support the tool-mark cause.",
      ]
    : ["A second window with the same signal and no defect would weaken the pattern."];

  const summary = signals.length || hydrogen
    ? [
        signals.length ? `${signals.length} signal${signals.length === 1 ? "" : "s"} found in the uploaded data` : "",
        hydrogen ? `hydrogen ${hydrogen.value} ppm vs ${hydrogen.limit}` : "",
        `the evidence ranks ${topLabel} above the initial guess`,
      ].filter(Boolean).join("; ") + "."
    : "No numeric signal was found in the uploaded files. Add a sensor window or batch record to compare.";

  return {
    analysis: {
      summary,
      signals,
      prevention,
      falsifiers,
      csv_count: csvCount,
    },
    findings,
    hypotheses,
  };
}
