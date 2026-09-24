"""
backend/config.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")

# ------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------

_default_sqlite = f"sqlite:///{(BASE_DIR / 'support_crm.db').as_posix()}"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    _default_sqlite
).strip()

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

# ------------------------------------------------------------------
# APP
# ------------------------------------------------------------------

APP_NAME = os.getenv(
    "APP_NAME",
    "DataStraw Support"
).strip()

APP_ENV = os.getenv(
    "APP_ENV",
    "production"
).strip()

# ------------------------------------------------------------------
# ADMIN PASSWORD
# ------------------------------------------------------------------

# IMPORTANT:
# On Vercel create:
#
# ADMIN_PASSWORD = DataStraw@2026
#
# You can change it to any password you want.

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "DataStraw@2026"
).strip()
