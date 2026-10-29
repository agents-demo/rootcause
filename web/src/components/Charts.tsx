import { useMemo, useRef, useState } from "react";

interface Series {
  name: string;
  color: string;
  values: number[];
  dashed?: boolean;
  dots?: boolean;
}

interface LineChartProps {
  series: Series[];
  labels?: string[];
  height?: number;
  yMin?: number;
  yMax?: number;
  unit?: string;
  area?: boolean;
  dots?: boolean;
  decimals?: number;
  refLow?: number | null;
  refHigh?: number | null;
  labelLast?: boolean;
  table?: boolean;
  tableLabel?: string;
}

export function LineChart({
  series,
  labels = [],
  height = 180,
  yMin,
  yMax,
  unit = "",
  area = false,
  dots = false,
  decimals = 1,
  refLow = null,
  refHigh = null,
  labelLast = false,
  table = true,
  tableLabel = "Data table",
}: LineChartProps) {
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const width = 620;
  const pad = { l: 38, r: 10, t: 10, b: 22 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  const all = series.flatMap((s) => s.values);
  if (refLow !== null) all.push(refLow);
  if (refHigh !== null) all.push(refHigh);
  const min = yMin ?? Math.min(...all);
  const max = yMax ?? Math.max(...all);
  const span = max - min || 1;
  const n = Math.max(...series.map((s) => s.values.length), 1);

  const xOf = (i: number) => pad.l + (i / Math.max(1, n - 1)) * innerW;
  const yOf = (v: number) => pad.t + innerH - ((v - min) / span) * innerH;

  const paths = useMemo(
    () =>
      series.map((s) => {
        const d = s.values
          .map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`)
          .join(" ");
        const areaD = `${d} L${xOf(s.values.length - 1).toFixed(1)},${(pad.t + innerH).toFixed(1)} L${xOf(0).toFixed(1)},${(pad.t + innerH).toFixed(1)} Z`;
        return { ...s, d, areaD };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [series, height, min, max, n],
  );

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => min + span * f);

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.clientX - rect.left) / rect.width) * width;
    const i = Math.round(((x - pad.l) / innerW) * (n - 1));
    setHover(Math.max(0, Math.min(n - 1, i)));
  }

  return (
    <div style={{ position: "relative" }}>
      <svg
        ref={ref}
        viewBox={`0 0 ${width} ${height}`}
        className="chart"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        role="img"
        aria-label={`Chart: ${series.map((s) => s.name).join(", ")}`}
      >
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={pad.l} x2={width - pad.r} y1={yOf(t)} y2={yOf(t)} className="gridline" />
            <text x={pad.l - 6} y={yOf(t) + 3} textAnchor="end" className="axis">
              {t.toFixed(decimals)}
            </text>
          </g>
        ))}
        {labels.map((l, i) =>
          i % Math.ceil(labels.length / 7) === 0 ? (
            <text key={i} x={xOf(i)} y={height - 6} textAnchor="middle" className="axis">
              {l}
            </text>
          ) : null,
        )}
        {paths.map((s) => (
          <g key={s.name}>
            {area && <path d={s.areaD} fill={s.color} className="area" />}
            <path
              d={s.d}
              className="series"
              stroke={s.color}
              strokeDasharray={s.dashed ? "4 4" : undefined}
            />
            {dots &&
              s.values.map((v, i) => (
                <circle key={i} cx={xOf(i)} cy={yOf(v)} r={1.9} fill={s.color} className="dot" />
              ))}
            {labelLast && s.values.length > 0 && (
              <text
                x={xOf(s.values.length - 1) - 3}
                y={yOf(s.values[s.values.length - 1]) - 5}
                textAnchor="end"
                style={{ fill: s.color, font: "9.5px var(--font-mono)" }}
              >
                {s.name}
              </text>
            )}
          </g>
        ))}
        {([
          ["low", refLow],
          ["high", refHigh],
        ] as const).map(([kind, val]) =>
          val !== null ? (
            <g key={kind}>
              <line
                x1={pad.l}
                x2={width - pad.r}
                y1={yOf(val)}
                y2={yOf(val)}
                stroke="rgba(248,113,113,.45)"
                strokeDasharray="3 4"
                strokeWidth={1}
              />
              <text x={width - pad.r - 2} y={yOf(val) - 3} textAnchor="end" className="axis" style={{ fill: "rgba(248,113,113,.7)" }}>
                spec {val}
              </text>
            </g>
          ) : null,
        )}
        {hover !== null && (
          <>
            <line x1={xOf(hover)} x2={xOf(hover)} y1={pad.t} y2={pad.t + innerH} stroke="rgba(255,255,255,.22)" strokeDasharray="3 3" />
            {series.map((s) => (
              <circle key={s.name} cx={xOf(hover)} cy={yOf(s.values[hover] ?? 0)} r={3} fill={s.color} stroke="#0b0c0f" strokeWidth={1.5} />
            ))}
          </>
        )}
      </svg>
      {hover !== null && (
        <div
          className="chart-legend"
          style={{
            position: "absolute",
            left: `${(xOf(hover) / width) * 100}%`,
            top: 4,
            transform: "translateX(-50%)",
            background: "#15181d",
            border: "1px solid rgba(255,255,255,.14)",
            borderRadius: 6,
            padding: "5px 8px",
            pointerEvents: "none",
            flexDirection: "column",
            gap: 2,
            zIndex: 2,
            whiteSpace: "nowrap",
          }}
        >
          <span className="soft xsmall">{labels[hover] ?? `#${hover + 1}`}</span>
          {series.map((s) => (
            <span key={s.name} style={{ color: s.color }}>
              <i style={{ background: s.color }} /> {s.name}: {(s.values[hover] ?? 0).toFixed(decimals)}
              {unit}
            </span>
          ))}
        </div>
      )}
      {table && (
        <details className="chart-data">
          <summary>{tableLabel}</summary>
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr><th>Point</th>{series.map((s) => <th key={s.name}>{s.name}</th>)}</tr>
              </thead>
              <tbody>
                {(labels.length ? labels : series[0]?.values.map((_, i) => String(i + 1)) ?? []).map((label, i) => (
                  <tr key={`${label}-${i}`}>
                    <td>{label}</td>
                    {series.map((s) => <td key={s.name}>{(s.values[i] ?? 0).toFixed(decimals)}{unit}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}

export function Sparkline({
  values,
  color = "#ffb454",
  height = 34,
  width = 120,
}: {
  values: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (!values.length) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const points = values.map((v, i) => {
    const x = (i / Math.max(1, values.length - 1)) * width;
    const y = height - 3 - ((v - min) / span) * (height - 6);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height} className="chart" aria-hidden="true">
      <polyline points={points.join(" ")} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export function BarList({
  items,
  color = "#ffb454",
  suffix = "",
  max,
}: {
  items: { label: string; value: number; sub?: string }[];
  color?: string;
  suffix?: string;
  max?: number;
}) {
  const top = max ?? Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="col gap8">
      {items.map((item) => (
        <div key={item.label}>
          <div className="row between" style={{ fontSize: 11.5 }}>
            <span style={{ color: "var(--ink-2)" }}>{item.label}</span>
            <span className="mono muted">
              {item.value}
              {suffix}
              {item.sub ? <span className="soft"> · {item.sub}</span> : null}
            </span>
          </div>
          <div className="meter mt8" style={{ height: 4 }}>
            <i style={{ width: `${(item.value / top) * 100}%`, background: color }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Donut({ value, size = 56, color = "#ffb454", label }: { value: number; size?: number; color?: string; label?: string }) {
  const r = size / 2 - 4;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: "relative", width: size, height: size, flex: "none" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#23272e" strokeWidth={4} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={4}
          strokeDasharray={`${c * value} ${c}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", fontSize: 11, fontFamily: "var(--mono)", color: "var(--ink-2)" }}>
        {label ?? `${Math.round(value * 100)}%`}
      </div>
    </div>
  );
}
