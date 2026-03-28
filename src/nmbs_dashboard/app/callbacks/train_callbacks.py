"""Callbacks for the train-centric dashboard tab."""

from __future__ import annotations

from typing import Any, Dict, List

import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 14},
    )
    return fig


def _build_delay_figure(train: Dict[str, Any]) -> go.Figure:
    history = train.get("delay_history", [])
    if not history:
        return _empty_figure("Vertraging doorheen snapshots", "Geen vertragingdata beschikbaar.")

    x = [item.get("observed_at") for item in history]
    y = [item.get("delay_minutes", 0) for item in history]
    source = [item.get("source", "unknown") for item in history]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line={"color": "#33a1ff", "width": 2},
                marker={"size": 7, "color": "#9ad0ff"},
                text=source,
                hovertemplate="Snapshot: %{x}<br>Vertraging: %{y} min<br>Bron: %{text}<extra></extra>",
                name="vertraging",
            )
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        title="Vertraging doorheen snapshots",
        xaxis_title="Snapshot",
        yaxis_title="Vertraging (min)",
        margin={"l": 50, "r": 20, "t": 60, "b": 50},
    )
    return fig


def _build_route_figure(train: Dict[str, Any]) -> go.Figure:
    trajectories = train.get("trajectory_updates", [])
    if not trajectories:
        return _empty_figure("Traject", "Geen trajectdata beschikbaar voor deze trein.")

    latest = trajectories[-1]
    stops = latest.get("stops", [])
    valid_stops = [stop for stop in stops if stop.get("lat") is not None and stop.get("lon") is not None]

    if len(valid_stops) < 2:
        return _empty_figure("Traject", "Onvoldoende coördinaten om een traject te tonen.")

    fig = go.Figure()
    fig.add_trace(
        go.Scattergeo(
            lat=[stop["lat"] for stop in valid_stops],
            lon=[stop["lon"] for stop in valid_stops],
            mode="lines+markers",
            line={"width": 3, "color": "#58d68d"},
            marker={"size": 8, "color": "#ecf0f1"},
            text=[
                f"{stop.get('station_name') or 'Onbekend station'}<br>{stop.get('stop_id')}<br>Delay: {round(stop.get('delay_seconds', 0)/60, 2)} min"
                for stop in valid_stops
            ],
            hovertemplate="%{text}<extra></extra>",
            name="stops",
        )
    )

    current = train.get("current_position", {})
    if current.get("lat") is not None and current.get("lon") is not None:
        current_label = (
            f"Huidige positie<br>{current.get('current_station') or 'Onbekend'}"
            f"<br>Volgende: {current.get('next_station') or '-'}"
            f"<br>Status: {current.get('status') or '-'}"
            f"<br>Vertraging: {current.get('delay_minutes', 0)} min"
        )
        fig.add_trace(
            go.Scattergeo(
                lat=[current.get("lat")],
                lon=[current.get("lon")],
                mode="markers",
                marker={"size": 14, "color": "#ff6b6b", "symbol": "diamond"},
                text=[current_label],
                hovertemplate="%{text}<extra></extra>",
                name="huidige positie",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        title="Trajectkaart per trein",
        geo={
            "scope": "europe",
            "projection_type": "mercator",
            "center": {"lat": 50.7, "lon": 4.4},
            "lataxis": {"range": [48.5, 52.5]},
            "lonaxis": {"range": [1.5, 7.5]},
            "showland": True,
            "landcolor": "#1f2b3a",
            "showocean": True,
            "oceancolor": "#0f1722",
            "countrycolor": "#3b4d63",
        },
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
        legend={"orientation": "h"},
    )
    return fig


def _build_summary(train: Dict[str, Any]) -> html.Div:
    route = train.get("route", {})
    trip = train.get("trip", {})
    current = train.get("current_position", {})

    return html.Div(
        [
            html.Div(
                [
                    html.H3("Treinprofiel"),
                    html.P(f"Trip ID: {train.get('trip_id') or '-'}"),
                    html.P(f"Treinnummer: {train.get('trip_number') or '-'}"),
                    html.P(f"Route: {route.get('route_name') or '-'}"),
                    html.P(f"Route type: {route.get('route_type') or '-'}"),
                    html.P(f"Richting: {trip.get('trip_headsign') or '-'}"),
                ],
                className="panel",
            ),
            html.Div(
                [
                    html.H3("Huidige status"),
                    html.P(f"Status: {current.get('status') or '-'}"),
                    html.P(f"Huidig station: {current.get('current_station') or '-'}"),
                    html.P(f"Volgend station: {current.get('next_station') or '-'}"),
                    html.P(f"Vertraging: {current.get('delay_minutes', 0)} min"),
                    html.P(f"Laatste observatie: {current.get('observed_at') or '-'}"),
                ],
                className="panel",
            ),
        ],
        className="panel-grid",
    )


def _build_stop_rows(train: Dict[str, Any]) -> List[Dict[str, Any]]:
    trajectories = train.get("trajectory_updates", [])
    if trajectories:
        rows: List[Dict[str, Any]] = []
        for stop in trajectories[-1].get("stops", []):
            rows.append(
                {
                    "station": stop.get("station_name"),
                    "stop_id": stop.get("stop_id"),
                    "platform": stop.get("platform") or "-",
                    "arrival": stop.get("arrival_datetime") or "-",
                    "departure": stop.get("departure_datetime") or "-",
                    "delay_min": round((stop.get("delay_seconds") or 0) / 60, 2),
                    "status": stop.get("status") or "-",
                }
            )
        return rows

    realtime = train.get("realtime_updates", [])
    if realtime:
        rows = []
        for stop in realtime[-1].get("stop_updates", []):
            rows.append(
                {
                    "station": train.get("known_stops", {}).get(stop.get("base_stop_id")) or "-",
                    "stop_id": stop.get("stop_id"),
                    "platform": stop.get("platform") or "-",
                    "arrival": stop.get("arrival_time") or "-",
                    "departure": stop.get("departure_time") or "-",
                    "delay_min": round((stop.get("delay_seconds") or 0) / 60, 2),
                    "status": stop.get("schedule_relationship") or "-",
                }
            )
        return rows

    return []


def _build_platform_block(train: Dict[str, Any]) -> html.Div:
    platform_changes = train.get("platform_changes", [])
    skipped = train.get("skipped_stops", [])
    if not platform_changes and not skipped:
        return html.Div("Geen spoorwissels of skip-events gedetecteerd.", className="note note-ok")

    items: List[html.Li] = []
    for change in platform_changes[:50]:
        station = train.get("known_stops", {}).get(change.get("base_stop_id"), change.get("base_stop_id"))
        items.append(
            html.Li(
                f"[{change.get('observed_at')}] {station}: spoor {change.get('old_platform')} → {change.get('new_platform')}"
            )
        )

    for skip in skipped[:50]:
        station = train.get("known_stops", {}).get(skip.get("base_stop_id"), skip.get("base_stop_id"))
        items.append(html.Li(f"[{skip.get('observed_at')}] overgeslagen halte: {station}"))

    return html.Div([html.Div("Spoorwijzigingen en verstoringen", className="section-title"), html.Ul(items, className="event-list")])


def register_train_callbacks(app: Dash, train_index: Dict[str, Any]) -> None:
    trains = train_index.get("trains", {})

    @app.callback(
        Output("train-summary", "children"),
        Output("delay-graph", "figure"),
        Output("route-graph", "figure"),
        Output("stops-table", "data"),
        Output("platform-events", "children"),
        Input("train-dropdown", "value"),
    )
    def update_train_tab(train_id: str):
        train = trains.get(train_id)
        if not train:
            empty = _empty_figure("Geen data", "Selecteer een trein om details te zien.")
            return html.Div("Geen trein geselecteerd."), empty, empty, [], html.Div("-")

        return (
            _build_summary(train),
            _build_delay_figure(train),
            _build_route_figure(train),
            _build_stop_rows(train),
            _build_platform_block(train),
        )
