# NMBS Data Package API Overview

This document provides an overview of the key modules and functions in the NMBS Data package.

## Data Module

The `nmbs_data.data` module provides utilities for accessing and managing data files.

### data_paths

```python
from nmbs_data.data import ensure_directories, get_realtime_dirs, clean_realtime_dirs
```

- `ensure_directories()` - Creates the necessary data directories if they don't exist and returns paths
- `get_realtime_dirs()` - Returns a list of paths to real-time data directories
- `clean_realtime_dirs()` - Removes sample files from real-time data directories

### gtfs_realtime_reader

```python
from nmbs_data.data import read_specific_realtime_files, extract_vehicle_positions, create_sample_files
```

- `read_specific_realtime_files()` - Reads real-time data files and parses their contents
- `extract_vehicle_positions(data)` - Extracts vehicle position information from parsed real-time data
- `create_sample_files(...)` - Creates sample real-time data files for testing and demonstration

## Analysis Module

The `nmbs_data.analysis` module provides tools for analyzing train data.

### train_data_overview

```python
from nmbs_data.analysis import TrainDataAnalyzer
```

- `TrainDataAnalyzer` - A class that analyzes GTFS, NeTEx, and real-time data files:
  - `load_planning_data()` - Loads and analyzes planning data files (GTFS, NeTEx)
  - `load_realtime_data()` - Loads and analyzes real-time data files
  - `generate_overview()` - Generates a comprehensive overview of all data
  - `save_overview(data)` - Saves the overview data to a JSON file

## Visualization Module

The `nmbs_data.visualization` module provides tools for visualizing train data.

### map_visualization

```python
from nmbs_data.visualization import visualize_train_routes
```

- `visualize_train_routes(...)` - Creates an interactive map of train routes:
  - Parameters:
    - `gtfs_file` - Path to a GTFS file (optional)
    - `routes_file` - Path to a routes file (optional)
    - `stations_file` - Path to a stations file (optional)
    - `output_file` - Name of the output HTML file (optional)
    - `include_realtime` - Whether to include real-time data (default: True)
    - `dark_mode` - Whether to use dark mode theme (default: False)
  - Returns: Path to the generated map file

## Web Application Module

The `nmbs_data.webapp` module provides a Dash web application for interactive exploration of the train data.

### app

```python
from nmbs_data.webapp import app, server
```

- `app` - The Dash application instance
- `server` - The Flask server instance (for WSGI deployment)

## Command-line Interface

The package provides a command-line interface through the main entry point:

```bash
# Run the web application
python main.py webapp

# Run data analysis only
python main.py analyze

# Generate a train route map
python main.py visualize

# Generate a map with light mode theme
python main.py visualize --light
```