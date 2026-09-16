from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import Point, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union

_WGS84 = "EPSG:4326"
_LIMA_PROJECTED = "EPSG:32718"


def normalize_name(value: Any) -> str:
    if value is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^A-Za-z0-9]+", " ", without_marks).upper().split())


@dataclass(frozen=True)
class DistrictBoundary:
    unit_id: str
    name: str
    geometry_wgs84: BaseGeometry
    geometry_projected: BaseGeometry


@dataclass(frozen=True)
class GridDefinition:
    cell_size_m: int
    offset_fraction: float
    origin_x: float
    origin_y: float
    valid_units: frozenset[str]
    full_cell_count: int
    partial_cell_count: int
    boundary_area_km2: float

    @property
    def unit_count(self) -> int:
        return len(self.valid_units)

    @property
    def representation_id(self) -> str:
        offset_label = "base" if self.offset_fraction == 0 else "half_shift"
        return f"grid_{self.cell_size_m}m_{offset_label}"


def _feature_properties(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties")
    return properties if isinstance(properties, dict) else {}


def load_district_boundaries(
    geojson_path: str | Path,
    *,
    district_field: str = "NOMBDIST",
    province_field: str | None = "NOMBPROV",
    province_name: str = "LIMA",
) -> list[DistrictBoundary]:
    """Load Lima district polygons and project them to UTM zone 18S.

    The input snapshot is expected to be WGS84 GeoJSON. Province filtering is explicit so a
    broader administrative layer can be reused without accidentally admitting Callao.
    """
    payload = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Boundary GeoJSON must contain a features array")

    transformer = Transformer.from_crs(_WGS84, _LIMA_PROJECTED, always_xy=True)
    districts: list[DistrictBoundary] = []
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict) or not isinstance(feature.get("geometry"), dict):
            continue
        properties = _feature_properties(feature)
        if province_field:
            province = normalize_name(properties.get(province_field))
            if province and province != normalize_name(province_name):
                continue
        raw_name = properties.get(district_field)
        name = normalize_name(raw_name)
        if not name:
            continue
        if name in seen:
            raise ValueError(f"Duplicate district feature after normalization: {name}")
        seen.add(name)
        geometry_wgs84 = shape(feature["geometry"])
        if geometry_wgs84.is_empty or not geometry_wgs84.is_valid:
            raise ValueError(f"Invalid district geometry: {name}")
        geometry_projected = transform(transformer.transform, geometry_wgs84)
        districts.append(
            DistrictBoundary(
                unit_id=f"district:{name}",
                name=name,
                geometry_wgs84=geometry_wgs84,
                geometry_projected=geometry_projected,
            )
        )

    if not districts:
        raise ValueError("No district boundaries matched the requested province")
    return sorted(districts, key=lambda item: item.name)


def projected_boundary_union(districts: list[DistrictBoundary]) -> BaseGeometry:
    union = unary_union([district.geometry_projected for district in districts])
    if union.is_empty or not union.is_valid:
        raise ValueError("Projected Lima boundary union is empty or invalid")
    return union


def assign_point_to_district(
    longitude: float,
    latitude: float,
    districts: list[DistrictBoundary],
) -> str | None:
    point = Point(longitude, latitude)
    for district in districts:
        if district.geometry_wgs84.covers(point):
            return district.unit_id
    return None


def _grid_origin(minimum: float, cell_size_m: int, offset_fraction: float) -> float:
    shift = cell_size_m * offset_fraction
    return math.floor((minimum - shift) / cell_size_m) * cell_size_m + shift


def _grid_unit_id(column: int, row: int) -> str:
    return f"c{column}:r{row}"


def build_grid_definition(
    boundary_projected: BaseGeometry,
    cell_size_m: int,
    *,
    offset_fraction: float = 0.0,
) -> GridDefinition:
    """Build a regular UTM lattice and retain cells that intersect the Lima boundary.

    Cell geometries are not clipped because a CNN candidate needs a regular lattice. Instead,
    full versus boundary-intersecting cells are counted separately and the lattice origin is
    retained so event assignment is reproducible.
    """
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be positive")
    if offset_fraction not in {0.0, 0.5}:
        raise ValueError("offset_fraction must be 0.0 or 0.5 for the current experiment")

    min_x, min_y, max_x, max_y = boundary_projected.bounds
    origin_x = _grid_origin(min_x, cell_size_m, offset_fraction)
    origin_y = _grid_origin(min_y, cell_size_m, offset_fraction)
    max_column = math.ceil((max_x - origin_x) / cell_size_m)
    max_row = math.ceil((max_y - origin_y) / cell_size_m)

    valid_units: set[str] = set()
    full_cell_count = 0
    partial_cell_count = 0
    for column in range(max_column):
        x0 = origin_x + column * cell_size_m
        x1 = x0 + cell_size_m
        for row in range(max_row):
            y0 = origin_y + row * cell_size_m
            y1 = y0 + cell_size_m
            cell = box(x0, y0, x1, y1)
            if not boundary_projected.intersects(cell):
                continue
            valid_units.add(_grid_unit_id(column, row))
            if boundary_projected.covers(cell):
                full_cell_count += 1
            else:
                partial_cell_count += 1

    return GridDefinition(
        cell_size_m=cell_size_m,
        offset_fraction=offset_fraction,
        origin_x=origin_x,
        origin_y=origin_y,
        valid_units=frozenset(valid_units),
        full_cell_count=full_cell_count,
        partial_cell_count=partial_cell_count,
        boundary_area_km2=boundary_projected.area / 1_000_000,
    )


def assign_point_to_grid(
    longitude: float,
    latitude: float,
    grid: GridDefinition,
    *,
    transformer: Transformer | None = None,
) -> str | None:
    projection = transformer or Transformer.from_crs(_WGS84, _LIMA_PROJECTED, always_xy=True)
    x, y = projection.transform(longitude, latitude)
    column = math.floor((x - grid.origin_x) / grid.cell_size_m)
    row = math.floor((y - grid.origin_y) / grid.cell_size_m)
    unit_id = _grid_unit_id(column, row)
    return unit_id if unit_id in grid.valid_units else None


def district_geometry_summary(districts: list[DistrictBoundary]) -> dict[str, Any]:
    union = projected_boundary_union(districts)
    return {
        "district_count": len(districts),
        "districts": [district.name for district in districts],
        "projected_crs": _LIMA_PROJECTED,
        "boundary_area_km2": round(union.area / 1_000_000, 3),
        "bounds_projected": [round(value, 3) for value in union.bounds],
    }
