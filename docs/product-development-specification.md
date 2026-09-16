# Product Development Specification

Status: **planning baseline**  
Scope source of truth: **Project Charter v1.1**  
Repository baseline audited: `40217fd2b0168ca974d4e681600ccd05e17aa912`

This document defines how the product must be developed while the remaining data and modeling decisions are progressively elaborated. It is intentionally stricter than a feature checklist: every analytical result must have a defensible data lineage, every model decision must be benchmarked, and every user-facing workflow must correspond to a real specialist task.

---

## 1. Why this specification exists

The current repository already proves that the application can ingest official ONSV workbooks, normalize Metropolitan Lima fatal pedestrian crash events, expose a model-independent API contract, and render an initial geospatial client.

That is an engineering starting point, not the final analytical product.

The project must not degrade into any of the following:

- a heat map of historical crash counts presented as risk;
- a CNN-RNN selected because it appears in the title rather than because the data representation supports it;
- a random train/test split that leaks spatial or temporal information;
- a synthetic `RiskProvider` used as model evidence;
- a polished map whose values cannot be explained, reproduced, or traced to sources;
- a web interface optimized for screenshots instead of specialist analysis tasks;
- a repository where architecture means only a folder tree.

The expected product is a serious analytical MVP that can be reviewed by road-safety specialists, GIS analysts, data engineers, software engineers, and public-sector technical staff without relying on simulated claims.

---

## 2. Product invariants

These constraints are not implementation suggestions.

1. The product analyzes **spatiotemporal pedestrian collision risk in Metropolitan Lima** and must support comparison between spatial units and periods.
2. Metropolitan Lima means the **43 districts of the Province of Lima**. Callao is outside the product scope unless a later approved scope change says otherwise.
3. Historical crash concentration is evidence of occurrence; it is **not, by itself, a comparable risk measure**.
4. Risk modeling must investigate variables related to at least the following conceptual families where defensible data exists:
   - pedestrian exposure or defensible exposure proxies;
   - motor-vehicle exposure/traffic;
   - road and built-environment characteristics;
   - temporal variation;
   - observed pedestrian crash outcomes.
5. The exact spatial unit, temporal interval, historical coverage, risk representation, recurrent variant, benchmark metrics, and acceptance thresholds remain open until profiling and benchmarking close them.
6. The software must contain a convolutional spatial component and a recurrent temporal component in the selected analytical architecture, but the concrete implementation is evidence-driven.
7. The output is analytical decision support. It is not an official classification, enforcement recommendation, emergency system, or automated institutional decision.
8. The user interface must expose source, period, spatial unit, model/data version, limitations, and enough context for a specialist to interpret a result.
9. A model result that cannot be traced to a reproducible data snapshot and model artifact is not a valid production result.
10. Optional capabilities may degrade explicitly; they must never fabricate values.

---

## 3. Scope baseline for the MVP

### 3.1 Mandatory product capabilities

The integrated MVP must provide:

1. **Data preparation**
   - acquire selected official/public sources reproducibly;
   - preserve immutable raw inputs or immutable source snapshots;
   - normalize source-specific schemas;
   - profile quality and coverage;
   - construct the selected spatial-temporal analytical dataset.

2. **Spatiotemporal modeling**
   - spatial representation compatible with a convolutional component;
   - temporal sequences compatible with a recurrent component;
   - a real baseline;
   - benchmarked CNN-RNN candidate configurations;
   - independent evaluation data.

3. **Comparable analytical results**
   - result per selected spatial unit and period;
   - comparison across units and/or periods;
   - representation selected by the benchmark and target formulation rather than hard-coded in advance.

4. **Geospatial analysis UI**
   - interactive map;
   - period selection;
   - spatial selection;
   - legend and non-color-only encoding;
   - zone/unit detail;
   - comparison workflow;
   - data/model provenance and limitations.

5. **Technical traceability**
   - source snapshot/version;
   - feature schema version;
   - spatial and temporal representation;
   - model version;
   - benchmark evidence;
   - generated-at/inference metadata.

### 3.2 Explicitly outside the MVP

Do not silently add:

- real-time incident monitoring;
- camera, sensor, or IoT ingestion;
- native mobile application;
- citizen incident reporting;
- emergency dispatch/management;
- enforcement or sanctions;
- person, vehicle, or plate recognition;
- automatic infrastructure recommendations;
- automatic institutional decisions;
- production integration with internal systems of public entities;
- operation as an official service with SLA;
- national scope;
- Callao.

---

## 4. Current repository state: what is real and what is not

### 4.1 ONSV data is real, but it is one layer

The normalized ONSV table currently produced by the repository is **not a mock**. It is derived from official ONSV fatal-crash and involved-person workbooks and is useful as a high-severity pedestrian crash outcome/event layer.

Its correct status is:

```text
REAL_SOURCE_LAYER
AUTHORITATIVE_FOR_ITS_PUBLISHED_SCOPE
NOT_FINAL_MODEL_READY_DATASET
NOT_ALL_PEDESTRIAN_COLLISIONS
NOT_A_STANDALONE_RISK_MEASURE
```

The current detailed ONSV open-data family is explicitly about **fatal road crashes**. Therefore the event table must never be described as all pedestrian collisions in Lima.

### 4.2 Current `RiskProvider`

The provider abstraction is useful because the application can keep a stable contract while the analytical implementation changes.

