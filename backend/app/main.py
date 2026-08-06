from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import Base, engine, get_db
from app.models.ticket import Ticket
from app.schemas.ticket import ReviewDecision, TicketCreate, TicketRead
from app.services.workflow import run_initial_workflow, apply_review_decision

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgentOps Support Automator",
    description="Multi-agent technical support workflow automation with human review.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketRead)
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


@app.get("/tickets", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)) -> list[Ticket]:
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


@app.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets/{ticket_id}/review", response_model=TicketRead)
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
