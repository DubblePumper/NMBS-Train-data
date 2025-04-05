"""
Data access module for the NMBS API.

This module provides functionality for accessing NMBS train data via the external API.
"""

from .api_client import (
    get_realtime_data,
    get_planning_files_list,
    get_planning_file,
    force_update
)

__all__ = [
    'get_realtime_data',
    'get_planning_files_list',
    'get_planning_file',
    'force_update'
]