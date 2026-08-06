const sampleHistory = [
  ["ingestion_agent", "completed", "Signals extracted from ticket text"],
  ["planning_agent", "completed", "Authentication issue marked high risk"],
  ["lookup_agent", "completed", "Evidence checklist attached"],
  ["drafting_agent", "completed", "Customer response and patch plan drafted"],
  ["human_review_gate", "waiting", "Approval required before execution"],
];

export default function Home() {
  return (
    <main>
      <section className="topbar">
        <div>
          <p>AgentOps</p>
          <h1>Support Automator</h1>
        </div>
        <span>review console</span>
      </section>

      <section className="workspace">
        <form className="ticket-panel">
          <p className="eyebrow">incoming ticket</p>
          <label>
            Title
            <input defaultValue="Users cannot log in after token refresh" />
          </label>
          <label>
            Customer
            <input defaultValue="Acme Cloud" />
          </label>
          <label>
            Report
            <textarea defaultValue="After the latest deploy, users are redirected back to login. JWT refresh appears to fail for existing sessions." />
          </label>
          <button type="button">Run Workflow</button>
        </form>

        <section className="workflow-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">workflow state</p>
              <h2>Awaiting human review</h2>
            </div>
            <strong>high risk</strong>
          </div>

          <div className="timeline">
            {sampleHistory.map(([node, status, detail]) => (
              <article key={node}>
                <span>{status}</span>
                <div>
                  <h3>{node}</h3>
                  <p>{detail}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="review-card">
            <p className="eyebrow">draft response</p>
            <pre>{`Category: authentication
Priority: high
Risk: high

Proposed action:
Acknowledge the report, validate affected sessions, inspect token middleware,
and require reviewer approval before execution.`}</pre>
            <div>
              <button type="button">Approve</button>
              <button type="button" className="secondary">Request Revision</button>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
