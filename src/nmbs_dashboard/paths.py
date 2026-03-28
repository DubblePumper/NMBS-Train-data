"""Path resolution helpers for the dashboard project."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT_ROOT = PROJECT_ROOT / "examples" / "endpoint_snapshots"


def resolve_snapshot_root() -> Path:
    """Return snapshot root, allowing override through SNAPSHOT_ROOT."""
    custom = os.getenv("SNAPSHOT_ROOT")
    if custom:
        return Path(custom).expanduser().resolve()
    return DEFAULT_SNAPSHOT_ROOT
