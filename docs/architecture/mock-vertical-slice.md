# Mock vertical slice v0

## Objetivo

Validar el recorrido técnico completo antes de disponer del dataset perfilado y del modelo real:

```text
MockRiskProvider -> FastAPI -> React -> Leaflet -> filtro/detalle/comparación
```

## Qué demuestra

- El frontend consume contratos del backend en lugar de conocer la implementación del modelo.
- Un cambio de periodo refresca el conjunto de resultados mostrado en el mapa.
- Una unidad puede seleccionarse y mostrar trazabilidad del resultado.
- Dos unidades pueden consultarse mediante el mismo contrato de comparación.
- El proveedor, versión de modelo y versión de dataset permanecen visibles.

## Qué NO demuestra

Este slice no valida el modelo científico ni toma decisiones sobre:

- unidad espacial definitiva;
- granularidad temporal definitiva;
- definición matemática del riesgo;
- horizonte predictivo;
- baseline;
- CNN-RNN concreta;
- LSTM, GRU o ConvLSTM;
- métrica o umbral de desempeño.

Los puntos representativos y periodos de `demo_catalog.py` son fixtures de integración. El valor producido por `MockRiskProvider` se deriva de un hash determinístico y carece de interpretación probabilística o analítica.

## Sustitución futura

La aplicación debe conservar el mismo límite `RiskProvider` cuando aparezcan los proveedores reales:

```text
MockRiskProvider
      |
      +--> BaselineRiskProvider
      |
      +--> CNNRNNRiskProvider
```

El perfilamiento de datos y el benchmarking podrán modificar las implementaciones y metadata sin obligar a rehacer la interfaz de usuario ni los casos de uso de consulta/comparación.
