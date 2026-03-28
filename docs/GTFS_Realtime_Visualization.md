# GTFS Realtime Visualization (Dashboard-Only)

Deze repository is herwerkt naar één duidelijke use-case:

- een dashboard dat snapshotdata visualiseert uit `examples/endpoint_snapshots`

## Datastroom

1. `manifest.json` per snapshot wordt ingelezen
2. Endpoint JSON payloads worden gekoppeld per snapshot
3. Realtime + trajectories worden train-centrisch geïndexeerd
4. Dashboard toont per trein:
   - status en richting
   - vertraging over tijd
   - traject op kaart
   - stops, skip-events en spoorwijzigingen

## Starten

### Lokaal

```bash
pip install -r requirements.txt
python main.py
```

### Docker Compose

```bash
docker compose up --build
```

## Snapshotbron wijzigen

Standaard gebruikt de app:

- `examples/endpoint_snapshots`

Override via environment variable:

- `SNAPSHOT_ROOT=/pad/naar/endpoint_snapshots`

## Architectuur

Code is georganiseerd in subfolders:

- `src/nmbs_dashboard/app/services` → data inlezen/indexeren
- `src/nmbs_dashboard/app/layout` → componenten + pagina-opbouw
- `src/nmbs_dashboard/app/callbacks` → tab-specifieke interactie
- `src/nmbs_dashboard/app/assets` → styling
- `main.py` → **enige startup entrypoint**
