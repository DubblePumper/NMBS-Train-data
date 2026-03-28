"""WSGI entrypoint for production servers (e.g., Gunicorn)."""

from __future__ import annotations

from nmbs_dashboard.app import create_dash_app

app = create_dash_app()
server = app.server
