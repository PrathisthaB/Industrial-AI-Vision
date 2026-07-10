"""
REST API — clean JSON endpoints consumed by the dashboard's JS and available
for external integration (e.g. a mobile app or a third-party EHS system).

Endpoints:
    GET  /api/dashboard        summary cards (violations today, compliance %, etc.)
    GET  /api/violations       filterable violation list
    GET  /api/analytics        daily/weekly/monthly trend + compliance data
    GET  /api/reports          generated incident reports
    POST /api/upload           upload a video/CCTV clip for processing
    GET  /api/cameras          list configured camera sources
    POST /api/cameras          register a new camera / CCTV stream
"""

from pathlib import Path
import uuid

from flask import Blueprint, request, jsonify, current_app

from app.utils.decorators import login_required
from app.utils.helpers import allowed_video_file, paginate_args
from app.models import Violation, Camera, IncidentReport
from app.services import analytics_service, report_service

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/dashboard")
@login_required
def dashboard():
    return jsonify(analytics_service.dashboard_summary())


@bp.route("/violations")
@login_required
def violations():
    limit, offset = paginate_args(request)
    rows = Violation.list_filtered(
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
        violation_type=request.args.get("type"),
        min_confidence=request.args.get("min_confidence", type=float),
        camera_id=request.args.get("camera_id", type=int),
        limit=limit,
        offset=offset,
    )
    return jsonify({"count": len(rows), "results": rows})


@bp.route("/violations/<int:violation_id>")
@login_required
def violation_detail(violation_id):
    row = Violation.get(violation_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(row)


@bp.route("/violations/<int:violation_id>/status", methods=["POST"])
@login_required
def update_violation_status(violation_id):
    status = request.json.get("status") if request.is_json else request.form.get("status")
    if status not in ("open", "reviewed", "resolved"):
        return jsonify({"error": "invalid status"}), 400
    Violation.update_status(violation_id, status)
    return jsonify({"ok": True, "id": violation_id, "status": status})


@bp.route("/analytics")
@login_required
def analytics():
    days = request.args.get("days", default=30, type=int)
    return jsonify({
        "daily": analytics_service.trend_series(days=days),
        "weekly": analytics_service.weekly_series(weeks=12),
        "monthly": analytics_service.monthly_series(months=12),
        "compliance_trend": analytics_service.compliance_trend(days=14),
        "breakdown": analytics_service.violation_type_breakdown(),
    })


@bp.route("/reports")
@login_required
def reports():
    return jsonify({"results": IncidentReport.list_all()})


@bp.route("/reports/<int:violation_id>/generate", methods=["POST"])
@login_required
def generate_report(violation_id):
    try:
        report = report_service.generate_report_for_violation(
            violation_id, current_app.config["REPORTS_DIR"]
        )
        return jsonify(report), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404


@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("video")
    if file is None or file.filename == "":
        return jsonify({"error": "no video file provided"}), 400

    if not allowed_video_file(file.filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
        return jsonify({"error": "unsupported video format"}), 400

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

    return jsonify({
        "ok": True,
        "camera_id": camera_id,
        "stream_url": f"/stream/{camera_id}",
    }), 201


@bp.route("/cameras")
@login_required
def cameras():
    return jsonify({"results": Camera.list_all()})


@bp.route("/cameras", methods=["POST"])
@login_required
def add_camera():
    payload = request.get_json(silent=True) or request.form
    name = payload.get("name")
    source_type = payload.get("source_type", "cctv")
    source_path = payload.get("source_path")

    if not name or not source_path:
        return jsonify({"error": "name and source_path are required"}), 400

    camera_id = Camera.create(
        name=name,
        location=payload.get("location", ""),
        source_type=source_type,
        source_path=source_path,
    )
    return jsonify({"ok": True, "camera_id": camera_id}), 201
