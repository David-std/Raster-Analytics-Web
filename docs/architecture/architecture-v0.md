# Architecture v0

Status: **provisional scaffold**.

This document describes the executable boundary we can build before the real-data profile and model benchmark are complete.

## Problem framing

The product is not currently defined as a future-event forecasting system. Its committed purpose is to support spatiotemporal analysis of pedestrian run-over risk by spatial unit and period. Therefore the architecture must not assume that the model output is a probability, a future forecast, a fixed ordinal label, or a specific spatial/temporal granularity.

## Conceptual flow

```text
Historical + contextual data
          |
          v
Data profiling and reproducible processing
          |
          v
Spatial-temporal representation
          |
          v
RiskProvider boundary
   |         |          |
   |         |          +--> CNNRNNRiskProvider (future)
   |         +-------------> BaselineRiskProvider (future)
   +-----------------------> MockRiskProvider (current)
          |
          v
Backend API
          |
          v
Web map + filters + comparison + result detail
```

## Stable boundaries in v0

- The web/API layer consumes `RiskResult`; it must not know which model implementation is active.
- `spatial_unit_id` is opaque: district, grid, road segment, intersection or another representation may be selected later.
- `period_id` is opaque: hour, time bucket, day, week or another temporal unit may be selected later.
- `RiskResult.value` is generic and MUST NOT be interpreted as a probability unless a future validated model contract explicitly states it.
- Mock outputs are always marked with `is_mock=true` and carry synthetic model/dataset versions.

## Open decisions

These remain intentionally unresolved until evidence is available:

1. Final spatial representation and granularity.
2. Final temporal representation and granularity.
3. Target/operational definition of pedestrian run-over risk.
4. Whether the final output is continuous, ordinal, categorical or another representation.
5. Baseline algorithm.
6. CNN-RNN topology and whether ConvLSTM is appropriate.
7. ML framework and training/deployment strategy.
8. Final metrics and thresholds.
9. Production database and map technology.

## Incremental implementation

```text
Scaffold -> Mock vertical slice -> Real-data profiling -> Baseline -> CNN-RNN benchmark -> Selected provider
```

The scaffold is an engineering skeleton, the mock is synthetic integration behavior, and the baseline is the first real reference model. These are different concepts and should not be conflated.
