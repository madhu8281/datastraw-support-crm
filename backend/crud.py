"""
backend/crud.py
"""

from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from . import models, schemas


# --------------------------------------------------------------------------
# Ticket ID generation
# --------------------------------------------------------------------------

def generate_ticket_id(db: Session) -> str:
    last_ticket = (
        db.query(models.Ticket)
        .order_by(models.Ticket.id.desc())
        .first()
    )

    if last_ticket is None:
        next_number = 1
    else:
        try:
            next_number = int(last_ticket.ticket_id.split("-")[1]) + 1
        except (IndexError, ValueError):
            next_number = last_ticket.id + 1

    return f"TKT-{next_number:03d}"


# --------------------------------------------------------------------------
# Create ticket
# --------------------------------------------------------------------------

def create_ticket(
    db: Session,
    payload: schemas.TicketCreate
) -> models.Ticket:

    for _ in range(5):

        ticket = models.Ticket(
            ticket_id=generate_ticket_id(db),
            customer_name=payload.customer_name,
            customer_email=str(payload.customer_email).strip().lower(),
            subject=payload.subject,
            description=payload.description,
            status=schemas.Status.OPEN.value,
            priority=payload.priority.value,
        )

        db.add(ticket)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        db.refresh(ticket)

        return ticket

    raise RuntimeError(
        "Could not generate a unique ticket id after 5 attempts"
    )


# --------------------------------------------------------------------------
# Get all tickets
# --------------------------------------------------------------------------

def get_tickets(
    db: Session,
    status: Optional[str] = None,
    search: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[models.Ticket]:

    query = db.query(models.Ticket)

    if status:
        query = query.filter(
            models.Ticket.status == status
        )

    if priority:
        query = query.filter(
            models.Ticket.priority == priority
        )

    if search:
        term = f"%{search.strip().lower()}%"

        query = query.filter(
            or_(
                func.lower(
                    models.Ticket.ticket_id
                ).like(term),

                func.lower(
                    models.Ticket.customer_name
                ).like(term),

                func.lower(
                    models.Ticket.customer_email
                ).like(term),

                func.lower(
                    models.Ticket.subject
                ).like(term),

                func.lower(
                    models.Ticket.description
                ).like(term),
            )
        )

    return (
        query
        .order_by(
            models.Ticket.created_at.desc(),
            models.Ticket.id.desc()
        )
        .all()
    )


# --------------------------------------------------------------------------
# CUSTOMER EMAIL SEARCH
# --------------------------------------------------------------------------

def get_customer_tickets(
    db: Session,
    email: str
) -> List[models.Ticket]:

    normalized_email = email.strip().lower()

    return (
        db.query(models.Ticket)
        .filter(
            func.lower(
                models.Ticket.customer_email
            ) == normalized_email
        )
        .order_by(
            models.Ticket.created_at.desc(),
            models.Ticket.id.desc()
        )
        .all()
    )


# --------------------------------------------------------------------------
# Get one ticket
# --------------------------------------------------------------------------

def get_ticket_by_ticket_id(
    db: Session,
    ticket_id: str
) -> Optional[models.Ticket]:

    return (
        db.query(models.Ticket)
        .options(
            selectinload(models.Ticket.notes)
        )
        .filter(
            func.lower(
                models.Ticket.ticket_id
            ) == ticket_id.strip().lower()
        )
        .first()
    )


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def get_stats(db: Session) -> dict:

    total = (
        db.query(
            func.count(models.Ticket.id)
        ).scalar()
        or 0
    )

    def count_status(value: str) -> int:
        return (
            db.query(
                func.count(models.Ticket.id)
            )
            .filter(
                models.Ticket.status == value
            )
            .scalar()
            or 0
        )

    high_priority_open = (
        db.query(
            func.count(models.Ticket.id)
        )
        .filter(
            models.Ticket.priority == "High",
            models.Ticket.status != "Closed"
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


# --------------------------------------------------------------------------
# Update ticket
# --------------------------------------------------------------------------

def update_ticket(
    db: Session,
    ticket: models.Ticket,
    payload: schemas.TicketUpdate
) -> models.Ticket:

    if payload.status is not None:
        ticket.status = payload.status.value

    if payload.priority is not None:
        ticket.priority = payload.priority.value

    if payload.notes:
        ticket.notes.append(
            models.Note(
                note_text=payload.notes
            )
        )

    ticket.updated_at = models.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket
