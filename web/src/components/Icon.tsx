import type { SVGProps } from "react";

const paths: Record<string, string> = {
  stage: "M3 5h18v11H3zM8 21h8M12 16v5M7 10l2.5 2.5L14 8l3 3",
  booth: "M4 3h16v18H4zM8 7h8M8 11h8M8 15h5",
  cases: "M4 6h16v14H4zM8 3h8v3M8 11h8M8 15h5",
  dashboard: "M3 3h7v8H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 15h7v6H3z",
  review: "M5 3h14v18l-7-4-7 4zM9 9l2 2 4-4",
  report: "M6 2h9l4 4v16H6zM15 2v5h4M9 12h7M9 16h7M9 8h2",
  connectors: "M9 3v5M15 3v5M7 8h10v4a5 5 0 0 1-10 0zM12 17v4",
  admin: "M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7zM9 12l2 2 4-4",
  about: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 7.5v.5",
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3",
  arrow: "M5 12h14M13 6l6 6-6 6",
  arrowRight: "M5 12h13M12 5l7 7-7 7",
  check: "M4 12l5 5L20 6",
  x: "M6 6l12 12M18 6L6 18",
  plus: "M12 5v14M5 12h14",
  play: "M7 4l13 8-13 8z",
  reset: "M3 12a9 9 0 1 0 3-6.7M3 4v5h5",
  download: "M12 3v12M7 10l5 5 5-5M4 21h16",
  camera: "M4 7h4l2-3h4l2 3h4v13H4zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  chevron: "M9 6l6 6-6 6",
  chevronDown: "M6 9l6 6 6-6",
  activity: "M3 12h4l3-8 4 16 3-8h4",
  cpu: "M7 7h10v10H7zM9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4",
  shield: "M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z",
  bolt: "M13 2L4 14h7l-1 8 9-12h-7z",
  chart: "M4 20V4M4 20h16M8 16v-5M13 16V7M18 16v-8",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
  alert: "M12 3l10 18H2zM12 9v5M12 17.5v.5",
  file: "M6 2h9l4 4v16H6zM15 2v5h4M9 12h7M9 16h7",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c0-4 3.6-6 8-6s8 2 8 6",
  external: "M14 4h6v6M20 4L10 14M18 14v6H4V6h6",
  lock: "M6 10h12v11H6zM9 10V7a3 3 0 0 1 6 0v3M12 14v3",
  grid: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
  factory: "M3 21V9l5 3V9l5 3V4h5v17zM7 17h1M12 17h1M17 17h1",
  target: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
  filter: "M3 5h18M6 12h12M10 19h4",
  menu: "M3 6h18M3 12h18M3 18h18",
  spark: "M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8zM19 16l.9 3.1L23 20l-3.1.9L19 24l-.9-3.1L15 20l3.1-.9z",
  zoom: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3M8 11h6M11 8v6",
  refresh: "M20 11a8 8 0 1 0-2.3 6.2M20 4v7h-7",
  link: "M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1",
  mail: "M3 5h18v14H3zM3 6l9 7 9-7",
  calendar: "M4 5h16v16H4zM8 3v4M16 3v4M4 10h16",
  therm: "M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z",
  gauge: "M4 18a8 8 0 1 1 16 0M12 14l4-4",
};

export function Icon({ name, size = 16, ...rest }: { name: string; size?: number } & SVGProps<SVGSVGElement>) {
  const d = paths[name] ?? paths.about;
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      <path d={d} />
    </svg>
  );
}
