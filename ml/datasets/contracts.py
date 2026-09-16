"""Machine-readable feature and target contracts.

The contract layer is intentionally model-agnostic. It prevents source limitations from being
silently converted into training semantics, especially exposure proxies used as denominators or
same-period crash outcomes leaked back into the feature matrix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ContractStatus(StrEnum):
    READY = "READY"
    CANDIDATE = "CANDIDATE"
    AUXILIARY = "AUXILIARY"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"


class FeatureRole(StrEnum):
    DIRECT_EXPOSURE = "direct_exposure"
    EXPOSURE_PROXY = "exposure_proxy"
    TRAFFIC_CONTEXT = "traffic_context"
    BUILT_ENVIRONMENT = "built_environment"
    TEMPORAL_CONTEXT = "temporal_context"
    OUTCOME_HISTORY = "outcome_history"


class TemporalSemantics(StrEnum):
    STATIC_SNAPSHOT = "static_snapshot"
    SAME_PERIOD = "same_period"
    LAGGED = "lagged"
    CALENDAR = "calendar"


class TargetKind(StrEnum):
    COUNT = "count"
    BINARY = "binary"
    RATE = "rate"
    PRESENTATION_INDEX = "presentation_index"


class ExposureMode(StrEnum):
    NONE = "none"
    OFFSET = "offset"
    DENOMINATOR = "denominator"


@dataclass(frozen=True)
class FeatureDefinition:
    id: str
    description: str
    role: FeatureRole
    status: ContractStatus
    temporal_semantics: TemporalSemantics
    source_ids: tuple[str, ...]
    unit: str | None = None
    minimum_lag_periods: int = 0
    can_be_exposure_offset: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FeatureDefinition":
        feature = cls(
            id=str(raw["id"]),
            description=str(raw["description"]),
            role=FeatureRole(raw["role"]),
            status=ContractStatus(raw["status"]),
            temporal_semantics=TemporalSemantics(raw["temporal_semantics"]),
            source_ids=tuple(str(item) for item in raw.get("source_ids", [])),
            unit=raw.get("unit"),
            minimum_lag_periods=int(raw.get("minimum_lag_periods", 0)),
            can_be_exposure_offset=bool(raw.get("can_be_exposure_offset", False)),
        )
        feature.validate()
        return feature

    def validate(self) -> None:
        if not self.id:
            raise ValueError("feature id must not be empty")
        if self.minimum_lag_periods < 0:
            raise ValueError(f"feature {self.id}: minimum_lag_periods must be non-negative")
        if self.temporal_semantics is TemporalSemantics.LAGGED:
            if self.minimum_lag_periods < 1:
                raise ValueError(f"feature {self.id}: lagged features require at least one period lag")
        elif self.minimum_lag_periods != 0:
            raise ValueError(
                f"feature {self.id}: minimum_lag_periods is only valid for lagged features"
            )
        if self.role is FeatureRole.OUTCOME_HISTORY:
            if self.temporal_semantics is not TemporalSemantics.LAGGED:
                raise ValueError(f"feature {self.id}: outcome history must be lagged")
            if self.minimum_lag_periods < 1:
                raise ValueError(f"feature {self.id}: outcome history requires a positive lag")
        if self.can_be_exposure_offset:
            if self.role is not FeatureRole.DIRECT_EXPOSURE:
                raise ValueError(
                    f"feature {self.id}: only direct exposure can be a count-model offset"
                )
            if not self.unit:
                raise ValueError(
                    f"feature {self.id}: exposure offsets require a documented physical unit"
                )
        if self.role is FeatureRole.EXPOSURE_PROXY and self.can_be_exposure_offset:
            raise ValueError(f"feature {self.id}: exposure proxies cannot be offsets")


@dataclass(frozen=True)
class TargetDefinition:
    id: str
    description: str
    kind: TargetKind
    status: ContractStatus
    population: str
    training_target: bool
    exposure_mode: ExposureMode = ExposureMode.NONE
    required_feature_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TargetDefinition":
        target = cls(
            id=str(raw["id"]),
            description=str(raw["description"]),
            kind=TargetKind(raw["kind"]),
            status=ContractStatus(raw["status"]),
            population=str(raw["population"]),
            training_target=bool(raw.get("training_target", True)),
            exposure_mode=ExposureMode(raw.get("exposure_mode", "none")),
            required_feature_ids=tuple(str(item) for item in raw.get("required_feature_ids", [])),
        )
        target.validate()
        return target

    def validate(self) -> None:
        if not self.id:
            raise ValueError("target id must not be empty")
        if self.kind is TargetKind.PRESENTATION_INDEX and self.training_target:
            raise ValueError(f"target {self.id}: presentation indices cannot be training labels")
        if self.exposure_mode is not ExposureMode.NONE and not self.required_feature_ids:
            raise ValueError(
                f"target {self.id}: exposure-normalized targets must name required exposure features"
            )


@dataclass(frozen=True)
class ContractCatalog:
    version: int
    analytical_grain: str
    feature_definitions: tuple[FeatureDefinition, ...]
    target_definitions: tuple[TargetDefinition, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ContractCatalog":
        catalog = cls(
            version=int(raw["version"]),
            analytical_grain=str(raw["analytical_grain"]),
            feature_definitions=tuple(
                FeatureDefinition.from_dict(item) for item in raw.get("features", [])
            ),
            target_definitions=tuple(
                TargetDefinition.from_dict(item) for item in raw.get("targets", [])
            ),
        )
        catalog.validate()
        return catalog

    @property
    def features(self) -> dict[str, FeatureDefinition]:
        return {item.id: item for item in self.feature_definitions}

    @property
    def targets(self) -> dict[str, TargetDefinition]:
        return {item.id: item for item in self.target_definitions}

    def validate(self) -> None:
        if self.version < 1:
            raise ValueError("contract catalog version must be positive")
        if not self.analytical_grain:
            raise ValueError("analytical_grain must not be empty")
        feature_ids = [item.id for item in self.feature_definitions]
        target_ids = [item.id for item in self.target_definitions]
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("feature ids must be unique")
        if len(target_ids) != len(set(target_ids)):
            raise ValueError("target ids must be unique")

        feature_map = self.features
        for target in self.target_definitions:
            missing = [item for item in target.required_feature_ids if item not in feature_map]
            if missing:
                raise ValueError(f"target {target.id}: unknown required features {missing}")
            if target.exposure_mode is not ExposureMode.NONE:
                for feature_id in target.required_feature_ids:
                    feature = feature_map[feature_id]
                    if feature.role is not FeatureRole.DIRECT_EXPOSURE:
                        raise ValueError(
                            f"target {target.id}: exposure normalization requires direct exposure, "
                            f"not {feature.role.value} ({feature_id})"
                        )
                    if not feature.can_be_exposure_offset:
                        raise ValueError(
                            f"target {target.id}: required exposure feature {feature_id} is not "
                            "approved for denominator/offset semantics"
                        )
            if target.status in {ContractStatus.READY, ContractStatus.CANDIDATE}:
                blocked = [
                    feature_id
                    for feature_id in target.required_feature_ids
                    if feature_map[feature_id].status
                    in {ContractStatus.BLOCKED, ContractStatus.REJECTED}
                ]
                if blocked:
                    raise ValueError(
                        f"target {target.id}: active target depends on unavailable features {blocked}"
                    )

    def require_feature_for_dataset(self, feature_id: str) -> FeatureDefinition:
        try:
            feature = self.features[feature_id]
        except KeyError as exc:
            raise ValueError(f"unknown feature: {feature_id}") from exc
        if feature.status in {ContractStatus.BLOCKED, ContractStatus.REJECTED}:
            raise ValueError(f"feature {feature_id} is not available for dataset construction")
        return feature

    def require_target_for_dataset(self, target_id: str) -> TargetDefinition:
        try:
            target = self.targets[target_id]
        except KeyError as exc:
            raise ValueError(f"unknown target: {target_id}") from exc
        if target.status in {ContractStatus.BLOCKED, ContractStatus.REJECTED}:
            raise ValueError(f"target {target_id} is not available for dataset construction")
        if not target.training_target:
            raise ValueError(f"target {target_id} is not a training target")
        return target

    def require_exposure_offset(self, feature_id: str) -> FeatureDefinition:
        feature = self.require_feature_for_dataset(feature_id)
        if feature.role is not FeatureRole.DIRECT_EXPOSURE or not feature.can_be_exposure_offset:
            raise ValueError(
                f"feature {feature_id} cannot be used as an exposure offset; "
                "only qualified direct exposure is allowed"
            )
        return feature


def load_contract_catalog(path: str | Path) -> ContractCatalog:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return ContractCatalog.from_dict(payload)
