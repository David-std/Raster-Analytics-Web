from pathlib import Path

from pipelines.profiling import profile_csv


def test_profile_csv_reports_quality_and_spatiotemporal_candidates(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        "event_id,event_datetime,latitude,longitude,district,exposure\n"
        "1,2025-01-01T08:00:00,-12.04,-77.04,Lima,10\n"
        "2,2025-01-02T09:30:00,-12.05,-77.05,La Victoria,12\n"
        "2,2025-01-02T09:30:00,-12.05,-77.05,La Victoria,12\n"
        "3,,,-77.02,Miraflores,\n",
        encoding="utf-8",
    )

    profile = profile_csv(source)

    assert profile.row_count == 4
    assert profile.column_count == 6
    assert profile.duplicate_row_count == 1
    assert profile.duplicate_row_pct == 25.0
    assert profile.sha256
    assert profile.temporal_candidates == ["event_datetime"]

    assert profile.coordinate_profile is not None
    assert profile.coordinate_profile.latitude_column == "latitude"
    assert profile.coordinate_profile.longitude_column == "longitude"
    assert profile.coordinate_profile.paired_non_null_count == 3
    assert profile.coordinate_profile.valid_coordinate_count == 3
    assert profile.coordinate_profile.valid_coordinate_pct == 100.0

    columns = {column.name: column for column in profile.columns}
    assert columns["event_id"].inferred_type == "integer"
    assert columns["event_datetime"].inferred_type == "datetime"
    assert columns["event_datetime"].minimum == "2025-01-01T08:00:00"
    assert columns["event_datetime"].maximum == "2025-01-02T09:30:00"
    assert columns["exposure"].null_pct == 25.0
    assert any("duplicate" in warning.lower() for warning in profile.warnings)


def test_profile_csv_detects_semicolon_delimiter_and_missing_geo_time(tmp_path: Path) -> None:
    source = tmp_path / "aggregate.csv"
    source.write_text(
        "district;events;category\nLima;20;A\nMiraflores;8;B\n",
        encoding="utf-8",
    )

    profile = profile_csv(source)

    assert profile.delimiter == ";"
    assert profile.row_count == 2
    assert profile.coordinate_profile is None
    assert profile.temporal_candidates == []
    assert any("latitude/longitude" in warning for warning in profile.warnings)
    assert any("temporal" in warning.lower() for warning in profile.warnings)
