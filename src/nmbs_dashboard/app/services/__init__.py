"""Data services for dashboard ingestion and indexing."""

from .snapshot_loader import load_snapshot_repository
from .train_model import build_train_index

__all__ = ["load_snapshot_repository", "build_train_index"]