A deterministic/synthetic provider may remain for:

- UI development;
- API contract tests;
- empty/loading/error state tests;
- integration mechanics.

It is **never** benchmark evidence and must never be rendered without an unmistakable non-production marker when used interactively.

### 4.3 Current web application

The current web client is a vertical integration surface. It is not yet the final information architecture or validated specialist workflow.

### 4.4 Current architecture document

The current architecture captures the high-level flow but not enough responsibility, data lineage, model lifecycle, deployment, or interaction detail. This specification defines the constraints that the later C4 and deployment views must make explicit.

---

## 5. Data strategy

The analytical dataset is a **multi-source product**, not one downloaded file.

### 5.1 Dataset layers

Use the following conceptual layers:

```text
SOURCE SNAPSHOTS
  -> SOURCE-SPECIFIC NORMALIZATION
  -> CANONICAL EVENT / GEOSPATIAL / TEMPORAL TABLES
  -> FEATURE LAYERS
  -> SPATIAL x TEMPORAL ANALYTICAL TABLE/CUBE
  -> TRAIN / VALIDATION / TEST WINDOWS
  -> MODEL-SPECIFIC TENSORS
```

Never jump directly from a downloaded workbook to a tensor without a documented intermediate contract.

### 5.2 Source qualification statuses

Every candidate source receives one of:

```text
ACCEPTED
CANDIDATE
AUXILIARY
REJECTED
BLOCKED
```

and records:

```yaml
publisher:
source_url:
retrieved_at:
published_or_modified_at:
coverage_period:
geographic_coverage:
granularity:
license_or_access_status:
key_fields:
join_keys_or_spatial_join:
missingness:
known_biases:
role_in_model:
status:
reason:
```

### 5.3 Initial source qualification matrix

| Source family | Initial status | Intended role | Important limitation / required check |
|---|---|---|---|
| ONSV fatal crashes 2021-2025 | ACCEPTED | observed high-severity crash events/outcome layer | fatal crashes only; 2025 preliminary; exact temporal coverage must be snapshotted |
| ONSV people in fatal crashes 2021-2025 | ACCEPTED | identify pedestrian involvement/severity | same fatal-only scope |
| ONSV vehicles in fatal crashes 2021-2025 | CANDIDATE | vehicle/context features for crash events | useful only after field completeness and join quality are profiled |
| ONSV historical crashes 2008-2025 | AUXILIARY | historical trend/context | different aggregation/schema; do not merge as event-level records unless compatibility is proven |
| INEI Census 2017 REDATAM at block level | CANDIDATE | static population/socioeconomic exposure proxies | older but structurally detailed; must be treated as static context, not current pedestrian counts |
| INEI Census 2025 detailed releases | CANDIDATE | newer structural context | use only when equivalent granular fields are actually available and documented |
| Lima mobility/built-environment GIS layers from public GeoServer/GeoServidor services | CANDIDATE | crossings, signals, transit stops, cycling, road/intersection, zoning, land-use, congestion/context features | audit coverage, publication date, CRS, completeness, ownership and whether each layer covers the 43 districts |
| MTC national road network 2022-2025 | AUXILIARY | road attributes where applicable | national-road network is not the complete urban street network |
| MTC toll-station traffic flow | AUXILIARY | coarse traffic trend/reference | point/toll coverage is too coarse to be treated as citywide per-zone exposure without evidence |
| MML open mobility layers such as cycleways | CANDIDATE | built-environment/context features | verify update date, geometry quality, district coverage and stable identifiers |
| OpenStreetMap Peru extract | CANDIDATE_FALLBACK | complete road/POI context if official layers are insufficient | public but not official; record extract date, ODbL provenance and feature completeness |
| SENAMHI observations | CANDIDATE | temporal weather covariates | only if station coverage and temporal alignment are sufficient |
| Direct pedestrian-volume/count data | BLOCKED/RESEARCH_PRIORITY | preferred pedestrian exposure | no citywide source accepted yet; this is a material project risk |

### 5.4 Exposure is a first-class data risk

The model must not rename `crash_count` to `risk`.

Preferred order for pedestrian exposure:

1. direct pedestrian counts with spatial/temporal alignment;
2. a validated composite exposure estimate/proxy based on variables such as population/activity density, land use/POIs, transit access, and walkability;
3. a simpler proxy only if its limitations and sensitivity are quantified.

Any proxy must be named as a proxy in code, data dictionaries, model cards, and UI methodology. It must not be presented as measured pedestrian flow.

If no defensible exposure or proxy can be constructed, the team must raise an explicit scope/modeling decision. Silently changing the product into a fatal-crash-density map is not acceptable.

### 5.5 Vehicle exposure/traffic

Prefer spatially aligned traffic counts/flow where available. Toll-station totals are not automatically valid for neighborhood/grid exposure.

If direct citywide traffic is unavailable, candidate proxies must be benchmarked and documented, for example:

- road hierarchy/capacity;
- public mobility congestion layers;
- transit route density;
- road-network centrality/functional class;
- other defensible public mobility indicators.

### 5.6 Built environment

Candidate features may include, only when source evidence supports them:

- intersection density;
- pedestrian crossings;
- traffic signals;
- road class and number of lanes;
- cycling infrastructure;
- transit stops/stations;
- land use/zoning;
- education/health/commercial/recreation facilities;
- road-surface or geometry attributes;
- walkability-related network measures.

