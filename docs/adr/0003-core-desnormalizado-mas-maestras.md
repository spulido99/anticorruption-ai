# core: tablas anchas desnormalizadas + maestras derivadas

`core.contratos` y `core.procesos` son **tablas anchas desnormalizadas**: cada fila lleva embebidos los atributos ya resueltos de entidad y contratista (llave normalizada, nombre canónico) — cero joins para el análisis corriente. Además se materializan **maestras derivadas** `core.entidades` y `core.contratistas` (una fila por identidad resuelta: llave, nombre canónico, variantes de nombre vistas, conteos y rangos de actividad) como fuente para perfiles y para proyectar el grafo. Todo se deriva en el mismo paso raw→core; nada se mantiene a mano.

No usamos esquema estrella con joins: en DuckDB la diferencia de rendimiento es marginal y la compresión por diccionario absorbe la repetición de valores, mientras que la tabla ancha simplifica cada consulta de las skills. La resolución de identidad ocurre **una vez** en raw→core y queda grabada en columnas — no se recalcula por consulta ni queda a criterio de cada skill.
