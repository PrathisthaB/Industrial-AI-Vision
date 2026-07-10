"""Camera model — represents a webcam, uploaded video, or CCTV stream source."""

from app.database import get_db


class Camera:
    @staticmethod
    def list_all(active_only=False):
        db = get_db()
        query = "SELECT * FROM cameras"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY id"
        return [dict(row) for row in db.execute(query).fetchall()]

    @staticmethod
    def get(camera_id):
        row = get_db().execute(
            "SELECT * FROM cameras WHERE id = ?", (camera_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name, location, source_type, source_path):
        db = get_db()
        cur = db.execute(
            "INSERT INTO cameras (name, location, source_type, source_path) "
            "VALUES (?, ?, ?, ?)",
            (name, location, source_type, source_path),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def count_active():
        row = get_db().execute(
            "SELECT COUNT(*) AS c FROM cameras WHERE is_active = 1"
        ).fetchone()
        return row["c"] if row else 0

    @staticmethod
    def set_active(camera_id, active):
        db = get_db()
        db.execute(
            "UPDATE cameras SET is_active = ? WHERE id = ?",
            (1 if active else 0, camera_id),
        )
        db.commit()
