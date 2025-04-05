"""
NMBS API - A Python library for accessing NMBS (Belgian Railways) train data

This module provides functions for accessing real-time and planning data 
from the NMBS/SNCB train service via an external API.
"""

from .data.api_client import (
    get_realtime_data,
    get_planning_files_list,
    get_planning_file,
    force_update
)

__version__ = "0.1.0"
__all__ = [
    'get_realtime_data',
    'get_planning_files_list',
    'get_planning_file',
    'force_update'
]