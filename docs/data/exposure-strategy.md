# Exposure strategy

Status: **direct citywide exposure remains unqualified; proxy use is constrained and testable**

Pedestrian-collision frequency, pedestrian exposure, vehicle exposure and built-environment context
are different quantities. This project must preserve that distinction in both the model and the web
product. A model can be useful without direct exposure, but its output must then be described as
model-estimated crash frequency/relative analytical risk rather than an exposure-normalized collision
rate or individual probability.

The machine-readable rules live in `data/features/exposure-strategy.json`.

## 1. Direct pedestrian exposure

A direct exposure feature is only admissible as a denominator or count-model offset if it has a
ratio-scale interpretation, defensible zero semantics, measured spatial/temporal alignment and known
coverage.

ATU publicly documents a PMU counting study performed at 27 high-traffic points in Lima and Callao.
The study counted vehicles and people continuously for 24 hours over seven days and used video plus
computer vision to distinguish pedestrians, bicycles and multiple vehicle classes. This is strong
evidence that direct observations exist in the planning process, but it is not the same as having a
reusable citywide microdata table with location/time metadata available to this repository.

Therefore:

```text
atu_pmu_2025_mobility_microdata = BLOCKED
```

until a reusable source is obtained and profiled.

## 2. Local observed pedestrian-activity signals

ATU's public Metropolitano data portal exposes station-oriented validation products, including:

```text
validations by station
validations by station and day type
annual station totals
monthly station totals
weekly station totals
period comparisons
```

The portal also offers Excel downloads for several reports. These data are observed public-transport
demand and can be useful for validating local pedestrian-activity proxies around the Metropolitano
network.

They are not citywide pedestrian counts. The following equivalence is forbidden:

```text
Metropolitano validations == pedestrian exposure across Lima
```

Allowed uses are local validation, temporal-pattern checks and sensitivity analysis around the served
corridor. Extrapolation outside the network requires separate evidence.

## 3. Proxy strategy if citywide direct exposure is unavailable

The project may need a pedestrian-activity proxy because no citywide, model-ready direct pedestrian
count source has yet been qualified. A proxy must be built from interpretable components rather than
from an arbitrary weighted score invented before validation.

Current candidate components are:

```text
population density
transit-stop density
transport-route density
land-use/zoning composition
```

Additional components such as POIs or walkability variables may be considered only if their source,
coverage and semantics are qualified first.

The initial modeling rule is:

```text
proxy components = ordinary covariates
```

not:

```text
proxy = exposure denominator
```

A separate exposure-proxy model can only be promoted if it is validated against observed demand or
count data.

## 4. Proxy validation protocol

If direct pedestrian exposure remains unavailable, a candidate proxy should be evaluated using a
separate development-only protocol:

1. assemble proxy components using only qualified source transformations;
2. fit or combine them using development data only;
3. compare predictions against observed local demand/count signals such as station validations or any
   direct-count locations later obtained;
4. inspect rank agreement, calibration and residual geography rather than a single global metric;
5. perform held-out local validation where sample size permits;
6. compare the combined proxy against each individual component;
7. retain an ablation in the crash-model benchmark with all exposure proxies removed.

A good local proxy still does not become a citywide denominator automatically. Ratio-scale exposure
semantics require stronger evidence than predictive association.

## 5. Vehicle exposure

Vehicle flow has the same problem. Transport-route geometry, congestion classes and toll-station
counts are useful context but they are not interchangeable with network-wide vehicle exposure.

The PMU count study proves that direct vehicle/person flow observations were collected at selected
points. If reusable counts are obtained, they should be profiled independently for location, time,
vehicle class, missingness and representativeness.

Until then:

```text
transport_route_density  -> traffic/mobility context
congestion class         -> local auxiliary context
toll flow                -> coarse external context
```

and none is allowed to masquerade as a citywide vehicle-volume denominator.

## 6. Consequence for target semantics

Two product paths remain legitimate.

### Path A: direct exposure becomes available

A count model may use a qualified exposure offset or an explicit exposure-normalized target. The
benchmark must then compare that formulation against non-exposure baselines and verify calibration.

### Path B: direct exposure remains unavailable

The project can still train models for fatal pedestrian crash count or occurrence using contextual
covariates and lagged history. The web product must describe the result as a relative analytical
estimate associated with observed/contextual conditions, not as an absolute pedestrian probability
or exposure-normalized rate.

This distinction prevents a useful contextual model from being oversold as something the data cannot
support.

## 7. Benchmark ablations required

The later benchmark must include at least these comparisons:

```text
all qualified context
minus exposure proxies
minus lagged outcome history
built-environment only
mobility/context only
simple statistical baseline
strong tabular baseline
CNN + recurrent candidate(s)
```

If performance collapses when lagged outcome history is removed, that must be reported rather than
hidden. If proxy components add little or behave inconsistently across space, they should not be kept
for narrative convenience.

## 8. Exit gate

The exposure gate closes only when one of the following is documented:

- compatible direct pedestrian exposure is qualified; or
- a limited proxy strategy is selected, validated and explicitly kept as a covariate rather than a
  denominator.

Vehicle exposure treatment must be documented separately. Product wording, target formulation and
benchmark metrics must match whichever path is selected.

## Official evidence used in this stage

- ATU open-data portal for Metropolitano validation products:
  https://sistemas.protransporte.gob.pe/DatosAbiertos/Metropolitano
- ATU PMU count-study note describing 27 high-traffic points, 24-hour continuous observation over
  seven days, and pedestrian/vehicle recognition:
  https://www.gob.pe/institucion/atu/noticias/794453-atu-la-inteligencia-artificial-ayudara-a-mejorar-la-movilidad-urbana-en-lima-y-callao
- ATU Plan de Movilidad Urbana publication package:
  https://www.gob.pe/institucion/atu/normas-legales/7530942-395-2025-atu-pe
