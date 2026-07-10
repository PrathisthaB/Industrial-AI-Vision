"""Protected dashboard page routes (server-rendered; data refreshed via REST API)."""

from flask import Blueprint, render_template, session

from app.utils.decorators import login_required
from app.services import analytics_service
from app.models import Camera

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def index():
    summary = analytics_service.dashboard_summary()
    cameras = Camera.list_all()
    return render_template(
        "dashboard.html",
        summary=summary,
        cameras=cameras,
        username=session.get("username"),
        role=session.get("role"),
    )