Feature inclusion is not based on availability alone. It must have a plausible relationship to the problem, usable coverage, acceptable missingness, and leakage-safe construction.

### 5.7 Freshness policy

"Newest" is not automatically "best".

Choose sources by **fitness for purpose**:

- dynamic variables should be temporally aligned with outcome periods as closely as practical;
- static structural variables may come from an older but consistent census or map when they are explicitly versioned;
- preliminary datasets can be used only with their cutoff documented;
- a newer source with partial/incompatible coverage must not silently replace a complete older source;
- every model dataset freezes source versions so a later upstream update cannot change a published benchmark retroactively.

---

## 6. Reproducible data lineage

Each raw source snapshot must have:

```yaml
source_id:
publisher:
source_url:
retrieved_at:
source_published_at:
content_hash:
media_type:
coverage:
license_or_terms:
```

Each normalized output must record:

```yaml
pipeline_version:
input_hashes:
schema_version:
row_count:
spatial_reference:
quality_report_id:
generated_at:
```

Each model-ready dataset must record:

```yaml
dataset_version:
feature_schema_version:
source_snapshot_ids:
spatial_unit_definition:
temporal_unit_definition:
coverage_start:
coverage_end:
row_or_cell_count:
zero_outcome_rate:
missingness_summary:
join_coverage:
split_definition:
content_hash:
```

A model artifact without this lineage is invalid for production integration.

---

## 7. Profiling before modeling

Profiling is a decision gate, not a notebook screenshot.

### 7.1 Required source-level measurements

For every candidate source measure where applicable:

- records/features;
- date range and effective cutoff;
- records by year/month/day/hour when available;
- geographic extent;
- records/features by district;
- coordinate validity;
- CRS and geometry validity;
- duplicates and duplicate keys;
- missingness per field;
- categorical cardinality and unknown values;
- join-key uniqueness;
- spatial join success rate;
- temporal join coverage;
- update/publication metadata;
- source-specific inconsistencies.

### 7.2 Required outcome profiling

Before selecting spatial/temporal granularity calculate for each candidate representation:

```text
number of spatial units
number of periods
number of unit-period cells
events per cell distribution
zero-event cell ratio
cells with sufficient covariate coverage
spatial coverage by district
temporal coverage by year/period
coordinate loss after filtering
```

Do this for multiple candidate spatial and temporal resolutions.

### 7.3 Data-quality gates

A source/feature cannot become a production feature until:

1. provenance is known;
2. semantic meaning is documented;
3. spatial/temporal granularity is understood;
4. join mechanism is reproducible;
5. missingness is measured;
6. leakage risk is assessed;
7. outliers/invalid values have a documented policy;
8. the feature has enough coverage for the chosen evaluation design.

Do not invent universal numeric thresholds before profiling. Thresholds are set from observed distributions and analytical requirements, then frozen before final training.

---

## 8. Spatial representation decision protocol

Do not commit to grid, road segment, intersection, or district before comparing them.

Candidate representations include:

### A. Regular grid

Advantages:

- natural tensor/image representation for CNNs;
- regular neighborhood structure;
- straightforward spatial joins and rasterized context.

Risks:

- severe sparsity at fine resolution;
- arbitrary boundary effects;
- cells differ in actual walkable/road area.

### B. Road segment / link

Advantages:

- closer to exposure and street-environment interpretation;
- useful for road-safety specialists.

Risks:

- irregular graph rather than natural image tensor;
- CNN formulation may require rasterization or graph-aware representation;
- source alignment can be difficult.

### C. Intersection / node

Advantages:

- meaningful for crossing-related risk;
- compact unit for intersection infrastructure.

Risks:

- excludes mid-block events unless explicitly assigned;
- network/topology quality becomes critical.

### D. District

Advantages:

- robust counts and easy interpretation.

Risks:

- too coarse to provide useful local analysis;
- only 43 units may underuse the spatial architecture;
- can hide intra-district variation.

### Decision evidence

Compare candidates using:

- event sparsity;
- covariate coverage;
- spatial resolution useful to specialists;
- representational compatibility with CNN-RNN;
- computational cost;
- stability across time;
- interpretability;
- sensitivity to unit boundaries.

The selected unit and rationale become an ADR and model-card field.

---

## 9. Temporal representation decision protocol

Candidate periods may include hourly bands, day/day-type, week, or month depending on source timestamps and sparsity.

Evaluate:

- event density per spatial unit-period;
- availability of exposure/context at the same temporal resolution;
- sequence length available for learning;
- seasonality/day-type effects;
- missing periods;
- usefulness to specialist tasks;
- leakage risk;
- computational cost.

A temporal interval is invalid if the model only appears to have more samples because repeated/static features dominate while outcomes are almost entirely zero.

---

## 10. Target/risk formulation

The exact mathematical output is intentionally open.

Candidate formulations can include:

- count/frequency conditional on exposure;
- normalized or relative risk score;
- event probability over a unit-period;
- ordinal risk level derived from a continuous model;
- ranking score for comparing unit-periods.

### Target decision requirements

The selected target must document:

```yaml
meaning:
unit:
spatial_support:
temporal_support:
source_fields:
derivation_formula:
exposure_treatment:
zero_handling:
interpretation:
what_it_does_not_mean:
```

A UI label such as `High risk` is not the target definition.

### No causal overclaim

