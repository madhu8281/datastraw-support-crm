"""
backend/main.py
"""

import secrets

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    status as http_status,
)

from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

from . import crud, models, schemas

from .config import (
    ADMIN_PASSWORD,
    ALLOWED_ORIGINS,
    APP_ENV,
    APP_NAME,
    FRONTEND_DIR,
)

from .database import (
    Base,
    engine,
    get_db,
)


# --------------------------------------------------------------------------
# DATABASE STARTUP
# --------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(
        bind=engine
    )

    yield


app = FastAPI(
    title=f"{APP_NAME} API",
    description="DataStraw customer support system",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
):

    messages = []

    for error in exc.errors():

        field = (
            error["loc"][-1]
            if error.get("loc")
            else "request"
        )

        messages.append(
            f"{field}: {error.get('msg', 'invalid value')}"
        )

    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Please check the values you entered.",
            "errors": messages,
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception
):

    print("SERVER ERROR:", repr(exc))

    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail":
                "Something went wrong on the server. "
                "Please try again."
        },
    )


# --------------------------------------------------------------------------
# ADMIN AUTHENTICATION
# --------------------------------------------------------------------------

def verify_admin_password(
    password: Optional[str]
):

    if not password:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin password.",
        )

    entered = password.strip()
    expected = ADMIN_PASSWORD.strip()

    if not secrets.compare_digest(
        entered,
        expected
    ):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin password.",
        )

    return True


def require_admin(
    x_admin_password: Optional[str] = Header(
        default=None
    )
):

    return verify_admin_password(
        x_admin_password
    )


# --------------------------------------------------------------------------
# ADMIN VERIFY ENDPOINT
# --------------------------------------------------------------------------

@app.post(
    "/api/admin/verify",
    tags=["admin"]
)
def verify_admin(
    x_admin_password: Optional[str] = Header(
        default=None
    )
):

    verify_admin_password(
        x_admin_password
    )

    return {
        "authenticated": True
    }


# --------------------------------------------------------------------------
# HEALTH
# --------------------------------------------------------------------------

@app.get(
    "/api/health",
    tags=["system"]
)
def health_check():

    return {
        "status": "ok",
        "app": APP_NAME,
        "environment": APP_ENV,
    }


# --------------------------------------------------------------------------
# CREATE TICKET
# --------------------------------------------------------------------------

@app.post(
    "/api/tickets",
    response_model=schemas.TicketCreated,
    status_code=http_status.HTTP_201_CREATED,
    tags=["tickets"],
)
def create_ticket(
    payload: schemas.TicketCreate,
    db: Session = Depends(get_db)
):

    ticket = crud.create_ticket(
        db,
        payload
    )

    return schemas.TicketCreated(
        ticket_id=ticket.ticket_id,
        created_at=ticket.created_at,
    )


# --------------------------------------------------------------------------
# ADMIN TICKET LIST
# --------------------------------------------------------------------------

@app.get(
    "/api/tickets",
    response_model=List[schemas.TicketListItem],
    tags=["tickets"],
)
def list_tickets(
    db: Session = Depends(get_db),

    status: Optional[schemas.Status] = Query(
        default=None
    ),

    priority: Optional[schemas.Priority] = Query(
        default=None
    ),

    search: Optional[str] = Query(
        default=None,
        max_length=100
    ),
):

    tickets = crud.get_tickets(
        db,
        status=status.value if status else None,
        search=search,
        priority=priority.value if priority else None,
    )

    return tickets


# --------------------------------------------------------------------------
# CUSTOMER EMAIL SEARCH
# --------------------------------------------------------------------------

@app.get(
    "/api/customer/tickets",
    response_model=List[schemas.CustomerTicket],
    tags=["customer"],
)
def customer_tickets(
    email: str = Query(
        ...,
        min_length=5,
        max_length=200
    ),
    db: Session = Depends(get_db),
):

    # Validate email using Pydantic.
    try:
        validated_email = schemas.TicketCreate(
            customer_name="Customer",
            customer_email=email,
            subject="Temporary",
            description="Temporary",
        ).customer_email

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    tickets = crud.get_customer_tickets(
        db,
        str(validated_email)
    )

    return tickets


# --------------------------------------------------------------------------
# STATS
# --------------------------------------------------------------------------

@app.get(
    "/api/stats",
    response_model=schemas.StatsOut,
    tags=["tickets"],
)
def ticket_stats(
    db: Session = Depends(get_db)
):

    return crud.get_stats(db)


# --------------------------------------------------------------------------
# SINGLE TICKET
# --------------------------------------------------------------------------

@app.get(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketDetail,
    tags=["tickets"],
)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db)
):

    ticket = crud.get_ticket_by_ticket_id(
        db,
        ticket_id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} was not found."
        )

    return ticket


# --------------------------------------------------------------------------
# ADMIN UPDATE TICKET
# --------------------------------------------------------------------------

@app.put(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketUpdated,
    tags=["tickets"],
    dependencies=[
        Depends(require_admin)
    ],
)
def update_ticket(
    ticket_id: str,
    payload: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):

    ticket = crud.get_ticket_by_ticket_id(
        db,
        ticket_id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} was not found."
        )

    updated = crud.update_ticket(
        db,
        ticket,
        payload
    )

    return schemas.TicketUpdated(
        success=True,
        updated_at=updated.updated_at
    )


# --------------------------------------------------------------------------
# FRONTEND
# --------------------------------------------------------------------------

if FRONTEND_DIR.exists():

    app.mount(
        "/",
        StaticFiles(
            directory=str(FRONTEND_DIR),
            html=True
        ),
        name="frontend"
    )
