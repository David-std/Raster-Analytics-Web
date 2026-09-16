# Data source qualification

This document is the canonical P1 record for data-source fitness, profiling findings, known gaps, and the gates that must be satisfied before spatial/temporal representation and target design are frozen.

It does **not** define the final model target, spatial unit, temporal interval, exposure formula, or CNN-RNN variant. Those decisions depend on evidence produced here and in the following representation experiments.

## 1. Analytical data requirement

The product is intended to support spatiotemporal comparison of pedestrian-collision risk across Lima Metropolitana. Historical collision concentration is an observed outcome layer, not a complete risk measure by itself.

The analytical dataset therefore needs, as far as defensible sources permit:

```text
observed pedestrian-collision outcomes
        +
pedestrian exposure or a validated proxy
        +
vehicle/traffic exposure or a validated proxy
        +
road and built-environment context
        +
temporal context
        +
reproducible spatial geometry
        ->
spatial-unit x period analytical dataset
```

A missing role must remain visible as a gap. It must never be replaced with fabricated observations or an undocumented proxy.

## 2. Qualification dimensions

A source is assessed on the following dimensions before it can be promoted from research material to an analytical input:

1. **Authority and provenance**: publisher, source URL, publication/update information, reproducible snapshot or query.
2. **Semantic fit**: what the records actually measure and whether that meaning matches the proposed analytical role.
3. **Geographic fit**: extent, coverage of the 43 districts of the Province of Lima, and any out-of-scope Callao/neighboring records.
4. **Temporal fit**: reference period, update cadence, partial years, temporal resolution, and compatibility with outcome periods.
5. **Spatial grain**: point, road segment, route, polygon, station, census unit, or aggregate area.
6. **Temporal grain**: event, hourly, daily, weekly, monthly, annual, or static snapshot.
7. **Completeness and missingness**: null patterns, absent areas, missing periods, and whether absence means zero or unknown.
8. **Joinability**: identifiers, coordinates, geometries, CRS, and spatial/temporal join coverage.
9. **Selection bias**: whether records describe the population of interest or only a selected subset, such as vehicles involved in fatal crashes.
10. **Leakage risk**: whether a feature could encode information that would only be known after the target event.
11. **Reproducibility and access**: stable download/query path, licensing/reuse conditions, hashes, and versioning feasibility.
12. **Model role**: outcome, direct exposure, exposure proxy, built environment, geometry, temporal context, or auxiliary validation/context.

The source registry is machine-readable at `data/sources/qualification.json`. Its evidence state records what has actually been verified, not what is merely planned.

## 3. Current readiness

The current source audit deliberately reports the dataset as **not model-ready**.

```text
outcome              PARTIAL_SCOPE
pedestrian exposure  RESEARCH_REQUIRED
traffic exposure     RESEARCH_REQUIRED
built environment    RESEARCH_REQUIRED
analysis geometry    RESEARCH_REQUIRED
temporal context     READY
```

This is a desirable result at P1: it prevents later stages from treating the first available tables as if they already formed a defensible risk dataset.

## 4. Outcome layer: ONSV detailed fatal crashes

### 4.1 What is proven

The official ONSV open-data publication currently provides detailed national files for:

- fatal road crashes, 2021-2025 preliminary;
- people involved in fatal road crashes, 2021-2025 preliminary;
- vehicles involved in fatal road crashes, 2021-2025 preliminary;
- a separate historical crash summary for 2008-2025 preliminary.

Source: <https://www.onsv.gob.pe/datosabiertos>

The ingestion pipeline downloads the official workbooks and joins crash/person records through the crash identifier. For Lima Province, the current normalized table contains **897 fatal crashes linked to at least one person classified as PEATON**, with **897/897 valid coordinate pairs** and no exact duplicate rows in the generated table.

Observed event coverage is:

| Year | Pedestrian-linked fatal crashes | First observed date | Last observed date |
| --- | ---: | --- | --- |
| 2021 | 179 | 2021-01-01 | 2021-12-31 |
| 2022 | 198 | 2022-01-01 | 2022-12-31 |
| 2023 | 232 | 2023-01-02 | 2023-12-30 |
| 2024 | 233 | 2024-01-02 | 2024-12-31 |
| 2025 | 55 | 2025-01-04 | 2025-04-02 |

The detailed 2025 file therefore does not currently represent a complete calendar year and must not be compared with complete years as if exposure time were identical.

The generic profile also identified substantial missingness in some fields:

- `vehicles_damaged`: about 79.7% null;
- `vertical_sign_exists`: about 85.8% null;
- `horizontal_sign_exists`: about 85.8% null.

