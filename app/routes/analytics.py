"""Analytics dashboard page (daily/weekly/monthly trends + compliance charts)."""

from flask import Blueprint, render_template

from app.utils.decorators import login_required
from app.services import analytics_service

bp = Blueprint("analytics", __name__)


@bp.route("/analytics")
@login_required
def index():
    return render_template(
        "analytics.html",
        daily=analytics_service.trend_series(days=30),
        weekly=analytics_service.weekly_series(weeks=12),
        monthly=analytics_service.monthly_series(months=12),
        compliance_trend=analytics_service.compliance_trend(days=14),
        breakdown=analytics_service.violation_type_breakdown(),
    )
