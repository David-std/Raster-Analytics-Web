# Spatial-temporal representation experiments

Status: **live evidence captured; candidate set narrowed but final representation not selected**

This document records how candidate spatial and temporal units behave before a model-ready
representation is frozen. The purpose is not to make a CNN-RNN fit whatever unit is easiest to code.
It is to expose sparsity, coverage, assignment loss, boundary effects, sequence length and source
support so the later target, feature and model design have defensible inputs.

## 1. Inputs inherited from source qualification

The current normalized ONSV event layer is a real official fatal-crash outcome layer, but it is not a
complete citywide pedestrian-risk dataset. Two outcome populations remain intentionally open:

```text
pedestrian_linked_fatal
  fatal crash linked to at least one person classified as PEATON

strict_fatal_atropello
  pedestrian-linked fatal crash whose recorded class contains ATROPELLO
```

The experiment measures both populations. It does not choose one.

The primary like-for-like diagnostic window is `2021-01-01` through `2024-12-31`. The current 2025
detailed ONSV publication is partial, so 2025 is used only as a source-cutoff sensitivity window and
is never treated as a complete calendar year.

The live audit loaded:

```text
pedestrian-linked fatal events        897
strict fatal ATROPELLO events         839
complete-window events (2021-2024)    842
```

All 897 event coordinates were assigned to the 43-district project boundary, and the geometric
district assignment produced zero mismatches against the normalized ONSV district value.

## 2. Project-boundary geometry

The executable boundary source is:

```text
Límite de los distritos de Lima Metropolitana (INEI, 2017)
served through MINAM GeoServidor
https://geoservidorperu.minam.gob.pe/arcgis/rest/services/GEOLOMAS_final/MapServer/0
```

Metric spatial operations use `EPSG:32718` (WGS 84 / UTM zone 18S). The live snapshot contains the
43 project districts and measures approximately `2641.889 km²` before any urban-support filtering.

This geometry is used for project-boundary validation, district assignment and representation
experiments. It does **not** select district as the final model unit. A newer official boundary may
replace it after equivalent coverage and identifier compatibility are proven.

## 3. Structural urban-support diagnostic

A full administrative boundary includes large peripheral areas that are not equivalent to observed
urban activity. To quantify that effect without fabricating pedestrian exposure, the experiment also
uses the qualified 2021 urban-zoning polygon layer as a **structural support mask**.

The live snapshot contained `87,858` polygons. After filtering to the project scope:

```text
retained polygons                         87,379
retained project districts                    43
excluded out-of-scope polygons               479
  Ventanilla                                  255
  Callao                                      171
  Chilca                                       50
  Carmen de la Legua y Reynoso                  3
```

The ArcGIS geometry carries an extra ordinate that is not needed by the analysis and may be null.
`87,379` retained geometries required deterministic normalization to XY before Shapely parsing. This
is treated as source-shape normalization, not silent repair of the analytical coordinates.

The support mask means only:

```text
candidate spatial cell intersects qualified mapped urban structure
```

It does **not** mean:

```text
pedestrian exposure > 0
traffic exposure > 0
risk > 0
safe/risky location
```

The mask therefore cannot be used as a risk denominator or target.

## 4. Spatial candidates measured

### District

District is a coarse reference representation. It is interpretable and provides an upper bound on
outcome density, but it is not presumed sufficiently local for the analytical product.

### Regular grid

The live experiment measured regular cells of:

```text
250 m
500 m
1000 m
2000 m
```

Each size was evaluated on a base UTM lattice and on a half-cell x/y shift. The shifted lattice is a
boundary-sensitivity test, not a second product representation.

Grid cells remain regular rather than being clipped into irregular fragments, preserving the raster
semantics that a conventional spatial convolution would require.

### Road segment and intersection/node

These remain blocked. No complete, qualified Lima urban road network with stable segment identity
has yet been accepted, and the signalized-intersection layer is not equivalent to a complete street
intersection topology. The project will not manufacture a graph from partial infrastructure data
merely to make every candidate executable.

## 5. Temporal candidates measured

The live experiment measured:

```text
month
ISO week
day
6-hour daypart
```

The 6-hour representation contains four chronological periods per day (`00`, `06`, `12`, `18`). It
is intentionally fine enough to reveal whether additional temporal resolution produces mostly empty
unit-period combinations.

No temporal interval is selected from convenience. Covariate availability, target semantics and
specialist usefulness must also be considered.

## 6. Live density evidence

For the primary `2021-2024` window and the broader `pedestrian_linked_fatal` population, the monthly
results were:

