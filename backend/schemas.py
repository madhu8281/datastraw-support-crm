"""
backend/schemas.py
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# --------------------------------------------------------------------------
# CREATE TICKET
# --------------------------------------------------------------------------

class TicketCreate(BaseModel):

    customer_name: str = Field(
        min_length=2,
        max_length=120
    )

    customer_email: EmailStr

    subject: str = Field(
        min_length=3,
        max_length=200
    )

    description: str = Field(
        min_length=5,
        max_length=5000
    )

    priority: Priority = Priority.MEDIUM

    @field_validator(
        "customer_name",
        "subject",
        "description"
    )
    @classmethod
    def not_only_spaces(cls, value: str) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "This field cannot be empty"
            )

        return cleaned


# --------------------------------------------------------------------------
# UPDATE TICKET
# --------------------------------------------------------------------------

class TicketUpdate(BaseModel):

    status: Optional[Status] = None

    priority: Optional[Priority] = None

    notes: Optional[str] = Field(
        default=None,
        max_length=2000
    )

    @field_validator("notes")
    @classmethod
    def clean_note(
        cls,
        value: Optional[str]
    ) -> Optional[str]:

        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @model_validator(mode="after")
    def at_least_one_field(self):

        if (
            self.status is None
            and self.priority is None
            and self.notes is None
        ):
            raise ValueError(
                "Send at least one of: status, priority, notes"
            )

        return self


# --------------------------------------------------------------------------
# NOTES
# --------------------------------------------------------------------------

class NoteOut(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    note_text: str
    created_at: datetime


# --------------------------------------------------------------------------
# CREATED RESPONSE
# --------------------------------------------------------------------------

class TicketCreated(BaseModel):

    ticket_id: str
    created_at: datetime


# --------------------------------------------------------------------------
# ADMIN TICKET LIST
# --------------------------------------------------------------------------

class TicketListItem(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    ticket_id: str
    customer_name: str
    subject: str
    status: str
    priority: str
    created_at: datetime


# --------------------------------------------------------------------------
# FULL TICKET
# --------------------------------------------------------------------------

class TicketDetail(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

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


# --------------------------------------------------------------------------
# CUSTOMER PORTAL RESPONSE
# --------------------------------------------------------------------------

class CustomerTicket(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# UPDATE RESPONSE
# --------------------------------------------------------------------------

class TicketUpdated(BaseModel):

    success: bool = True
    updated_at: datetime


# --------------------------------------------------------------------------
# STATS
# --------------------------------------------------------------------------

class StatsOut(BaseModel):

    total: int
    open: int
    in_progress: int
    closed: int
    high_priority_open: int
