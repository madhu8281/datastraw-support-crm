"""DataStraw Support CRM - FastAPI application for Vercel."""

import logging
import secrets
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status as http_status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .config import ADMIN_PASSWORD, ALLOWED_ORIGINS, APP_ENV, APP_NAME, FRONTEND_DIR
from .database import Base, ensure_tables, get_db, get_engine

logger = logging.getLogger("datastraw")

app = FastAPI(
    title=f"{APP_NAME} API",
    version="2.0.0",
    description="Customer support ticketing system",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        location = error.get("loc") or ("request",)
        field = location[-1]
        messages.append(f"{field}: {error.get('msg', 'invalid value')}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Please check the values you entered.",
            "errors": messages,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    # Rollback is handled by the request session's close; logging keeps the
    # real cause visible in Vercel logs without exposing credentials to users.
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The database is temporarily unavailable. "
                "Please try again in a moment."
            )
        },
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    logger.exception("Configuration/runtime error on %s", request.url.path)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Unexpected server error. Please try again."},
    )


def require_admin(x_admin_password: Optional[str] = Header(default=None)):
    if not x_admin_password or not secrets.compare_digest(
        x_admin_password, ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin password.",
        )


@app.get("/api/health", tags=["system"])
def health_check():
    """Checks both application configuration and database connectivity."""
    try:
        ensure_tables()
        with get_engine().connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "ok", "database": "connected", "app": APP_NAME}
    except Exception as exc:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "unavailable",
                "detail": str(exc),
                "app": APP_NAME,
            },
        )


@app.post("/api/admin/verify", tags=["admin"])
def verify_admin(x_admin_password: Optional[str] = Header(default=None)):
    if not x_admin_password or not secrets.compare_digest(
        x_admin_password, ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=401, detail="Incorrect admin password."
        )
    return {"authenticated": True}


@app.post(
    "/api/tickets",
    response_model=schemas.TicketCreated,
    status_code=201,
    tags=["tickets"],
)
def create_ticket(
    payload: schemas.TicketCreate, db: Session = Depends(get_db)
):
    ticket = crud.create_ticket(db, payload)
    return schemas.TicketCreated(
        ticket_id=ticket.ticket_id,
        created_at=ticket.created_at,
    )


@app.get(
    "/api/tickets",
    response_model=List[schemas.TicketListItem],
    dependencies=[Depends(require_admin)],
)
def list_tickets(
    db: Session = Depends(get_db),
    status: Optional[schemas.Status] = Query(default=None),
    priority: Optional[schemas.Priority] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
):
    return crud.get_tickets(
        db,
        status=status.value if status else None,
        search=search,
        priority=priority.value if priority else None,
    )


@app.get(
    "/api/stats",
    response_model=schemas.StatsOut,
    dependencies=[Depends(require_admin)],
)
def ticket_stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)


@app.get(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketDetail,
    dependencies=[Depends(require_admin)],
)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = crud.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} was not found.",
        )
    return ticket


@app.put(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketUpdated,
    dependencies=[Depends(require_admin)],
)
def update_ticket(
    ticket_id: str,
    payload: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket_by_ticket_id(db, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} was not found.",
        )
    updated = crud.update_ticket(db, ticket, payload)
    return schemas.TicketUpdated(
        success=True, updated_at=updated.updated_at
    )


# The static frontend is served from the same FastAPI function, so the
# browser always calls /api/... on the same origin.
if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
