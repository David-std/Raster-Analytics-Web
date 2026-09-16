# Architecture

Raster Analytics separates data acquisition, analytical feature construction, model inference, API delivery, and map presentation so each responsibility can evolve independently.

This document is intentionally high level. The evidence-driven product, data, ML, UX, and architecture constraints are defined in `docs/product-development-specification.md` while the project is being progressively elaborated.

## System flow

```text
Data sources
    |
    v
Ingestion, profiling, and source-specific normalization
    |
    v
Spatial-temporal feature construction
    |
    v
Model-ready analytical dataset
    |
    v
RiskProvider
    |
    v
FastAPI
    |
    v
React geospatial application
```

## Backend

The API exposes metadata, risk queries, map results, comparison operations, and model/source traceability. `RiskProvider` owns risk inference and keeps model-specific logic out of the HTTP layer.

Core domain objects currently include:

- `RiskQuery`: spatial unit and period requested by the client.
- `RiskResult`: analytical result and model traceability returned by the provider.
- `RiskMapItem`: result enriched with map geometry/coordinates and display metadata.
- `SpatialUnitMetadata`: map-facing spatial metadata.
- `PeriodMetadata`: selectable temporal metadata.

As the analytical pipeline matures, feature construction and model evaluation remain outside HTTP handlers and are integrated through explicit application contracts.

## Frontend

The React application consumes the API through `apps/web/src/api.ts`. The map is the primary analytical surface; controls, comparison, detail, provenance, limitations, and methodology should remain separate UI responsibilities rather than model concerns.

The current map library is an implementation choice, not an architectural commitment. It may be changed if vector geometries, interaction requirements, accessibility, or measured performance justify it.

## Data pipeline

Source workbooks/files are immutable inputs. `pipelines/ingestion` acquires and inventories sources, `pipelines/profiling` measures source fitness and data quality, and `pipelines/processing` performs source-specific normalization. Feature engineering and final spatial-temporal dataset construction must be reproducible and traceable to source versions.

The current ONSV pedestrian fatal-crash table is one real source-derived event layer. It is not, by itself, the final model-ready risk dataset.

## Model integration

The API depends on `RiskProvider` rather than embedding training or inference logic in route handlers. Baselines, candidate CNN-RNN configurations, feature construction, artifact loading, and inference can therefore evolve behind the same application-facing contract.

The production provider must expose enough metadata to identify the model version, data snapshot, feature schema, spatial/temporal representation, and benchmark evidence associated with a result.
