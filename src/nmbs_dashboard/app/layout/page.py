"""Top-level dashboard page layout."""

from __future__ import annotations

from typing import Any, Dict

from dash import dash_table, dcc, html

from .components import metric_card
from ..services.snapshot_loader import endpoint_options, endpoint_status_rows, snapshot_options


def build_layout(repository: Dict[str, Any], train_index: Dict[str, Any]) -> html.Div:
    train_options = train_index.get("train_options", [])
    metrics = train_index.get("metrics", {})

    default_train_id = train_options[0]["value"] if train_options else None
    default_snapshot_id = repository.get("latest_snapshot_id")
    default_endpoint = repository.get("endpoint_names", [None])[0]

    return html.Div(
        [
            html.Div(
                [
                    html.H1("NMBS Export Dashboard"),
                    html.P(
                        "Centrale cockpit op basis van voorbeeld-snapshots in examples/endpoint_snapshots."
                    ),
                ],
                className="hero",
            ),
            html.Div(
                [
                    metric_card("Snapshots", metrics.get("snapshot_count", 0), "in examples/endpoint_snapshots"),
                    metric_card("Treinen", metrics.get("train_count", 0), "geïndexeerd over snapshots"),
                    metric_card("Endpoints (latest)", metrics.get("endpoint_count_latest", 0), "in laatste snapshot"),
                    metric_card("Treinen met vertraging", metrics.get("trains_with_delay", 0), "delay > 0 min"),
                    metric_card(
                        "Treinen met spoorwissels",
                        metrics.get("trains_with_platform_changes", 0),
                        "heuristisch gedetecteerd",
                    ),
                ],
                className="metrics-grid",
            ),
            dcc.Tabs(
                [
                    dcc.Tab(
                        label="Per trein",
                        children=[
                            html.Div(
                                [
                                    html.Label("Kies trein (trip_id):", className="field-label"),
                                    dcc.Dropdown(
                                        id="train-dropdown",
                                        options=train_options,
                                        value=default_train_id,
                                        placeholder="Selecteer een trein",
                                    ),
                                ],
                                className="control-panel",
                            ),
                            html.Div(id="train-summary"),
                            html.Div(
                                [
                                    dcc.Graph(id="delay-graph", className="graph"),
                                    dcc.Graph(id="route-graph", className="graph"),
                                ],
                                className="graph-grid",
                            ),
                            html.Div(
                                [
                                    html.Div("Stops en timing", className="section-title"),
                                    dash_table.DataTable(
                                        id="stops-table",
                                        columns=[
                                            {"name": "Station", "id": "station"},
                                            {"name": "Stop ID", "id": "stop_id"},
                                            {"name": "Spoor", "id": "platform"},
                                            {"name": "Aankomst", "id": "arrival"},
                                            {"name": "Vertrek", "id": "departure"},
                                            {"name": "Vertraging (min)", "id": "delay_min"},
                                            {"name": "Status", "id": "status"},
                                        ],
                                        data=[],
                                        page_size=12,
                                        style_table={"overflowX": "auto"},
                                        style_cell={"textAlign": "left", "padding": "8px"},
                                        style_header={"fontWeight": "bold"},
                                    ),
                                ],
                                className="panel",
                            ),
                            html.Div(id="platform-events", className="panel"),
                        ],
                    ),
                    dcc.Tab(
                        label="Export browser",
                        children=[
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label("Snapshot", className="field-label"),
                                            dcc.Dropdown(
                                                id="snapshot-dropdown",
                                                options=snapshot_options(repository),
                                                value=default_snapshot_id,
                                            ),
                                        ],
                                        className="field-block",
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Endpoint", className="field-label"),
                                            dcc.Dropdown(
                                                id="endpoint-dropdown",
                                                options=endpoint_options(repository, default_snapshot_id),
                                                value=default_endpoint,
                                            ),
                                        ],
                                        className="field-block",
                                    ),
                                ],
                                className="control-panel dual",
                            ),
                            html.Div(
                                [
                                    html.Div("Endpoint status in snapshot", className="section-title"),
                                    dash_table.DataTable(
                                        id="endpoint-table",
                                        columns=[
                                            {"name": "Endpoint", "id": "endpoint"},
                                            {"name": "Status", "id": "status"},
                                            {"name": "OK", "id": "ok"},
                                            {"name": "JSON", "id": "is_json"},
                                            {"name": "Bestand", "id": "file"},
                                        ],
                                        data=endpoint_status_rows(repository, default_snapshot_id),
                                        page_size=12,
                                        style_table={"overflowX": "auto"},
                                        style_cell={"textAlign": "left", "padding": "8px"},
                                        style_header={"fontWeight": "bold"},
                                    ),
                                ],
                                className="panel",
                            ),
                            html.Div(
                                [
                                    html.Div("Raw endpoint JSON", className="section-title"),
                                    html.Pre(id="endpoint-json", className="json-preview"),
                                ],
                                className="panel",
                            ),
                        ],
                    ),
                ]
            ),
        ],
        className="dashboard-shell",
    )
