"""Source-to-feature transformations that preserve source-coverage semantics."""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.strtree import STRtree

from pipelines.features.coverage import AnalysisUnit

_UNCLASSIFIED = "__UNCLASSIFIED__"


@dataclass(frozen=True)
class FeatureValue:
    """Observed scalar feature value for one analytical unit.

    Units with no observed source geometry are deliberately omitted. The caller must decide whether
    absence means true zero, missing, or outside source coverage from separately proven semantics.
    """

    unit_id: str
    value: float
    source_feature_count: int


@dataclass(frozen=True)
class CategorizedGeometry:
    geometry: BaseGeometry
    category: str | None


@dataclass(frozen=True)
class FeatureComposition:
    """Area composition for one unit without hiding uncovered or overlapping geometry."""

    unit_id: str
    category_area_shares: dict[str, float]
    observed_area_ratio: float
    category_sum_ratio: float
    overlap_ratio: float
    source_feature_count: int


def _unit_index(units: list[AnalysisUnit]) -> tuple[list[BaseGeometry], STRtree]:
    if not units:
        raise ValueError("feature transformation requires at least one analytical unit")
    geometries = [unit.geometry for unit in units]
    return geometries, STRtree(geometries)


def _require_positive_area(unit: AnalysisUnit) -> None:
    if unit.area_km2 <= 0 or unit.geometry.area <= 0:
        raise ValueError(f"unit {unit.unit_id} has non-positive area")


def point_density(
    units: list[AnalysisUnit],
    source_geometries: list[BaseGeometry],
) -> list[FeatureValue]:
    """Count point observations once and normalize by unit area.

    A point exactly on a shared unit boundary may intersect multiple polygons. To prevent duplicate
    source observations, assignment is deterministic: the lexicographically smallest intersecting
    unit id receives the point.
    """
    _, tree = _unit_index(units)
    counts = [0 for _ in units]

    for geometry in source_geometries:
        if geometry.geom_type != "Point" or geometry.is_empty:
            continue
        indexes = [int(index) for index in tree.query(geometry, predicate="intersects")]
        if not indexes:
            continue
        selected = min(indexes, key=lambda index: units[index].unit_id)
        counts[selected] += 1

    values: list[FeatureValue] = []
    for index, count in enumerate(counts):
        if count == 0:
            continue
        _require_positive_area(units[index])
        values.append(
            FeatureValue(
                unit_id=units[index].unit_id,
                value=count / units[index].area_km2,
                source_feature_count=count,
            )
        )
    return values


def line_length_density(
    units: list[AnalysisUnit],
    source_geometries: list[BaseGeometry],
) -> list[FeatureValue]:
    """Calculate intersecting line kilometres per square kilometre of analytical area.

    Length is computed after clipping each source line to each analytical unit. This avoids counting
    a whole transport route in every unit it touches and keeps the metric comparable across units.
    """
    unit_geometries, tree = _unit_index(units)
    length_m = [0.0 for _ in units]
    source_counts = [0 for _ in units]

    for geometry in source_geometries:
        if geometry.geom_type not in {"LineString", "MultiLineString"} or geometry.is_empty:
            continue
        for raw_index in tree.query(geometry, predicate="intersects"):
            index = int(raw_index)
            clipped = geometry.intersection(unit_geometries[index])
            if clipped.is_empty or clipped.length <= 0:
                continue
            length_m[index] += float(clipped.length)
            source_counts[index] += 1

    values: list[FeatureValue] = []
    for index, total_length_m in enumerate(length_m):
        if total_length_m <= 0:
            continue
        _require_positive_area(units[index])
        values.append(
            FeatureValue(
                unit_id=units[index].unit_id,
                value=(total_length_m / 1000.0) / units[index].area_km2,
                source_feature_count=source_counts[index],
            )
        )
    return values


def polygon_category_composition(
    units: list[AnalysisUnit],
    source_features: list[CategorizedGeometry],
) -> list[FeatureComposition]:
    """Measure polygon-category area shares while preserving coverage and overlap diagnostics.

    Shares use the full analytical-unit area as denominator. They are therefore not silently
    renormalized to 100% when the source covers only part of a unit. `observed_area_ratio` reports
    the union of all observed source geometry, while `overlap_ratio` exposes cross-category overlap
    that could otherwise make category shares appear more complete than the geometry really is.
    """
    unit_geometries, tree = _unit_index(units)
    clipped_by_unit: list[dict[str, list[BaseGeometry]]] = [{} for _ in units]
    source_counts = [0 for _ in units]

    for feature in source_features:
        geometry = feature.geometry
        if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty:
            continue
        category = (feature.category or "").strip() or _UNCLASSIFIED
        for raw_index in tree.query(geometry, predicate="intersects"):
            index = int(raw_index)
            clipped = geometry.intersection(unit_geometries[index])
            if clipped.is_empty or clipped.area <= 0:
                continue
            clipped_by_unit[index].setdefault(category, []).append(clipped)
            source_counts[index] += 1

    compositions: list[FeatureComposition] = []
    for index, category_geometries in enumerate(clipped_by_unit):
        if not category_geometries:
            continue
        unit = units[index]
        _require_positive_area(unit)
        denominator = float(unit.geometry.area)

        category_unions = {
            category: unary_union(geometries)
            for category, geometries in category_geometries.items()
        }
        shares = {
            category: float(geometry.area) / denominator
            for category, geometry in sorted(category_unions.items())
        }
        overall_union = unary_union(list(category_unions.values()))
        observed_area_ratio = float(overall_union.area) / denominator
        category_sum_ratio = sum(shares.values())
        overlap_ratio = max(0.0, category_sum_ratio - observed_area_ratio)

        compositions.append(
            FeatureComposition(
                unit_id=unit.unit_id,
                category_area_shares=shares,
                observed_area_ratio=observed_area_ratio,
                category_sum_ratio=category_sum_ratio,
                overlap_ratio=overlap_ratio,
                source_feature_count=source_counts[index],
            )
        )
    return compositions
