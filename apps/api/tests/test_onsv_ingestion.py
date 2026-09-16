from openpyxl import Workbook

from pipelines.ingestion.onsv import inspect_workbook, load_sources, primary_source_ids


def test_source_registry_contains_primary_crash_and_people_datasets() -> None:
    sources = load_sources()

    assert primary_source_ids(sources) == [
        "fatal_crashes_2021_2025",
        "people_fatal_crashes_2021_2025",
    ]
    assert all(source["url"].startswith("https://www.onsv.gob.pe/") for source in sources.values())


def test_workbook_inventory_finds_header_and_columns(tmp_path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Crashes"
    worksheet.append(["Road crash records"])
    worksheet.append(["Crash ID", "Date", "Latitude", "Longitude"])
    worksheet.append(["A-1", "2025-01-01", -12.04, -77.03])
    worksheet.append(["A-2", "2025-01-02", -12.05, -77.04])

    people = workbook.create_sheet("People")
    people.append(["Crash ID", "Road user", "Outcome"])
    people.append(["A-1", "Pedestrian", "Fatal"])

    path = tmp_path / "source.xlsx"
    workbook.save(path)

    inventory = inspect_workbook(path)

    assert inventory["filename"] == "source.xlsx"
    assert inventory["sha256"]
    assert inventory["sheets"][0]["name"] == "Crashes"
    assert inventory["sheets"][0]["header_row"] == 2
    assert inventory["sheets"][0]["columns"] == [
        "Crash ID",
        "Date",
        "Latitude",
        "Longitude",
    ]
    assert inventory["sheets"][1]["columns"] == ["Crash ID", "Road user", "Outcome"]
