"""
Database connection management and automatic schema initialization.

Uses plain sqlite3 (no ORM) with row factories for dict-like access.
Kept dependency-free so the project runs anywhere Python + SQLite runs.
"""

import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    """Return a request-scoped SQLite connection, creating it if needed."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create all tables (idempotent) and seed a default admin user."""
    with app.app_context():
        db = get_db()
        schema_path = Path(app.config["SCHEMA_PATH"])
        with open(schema_path, "r", encoding="utf-8") as f:
            db.executescript(f.read())
        db.commit()
        _seed_default_admin(app, db)


def _seed_default_admin(app, db):
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?",
        (app.config["DEFAULT_ADMIN_USERNAME"],),
    ).fetchone()
    if existing is None:
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) "
            "VALUES (?, ?, 'admin', 'Platform Administrator')",
            (
                app.config["DEFAULT_ADMIN_USERNAME"],
                generate_password_hash(app.config["DEFAULT_ADMIN_PASSWORD"]),
            ),
        )
        db.commit()


def register_db(app):
    """Wire teardown handler and ensure the schema exists at startup."""
    app.teardown_appcontext(close_db)
    init_db(app)
