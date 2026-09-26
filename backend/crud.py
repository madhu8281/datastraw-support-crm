"""Database operations for the support CRM."""

from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from . import models, schemas


def create_ticket(db: Session, payload: schemas.TicketCreate) -> models.Ticket:
    """Create a ticket using the database-generated integer id.

    This is safer than MAX(ticket_id)+1 because two Vercel instances can
    receive requests at the same time.
    """
    ticket = models.Ticket(
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email),
        subject=payload.subject,
        description=payload.description,
        status=schemas.Status.OPEN.value,
        priority=payload.priority.value,
    )
    db.add(ticket)
    db.flush()  # PostgreSQL/SQLite assigns ticket.id without committing yet.
    ticket.ticket_id = f"TKT-{ticket.id:03d}"
    db.commit()
    db.refresh(ticket)
    return ticket


def get_tickets(
    db: Session,
    status: Optional[str] = None,
    search: Optional[str] = None,
    priority: Optional[str] = None,
):
    query = db.query(models.Ticket)

    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)

    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Ticket.ticket_id).like(term),
                func.lower(models.Ticket.customer_name).like(term),
                func.lower(models.Ticket.customer_email).like(term),
                func.lower(models.Ticket.subject).like(term),
                func.lower(models.Ticket.description).like(term),
            )
        )

    return query.order_by(
        models.Ticket.created_at.desc(), models.Ticket.id.desc()
    ).all()


def get_ticket_by_ticket_id(db: Session, ticket_id: str):
    return (
        db.query(models.Ticket)
        .options(selectinload(models.Ticket.notes))
        .filter(func.lower(models.Ticket.ticket_id) == ticket_id.strip().lower())
        .first()
    )


def get_stats(db: Session) -> dict:
    total = db.query(func.count(models.Ticket.id)).scalar() or 0

    def count_status(value: str) -> int:
        return (
            db.query(func.count(models.Ticket.id))
            .filter(models.Ticket.status == value)
            .scalar()
            or 0
        )

    high_priority_open = (
        db.query(func.count(models.Ticket.id))
        .filter(
            models.Ticket.priority == "High",
            models.Ticket.status != "Closed",
        )
        .scalar()
        or 0
    )

    return {
        "total": total,
        "open": count_status("Open"),
        "in_progress": count_status("In Progress"),
        "closed": count_status("Closed"),
        "high_priority_open": high_priority_open,
    }


def update_ticket(
    db: Session, ticket: models.Ticket, payload: schemas.TicketUpdate
) -> models.Ticket:
    if payload.status is not None:
        ticket.status = payload.status.value
    if payload.priority is not None:
        ticket.priority = payload.priority.value
    if payload.notes:
        ticket.notes.append(models.Note(note_text=payload.notes))

    ticket.updated_at = models.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket
