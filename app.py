"""Vercel entrypoint.

Vercel's current FastAPI support can discover a root app.py automatically.
Keeping this tiny file also makes the entrypoint unambiguous for the platform.
"""

from backend.main import app

__all__ = ["app"]
