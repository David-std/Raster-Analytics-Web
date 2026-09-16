from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from shapely.strtree import STRtree

from pipelines.representation.spatial import DistrictBoundary, GridDefinition

_ANALYSIS_CRS = "EPSG:32718"
_GRID_ID = re.compile(r"^c(-?\d+):r(-?\d+)$")


class SourceCoverageSemantics(StrEnum):
    """How an absent source feature may be interpreted for an analytical unit."""

    COMPLETE = "complete"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class AnalysisUnit:
    unit_id: str
    geometry: BaseGeometry
    area_km2: float


@dataclass(frozen=True)
class SourceGeometryProfile:
    source: str
    source_crs: str
    input_feature_count: int
    valid_feature_count: int
    invalid_feature_count: int
    normalized_extra_ordinate_count: int


@dataclass(frozen=True)
class FeatureCoverageReport:
    source_id: str
    feature_id: str
    representation_id: str
    coverage_semantics: SourceCoverageSemantics
    unit_count: int
    source_feature_count: int
    source_features_intersecting_units: int
    source_features_outside_units: int
    units_with_observed_features: int
    units_without_observed_features: int
    observed_unit_ratio: float
    true_zero_eligible_units: int
    coverage_unresolved_units: int
    features_per_observed_unit_p50: int
    features_per_observed_unit_p90: int
    features_per_observed_unit_p95: int
    features_per_observed_unit_max: int
    source_geometry: SourceGeometryProfile

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coverage_semantics"] = self.coverage_semantics.value
        return payload


def build_district_units(districts: list[DistrictBoundary]) -> list[AnalysisUnit]:
    return [
        AnalysisUnit(
            unit_id=district.unit_id,
            geometry=district.geometry_projected,
            area_km2=district.geometry_projected.area / 1_000_000,
        )
        for district in districts
    ]


def _grid_indices(unit_id: str) -> tuple[int, int]:
    match = _GRID_ID.match(unit_id)
    if match is None:
        raise ValueError(f"invalid grid unit id: {unit_id}")
    return int(match.group(1)), int(match.group(2))


def build_grid_units(grid: GridDefinition) -> list[AnalysisUnit]:
    """Materialize regular cells without clipping their raster geometry."""
    units: list[AnalysisUnit] = []
    area_km2 = (grid.cell_size_m * grid.cell_size_m) / 1_000_000
    for unit_id in sorted(grid.valid_units):
        column, row = _grid_indices(unit_id)
        x0 = grid.origin_x + column * grid.cell_size_m
        y0 = grid.origin_y + row * grid.cell_size_m
        geometry = box(x0, y0, x0 + grid.cell_size_m, y0 + grid.cell_size_m)
        units.append(AnalysisUnit(unit_id=unit_id, geometry=geometry, area_km2=area_km2))
    return units


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _xy_coordinate_tree(value: Any) -> tuple[list[Any], bool]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("GeoJSON coordinates must be nested arrays")
    if len(value) >= 2 and _finite_number(value[0]) and _finite_number(value[1]):
        return [float(value[0]), float(value[1])], len(value) > 2

    cleaned: list[Any] = []
    normalized = False
    for item in value:
        cleaned_item, item_normalized = _xy_coordinate_tree(item)
        cleaned.append(cleaned_item)
        normalized = normalized or item_normalized
    return cleaned, normalized


def _xy_geometry_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    cleaned = dict(payload)
    if payload.get("type") == "GeometryCollection":
        geometries = payload.get("geometries")
        if not isinstance(geometries, list):
            raise ValueError("GeometryCollection requires a geometries array")
        cleaned_geometries: list[dict[str, Any]] = []
        normalized = False
        for item in geometries:
            if not isinstance(item, dict):
                raise ValueError("GeometryCollection members must be objects")
            cleaned_item, item_normalized = _xy_geometry_payload(item)
            cleaned_geometries.append(cleaned_item)
            normalized = normalized or item_normalized
        cleaned["geometries"] = cleaned_geometries
        return cleaned, normalized

    coordinates, normalized = _xy_coordinate_tree(payload.get("coordinates"))
    cleaned["coordinates"] = coordinates
    return cleaned, normalized


