from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agents.drafter import draft_response
from app.agents.ingestion import ingest_ticket
from app.agents.lookup import lookup_evidence
from app.agents.planner import plan_workflow
from app.models.ticket import Ticket
from app.schemas.ticket import ReviewDecision


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


def run_initial_workflow(db: Session, ticket: Ticket) -> None:
    ingested = ingest_ticket(ticket.title, ticket.body)
    _append_state(ticket, "ingestion_agent", "completed", ingested)

    plan = plan_workflow(ingested["signals"])
    ticket.category = plan["category"]
    ticket.priority = plan["priority"]
    ticket.risk = plan["risk"]
    _append_state(ticket, "planning_agent", "completed", plan)

    evidence = lookup_evidence(ticket.category)
    _append_state(ticket, "lookup_agent", "completed", {"evidence": evidence})

    ticket.draft_response = draft_response(ticket.category, ticket.priority, ticket.risk, evidence)
    _append_state(ticket, "drafting_agent", "completed", {"drafted": True})

    ticket.status = "awaiting_review" if ticket.risk in {"medium", "high"} else "ready_to_send"
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
        ticket.status = "approved_for_execution"
        _append_state(
            ticket,
            "human_review_gate",
            "approved",
            {"reviewer": decision.reviewer, "notes": decision.notes},
        )
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
