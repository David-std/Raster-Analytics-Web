"""Source-to-feature transformations that preserve source-coverage semantics."""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from pipelines.features.coverage import AnalysisUnit


@dataclass(frozen=True)
class FeatureValue:
    """Observed feature value for one analytical unit.

    Units with no observed source geometry are deliberately omitted. The caller must decide whether
    absence means true zero, missing, or outside source coverage from separately proven semantics.
    """

    unit_id: str
    value: float
    source_feature_count: int


def _unit_index(units: list[AnalysisUnit]) -> tuple[list[BaseGeometry], STRtree]:
    if not units:
        raise ValueError("feature transformation requires at least one analytical unit")
    geometries = [unit.geometry for unit in units]
    return geometries, STRtree(geometries)


def point_density(
    units: list[AnalysisUnit],
    source_geometries: list[BaseGeometry],
) -> list[FeatureValue]:
    """Count point observations once and normalize by unit area.

    A point exactly on a shared unit boundary may intersect multiple polygons. To prevent duplicate
    source observations, assignment is deterministic: the lexicographically smallest intersecting
    unit id receives the point.
    """
    unit_geometries, tree = _unit_index(units)
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
        area = units[index].area_km2
        if area <= 0:
            raise ValueError(f"unit {units[index].unit_id} has non-positive area")
        values.append(
            FeatureValue(
                unit_id=units[index].unit_id,
                value=count / area,
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
        area = units[index].area_km2
        if area <= 0:
            raise ValueError(f"unit {units[index].unit_id} has non-positive area")
        values.append(
            FeatureValue(
                unit_id=units[index].unit_id,
                value=(total_length_m / 1000.0) / area,
                source_feature_count=source_counts[index],
            )
        )
    return values
