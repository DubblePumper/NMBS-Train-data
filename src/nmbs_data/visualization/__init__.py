"""
Visualization module for NMBS Train Data

This module provides tools for visualizing train routes, stations, and data.
"""

from .map_visualization import create_realtime_train_routes_map as visualize_train_routes
from .map_visualization import (
    load_station_data,
    load_route_data,
    get_realtime_train_data
)