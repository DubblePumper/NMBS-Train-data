# NMBS Export Dashboard

Dashboard-only project for exploring NMBS API snapshot exports.

## What this project is now

This repository was fully reworked to focus on **one thing only**:

- a train-centric dashboard over snapshot data in `examples/endpoint_snapshots`

Removed from the project:

- legacy analysis scripts
- API fetch/services code
- map generators and unrelated reports
- extra startup flows

## Project structure

```text
NMBS-Train-data/
├── main.py                          # single startup file
├── docker-compose.yml               # easy local run
├── Dockerfile                       # Python 3.14.3 runtime
├── requirements.txt
├── docs/
│   └── GTFS_Realtime_Visualization.md
├── examples/
│   └── endpoint_snapshots/
└── src/
    └── nmbs_dashboard/
        ├── wsgi.py                    # Gunicorn WSGI entrypoint
        ├── app/
        │   ├── assets/
        │   ├── callbacks/
        │   ├── layout/
        │   ├── services/
        │   └── server.py
        └── paths.py
```

## Run locally (no Docker)

```bash
pip install -r requirements.txt
python main.py
```

Open: `http://localhost:8050`

Optional flags:

```bash
python main.py --host 0.0.0.0 --port 8050 --debug
```

## Run with Docker Compose (recommended)

```bash
docker compose up --build
```

Open: `http://localhost:8050`

Container runtime details:

- Python image: `3.14.3-slim`
- Process manager: `gunicorn` (2 workers, gthread worker class)
- Runs as a non-root user (`app`)
- Healthcheck probes `http://127.0.0.1:8050`

Stop:

```bash
docker compose down
```

## Notes

- Default snapshot source is `examples/endpoint_snapshots`.
- You can override snapshot source with environment variable `SNAPSHOT_ROOT`.

## Tests

```bash
pytest
```
