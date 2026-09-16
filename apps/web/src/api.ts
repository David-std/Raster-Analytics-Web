import type {
  PeriodMetadata,
  RiskMapItem,
  RiskResult,
  SpatialUnitMetadata,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body || response.statusText}`);
  }

  return (await response.json()) as T;
}

export function fetchSpatialUnits(): Promise<SpatialUnitMetadata[]> {
  return request<SpatialUnitMetadata[]>("/metadata/spatial-units");
}

export function fetchPeriods(): Promise<PeriodMetadata[]> {
  return request<PeriodMetadata[]>("/metadata/periods");
}

export function fetchRiskMap(periodId: string): Promise<RiskMapItem[]> {
  const params = new URLSearchParams({ period: periodId });
  return request<RiskMapItem[]>(`/risk/map?${params.toString()}`);
}

export function compareRisk(
  spatialUnitA: string,
  spatialUnitB: string,
  periodId: string,
): Promise<RiskResult[]> {
  return request<RiskResult[]>("/risk/compare", {
    method: "POST",
    body: JSON.stringify([
      { spatial_unit_id: spatialUnitA, period_id: periodId },
      { spatial_unit_id: spatialUnitB, period_id: periodId },
    ]),
  });
}
