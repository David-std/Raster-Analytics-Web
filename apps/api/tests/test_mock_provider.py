from raster_api.domain.models import RiskQuery
from raster_api.providers.mock import MockRiskProvider


def test_mock_provider_is_deterministic() -> None:
    provider = MockRiskProvider()
    query = RiskQuery(spatial_unit_id="demo-unit", period_id="demo-period")

    first = provider.predict(query)
    second = provider.predict(query)

    assert first == second
    assert first.is_mock is True
    assert first.label is None
    assert 0.0 <= first.value <= 1.0


def test_mock_metadata_is_explicit() -> None:
    metadata = MockRiskProvider().metadata()

    assert metadata.provider == "mock"
    assert metadata.is_mock is True
    assert "not risk probabilities" in metadata.description