Feature importance/association must not be presented as proof that a variable causes crashes. The MVP provides analytical association/risk estimation, not causal policy evaluation.

---

## 11. Benchmarking protocol

Benchmarking selects the defensible configuration; it does not decorate a preselected model.

### 11.1 Baseline hierarchy

At least one simple and one strong non-deep baseline should be considered where compatible with the target.

Candidate baseline families:

1. **Historical naive baseline**
   - previous-period rate/count;
   - moving historical average;
   - exposure-normalized historical rate when a defensible denominator exists.

2. **Statistical count baseline**
   - Poisson;
   - Negative Binomial;
   - hurdle/zero-inflated formulation if profiling demonstrates excess zeros/dispersion.

3. **Tabular machine-learning baseline**
   - gradient-boosted trees or equivalent for nonlinear feature interactions when appropriate.

The final benchmark must include at least one model that is meaningfully competitive, not only a deliberately weak baseline.

### 11.2 CNN-RNN candidate families

Only evaluate architectures compatible with the selected representation.

Examples:

```text
regular grid + sequence -> CNN encoder + LSTM
regular grid + sequence -> CNN encoder + GRU
regular raster sequence -> ConvLSTM candidate if justified
```

Do not use ConvLSTM merely because it combines convolution and recurrence. It is appropriate only when the tensor geometry and temporal sequence actually fit its assumptions.

### 11.3 Split strategy: leakage is a first-class concern

Do not use an unconstrained random row split as the primary final evaluation.

Required design:

- final independent **chronological holdout**;
- validation/training windows that respect time order (rolling/expanding origin where appropriate);
- at least one **geographic robustness** analysis or held-out spatial partition if sample size allows;
- preprocessing/scalers/encoders fitted only on training data;
- spatial/temporal feature computation audited so future/test information cannot leak backward.

If the model is used for historical risk estimation rather than future forecasting, the independent temporal holdout still tests whether the learned representation generalizes to an unseen period.

### 11.4 Metrics depend on target

Do not freeze metrics before the target.

Examples:

| Target type | Candidate primary/secondary metrics |
|---|---|
| count/frequency | MAE, RMSE, Poisson/Tweedie deviance, rank correlation |
| rare binary event | PR-AUC, recall/precision at operational top-k, Brier score/calibration; ROC-AUC only as secondary context |
| ordinal level | macro-F1, weighted kappa, class recall |
| ranking | nDCG@k, Recall@k, precision@k, rank correlation |
| continuous relative risk | MAE/RMSE plus calibration/ranking stability as appropriate |

Model selection must consider more than one metric when the task has both numerical and prioritization meaning.

### 11.5 Benchmark report

Every candidate row records:

```yaml
experiment_id:
data_version:
feature_schema_version:
spatial_unit:
temporal_unit:
target_definition:
split_definition:
model_family:
model_configuration:
seed:
metrics:
training_time:
inference_time:
parameter_count:
limitations:
```

The selected configuration must explain why it is preferable to the baseline and other candidates. If it does not outperform the baseline on the primary evidence, do not claim success; investigate formulation/data/model assumptions.

---

## 12. Model lifecycle and `RiskProvider`

The web/API layer must not know whether a result comes from LSTM, GRU, ConvLSTM, a baseline, or another candidate.

Conceptual contract:

```python
class RiskProvider(Protocol):
    def predict(self, query: RiskQuery) -> RiskResult: ...
    def compare(self, queries: list[RiskQuery]) -> list[RiskResult]: ...
    def map(self, query: RiskMapQuery) -> list[RiskMapItem]: ...
    def metadata(self) -> ModelMetadata: ...
```

Production metadata must include at least:

```yaml
model_id:
model_version:
model_family:
artifact_hash:
dataset_version:
feature_schema_version:
spatial_unit_version:
temporal_unit:
target_definition_version:
training_period:
test_period:
benchmark_summary:
created_at:
status:
```

Never load an artifact when its expected feature schema/data contract is incompatible with the running application.

---

## 13. Logical architecture

The project is an analytical web product. It does not need ERP-style policy layers or distributed microservices, but it does need explicit responsibilities.

### 13.1 C4 System Context

Actors:

- road-safety / urban-mobility specialist;
- traffic/transport professional;
- GIS / territorial-data analyst.

External systems/sources:

- official/public road-safety and geospatial data publishers;
- optional public contextual datasets.

System:

- Raster Analytics Web: prepares selected data, produces versioned spatiotemporal analytical results, and lets specialists explore and compare them.

### 13.2 C4 Container view

```text
[Specialist]
     |
     v
[Web Application: React/TypeScript]
     |
     | HTTPS/JSON
     v
[API: FastAPI]
     |       \
     |        \--> [Model Runtime / RiskProvider]
     v
[PostgreSQL + PostGIS]
     ^
     |
[Data + Feature Pipelines]
     ^
     |
[Versioned Source Snapshots]

[Training / Evaluation Pipeline]
     | reads versioned analytical dataset
     | writes model + benchmark metadata
     v
[Model Artifacts]
```

A local deployment may run several responsibilities in the same process/container. Logical separation is about ownership and coupling, not about forcing microservices.

### 13.3 Responsibility boundaries

#### `pipelines/ingestion`

Owns:

- source registry;
- source download/acquisition;
- snapshot metadata and hashes;
- raw immutability;
- source inventories.

Does not own feature engineering or model training.

#### `pipelines/profiling`

