"""Session, IncidentReport, and DailyStats models."""

from app.database import get_db


class Session:
    @staticmethod
    def start(source_type, source_label, camera_id=None):
        db = get_db()
        cur = db.execute(
            "INSERT INTO sessions (camera_id, source_type, source_label) "
            "VALUES (?, ?, ?)",
            (camera_id, source_type, source_label),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def update_progress(session_id, frames_processed, workers_detected):
        db = get_db()
        db.execute(
            "UPDATE sessions SET frames_processed = ?, workers_detected = ? "
            "WHERE id = ?",
            (frames_processed, workers_detected, session_id),
        )
        db.commit()

    @staticmethod
    def finish(session_id, status="completed"):
        db = get_db()
        db.execute(
            "UPDATE sessions SET status = ?, ended_at = datetime('now') WHERE id = ?",
            (status, session_id),
        )
        db.commit()

    @staticmethod
    def get(session_id):
        row = get_db().execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def total_workers_today():
        row = get_db().execute(
            "SELECT COALESCE(SUM(workers_detected), 0) AS c FROM sessions "
            "WHERE date(started_at) = date('now')"
        ).fetchone()
        return row["c"] if row else 0


class IncidentReport:
    @staticmethod
    def create(incident_code, violation_id, severity, recommended_action, file_path=None):
        db = get_db()
        cur = db.execute(
            "INSERT INTO incident_reports "
            "(incident_code, violation_id, severity, recommended_action, file_path) "
            "VALUES (?, ?, ?, ?, ?)",
            (incident_code, violation_id, severity, recommended_action, file_path),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def list_all(limit=100):
        rows = get_db().execute(
            """
            SELECT ir.*, v.violation_type, v.confidence, v.timestamp AS violation_time,
                   v.screenshot_path
            FROM incident_reports ir
            JOIN violations v ON v.id = ir.violation_id
            ORDER BY ir.generated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(report_id):
        row = get_db().execute(
            """
            SELECT ir.*, v.violation_type, v.confidence, v.timestamp AS violation_time,
                   v.screenshot_path
            FROM incident_reports ir
            JOIN violations v ON v.id = ir.violation_id
            WHERE ir.id = ?
            """,
            (report_id,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def set_file_path(report_id, file_path):
        db = get_db()
        db.execute(
            "UPDATE incident_reports SET file_path = ? WHERE id = ?",
            (file_path, report_id),
        )
        db.commit()


class DailyStats:
    @staticmethod
    def upsert(date, **fields):
        db = get_db()
        existing = db.execute(
            "SELECT date FROM daily_stats WHERE date = ?", (date,)
        ).fetchone()
        if existing:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            db.execute(
                f"UPDATE daily_stats SET {set_clause} WHERE date = ?",
                (*fields.values(), date),
            )
        else:
            cols = ", ".join(["date", *fields.keys()])
            placeholders = ", ".join(["?"] * (len(fields) + 1))
            db.execute(
                f"INSERT INTO daily_stats ({cols}) VALUES ({placeholders})",
                (date, *fields.values()),
            )
        db.commit()

    @staticmethod
    def range(days=30):
        rows = get_db().execute(
            "SELECT * FROM daily_stats WHERE date >= date('now', ?) ORDER BY date",
            (f"-{days} days",),
        ).fetchall()
        return [dict(r) for r in rows]
