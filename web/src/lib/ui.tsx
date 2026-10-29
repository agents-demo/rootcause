import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

type Theme = "dark" | "light";
type Density = "comfortable" | "compact";
export type Role = "quality_manager" | "engineer" | "operator" | "admin";

interface UISettings {
  theme: Theme;
  density: Density;
  role: Role;
  setTheme: (t: Theme) => void;
  setDensity: (d: Density) => void;
  setRole: (r: Role) => void;
  toggleTheme: () => void;
}

const KEY = "rootcause.ui.v1";
const UI = createContext<UISettings | null>(null);

function load(): { theme: Theme; density: Density; role: Role } {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<UISettings>;
      return {
        theme: parsed.theme === "light" ? "light" : "dark",
        density: parsed.density === "compact" ? "compact" : "comfortable",
        role: (["quality_manager", "engineer", "operator", "admin"] as Role[]).includes(parsed.role as Role)
          ? (parsed.role as Role)
          : "quality_manager",
      };
    }
  } catch {
    /* ignore */
  }
  return { theme: "dark", density: "comfortable", role: "quality_manager" };
}

export function UIProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState(load);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = settings.theme;
    root.dataset.density = settings.density;
    root.style.colorScheme = settings.theme;
    try {
      localStorage.setItem(KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  }, [settings]);

  const setTheme = useCallback((theme: Theme) => setSettings((s) => ({ ...s, theme })), []);
  const setDensity = useCallback((density: Density) => setSettings((s) => ({ ...s, density })), []);
  const setRole = useCallback((role: Role) => setSettings((s) => ({ ...s, role })), []);
  const toggleTheme = useCallback(() => setSettings((s) => ({ ...s, theme: s.theme === "dark" ? "light" : "dark" })), []);

  const value = useMemo(
    () => ({ ...settings, setTheme, setDensity, setRole, toggleTheme }),
    [settings, setTheme, setDensity, setRole, toggleTheme],
  );
  return <UI.Provider value={value}>{children}</UI.Provider>;
}

export function useUI(): UISettings {
  const ctx = useContext(UI);
  if (!ctx) throw new Error("useUI must be used inside UIProvider");
  return ctx;
}

export function navigateWithTransition(navigate: (to: string) => void, to: string) {
  const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const doc = document as Document & { startViewTransition?: (cb: () => void) => void };
  if (!reduced && doc.startViewTransition) {
    doc.startViewTransition(() => navigate(to));
  } else {
    navigate(to);
  }
}
