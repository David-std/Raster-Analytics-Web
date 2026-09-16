# Raster Analytics Web

Aplicación web para el análisis espaciotemporal del riesgo de atropello peatonal en Lima Metropolitana.

## Estado actual

`mock vertical slice v0`

La base está diseñada para evolucionar sin acoplar la aplicación a una implementación concreta del modelo:

```text
MockRiskProvider -> BaselineRiskProvider -> CNNRNNRiskProvider
```

- **Scaffold**: estructura ejecutable y contratos entre componentes.
- **Mock**: implementación sintética para probar integración sin datos/modelo reales.
- **Baseline**: primer modelo real de referencia, construido después del perfilamiento.

## Flujo conceptual

```text
Datos históricos/contextuales
          |
          v
Procesamiento espaciotemporal
          |
          v
RiskProvider
          |
          v
API
          |
          v
Mapa + filtros + detalle + comparación
```

El proyecto no asume todavía que la salida sea una probabilidad ni una predicción futura. La unidad espacial, unidad temporal, definición operativa del riesgo, baseline y configuración CNN-RNN siguen abiertas hasta perfilamiento y benchmarking.

## Mock vertical slice

La rama de integración contiene un flujo ejecutable con:

- catálogo DEMO de puntos representativos en Lima;
- periodos DEMO;
- `MockRiskProvider` determinístico;
- API de metadata, mapa y comparación;
- frontend React/TypeScript;
- mapa Leaflet;
- filtro por periodo, selección, detalle y comparación;
- trazabilidad del provider/modelo/dataset activo.

**Nada del catálogo o de los valores DEMO constituye evidencia del proyecto.** Los puntos no fijan la futura unidad espacial y los valores sintéticos no son probabilidades, predicciones ni niveles reales de riesgo.

## GitFlow

- `main`: línea estable.
- `develop`: integración.
- `feature/*`: trabajo aislado.
- `release/*`: preparación de entregas.
- `hotfix/*`: correcciones urgentes.

El trabajo normal entra primero a `develop` mediante PR. `main` se reserva para cortes estables.

## Ejecutar API

Requisitos: Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn raster_api.main:app --app-dir apps/api/src --reload
```

Endpoints actuales:

- `GET /health`
- `GET /model/metadata`
- `GET /metadata/spatial-units`
- `GET /metadata/periods`
- `GET /risk?spatial_unit=...&period=...`
- `GET /risk/map?period=...`
- `POST /risk/compare`

## Ejecutar frontend

Con la API corriendo en `http://localhost:8000`:

```bash
cd apps/web
npm install
npm run dev
```

La interfaz estará disponible en `http://localhost:5173`.

## Calidad

Backend:

```bash
ruff check .
pytest
```

Frontend:

```bash
cd apps/web
npm run typecheck
npm run build
```

La documentación de arquitectura está en `docs/architecture/`.
