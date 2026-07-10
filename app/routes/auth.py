"""Login / logout routes. Session-based auth protecting all dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.verify_credentials(username, password)
        if user is None:
            flash("Invalid username or password.", "error")
            return render_template("login.html", username=username), 401

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        session.permanent = True

        next_url = request.args.get("next") or url_for("dashboard.index")
        return redirect(next_url)

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))