| Spatial representation | Spatial units | Assigned events | Assignment ratio | Zero-event unit-periods |
| --- | ---: | ---: | ---: | ---: |
| District | 43 | 842 | 100.000% | 70.4942% |
| 250 m grid, full boundary | 43,373 | 842 | 100.000% | 99.9599% |
| 250 m grid, zoning support | 32,966 | 841 | 99.8812% | 99.9473% |
| 500 m grid, full boundary | 11,111 | 842 | 100.000% | 99.8436% |
| 500 m grid, zoning support | 8,494 | 841 | 99.8812% | 99.7957% |
| 1000 m grid, full boundary | 2,899 | 842 | 100.000% | 99.4071% |
| 1000 m grid, zoning support | 2,238 | 841 | 99.8812% | 99.2329% |
| 2000 m grid, full boundary | 783 | 842 | 100.000% | 97.8847% |
| 2000 m grid, zoning support | 620 | 842 | 100.000% | 97.3286% |

The structural mask removes roughly `21-24%` of grid units, depending on cell size, while preserving
nearly every observed event. At 250-1000 m one of the 842 complete-window events falls outside the
mapped zoning support; the 2000 m cells still intersect support and retain all 842 events. That event
loss is a source-coverage finding and must not be silently erased.

The support mask improves the measured sparsity, but it does **not** make the fine grids dense. This
is important: the extreme sparsity is not explained mainly by mountains or peripheral administrative
area. It is fundamentally driven by the rarity of the current fatal-only outcome relative to the
space-time lattice.

## 7. Temporal-resolution evidence

Even the coarse district representation becomes sparse as temporal resolution increases:

| Temporal representation | District-period cells | Zero-event ratio | Maximum events in one cell |
| --- | ---: | ---: | ---: |
| Month | 2,064 | 70.4942% | 5 |
| ISO week | 9,030 | 91.3953% | 3 |
| Day | 62,823 | 98.6741% | 2 |
| 6-hour daypart | 251,292 | 99.6673% | 2 |

For a 500 m full-boundary grid, daily resolution creates `16,233,171` unit-period cells for the same
842 observed events and yields a `99.9948%` zero-event ratio. A 250 m x 6-hour representation would
create more than `253 million` unit-period cells with the current event layer.

These measurements do not impose a universal acceptable sparsity threshold. They demonstrate that a
fine daily/daypart target built only from the current fatal-event layer would be dominated by zeros
and would require a different target formulation, substantially denser outcome data, carefully
designed negative sampling/likelihood treatment, or a coarser representation.

## 8. Grid-origin sensitivity

The half-cell shift test shows that moving the lattice origin has very small effects on the headline
zero-event ratios. For the monthly complete-window population, zero-ratio deltas are near zero across
250-2000 m grids. Occupied-cell counts change only slightly.

This is useful negative evidence: the observed sparsity is not an artifact of having chosen a lucky
or unlucky grid origin.

A small support-boundary interaction remains visible at 2000 m, where the shifted zoning-supported
grid can lose one assigned event. Therefore any later selected support mask must retain explicit
assignment-loss auditing.

## 9. Interpretation and narrowed candidate set

No final spatial/temporal representation is selected here. However, the live evidence is sufficient
to narrow what should be carried into the next feature/target stage.

### Carry forward as primary analytical candidates

```text
district x month
1000 m grid x month
2000 m grid x month
```

`district x month` remains an interpretable reference and reporting baseline. `1000 m` and `2000 m`
monthly grids remain the main raster candidates because they preserve regular spatial structure
while avoiding the most extreme expansion of the finer lattices.

### Carry forward conditionally

```text
500 m grid x month
```

It remains useful for sensitivity analysis and could become viable if a broader non-fatal outcome
source or stronger exposure/feature formulation materially changes the information density.

### Defer with the current fatal-only outcome

```text
250 m grid
ISO week
day
6-hour daypart
```

These are not declared universally invalid. They are deferred because the current outcome evidence
is too sparse to justify making them the primary model-ready lattice now. They may be re-opened if
future source qualification changes the event density or target semantics.

Road-segment and intersection/node representations remain `BLOCKED`, not rejected.

## 10. Reproducibility and evidence state

The live workflow snapshots the district boundary, urban-zoning support and ONSV source, then writes
`representation-report.json` as an artifact. The successful live audit at commit
`b0a984be4f595bdedefae7baa110287f836559ca` completed source acquisition, ONSV processing, the full
representation experiment and artifact upload successfully.

The audit is intentionally manual after evidence capture because external public servers should not
become a mandatory availability dependency for every normal code commit.

Normal CI continues to validate deterministic code, unit tests, lint, frontend typecheck and build.

## 11. Decision gate before model-ready data

The next stage must not train CNN/RNN candidates yet. It must first establish the feature and target
contract for the surviving representations. At minimum that requires:

- direct pedestrian exposure or a documented/validated exposure proxy strategy;
- traffic/mobility exposure treatment;
- built-environment feature coverage and missingness semantics;
- outcome-population decision or explicit comparison protocol;
- a risk target that is mathematically defined and not merely a renamed event count;
- leakage-safe temporal windows and independent evaluation periods;
- evidence that each feature can be joined at the selected spatial and temporal grain.

Until those conditions are satisfied, `selection_status` remains `NOT_SELECTED` for the final
model-ready representation.
