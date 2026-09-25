# Population source plan

Status: **fine-geography candidate identified; reproducible extraction not yet proven**

Population is useful as structural context and as a possible pedestrian-activity proxy component, but
resident population is not pedestrian flow. The repository therefore keeps
`population_density_static` as an exposure-proxy covariate and explicitly forbids using it as a
pedestrian-exposure denominator or count-model offset.

The machine-readable gate is `data/features/population-source-plan.json`.

## 1. Candidate source

INEI's official census index currently exposes both district-level and **manzana-level** REDATAM
products for the 2017 population and housing census. The same official index lists the 2025 census
with first results, but the project has not yet proven a reproducible 2025 fine-geography product with
the variables and identifiers needed by this pipeline.

Therefore 2017 remains the current fine-geography candidate despite its age. This is not a claim that
2017 is intrinsically better than 2025. It applies the rule:

```text
fitness for purpose > recency alone
```

A newer source replaces it only when compatible geography, variables, coverage and reproducible
machine access are demonstrated.

## 2. Intended semantics

The candidate feature is:

```text
population_density_static
```

with semantics:

```text
structural resident-population context / pedestrian-activity proxy component
```

not:

```text
observed pedestrian volume
exposure denominator
individual collision probability denominator
```

Its census date must remain part of the feature metadata so the web methodology view and benchmark
report can expose the temporal mismatch transparently.

## 3. Extraction gate

The source is not promoted from planned evidence until the extraction pipeline proves all of the
following:

1. reproducible Lima-province population output;
2. stable geographic identifier at the finest usable census geography;
3. matching or officially reconcilable geometry identifier;
4. explicit filter to the 43 Lima-province districts with Callao excluded;
5. population totals reconciled against a coarser official control total;
6. report of null, duplicate and unmatched geography identifiers;
7. reference-date and static-snapshot metadata.

An interactive REDATAM page by itself is not enough. The project needs a repeatable extraction or a
versioned officially derived export before model use.

## 4. Alignment to analytical units

District models can aggregate census records through stable geography when the hierarchy is clean.
Grid models are harder because grid boundaries can cut census polygons.

If a manzana intersects several grid cells, a simple area-weighted allocation is only an
approximation. It implicitly assumes population is distributed uniformly within the census polygon.
If this method is used, the pipeline must:

```text
preserve total population
report partially intersected polygons
measure allocation sensitivity
record the allocation method in dataset metadata
```

A later dasymetric method using residential/built-up information may improve allocation, but it adds
another model and another source dependency. It should only be introduced if evidence shows that the
simpler allocation materially distorts the candidate representations.

## 5. Reconciliation tests

Before population becomes an active model feature, the pipeline should verify:

- sum of extracted small-area population against official district control totals;
- 43-district coverage and explicit absence of Callao from analytical output;
- percentage of census polygons matched to geometry;
- population conserved after any grid allocation;
- sensitivity of 500 m, 1 km and 2 km allocations to boundary intersections.

A failed reconciliation blocks the feature rather than silently filling missing areas.

## 6. Treatment of the 2025 census

The 2025 census should be re-evaluated as soon as INEI exposes a sufficiently granular and
reproducible product. If it becomes suitable, the project must decide whether to replace the 2017
snapshot or create a separate vintage-aware feature. It must not mix 2017 and 2025 values as though
they describe the same reference period.

This is especially important because population is structural context while the crash outcome covers
2021-2024 complete calendar years. Recency matters, but semantic consistency and reproducibility are
also required.

## Official evidence

- INEI census index, which lists 2017 REDATAM products at district and manzana level and the 2025
  census first-results entry:
  https://www.inei.gob.pe/estadisticas/censos/
- INEI REDATAM 2017 manzana application linked from the official census index:
  https://censos2017.inei.gob.pe/pubinei/index.asp
