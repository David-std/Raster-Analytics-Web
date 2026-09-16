from typing import Protocol

from raster_api.domain.models import ModelMetadata, RiskQuery, RiskResult


class RiskProvider(Protocol):
    """Boundary between the application and any risk-estimation implementation."""

    def predict(self, query: RiskQuery) -> RiskResult: ...

    def compare(self, queries: list[RiskQuery]) -> list[RiskResult]: ...

    def metadata(self) -> ModelMetadata: ...
