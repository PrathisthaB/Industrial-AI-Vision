"""Incident report generation, listing, and export routes."""

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    send_from_directory, current_app, Response,
)

from app.utils.decorators import login_required
from app.models import IncidentReport, Violation
from app.services import report_service

bp = Blueprint("reports", __name__)


@bp.route("/reports")
@login_required
def index():
    reports = report_service.sort_by_severity(IncidentReport.list_all())
    open_violations = Violation.list_filtered(limit=50)
    return render_template("reports.html", reports=reports, open_violations=open_violations)


@bp.route("/reports/generate/<int:violation_id>", methods=["POST"])
@login_required
def generate(violation_id):
    try:
        report = report_service.generate_report_for_violation(
            violation_id, current_app.config["REPORTS_DIR"]
        )
        flash(f"Incident report {report['incident_code']} generated.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("reports.index"))


@bp.route("/reports/<int:report_id>/download")
@login_required
def download(report_id):
    report = IncidentReport.get(report_id)
    if report is None or not report.get("file_path"):
        flash("Report file not found.", "error")
        return redirect(url_for("reports.index"))

    reports_dir = current_app.config["REPORTS_DIR"]
    filename = f"{report['incident_code']}.pdf"
    return send_from_directory(reports_dir, filename, as_attachment=True)


@bp.route("/reports/export.csv")
@login_required
def export_csv():
    violations = Violation.list_filtered(limit=1000)
    csv_text = report_service.export_violations_csv(violations)
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=violations_export.csv"},
    )
