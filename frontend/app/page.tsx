"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Ticket = {
  id: number;
  title: string;
  customer: string;
  body: string;
  category: string | null;
  priority: string | null;
  risk: string | null;
  status: string;
  draft_response: string | null;
  state_history: Array<{
    node: string;
    status: string;
    payload: Record<string, unknown>;
    timestamp: string;
  }>;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    title: "Users cannot log in after token refresh",
    customer: "Acme Cloud",
    body: "After the latest deploy, users are redirected back to login. JWT refresh appears to fail for existing sessions.",
  });

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedId) ?? tickets[0],
    [selectedId, tickets],
  );
  const finalSummary =
    selectedTicket?.status === "resolved"
      ? "Approved workflow completed. The execution node prepared the response for customer send."
      : selectedTicket?.status === "needs_revision"
        ? "Reviewer rejected this run. The workflow is parked for a safer revised plan."
        : selectedTicket?.status === "awaiting_review"
          ? "Human sign-off is required before execution."
          : "Run a workflow to create an auditable state trail.";

  async function loadTickets() {
    const response = await fetch(`${apiUrl}/tickets`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Could not load tickets");
    }
    const data = (await response.json()) as Ticket[];
    setTickets(data);
    setSelectedId((current) => current ?? data[0]?.id ?? null);
  }

  useEffect(() => {
    loadTickets().catch(() => setMessage("API is not reachable yet."));
  }, []);

  async function submitTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!response.ok) {
        throw new Error("Workflow failed");
      }
      const ticket = (await response.json()) as Ticket;
      await loadTickets();
      setSelectedId(ticket.id);
      setMessage(`Workflow ${ticket.id} is ${ticket.status}.`);
    } catch {
      setMessage("Could not run the workflow. Check the API container.");
    } finally {
      setLoading(false);
    }
  }

  async function review(decision: "approved" | "rejected") {
    if (!selectedTicket) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${apiUrl}/tickets/${selectedTicket.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decision,
          reviewer: "Aadya",
          notes: decision === "approved" ? "Approved from review console." : "Needs a safer patch plan.",
        }),
      });
      if (!response.ok) {
        throw new Error("Review failed");
      }
      const ticket = (await response.json()) as Ticket;
      await loadTickets();
      setSelectedId(ticket.id);
      setMessage(`Review saved: ${ticket.status}.`);
    } catch {
      setMessage("Could not save the review decision.");
    } finally {
      setLoading(false);
    }
  }

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
        <form className="ticket-panel" onSubmit={submitTicket}>
          <p className="eyebrow">incoming ticket</p>
          <label>
            Title
            <input
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
            />
          </label>
          <label>
            Customer
            <input
              value={form.customer}
              onChange={(event) => setForm({ ...form, customer: event.target.value })}
            />
          </label>
          <label>
            Report
            <textarea
              value={form.body}
              onChange={(event) => setForm({ ...form, body: event.target.value })}
            />
          </label>
          <button disabled={loading}>{loading ? "Running..." : "Run Workflow"}</button>
          {message ? <p className="status-message">{message}</p> : null}

          <div className="ticket-list">
            {tickets.map((ticket) => (
              <button
                key={ticket.id}
                type="button"
                className={ticket.id === selectedTicket?.id ? "ticket-tab active" : "ticket-tab"}
                onClick={() => setSelectedId(ticket.id)}
              >
                #{ticket.id} {ticket.status}
              </button>
            ))}
          </div>
        </form>

        <section className="workflow-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">workflow state</p>
              <h2>{selectedTicket?.status ?? "No workflow yet"}</h2>
            </div>
            <strong>{selectedTicket?.risk ?? "pending"}</strong>
          </div>

          {selectedTicket ? (
            <>
              <div className="meta-grid">
                <span>Category: {selectedTicket.category}</span>
                <span>Priority: {selectedTicket.priority}</span>
                <span>Customer: {selectedTicket.customer}</span>
              </div>
              <div className="state-summary">{finalSummary}</div>

              <div className="timeline">
                {selectedTicket.state_history.map((item, index) => (
                  <article key={`${item.node}-${index}`}>
                    <span>{item.status}</span>
                    <div>
                      <h3>{item.node}</h3>
                      <p>{new Date(item.timestamp).toLocaleString()}</p>
                    </div>
                  </article>
                ))}
              </div>

              <div className="review-card">
                <p className="eyebrow">draft response</p>
                <pre>{selectedTicket.draft_response}</pre>
                <div>
                  <button
                    type="button"
                    disabled={loading || selectedTicket.status !== "awaiting_review"}
                    onClick={() => review("approved")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={loading || selectedTicket.status !== "awaiting_review"}
                    onClick={() => review("rejected")}
                  >
                    Request Revision
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">Run a ticket to create the first workflow.</div>
          )}
        </section>
      </section>
    </main>
  );
}
