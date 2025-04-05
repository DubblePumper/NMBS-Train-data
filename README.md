# NMBS Treingegevens Analyse | Vibe Coding

<div align="center">

![NMBS/SNCB Logo](https://img.shields.io/badge/NMBS%2FSNCB-Analysis-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-0.1.0-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

</div>

*[English version below](#nmbs-train-data-analysis--vibe-coding-1)*

Een pakket voor het analyseren, visualiseren en verkennen van NMBS (Belgische Spoorwegen) treingegevens, inclusief dienstregelingen en realtime updates.

> 🔗 Dit project maakt gebruik van onze dedicated API: [NMBS-Train-data-API](https://github.com/DubblePumper/NMBS-Train-data-API)

## 📋 Inhoudsopgave
- [Kenmerken](#-kenmerken)
- [Projectstructuur](#-projectstructuur)
- [Installatie](#-installatie)
- [Gebruik](#-gebruik)
  - [Alles Uitvoeren](#alles-uitvoeren-analyse-visualisatie-en-web-app)
  - [De Webapplicatie Uitvoeren](#de-webapplicatie-uitvoeren)
  - [Alleen de Gegevensanalyse Uitvoeren](#alleen-de-gegevensanalyse-uitvoeren)
  - [Een Kaartvisualisatie Genereren](#een-kaartvisualisatie-genereren)
- [Gegevensbronnen](#-gegevensbronnen)
- [Realtime Gegevenstoegang](#-realtime-gegevenstoegang)
- [Pakketstructuur](#-pakketstructuur)
- [API Endpoints](#-api-endpoints)
- [Licentie](#-licentie)

## ✨ Kenmerken

- Analyseert NMBS treingegevens om patronen en trends te ontdekken
- Visualiseert treinroutes op interactieve kaarten
- Verwerkt zowel statische planningsgegevens als realtime updates
- Biedt een interactieve webapplicatie voor gegevensverkenning
- Ondersteunt lichte en donkere modus voor visualisaties
- Automatische gegevensverwerking en analyse
- Integreert met onze realtime NMBS API voor up-to-date informatie

## 📂 Projectstructuur

Het project is gestructureerd als een volwaardig Python-pakket:

```
nmbs-train-data/
│
├── requirements.txt        # Projectafhankelijkheden
├── setup.py                # Pakketconfiguratie
├── main.py                 # Hoofdingangspunt
│
├── src/                    # Broncodepakket
│   └── nmbs_data/          # Hoofdpakket
│       ├── data/           # Gegevenstoegangslaag
│       ├── analysis/       # Analysecomponenten
│       ├── visualization/  # Visualisatiecomponenten
│       └── webapp/         # Webapplicatie
│
├── docs/                   # Documentatie
│
└── tests/                  # Testsuites
```

## 🚀 Installatie

1. Kloon de repository:
```bash
git clone https://github.com/yourusername/NMBS-Train-data.git
cd NMBS-Train-data
```

2. Installeer het pakket en de afhankelijkheden:
```bash
pip install -e .
```

## 🔧 Gebruik

### Alles Uitvoeren (Analyse, Visualisatie en Web App)

```bash
python main.py all
```

Je kunt ook de `--light` vlag gebruiken voor een visualisatie in lichte modus:

```bash
python main.py all --light
```

### De Webapplicatie Uitvoeren

```bash
python main.py webapp
```

### Alleen de Gegevensanalyse Uitvoeren

```bash
python main.py analyze
```

### Een Kaartvisualisatie Genereren

```bash
python main.py visualize
```

Je kunt de `--light` vlag gebruiken voor een visualisatie in lichte modus:

```bash
python main.py visualize --light
```

## 📊 Gegevensbronnen

De applicatie werkt met de volgende gegevensbronnen:

1. **Planningsgegevens**: GTFS, NeTEx en andere dienstregeling-formaten van NMBS/SNCB
2. **Realtime gegevens**: GTFS-RT formaat gegevens via onze API-endpoint

## 🔄 Realtime Gegevenstoegang

Deze applicatie maakt verbinding met onze speciale API-endpoint op `https://nmbsapi.sanderzijntestjes.be/api/` om de nieuwste NMBS-treingegevens op te halen. De API-service draait onafhankelijk en levert realtime GTFS-gegevens, die deze applicatie vervolgens verwerkt, analyseert en visualiseert.

### Gegevensformaat

De API levert gegevens in het standaard GTFS Realtime-formaat, met informatie over:
- Ritwijzigingen
- Dienstregeling-wijzigingen
- Perroninformatie
- Vertragingsinformatie

## 🧩 Pakketstructuur

- **data**: Verzorgt gegevenstoegang via de API-endpoint en beheert bestandspaden
- **analysis**: Bevat gegevensverwerking en analyselogica
- **visualization**: Beheert kaartcreatie en visualisaties
- **webapp**: Bevat de Dash webapplicatiecomponenten

## 🌐 API Endpoints

De applicatie maakt gebruik van de volgende API endpoints:

- `/api/health`: Controleert de status van de API
- `/api/realtime/data`: Haalt de nieuwste realtime treingegevens op
- `/api/planningdata/stops`: Haalt stationsinformatie op
- `/api/planningdata/routes`: Haalt route-informatie op
- `/api/planningdata/trips`: Haalt ritinformatie op
- En meer...

Voor meer informatie over de API, zie: [https://github.com/DubblePumper/NMBS-Train-data-API](https://github.com/DubblePumper/NMBS-Train-data-API)

## 🧪 Ontwikkeling

### Tests Uitvoeren

```bash
pytest tests/
```

## 📜 Licentie

Dit project is gelicenseerd onder de MIT-licentie - zie het LICENSE-bestand voor details.

---

# NMBS Train Data Analysis | Vibe Coding

<div align="center">

![NMBS/SNCB Logo](https://img.shields.io/badge/NMBS%2FSNCB-Analysis-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/version-0.1.0-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

</div>

A package for analyzing, visualizing, and exploring NMBS (Belgian Railways) train data, including schedules and real-time updates.

> 🔗 This project uses our dedicated API: [NMBS-Train-data-API](https://github.com/DubblePumper/NMBS-Train-data-API)

## 📋 Table of Contents
- [Features](#-features-1)
- [Project Structure](#-project-structure)
- [Installation](#-installation-1)
- [Usage](#-usage-1)
  - [Run Everything](#run-everything-analysis-visualization-and-web-app)
  - [Run the Web Application](#run-the-web-application)
  - [Run Only Data Analysis](#run-only-data-analysis)
  - [Generate a Map Visualization](#generate-a-map-visualization)
- [Data Sources](#-data-sources)
- [Real-time Data Access](#-real-time-data-access)
- [Package Structure](#-package-structure)
- [API Endpoints](#-api-endpoints-1)
- [License](#-license)

## ✨ Features

- Analyzes NMBS train data to discover patterns and trends
- Visualizes train routes on interactive maps
- Processes both static planning data and real-time updates
- Provides an interactive web application for data exploration
- Supports light and dark mode for visualizations
- Automatic data processing and analysis
- Integrates with our real-time NMBS API for up-to-date information

## 📂 Project Structure

The project is structured as a full-fledged Python package:

```
nmbs-train-data/
│
├── requirements.txt        # Project dependencies
├── setup.py                # Package configuration
├── main.py                 # Main entry point
│
├── src/                    # Source code package
│   └── nmbs_data/          # Main package
│       ├── data/           # Data access layer
│       ├── analysis/       # Analysis components
│       ├── visualization/  # Visualization components
│       └── webapp/         # Web application
│
├── docs/                   # Documentation
│
└── tests/                  # Test suites
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NMBS-Train-data.git
cd NMBS-Train-data
```

2. Install the package and dependencies:
```bash
pip install -e .
```

## 🔧 Usage

### Run Everything (Analysis, Visualization and Web App)

```bash
python main.py all
```

You can also use the `--light` flag for a visualization in light mode:

```bash
python main.py all --light
```

### Run the Web Application

```bash
python main.py webapp
```

### Run Only Data Analysis

```bash
python main.py analyze
```

### Generate a Map Visualization

```bash
python main.py visualize
```

You can use the `--light` flag for a visualization in light mode:

```bash
python main.py visualize --light
```

## 📊 Data Sources

The application works with the following data sources:

1. **Planning data**: GTFS, NeTEx and other schedule formats from NMBS/SNCB
2. **Real-time data**: GTFS-RT format data via our API endpoint

## 🔄 Real-time Data Access

This application connects to our dedicated API endpoint at `https://nmbsapi.sanderzijntestjes.be/api/` to fetch the latest NMBS train data. The API service runs independently and provides real-time GTFS data, which this application then processes, analyzes, and visualizes.

### Data Format

The API provides data in the standard GTFS Realtime format, with information about:
- Trip changes
- Schedule changes
- Platform information
- Delay information

## 🧩 Package Structure

- **data**: Handles data access via the API endpoint and manages file paths
- **analysis**: Contains data processing and analysis logic
- **visualization**: Manages map creation and visualizations
- **webapp**: Contains the Dash web application components

## 🌐 API Endpoints

The application uses the following API endpoints:

- `/api/health`: Checks the status of the API
- `/api/realtime/data`: Retrieves the latest real-time train data
- `/api/planningdata/stops`: Retrieves station information
- `/api/planningdata/routes`: Retrieves route information
- `/api/planningdata/trips`: Retrieves trip information
- And more...

For more information about the API, see: [https://github.com/DubblePumper/NMBS-Train-data-API](https://github.com/DubblePumper/NMBS-Train-data-API)

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
