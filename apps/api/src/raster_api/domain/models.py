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


class ModelMetadata(BaseModel):
    provider: str
    model_version: str
    dataset_version: str
    description: str


class SpatialUnitMetadata(BaseModel):
    spatial_unit_id: str
    name: str
    unit_type: str
    latitude: float
    longitude: float


class PeriodMetadata(BaseModel):
    period_id: str
    name: str


class RiskMapItem(RiskResult):
    name: str
    latitude: float
    longitude: float
