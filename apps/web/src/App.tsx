import { useEffect, useMemo, useState } from "react";

import {
  compareRisk,
  fetchModelMetadata,
  fetchPeriods,
  fetchRiskMap,
  fetchSpatialUnits,
} from "./api";
import { RiskMap } from "./components/RiskMap";
import type {
  ModelMetadata,
  PeriodMetadata,
  RiskMapItem,
  RiskResult,
  SpatialUnitMetadata,
} from "./types";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

function demoValue(value: number | null): string {
  return value === null ? "Sin valor" : value.toFixed(4);
}

export default function App() {
  const [spatialUnits, setSpatialUnits] = useState<SpatialUnitMetadata[]>([]);
  const [periods, setPeriods] = useState<PeriodMetadata[]>([]);
  const [metadata, setMetadata] = useState<ModelMetadata | null>(null);
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

    async function bootstrap() {
      try {
        const [units, availablePeriods, modelMetadata] = await Promise.all([
          fetchSpatialUnits(),
          fetchPeriods(),
          fetchModelMetadata(),
        ]);

        if (cancelled) return;
        setSpatialUnits(units);
        setPeriods(availablePeriods);
        setMetadata(modelMetadata);
        setSelectedPeriod(availablePeriods[0]?.period_id ?? "");
        setCompareA(units[0]?.spatial_unit_id ?? "");
        setCompareB(units[1]?.spatial_unit_id ?? units[0]?.spatial_unit_id ?? "");
      } catch (bootstrapError) {
        if (!cancelled) setError(errorMessage(bootstrapError));
      }
    }

    void bootstrap();
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

  const averageDemoValue = useMemo(() => {
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
          <p className="eyebrow">SI727 · Grupo 6 · Prototipo técnico</p>
          <h1>Raster Analytics Web</h1>
          <p className="subtitle">
            Base modular para análisis espaciotemporal del riesgo de atropello peatonal en
            Lima Metropolitana.
          </p>
        </div>
        <div className="mock-badge" aria-label="Modo demo activo">
          MOCK / DEMO
        </div>
      </header>

      <section className="warning-banner">
        <strong>Datos sintéticos.</strong> Los puntos, periodos y valores de esta pantalla existen
        únicamente para validar el flujo técnico. El valor DEMO no es una probabilidad, una
        predicción futura ni un resultado de riesgo real.
      </section>

      {error && <section className="error-banner">{error}</section>}

      <main className="dashboard-grid">
        <section className="panel controls-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Consulta</p>
              <h2>Periodo y mapa</h2>
            </div>
            {loadingMap && <span className="status-pill">Actualizando…</span>}
          </div>

          <label className="field">
            <span>Periodo</span>
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
            <span><i className="legend-dot low" /> Valor DEMO menor</span>
            <span><i className="legend-dot medium" /> Valor DEMO intermedio</span>
            <span><i className="legend-dot high" /> Valor DEMO mayor</span>
          </div>
        </section>

        <aside className="side-column">
          <section className="panel detail-panel">
            <p className="section-kicker">Detalle seleccionado</p>
            <h2>{selectedItem?.name ?? "Seleccione un punto"}</h2>
            {selectedItem ? (
              <>
                <div className="demo-value">{demoValue(selectedItem.value)}</div>
                <p className="muted">Valor sintético para integración, sin interpretación científica.</p>
                <dl className="metadata-list">
                  <div><dt>Unidad</dt><dd>{selectedItem.spatial_unit_id}</dd></div>
                  <div><dt>Periodo</dt><dd>{selectedItem.period_id}</dd></div>
                  <div><dt>Proveedor</dt><dd>{selectedItem.provider}</dd></div>
                  <div><dt>Modelo</dt><dd>{selectedItem.model_version}</dd></div>
                </dl>
              </>
            ) : (
              <p className="muted">El detalle aparecerá cuando la API entregue el mapa demo.</p>
            )}
          </section>

          <section className="panel summary-panel">
            <p className="section-kicker">Estado del slice</p>
            <div className="stat-row">
              <div><strong>{mapItems.length}</strong><span>puntos DEMO</span></div>
              <div><strong>{demoValue(averageDemoValue)}</strong><span>promedio DEMO</span></div>
            </div>
            <p className="muted compact">
              La unidad espacial definitiva sigue abierta. Estos puntos solo permiten ejercitar
              mapa, selección, filtros y contratos API.
            </p>
          </section>
        </aside>

        <section className="panel compare-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Comparación</p>
              <h2>Dos unidades, mismo periodo</h2>
            </div>
          </div>

          <div className="comparison-form">
            <label className="field">
              <span>Unidad A</span>
              <select value={compareA} onChange={(event) => setCompareA(event.target.value)}>
                {spatialUnits.map((unit) => (
                  <option key={unit.spatial_unit_id} value={unit.spatial_unit_id}>{unit.name}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Unidad B</span>
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
              {loadingComparison ? "Comparando…" : "Comparar DEMO"}
            </button>
          </div>

          {comparison && (
            <div className="comparison-results">
              {comparison.map((result) => (
                <article key={result.spatial_unit_id}>
                  <span>{spatialUnitName(result.spatial_unit_id)}</span>
                  <strong>{demoValue(result.value)}</strong>
                  <small>{result.model_version}</small>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel provenance-panel">
          <p className="section-kicker">Trazabilidad técnica</p>
          <h2>Proveedor activo</h2>
          <dl className="metadata-list horizontal">
            <div><dt>Provider</dt><dd>{metadata?.provider ?? "—"}</dd></div>
            <div><dt>Modelo</dt><dd>{metadata?.model_version ?? "—"}</dd></div>
            <div><dt>Dataset</dt><dd>{metadata?.dataset_version ?? "—"}</dd></div>
            <div><dt>Mock</dt><dd>{metadata?.is_mock ? "Sí" : "No"}</dd></div>
          </dl>
          <p className="muted compact">{metadata?.description}</p>
        </section>
      </main>
    </div>
  );
}
