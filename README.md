# NMBS Train Data Analysis

A package for analyzing, visualizing, and exploring NMBS (Belgian Railways) train data, including schedule information and real-time updates.

## Project Structure

The project has been structured as a proper Python package:

```
nmbs-train-data/
│
├── requirements.txt        # Project dependencies
├── setup.py               # Package configuration
├── main.py                # Main entry point
│
├── src/                   # Source code package
│   └── nmbs_data/         # Main package
│       ├── data/          # Data access layer
│       ├── analysis/      # Analysis components
│       ├── visualization/ # Visualization components
│       └── webapp/        # Web application
│
├── data/                  # Data directory
│   ├── Planningsgegevens/  # Planning data
│   ├── Real-time_gegevens/ # Real-time data
│   └── Maps/              # Generated maps
│
├── docs/                  # Documentation
│
└── tests/                 # Test suite
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NMBS-Train-data.git
cd NMBS-Train-data
```

2. Install the package and dependencies:
```bash
pip install -e .
```

## Usage

### Running Everything (Analysis, Visualization, and Web App)

```bash
python main.py all
```

You can also use the `--light` flag to use light mode for the visualization:

```bash
python main.py all --light
```

### Running the Web Application

```bash
python main.py webapp
```

### Running the Data Analysis Only

```bash
python main.py analyze
```

### Generating a Map Visualization

```bash
python main.py visualize
```

You can use the `--light` flag for a light-mode visualization:

```bash
python main.py visualize --light
```

## Data Sources

The application works with the following data sources:

1. **Planning Data**: GTFS, NeTEx, and other schedule formats from NMBS/SNCB
2. **Real-time Data**: GTFS-RT format data accessed via our API endpoint

## Real-time Data Access

This application connects to our dedicated API endpoint at `http://185.228.81.219:25580/api/data` to fetch the latest NMBS train data. The API service runs separately and provides real-time GTFS data, which this application then processes, analyzes, and visualizes.

### Data Format

The API returns data in the standard GTFS Realtime format, containing information about:
- Trip updates
- Schedule changes
- Platform information
- Delay information

## Development

### Running Tests

```bash
pytest tests/
```

### Package Structure

- **data**: Handles data access via the API endpoint and manages file paths
- **analysis**: Contains data processing and analysis logic
- **visualization**: Manages map creation and visualizations
- **webapp**: Contains the Dash web application components

## Services

The application includes a service component that can be run to periodically fetch data from the API:

```bash
python service.py
```

This will download data at regular intervals and store it for offline access.

## License

[Specify your license here]
