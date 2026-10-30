import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { eur, pct } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead } from "../components/UI";

export default function Proof() {
  const { pack, audits } = useStore();
  const data = pack?.dashboard;
  if (!data) return <div className="empty">Loading the proof sheet…</div>;

  const speedup = data.baseline_hours_to_cause / data.median_hours_to_cause;
  const prevented = data.scrap_prevented_eur + data.rework_prevented_eur;
  const signed = audits().filter((a) => a.action === "case.approved" || a.action === "report.approved").length;
  const shiftCase = pack.scenarios[0]?.case.id ?? "RC-0417";

  return (
    <div className="proof-page">
      <PageHead
        kicker="Manager proof · reference pack"
        title="The manager proof."
        subtitle="Baseline days to hours. The engineer still signs. One page to take into the pilot review, with the numbers the quality manager is accountable for."
        actions={
          <>
            <button className="btn sm" onClick={() => window.print()}><Icon name="download" size={12} /> Print / PDF</button>
            <Link className="btn sm" to="/dashboard"><Icon name="chart" size={12} /> Weekly dashboard</Link>
          </>
        }
      />

      <div className="proof-band">
        <div className="proof-metric">
          <div className="label">Time to cause</div>
          <div className="value">{data.baseline_hours_to_cause}h <span>→</span> {data.median_hours_to_cause}h</div>
          <div className="note">{speedup.toFixed(1)}× faster than the recorded baseline</div>
        </div>
        <div className="proof-metric">
          <div className="label">First-cause acceptance</div>
          <div className="value">{pct(data.cause_accuracy)}</div>
          <div className="note">engineer-accepted, not model confidence</div>
        </div>
        <div className="proof-metric">
          <div className="label">Scrap + rework prevented</div>
          <div className="value">{eur(prevented)}</div>
          <div className="note">pack estimate, not a finance-approved figure</div>
        </div>
        <div className="proof-metric">
          <div className="label">Engineer hours saved</div>
          <div className="value">{data.engineer_hours_saved}h</div>
          <div className="note">{signed} signed sign-off events in this store</div>
        </div>
      </div>

      <div className="proof-quote">
        <span className="page-kicker">The sentence to remember</span>
        <blockquote>“From {data.baseline_hours_to_cause} hours to {data.median_hours_to_cause} hours; the engineer still signs.”</blockquote>
        <p>
          Reference pack measurement. The pilot target is three days to 90 minutes on the customer's own baseline —
          set with them, measured weekly, not assumed here.
        </p>
      </div>

      <div className="grid g2">
        <div className="panel">
          <div className="panel-head"><h3>What changes for the quality manager</h3><span className="sub">daily return</span></div>
          <div className="panel-body">
            <ul className="proof-list">
              <li><b>Fewer repeated causes.</b> A rejected cause is stored with the reason and re-ranks the next case.</li>
              <li><b>Faster reports.</b> The report is drafted from the same evidence the engineer just reviewed.</li>
              <li><b>Fewer escalations.</b> The shift brief names the open watches before the defect, not after.</li>
              <li><b>Audit-ready evidence.</b> Evidence, corrections, versions and approval are append-only.</li>
            </ul>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head"><h3>How to read these numbers</h3><span className="sub">honest labels</span></div>
          <div className="panel-body">
            <ul className="proof-list">
              <li>The baseline is the recorded pre-pilot median on the same lines, not a modelled comparison.</li>
              <li>Acceptance means an engineer accepted the first ranked cause. The model does not grade itself.</li>
              <li>Scrap and rework use the pack's unit-cost assumptions. Replace them with plant finance values before external use.</li>
              <li>This page runs on the synthetic reference pack (seed {pack.meta.seed}). A pilot replaces every number with measured data.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="panel mt16">
        <div className="panel-head"><h3>Buyer and next step</h3><span className="sub">one line, one defect type</span></div>
        <div className="panel-body">
          <p className="small" style={{ color: "var(--ink-2)", lineHeight: 1.6 }}>
            The buyer is the plant quality manager, with the plant manager signing the pilot. Start with one line and
            one defect type for 90 days. Success is engineer-accepted causes, time to cause, report sign-off time and
            prevented scrap — reviewed weekly against the baseline.
          </p>
          <div className="row gap8 mt12" style={{ flexWrap: "wrap" }}>
            <Link className="btn primary" to={`/cases/${shiftCase}`}><Icon name="cases" size={12} /> Open the pilot case</Link>
            <Link className="btn" to="/cut"><Icon name="play" size={12} /> Run the 10-minute cut</Link>
            <Link className="btn ghost" to="/dashboard"><Icon name="chart" size={12} /> See the weekly series</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
