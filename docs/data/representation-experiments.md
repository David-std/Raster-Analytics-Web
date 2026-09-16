# P2 spatial-temporal representation experiments

Status: **evidence in progress; no representation selected**

This document records how candidate spatial and temporal units are measured before the project
freezes a model-ready representation. The purpose of P2 is not to make a CNN-RNN fit whatever
unit is easiest to code. It is to expose sparsity, coverage, assignment loss, boundary effects and
sequence length so the later target and model design have defensible inputs.

## 1. Inputs inherited from P1

P1 established that the current ONSV normalized event layer is a real official fatal-crash outcome
layer, but not a complete citywide pedestrian-risk dataset. Two outcome populations remain open:

```text
pedestrian_linked_fatal
  fatal crash linked to at least one person classified as PEATON

strict_fatal_atropello
  pedestrian-linked fatal crash whose recorded class contains ATROPELLO
```

P2 measures both populations. It does not choose one.

The primary like-for-like diagnostic window is `2021-01-01` through `2024-12-31`. The current
2025 detailed ONSV source is partial, so an additional source-cutoff window may be reported only as
a sensitivity/coverage diagnostic. It is never treated as a complete calendar year.

## 2. Project-boundary geometry

The first executable boundary candidate is the public layer:

```text
Límite de los distritos de Lima Metropolitana (INEI, 2017)
https://geoservidorperu.minam.gob.pe/arcgis/rest/services/GEOLOMAS_final/MapServer/0
```

The repository snapshots the layer as WGS84 GeoJSON and records the snapshot hash. Metric spatial
operations use `EPSG:32718` (WGS 84 / UTM zone 18S).

This geometry is used to test project-boundary and district assignment. Its use does **not** mean
that district has been selected as the final model unit. A newer boundary may replace it only after
coverage and identifier compatibility are proven.

## 3. Spatial candidates currently executable

### District

District is measured as a coarse reference representation because it is interpretable and provides
a useful upper bound on event density. It is not presumed to be sufficiently local for the product.

The experiment spatially assigns every outcome coordinate to a district polygon and compares that
assignment with the district name present in the ONSV source. Mismatches and unassigned points are
reported explicitly.

### Regular grid

The initial grid experiment measures cell sizes:

```text
250 m
500 m
1000 m
2000 m
```

Each size is evaluated twice: once on a base UTM lattice and once with a half-cell x/y shift. The
shift is not another candidate product design. It is a boundary-sensitivity test. A representation
whose apparent density changes materially when the grid origin moves is less stable than its raw
cell count may suggest.

Grid cells remain regular rather than being geometrically clipped into irregular pieces. Cells that
intersect the Lima boundary are retained and marked as full or boundary-intersecting cells. This
preserves the lattice semantics that a conventional CNN would require.

### Road segment and intersection/node

These candidates remain blocked at this point. The qualified public `Tipos Vias Transporte` layer
is not yet proven to be a complete Lima street network with stable segment identity, and the
signalized-intersection layer is not equivalent to a complete street-intersection topology.

P2 will not manufacture network nodes or pretend a partial infrastructure layer is a complete road
graph merely to make every candidate executable.

## 4. Temporal candidates

The first experiment measures:

```text
month
ISO week
day
6-hour daypart
```

The 6-hour representation is encoded as four chronological periods per day (`00`, `06`, `12`,
`18`). It is intentionally fine-grained so the experiment can quantify whether the additional
sequence resolution is mostly empty.

No interval is selected from convenience. A temporal candidate must later be considered together
with covariate availability and specialist usefulness, not only outcome density.

## 5. Metrics

Every spatial x temporal x outcome-population x analysis-window combination reports:

- spatial-unit count;
- period count;
- total unit-period cells;
- assigned and unassigned events;
- occupied unit-period cells;
- zero-event cell ratio;
- mean events per cell;
- nearest-rank p50, p90, p95 and p99 event counts;
- maximum event count per cell;
- mean events per non-zero cell;
- spatial units with at least one event;
- periods with at least one event.

Grid pairs also report half-shift minus base deltas for unit count, zero-event ratio, occupied cells
and maximum events in a cell.

These are profiling measurements, not model acceptance thresholds. P2 does not invent a maximum
acceptable zero ratio before seeing the observed distributions.

## 6. Important interpretation rules

A zero outcome in a unit-period cell means only that the selected outcome layer contains no event in
that cell and period. It does not mean zero pedestrian exposure or zero risk.

A cell outside a candidate feature source's coverage must later remain distinct from an observed
feature value of zero. P2 representation metrics do not fill missing exposure or built-environment
layers with zeros.

The regular grid is naturally compatible with image-like convolution, but that convenience alone
cannot select it. District is easy to interpret, but that convenience cannot select it either.

## 7. Reproducibility

The executable report is produced with:

```bash
python -m pipelines.representation \
  data/processed/onsv/lima_pedestrian_fatal_crashes.csv \
  /path/to/versioned-lima-districts.geojson \
  --output /tmp/representation-report.json
```

The live evidence workflow additionally snapshots the boundary source and ONSV workbooks before
running the experiment. Generated source data and reports remain CI artifacts rather than being
committed as if they were hand-authored evidence.

## 8. P2 decision gate

P2 may narrow the candidate set when the report provides enough evidence to explain why a
representation is unsuitable or worth carrying into feature/target experiments. Final selection is
still deferred until candidate covariate coverage and the target formulation are known.

Therefore the output field `selection_status` must remain `NOT_SELECTED` during this stage.