Owns:

- quality measurements;
- coverage reports;
- schema inspection;
- candidate-granularity statistics;
- source fitness evidence.

Does not silently mutate data.

#### `pipelines/processing`

Owns:

- source-specific normalization;
- canonical field names/types;
- source-level deduplication rules;
- CRS/date normalization;
- deterministic source joins such as crash-person relations.

#### `pipelines/features`

Owns:

- spatial joins;
- temporal joins;
- feature derivations;
- exposure proxies;
- neighborhood/window features;
- analytical table/cube construction;
- feature schema versioning.

#### `ml/datasets`

Owns:

- leakage-safe split definitions;
- temporal windows/sequences;
- tensor construction;
- training-only fit transformations.

#### `ml/baselines`

Owns statistical/naive/tabular benchmark models.

#### `ml/models`

Owns CNN-RNN candidate implementations and model-specific tensor expectations.

#### `ml/evaluation`

Owns metrics, experiment manifests, benchmark comparison, calibration/ranking diagnostics, and reproducibility reports.

#### `apps/api`

Owns:

- input validation;
- use-case orchestration;
- stable HTTP contracts;
- result/source/model metadata delivery;
- explicit errors.

It does not contain training logic or ad-hoc feature engineering.

#### `apps/web`

Owns specialist interaction, map/comparison presentation, filters, provenance/limitations presentation, accessibility and client state.

It does not compute the analytical model result.

### 13.4 Persistence

Use PostgreSQL + PostGIS when persistent spatial analysis is introduced.

Separate conceptually:

```text
source metadata
canonical normalized data
geometries/spatial units
feature datasets/versions
model metadata
analytical results/cache
```

Large raw datasets and binary model artifacts remain outside normal Git history.

---

## 14. Physical architecture and deployment

The initial deployable shape should remain simple:

```text
Browser
  -> Web static assets
  -> FastAPI
  -> PostgreSQL/PostGIS
  -> versioned model artifact available to API/model runtime
```

Batch data preparation/training executes separately from request-time inference.

Do not train models inside an HTTP request.

Containerization is acceptable for reproducibility, but a distributed production topology is not required to validate the MVP.

The later deployment diagram must identify:

- web build/runtime;
- API runtime;
- database;
- artifact/data volume locations;
- environment configuration;
- network relationships;
- reproducible startup/migrations.

---

## 15. API contract principles

Keep API output model-neutral and interpretation-aware.

Candidate result:

```json
{
  "spatial_unit_id": "...",
  "period": {
    "start": "...",
    "end": "..."
  },
  "value": 0.0,
  "representation": "relative_score",
  "label": null,
  "rank": null,
  "model": {
    "id": "...",
    "version": "..."
  },
  "dataset_version": "...",
  "feature_schema_version": "...",
  "sources": ["..."],
  "limitations": ["..."]
}
```

Fields such as `probability`, `label`, or `rank` appear only when the selected target gives them that meaning.

Required endpoint families are expected to cover:

```text
health
source/methodology metadata
spatial units
periods
risk/result query
map result query
comparison
model metadata
```

Do not expose model-framework internals to the frontend as required input parameters.

---

## 16. Web product specification

The UI is an analytical workspace, not a generic dashboard.

### 16.1 Primary specialist tasks

The product must make these tasks straightforward:

1. identify which spatial units show the highest modeled risk for a selected period;
2. inspect one unit and understand its value, period, source/data/model context and available contributing/context variables;
3. compare two spatial units for the same period;
4. compare the same unit across periods;
5. change time/spatial filters without losing orientation;
6. understand whether data/model limitations affect the current view;
7. distinguish modeled risk from raw historical crash occurrence.

### 16.2 Information architecture

#### Analysis map

Primary surface:

- map;
- spatial and temporal controls;
- risk legend;
- selected-unit panel;
- summary/rank where supported;
- visible active filters;
- data/model status;
- clear loading, empty and error states.

#### Comparison workspace

Supports:

- A vs B spatial comparison;
- period A vs period B temporal comparison;
- small number of clearly comparable attributes/series;
- consistent scales and definitions;
- links back to map context.

#### Detail

Shows:

- analytical result;
- representation/meaning;
- observed historical context separately from modeled value;
- period;
- spatial unit;
- feature/context values allowed by the model contract;
- model/data version;
- caveats.

#### Sources and methodology

Shows:

- source publishers;
- coverage;
- retrieval/snapshot dates;
- variable families;
- spatial/temporal unit definition;
- target definition;
- limitations;
- model version and benchmark summary.

### 16.3 Interaction heuristics

Apply at least:

- visibility of system status;
- terminology that matches road-safety/GIS users rather than implementation jargon;
- user control and reversible filter changes;
- consistency between map, comparison and detail;
- error prevention for incompatible periods/units;
- recognition over recall through visible filters/legends;
- efficient repeated comparison;
- minimalist analytical hierarchy;
- actionable error/empty messages;
- contextual help/methodology when needed.

### 16.4 Accessibility

Target WCAG 2.2 AA for the implemented flows where applicable.

For maps/charts specifically:

- color must not be the only carrier of risk information;
- provide text/labels/legend values and alternative list/table access to map results;
- meaningful UI and graphical objects need sufficient contrast;
- keyboard focus and control labels must be visible;
- tooltip-only information must have an accessible equivalent;
- selected/highlighted state cannot depend on hue alone.

