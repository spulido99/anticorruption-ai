# DuckDB como datastore; análisis de grafos en Python, no en la base

El sistema necesita un datastore local, $0 de costo fijo, para ~49 M de filas de SECOP. Elegimos **DuckDB** (validado en el prototipo [#5](https://github.com/spulido99/anticorruption-ai/issues/5): compresión ~3,8×, núcleo v1 ≈ 12–15 GB, un solo archivo compartible). Los análisis de red (centralidad, comunidades, caminos) **no** viven en la base: DuckDB proyecta listas de aristas (`GROUP BY` entidad↔contratista) y Python las carga en **igraph/NetworkX** — el grafo proyectado cabe en memoria de sobra.

## Considered Options

- **Postgres**: costo operativo de servidor, rompe "todo local y simple".
- **SQLite**: sin ventaja columnar para analítica.
- **Neo4j u otro grafo-DB**: infra adicional sin beneficio a esta escala; el grueso de las red flags son agregaciones SQL, no algoritmos de grafo.
- **Extensiones de grafos de DuckDB (DuckPGQ, Onager)**: proyectos de investigación en desarrollo (verificado 2026-07); pueden explorarse para un análisis puntual pero nunca como dependencia del núcleo.