Those fields cannot be promoted into model features without a missingness strategy and an assessment of whether missingness is systematic by year/location.

### 4.2 Important semantic finding: pedestrian-linked crash is not automatically `ATROPELLO`

The first normalized table was correctly named `lima_pedestrian_fatal_crashes.csv`: its inclusion rule is based on a linked person classified as `PEATON`.

The source-specific P1 audit found the following recorded crash classes among the 897 rows:

| Recorded class | Rows |
| --- | ---: |
| ATROPELLO | 605 |
| ATROPELLO FUGA | 234 |
| DESPISTE | 23 |
| CHOQUE | 21 |
| ESPECIAL | 6 |
| VOLCADURA | 4 |
| CHOQUE CON OBJETO FIJO | 2 |
| CHOQUE FUGA | 1 |
| FERROVIARIO | 1 |

Thus **839 rows** have a recorded class containing `ATROPELLO`, while **58 rows** are pedestrian-linked fatal crashes with another recorded class. Those 58 rows include 59 pedestrian fatalities.

This creates two defensible *candidate populations*, not one silently chosen target:

```text
A. strict fatal-atropello population
   recorded crash class contains ATROPELLO

B. broader fatal pedestrian-collision population
   fatal crash has a linked person classified as PEATON
```

P1 does not select between A and B. The choice must be documented during target specification because it changes the meaning of the model, the sample size, and the wording that can be shown to users.

### 4.3 District coverage

The 897-row layer contains events in **42 of the 43** Lima Metropolitana districts. `SANTA MARIA DEL MAR` has no observed row in the current period. This must not be treated automatically as evidence of zero risk.

A model-ready spatial table must distinguish at least:

```text
observed zero events
no event in available outcome records
missing covariates
source not covering the unit
out-of-scope unit
```

Those states are analytically different.

### 4.4 Fatal-only limitation

The detailed ONSV open files are an authoritative source for their published scope, but they cover **fatal crashes**. They do not provide a complete event-level file of every pedestrian collision in Lima through the same open-data publication.

The public SRATMA/ONSV crash viewer exposes a broader interactive crash universe with filters including source, year, UBIGEO, date and crash class:

<https://sratma.mtc.gob.pe/SRATMA/mapa/>

However, P1 has not yet proven a stable, documented, reusable machine-readable public export/API from that viewer. Therefore it is registered as `BLOCKED` rather than being scraped opportunistically and presented as a reliable source.

**P1 outcome conclusion:** the ONSV fatal layer is retained, but the final product target remains `PARTIAL_SCOPE` until the project either obtains a broader event source or explicitly validates a severe/fatal-risk scope change.

## 5. Pedestrian exposure

### 5.1 Why exposure is not optional conceptually

A place can record more pedestrian crashes simply because substantially more people walk there. Comparing raw crash counts without exposure can therefore conflate collision opportunity with risk conditional on exposure.

For this project, direct pedestrian exposure would ideally be represented by observed pedestrian counts at a useful location/time grain. If such a citywide source cannot be obtained, a proxy may be constructed only if its interpretation and limitations are explicit and validated.

### 5.2 Direct pedestrian counts: current blocker

The ATU Plan de Movilidad Urbana confirms that a substantial mobility study exists, but the currently reviewed public plan/report material does not by itself prove that reusable station-level or segment-level pedestrian count microdata can be downloaded for model construction.

The catalog therefore records direct PMU pedestrian/traffic microdata as `BLOCKED`, with the next action to locate or request machine-readable counts with location and time metadata.

### 5.3 Candidate proxy signals

Several sources may contribute to a pedestrian-exposure proxy, but no single one can be renamed as pedestrian volume:

- **ATU Metropolitano validations**: the open-data portal provides validations by station, period and day type. This is direct transit demand for the BRT system and can be a useful local activity signal around stations, but it covers a corridor rather than all Lima.
- **OSITRAN/rail passenger traffic**: useful for rail-served areas and temporal demand context, not a citywide pedestrian surface.
- **MINAM/IMP public-transport stops and routes**: spatial accessibility/activity opportunity, but stop/route presence is not a count of pedestrians.
- **INEI population/census variables**: useful static population/activity context; resident population is not pedestrian flow.
- **POIs and urban activity features**: possible fallback proxy components where official layers are insufficient, but provenance and coverage bias must be measured.

Any proxy formulation must later be accompanied by:

```text
component definition
normalization rule
spatial aggregation rule
temporal availability
coverage mask
sensitivity/ablation analysis
validation against observed demand/count data where available
```

