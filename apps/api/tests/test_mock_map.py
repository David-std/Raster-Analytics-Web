from fastapi.testclient import TestClient
from raster_api.main import app

client = TestClient(app)


def test_mock_metadata_catalog() -> None:
    units = client.get("/metadata/spatial-units")
    periods = client.get("/metadata/periods")

    assert units.status_code == 200
    assert periods.status_code == 200
    assert len(units.json()) == 8
    assert len(periods.json()) == 3
    assert all(item["is_mock"] for item in units.json())
    assert all(item["is_mock"] for item in periods.json())


def test_mock_risk_map_is_deterministic_and_explicitly_mock() -> None:
    first = client.get("/risk/map", params={"period": "demo-period-a"})
    second = client.get("/risk/map", params={"period": "demo-period-a"})

    assert first.status_code == 200
    assert first.json() == second.json()
    assert len(first.json()) == 8
    assert all(item["is_mock"] for item in first.json())
    assert all(item["period_id"] == "demo-period-a" for item in first.json())


def test_mock_risk_map_rejects_unknown_period() -> None:
    response = client.get("/risk/map", params={"period": "not-a-demo-period"})

    assert response.status_code == 404
