import pytest
from shapely.geometry import LineString, Point, box

from pipelines.features.coverage import AnalysisUnit
from pipelines.features.transform import (
    CategorizedGeometry,
    line_length_density,
    point_density,
    polygon_category_composition,
)


def _units() -> list[AnalysisUnit]:
    return [
        AnalysisUnit("a", box(0, 0, 1000, 1000), 1.0),
        AnalysisUnit("b", box(1000, 0, 2000, 1000), 1.0),
    ]


def test_point_density_omits_unobserved_units() -> None:
    values = point_density(_units(), [Point(100, 100), Point(200, 200)])

    assert len(values) == 1
    assert values[0].unit_id == "a"
    assert values[0].source_feature_count == 2
    assert values[0].value == pytest.approx(2.0)


def test_point_on_shared_boundary_is_not_double_counted() -> None:
    values = point_density(_units(), [Point(1000, 500)])

    assert sum(item.source_feature_count for item in values) == 1
    assert values[0].unit_id == "a"


def test_line_density_uses_clipped_length_per_unit_area() -> None:
    values = line_length_density(
        _units(),
        [LineString([(500, 500), (1500, 500)])],
    )
    by_unit = {item.unit_id: item for item in values}

    assert by_unit["a"].value == pytest.approx(0.5)
    assert by_unit["b"].value == pytest.approx(0.5)
    assert by_unit["a"].source_feature_count == 1
    assert by_unit["b"].source_feature_count == 1


def test_line_density_rejects_non_positive_unit_area() -> None:
    units = [AnalysisUnit("bad", box(0, 0, 1000, 1000), 0.0)]

    with pytest.raises(ValueError, match="non-positive area"):
        line_length_density(units, [LineString([(0, 500), (1000, 500)])])


def test_polygon_composition_uses_full_unit_area_as_denominator() -> None:
    features = [
        CategorizedGeometry(box(0, 0, 500, 1000), "residential"),
        CategorizedGeometry(box(500, 0, 750, 1000), "commercial"),
    ]

    result = polygon_category_composition(_units(), features)[0]

    assert result.unit_id == "a"
    assert result.category_area_shares["residential"] == pytest.approx(0.5)
    assert result.category_area_shares["commercial"] == pytest.approx(0.25)
    assert result.observed_area_ratio == pytest.approx(0.75)
    assert result.category_sum_ratio == pytest.approx(0.75)
    assert result.overlap_ratio == pytest.approx(0.0)


def test_polygon_composition_exposes_cross_category_overlap() -> None:
    features = [
        CategorizedGeometry(box(0, 0, 750, 1000), "residential"),
        CategorizedGeometry(box(500, 0, 1000, 1000), "commercial"),
    ]

    result = polygon_category_composition(_units(), features)[0]

    assert result.observed_area_ratio == pytest.approx(1.0)
    assert result.category_sum_ratio == pytest.approx(1.25)
    assert result.overlap_ratio == pytest.approx(0.25)


def test_polygon_composition_preserves_unclassified_area() -> None:
    result = polygon_category_composition(
        _units(),
        [CategorizedGeometry(box(0, 0, 500, 1000), None)],
    )[0]

    assert result.category_area_shares["__UNCLASSIFIED__"] == pytest.approx(0.5)


def test_transform_requires_units() -> None:
    with pytest.raises(ValueError, match="at least one analytical unit"):
        point_density([], [Point(0, 0)])
