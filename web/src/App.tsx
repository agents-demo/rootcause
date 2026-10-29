import { useEffect } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import { StoreProvider, useStore } from "./lib/store";
import { Shell } from "./components/Shell";
import About from "./pages/About";
import Stage from "./pages/Stage";
import Booth from "./pages/Booth";
import Cases from "./pages/Cases";
import CaseWorkspace from "./pages/CaseWorkspace";
import Review from "./pages/Review";
import Reports from "./pages/Reports";
import Dashboard from "./pages/Dashboard";
import Connectors from "./pages/Connectors";
import Admin from "./pages/Admin";
import MobileCapture from "./pages/MobileCapture";
import Watchlist from "./pages/Watchlist";
import WatchDetail from "./pages/WatchDetail";
import ShiftBriefPage from "./pages/ShiftBrief";
import Alerts from "./pages/Alerts";
import ProactiveDashboard from "./pages/ProactiveDashboard";
import ProactiveBooth from "./pages/ProactiveBooth";
import { Icon } from "./components/Icon";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);
  return null;
}

function BoothRun() {
  const { sid } = useParams();
  const { pack } = useStore();
  const scenario = pack?.scenarios.find((s) => s.id === sid) ?? pack?.scenarios[0];
  if (!scenario) return <div className="empty">Loading…</div>;
  return <Navigate to={`/cases/${scenario.case.id}?booth=1`} replace />;
}

function NotFound() {
  return (
    <div className="empty" style={{ paddingTop: 80 }}>
      <div className="big">404</div>
      <p>That page is not part of the case file.</p>
      <a className="btn mt12" href="#/cases">Back to cases</a>
    </div>
  );
}

function Routed() {
  const location = useLocation();
  const isStage = location.pathname === "/stage";
  const { loading, error } = useStore();

  useEffect(() => {
    const names: Record<string, string> = {
      "/": "RootCause — it wasn't fatigue",
      "/about": "About — RootCause",
      "/stage": "The 90-second teardown — RootCause",
      "/booth": "Functional demo — RootCause",
      "/booth/proactive": "Proactive quality — RootCause",
      "/watchlist": "Risk watchlist — RootCause",
      "/brief": "Shift risk brief — RootCause",
      "/alerts": "Alert center — RootCause",
      "/proactive": "Proactive operations — RootCause",
      "/cases": "Cases — RootCause",
      "/review": "Engineer review — RootCause",
      "/reports": "Quality reports — RootCause",
      "/dashboard": "Pilot dashboard — RootCause",
      "/connectors": "Connectors — RootCause",
      "/admin": "Site administration — RootCause",
      "/capture": "Mobile capture — RootCause",
    };
    document.title = names[location.pathname] ?? "RootCause";
  }, [location.pathname]);

  if (loading) {
    return (
      <div style={{ position: "fixed", inset: 0, display: "grid", placeItems: "center", background: "var(--bg)" }}>
        <div className="center">
          <div className="brand-mark" style={{ margin: "0 auto 12px" }} />
          <div className="mono xsmall soft" style={{ letterSpacing: ".2em" }}>LOADING EVIDENCE PACK</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ position: "fixed", inset: 0, display: "grid", placeItems: "center", background: "var(--bg)", padding: 20 }}>
        <div className="panel" style={{ maxWidth: 440 }}>
          <div className="panel-body">
            <h3 style={{ marginBottom: 6 }}>The demo pack could not load</h3>
            <p className="small muted">{error}</p>
            <p className="xsmall soft mt8">Run <code className="mono">python scripts/build_demo_pack.py</code> to regenerate it.</p>
            <button className="btn mt12" onClick={() => window.location.reload()}><Icon name="refresh" size={12} /> Retry</button>
          </div>
        </div>
      </div>
    );
  }

  if (isStage) {
    return (
      <Routes>
        <Route path="/stage" element={<Stage />} />
      </Routes>
    );
  }

  return (
    <Shell>
      <Routes>
        <Route path="/" element={<About />} />
        <Route path="/about" element={<About />} />
        <Route path="/booth" element={<Booth />} />
        <Route path="/booth/run/:sid" element={<BoothRun />} />
        <Route path="/booth/proactive" element={<ProactiveBooth />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/watch/:watchId" element={<WatchDetail />} />
        <Route path="/brief" element={<ShiftBriefPage />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/proactive" element={<ProactiveDashboard />} />
        <Route path="/cases" element={<Cases />} />
        <Route path="/cases/:caseId" element={<CaseWorkspace />} />
        <Route path="/review" element={<Review />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/connectors" element={<Connectors />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/capture" element={<MobileCapture />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Shell>
  );
}

export default function App() {
  return (
    <HashRouter>
      <StoreProvider>
        <ScrollToTop />
        <Routed />
      </StoreProvider>
    </HashRouter>
  );
}
