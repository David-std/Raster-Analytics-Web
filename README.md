# Raster Analytics Web

Web application for spatiotemporal analysis of pedestrian collision risk in Metropolitan Lima.

## Overview

The system combines a geospatial web interface, an API for risk queries, and a reproducible data pipeline for profiling and preparing source datasets.

```text
Source data
    |
    v
Ingestion and processing
    |
    v
Risk model
    |
    v
FastAPI
    |
    v
React geospatial application
```

The web application supports period filtering, map exploration, area selection, and side-by-side comparison. The model layer is isolated from the API so the scoring implementation can evolve without changing the client contract.

## Repository structure

```text
apps/api        FastAPI backend
apps/web        React + TypeScript frontend
pipelines       Data ingestion, profiling, and processing utilities
data            Source registry and data documentation
docs            Product and architecture documentation
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

## Data

Official source workbooks are registered under `data/sources/`. To download the primary ONSV crash/person sources and build the normalized Metropolitan Lima pedestrian fatal-crash table:

```bash
python -m pipelines.ingestion.onsv sync
python -m pipelines.processing.onsv
```

Raw files and generated datasets remain outside version control.

## Quality checks

Backend and pipelines:

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

## Product and architecture documentation

- `docs/product-development-specification.md` defines the evidence-driven data, ML, architecture, UX, validation, and implementation gates.
- `docs/architecture/architecture.md` describes the current high-level application structure and responsibility boundaries.
