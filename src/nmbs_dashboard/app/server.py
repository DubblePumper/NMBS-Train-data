"""Application factory for the NMBS export dashboard."""

from __future__ import annotations

from pathlib import Path

from dash import Dash

from ..paths import resolve_snapshot_root
from .callbacks import register_export_callbacks, register_train_callbacks
from .layout import build_layout
from .services import build_train_index, load_snapshot_repository


def create_dash_app(snapshot_root: Path | None = None) -> Dash:
    root = snapshot_root or resolve_snapshot_root()
    repository = load_snapshot_repository(root)
    train_index = build_train_index(repository)

    app = Dash(
        __name__,
        title="NMBS Export Dashboard",
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )
    app.layout = build_layout(repository, train_index)

    register_train_callbacks(app, train_index)
    register_export_callbacks(app, repository)
    return app
