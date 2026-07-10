"""Application factory — wires config, database, and blueprints together."""

from pathlib import Path

from flask import Flask

from app.config import get_config
from app.database import register_db


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Ensure runtime directories exist before anything tries to write to them.
    for key in ("VIOLATIONS_DIR", "REPORTS_DIR", "UPLOAD_DIR"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True) \
        if app.config["DATABASE_PATH"] != ":memory:" else None

    register_db(app)
    _register_blueprints(app)
    _register_template_helpers(app)

    return app


def _register_blueprints(app):
    from app.routes import main, auth, dashboard, violations, analytics, reports, upload, stream, api

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(violations.bp)
    app.register_blueprint(analytics.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(stream.bp)
    app.register_blueprint(api.bp)


def _register_template_helpers(app):
    @app.context_processor
    def inject_globals():
        return {"app_name": "Industrial AI Vision"}
