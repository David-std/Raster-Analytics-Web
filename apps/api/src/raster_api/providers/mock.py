import hashlib

from raster_api.domain.models import ModelMetadata, RiskQuery, RiskResult


class MockRiskProvider:
    """Deterministic demo provider.

    The returned value is synthetic and has no probabilistic or scientific interpretation.
    It exists only to exercise the application contract before real data/model integration.
    """

    provider_name = "mock"
    model_version = "mock-v0"
    dataset_version = "synthetic-v0"

    @staticmethod
    def _demo_value(query: RiskQuery) -> float:
        key = f"{query.spatial_unit_id}|{query.period_id}".encode()
        digest = hashlib.sha256(key).digest()
        integer = int.from_bytes(digest[:8], byteorder="big")
        return round(integer / (2**64 - 1), 4)

    def predict(self, query: RiskQuery) -> RiskResult:
        return RiskResult(
            spatial_unit_id=query.spatial_unit_id,
            period_id=query.period_id,
            value=self._demo_value(query),
            label=None,
            provider=self.provider_name,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
            is_mock=True,
        )

    def compare(self, queries: list[RiskQuery]) -> list[RiskResult]:
        return [self.predict(query) for query in queries]

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            provider=self.provider_name,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
            is_mock=True,
            description=(
                "Deterministic synthetic provider for integration only; values are not risk "
                "probabilities, forecasts, or analytical results."
            ),
        )