def load_source_geometries(
    path: str | Path,
    *,
    source_crs: str,
    analysis_crs: str = _ANALYSIS_CRS,
) -> tuple[list[BaseGeometry], SourceGeometryProfile]:
    """Load external GeoJSON and explicitly normalize unused Z/M ordinates to XY."""
    source_path = Path(path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Source GeoJSON must contain a features array")

    transformer = None
    if source_crs != analysis_crs:
        transformer = Transformer.from_crs(source_crs, analysis_crs, always_xy=True)

    geometries: list[BaseGeometry] = []
    invalid_count = 0
    normalized_count = 0
    for feature in features:
        if not isinstance(feature, dict) or not isinstance(feature.get("geometry"), dict):
            invalid_count += 1
            continue
        try:
            cleaned, normalized = _xy_geometry_payload(feature["geometry"])
            geometry = shape(cleaned)
            if transformer is not None:
                geometry = transform(transformer.transform, geometry)
            if geometry.is_empty or not geometry.is_valid:
                invalid_count += 1
                continue
            geometries.append(geometry)
            if normalized:
                normalized_count += 1
        except (TypeError, ValueError, IndexError):
            invalid_count += 1

    profile = SourceGeometryProfile(
        source=str(source_path),
        source_crs=source_crs,
        input_feature_count=len(features),
        valid_feature_count=len(geometries),
        invalid_feature_count=invalid_count,
        normalized_extra_ordinate_count=normalized_count,
    )
    return geometries, profile


def _nearest_rank(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def profile_loaded_source_coverage(
    *,
    source_id: str,
    feature_id: str,
    representation_id: str,
    units: list[AnalysisUnit],
    source_geometries: list[BaseGeometry],
    source_profile: SourceGeometryProfile,
    coverage_semantics: SourceCoverageSemantics = SourceCoverageSemantics.UNRESOLVED,
) -> FeatureCoverageReport:
    """Measure already-loaded source geometry against one analytical representation."""
    if not units:
        raise ValueError("coverage profiling requires at least one analytical unit")

    tree = STRtree([unit.geometry for unit in units])
    counts = [0 for _ in units]
    intersecting_source_features = 0

    for geometry in source_geometries:
        indexes = tree.query(geometry, predicate="intersects")
        if len(indexes) == 0:
            continue
        intersecting_source_features += 1
        for index in indexes:
            counts[int(index)] += 1

    observed_counts = [count for count in counts if count > 0]
    observed_units = len(observed_counts)
    absent_units = len(units) - observed_units
    complete = coverage_semantics is SourceCoverageSemantics.COMPLETE

    return FeatureCoverageReport(
        source_id=source_id,
        feature_id=feature_id,
        representation_id=representation_id,
        coverage_semantics=coverage_semantics,
        unit_count=len(units),
        source_feature_count=len(source_geometries),
        source_features_intersecting_units=intersecting_source_features,
        source_features_outside_units=len(source_geometries) - intersecting_source_features,
        units_with_observed_features=observed_units,
        units_without_observed_features=absent_units,
        observed_unit_ratio=round(observed_units / len(units), 6),
        true_zero_eligible_units=absent_units if complete else 0,
        coverage_unresolved_units=0 if complete else absent_units,
        features_per_observed_unit_p50=_nearest_rank(observed_counts, 0.50),
        features_per_observed_unit_p90=_nearest_rank(observed_counts, 0.90),
        features_per_observed_unit_p95=_nearest_rank(observed_counts, 0.95),
        features_per_observed_unit_max=max(observed_counts, default=0),
        source_geometry=source_profile,
    )


def profile_source_coverage(
    *,
    source_id: str,
    feature_id: str,
    representation_id: str,
    units: list[AnalysisUnit],
    source_path: str | Path,
    source_crs: str,
    coverage_semantics: SourceCoverageSemantics = SourceCoverageSemantics.UNRESOLVED,
) -> FeatureCoverageReport:
    """Load and profile a source without inventing zero semantics.

    A unit with no intersecting feature is only a true zero when the source has separately proven
    complete coverage. Otherwise it remains coverage-unresolved and cannot become a numeric zero in
    the canonical analytical dataset.
    """
    source_geometries, source_profile = load_source_geometries(
        source_path,
        source_crs=source_crs,
    )
    return profile_loaded_source_coverage(
        source_id=source_id,
        feature_id=feature_id,
        representation_id=representation_id,
        units=units,
        source_geometries=source_geometries,
        source_profile=source_profile,
        coverage_semantics=coverage_semantics,
    )
