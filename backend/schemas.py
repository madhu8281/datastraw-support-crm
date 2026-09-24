"""
schemas.py
----------
Pydantic models = the "shape" of the JSON going in and out of the API.

models.py  describes what the DATABASE stores.
schemas.py describes what the API ACCEPTS and RETURNS.

Keeping them separate matters: the database row has an internal `id` and
could later hold private fields; the API should only expose what we choose.
Pydantic also validates incoming JSON for us. If the client sends a bad
email or an empty subject, FastAPI rejects the request with 422 before a
single line of our own code runs.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class Status(str, Enum):
    """The only three statuses the system accepts. Anything else -> 422."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# --------------------------------------------------------------------------
# Incoming data
# --------------------------------------------------------------------------
class TicketCreate(BaseModel):
    """Body of POST /api/tickets"""

    customer_name: str = Field(min_length=2, max_length=120, examples=["Madhavi Lokhande"])
    customer_email: EmailStr = Field(examples=["madhavi@example.com"])
    subject: str = Field(min_length=3, max_length=200, examples=["Unable to login"])
    description: str = Field(min_length=5, max_length=5000, examples=["I cannot access my account."])
    priority: Priority = Priority.MEDIUM

    @field_validator("customer_name", "subject", "description")
    @classmethod
    def not_only_spaces(cls, value: str) -> str:
        """"   " passes a length check but is still empty. Strip and re-check."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty")
        return cleaned


class TicketUpdate(BaseModel):
    """
    Body of PUT /api/tickets/{ticket_id}

    Every field is optional, so the support agent can change only the status,
    or only add a note, or do both in one request.
    """

    status: Optional[Status] = None
    priority: Optional[Priority] = None
    notes: Optional[str] = Field(default=None, max_length=2000, examples=["Customer has been contacted."])

    @field_validator("notes")
    @classmethod
    def clean_note(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.status is None and self.priority is None and self.notes is None:
            raise ValueError("Send at least one of: status, priority, notes")
        return self


# --------------------------------------------------------------------------
# Outgoing data
# --------------------------------------------------------------------------
class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_text: str
    created_at: datetime


class TicketCreated(BaseModel):
    """Response of POST /api/tickets - exactly what the assignment asks for."""
    ticket_id: str
    created_at: datetime


class TicketListItem(BaseModel):
    """One row of the dashboard table."""
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    customer_name: str
    subject: str
    status: str
    priority: str
    created_at: datetime


class TicketDetail(BaseModel):
    """Full ticket, used by the ticket details page."""
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    notes: List[NoteOut] = []


class TicketUpdated(BaseModel):
    """Response of PUT /api/tickets/{ticket_id}"""
    success: bool = True
    updated_at: datetime


class StatsOut(BaseModel):
    """Numbers for the four cards at the top of the dashboard."""
    total: int
    open: int
    in_progress: int
    closed: int
    high_priority_open: int
