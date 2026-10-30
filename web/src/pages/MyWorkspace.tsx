import { Link } from "react-router-dom";
import { useStore } from "../lib/store";
import { fmtDateTime } from "../lib/engine";
import { Icon } from "../components/Icon";
import { PageHead, StatusBadge } from "../components/UI";

export default function MyWorkspace() {
  const { pack, caseStatus, setDataMode } = useStore();
  const cases = pack?.scenarios ?? [];
  const open = cases.filter((s) => caseStatus(s.case.id) !== "approved").length;
  const awaiting = cases.filter((s) => caseStatus(s.case.id) === "awaiting_review").length;
  const approved = cases.filter((s) => caseStatus(s.case.id) === "approved").length;

  return (
    <div>
      <PageHead
        kicker="My workspace · stored in this browser"
        title="My cases."
        subtitle="Blank on purpose. Add a case you actually have, attach what you know, and use the same evidence, review and report flow. Nothing here is synthetic."
        actions={
          <>
            <Link className="btn primary sm" to="/cases/new"><Icon name="plus" size={12} /> New case</Link>
            <button className="btn sm" onClick={() => setDataMode("reference")}><Icon name="grid" size={12} /> Reference data</button>
          </>
        }
      />

      {cases.length === 0 ? (
        <div className="own-empty">
          <div className="own-empty-mark"><Icon name="cases" size={26} /></div>
          <h2>No cases yet.</h2>
          <p>
            This is your workspace, not the demo. Create a case from something that happened on your line: a defect,
            a part, a batch, and what you already know. You can add causes, reject them, write the report and sign it.
          </p>
          <div className="row gap8" style={{ flexWrap: "wrap", justifyContent: "center" }}>
            <Link className="btn primary" to="/cases/new"><Icon name="plus" size={13} /> Create my first case</Link>
            <button className="btn" onClick={() => setDataMode("reference")}><Icon name="grid" size={13} /> Explore the reference workspace</button>
          </div>
          <div className="own-empty-limits">
            <span><Icon name="lock" size={11} /> Stored in this browser</span>
            <span><Icon name="connectors" size={11} /> No plant connection</span>
            <span><Icon name="shield" size={11} /> No synthetic records</span>
          </div>
        </div>
      ) : (
        <>
          <div className="small-multiples mb16">
            <div className="small-multiple">
              <div className="label">My cases</div>
              <div className="value">{cases.length}</div>
              <div className="note">entered by hand</div>
            </div>
            <div className="small-multiple">
              <div className="label">Open</div>
              <div className="value">{open}</div>
              <div className="note">not signed off</div>
            </div>
            <div className="small-multiple">
              <div className="label">Awaiting review</div>
              <div className="value">{awaiting}</div>
              <div className="note">need a decision</div>
            </div>
            <div className="small-multiple">
              <div className="label">Approved</div>
              <div className="value">{approved}</div>
              <div className="note">signed by you</div>
            </div>
          </div>

          <div className="queue-section-title"><span>My cases</span><span>{cases.length} total</span></div>
          <div className="decision-queue">
            {cases.map((s) => (
              <Link key={s.case.id} className="decision-row own-case-row" to={`/cases/${s.case.id}`}>
                <span className={`severity ${s.case.severity === "critical" || s.case.severity === "high" ? "critical" : "warning"}`} />
                <span>
                  <span className="kind">{s.case.id} · {s.case.line_id}</span>
                  <h3>{s.case.defect_type}</h3>
                  <p>{s.case.part} · batch {s.case.batch_id} · {fmtDateTime(s.case.detected_at)}</p>
                </span>
                <span className="meta"><StatusBadge status={caseStatus(s.case.id)} /></span>
              </Link>
            ))}
          </div>
        </>
      )}

      <div className="panel mt16">
        <div className="panel-head"><h3>What this workspace does and does not do</h3><span className="sub">honest limits</span></div>
        <div className="panel-body">
          <ul className="proof-list">
            <li><b>Does:</b> store your cases, rank the causes you enter, record rejections, draft a report and keep an audit trail.</li>
            <li><b>Does not:</b> read a machine, pull a batch record or run the defect detector. Those need a connected line.</li>
            <li><b>Does not:</b> leave this browser. Clearing site data deletes it; export the case JSON if you need a copy.</li>
            <li><b>Reference data stays available:</b> switch to it from the command palette, the More sheet, or the button above.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
