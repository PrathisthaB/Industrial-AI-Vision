#!/usr/bin/env python3
"""
Entry point for the AI-Powered Industrial Safety Monitoring Platform.

Usage:
    python run.py                 # development server on http://localhost:5000
    FLASK_ENV=production python run.py

For production deployment, prefer a WSGI server, e.g.:
    gunicorn -w 2 -b 0.0.0.0:8000 'run:app'
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
