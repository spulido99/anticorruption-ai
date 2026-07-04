# Capa `metrics` — indicadores de red flags precomputados

**Decidida en:** [#8](https://github.com/spulido99/anticorruption-ai/issues/8) · **construida en:** [#14](https://github.com/spulido99/anticorruption-ai/issues/14) · **fichas:** [`docs/research/red-flags-contratacion.md`](../research/red-flags-contratacion.md)

Regla de #8: **ningún número entra a un hallazgo sin salir de `metrics`**. Las skills leen estas tablas; el SQL ad-hoc queda para exploración.

## Cómo se construye

```
python -m secop --db data/secop.duckdb metrics               # build con umbrales versionados
python -m secop --db data/secop.duckdb metrics --calibrate   # recalibra umbrales y build
```

Build determinista desde `core` (re-ejecutable sin re-descargar). Los umbrales **no** se calculan en el build: viven en [`src/secop/umbrales.json`](../../src/secop/umbrales.json), versionado en el repo, y `metrics.build_info` guarda la copia exacta usada más la fecha del build — un build es reproducible contra un JSON dado.

### Calibración (estilo OCP: percentiles/IQR por grupo comparable)

`calibrate()` construye metrics con umbrales neutros, lee las distribuciones de las tablas resultantes y deriva los cortes:

| Umbral | Fórmula | Grupo comparable | Piso de datos |
|---|---|---|---|
| `rf01_share_outlier` | mín(Q3 + 1,5·IQR, P95) del share de single bidding entidad-año | `orden` de la entidad | ≥ 20 procesos competitivos adjudicados por entidad-año; ≥ 200 entidades-año por grupo |
| `rf02_pct_directa_valor_outlier` | mín(Q3 + 1,5·IQR, P95) del % directa en valor | `orden` | ≥ 20 contratos; ≥ 200 por grupo |
| `rf07_ventana` | P5 / P95 de los días publicación→adjudicación | modalidad × año | ≥ 200 procesos por grupo |
| `rf08_pct_diciembre_p90` | P90 del % del valor firmado en diciembre | `orden` | ≥ 20 contratos; ≥ 200 por grupo |
| `rf08_preelectoral_p90` | P90 del ratio preelectoral | `orden` | ≥ 200 por grupo (sin piso de actividad: la ventana vive en el año anterior) |
| `rf11_pct_prorroga_p90` | P90 de la prórroga relativa | `tipo_de_contrato` | ≥ 200 contratos por grupo |
| `rf19_no_evaluable` | P90 del score de opacidad (escalar nacional) | — | — |

**Por qué el tope P95:** los shares viven en [0,1] y sus distribuciones nacionales se pegan a 1,0 — la regla IQR sin tope emite cortes > 1 (verificado: 1,28 para RF-01 Territorial, 1,85 para RF-02), o sea un flag que jamás dispara y que se lee como "todo limpio". Con el tope, el flag marca como mínimo el 5 % superior del grupo.

Constantes normativas que viajan en el mismo JSON: `rf05_share_outlier = 0.4` (ejemplo de OCP R040 — el grano par-mes está dominado por micro-pares, P75 nacional ≈ 0,1 %, así que un corte IQR flaggearía todo), `rf06_hhi_alto = 0.25` (convención antitrust), `rf06_min_contratos = 10`, `rf06_min_contratistas = 3`, `rf11_min_pct = 0.5` (eco del tope del 50 % de la Ley 80).

**Semántica de flags:** un flag es `NULL` cuando la entidad/grupo no alcanza el piso de datos o no hay corte calibrado para su grupo — *no evaluado* nunca se reporta como *limpio*. Los `boolean` solo aparecen donde la regla se pudo aplicar.

**Higiene de valores:** las sumas de valor excluyen `valor_atipico` (errores de digitación > 5×10¹¹ COP, marcados en core tras el hallazgo de #7); los conteos los incluyen y RF-19 los reporta.

## Tablas

### `metrics.procesos` (grano: proceso)

- **RF-01** `rf01_single_bid`: modalidad competitiva **y** adjudicado **y** (`proveedores_unicos_con = 1` o `respuestas_al_procedimiento = 1`). `NULL` fuera del universo competitivo-adjudicado (el denominador correcto, lección de #7).
- **RF-07** `rf07_dias`, `rf07_ventana` (`'corta'`/`'larga'`/`NULL`): días publicación→adjudicación contra P5/P95 de su modalidad×año.

### `metrics.contratos` (grano: contrato)

- **RF-11** `rf11_pct_prorroga`, `rf11_flag`: días adicionados relativos al plazo original. **Desviación declarada de la ficha:** en `jbjy-vk9h` la `fecha_de_fin_del_contrato` *ya incluye* la adición (verificado en la carga nacional: <0,6 % de los contratos con adición la contradicen), así que `plazo_original = (fin − inicio) − dias_adicionados`, no `fin − inicio`. Flag = pct > 50 % **y** > P90 del tipo de contrato.

### `metrics.entidad_anio` (grano: entidad × año)

- **RF-01** `rf01_share`, `rf01_flag`: share de single bidding sobre procesos competitivos adjudicados (año de la fecha de publicación).
- **RF-02** cuatro variantes: `pct_directa_n`, `pct_directa_valor` (la robusta, la que flaggea) y las `_estricta` que excluyen del numerador `tipo_de_contrato = 'Prestación de servicios'` (directa por diseño legal; domina el conteo).
- **RF-06** `rf06_hhi`, `rf06_n_contratistas`, `rf06_flag`: HHI del gasto por contratista (solo contratistas resueltos con valor sano > 0). Sin desagregar consorcios/UT — ver "Diferidos".
- **RF-08** `rf08_pct_diciembre`, `rf08_flag`; y `rf08_ratio_preelectoral`, `rf08_flag_preelectoral`: valor directo firmado en los 2 meses previos al inicio de la restricción de la Ley de Garantías (elecciones presidenciales: 2018-01-27, 2022-01-29, 2026-01-31) contra el promedio mensual de los 12 meses previos; la fila cae en el año electoral. El pico preelectoral es *conducta legal* — señal de planeación/clientelismo, no ilegalidad.
- **RF-19** componentes (`pct_contratistas_no_resueltos`, `pct_valor_cero`, `pct_valor_atipico`, `pct_procesos_sin_proveedor`), `rf19_score` (promedio de los disponibles) y `rf19_no_evaluable` (score > P90 nacional). **RF-19 modula todo lo demás:** una entidad `no_evaluable` no debe aparecer como "limpia" en ningún ranking.

### `metrics.entidad_contratista_12m` (grano: entidad × contratista × mes)

- **RF-05** `rf05_share`, `rf05_flag`: share del contratista en el gasto sano de la entidad en la ventana móvil de 12 meses que termina en `mes` (solo meses con actividad del par). Contratistas no resueltos: fuera del numerador, dentro del denominador (su gasto es real). Flag exige ≥ 20 contratos de la entidad en la ventana.

### `metrics.build_info`

`built_at`, el JSON exacto de umbrales usado, y los conteos de core — la trazabilidad que `documentar-hallazgo` estampa (fecha de snapshot).

## Indicadores diferidos (datos aún no ingeridos)

| Indicador | Qué falta |
|---|---|
| RF-09 publicación tardía | SECOP I (`f789-7hwg`/`qddk-cgux`): la ficha lo define sobre `fecha_de_cargue`, que no existe en SECOP II. |
| RF-10 adiciones en valor | SECOP I (directo) o `u8cx-r425` (modificaciones SECOP II, esquema sin verificar). `jbjy-vk9h` no trae valor de adiciones. |
| RF-13 proveedor recién creado | RUES (#19) para fecha de constitución real; `qmzu-gj57` (#21) para resolver por código. |
| RF-14 sancionados | SIRI + Boletín de Responsables Fiscales (#19) y multas SECOP. |
| Desagregación de consorcios (RF-05/06) | `ceth-n4bn` (#21): hoy un consorcio cuenta como su propio NIT efímero — el share del grupo económico queda subestimado. |
| RF-15b/c, RF-16 (variante fina de `red`) | `hgi6-6wh3` + `ceth-n4bn` (#21). |

## Reproducción de #7 (criterio de aceptación)

`python -m secop --db data/secop.duckdb verify` incluye `pilot_numbers_metrics`: los anclas de Boyacá recomputados desde `metrics`. Caveat de grano declarado en el código: metrics vive sobre core (sin duplicados exactos) y sus sumas excluyen atípicos, mientras #7 contó filas crudas del API con sumas sin winsorizar — los porcentajes deben coincidir a décimas; los valores absolutos son la variante sana.
