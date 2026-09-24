"""SQLAlchemy database models."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable during the one transaction in which we obtain the database id.
    # It becomes TKT-<id> before commit, eliminating ticket-number races.
    ticket_id = Column(String(32), unique=True, index=True, nullable=True)

    customer_name = Column(String(120), nullable=False)
    customer_email = Column(String(200), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    status = Column(String(20), nullable=False, default="Open", index=True)
    priority = Column(String(10), nullable=False, default="Medium", index=True)

    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    notes = relationship(
        "Note",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Note.created_at",
    )


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    ticket = relationship("Ticket", back_populates="notes")