### 16.5 Map technology decision

Leaflet is acceptable for the current vertical slice.

Before the final analytical map, compare whether current requirements justify staying with Leaflet or moving to a vector-WebGL library such as MapLibre GL JS.

Evaluate:

- polygon/grid/segment rendering volume;
- vector-tile need;
- style expressions;
- hover/select performance;
- accessibility integration;
- bundle/runtime complexity;
- team maintainability.

Do not migrate for novelty.

---

## 17. User stories

These are product-oriented starting stories. They must be reconciled with the approved requirements and traceability matrix before becoming final scope commitments.

### US-01 — Explore modeled risk by period

As a road-safety specialist, I want to select a period and view comparable risk results over Lima so I can identify areas that require closer analytical review.

Acceptance intent:

- current period is always visible;
- map/list values use one documented representation;
- result is not confused with raw crash count;
- provenance/model version is reachable;
- unsupported periods cannot be selected silently.

### US-02 — Inspect a spatial unit

As a GIS/territorial analyst, I want to select a unit and inspect its result and context so I can understand what the map value represents.

### US-03 — Compare spatial units

As a transport professional, I want to compare two units within the same period using the same definition/scale so I can identify meaningful differences.

### US-04 — Compare periods

As a mobility specialist, I want to compare one unit across two periods so I can examine temporal changes rather than a single aggregate condition.

### US-05 — Review historical occurrence separately

As a specialist, I want to see historical crash occurrence without conflating it with modeled risk so I can interpret the relationship between observed events and the model result.

### US-06 — Understand source and model limits

As an analyst, I want to inspect source coverage, model/data version and limitations so I can decide whether the result is suitable for my analysis.

### US-07 — Recover from unavailable analysis

As a user, I want a clear message when a period/unit/result cannot be computed so I do not interpret missing data as low risk.

### US-08 — Use results without relying on color

As a user, I want equivalent textual/tabular values and accessible controls so the analysis is usable when color perception or map interaction is limited.

---

## 18. Technical stories

### TS-01 — Immutable source snapshots

Implement source metadata/hashing so every analytical dataset can identify exact upstream inputs.

### TS-02 — Source qualification profiler

Generate machine-readable profiling reports for coverage, missingness, spatial/temporal validity, keys and joinability.

### TS-03 — Canonical geospatial model

Introduce explicit spatial-unit geometry contracts in PostGIS without prematurely fixing the final unit.

### TS-04 — Feature schema registry

Version analytical feature definitions and transformations, including proxy meaning and provenance.

### TS-05 — Leakage-safe dataset builder

Build training/validation/test windows with chronological separation and training-only fitted transforms.

### TS-06 — Baseline benchmark harness

Execute historical/statistical/tabular baselines through one experiment contract.

### TS-07 — CNN-RNN experiment harness

Execute model candidates through the same data split and metric contract used by baselines.

### TS-08 — Model artifact registry

Persist model metadata, artifact hash, compatible feature schema, data version and benchmark status.

### TS-09 — Production RiskProvider

Load only an approved compatible model artifact and fail explicitly on schema/version mismatch.

### TS-10 — Analysis API

Expose map/query/compare/model/source metadata without coupling the client to ML implementation.

### TS-11 — Specialist analysis UI

Implement map, details, comparisons, methodology, states and accessibility from the accepted interaction prototype.

### TS-12 — End-to-end analytical trace

Given a visible result, tests/diagnostics can trace it to the spatial unit, period, feature dataset, model artifact and sources.

---

## 19. Code documentation rules

Comments are required when they preserve knowledge that is not obvious from the code.

Comment/docstring examples that **are required**:

- why a data exclusion exists;
- why a source field maps to a canonical concept;
- CRS conversions and spatial assumptions;
- non-obvious geospatial joins/buffers;
- exposure-proxy formula/assumption;
- temporal window semantics;
- leakage guards;
- tensor dimension/order assumptions;
- target transformation;
- model artifact compatibility rules;
- numerical stability handling;
- externally constrained API behavior.

Do **not** add comments that simply paraphrase obvious syntax.

Public functions/contracts and analytical transformations should have concise docstrings where the semantic contract is not evident from types alone.

---

## 20. Testing strategy

### Data tests

- source hash/metadata;
- schema/header changes detected;
- coordinate ranges;
- geometry validity/CRS;
- duplicate keys;
- date/time validity;
- district/province filtering;
- source join coverage;
- feature missingness policy;
- spatial join determinism;
- train/test temporal boundary;
- no future-data leakage.

### ML tests

- deterministic experiment manifests with seeds;
- tensor shapes;
- sequence ordering;
- training-only preprocessing;
- baseline execution;
- model smoke training on tiny fixture;
- metric correctness;
- artifact save/load parity;
- inference schema compatibility;
- benchmark report generation.

### API tests

- validation;
- unknown spatial unit/period;
- model unavailable/incompatible;
- empty result is not converted to zero risk;
- comparison uses compatible representation/version;
- provenance fields present.

### Web tests

- filter state;
- map/list selection synchronization;
- loading/empty/error states;
- A/B comparison;
- period comparison;
- keyboard/control semantics;
- methodology/provenance access;
- non-color-only result representation.

### End-to-end tests

At minimum:

```text
selected period -> map results -> select unit -> detail
selected period -> compare two units
selected unit -> compare two periods
result -> source/model metadata
unsupported period -> explicit non-misleading state
```

