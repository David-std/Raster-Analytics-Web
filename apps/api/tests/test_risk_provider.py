from raster_api.domain.models import RiskQuery
from raster_api.providers import RiskProvider


def test_risk_provider_is_deterministic() -> None:
    provider = RiskProvider()
    query = RiskQuery(spatial_unit_id="area-a", period_id="period-a")

    first = provider.predict(query)
    second = provider.predict(query)

    assert first == second
    assert first.label is None
    assert first.value is not None
    assert 0.0 <= first.value <= 1.0


def test_provider_metadata() -> None:
    metadata = RiskProvider().metadata()

    assert metadata.provider == "default"
    assert metadata.description
