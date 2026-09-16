# Feature and target contract

Status: **candidate analytical contract; no final risk target or feature set selected**

This document defines the rules that must hold before the repository can build a model-ready dataset.
The contract narrows the space of valid implementations without pretending that missing exposure data
or unresolved outcome semantics have already been solved.

## 1. What the model is allowed to learn

For a spatial unit `u` and month `t`, let `Y[u,t]` denote an observed pedestrian-collision outcome.
The current official event layer supports two fatal-outcome populations:

```text
pedestrian_linked_fatal
strict_fatal_atropello
```

They remain separate until the target population is selected with domain justification.

The model may learn relationships between the outcome and qualified spatial/temporal context, but it
must never use the target-period outcome itself as an input feature. Outcome history is allowed only
through explicitly lagged features.

The product remains an analytical risk-comparison system. A model can estimate an outcome for a
period without the product becoming a promise that it forecasts where an individual will be hit in
the future.

## 2. Crash frequency is not automatically exposure-normalized risk

The primary count candidate is:

```text
Y[u,t] = number of qualified fatal pedestrian crash events in unit u during month t
```

This is a legitimate crash-frequency target and a useful benchmark target. It is not, by itself, a
pedestrian exposure-normalized risk measure.

Transportation-safety guidance treats pedestrian exposure as a separate analytical quantity. FHWA
lists measures such as pedestrian volume, entering pedestrian/motor-vehicle flows, estimated street
crossings, travel distance and travel time, and notes that exposure can be used as a normalization
factor depending on the safety question.

Recent pedestrian-safety research reinforces the same distinction. Guo, Janson and Peng (2024)
constructed a multidimensional pedestrian-exposure indicator for spatiotemporal deep learning rather
than treating crash counts alone as risk. Hu, Chen and Zhao (2024) estimated link-level pedestrian
exposure and validated it against manual pedestrian counts; their results also show why coarse proxy
variables can differ materially from direct pedestrian activity.

## 3. Exposure treatment rules

### 3.1 Direct exposure

A direct exposure measure may be used as a denominator or count-model offset only when all of these
conditions are met:

- ratio-scale interpretation is defensible;
- zero has a real physical meaning;
- spatial unit and temporal period align with the target;
- source coverage is measured;
- the observation is not conditioned on crash occurrence;
- missing/out-of-coverage values are distinguishable from true zero;
- units are documented and stable.

A conventional count model may then use a formulation such as:

```text
Y[u,t] ~ count distribution(mu[u,t])
log(mu[u,t]) = model(features[u,t]) + log(exposure[u,t])
```

The exact distribution is not selected here. Negative-binomial regression is a required baseline
candidate because crash counts are non-negative and often overdispersed, but it must be compared
against the observed data rather than assumed to be correct.

### 3.2 Exposure proxies

Population density, transit access, route density, land use, points of interest and similar variables
may be useful predictors of pedestrian activity, but they are not automatically direct pedestrian
exposure.

Therefore an arbitrary composite proxy must **not** be used as `log(exposure)` and must not be divided
into the crash count to manufacture a risk rate. Proxy components are covariates until a validation
study supports stronger semantics.

The repository should exploit observed demand data where available to validate proxy behavior. ATU
publishes Metropolitano validation reports by station and time period, which can provide local demand
signals around that network. They are not citywide pedestrian counts and cannot be extrapolated to
all Lima without evidence.

ATU also reported an AI-assisted mobility-plan count study that measured vehicle flow and people at
27 high-traffic points in Lima and Callao. That is evidence that direct observations exist in the
planning process, but no reusable citywide microdata contract has yet been qualified in this
repository. The existence of a study or published report is therefore not enough to declare a model
feature available.

## 4. Candidate feature families

The machine-readable catalog in `data/features/catalog.json` is authoritative for implementation
status. Current families are:

```text
DIRECT PEDESTRIAN EXPOSURE
  blocked until a qualified citywide or otherwise compatible source is accepted

PEDESTRIAN EXPOSURE PROXIES
  population density
  transit stop density
  transport-route density
  local transit validation activity where observed

TRAFFIC / MOBILITY CONTEXT
  qualified traffic proxies only where coverage is demonstrated

BUILT ENVIRONMENT
  signalized intersections
  crossings where source coverage exists
  zoning / land-use composition
  road-type composition

TEMPORAL CONTEXT
  deterministic calendar encoding

OUTCOME HISTORY
  lagged fatal pedestrian events only, minimum one complete period lag
```

Availability alone does not make a feature valid. Each feature still needs spatial coverage,
missingness, joinability and ablation evidence.

## 5. Target candidates

### Count targets

`pedestrian_linked_fatal_count` and `strict_fatal_atropello_count` remain candidate training targets.
They preserve all count information and support count-model baselines.

### Binary occurrence

`pedestrian_linked_fatal_occurrence = 1(Y[u,t] > 0)` is retained only as a rare-event sensitivity
formulation. It discards count magnitude, so it is not the default benchmark target.

### Exposure-normalized rate

`fatal_pedestrian_exposure_rate` is blocked until qualified direct exposure exists at compatible
grain. The repository must fail closed rather than substituting a convenience proxy.

### Relative-risk / presentation index

A user-facing relative-risk score can be useful for maps and comparison, but it must be derived from
a validated model output. It is not a hand-crafted training label. The normalization formula remains
open until calibration and benchmark behavior are known.

### Broader non-fatal target

An all-pedestrian-collision count remains blocked until a reproducible non-fatal event source is
qualified. If that source is accepted later, representation profiling and target selection must be
rerun because the event density may change materially.

## 6. Missingness and source coverage

