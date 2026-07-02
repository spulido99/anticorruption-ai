# Prototipo: ingesta de muestra de SECOP II a DuckDB — informe de calidad y viabilidad

**Fecha:** 2026-07-02 · **Ticket:** [#5](https://github.com/spulido99/anticorruption-ai/issues/5)
**Método:** estadísticas sobre el dataset **completo** vía agregaciones SoQL server-side (no extrapoladas) + muestra estratificada por año de firma (101.351 contratos de `jbjy-vk9h`, 10k/año 2015–2026) + 20.000 procesos recientes de `p6dx-8zbt`, cargados a DuckDB con todas las columnas como texto crudo. Código: [`ingest_sample.py`](ingest_sample.py); métricas crudas: `metrics.json` (regenerable ejecutando el script).

## Veredicto

**La ingesta nacional local es viable**, con dos condiciones: ingesta streaming/por lotes **sin retener CSVs crudos** (el disco disponible hoy —34 GB libres— no aguanta los ~40 GB de CSV del núcleo v1 más la base), y **app token de Socrata** para no depender del pool compartido por IP. El dataset completo del núcleo v1 cabe en DuckDB en ~12–15 GB.

## 1. Calidad — dataset completo (5.657.593 contratos, verificado server-side)

| Problema | Magnitud | % | Implicación |
|---|---|---|---|
| `nit_entidad` con >9 dígitos (DV pegado) | 478.330 | 8,5 % | normalizar NIT a 9 dígitos (algoritmo DIAN) antes de cualquier agregación por entidad |
| `fecha_de_firma` NULL | 409.169 | 7,2 % | las series temporales pierden ~7 % de contratos; usar `fecha_de_inicio` como fallback |
| `valor_del_contrato` = 0 | 193.827 | 3,4 % | tratar 0 como "no reportado", no como gratis |
| `documento_proveedor` = 'No Definido' | 171.589 | 3,0 % | tratar placeholder como NULL |
| `fecha_de_inicio_del_contrato` NULL | 429.181 | 7,6 % | ídem fechas |
| `id_contrato` duplicado | existe (pares exactos) | bajo | filas 100 % idénticas → `SELECT DISTINCT` al ingerir; upsert por `id_contrato` es seguro |
| Valores negativos | 0 | — | no hay |

Todos los campos clave reportan 100 % non-null en la API — pero "non-null" incluye placeholders (`'No Definido'`) y ceros: **la limpieza es semántica, no de NULLs**.

## 2. Calidad — muestra local (101.351 contratos, 84 columnas)

- **NIT de entidad**: 92,3 % con 9 dígitos, 7,6 % con 10 (DV pegado — consistente con el 8,5 % del dataset completo), 88 filas con <9 dígitos. 0 no-numéricos.
- **`documento_proveedor`**: 1,4 % no-numéricos (documentos extranjeros y basura mezclados) — la normalización de contratista necesita el campo `tipodocproveedor`.
- **Fechas**: 0 fechas no parseables y 0 fuera de rango en la muestra — la suciedad de fechas extremas reportada en el SECOP Integrado (`rpmr-utcd`) **no** aparece en `jbjy-vk9h`.
- **Valores**: 100 % casteables a DECIMAL; 2 contratos > 1 billón COP (outliers a verificar contra expediente, no errores de parseo).
- **Invariantes de formato confirmados**: `id_contrato` 100 % `CO1.PCCNTR.*`; `proceso_de_compra` 100 % `CO1.BDOS.*`.

## 3. La llave de cruce contratos↔procesos funciona

El `noticeUID` (`CO1.NTC.*`) embebido en `urlproceso`:

- **Contratos**: extraíble en 101.350/101.351 (99,999 %).
- **Procesos publicados** (adjudicados, en ofertas, en observaciones…): extraíble en el **100 %**.
- **Procesos en borrador/planeación** (`estado_resumen = 'No Definido'`, 66 % de la muestra de procesos *recientes*): 0 % — su `urlproceso` es la página de login de SECOP. No son cruzables ni relevantes para contratos (aún no publican aviso).

Conclusión para el modelo de datos (#6): extraer `notice_uid` como columna materializada en ambas tablas al ingerir; el join es confiable para todo proceso publicado.

## 4. Viabilidad de la ingesta nacional local

Medido en esta corrida (sin app token, red doméstica):

| Métrica | Valor | Extrapolación |
|---|---|---|
| Throughput de descarga SODA | 1,9 MB/s | `jbjy-vk9h` completo (~9,7 GB CSV): **~1,5 h**; núcleo v1 (~40 GB): **~6 h** |
| Tamaño DuckDB | 423 B/fila (vs 1.590 B/fila CSV) | compresión ~3,8×; núcleo v1 (~49 M filas): **~12–15 GB** |
| Disco libre hoy | 34 GB | DuckDB completo cabe; **CSVs crudos + DB no caben** |
| Throttling sin token | 0 × 429 en ~30 requests | funciona, pero el pool por IP es compartido — token gratuito recomendado |

**Estrategia de ingesta recomendada** (insumo para #6):

1. Carga inicial por dataset vía export streaming (`rows.csv?accessType=DOWNLOAD`) **procesado por lotes hacia DuckDB sin persistir el CSV completo** (o páginas SODA de 100k–200k con `$order` sobre llave estable).
2. `SELECT DISTINCT` (o dedup por llave natural) al cargar — los duplicados son filas idénticas.
3. Normalizar al ingerir: NIT a 9 dígitos, placeholders → NULL, `notice_uid` materializado.
4. Delta diario por `:updated_at` de Socrata + upsert por llave natural (`id_contrato` / `id_del_proceso`).
5. Registrar app token de Socrata (gratis) antes de la carga inicial.
6. Si el disco sigue en ~34 GB libres, empezar solo con SECOP II (`jbjy-vk9h` + `p6dx-8zbt` ≈ 5 GB en DuckDB) y sumar SECOP I/Integrado después o liberar disco.

## 5. Qué NO valida este prototipo

- El join real contratos↔procesos por `notice_uid` a escala (las muestras son tajadas distintas; validarlo en la ingesta completa).
- La calidad de SECOP I (`f789-7hwg`, `qddk-cgux`) y del Integrado — solo se perfiló SECOP II.
- Tiempos de descarga con app token (probablemente mejores).
