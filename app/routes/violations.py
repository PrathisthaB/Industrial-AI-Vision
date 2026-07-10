"""Evidence gallery: browse and filter violation screenshots."""

from flask import Blueprint, render_template, request, send_from_directory, current_app

from app.utils.decorators import login_required
from app.models import Violation

bp = Blueprint("violations", __name__)


@bp.route("/violations")
@login_required
def gallery():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    violation_type = request.args.get("type") or None
    min_confidence = request.args.get("min_confidence", type=float)

    violations = Violation.list_filtered(
        date_from=date_from,
        date_to=date_to,
        violation_type=violation_type,
        min_confidence=min_confidence,
        limit=100,
    )

    return render_template(
        "violations.html",
        violations=violations,
        filters={
            "date_from": date_from or "",
            "date_to": date_to or "",
            "type": violation_type or "",
            "min_confidence": min_confidence or "",
        },
    )


@bp.route("/evidence/<path:filename>")
@login_required
def evidence_file(filename):
    """Serve a saved violation screenshot from the violations directory."""
    violations_dir = current_app.config["VIOLATIONS_DIR"]
    return send_from_directory(violations_dir, filename)
