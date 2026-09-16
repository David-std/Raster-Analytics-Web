# Data

Raw and generated datasets are not stored in Git. Source metadata, schemas, and small reproducible fixtures can be versioned here.

The primary source pair is published by the Observatorio Nacional de Seguridad Vial (ONSV):

- fatal road crashes, 2021-2025;
- people involved in fatal road crashes, 2021-2025.

The crash table provides the event-level record, while the people table identifies pedestrian involvement. Vehicle-level and long-term historical files are registered as supporting sources.

Source definitions live in `data/sources/onsv.json`.

Download and inspect the primary workbooks:

```bash
python -m pipelines.ingestion.onsv sync
```

Build the normalized Metropolitan Lima pedestrian fatal-crash event table:

```bash
python -m pipelines.processing.onsv
```

The generated CSV is written to `data/processed/onsv/lima_pedestrian_fatal_crashes.csv`.

Include every registered ONSV workbook when refreshing sources:

```bash
python -m pipelines.ingestion.onsv sync --all
```

Raw downloads, inventories, and processed outputs remain outside version control.

The normalized event table is intentionally named `fatal_crashes`: these ONSV open datasets contain fatal road crashes. They are suitable for high-severity pedestrian-risk analysis but do not, on their own, represent every pedestrian collision in Metropolitan Lima.
