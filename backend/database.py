"""Database layer.

This module deliberately creates the engine lazily.

Why:
- Importing the FastAPI app must never try to open/write a database file.
- Vercel functions may be imported in a read-only build/runtime environment.
- Production uses Neon PostgreSQL; local development can still use SQLite.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

Base = declarative_base()

_engine: Engine | None = None
_session_factory = None
_tables_ready = False


def _normalise_url(url: str) -> str:
    """Make common Neon/Postgres URLs explicit for psycopg v3."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Add a Neon PostgreSQL connection "
            "string to the Vercel project's Environment Variables."
        )

    url = _normalise_url(DATABASE_URL)

    if url.startswith("sqlite"):
        raw = url.split("sqlite:///")[-1]
        if raw and raw != ":memory:":
            Path(raw).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    else:
        # Small serverless pool. Neon handles the actual persistent database.
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=1,
            max_overflow=2,
        )

    return _engine


def ensure_tables() -> None:
    """Create missing tables once per warm function instance."""
    global _tables_ready
    if _tables_ready:
        return

    # Importing models here registers them with Base.metadata without causing
    # a circular import during application startup.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
    _tables_ready = True


def get_db() -> Generator:
    ensure_tables()
    factory = sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    db = factory()
    try:
        yield db
    finally:
        db.close()
