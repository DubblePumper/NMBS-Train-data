"""Tests for dashboard pipeline over examples snapshot data."""

from pathlib import Path

from nmbs_dashboard.app.services.snapshot_loader import get_endpoint_payload, load_snapshot_repository
from nmbs_dashboard.app.services.train_model import build_train_index


def test_repository_loads_examples_snapshots() -> None:
    project_root = Path(__file__).resolve().parents[1]
    snapshot_root = project_root / "examples" / "endpoint_snapshots"

    repository = load_snapshot_repository(snapshot_root)

    assert repository["snapshot_count"] >= 1
    assert repository["latest_snapshot_id"] is not None
    assert "realtime" in repository["endpoint_names"]
    assert "trajectories" in repository["endpoint_names"]


def test_train_index_is_built() -> None:
    project_root = Path(__file__).resolve().parents[1]
    snapshot_root = project_root / "examples" / "endpoint_snapshots"

    repository = load_snapshot_repository(snapshot_root)
    index = build_train_index(repository)

    assert index["metrics"]["snapshot_count"] == repository["snapshot_count"]
    assert index["metrics"]["train_count"] > 0
    assert len(index["train_options"]) == index["metrics"]["train_count"]


def test_latest_realtime_payload_is_available() -> None:
    project_root = Path(__file__).resolve().parents[1]
    snapshot_root = project_root / "examples" / "endpoint_snapshots"

    repository = load_snapshot_repository(snapshot_root)
    snapshot_id = repository["latest_snapshot_id"]

    payload = get_endpoint_payload(repository, snapshot_id, "realtime")
    assert payload is not None
    assert payload.get("name") == "realtime"
