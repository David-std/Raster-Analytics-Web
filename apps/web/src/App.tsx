import { useEffect, useMemo, useState } from "react";

import {
  compareRisk,
  fetchPeriods,
  fetchRiskMap,
  fetchSpatialUnits,
} from "./api";
import { RiskMap } from "./components/RiskMap";
import type {
  PeriodMetadata,
  RiskMapItem,
  RiskResult,
  SpatialUnitMetadata,
} from "./types";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

function formatValue(value: number | null): string {
  return value === null ? "No value" : value.toFixed(4);
}

export default function App() {
  const [spatialUnits, setSpatialUnits] = useState<SpatialUnitMetadata[]>([]);
  const [periods, setPeriods] = useState<PeriodMetadata[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const [mapItems, setMapItems] = useState<RiskMapItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<RiskMapItem | null>(null);
  const [compareA, setCompareA] = useState("");
  const [compareB, setCompareB] = useState("");
  const [comparison, setComparison] = useState<RiskResult[] | null>(null);
  const [loadingMap, setLoadingMap] = useState(false);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMetadata() {
      try {
        const [units, availablePeriods] = await Promise.all([
          fetchSpatialUnits(),
          fetchPeriods(),
        ]);

        if (cancelled) return;
        setSpatialUnits(units);
        setPeriods(availablePeriods);
        setSelectedPeriod(availablePeriods[0]?.period_id ?? "");
        setCompareA(units[0]?.spatial_unit_id ?? "");
        setCompareB(units[1]?.spatial_unit_id ?? units[0]?.spatial_unit_id ?? "");
      } catch (metadataError) {
        if (!cancelled) setError(errorMessage(metadataError));
      }
    }

    void loadMetadata();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedPeriod) return;
    let cancelled = false;

    async function loadMap() {
      setLoadingMap(true);
      setError(null);
      try {
        const items = await fetchRiskMap(selectedPeriod);
        if (cancelled) return;
        setMapItems(items);
        setSelectedItem((current) => {
          if (!current) return items[0] ?? null;
          return (
            items.find((item) => item.spatial_unit_id === current.spatial_unit_id) ??
            items[0] ??
            null
          );
        });
        setComparison(null);
      } catch (mapError) {
        if (!cancelled) setError(errorMessage(mapError));
      } finally {
        if (!cancelled) setLoadingMap(false);
      }
    }

    void loadMap();
    return () => {
      cancelled = true;
    };
  }, [selectedPeriod]);

  const averageValue = useMemo(() => {
    const values = mapItems
      .map((item) => item.value)
      .filter((value): value is number => value !== null);
    if (values.length === 0) return null;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  }, [mapItems]);

  function spatialUnitName(id: string): string {
    return spatialUnits.find((unit) => unit.spatial_unit_id === id)?.name ?? id;
  }

  async function runComparison() {
    if (!selectedPeriod || !compareA || !compareB) return;
    setLoadingComparison(true);
    setError(null);
    try {
      setComparison(await compareRisk(compareA, compareB, selectedPeriod));
    } catch (comparisonError) {
      setError(errorMessage(comparisonError));
    } finally {
      setLoadingComparison(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Pedestrian risk analysis</p>
          <h1>Raster Analytics</h1>
          <p className="subtitle">
            Explore spatiotemporal pedestrian collision risk across Metropolitan Lima.
          </p>
        </div>
      </header>

      {error && <section className="error-banner">{error}</section>}

      <main className="dashboard-grid">
        <section className="panel controls-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Explore</p>
              <h2>Period and map</h2>
            </div>
            {loadingMap && <span className="status-pill">Updating…</span>}
          </div>

          <label className="field">
            <span>Period</span>
            <select
              value={selectedPeriod}
              onChange={(event) => setSelectedPeriod(event.target.value)}
              disabled={periods.length === 0}
            >
              {periods.map((period) => (
                <option key={period.period_id} value={period.period_id}>
                  {period.name}
                </option>
              ))}
            </select>
          </label>

          <div className="map-frame">
            <RiskMap
              items={mapItems}
              selectedId={selectedItem?.spatial_unit_id ?? null}
              onSelect={setSelectedItem}
            />
          </div>

          <div className="legend">
            <span><i className="legend-dot low" /> Lower score</span>
            <span><i className="legend-dot medium" /> Mid-range score</span>
            <span><i className="legend-dot high" /> Higher score</span>
          </div>
        </section>

        <aside className="side-column">
          <section className="panel detail-panel">
            <p className="section-kicker">Selected area</p>
            <h2>{selectedItem?.name ?? "Select an area"}</h2>
            {selectedItem ? (
              <>
                <div className="risk-value">{formatValue(selectedItem.value)}</div>
                <p className="muted">Score for the selected period.</p>
                <dl className="metadata-list">
                  <div><dt>Area</dt><dd>{selectedItem.spatial_unit_id}</dd></div>
                  <div><dt>Period</dt><dd>{selectedItem.period_id}</dd></div>
                </dl>
              </>
            ) : (
              <p className="muted">Select an area on the map to inspect its result.</p>
            )}
          </section>

          <section className="panel summary-panel">
            <p className="section-kicker">Overview</p>
            <div className="stat-row">
              <div><strong>{mapItems.length}</strong><span>mapped areas</span></div>
              <div><strong>{formatValue(averageValue)}</strong><span>average score</span></div>
            </div>
          </section>
        </aside>

        <section className="panel compare-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Compare</p>
              <h2>Two areas, same period</h2>
            </div>
          </div>

          <div className="comparison-form">
            <label className="field">
              <span>Area A</span>
              <select value={compareA} onChange={(event) => setCompareA(event.target.value)}>
                {spatialUnits.map((unit) => (
                  <option key={unit.spatial_unit_id} value={unit.spatial_unit_id}>{unit.name}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Area B</span>
              <select value={compareB} onChange={(event) => setCompareB(event.target.value)}>
                {spatialUnits.map((unit) => (
                  <option key={unit.spatial_unit_id} value={unit.spatial_unit_id}>{unit.name}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="primary-button"
              onClick={() => void runComparison()}
              disabled={loadingComparison || !compareA || !compareB || !selectedPeriod}
            >
              {loadingComparison ? "Comparing…" : "Compare"}
            </button>
          </div>

          {comparison && (
            <div className="comparison-results">
              {comparison.map((result) => (
                <article key={result.spatial_unit_id}>
                  <span>{spatialUnitName(result.spatial_unit_id)}</span>
                  <strong>{formatValue(result.value)}</strong>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
