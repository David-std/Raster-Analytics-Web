# Data pipelines

Reproducible data path:

```text
source -> profiling -> ingest -> clean -> geospatial -> temporal -> model-ready dataset
```

## Profiling

The profiler inspects a CSV before ingestion and produces a JSON quality report.

Run from the repository root:

```bash
python -m pipelines.profiling path/to/source.csv --output reports/source-profile.json
```

The report includes:

- file size and SHA-256;
- delimiter, row count, and column count;
- exact duplicate rows;
- null percentage and capped unique-count tracking per column;
- conservative type inference;
- minimum and maximum values for numeric and temporal fields;
- representative sample values;
- latitude/longitude pair detection and geographic validity;
- temporal candidates that reach the parse-confidence threshold;
- quality warnings that require review.

The profiler is diagnostic and does not modify source data.
