# Raster Analytics Web

Web application for spatiotemporal analysis of pedestrian collision risk in Metropolitan Lima.

## Overview

The system combines a geospatial web interface, an API for risk queries, and a reproducible data pipeline for profiling and preparing source datasets.

```text
Source data
    |
    v
Profiling and processing
    |
    v
Risk model
    |
    v
FastAPI
    |
    v
React + Leaflet
```

The web application supports period filtering, map exploration, area selection, and side-by-side comparison. The model layer is isolated from the API so the scoring implementation can evolve without changing the client contract.

## Repository structure

```text
apps/api        FastAPI backend
apps/web        React + TypeScript frontend
pipelines       Data profiling and processing utilities
docs            Architecture documentation
```

## Run the API

Requirements: Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn raster_api.main:app --app-dir apps/api/src --reload
```

Available endpoints:

- `GET /health`
- `GET /model/metadata`
- `GET /metadata/spatial-units`
- `GET /metadata/periods`
- `GET /risk?spatial_unit=...&period=...`
- `GET /risk/map?period=...`
- `POST /risk/compare`

## Run the web application

With the API available at `http://localhost:8000`:

```bash
cd apps/web
npm install
npm run dev
```

The application is served at `http://localhost:5173` by default.

## Profile a dataset

The profiling pipeline inspects a CSV without modifying the source file:

```bash
python -m pipelines.profiling path/to/source.csv --output reports/source-profile.json
```

The generated report includes file traceability, row and column counts, duplicate detection, null rates, conservative type inference, coordinate checks, temporal candidates, and quality warnings.

## Quality checks

Backend:

```bash
ruff check .
pytest
```

Frontend:

```bash
cd apps/web
npm run typecheck
npm run build
```

See `docs/architecture/architecture.md` for the application structure.
