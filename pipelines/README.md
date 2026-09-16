# Data pipelines

Reproducible data path:

```text
source -> ingestion -> profiling -> processing -> model-ready dataset
```

## ONSV ingestion

Official ONSV workbook URLs are registered in `data/sources/onsv.json`.

```bash
python -m pipelines.ingestion.onsv sync
```

This downloads the primary crash/person workbooks to `data/raw/onsv/` and writes a workbook inventory under `data/interim/onsv/`.

## ONSV pedestrian events

After ingestion, build the normalized event-level table for fatal crashes involving pedestrians in Metropolitan Lima:

```bash
python -m pipelines.processing.onsv
```

The output is `data/processed/onsv/lima_pedestrian_fatal_crashes.csv`.

## CSV profiling

The generic CSV profiler inspects a dataset before modeling:

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

Profiling is diagnostic and does not modify source data.