---

## 21. Observability and reproducibility

At MVP scale, keep observability proportionate but useful.

Log/measure at least:

- data pipeline run ID and source snapshot IDs;
- rows/features in/out of transformations;
- rejected/invalid geospatial records;
- model artifact/version loaded;
- inference errors and latency;
- API request/error timing;
- frontend fetch failures without leaking sensitive configuration.

Experiments must be reproducible from:

```text
code commit
+ data snapshot/version
+ feature schema
+ split definition
+ configuration
+ seed
```

---

## 22. Risk register for technical execution

### R1 — Fatal-only outcome source is narrower than the intended problem

Trigger: no acceptable non-fatal collision source is found and final claims imply all pedestrian collisions.

Response:

- continue using ONSV fatal events as a valid high-severity layer;
- research other verifiable public/official sources;
- never generalize silently;
- if final product must be narrowed to fatal/high-severity risk, treat that as an explicit scope decision and update requirements/validation language.

### R2 — No defensible pedestrian exposure source

Response:

- search direct counts first;
- evaluate a documented composite proxy;
- perform sensitivity/ablation analysis;
- preserve proxy labeling;
- raise scope/model decision if no defensible alternative exists.

### R3 — Traffic exposure too coarse

Response:

- do not broadcast toll counts across Lima;
- evaluate local/public mobility layers and road-network proxies;
- quantify spatial coverage.

### R4 — Spatial/temporal cells are too sparse

Response:

- compare coarser units/periods;
- evaluate count-model/zero-aware baselines;
- do not oversample in a way that changes the meaning of the target;
- document the selected compromise.

### R5 — CNN-RNN does not beat baseline

Response:

- inspect representation, features, target, split and data sufficiency;
- record failed experiments;
- do not tune on the final test set;
- do not weaken the baseline or metrics to manufacture success.

### R6 — Source vintages do not align

Response:

- distinguish static vs dynamic variables;
- snapshot vintages;
- test sensitivity to mismatched years;
- exclude variables that cannot be interpreted responsibly.

### R7 — Map communicates false precision

Response:

- use spatial units consistent with data/model resolution;
- expose limitations;
- avoid point-level implication when model operates on coarse cells;
- keep observed events visually distinct from modeled outputs.

### R8 — Specialist workflow becomes secondary to visual polish

Response:

- validate task flows before cosmetic refinement;
- use heuristic evaluation and specialist feedback;
- require map/detail/compare/methodology tasks to pass acceptance scenarios.

---

## 23. Implementation order

Functionality and evidence should advance together.

### P0 — Specification and source inventory

- adopt this specification;
- maintain the source qualification registry;
- synchronize architecture documentation;
- keep synthetic provider clearly non-production.

### P1 — Data profiling and qualification

- profile ONSV layers in full;
- acquire/profile candidate exposure, traffic and built-environment sources;
- produce coverage/joinability reports;
- close or escalate data-source risks.

Gate: enough defensible inputs exist to formulate candidate analytical datasets.

### P2 — Spatial/temporal representation experiments

- build candidate units/periods;
- quantify sparsity/coverage;
- select or narrow candidates;
- record ADR.

Gate: chosen representation is both useful and learnable.

### P3 — Feature and target specification

- define feature schema;
- define exposure treatment;
- define target alternatives;
- implement leakage-safe dataset builder;
- freeze benchmark protocol before final model selection.

### P4 — Baselines

- historical/statistical/tabular baselines as appropriate;
- diagnostics for zeros/calibration/ranking;
- independent evaluation infrastructure.

### P5 — CNN-RNN benchmarking

- execute compatible CNN-RNN candidates;
- compare on identical splits/metrics;
- perform ablations where they answer a real question;
- select configuration only from evidence.

### P6 — Production analytical integration

- model registry/artifact metadata;
- production RiskProvider;
- PostGIS-backed spatial/period metadata and result flow;
- API compatibility/error behavior.

### P7 — Validated specialist web experience

- high-fidelity interaction prototype;
- map/detail/comparison/methodology implementation;
- accessibility and heuristic review;
- specialist task validation.

### P8 — Integrated verification and validation

- end-to-end scenarios;
- independent test evaluation;
- robustness/limitations report;
- specialist functional validation;
- reproducibility package and technical documentation.

---

## 24. Pull-request evidence rules

A capability may be described using these evidence states:

```text
PLANNED
IMPLEMENTED_NOT_EXECUTED
PROVEN_WITH_FIXTURE
PROVEN_WITH_REAL_SOURCE
BENCHMARKED
VALIDATED_WITH_SPECIALIST
BLOCKED
REJECTED
```

Do not use `BENCHMARKED` for a synthetic provider or unit-test fixture.

Do not use `PROVEN_WITH_REAL_SOURCE` when the test only exercises handcrafted data.

---

## 25. Forbidden shortcuts

Do not complete future iterations by:

