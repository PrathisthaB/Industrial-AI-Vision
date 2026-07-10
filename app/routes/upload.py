"""Video upload endpoint — accepts CCTV/recorded footage for offline processing."""

import uuid
from pathlib import Path

from flask import Blueprint, request, redirect, url_for, flash, current_app, jsonify

from app.utils.decorators import login_required
from app.utils.helpers import allowed_video_file
from app.models import Camera

bp = Blueprint("upload", __name__)


@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_page():
    if request.method == "GET":
        return redirect(url_for("dashboard.index"))
    return _handle_upload()


def _handle_upload():
    file = request.files.get("video")
    if file is None or file.filename == "":
        flash("No video file selected.", "error")
        return redirect(url_for("dashboard.index"))

    if not allowed_video_file(file.filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
        flash("Unsupported video format. Use mp4, avi, mov, or mkv.", "error")
        return redirect(url_for("dashboard.index"))

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:10]}_{file.filename}"
    dest = upload_dir / safe_name
    file.save(dest)

    camera_id = Camera.create(
        name=request.form.get("camera_name") or f"Uploaded: {file.filename}",
        location=request.form.get("location") or "Uploaded Footage",
        source_type="upload",
        source_path=str(dest),
    )

    flash(f"Video uploaded. Open the live feed to begin detection.", "success")
    return redirect(url_for("dashboard.index", camera_id=camera_id))
