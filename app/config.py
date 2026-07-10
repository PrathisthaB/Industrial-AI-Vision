"""
Application configuration.

Configuration is environment-driven so the same codebase can run in
development, testing, and production without code changes.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration shared by all environments."""

    # --- Core Flask settings -------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours

    # --- Paths ----------------------------------------------------------------
    BASE_DIR = BASE_DIR
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", str(BASE_DIR / "database" / "safety_platform.db")
    )
    SCHEMA_PATH = str(BASE_DIR / "app" / "database" / "schema.sql")
    VIOLATIONS_DIR = os.environ.get("VIOLATIONS_DIR", str(BASE_DIR / "violations"))
    REPORTS_DIR = os.environ.get("REPORTS_DIR", str(BASE_DIR / "reports"))
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "uploads"))
    MODEL_PATH = os.environ.get("MODEL_PATH", str(BASE_DIR / "yolov8n.pt"))
    PPE_MODEL_CANDIDATES = ["yolov8n-ppe.pt", "best.pt", "ppe.pt"]

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max upload
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

    # --- Detection pipeline ----------------------------------------------------
    INFER_SIZE = 640
    CONF_THRESHOLD = 0.35
    IOU_THRESHOLD = 0.45
    FRAME_SKIP = 2                # process every Nth frame to sustain FPS
    DUPLICATE_FRAME_THRESHOLD = 2.0  # mean abs diff below this => treat as duplicate
    VIOLATION_COOLDOWN_SECONDS = 8  # avoid re-logging the same ongoing violation

    # --- Auth -------------------------------------------------------------------
    DEFAULT_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ":memory:"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(name=None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(name, DevelopmentConfig)