- calling ONSV fatal events the complete project dataset;
- calling historical event density "risk" without a documented target/exposure formulation;
- calling synthetic provider output model validation;
- selecting LSTM, GRU or ConvLSTM before data representation evidence;
- using a random record split as the only final evaluation;
- fitting preprocessing on all data before splitting;
- using final test data for iterative model selection;
- choosing a weaker baseline to make the CNN-RNN appear better;
- inventing pedestrian counts or traffic values for missing areas;
- treating a proxy as measured exposure;
- joining sources with incompatible geography/time without recording the assumption;
- using a newer but incomplete source merely because it is newer;
- hard-coding risk thresholds without a derivation/validation rule;
- hiding model/data limitations from the web interface;
- encoding risk only by map color;
- using an attractive dashboard as evidence of usability;
- adding microservices, queues, caches, or infrastructure without a measured need;
- turning architecture documentation into only a repository tree;
- filling code with comments that restate obvious lines;
- claiming adoption/endorsement by an entity that has not provided it.

---

## 26. Decisions that remain open and how they close

| Decision | Current state | Evidence required to close |
|---|---|---|
| all-collision vs fatal/high-severity outcome coverage | OPEN | accepted outcome sources and scope review |
| pedestrian exposure source/proxy | OPEN / HIGH PRIORITY | source profiling, coverage and proxy validation/sensitivity |
| traffic exposure source/proxy | OPEN | source profiling and spatial/temporal alignment |
| final spatial unit | OPEN | sparsity, coverage, interpretability and model-representation comparison |
| final temporal unit | OPEN | density, coverage, sequence utility and specialist task needs |
| target/risk representation | OPEN | data distributions, exposure treatment and benchmark design |
| LSTM vs GRU vs ConvLSTM/other compatible recurrent integration | OPEN | common benchmark on selected representation |
| primary model metrics | OPEN | target definition + operational analytical task |
| acceptance threshold vs baseline | OPEN | pre-registered benchmark criterion before final test |
| Leaflet vs MapLibre/other map renderer | OPEN | interaction/performance/accessibility prototype evidence |
| exact UI visual system | OPEN | high-fidelity prototype + heuristic/accessibility review + specialist feedback |

---

## 27. Definition of Done for the analytical MVP

The MVP is not done until all of the following are true:

- selected source snapshots are reproducible and documented;
- every production feature is defined and traceable;
- selected spatial/temporal representation has profiling evidence;
- target/risk meaning is mathematically documented;
- baseline and CNN-RNN candidates are evaluated on the same leakage-safe protocol;
- final model evidence uses an independent test partition;
- production model artifact is tied to dataset/feature versions;
- API returns traceable analytical results and fails explicitly when unavailable;
- web supports map, spatial comparison, temporal comparison, detail and methodology;
- observed historical occurrence is distinguishable from modeled risk;
- accessibility does not rely on color alone;
- critical end-to-end flows pass without blocking defects;
- specialist validation covers the critical identification/comparison tasks;
- limitations and unresolved data risks are documented rather than hidden.

---

## 28. Research references constraining implementation

These references guide the plan; they do not freeze implementation choices when local evidence contradicts a detail.

### Official/current public data

- Observatorio Nacional de Seguridad Vial, Datos Abiertos: https://www.onsv.gob.pe/datosabiertos
- ONSV, Informe de Siniestralidad de tránsito fatal con peatones 2024: https://www.onsv.gob.pe/post/informe-de-siniestralidad-de-transito-fatal-con-peatones-2024/
- MTC, Red vial nacional 2022-2025: https://www.datosabiertos.gob.pe/dataset/red-vial-nacional-del-sistema-nacional-de-carreteras-2022-2025-ministerio-de-transportes-y
- MTC open-data group, including toll traffic-flow datasets: https://www.datosabiertos.gob.pe/group/ministerio-de-transportes-y-comunicaciones
- INEI census portal: https://www.inei.gob.pe/estadisticas/censos/
- INEI Censos 2017 / REDATAM: https://censo2017.inei.gob.pe/
- MML, Ciclovías existentes en Lima Metropolitana: https://www.datosabiertos.gob.pe/dataset/ciclov%C3%ADas-existentes-en-lima-metropolitana-municipalidad-metropolitana-de-lima-mml

### Pedestrian-risk research

- Guo, M., Janson, B., & Peng, Y. (2024). *A spatiotemporal deep learning approach for pedestrian crash risk prediction based on POI trip characteristics and pedestrian exposure intensity*. Accident Analysis & Prevention, 198, 107493. https://doi.org/10.1016/j.aap.2024.107493
- Hu, Y., Chen, L., & Zhao, Z. (2024). *How does street environment affect pedestrian crash risks? A link-level analysis using street view image-based pedestrian exposure measurement*. Accident Analysis & Prevention, 205, 107682. https://doi.org/10.1016/j.aap.2024.107682

These studies are particularly important because they reinforce that exposure and the street/built environment materially affect interpretation of pedestrian crash frequency. They are not evidence that their exact architectures or variables should be copied into Lima.

### Architecture and UX

- C4 model diagrams: https://c4model.com/diagrams
- C4 container diagram guidance: https://c4model.com/diagrams/container
- Nielsen Norman Group, 10 usability heuristics: https://www.nngroup.com/articles/ten-usability-heuristics/
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/

---

## 29. Instruction for future implementation iterations

For each substantial analytical change:

```text
state the question
-> identify source/evidence
-> profile/reproduce current behavior
-> define acceptance evidence
-> implement the smallest coherent responsibility
-> add focused tests
-> execute on fixture
-> execute on real source where applicable
-> record result/limitation
-> only then promote the decision
```

Do not interpret "iterative" as permission to skip the decision evidence. Iterations may refine implementation, but each accepted decision must remain traceable to data, requirements, benchmark results, or specialist validation.
