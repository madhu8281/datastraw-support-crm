"""Application configuration.

Production on Vercel uses PostgreSQL (Neon) through DATABASE_URL.
Local development automatically falls back to SQLite.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

IS_VERCEL = os.getenv("VERCEL", "").lower() == "1"

# Do not invent a writable SQLite path on Vercel. Vercel's function filesystem
# is ephemeral and must not be used as the application's persistent database.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL and not IS_VERCEL:
    DATABASE_URL = f"sqlite:///{(BASE_DIR / 'support_crm.db').as_posix()}"

APP_NAME = os.getenv("APP_NAME", "DataStraw Support")
APP_ENV = os.getenv("APP_ENV", "production" if IS_VERCEL else "development")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "DataStraw@2026")

ALLOWED_ORIGINS = [
    x.strip()
    for x in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if x.strip()
]
