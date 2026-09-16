from fastapi.testclient import TestClient
from raster_api.main import app

client = TestClient(app)


def test_metadata_catalog() -> None:
    units = client.get("/metadata/spatial-units")
    periods = client.get("/metadata/periods")

    assert units.status_code == 200
    assert periods.status_code == 200
    assert len(units.json()) == 8
    assert len(periods.json()) == 3


def test_risk_map_is_deterministic() -> None:
    first = client.get("/risk/map", params={"period": "period-a"})
    second = client.get("/risk/map", params={"period": "period-a"})

    assert first.status_code == 200
    assert first.json() == second.json()
    assert len(first.json()) == 8
    assert all(item["period_id"] == "period-a" for item in first.json())


def test_risk_map_rejects_unknown_period() -> None:
    response = client.get("/risk/map", params={"period": "unknown-period"})

    assert response.status_code == 404
