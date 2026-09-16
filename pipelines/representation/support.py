from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from shapely.strtree import STRtree

from pipelines.representation.spatial import normalize_name

_PROJECTED_CRS = "EPSG:32718"


@dataclass(frozen=True)
class SupportMaskProfile:
    source: str
    support_label: str
    source_crs: str
    analysis_crs: str
    input_feature_count: int
    retained_feature_count: int
    invalid_geometry_count: int
    missing_district_count: int
    excluded_district_count: int
    excluded_districts: dict[str, int]
    retained_district_count: int
    retained_districts: list[str]
    year_values: list[str]


class SupportMask:
    """Queryable structural support surface without dissolving a large polygon source.

    The mask says only whether a candidate cell intersects a qualified structural polygon. It does
    not encode pedestrian exposure, outcome presence, or risk. STRtree keeps the experiment usable
    for high-feature-count sources such as zoning/manzana polygons.
    """

    def __init__(
        self,
        geometries: list[BaseGeometry],
        profile: SupportMaskProfile,
    ) -> None:
        if not geometries:
            raise ValueError("Support mask requires at least one retained geometry")
        self._geometries = geometries
        self._tree = STRtree(geometries)
        self.profile = profile

    def intersects(self, geometry: BaseGeometry) -> bool:
        return len(self._tree.query(geometry, predicate="intersects")) > 0


def _geojson_crs(payload: dict[str, Any]) -> str | None:
    crs = payload.get("crs")
    if not isinstance(crs, dict):
        return None
    properties = crs.get("properties")
    if not isinstance(properties, dict):
        return None
    name = properties.get("name")
    return name if isinstance(name, str) and name else None


def load_support_mask(
    geojson_path: str | Path,
    *,
    expected_districts: set[str],
    district_field: str,
    support_label: str,
    source_crs: str | None = None,
    analysis_crs: str = _PROJECTED_CRS,
    year_field: str | None = "Anio",
) -> SupportMask:
    """Load and clip a structural polygon source to the project's 43-district name set.

    District filtering is deliberately independent from event presence. A district with no outcome
    event remains eligible when the structural source covers it.
    """
    path = Path(geojson_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Support GeoJSON must contain a features array")

    declared_crs = source_crs or _geojson_crs(payload) or "EPSG:4326"
    transformer = None
    if declared_crs != analysis_crs:
        transformer = Transformer.from_crs(declared_crs, analysis_crs, always_xy=True)

    retained: list[BaseGeometry] = []
    retained_districts: set[str] = set()
    excluded_districts: Counter[str] = Counter()
    year_values: set[str] = set()
    invalid_geometry_count = 0
    missing_district_count = 0

    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        geometry_payload = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry_payload, dict):
            invalid_geometry_count += 1
            continue

        district = normalize_name(properties.get(district_field))
        if not district:
            missing_district_count += 1
            continue
        if district not in expected_districts:
            excluded_districts[district] += 1
            continue

        geometry = shape(geometry_payload)
        if geometry.is_empty or not geometry.is_valid:
            invalid_geometry_count += 1
            continue
        if transformer is not None:
            geometry = transform(transformer.transform, geometry)
        retained.append(geometry)
        retained_districts.add(district)

        if year_field:
            year = properties.get(year_field)
            if year not in (None, ""):
                year_values.add(str(year))

    profile = SupportMaskProfile(
        source=str(path),
        support_label=support_label,
        source_crs=declared_crs,
        analysis_crs=analysis_crs,
        input_feature_count=len(features),
        retained_feature_count=len(retained),
        invalid_geometry_count=invalid_geometry_count,
        missing_district_count=missing_district_count,
        excluded_district_count=sum(excluded_districts.values()),
        excluded_districts=dict(excluded_districts.most_common()),
        retained_district_count=len(retained_districts),
        retained_districts=sorted(retained_districts),
        year_values=sorted(year_values),
    )
    return SupportMask(retained, profile)
