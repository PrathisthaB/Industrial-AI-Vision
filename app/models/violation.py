"""Violation model — persistence for PPE non-compliance events."""

import json

from app.database import get_db


class Violation:
    @staticmethod
    def create(
        violation_type,
        confidence,
        severity,
        screenshot_path,
        compliance_score,
        worker_bbox,
        camera_id=None,
        session_id=None,
    ):
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO violations
                (session_id, camera_id, violation_type, confidence, severity,
                 screenshot_path, compliance_score, worker_bbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                camera_id,
                violation_type,
                confidence,
                severity,
                screenshot_path,
                compliance_score,
                json.dumps(worker_bbox) if worker_bbox is not None else None,
            ),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def get(violation_id):
        row = get_db().execute(
            "SELECT * FROM violations WHERE id = ?", (violation_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_filtered(
        date_from=None,
        date_to=None,
        violation_type=None,
        min_confidence=None,
        camera_id=None,
        limit=200,
        offset=0,
    ):
        db = get_db()
        clauses = []
        params = []

        if date_from:
            clauses.append("date(timestamp) >= date(?)")
            params.append(date_from)
        if date_to:
            clauses.append("date(timestamp) <= date(?)")
            params.append(date_to)
        if violation_type:
            clauses.append("violation_type = ?")
            params.append(violation_type)
        if min_confidence is not None:
            clauses.append("confidence >= ?")
            params.append(min_confidence)
        if camera_id:
            clauses.append("camera_id = ?")
            params.append(camera_id)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = (
            f"SELECT * FROM violations {where} "
            f"ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])
        rows = db.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def count_today():
        row = get_db().execute(
            "SELECT COUNT(*) AS c FROM violations WHERE date(timestamp) = date('now')"
        ).fetchone()
        return row["c"] if row else 0

    @staticmethod
    def recent(limit=10):
        rows = get_db().execute(
            "SELECT * FROM violations ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def counts_by_type(date_from=None, date_to=None):
        db = get_db()
        clauses = []
        params = []
        if date_from:
            clauses.append("date(timestamp) >= date(?)")
            params.append(date_from)
        if date_to:
            clauses.append("date(timestamp) <= date(?)")
            params.append(date_to)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = db.execute(
            f"SELECT violation_type, COUNT(*) AS c FROM violations {where} "
            f"GROUP BY violation_type",
            params,
        ).fetchall()
        return {r["violation_type"]: r["c"] for r in rows}

    @staticmethod
    def counts_by_day(days=30):
        rows = get_db().execute(
            """
            SELECT date(timestamp) AS day, COUNT(*) AS c
            FROM violations
            WHERE date(timestamp) >= date('now', ?)
            GROUP BY day
            ORDER BY day
            """,
            (f"-{days} days",),
        ).fetchall()
        return [{"day": r["day"], "count": r["c"]} for r in rows]

    @staticmethod
    def update_status(violation_id, status):
        db = get_db()
        db.execute(
            "UPDATE violations SET status = ? WHERE id = ?", (status, violation_id)
        )
        db.commit()