**P1 pedestrian-exposure conclusion:** `RESEARCH_REQUIRED`. No direct citywide pedestrian count source is currently accepted.

## 6. Vehicle/traffic exposure

No reviewed source currently qualifies as direct, citywide vehicle exposure at the spatial/temporal resolution likely needed for a detailed Lima risk surface.

Important distinctions:

- ONSV vehicle records contain **vehicles involved in fatal crashes** and are outcome-conditioned; they must not be used as ambient traffic exposure.
- MTC toll flow is direct traffic flow at toll locations, but those stations are too spatially sparse/coarse to represent citywide urban traffic.
- MINAM `Congestion Vehicular` is a real layer but the live audit found only **22 line features** in a small central-Lima extent. Congestion class is not equivalent to traffic volume.
- Conventional transit-route geometry indicates service corridors but not actual vehicle counts.
- Direct ATU/MML traffic-count microdata remains a research priority.

**P1 traffic-exposure conclusion:** `RESEARCH_REQUIRED`.

## 7. Built environment and mobility layers

The MINAM `Desarrollo_Orientado_a_Transporte` ArcGIS service is accessible and queryable. P1 executes metadata/count/extent probes rather than assuming that a layer name implies citywide suitability.

Source service: <https://geoservidorperu.minam.gob.pe/arcgis/rest/services/CS/Desarrollo_Orientado_a_Transporte/MapServer>

Live findings from the current audit are:

| Layer | Features | Geometry | Observed year | Current use status |
| --- | ---: | --- | --- | --- |
| Intersecciones Semafo Lima | 1,421 | Point | 2021 | candidate built-environment feature |
| Paraderos IMP | 3,262 | Point | 2021 | candidate activity/accessibility proxy + context |
| Cruces Peatonales | 405 | Point | 2021 | auxiliary only; limited extent |
| Rutas Convencionales | 278 | Polyline | 2021 | candidate mobility/context layer |
| Tipos Vias Transporte | 349 | Polyline | 2021 | candidate road/context layer; not a complete street graph by count alone |
| Congestion Vehicular | 22 | Polyline | 2021 | auxiliary only; limited central extent |
| Zonificacion Urbana Lima | 87,858 | Polygon | 2021 | strong candidate contextual/geometry layer |

### 7.1 Coverage is not uniform

Two findings are especially important for later feature engineering:

- `Cruces Peatonales` covers a visibly limited central extent. A spatial unit outside that extent must be marked **unknown/not-covered**, not assigned `crossing_count = 0` as if the source proved no crossing exists.
- `Congestion Vehicular` is even narrower, with only 22 features. It cannot be extrapolated as citywide traffic exposure.

Conversely, `Zonificacion Urbana Lima` contains all 43 Lima districts in its district attribute, but also includes out-of-scope neighboring areas such as Callao districts and Chilca. Every analytical extraction must be spatially clipped to the project boundary.

### 7.2 2021 structural vintage

The audited MINAM layers currently expose `Anio = 2021`. This does not automatically disqualify them: road type, zoning and some infrastructure features change more slowly than traffic demand. It does mean that their use must be treated as a structural snapshot rather than time-varying truth for 2024/2025.

Where a newer equivalent source is found, selection will consider coverage and semantics as well as date. `newer` is not synonymous with `better` if the newer source is incomplete or less joinable.

## 8. Geometry boundary

The canonical project boundary is the **43 districts of the Province of Lima**. INEI uses the name `Lima Metropolitana` for this set under Law 31140.

Reference: <https://www.inei.gob.pe/peru_en_cifras/>

The repository contains `data/reference/lima_metropolitana_districts.json` as a name-level validation reference. This is not yet the final polygon geometry source.

P1 does not choose the final analytical unit. Candidate units to examine in P2 include:

```text
regular grid cells
road segments
intersections / nodes
administrative areas for aggregation or reporting
```

Districts are useful reporting/coverage boundaries but are likely too coarse to be assumed as the model unit without testing.

## 9. Temporal alignment rules

Before sources are joined, every feature must be classified as one of:

```text
time-varying observation
period aggregate
structural snapshot
static reference
```

Rules:

1. A partial outcome year is never silently normalized as a complete year.
2. A structural 2021 layer may be joined to later outcomes only as an explicitly static/structural covariate.
3. Dynamic demand/weather/traffic features must respect their own timestamps and the model prediction/analysis window.
4. Features derived using future observations relative to a target period are leakage and must be rejected from predictive/forward-looking experiments.
5. If the final use remains contemporaneous risk estimation rather than forecasting, temporal semantics must still state which period each covariate represents.

## 10. Source-specific missingness versus true zero

