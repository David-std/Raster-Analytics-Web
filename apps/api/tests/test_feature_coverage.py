import json
from pathlib import Path

import pytest
from shapely.geometry import box

from pipelines.features.coverage import (
    AnalysisUnit,
    SourceCoverageSemantics,
    profile_source_coverage,
)


def _write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )


def _point_feature(x: float, y: float, *extra: float | None) -> dict:
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "Point", "coordinates": [x, y, *extra]},
    }


def _units() -> list[AnalysisUnit]:
    return [
        AnalysisUnit("u1", box(0, 0, 10, 10), 0.0001),
        AnalysisUnit("u2", box(10, 0, 20, 10), 0.0001),
        AnalysisUnit("u3", box(20, 0, 30, 10), 0.0001),
    ]


def test_unresolved_source_absence_does_not_become_true_zero(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(source, [_point_feature(5, 5), _point_feature(15, 5)])

    report = profile_source_coverage(
        source_id="source",
        feature_id="feature",
        representation_id="test",
        units=_units(),
        source_path=source,
        source_crs="EPSG:32718",
        coverage_semantics=SourceCoverageSemantics.UNRESOLVED,
    )

    assert report.units_with_observed_features == 2
    assert report.units_without_observed_features == 1
    assert report.true_zero_eligible_units == 0
    assert report.coverage_unresolved_units == 1


def test_complete_source_allows_absence_to_be_true_zero(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(source, [_point_feature(5, 5)])

    report = profile_source_coverage(
        source_id="source",
        feature_id="feature",
        representation_id="test",
        units=_units(),
        source_path=source,
        source_crs="EPSG:32718",
        coverage_semantics=SourceCoverageSemantics.COMPLETE,
    )

    assert report.true_zero_eligible_units == 2
    assert report.coverage_unresolved_units == 0


def test_source_features_outside_project_units_are_reported(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(source, [_point_feature(5, 5), _point_feature(100, 100)])

    report = profile_source_coverage(
        source_id="source",
        feature_id="feature",
        representation_id="test",
        units=_units(),
        source_path=source,
        source_crs="EPSG:32718",
    )

    assert report.source_feature_count == 2
    assert report.source_features_intersecting_units == 1
    assert report.source_features_outside_units == 1


def test_extra_arcgis_ordinates_are_removed_without_fabricating_xy(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(source, [_point_feature(5, 5, 7, None)])

    report = profile_source_coverage(
        source_id="source",
        feature_id="feature",
        representation_id="test",
        units=_units(),
        source_path=source,
        source_crs="EPSG:32718",
    )

    assert report.source_geometry.valid_feature_count == 1
    assert report.source_geometry.normalized_extra_ordinate_count == 1
    assert report.units_with_observed_features == 1


def test_invalid_xy_geometry_is_failed_closed(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(
        source,
        [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", "coordinates": [None, 5, 7, None]},
            }
        ],
    )

    report = profile_source_coverage(
        source_id="source",
        feature_id="feature",
        representation_id="test",
        units=_units(),
        source_path=source,
        source_crs="EPSG:32718",
    )

    assert report.source_geometry.valid_feature_count == 0
    assert report.source_geometry.invalid_feature_count == 1
    assert report.units_with_observed_features == 0


def test_coverage_requires_units(tmp_path: Path) -> None:
    source = tmp_path / "points.geojson"
    _write_geojson(source, [_point_feature(5, 5)])

    with pytest.raises(ValueError, match="at least one analytical unit"):
        profile_source_coverage(
            source_id="source",
            feature_id="feature",
            representation_id="test",
            units=[],
            source_path=source,
            source_crs="EPSG:32718",
        )
