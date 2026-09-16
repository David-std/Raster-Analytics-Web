import csv
import json
from datetime import date, datetime

from pipelines.representation.experiment import run_representation_experiment
from pipelines.representation.temporal import enumerate_period_ids, period_id


def _write_boundary(path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"NOMBDIST": "ALFA", "NOMBPROV": "LIMA"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-77.10, -12.10],
                            [-77.05, -12.10],
                            [-77.05, -12.00],
                            [-77.10, -12.00],
                            [-77.10, -12.10],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"NOMBDIST": "BETA", "NOMBPROV": "LIMA"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-77.05, -12.10],
                            [-77.00, -12.10],
                            [-77.00, -12.00],
                            [-77.05, -12.00],
                            [-77.05, -12.10],
                        ]
                    ],
                },
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_events(path) -> None:
    fieldnames = [
        "crash_id",
        "crash_date",
        "crash_time",
        "district",
        "latitude",
        "longitude",
        "crash_class",
    ]
    rows = [
        {
            "crash_id": "a",
            "crash_date": "2021-01-05",
            "crash_time": "08:00",
            "district": "ALFA",
            "latitude": -12.05,
            "longitude": -77.08,
            "crash_class": "ATROPELLO",
        },
        {
            "crash_id": "b",
            "crash_date": "2021-01-06",
            "crash_time": "14:00",
            "district": "ALFA",
            "latitude": -12.05,
            "longitude": -77.02,
            "crash_class": "CHOQUE",
        },
        {
            "crash_id": "c",
            "crash_date": "2024-12-20",
            "crash_time": "23:00",
            "district": "BETA",
            "latitude": -12.02,
            "longitude": -77.01,
            "crash_class": "ATROPELLO FUGA",
        },
        {
            "crash_id": "d",
            "crash_date": "2025-03-01",
            "crash_time": "06:00",
            "district": "BETA",
            "latitude": -12.08,
            "longitude": -77.03,
            "crash_class": "ATROPELLO",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_temporal_candidates_have_explicit_period_semantics() -> None:
    months = enumerate_period_ids(date(2021, 1, 1), date(2021, 3, 31), "month")
    assert months == ["2021-01", "2021-02", "2021-03"]
    assert period_id(datetime(2021, 1, 2, 13, 30), "daypart_6h") == "2021-01-02T12"


def test_representation_report_preserves_population_and_scope_distinctions(tmp_path) -> None:
    boundary = tmp_path / "boundary.geojson"
    events = tmp_path / "events.csv"
    _write_boundary(boundary)
    _write_events(events)

    report = run_representation_experiment(
        events,
        boundary,
        grid_sizes=(5000,),
        temporal_kinds=("month",),
    )

    assert report["selection_status"] == "NOT_SELECTED"
    assert report["event_count_loaded"] == 4
    assert report["strict_atropello_count_loaded"] == 3
    assert len(report["analysis_windows"]) == 2
    assert report["district_assignment_audit"]["source_district_geometry_mismatches"] == 1
    assert {item["kind"] for item in report["blocked_spatial_candidates"]} == {
        "road_segment",
        "intersection_node",
    }

    district_results = [
        item
        for item in report["results"]
        if item["window_id"] == "complete_calendar_years_2021_2024"
        and item["spatial_representation"] == "district"
        and item["temporal_representation"] == "month"
    ]
    broad = next(item for item in district_results if item["population"] == "pedestrian_linked_fatal")
    strict = next(item for item in district_results if item["population"] == "strict_fatal_atropello")

    assert broad["spatial_units"] == 2
    assert broad["periods"] == 48
    assert broad["assigned_events"] == 3
    assert strict["assigned_events"] == 2
    assert broad["zero_event_ratio"] > 0.9
    assert report["grid_boundary_sensitivity"]
