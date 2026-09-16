# Feature coverage evidence

Status: **real-source coverage measured; feature semantics remain conservative**

This document records the live coverage audit executed against the qualified MINAM / Desarrollo
Orientado al Transporte ArcGIS layers. It is evidence for feature admissibility and representation
selection; it is not evidence that a source is complete or that an absent feature equals zero.

The reproducible audit is implemented in `.github/workflows/feature-coverage-audit.yml` and is manual
because availability of external public services must not determine ordinary repository CI health.
The compact machine-readable evidence is stored in `data/features/coverage-evidence.json`.

## 1. Audit provenance

The accepted audit completed successfully on 2026-09-16:

```text
workflow     Feature coverage audit
run id       35151305930
head sha     db9200eec33b0d1fe61bf429f30dd5e369669e21
result       success
```

The run downloaded fresh source snapshots, measured feature intersections against each candidate
analytical representation and uploaded the detailed report as an artifact.

## 2. Structural-support mask

The full project boundary creates many geometrically valid cells that do not correspond to the
urbanized/support area described by the zoning source. The zoning mask reduces the candidate grid:

| Representation | Full boundary | Zoning-supported | Reduction |
| --- | ---: | ---: | ---: |
| 500 m | 11,111 | 8,494 | 23.6% |
| 1,000 m | 2,899 | 2,238 | 22.8% |
| 2,000 m | 783 | 620 | 20.8% |

This mask is used only to avoid treating unsupported peripheral space as equivalent analytical urban
space. It must never be interpreted as pedestrian exposure, population or risk.

## 3. Observed source coverage

The table below reports the share of analytical units intersecting at least one observed source
geometry. `Observed` means the source contains geometry there. It does **not** prove that the source
contains every real-world object of that type.

| Candidate feature | District | 500 m supported | 1 km supported | 2 km supported |
| --- | ---: | ---: | ---: | ---: |
| Signalized intersections | 83.7% | 8.9% | 16.1% | 24.4% |
| Transit stops | 95.3% | 11.2% | 19.2% | 27.4% |
| Transport routes | 83.7% | 15.9% | 23.1% | 30.5% |
| Pedestrian crossings | 16.3% | 0.5% | 1.0% | 1.8% |
| Zoning | 100.0% | 100.0% | 100.0% | 100.0% |

The audit therefore supports different conclusions for different layers.

### Zoning

Zoning is the strongest structural layer currently available. Every zoning-supported analytical unit
intersects zoning geometry, and all 43 districts are represented after clipping to the project scope.
This supports its use as structural context and as a support mask. It still does not make zoning an
exposure measure, and its category vocabulary must be audited before composition features are frozen.

### Transit stops

Transit stops have broad district presence but sparse grid-level observations. They remain a useful
pedestrian-activity proxy candidate, especially for ablation and local context, but source absence
cannot yet become `0 stops` unless completeness is established independently.

### Transport routes

Route geometry reaches a larger share of supported grid cells than the other mobility layers. Route
length density is a legitimate geometric context feature, but route presence or route length is not
measured vehicle flow or pedestrian flow.

### Signalized intersections

Signalized intersections remain a built-environment candidate. Fine-grid absence is unresolved, so
unobserved cells must preserve missing/coverage state rather than receive a fabricated zero.

### Pedestrian crossings

The crossing source is unsuitable as a citywide numeric density under the current evidence. Only 7 of
43 districts and roughly 0.5-1.8% of supported grid units contain observed crossing geometry. It
remains auxiliary and may only be used with an explicit source-coverage mask or in a local analysis.

## 4. Consequence for feature transformation

Two model-independent transformations are now implemented:

```text
point density
  observed source points / analytical-unit area

line-length density
  clipped source line kilometres / analytical-unit area
```

Point observations exactly on a shared boundary are assigned deterministically to one analytical unit
to avoid double counting. Line features are clipped before their length is accumulated; a complete
route is never counted in every unit it touches.

The transformation layer deliberately emits values only for units with observed source geometry.
Unobserved units remain absent until source-coverage semantics determine whether they are `true_zero`,
`missing`, `outside_source_coverage` or another explicit dataset state.

## 5. What is still unresolved

This audit does not close the analytical dataset. The next evidence required is:

1. zoning category/schema profiling before land-use composition is generated;
2. direct or validated pedestrian-exposure strategy;
3. traffic-volume/exposure strategy distinct from route geometry;
4. population/census extraction and spatial alignment evidence;
5. outcome-population sensitivity (`pedestrian_linked_fatal` versus strict `ATROPELLO`);
6. ablation plan for each proxy/context family;
7. final representation selection after candidate features are assembled and missingness is measured.

Until those items are resolved, the feature catalog remains a candidate contract rather than a frozen
model-ready dataset.