The dataset uses explicit states:

```text
observed
true_zero
missing
outside_source_coverage
unavailable_for_period
not_applicable
```

The following equivalences are forbidden:

```text
outside_source_coverage == 0
missing == 0
unavailable_for_period == 0
```

This rule is especially important for partial layers such as the current pedestrian-crossing and
congestion sources. A municipality reviewer must be able to distinguish "the source says zero" from
"the source does not describe this location".

Imputation, if later required by a model, is a model-pipeline transformation learned only from the
development partition. The canonical analytical dataset preserves the original missingness state.

## 7. Temporal leakage contract

The primary benchmark uses ordered calendar windows rather than random row splitting.

For the current complete 2021-2024 fatal-outcome evidence, the candidate split is:

```text
train        2021-01 through 2022-12
validation   2023-01 through 2023-12
test         2024-01 through 2024-12
```

2025 is excluded from complete-calendar benchmark design because the current detailed ONSV source is
partial.

The final 2024 test window is untouched during model and hyperparameter selection. After selection,
the model may be refit on development data through 2023 and evaluated once on 2024.

Spatial robustness checks may be added inside development data, but they do not replace the temporal
holdout.

### Feature timing

Feature semantics are machine-readable:

- `static_snapshot`: latest qualified snapshot effective on or before the target period;
- `same_period`: context observed for the same analytical month;
- `lagged`: observation must precede the target by the declared minimum lag;
- `calendar`: deterministic feature generated from the period key.

Same-period fatal-crash counts are never legal inputs to a fatal-crash target.

## 8. Retrospective analysis vs forecasting

The current MVP is allowed to analyze historical periods using context associated with those periods.
That is different from committing the product to future forecasting.

If a later requirement asks the model to score a genuinely future month, every dynamic same-period
feature must either be known in advance, forecast separately, or removed. The repository must not
reuse retrospective covariates and call the result a deployable forecast.

## 9. Candidate mathematical baselines

The benchmark stage must include transparent models before deep learning. Depending on dispersion,
zero structure and the selected target, candidates include:

```text
historical naive / seasonal reference
Poisson count model
negative-binomial count model
hurdle / zero-inflated sensitivity only if diagnostics justify it
strong tabular machine-learning baseline
CNN + recurrent candidates after the representation/feature contract is closed
```

A deep model must beat meaningful baselines on an independent test; the baseline cannot be weakened
for convenience.

## 10. Carry-forward spatial/temporal representations

Representation profiling narrowed the next-stage candidates to:

```text
primary
  district x month
  1000 m grid x month
  2000 m grid x month

conditional sensitivity
  500 m grid x month
```

`250 m`, ISO-week, day and 6-hour targets are deferred with the current fatal-only outcome evidence.
They may be reopened if a broader outcome source or materially different exposure formulation changes
the information density.

## 11. Implementation contract

The code in `ml/datasets` and the later `pipelines/features` layer enforces several non-negotiable
rules:

- proxy exposure cannot be declared as a count-model offset;
- direct-exposure targets cannot be active while the required exposure feature is blocked;
- outcome-history features must be lagged;
- absent observations become explicit missing values, not zeros;
- temporal partitions are ordered and non-overlapping.

The dataset builder in this stage deliberately stops before imputation, normalization, tensorization
or model-specific sampling. Those transformations belong to the later benchmark/training pipeline
and must be fitted only on development data.

## 12. Exit gate

This stage is not complete merely because the contract code exists. Before a model-ready dataset is
frozen, the project still needs evidence for:

1. pedestrian-exposure strategy: direct measure or validated proxy plan;
2. traffic/mobility treatment;
3. feature coverage for each surviving spatial representation;
4. source-to-feature transformations with units and missingness;
5. final outcome-population decision or pre-registered sensitivity comparison;
6. target formulation selected for benchmark;
7. temporal split version frozen before final training;
8. feature leakage review;
9. ablation plan, especially for lagged outcome history and exposure proxies.

Until these gates close, the correct state is **contract defined, model-ready dataset not yet frozen**.

## References used for this contract

- Guo, M., Janson, B., & Peng, Y. (2024). *A spatiotemporal deep learning approach for pedestrian
  crash risk prediction based on POI trip characteristics and pedestrian exposure intensity*.
  Accident Analysis & Prevention, 198, 107493. https://doi.org/10.1016/j.aap.2024.107493
- Hu, Y., Chen, L., & Zhao, Z. (2024). *How does street environment affect pedestrian crash risks?
  A link-level analysis using street view image-based pedestrian exposure measurement*. Accident
  Analysis & Prevention, 205, 107682. https://doi.org/10.1016/j.aap.2024.107682
- Federal Highway Administration. *Guidebook on Identification of High Pedestrian Crash Locations*.
  Exposure section: https://www.fhwa.dot.gov/publications/research/safety/17106/004.cfm
- Federal Highway Administration. *Safety Effects of Marked Versus Unmarked Crosswalks at
  Uncontrolled Locations*. Negative-binomial pedestrian crash model and exposure variables:
  https://www.fhwa.dot.gov/publications/research/safety/04100/02.cfm
- Autoridad de Transporte Urbano para Lima y Callao. Metropolitano open-data validation reports:
  https://sistemas.protransporte.gob.pe/DatosAbiertos/Metropolitano
- Autoridad de Transporte Urbano para Lima y Callao. AI-assisted PMU traffic/person count study at
  27 high-traffic points (2023):
  https://www.gob.pe/institucion/atu/noticias/794453-atu-la-inteligencia-artificial-ayudara-a-mejorar-la-movilidad-urbana-en-lima-y-callao
