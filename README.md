# NMBS Train Data Analysis

A package for analyzing, visualizing, and exploring NMBS (Belgian Railways) train data, including schedule information and real-time updates.

## Project Structure

The project has been restructured as a proper Python package:

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
git clone <repository-url>
cd NMBS-Train-data
```

2. Install the package and dependencies:
```bash
pip install -e .
```

## Usage

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

## Data Sources

The application works with the following data sources:

1. **Planning Data**: GTFS, NeTEx, and other schedule formats from NMBS/SNCB
2. **Real-time Data**: GTFS-RT format data with and without platform changes

## Development

### Running Tests

```bash
pytest tests/
```

### Package Structure

- **data**: Handles data access and file paths
- **analysis**: Contains data processing and analysis logic
- **visualization**: Manages map creation and visualizations
- **webapp**: Contains the Dash web application components

## License

[Specify your license here]
