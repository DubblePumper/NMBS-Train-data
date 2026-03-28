"""Callbacks for snapshot + endpoint browsing tab."""

from __future__ import annotations

from typing import Any, Dict

from dash import Dash, Input, Output

from ..services.snapshot_loader import (
    endpoint_options,
    endpoint_status_rows,
    get_endpoint_payload,
    render_json_preview,
)


def register_export_callbacks(app: Dash, repository: Dict[str, Any]) -> None:
    @app.callback(
        Output("endpoint-dropdown", "options"),
        Output("endpoint-dropdown", "value"),
        Output("endpoint-table", "data"),
        Input("snapshot-dropdown", "value"),
    )
    def update_endpoint_selector(snapshot_id: str):
        options = endpoint_options(repository, snapshot_id)
        value = options[0]["value"] if options else None
        rows = endpoint_status_rows(repository, snapshot_id)
        return options, value, rows

    @app.callback(
        Output("endpoint-json", "children"),
        Input("snapshot-dropdown", "value"),
        Input("endpoint-dropdown", "value"),
    )
    def update_endpoint_preview(snapshot_id: str, endpoint_name: str):
        payload = get_endpoint_payload(repository, snapshot_id, endpoint_name)
        if payload is None:
            return "Geen payload gevonden voor deze combinatie van snapshot en endpoint."
        return render_json_preview(payload)
