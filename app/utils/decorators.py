"""Auth-related decorators for route protection."""

from functools import wraps

from flask import session, redirect, url_for, request, jsonify

from app.models import User


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "authentication required"}), 401
                return redirect(url_for("auth.login", next=request.path))
            user = User.get_by_id(user_id)
            if user is None or (roles and user.role not in roles):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "insufficient permissions"}), 403
                return redirect(url_for("dashboard.index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.get_by_id(user_id)
