from __future__ import annotations

import os
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _base_dir()
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = DATA_DIR / "reports"
BACKUP_DIR = DATA_DIR / "backups"
UPLOAD_DIR = DATA_DIR / "uploads"
ASSETS_DIR = BASE_DIR / "app" / "assets"

APP_NAME = "VulnScore"
APP_FULL_NAME = "Automatic Vulnerability Assessment Scoring System"
APP_VERSION = "1.0.0"

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

SESSION_IDLE_TIMEOUT_SECONDS = 30 * 60
MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_SECONDS = 15 * 60

DATABASE_URL = os.environ.get("VULNSCORE_DATABASE_URL", f"sqlite:///{DATA_DIR / 'vulnscore.db'}")


def ensure_directories() -> None:
    for directory in (DATA_DIR, EXPORT_DIR, BACKUP_DIR, UPLOAD_DIR, ASSETS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def database_file() -> Path:
    return DATA_DIR / "vulnscore.db"
