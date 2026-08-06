from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.drafter import draft_response
from app.agents.ingestion import ingest_ticket
from app.agents.lookup import lookup_evidence
from app.agents.planner import plan_workflow
from app.core.telemetry import AgentTelemetry
from app.models.ticket import Ticket
from app.schemas.ticket import ReviewDecision


class WorkflowState(TypedDict, total=False):
    title: str
    body: str
    ingested: dict[str, Any]
    category: str
    priority: str
    risk: str
    evidence: list[str]
    draft_response: str
    status: str


def _append_state(ticket: Ticket, node: str, status: str, payload: dict[str, Any]) -> None:
    history = list(ticket.state_history or [])
    history.append(
        {
            "node": node,
            "status": status,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    ticket.state_history = history


def _append_failure(ticket: Ticket, node: str, exc: Exception) -> None:
    _append_state(
        ticket,
        node,
        "failed",
        {
            "error": str(exc),
            "fallback": "workflow paused for manual triage",
        },
    )
    ticket.status = "failed_manual_triage"


def _ingestion_node(state: WorkflowState) -> WorkflowState:
    return {"ingested": ingest_ticket(state["title"], state["body"])}


def _planning_node(state: WorkflowState) -> WorkflowState:
    plan = plan_workflow(state["ingested"]["signals"])
    return {
        "category": plan["category"],
        "priority": plan["priority"],
        "risk": plan["risk"],
    }


def _lookup_node(state: WorkflowState) -> WorkflowState:
    return {"evidence": lookup_evidence(state["category"])}


def _drafting_node(state: WorkflowState) -> WorkflowState:
    return {
        "draft_response": draft_response(
            state["category"],
            state["priority"],
            state["risk"],
            state["evidence"],
        )
    }


def _review_gate_node(state: WorkflowState) -> WorkflowState:
    status = "awaiting_review" if state["risk"] in {"medium", "high"} else "ready_to_send"
    return {"status": status}


def build_support_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("ingestion_agent", _ingestion_node)
    graph.add_node("planning_agent", _planning_node)
    graph.add_node("lookup_agent", _lookup_node)
    graph.add_node("drafting_agent", _drafting_node)
    graph.add_node("human_review_gate", _review_gate_node)

    graph.set_entry_point("ingestion_agent")
    graph.add_edge("ingestion_agent", "planning_agent")
    graph.add_edge("planning_agent", "lookup_agent")
    graph.add_edge("lookup_agent", "drafting_agent")
    graph.add_edge("drafting_agent", "human_review_gate")
    graph.add_edge("human_review_gate", END)
    return graph.compile()


def run_initial_workflow(db: Session, ticket: Ticket) -> None:
    telemetry = AgentTelemetry()
    workflow = build_support_workflow()

    try:
        with telemetry.node("support_workflow") as trace:
            result = workflow.invoke({"title": ticket.title, "body": ticket.body})
        _append_state(ticket, "agentops_trace", "completed", trace)
    except Exception as exc:
        _append_failure(ticket, "support_workflow", exc)
        db.add(ticket)
        db.commit()
        return

    ingested = result["ingested"]
    _append_state(ticket, "ingestion_agent", "completed", ingested)

    ticket.category = result["category"]
    ticket.priority = result["priority"]
    ticket.risk = result["risk"]
    _append_state(
        ticket,
        "planning_agent",
        "completed",
        {
            "category": ticket.category,
            "priority": ticket.priority,
            "risk": ticket.risk,
        },
    )

    evidence = result["evidence"]
    _append_state(ticket, "lookup_agent", "completed", {"evidence": evidence})

    ticket.draft_response = result["draft_response"]
    _append_state(ticket, "drafting_agent", "completed", {"drafted": True})

    ticket.status = result["status"]
    _append_state(
        ticket,
        "human_review_gate",
        "waiting" if ticket.status == "awaiting_review" else "skipped",
        {"reason": f"{ticket.risk} risk workflow"},
    )
    db.add(ticket)
    db.commit()


def apply_review_decision(db: Session, ticket: Ticket, decision: ReviewDecision) -> None:
    if ticket.status != "awaiting_review":
        _append_state(
            ticket,
            "human_review_gate",
            "ignored",
            {"reason": f"ticket is {ticket.status}"},
        )
    elif decision.decision == "approved":
        telemetry = AgentTelemetry()
        _append_state(
            ticket,
            "human_review_gate",
            "approved",
            {"reviewer": decision.reviewer, "notes": decision.notes},
        )
        try:
            with telemetry.node("execution_node") as trace:
                payload = {
                    "action": "safe_response_prepared",
                    "result": "Draft marked ready for customer send and internal follow-up.",
                    "trace_id": trace["trace_id"],
                }
            _append_state(ticket, "execution_node", "completed", payload)
            ticket.status = "resolved"
        except Exception as exc:
            _append_failure(ticket, "execution_node", exc)
    else:
        ticket.status = "needs_revision"
        _append_state(
            ticket,
            "human_review_gate",
            "rejected",
            {"reviewer": decision.reviewer, "notes": decision.notes},
        )

    db.add(ticket)
    db.commit()
