"""Leakage-safe, missingness-preserving analytical dataset assembly."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ml.datasets.contracts import (
    ContractCatalog,
    FeatureDefinition,
    FeatureRole,
    TemporalSemantics,
)
from ml.datasets.splits import TemporalSplit


class ObservationState(StrEnum):
    OBSERVED = "observed"
    TRUE_ZERO = "true_zero"
    MISSING = "missing"
    OUTSIDE_SOURCE_COVERAGE = "outside_source_coverage"
    UNAVAILABLE_FOR_PERIOD = "unavailable_for_period"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class FeatureObservation:
    feature_id: str
    spatial_unit_id: str
    target_period_id: str
    state: ObservationState
    value: float | int | str | None = None
    observation_period_id: str | None = None


@dataclass(frozen=True)
class TargetObservation:
    target_id: str
    spatial_unit_id: str
    period_id: str
    value: float | int


@dataclass(frozen=True)
class DatasetRow:
    spatial_unit_id: str
    period_id: str
    partition: str
    target_id: str
    target_value: float | int
    feature_values: dict[str, float | int | str | None]
    feature_states: dict[str, ObservationState]


def _month_index(period_id: str) -> int:
    try:
        year_text, month_text = period_id.split("-", 1)
        year = int(year_text)
        month = int(month_text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid monthly period id: {period_id!r}") from exc
    if not 1 <= month <= 12:
        raise ValueError(f"invalid monthly period id: {period_id!r}")
    return year * 12 + month


class LeakageSafeDatasetBuilder:
    def __init__(self, catalog: ContractCatalog, split: TemporalSplit) -> None:
        self.catalog = catalog
        self.split = split

    def build(
        self,
        *,
        target_id: str,
        feature_ids: list[str],
        targets: list[TargetObservation],
        features: list[FeatureObservation],
    ) -> list[DatasetRow]:
        self.catalog.require_target_for_dataset(target_id)
        feature_defs = {
            feature_id: self.catalog.require_feature_for_dataset(feature_id)
            for feature_id in feature_ids
        }
        self._validate_observations(feature_defs, features)

        observations: dict[tuple[str, str, str], FeatureObservation] = {}
        for observation in features:
            if observation.feature_id not in feature_defs:
                continue
            key = (
                observation.spatial_unit_id,
                observation.target_period_id,
                observation.feature_id,
            )
            if key in observations:
                raise ValueError(f"duplicate feature observation for {key}")
            observations[key] = observation

        rows: list[DatasetRow] = []
        for target in targets:
            if target.target_id != target_id:
                continue
            partition = self.split.partition_for(target.period_id)
            if partition is None:
                continue

            feature_values: dict[str, float | int | str | None] = {}
            feature_states: dict[str, ObservationState] = {}
            for feature_id in feature_ids:
                key = (target.spatial_unit_id, target.period_id, feature_id)
                observation = observations.get(key)
                if observation is None:
                    feature_values[feature_id] = None
                    feature_states[feature_id] = ObservationState.MISSING
                    continue
                feature_values[feature_id] = observation.value
                feature_states[feature_id] = observation.state

            rows.append(
                DatasetRow(
                    spatial_unit_id=target.spatial_unit_id,
                    period_id=target.period_id,
                    partition=partition,
                    target_id=target.target_id,
                    target_value=target.value,
                    feature_values=feature_values,
                    feature_states=feature_states,
                )
            )
        return rows

    def _validate_observations(
        self,
        feature_defs: dict[str, FeatureDefinition],
        observations: list[FeatureObservation],
    ) -> None:
        for observation in observations:
            definition = feature_defs.get(observation.feature_id)
            if definition is None:
                continue
            self._validate_state_value(observation)
            self._validate_temporal_semantics(definition, observation)

    @staticmethod
    def _validate_state_value(observation: FeatureObservation) -> None:
        if observation.state is ObservationState.TRUE_ZERO and observation.value != 0:
            raise ValueError(
                f"feature {observation.feature_id}: true_zero observations must carry value 0"
            )
        if observation.state in {
            ObservationState.MISSING,
            ObservationState.OUTSIDE_SOURCE_COVERAGE,
            ObservationState.UNAVAILABLE_FOR_PERIOD,
            ObservationState.NOT_APPLICABLE,
        } and observation.value is not None:
            raise ValueError(
                f"feature {observation.feature_id}: {observation.state.value} observations "
                "must not fabricate a value"
            )
        if observation.state is ObservationState.OBSERVED and observation.value is None:
            raise ValueError(
                f"feature {observation.feature_id}: observed observations require a value"
            )

    @staticmethod
    def _validate_temporal_semantics(
        definition: FeatureDefinition,
        observation: FeatureObservation,
    ) -> None:
        semantics = definition.temporal_semantics
        if semantics is TemporalSemantics.LAGGED:
            if observation.observation_period_id is None:
                raise ValueError(
                    f"feature {definition.id}: lagged observation requires observation_period_id"
                )
            lag = _month_index(observation.target_period_id) - _month_index(
                observation.observation_period_id
            )
            if lag < definition.minimum_lag_periods:
                raise ValueError(
                    f"feature {definition.id}: requires at least {definition.minimum_lag_periods} "
                    f"period lag; got {lag}"
                )
        elif definition.role is FeatureRole.OUTCOME_HISTORY:
            # Redundant with contract validation by design: the builder also fails closed if a
            # malformed contract somehow reaches dataset assembly.
            raise ValueError(f"feature {definition.id}: outcome history cannot be same-period")
