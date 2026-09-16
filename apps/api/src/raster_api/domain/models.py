"""Domain models kept intentionally neutral until profiling/benchmarking close open decisions."""

from pydantic import BaseModel, Field


class RiskQuery(BaseModel):
    spatial_unit_id: str = Field(min_length=1)
    period_id: str = Field(min_length=1)


class RiskResult(BaseModel):
    spatial_unit_id: str
    period_id: str
    value: float | None = None
    label: str | None = None
    provider: str
    model_version: str
    dataset_version: str
    is_mock: bool = False


class ModelMetadata(BaseModel):
    provider: str
    model_version: str
    dataset_version: str
    is_mock: bool
    description: str


class SpatialUnitMetadata(BaseModel):
    spatial_unit_id: str
    name: str
    unit_type: str
    latitude: float
    longitude: float
    is_mock: bool = True


class PeriodMetadata(BaseModel):
    period_id: str
    name: str
    is_mock: bool = True


class RiskMapItem(RiskResult):
    name: str
    latitude: float
    longitude: float
