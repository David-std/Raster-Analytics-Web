from fastapi import FastAPI

from raster_api.config import get_settings
from raster_api.domain.models import ModelMetadata, RiskQuery, RiskResult
from raster_api.providers.mock import MockRiskProvider

app = FastAPI(
    title="Raster Analytics API",
    version="0.1.0",
    description="Provisional API for spatiotemporal pedestrian run-over risk analysis.",
)

settings = get_settings()

# v0 intentionally supports only mock. Baseline and CNN-RNN providers will be added behind
# the same contract after data profiling and benchmarking.
provider = MockRiskProvider()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/model/metadata", response_model=ModelMetadata)
def model_metadata() -> ModelMetadata:
    return provider.metadata()


@app.get("/risk", response_model=RiskResult)
def risk(spatial_unit: str, period: str) -> RiskResult:
    return provider.predict(RiskQuery(spatial_unit_id=spatial_unit, period_id=period))


@app.post("/risk/compare", response_model=list[RiskResult])
def compare(queries: list[RiskQuery]) -> list[RiskResult]:
    return provider.compare(queries)
