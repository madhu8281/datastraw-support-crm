"""Vercel FastAPI entrypoint for DataStraw Support CRM.

Vercel maps /api/* requests to this module.  The FastAPI application keeps
the /api prefix in its route declarations so local and production URLs are
identical.
"""
from backend.main import app

__all__ = ["app"]
