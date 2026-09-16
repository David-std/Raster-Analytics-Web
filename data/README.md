# Data

Raw and generated datasets are not stored in Git. Source metadata, schemas, deterministic references, and small reproducible fixtures can be versioned here.

## Source qualification

`data/sources/qualification.json` is the machine-readable registry for candidate analytical sources. It records current status, evidence state, analytical role, geographic/temporal grain, access path, and known limitations.

The current findings and gating rules are documented in:

`docs/data/source-qualification.md`

A source being registered does not mean it is accepted as a model feature. The final analytical dataset is expected to combine outcome, exposure/proxy, built-environment, temporal, and geometry layers only after their fitness is demonstrated.

## ONSV outcome sources

The primary source pair is published by the Observatorio Nacional de Seguridad Vial (ONSV):

- fatal road crashes, 2021-2025 preliminary;
- people involved in fatal road crashes, 2021-2025 preliminary.

The crash table provides event-level records, while the people table identifies pedestrian involvement. Vehicle-level and long-term historical files are registered as supporting/auxiliary sources in `data/sources/onsv.json`.

Download and inspect the primary workbooks:

```bash
python -m pipelines.ingestion.onsv sync
```

Build the normalized Metropolitan Lima pedestrian-linked fatal-crash event table:

```bash
python -m pipelines.processing.onsv
```

The generated CSV is written to:

```text
data/processed/onsv/lima_pedestrian_fatal_crashes.csv
```

The table contains fatal crashes linked to at least one person classified as pedestrian. It must not be described automatically as a table of `ATROPELLO` crashes: P1 profiling found additional recorded crash classes and keeps target semantics open for explicit review.

Include every registered ONSV workbook when refreshing sources:

```bash
python -m pipelines.ingestion.onsv sync --all
```

## Profiling

Profile a generated CSV without changing it:

```bash
python -m pipelines.profiling \
  data/processed/onsv/lima_pedestrian_fatal_crashes.csv \
  --output reports/onsv-profile.json
```

Validate the source catalog and report analytical-role readiness:

```bash
python -m pipelines.profiling.source_catalog \
  data/sources/qualification.json \
  --output reports/source-readiness.json
```

Audit ONSV-specific target semantics and district coverage:

```bash
python -m pipelines.profiling.onsv_quality \
  data/processed/onsv/lima_pedestrian_fatal_crashes.csv \
  --output reports/onsv-quality.json
```

Registered ArcGIS layers can be probed for metadata, feature count, extent, fields, and selected coverage values:

```bash
python -m pipelines.profiling.arcgis_profiler \
  data/sources/qualification.json \
  --output reports/arcgis-profiles.json
```

## Data policy

- raw downloads are immutable inputs;
- processed outputs are reproducible transformations, not manually edited datasets;
- source coverage and source absence are tracked separately from feature value zero;
- partial years are never silently treated as full years;
- direct exposure and exposure proxies are distinguished explicitly;
- event-conditioned records are not reused as ambient exposure;
- final spatial and temporal units remain open until representation experiments justify them;
- raw downloads, inventories, reports, and generated analytical datasets remain outside version control unless intentionally reduced to a small fixture/reference.
