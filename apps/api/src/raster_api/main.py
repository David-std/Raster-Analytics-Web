from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from raster_api.config import get_settings
from raster_api.demo_catalog import has_period, periods, spatial_units
from raster_api.domain.models import (
    ModelMetadata,
    PeriodMetadata,
    RiskMapItem,
    RiskQuery,
    RiskResult,
    SpatialUnitMetadata,
)
from raster_api.providers.mock import MockRiskProvider

app = FastAPI(
    title="Raster Analytics API",
    version="0.2.0",
    description="Provisional API for spatiotemporal pedestrian run-over risk analysis.",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# v0 intentionally supports only mock. Baseline and CNN-RNN providers will be added behind
# the same contract after data profiling and benchmarking.
provider = MockRiskProvider()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/model/metadata", response_model=ModelMetadata)
def model_metadata() -> ModelMetadata:
    return provider.metadata()


@app.get("/metadata/spatial-units", response_model=list[SpatialUnitMetadata])
def spatial_unit_metadata() -> list[SpatialUnitMetadata]:
    return spatial_units()


@app.get("/metadata/periods", response_model=list[PeriodMetadata])
def period_metadata() -> list[PeriodMetadata]:
    return periods()


@app.get("/risk", response_model=RiskResult)
def risk(spatial_unit: str, period: str) -> RiskResult:
    return provider.predict(RiskQuery(spatial_unit_id=spatial_unit, period_id=period))


@app.get("/risk/map", response_model=list[RiskMapItem])
def risk_map(period: str) -> list[RiskMapItem]:
    if not has_period(period):
        raise HTTPException(status_code=404, detail="Unknown demo period")

    items: list[RiskMapItem] = []
    for unit in spatial_units():
        result = provider.predict(
            RiskQuery(spatial_unit_id=unit.spatial_unit_id, period_id=period)
        )
        items.append(
            RiskMapItem(
                **result.model_dump(),
                name=unit.name,
                latitude=unit.latitude,
                longitude=unit.longitude,
            )
        )
    return items


@app.post("/risk/compare", response_model=list[RiskResult])
def compare(queries: list[RiskQuery]) -> list[RiskResult]:
    return provider.compare(queries)
