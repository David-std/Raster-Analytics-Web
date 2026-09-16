# Pipelines

Reproducible data path:

```text
source -> profiling -> ingest -> clean -> geospatial -> temporal -> model-ready dataset
```

## Profiling v0

The first implemented capability inspects a CSV before the project commits to a spatial unit, temporal granularity or model-ready schema.

Run from the repository root:

```bash
python -m pipelines.profiling path/to/source.csv --output reports/source-profile.json
```

The JSON report records:

- file size and SHA-256;
- delimiter, rows and columns;
- exact duplicate rows;
- null percentage and capped unique-count tracking per column;
- conservative type inference;
- minimum/maximum for numeric and temporal fields;
- representative sample values;
- explicit latitude/longitude pair detection and geographic validity;
- temporal candidates that reach the parse-confidence threshold;
- warnings for quality conditions that need investigation.

This is a **diagnostic tool, not a cleaning step**. It does not alter source data and does not decide the final spatial/temporal representation.

CSV is intentionally the only adapter in v0. Other formats (for example GeoJSON, XLSX or database sources) should be added after the real official sources are confirmed instead of being guessed in advance.
