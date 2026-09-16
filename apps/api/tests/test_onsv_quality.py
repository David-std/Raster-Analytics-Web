import csv
import json

from pipelines.profiling.onsv_quality import profile_onsv_pedestrian_events


def test_onsv_quality_separates_pedestrian_person_from_atropello_class(tmp_path) -> None:
    districts = tmp_path / "districts.json"
    districts.write_text(
        json.dumps({"districts": ["ATE", "BARRANCO"]}),
        encoding="utf-8",
    )
    source = tmp_path / "events.csv"
    with source.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=[
                "crash_date",
                "crash_time",
                "year",
                "district",
                "crash_class",
                "pedestrian_fatalities",
            ],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "crash_date": "2024-05-10",
                    "crash_time": "08:30",
                    "year": "2024",
                    "district": "ATE",
                    "crash_class": "ATROPELLO",
                    "pedestrian_fatalities": "1",
                },
                {
                    "crash_date": "2024-06-11",
                    "crash_time": "09:45:00",
                    "year": "2024",
                    "district": "ATE",
                    "crash_class": "CHOQUE CON OBJETO FIJO",
                    "pedestrian_fatalities": "1",
                },
            ]
        )

    profile = profile_onsv_pedestrian_events(source, district_reference=districts)

    assert profile["rows"] == 2
    assert profile["class_name_contains_atropello"] == 1
    assert profile["class_name_not_contains_atropello"] == 1
    assert profile["pedestrian_fatalities_in_non_atropello_class"] == 1
    assert profile["district_coverage"]["missing"] == ["BARRANCO"]
    assert profile["time_parse_success_pct"] == 100.0
