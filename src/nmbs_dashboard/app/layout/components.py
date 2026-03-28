"""Reusable layout components."""

from __future__ import annotations

from typing import Any

from dash import html


def metric_card(label: str, value: Any, subtitle: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(label, className="metric-label"),
            html.Div(str(value), className="metric-value"),
            html.Div(subtitle, className="metric-subtitle"),
        ],
        className="metric-card",
    )
