# Raster Analytics Web

Aplicación web para el análisis espaciotemporal del riesgo de atropello peatonal en Lima Metropolitana.

## Estado

Repositorio inicial del proyecto SI727. La arquitectura se desarrollará de forma incremental y desacoplada para permitir la evolución `mock -> baseline -> CNN-RNN` sin rehacer la aplicación.

## Flujo Git

Se utilizará un flujo inspirado en GitFlow:

- `main`: línea estable.
- `develop`: integración del desarrollo.
- `feature/*`: trabajo aislado por capacidad.
- `release/*`: preparación de entregas cuando sea necesario.
- `hotfix/*`: correcciones urgentes sobre `main`.

Las decisiones técnicas aún no validadas por perfilamiento o benchmarking se consideran provisionales.
