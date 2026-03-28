"""Callback registration for dashboard tabs."""

from .export_callbacks import register_export_callbacks
from .train_callbacks import register_train_callbacks

__all__ = ["register_export_callbacks", "register_train_callbacks"]
