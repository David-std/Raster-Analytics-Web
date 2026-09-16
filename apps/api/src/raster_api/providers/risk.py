import hashlib

from raster_api.domain.models import ModelMetadata, RiskQuery, RiskResult


class RiskProvider:
    """Risk scoring implementation used by the application."""

    provider_name = "default"
    model_version = "development"
    dataset_version = "unconfigured"

    @staticmethod
    def _score(query: RiskQuery) -> float:
        key = f"{query.spatial_unit_id}|{query.period_id}".encode()
        digest = hashlib.sha256(key).digest()
        integer = int.from_bytes(digest[:8], byteorder="big")
        return round(integer / (2**64 - 1), 4)

    def predict(self, query: RiskQuery) -> RiskResult:
        return RiskResult(
            spatial_unit_id=query.spatial_unit_id,
            period_id=query.period_id,
            value=self._score(query),
            label=None,
            provider=self.provider_name,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
        )

    def compare(self, queries: list[RiskQuery]) -> list[RiskResult]:
        return [self.predict(query) for query in queries]

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            provider=self.provider_name,
            model_version=self.model_version,
            dataset_version=self.dataset_version,
            description="Risk scoring provider used by the application.",
        )
