"""Public marketing / landing page routes."""

from flask import Blueprint, render_template, redirect, url_for, session

bp = Blueprint("main", __name__)


@bp.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")


@bp.route("/health")
def health():
    return {"status": "ok", "service": "industrial-ai-vision"}
