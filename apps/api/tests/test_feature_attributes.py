import json
from pathlib import Path

import pytest

from pipelines.features.attributes import profile_geojson_attributes


def _write_geojson(path: Path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"zone": " residential ", "year": 2021}},
            {"type": "Feature", "properties": {"zone": "residential", "year": 2021}},
            {"type": "Feature", "properties": {"zone": "", "year": None}},
            {"type": "Feature", "properties": {"other": "x"}},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_attribute_profiler_distinguishes_missing_blank_and_values(tmp_path: Path) -> None:
    source = tmp_path / "source.geojson"
    _write_geojson(source)

    result = profile_geojson_attributes(source, fields=["zone", "year"])
    profiles = {profile.field: profile for profile in result.fields}

    zone = profiles["zone"]
    assert zone.feature_count == 4
    assert zone.present_count == 3
    assert zone.missing_property_count == 1
    assert zone.null_or_blank_count == 1
    assert zone.non_null_count == 2
    assert zone.distinct_non_null_count == 1
    assert zone.top_values[0].value == "residential"
    assert zone.top_values[0].count == 2

    year = profiles["year"]
    assert year.missing_property_count == 1
    assert year.null_or_blank_count == 1
    assert year.top_values[0].value == "2021"
    assert year.top_values[0].count == 2


def test_attribute_profiler_orders_top_values_deterministically(tmp_path: Path) -> None:
    source = tmp_path / "source.geojson"
    payload = {
        "type": "FeatureCollection",
        "features": [
            {"properties": {"zone": "b"}},
            {"properties": {"zone": "a"}},
            {"properties": {"zone": "b"}},
            {"properties": {"zone": "a"}},
            {"properties": {"zone": "c"}},
        ],
    }
    source.write_text(json.dumps(payload), encoding="utf-8")

    profile = profile_geojson_attributes(source, fields=["zone"], top_n=2).fields[0]

    assert [(item.value, item.count) for item in profile.top_values] == [("a", 2), ("b", 2)]


def test_attribute_profiler_requires_fields_and_positive_top_n(tmp_path: Path) -> None:
    source = tmp_path / "source.geojson"
    _write_geojson(source)

    with pytest.raises(ValueError, match="non-empty field names"):
        profile_geojson_attributes(source, fields=[])
    with pytest.raises(ValueError, match="top_n must be positive"):
        profile_geojson_attributes(source, fields=["zone"], top_n=0)
