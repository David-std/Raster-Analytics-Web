# Web app · Mock vertical slice

Frontend provisional en React + TypeScript + Leaflet para validar el flujo `MockRiskProvider -> API -> mapa -> filtro -> detalle -> comparación`.

## Ejecutar

Con la API disponible en `http://localhost:8000`:

```bash
cd apps/web
npm install
npm run dev
```

Por defecto el frontend consulta `http://localhost:8000`. Para cambiarlo:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

En Windows puede crearse `apps/web/.env.local`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Importante

Todo lo visible en esta fase es **MOCK / DEMO**. Los nombres y puntos representativos permiten ejercitar la interfaz geoespacial, pero no fijan la unidad espacial definitiva del proyecto. Los valores son sintéticos y no representan probabilidades, predicciones ni resultados analíticos.
