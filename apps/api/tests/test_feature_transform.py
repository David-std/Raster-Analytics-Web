import pytest
from shapely.geometry import LineString, Point, box

from pipelines.features.coverage import AnalysisUnit
from pipelines.features.transform import line_length_density, point_density


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


def test_transform_requires_units() -> None:
    with pytest.raises(ValueError, match="at least one analytical unit"):
        point_density([], [Point(0, 0)])