Every feature layer produced after P1 must carry enough metadata to distinguish:

```text
value observed = 0
value observed > 0
source covers cell but value missing
source does not cover cell
source unavailable for period
not applicable
```

This is mandatory for spatial counts such as crossings, stops, facilities and traffic observations. Treating uncovered geography as zero would create false spatial patterns that a CNN could learn as if they were real infrastructure differences.

## 11. Join strategy requirements

P1 does not perform final feature joins, but it defines the contracts P2/P3 must satisfy.

### Event -> spatial unit

- retain original WGS84 coordinates and source ID;
- transform through an explicit projected CRS for metric operations;
- preserve the spatial-unit version/hash used for assignment;
- quantify unassigned/outside-boundary events;
- never silently snap a point across a large distance.

### Static feature -> spatial unit

- use intersection/count/length/area/distance semantics appropriate to feature geometry;
- record source-coverage mask separately from feature value;
- retain source vintage.

### Time-varying feature -> unit-period

- define aggregation window explicitly;
- retain original timestamp grain;
- document interpolation/imputation;
- calculate join coverage by unit and period.

## 12. P1 gates before P2/P3

P1 is considered sufficient to start representation experiments when the following are true:

- the outcome population alternatives are explicitly recorded;
- source cutoffs and fatal-only scope are visible;
- all candidate feature sources have a provenance record;
- at least one defensible geometry path can be tested;
- direct exposure gaps and proxy candidates are explicit;
- source coverage masks can be generated rather than assuming absence = zero;
- machine-readable profiling can be rerun;
- no source is admitted merely because it is convenient.

P1 does **not** require every source to be accepted. Some gaps may legitimately remain `BLOCKED` and become scope/model decisions later.

## 13. Highest-priority unresolved work

The next data research tasks are ordered by analytical impact:

1. **Broaden/confirm the outcome definition.** Determine whether SRATMA/another official source exposes a stable machine-readable event dataset for non-fatal pedestrian collisions. In parallel, resolve the strict `ATROPELLO` vs broader pedestrian-linked fatal-event semantics with domain review.
2. **Direct pedestrian exposure.** Locate/request PMU or other official pedestrian-count microdata. If unavailable, design proxy candidates but do not accept them until they are validated.
3. **Direct vehicle exposure.** Search for ATU/MML urban traffic counts with station/segment and time metadata. Toll data and the 22-feature congestion layer are insufficient substitutes.
4. **District/analysis geometry.** Obtain and version a suitable official polygon/road geometry source and quantify exact 43-district coverage.
5. **Machine-profile ATU demand data.** Determine date range, station coverage, missing periods and export stability for Metropolitano/rail validation data.
6. **Census extraction.** Prove a reproducible INEI extraction/join path and evaluate whether 2017 variables remain useful structural covariates or only validation/context features.
7. **Weather.** Select Lima stations/products only if temporal weather variability is justified as a candidate feature and can be aligned without excessive missingness.

## 14. Evidence and reproducibility

The live audit can be executed through the dedicated source-audit workflow or equivalent commands. It produces:

```text
source-readiness.json
arcgis-profiles.json
onsv-inventory.json
onsv-pedestrian-profile.json
onsv-pedestrian-quality.json
```

The live workflow is evidence generation, not an ordinary unit-test dependency. External source availability must not make core CI flaky.

Core tests cover the catalog model, ArcGIS profiling contract and ONSV semantic audit with deterministic fixtures. Live runs validate those mechanisms against current official sources.

## 15. Decision state after P1 iteration 1

```yaml
outcome:
  fatal_pedestrian_linked_source: PROVEN_WITH_REAL_SOURCE
  strict_atropello_target: CANDIDATE_NOT_SELECTED
  broader_pedestrian_collision_source: BLOCKED

pedestrian_exposure:
  direct_citywide_counts: BLOCKED
  proxy_components: RESEARCH_REQUIRED

traffic_exposure:
  direct_citywide_counts: BLOCKED
  coarse_or_partial_proxies: AVAILABLE_BUT_NOT_ACCEPTED

built_environment:
  multiple_official_layers: PROVEN_WITH_REAL_SOURCE
  uniform_citywide_coverage: NOT_PROVEN_FOR_ALL_LAYERS

geometry:
  project_boundary: DEFINED
  final_analysis_unit: NOT_SELECTED

temporal:
  event_timestamps: PROVEN_WITH_REAL_SOURCE
  2025_detailed_outcome_year: PARTIAL

model_ready: false
```

The correct next step is therefore **not model training**. It is to complete the highest-impact source qualification work and then run P2 representation experiments using explicitly versioned candidate layers.
