# SkyPy Crew Rostering System

Backend scheduling engine for SkyPy, a regional airline. Reads flight and crew
data, enforces operational rules, and produces legal crew assignments.

## Prerequisites

- Python 3.10+
- Git
- Docker (optional, for containerised runs)

## Setup

```bash
git clone https://github.com/lediadakaj/SkyPy-Crew-Rostering.git
cd SkyPy-Crew-Rostering
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### CLI: generate `roster_output.json`

```bash
python main.py
```

Reads `data/flights.csv` and `data/crew.csv`, runs the scheduler, writes
`roster_output.json`. Optional flags: `--flights`, `--crew`, `--out`.

### Flask API

```bash
python app.py
```

Listens on `http://127.0.0.1:5000`.

| Endpoint | Description |
|---|---|
| `POST /schedule` | Submit flights + crew JSON, get the full roster |
| `GET /roster/<crew_id>` | Flights, hours, and layover cost for one crew member |
| `GET /report` | Summary of the last scheduling run |
| `GET /health` | Liveness probe (`{"status": "ok"}`) |
| `GET /swagger-ui` | Swagger UI for the endpoints above |
| `GET /openapi.json` | Raw OpenAPI 3.0.3 spec |

The OpenAPI document is assembled by [flask-smorest](https://flask-smorest.readthedocs.io/)
from per-route YAML files under [`skypy/api/openapi/`](skypy/api/openapi/) — edit those
to change request/response docs.

Example with the included `request.json`:

```bash
curl -X POST http://127.0.0.1:5000/schedule \
    -H "Content-Type: application/json" \
    -d @request.json
```

> On Windows PowerShell use `curl.exe`, not `curl` (which is an alias for `Invoke-WebRequest`).

### Tests

```bash
python -m pytest
```

Runs the full pytest suite with coverage. Gate fails the run below 90%.

### Docker

Build the image and start the service:

```bash
./deploy.sh                
# or, equivalently:
docker compose up --build
```

**The container runs the pytest suite on every startup.** waitress only binds
port 5000 if `pytest` exits 0. A test failure stops the container without
ever opening the port, so a green deploy is also a green test run.

Lower-level alternative (no compose):

```bash
docker build -t skypy-roster .
docker run --rm -p 5000:5000 skypy-roster
```

Image uses `waitress` (production WSGI), runs as a non-root user, and ships
with a `HEALTHCHECK` against `/health`.

## Operational rules

| Rule | Description |
|---|---|
| **Range Certification** | Flight distance ≤ crew's `max_range_miles` |
| **Home Base Start** | First flight must depart from crew's `home_base` |
| **Route Continuity** | `flight[i].destination` = `flight[i+1].origin` |
| **Dynamic Rest** | 60 min rest after flights < 180 min, 120 min after flights ≥ 180 min |
| **Crew Pairing** | Exactly 1 Captain + at least 1 First Officer per flight |

## Project structure

```
skypy/models/         Flight, Crew, Roster (pure data)
skypy/engine/         rules, pairing, scheduler, costs
skypy/io/             CSV loader + JSON exporter
skypy/api/            Flask app factory + blueprints
skypy/api/openapi/    Per-route YAML specs served via Swagger UI
tests/                pytest suite
Dockerfile            production image, pytest-gated startup
docker-compose.yml    single-service compose for local runs
deploy.sh             one-command build + start
```

See [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) for scoped-out features and
design decisions.
