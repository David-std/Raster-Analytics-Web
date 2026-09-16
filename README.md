# Raster Analytics Web

Aplicación web para el análisis espaciotemporal del riesgo de atropello peatonal en Lima Metropolitana.

## Estado actual

`scaffold v0`

La base se está construyendo para evolucionar sin acoplar la aplicación a una implementación concreta del modelo:

```text
MockRiskProvider -> BaselineRiskProvider -> CNNRNNRiskProvider
```

**Scaffold**, **mock** y **baseline** no son sinónimos:

- **Scaffold**: estructura ejecutable del proyecto y contratos entre componentes.
- **Mock**: implementación sintética para probar integración sin datos/modelo reales.
- **Baseline**: primer modelo real de referencia, construido después del perfilamiento de datos.

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
Mapa + filtros + comparación
```

El proyecto no asume todavía que la salida sea una probabilidad ni una predicción futura. La unidad espacial, unidad temporal, definición operativa del riesgo y configuración CNN-RNN siguen abiertas hasta perfilamiento y benchmarking.

## GitFlow

- `main`: línea estable.
- `develop`: integración.
- `feature/*`: trabajo aislado.
- `release/*`: preparación de entregas.
- `hotfix/*`: correcciones urgentes de producción/entrega estable.

El trabajo normal entra primero a `develop` mediante PR. `main` se reserva para cortes estables.

## API scaffold

Requisitos: Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn raster_api.main:app --app-dir apps/api/src --reload
```

Endpoints iniciales:

- `GET /health`
- `GET /model/metadata`
- `GET /risk?spatial_unit=...&period=...`
- `POST /risk/compare`

Todos los resultados actuales provienen de `MockRiskProvider` y deben tratarse únicamente como DEMO/MOCK.

## Calidad

```bash
ruff check .
pytest
```

La documentación de arquitectura está en `docs/architecture/architecture-v0.md`.
