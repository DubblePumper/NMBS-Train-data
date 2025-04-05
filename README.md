# NMBS Treingegevens Analyse | Vibe Coding

Een pakket voor het analyseren, visualiseren en verkennen van NMBS (Belgische Spoorwegen) treingegevens, inclusief dienstregelingen en realtime updates.

## Projectstructuur

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

## Installatie

1. Kloon de repository:
```bash
git clone https://github.com/yourusername/NMBS-Train-data.git
cd NMBS-Train-data
```

2. Installeer het pakket en de afhankelijkheden:
```bash
pip install -e .
```

## Gebruik

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

## Gegevensbronnen

De applicatie werkt met de volgende gegevensbronnen:

1. **Planningsgegevens**: GTFS, NeTEx en andere dienstregeling-formaten van NMBS/SNCB
2. **Realtime gegevens**: GTFS-RT formaat gegevens via onze API-endpoint

## Realtime Gegevenstoegang

Deze applicatie maakt verbinding met onze speciale API-endpoint op `https://nmbsapi.sanderzijntestjes.be/api/` om de nieuwste NMBS-treingegevens op te halen. De API-service draait onafhankelijk en levert realtime GTFS-gegevens, die deze applicatie vervolgens verwerkt, analyseert en visualiseert.

### Gegevensformaat

De API levert gegevens in het standaard GTFS Realtime-formaat, met informatie over:
- Ritwijzigingen
- Dienstregeling-wijzigingen
- Perroninformatie
- Vertragingsinformatie

## Ontwikkeling

### Tests Uitvoeren

```bash
pytest tests/
```

### Pakketstructuur

- **data**: Verzorgt gegevenstoegang via de API-endpoint en beheert bestandspaden
- **analysis**: Bevat gegevensverwerking en analyselogica
- **visualization**: Beheert kaartcreatie en visualisaties
- **webapp**: Bevat de Dash webapplicatiecomponenten

## API Endpoints

De applicatie maakt gebruik van de volgende API endpoints:

- `/api/health`: Controleert de status van de API
- `/api/realtime/data`: Haalt de nieuwste realtime treingegevens op
- `/api/planningdata/stops`: Haalt stationsinformatie op
- `/api/planningdata/routes`: Haalt route-informatie op
- `/api/planningdata/trips`: Haalt ritinformatie op
- En meer...

API onderdeel van: https://github.com/DubblePumper/NMBS-Train-data

## Licentie

Dit project is gelicenseerd onder de MIT-licentie - zie het LICENSE-bestand voor details.
