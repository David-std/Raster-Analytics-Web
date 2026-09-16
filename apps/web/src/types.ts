export interface SpatialUnitMetadata {
  spatial_unit_id: string;
  name: string;
  unit_type: string;
  latitude: number;
  longitude: number;
  is_mock: boolean;
}

export interface PeriodMetadata {
  period_id: string;
  name: string;
  is_mock: boolean;
}

export interface RiskResult {
  spatial_unit_id: string;
  period_id: string;
  value: number | null;
  label: string | null;
  provider: string;
  model_version: string;
  dataset_version: string;
  is_mock: boolean;
}

export interface RiskMapItem extends RiskResult {
  name: string;
  latitude: number;
  longitude: number;
}

export interface ModelMetadata {
  provider: string;
  model_version: string;
  dataset_version: string;
  is_mock: boolean;
  description: string;
}
