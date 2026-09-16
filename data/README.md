# Data

Raw and generated datasets are not stored in Git. Source metadata, schemas, and small reproducible fixtures can be versioned here.

The current primary source pair is published by the Observatorio Nacional de Seguridad Vial (ONSV):

- fatal road crashes, 2021-2025;
- people involved in fatal road crashes, 2021-2025.

The crash table provides the event-level record, while the people table is used to identify pedestrian involvement. Vehicle-level and long-term historical files are registered as supporting sources.

Source definitions live in `data/sources/onsv.json`.

Download and inspect the primary workbooks:

```bash
python -m pipelines.ingestion.onsv sync
```

Include all registered ONSV workbooks:

```bash
python -m pipelines.ingestion.onsv sync --all
```

Downloads are written to `data/raw/onsv/` and the workbook inventory to `data/interim/onsv/source-inventory.json`; both paths are ignored by Git.

Filtering to Metropolitan Lima, identifying pedestrian records, and defining the model-ready spatial and temporal representation are downstream transformations performed after the source schema has been inspected.
