from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import ReviewDecision, TicketCreate, TicketRead
from app.services.workflow import apply_review_decision, run_initial_workflow

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    ticket = Ticket(
        title=payload.title,
        customer=payload.customer,
        body=payload.body,
        status="received",
        state_history=[],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    run_initial_workflow(db, ticket)
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)) -> list[Ticket]:
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/{ticket_id}/review", response_model=TicketRead)
def review_ticket(
    ticket_id: int,
    payload: ReviewDecision,
    db: Session = Depends(get_db),
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    apply_review_decision(db, ticket, payload)
    db.refresh(ticket)
    return ticket
