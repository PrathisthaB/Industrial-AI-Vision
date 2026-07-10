"""User model — authentication data access."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import get_db


class User:
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.role = row["role"]
        self.full_name = row["full_name"]
        self.created_at = row["created_at"]
        self.last_login_at = row["last_login_at"]

    # Flask-Login-style helpers (used manually via session, no extra dependency)
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "full_name": self.full_name,
        }

    @staticmethod
    def get_by_id(user_id):
        row = get_db().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User(row) if row else None

    @staticmethod
    def get_by_username(username):
        row = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return User(row) if row else None

    @staticmethod
    def verify_credentials(username, password):
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return None
        if not check_password_hash(row["password_hash"], password):
            return None
        db.execute(
            "UPDATE users SET last_login_at = datetime('now') WHERE id = ?",
            (row["id"],),
        )
        db.commit()
        return User(row)

    @staticmethod
    def create(username, password, role="operator", full_name=None):
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name) "
            "VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), role, full_name),
        )
        db.commit()
