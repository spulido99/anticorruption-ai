# Dos capas materializadas: raw → core

La limpieza de SECOP es semántica, no de NULLs (NITs con DV pegado, placeholders `'No Definido'`, ceros como "no reportado" — ver [prototipo #5](../../prototypes/secop-duckdb-sample/REPORT.md)), y sus reglas van a iterar. Por eso la base tiene dos esquemas materializados: **`raw`** (los datos tal cual llegan de Socrata, **todas las columnas** de cada dataset, todo como texto) y **`core`** (tablas canónicas limpias y tipadas que consumen las skills de análisis). La transformación raw→core es un paso reproducible y re-ejecutable sin re-descargar (~6 h de descarga para el núcleo v1).

`raw` conserva todas las columnas — no un subconjunto curado — porque el criterio de relevancia cambia con cada red flag nueva del catálogo, la descarga es la parte lenta y frágil del pipeline, y el texto repetitivo comprime muy bien en DuckDB. `core` sí es curado.

## Consequences

- Disco ~2× sobre la estimación de solo-core. Con ~34 GB libres, la v1 arranca **solo con SECOP II** (`jbjy-vk9h` + `p6dx-8zbt` ≈ 10 GB con ambas capas); SECOP I se suma después o al liberar disco.
- Para hallazgos publicables, la transformación auditable raw→core es trazabilidad metodológica: siempre se puede mostrar qué se le hizo al dato crudo.
