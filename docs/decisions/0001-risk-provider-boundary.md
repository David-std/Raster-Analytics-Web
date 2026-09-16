# ADR 0001: RiskProvider as the model boundary

- Status: Accepted for scaffold v0
- Date: 2026-09-15

## Context

The project commits to a CNN-RNN architectural direction, but several model and data decisions remain open until profiling and benchmarking. Coupling the API directly to a specific implementation such as ConvLSTM would create avoidable rework.

## Decision

The application depends on a `RiskProvider` contract rather than a concrete model. Initial implementations evolve as follows:

1. `MockRiskProvider`: synthetic deterministic values for end-to-end integration.
2. `BaselineRiskProvider`: first reproducible reference model using real profiled data.
3. `CNNRNNRiskProvider`: selected CNN-RNN implementation after benchmarking.

The API contract uses neutral identifiers (`spatial_unit_id`, `period_id`) and a neutral `value` field.

## Consequences

- Frontend and API can be developed before final model selection.
- Mock output cannot be mistaken for scientific evidence because it is explicitly tagged.
- Model replacement does not require rewriting the application boundary.
- The contract may still evolve if profiling proves that additional mandatory metadata is required.
