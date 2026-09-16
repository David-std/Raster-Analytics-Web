# Architecture

Raster Analytics separates data processing, risk scoring, API delivery, and map presentation so each part can evolve independently.

## System flow

```text
Data sources
    |
    v
Profiling and processing
    |
    v
Model-ready data
    |
    v
RiskProvider
    |
    v
FastAPI
    |
    v
React + Leaflet
```

## Backend

The API exposes metadata, risk queries, map results, and comparison operations. `RiskProvider` owns risk scoring and keeps model-specific logic out of the HTTP layer.

Core domain objects:

- `RiskQuery`: spatial unit and period requested by the client.
- `RiskResult`: score and model traceability returned by the provider.
- `RiskMapItem`: result enriched with map coordinates and display name.
- `SpatialUnitMetadata`: map-facing spatial metadata.
- `PeriodMetadata`: selectable temporal metadata.

## Frontend

The React application consumes the API through `apps/web/src/api.ts`. Leaflet renders the map, while the rest of the interface handles period selection, area detail, summary values, and comparison.

## Data pipeline

`pipelines/profiling` provides dataset inspection before ingestion. Additional processing stages can be added under `pipelines` while keeping source files immutable and transformations reproducible.

## Model integration

The API depends on `RiskProvider` rather than embedding model logic in route handlers. Trained model loading, feature construction, and inference can therefore change behind the same application-facing interface.
