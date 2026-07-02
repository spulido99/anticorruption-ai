# Radiografía de las fuentes de datos de contratación pública colombiana

**Fecha de investigación:** 2026-07-02
**Método:** todos los identificadores 4x4, conteos de filas, rangos de fechas y muestras de campos fueron verificados con requests directos a la API SODA de datos.gov.co (`https://www.datos.gov.co/resource/<4x4>.json?$select=count(1)`, `min()/max()`, muestras `$limit`) y a la API de metadatos (`https://www.datos.gov.co/api/views/<4x4>.json`) en la fecha indicada. Donde un dato no pudo verificarse, se dice explícitamente.

---

## 1. Resumen ejecutivo

El ecosistema de datos abiertos del SECOP (administrado por la Agencia Nacional de Contratación Pública — Colombia Compra Eficiente, CCE) vive **enteramente en datos.gov.co (plataforma Socrata)**. CCE no ofrece dumps propios: su página de datos abiertos solo enlaza a datos.gov.co ([colombiacompra.gov.co/transparencia/datos-abiertos/conjuntos-de-datos-abiertos](https://www.colombiacompra.gov.co/transparencia/datos-abiertos/conjuntos-de-datos-abiertos)). La actualización es **diaria** (metadatos de cada dataset y Manual M-MUDA-02 de CCE).

**Recomendación para una v1 de análisis anticorrupción:**

1. **`jbjy-vk9h` (SECOP II — Contratos Electrónicos, 5,66 M filas)** — el dataset más rico: valores pagados/facturados/pendientes, NIT de entidad y documento de proveedor, representante legal, supervisor, ordenador del gasto, origen de recursos. Es la fuente principal para contratos desde ~2018 (SECOP II es obligatorio para la mayoría de entidades desde 2020-2022).
2. **`f789-7hwg` (SECOP I — Procesos de Compra Pública, 6,38 M filas, cargues 2018-01-01 → hoy)** + **`qddk-cgux` (SECOP I Histórico, 6,12 M filas, 2004-11 → 2017-12)** — para el régimen de "simple publicidad" y la cola larga de entidades territoriales que siguieron usando SECOP I.
3. **`p6dx-8zbt` (SECOP II — Procesos, 8,75 M filas)** — necesario para medir competencia (número de oferentes, invitados, manifestaciones de interés) y procesos no adjudicados.
4. **`rpmr-utcd` (SECOP Integrado, 22,1 M filas)** — vista unificada SECOP I + II de procesos con contrato; útil como columna vertebral entidad-contratista-valor, pero con solo 22 columnas y fechas sucias (verificado: min fecha de firma 2000-01-01, max 2099-12-30).
5. **`rgxm-mmea` (TVEC, 165 K filas)** — órdenes de compra por acuerdos marco. **Riesgo detectado y verificado: el 100 % de las filas tiene `nit_entidad = "No Definido"` y `nit_proveedor = "No Aplica"`** — el cruce con SECOP solo es posible por nombre de entidad/proveedor o por `id_entidad` interno.

Datasets satélite valiosos: adiciones (`cb9c-h8sn`, `7fix-nd37`), multas y sanciones (`4n4q-k399`, `it5q-hg94`), proveedores registrados (`qmzu-gj57`), proponentes (`tauh-5jvn`, `hgi6-6wh3`), PAA (`9sue-ezhx`, `b6m4-qgqv`).

---

## 2. Tabla comparativa (todo verificado vía API el 2026-07-02)

| Dataset | 4x4 | Filas (count verificado) | Cobertura temporal (verificada) | Granularidad | Tamaño CSV estimado* |
|---|---|---|---|---|---|
| SECOP I — Procesos de Compra Pública | `f789-7hwg` | 6.382.831 | cargues 2018-01-01 → 2026-07-01 | proceso/adjudicación | ~11 GB |
| SECOP I — Procesos Histórico | `qddk-cgux` | 6.122.524 | cargues 2004-11-05 → 2017-12-31 | proceso/adjudicación | ~10 GB (no muestreado; mismo esquema que f789) |
| SECOP II — Procesos de Contratación | `p6dx-8zbt` | 8.752.791 | publicación 2015-04-16 → 2026-07-01 | proceso | ~10 GB |
| SECOP II — Contratos Electrónicos | `jbjy-vk9h` | 5.657.593 | firma 2015-06-11 → 2026-07-01 | contrato | ~9,7 GB |
| SECOP Integrado | `rpmr-utcd` | 22.112.274 (SECOPI: 14.532.362 / SECOPII: 7.579.912) | fechas de firma sucias (2000 → 2099); en la práctica ~2007 → hoy | contrato | ~18 GB |
| TVEC — Consolidado | `rgxm-mmea` | 165.472 | años 2013 → 2026 | orden de compra | ~130 MB |
| SECOP II — PAA Detalle | `9sue-ezhx` | 11.456.697 | años 2016 → 2027 | línea de plan de compras | grande (no muestreado) |
| SECOP II — PAA Encabezado | `b6m4-qgqv` | 52.775 | por vigencia | plan por entidad/año | pequeño |
| Multas y Sanciones SECOP I | `4n4q-k399` | 1.705 | actualizado hasta 2026-05-26 | sanción | trivial |
| SECOP II — Multas y Sanciones | `it5q-hg94` | 538 | actualizado 2026-07-02 | sanción | trivial |
| SECOP II — Proveedores Registrados | `qmzu-gj57` | 1.579.694 | registro desde 2015 | proveedor | moderado |
| SECOP II — Adiciones | `cb9c-h8sn` | 23.223.734 | desde 2020 (creación) | evento de modificación | grande |
| SECOP I — Adiciones | `7fix-nd37` | 1.500.172 | desde 2015 (según descripción CCE) | adición por adjudicación | pequeño |
| SECOP I — Proponentes | `tauh-5jvn` | 119.942 | — | proponente×proceso | pequeño |
| SECOP — Convenios Interadministrativos | `s484-c9k3` | 89.664 | desde 2019-01-01 (descripción CCE) | contrato | pequeño |

\* Estimación: bytes de una muestra CSV de 1.000 filas (`/resource/<4x4>.csv?$limit=1000`) × total de filas. Ej.: jbjy-vk9h ≈ 1,72 KB/fila.

URL canónica de cada dataset: `https://www.datos.gov.co/d/<4x4>` (ej.: [datos.gov.co/d/jbjy-vk9h](https://www.datos.gov.co/d/jbjy-vk9h)). Página API Foundry: `https://dev.socrata.com/foundry/www.datos.gov.co/<4x4>`.

---

## 3. Fichas por dataset

### 3.1 SECOP I — Procesos de Compra Pública (`f789-7hwg`)

- **URL:** https://www.datos.gov.co/d/f789-7hwg — metadatos: https://www.datos.gov.co/api/views/f789-7hwg.json
- **Descripción oficial:** "Procesos de Compra pública registrados en el SECOP I desde el 01 de enero de 2018, contiene la información del proceso, fase de selección y la adjudicación". Frecuencia de actualización declarada: **diaria**; cobertura geográfica: **Nacional**.
- **Esquema (79 columnas; las clave para anticorrupción):**
  - Entidad: `nombre_entidad`, `nit_de_la_entidad` (text), `c_digo_de_la_entidad` (number), `nivel_entidad`, `orden_entidad`, `departamento_entidad`, `municipio_entidad`
  - Contratista: `tipo_identifi_del_contratista` ("Nit de Persona Jurídica", "Cédula de Ciudadanía", "No Definido"…), `identificacion_del_contratista`, `nom_razon_social_contratista`, `dpto_y_muni_contratista`; representante legal (`tipo_doc_representante_legal`, `identific_representante_legal`, `nombre_del_represen_legal`, `sexo_replegal`)
  - Proceso/contrato: `numero_de_proceso`, `numero_de_contrato`, `numero_de_constancia`, `id_adjudicacion`, `modalidad_de_contratacion` (+`id_modalidad`), `estado_del_proceso`, `tipo_de_contrato`, `objeto_a_contratar`, `detalle_del_objeto_a_contratar`, clasificación UNSPSC (`id_grupo/familia/clase` + nombres)
  - Valores: `cuantia_proceso`, `cuantia_contrato`, `valor_total_de_adiciones`, `valor_contrato_con_adiciones`, `tiempo_adiciones_en_dias/meses`, `moneda`
  - Fechas: `fecha_de_cargue_en_el_secop`, `fecha_de_firma_del_contrato`, `fecha_ini_ejec_contrato`, `fecha_fin_ejec_contrato`, `fecha_liquidacion`, `ultima_actualizacion`
  - Otros: `ruta_proceso_en_secop_i` (URL al expediente), `es_mipyme`, `codigo_bpin`, `pliegos_tipo`, marcas de posconflicto
- **Volumen (verificado):** 6.382.831 filas; ~1,74 KB/fila CSV ⇒ **~11 GB**.
- **Cobertura (verificada):** `fecha_de_cargue_en_el_secop` de 2018-01-01 a 2026-07-01; `anno_cargue_secop` 2018–2026. Nacional + territorial (departamento/municipio de entidad y de ejecución).
- **Calidad (verificada por consulta):** 570.017 filas con `cuantia_contrato = 0`; 541.635 filas con `identificacion_del_contratista = 'No Definido'` (procesos no adjudicados o mal diligenciados). El dataset mezcla procesos en todas las fases (convocatoria, celebrado, liquidado…): para "contratos reales" hay que filtrar `estado_del_proceso` en Celebrado/Liquidado/Terminado sin liquidar, como recomienda el propio manual de CCE.
- **Descarga masiva:** export completo `https://www.datos.gov.co/api/views/f789-7hwg/rows.csv?accessType=DOWNLOAD` o paginación SODA (ver §5).

### 3.2 SECOP I — Procesos Histórico (`qddk-cgux`)

- **URL:** https://www.datos.gov.co/d/qddk-cgux
- **Volumen (verificado):** 6.122.524 filas. **Cobertura (verificada):** cargues 2004-11-05 → 2017-12-31. Mismo esquema que `f789-7hwg`. Es el complemento imprescindible para series históricas; CCE lo lista como uno de sus 4 datasets principales ([conjuntos-de-datos-abiertos](https://www.colombiacompra.gov.co/transparencia/datos-abiertos/conjuntos-de-datos-abiertos)).
- Nota: el manual de CCE dice que SECOP I en datos abiertos arranca "a partir del año 2011", pero la API devuelve cargues desde 2004 — los registros 2004–2010 existen aunque su calidad es menor.

### 3.3 SECOP II — Procesos de Contratación (`p6dx-8zbt`)

- **URL:** https://www.datos.gov.co/d/p6dx-8zbt
- **Descripción oficial:** "Registro de los procesos de compra, sean o no adjudicados, hechos en la plataforma SECOP II desde su lanzamiento". Actualización diaria.
- **Esquema (59 columnas; clave):**
  - Entidad: `entidad`, `nit_entidad` (text), `codigo_entidad` (number), `departamento_entidad`, `ciudad_entidad`, `ordenentidad`
  - Proceso: `id_del_proceso` (**formato `CO1.REQ.*` en el 100 % de las filas — verificado**), `referencia_del_proceso`, `nombre_del_procedimiento`, `descripci_n_del_procedimiento`, `fase`, `modalidad_de_contratacion`, `justificaci_n_modalidad_de`, `estado_del_procedimiento`, `estado_resumen`, `tipo_de_contrato`, `codigo_principal_de_categoria` (UNSPSC)
  - **Competencia (exclusivo de este dataset):** `proveedores_invitados`, `proveedores_con_invitacion` (directa), `proveedores_que_manifestaron`, `respuestas_al_procedimiento`, `proveedores_unicos_con` (respuestas), `visualizaciones_del`, `numero_de_lotes`
  - Adjudicación: `adjudicado` (Si/No), `id_adjudicacion`, `fecha_adjudicacion`, `valor_total_adjudicacion`, `nombre_del_proveedor`, `nit_del_proveedor_adjudicado`, `codigoproveedor`
  - Valores/fechas: `precio_base`, `fecha_de_publicacion_del`, fechas por fase, `urlproceso` (contiene `noticeUID=CO1.NTC.*`)
- **Volumen (verificado):** 8.752.791 filas; ~1,15 KB/fila ⇒ **~10 GB**.
- **Cobertura (verificada):** publicación 2015-04-16 → 2026-07-01. Nacional/territorial.
- **Calidad (verificada):** solo 854.118 procesos con `adjudicado = 'Si'` vs 7.898.673 con 'No' (la mayoría son contratación directa donde la "adjudicación" no se marca, procesos en curso o desiertos); `nit_del_proveedor_adjudicado = 'No Definido'` es masivo en la muestra. Una fila por proceso, no por lote: procesos multi-lote pierden detalle de adjudicación por lote.
- **Descarga masiva:** ídem §5.

### 3.4 SECOP II — Contratos Electrónicos (`jbjy-vk9h`)

- **URL:** https://www.datos.gov.co/d/jbjy-vk9h — Foundry: https://dev.socrata.com/foundry/www.datos.gov.co/jbjy-vk9h
- **Descripción oficial:** "Información de los contratos registrados en SECOP II desde su lanzamiento". Actualización diaria.
- **Esquema (84 columnas; clave):**
  - Entidad: `nombre_entidad`, `nit_entidad` (**tipo `number` — ojo, ver §4**), `codigo_entidad` (number), `departamento`, `ciudad`, `orden`, `sector`, `rama`
  - Contratista: `tipodocproveedor` ("Cédula de Ciudadanía", "Nit"…), `documento_proveedor` (text), `proveedor_adjudicado` (nombre), `codigo_proveedor`, `es_grupo` (consorcios/UT), `es_pyme`
  - Identificadores: `proceso_de_compra` (**formato `CO1.BDOS.*` en el 100 % de filas — verificado**), `id_contrato` (**`CO1.PCCNTR.*`**), `referencia_del_contrato`, `urlproceso` (contiene `noticeUID=CO1.NTC.*`)
  - Valores (los más ricos del ecosistema): `valor_del_contrato`, `valor_pagado`, `valor_facturado`, `valor_pendiente_de_pago`, `valor_pendiente_de_ejecucion`, `valor_amortizado`, `saldo_cdp`, `valor_de_pago_adelantado`; desagregación por fuente: `presupuesto_general_de_la_nacion_pgn`, `sistema_general_de_participaciones`, `sistema_general_de_regal_as`, `recursos_propios`, `recursos_de_credito`
  - Fechas: `fecha_de_firma`, `fecha_de_inicio_del_contrato`, `fecha_de_fin_del_contrato`, `fecha_inicio/fin_liquidacion`, `ultima_actualizacion`
  - Trazabilidad humana (oro anticorrupción): representante legal (nombre, tipo/número de documento, género, nacionalidad), `nombre_supervisor` + documento, `nombre_ordenador_del_gasto` + documento, `nombre_ordenador_de_pago` + documento, banco/cuenta del contratista
  - Otros: `estado_contrato`, `modalidad_de_contratacion`, `justificacion_modalidad_de`, `objeto_del_contrato`, `dias_adicionados`, `origen_de_los_recursos`, `destino_gasto`
- **Volumen (verificado):** 5.657.593 filas; ~1,72 KB/fila ⇒ **~9,7 GB**.
- **Cobertura (verificada):** firmas 2015-06-11 → 2026-07-01. Nacional/territorial.
- **Calidad (verificada por consulta):**
  - 193.827 contratos con `valor_del_contrato = 0`.
  - 171.589 con `documento_proveedor = 'No Definido'`.
  - **478.330 filas con `nit_entidad` de más de 9 dígitos** (`$where=nit_entidad > 999999999`) — NIT con dígito de verificación concatenado o error de digitación; ej. observado: `8001136727`.
  - `valor_pagado`/`valor_facturado` dependen de que la entidad use la gestión contractual electrónica: hay ceros que significan "no reportado", no "no pagado".
- **Descarga masiva:** ídem §5.

### 3.5 SECOP Integrado (`rpmr-utcd`)

- **URL:** https://www.datos.gov.co/d/rpmr-utcd
- **Descripción oficial:** "Información integrada de los procesos de compra pública que se han registrado en las plataformas SECOP I y II, que han finalizado con un contrato."
- **Esquema (22 columnas):** `nivel_entidad`, `codigo_entidad_en_secop`, `nombre_de_la_entidad`, `nit_de_la_entidad` (text), `departamento_entidad`, `municipio_entidad`, `estado_del_proceso`, `modalidad_de_contrataci_n`, `objeto_a_contratar`, `objeto_del_proceso`, `tipo_de_contrato`, `fecha_de_firma_del_contrato`, `fecha_inicio/fin_ejecuci_n`, `numero_del_contrato`, `numero_de_proceso`, `valor_contrato`, `nom_raz_social_contratista`, `url_contrato`, **`origen`** (SECOPI/SECOPII), `tipo_documento_proveedor`, `documento_proveedor`.
- **Volumen (verificado):** 22.112.274 filas — `origen='SECOPI'`: 14.532.362; `origen='SECOPII'`: 7.579.912. ~0,82 KB/fila ⇒ **~18 GB**.
- **Cobertura (verificada):** `min(fecha_de_firma_del_contrato)` = 2000-01-01 y `max` = **2099-12-30** — fechas basura en los extremos; el grueso real va de ~2007 a hoy. Nacional/territorial.
- **Calidad (verificada):** 0 filas con NIT de entidad nulo; solo 75 con `documento_proveedor` nulo, pero abundan `tipo_documento_proveedor = 'No Definido'`. `numero_de_proceso` es texto libre en filas SECOP I/II antiguas (ej. observado: "Contrato de prestación de servicios No. 566 de 2023"). Al ser una integración row-per-contract con solo 22 columnas, pierde toda la riqueza de `jbjy-vk9h`. Nota curiosa: el catálogo Socrata atribuye el dataset a "Alcaldía de Somondoco, Boyacá" (error de metadatos del portal), pero los custom fields internos confirman que el responsable es CCE.
- **Cuándo usarlo:** deduplicación entidad-contratista-valor entre plataformas y series largas; no para análisis fino.

### 3.6 TVEC — Tienda Virtual del Estado Colombiano (`rgxm-mmea`)

- **URL:** https://www.datos.gov.co/d/rgxm-mmea
- **Descripción oficial:** "Procesos de compra pública hechos a través de procesos de agregación de la demanda en acuerdos marco, en la plataforma de Tienda Virtual del Estado Colombiano". Es decir: **órdenes de compra bajo Acuerdos Marco de Precios e Instrumentos de Agregación de Demanda** — no existe un dataset separado "Acuerdos Marco"; este consolidado es la fuente (el instrumento va en la columna `agregacion`).
- **Esquema (22 columnas):** `a_o`, `identificador_de_la_orden`, `rama/orden/sector_de_la_entidad`, `entidad`, `solicitante`, `fecha`, `fecha_vence`, `proveedor`, `estado`, `items` (texto con detalle), `total`, **`agregacion`** (nombre del acuerdo marco), `ciudad`, `espostconflicto`, `nit_proveedor`, `nit_entidad`, `id_entidad`, `actividad_economica_proveedor`.
- **Volumen (verificado):** 165.472 filas; ~0,79 KB/fila ⇒ **~130 MB**.
- **Cobertura (verificada):** años 2013 → 2026. Nacional.
- **Calidad (verificada — hallazgo crítico):** el conteo con `$where=nit_entidad='No Definido'` devuelve **165.472 = 100 % de las filas**, y `nit_proveedor='No Aplica'` también 165.472. **Hoy el dataset no trae ningún NIT utilizable**: el cruce con SECOP debe hacerse por nombre de entidad/proveedor (fuzzy) o manteniendo un mapeo propio de `id_entidad`. Además `items` es un blob de texto semiestructurado.
- **Descarga masiva:** trivial por tamaño (un solo GET al export CSV).

### 3.7 Plan Anual de Adquisiciones — SECOP II (`9sue-ezhx` detalle, `b6m4-qgqv` encabezado)

- **URLs:** https://www.datos.gov.co/d/9sue-ezhx y https://www.datos.gov.co/d/b6m4-qgqv
- **Detalle (`9sue-ezhx`, 32 columnas):** una fila por línea de compra planeada y por **versión** del PAA: `nit_entidad`, `codigo_entidad`, `nombre_entidad`, `descripcion`, `valor_total_esperado`, `modalidad`, `categorias_unspsc`, `annio`, `version_del_paa`, `procesos_relacionados` (enlaza a procesos SECOP II), `id_paa_encabezado`.
- **Volumen (verificado):** 11.456.697 filas (infla porque cada versión del PAA re-publica todas las líneas); años 2016 → 2027. Encabezado: 52.775 filas.
- **Uso anticorrupción:** contraste plan vs ejecución (compras no planeadas, fraccionamiento). Para SECOP I existen los equivalentes `azeg-sgqg` (PAA Detalle) y `prdx-nxyp` (PAA Encabezado) — identificados en el catálogo, no conteados.
- **Calidad:** hay que quedarse con la última `version_del_paa` por entidad/año para no duplicar; fechas almacenadas como texto.

### 3.8 Multas y Sanciones (`4n4q-k399` SECOP I, `it5q-hg94` SECOP II)

- **URLs:** https://www.datos.gov.co/d/4n4q-k399 y https://www.datos.gov.co/d/it5q-hg94
- **SECOP I (14 columnas):** `nit_entidad`, `documento_contratista`, `nombre_contratista`, `numero_de_contrato`, `valor_sancion`, `fecha_de_firmeza`, `numero_de_resolucion`. **1.705 filas** (verificado; última actualización de filas 2026-05-26).
- **SECOP II (17 columnas):** `id_proceso`, `id_contrato`, `codigo_entidad_creadora`, código/nombre del proveedor multado, `valor`, `valor_pagado`, `tipo_de_sancion`, `estado`. **538 filas** (verificado).
- **Calidad:** cobertura bajísima frente al universo real de sanciones (las entidades casi no las registran); en SECOP II el proveedor se identifica por código interno, no por NIT — hay que resolverlo contra `qmzu-gj57`. Útil como semilla, insuficiente como censo. Complementar con "Antecedentes SIRI" de la Procuraduría (`iaeu-rcn6`) y "Responsabilidad Fiscal" de la Contraloría (`jr8e-e8tu`), ambos en datos.gov.co.

### 3.9 SECOP II — Proveedores Registrados (`qmzu-gj57`)

- **URL:** https://www.datos.gov.co/d/qmzu-gj57
- **Esquema (25 columnas):** `codigo` (código interno de proveedor — la llave que usan otros datasets SECOP II), `nombre`, `nit` (text), `es_entidad`, `es_grupo`, `esta_activa`, `fecha_creacion`, ubicación, `tipo_empresa`, representante legal (nombre, tipo y número de documento, teléfono, correo), `espyme`.
- **Volumen (verificado):** 1.579.694 filas. Nacional (incluye proveedores extranjeros con campo `pais`).
- **Uso:** tabla maestra para resolver `codigo_proveedor`/`codigoproveedor` → NIT y para detectar redes (mismo representante legal en varios proveedores, direcciones/teléfonos compartidos).

### 3.10 Adiciones y modificaciones

- **SECOP II — Adiciones (`cb9c-h8sn`):** **23.223.734 filas** (verificado) pero solo 5 columnas: `identificador`, `id_contrato` (CO1.PCCNTR — cruza con `jbjy-vk9h`), `tipo`, `descripcion`, `fecharegistro`. Es un log de eventos de modificación; el volumen enorme confirma el hallazgo de OCP de que "cualquier documento publicado tras la firma puede contarse como modificación" ([open-contracting.org, red flags en América Latina](https://www.open-contracting.org/2019/06/27/examining-procurement-red-flags-in-latin-america-with-data/)). Para valores adicionados usar mejor `dias_adicionados` de jbjy y `u8cx-r425` (SECOP II — Modificaciones a contratos).
- **SECOP I — Adiciones (`7fix-nd37`):** 1.500.172 filas (verificado); `id_adjudicacion`, `adicion_en_valor`, `adicion_en_dias/meses`, `fecha_firma`. Cruza con `f789-7hwg.id_adjudicacion`. En f789 además vienen ya agregados `valor_total_de_adiciones` y `valor_contrato_con_adiciones`.

### 3.11 Otros datasets CCE relevantes (identificados en el catálogo, conteo no verificado salvo indicación)

`tauh-5jvn` SECOP I — Proponentes (119.942 filas, verificado; incluye `digito_verificaci_n_proponente` separado), `hgi6-6wh3` Proponentes por Proceso SECOP II, `mfmm-jqmq` Ejecución de contratos, `ibyt-yi2f` Facturas, `gjp9-cutm` Garantías, `u99c-7mfm` Suspensiones, `uymx-8p3j` Plan de pagos, `skc9-met7` Compromisos presupuestales, `a86w-fh92` Solicitudes CDP, `cwhv-7fnp` Rubros presupuestales, `d9na-abhe` BPIN por proceso, `e2u2-swiw`/`u8cx-r425` Modificaciones (procesos/contratos SECOP II), `36vw-pbq2`/`u5b4-ae3s` Modificaciones SECOP I, `ceth-n4bn` Grupos de proveedores (consorcios/UT), `3xwx-53wt` Origen de los recursos SECOP I, `wwhe-4sq8` Ubicaciones adicionales, `s484-c9k3` Convenios interadministrativos (89.664 filas, verificado), `ps88-5e3v`/`8kpz-m6cc`/`dmgg-8hin` Archivos descarga (índices de documentos adjuntos).

---

## 4. Identificación y cruces entre datasets

### Entidades compradoras

| Dataset | Campo NIT | Tipo | Campo código |
|---|---|---|---|
| f789-7hwg / qddk-cgux | `nit_de_la_entidad` | text (9 dígitos sin DV en muestra) | `c_digo_de_la_entidad` (number) |
| p6dx-8zbt | `nit_entidad` | text | `codigo_entidad` (number) |
| jbjy-vk9h | `nit_entidad` | **number** | `codigo_entidad` (number) |
| rpmr-utcd | `nit_de_la_entidad` | text | `codigo_entidad_en_secop` (text) |
| rgxm-mmea (TVEC) | `nit_entidad` | text, **100 % "No Definido"** | `id_entidad` (interno TVEC) |

**La llave de cruce práctica entre plataformas es el NIT de entidad sin dígito de verificación** (9 dígitos). Problemas verificados: en jbjy es numérico y 478.330 filas superan 9 dígitos (DV pegado); en TVEC no existe. `codigo_entidad` de SECOP II ≠ `c_digo_de_la_entidad` de SECOP I (numeraciones internas distintas por plataforma).

### Contratistas

- SECOP I: `tipo_identifi_del_contratista` + `identificacion_del_contratista` (NIT o cédula, texto). El DV está separado solo en `tauh-5jvn` (`digito_verificaci_n_proponente`).
- SECOP II: `tipodocproveedor` + `documento_proveedor` (texto) + `codigo_proveedor` (interno; resolver contra `qmzu-gj57.codigo`).
- Integrado: `tipo_documento_proveedor` + `documento_proveedor`.
- TVEC: solo `proveedor` (nombre) — NIT inutilizable hoy.
- Cédulas y NITs comparten el mismo campo: distinguir siempre por el campo de tipo. Consorcios/UT (SECOP II `es_grupo='Si'`) tienen NITs propios efímeros; desagregarlos vía `ceth-n4bn`.

### Cruces proceso/contrato (verificados con muestras)

- **Dentro de SECOP II:** `p6dx-8zbt.id_del_proceso` es 100 % `CO1.REQ.*` y `jbjy-vk9h.proceso_de_compra` es 100 % `CO1.BDOS.*` — **no existe join directo por ID de proceso** (verificado por conteo de prefijos). El puente fiable es el **`noticeUID=CO1.NTC.<n>`** embebido en el campo `urlproceso` de **ambos** datasets (verificado en muestras): extraerlo con regex y usarlo como llave. Alternativa imperfecta: `referencia_del_proceso` + `nit_entidad`.
- Satélites SECOP II → contratos: por `id_contrato` (`CO1.PCCNTR.*`).
- Integrado → jbjy: `numero_del_contrato` de filas `origen='SECOPII'` es `CO1.PCCNTR.*` (verificado en muestra) = `jbjy.id_contrato`.
- Integrado → SECOP I: `numero_del_contrato` con formato `AA-1-XXXXX`-tipo constancia (ej. observado "18-12-7570482") casa con `f789/qddk.numero_de_constancia`; `numero_de_proceso` es texto libre — no confiar.
- SECOP I interno: `f789.id_adjudicacion` ↔ `7fix-nd37.id_adjudicacion` ↔ `tauh-5jvn.id_adjudicacion`.
- TVEC ↔ SECOP: sin llave dura. Nombre de entidad normalizado o mapeo manual `id_entidad`→NIT.

### Normalización recomendada

1. NIT canónico = 9 dígitos sin DV: quitar puntos/guiones, si quedan 10 dígitos y el último coincide con el DV calculado (algoritmo DIAN, pesos 41,37,29,23,19,17,13,7,3), truncarlo.
2. Castear siempre a texto (jbjy lo publica como number).
3. Tratar `"No Definido"`, `"No Aplica"`, `0`, vacío como NULL.
4. Fechas: descartar < 1990 y > hoy+20 años (el Integrado tiene 2000-01-01 y 2099-12-30 como extremos verificados).

---

## 5. API Socrata (SODA) y estrategia de descarga masiva

Fuente: [dev.socrata.com/docs/app-tokens.html](https://dev.socrata.com/docs/app-tokens.html) y [dev.socrata.com/docs/queries/limit.html](https://dev.socrata.com/docs/queries/limit.html) (consultados 2026-07-02).

- **Endpoints:** `https://www.datos.gov.co/resource/<4x4>.{json|csv}` con SoQL (`$select`, `$where`, `$group`, `$order`, `$limit`, `$offset`). Metadatos: `/api/views/<4x4>.json`. Catálogo: `https://api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&q=...`.
- **App token:** opcional pero muy recomendado. Sin token las requests comparten un pool por IP y reciben `429` al exceder; con token "actualmente no limitamos las requests que usan application token, salvo uso abusivo". Se registra gratis en el perfil de Socrata (datos.gov.co → cuenta) y se pasa por header `X-App-Token` (preferido) o parámetro `$$app_token`.
- **Paginación:** `$limit` por defecto 1.000; máximo 50.000 en API 2.0; **sin máximo en 2.1** (todos estos datasets son 2.1, pero payloads gigantes hacen timeout — en la práctica usar páginas de 50k–200k). Paginar siempre con `$order` sobre una llave estable (`id_contrato`, `uid`, `identificador_de_la_orden`) para evitar duplicados/huecos entre páginas.
- **Export completo:** `https://www.datos.gov.co/api/views/<4x4>/rows.csv?accessType=DOWNLOAD` genera el CSV completo en streaming (10–18 GB para los grandes: preferir para la carga inicial).
- **Incremental (recomendado):** varios datasets traen campo de marca temporal propio (`ultima_actualizacion` en f789 y jbjy; `fecharegistro` en cb9c-h8sn); además Socrata expone el metadato de sistema **`:updated_at`** por fila: `?$where=:updated_at > '2026-07-01T00:00:00'&$order=:id` es el patrón de sincronización diaria más robusto (no depende de la calidad del campo de negocio). Flujo v1: (1) carga inicial vía `rows.csv`; (2) delta diario por `:updated_at`; (3) upsert por llave natural (`id_contrato` / `uid` / `id_del_proceso`).
- **Dumps de CCE:** no existen; CCE delega todo en datos.gov.co (verificado en su página de conjuntos de datos). El equipo de analítica de CCE publica ejemplos de consumo vía sodapy en GitHub: [ANCP-CCE-Analitica/datos_abiertos](https://github.com/ANCP-CCE-Analitica/datos_abiertos/blob/main/SOCRATA_Consulta.ipynb).

---

## 6. Calidad de datos conocida (documentada + verificada)

**Verificado de primera mano (2026-07-02, vía API):**

| Problema | Dataset | Magnitud |
|---|---|---|
| TVEC sin NIT de entidad ni de proveedor (placeholders en el 100 %) | rgxm-mmea | 165.472/165.472 |
| NIT de entidad con >9 dígitos (DV pegado / typo) | jbjy-vk9h | 478.330 |
| Contratos con valor 0 | jbjy-vk9h | 193.827 |
| Procesos con cuantía de contrato 0 | f789-7hwg | 570.017 |
| Contratista "No Definido" | f789-7hwg | 541.635 |
| Documento de proveedor "No Definido" | jbjy-vk9h | 171.589 |
| Fechas imposibles (2000-01-01 … 2099-12-30) | rpmr-utcd | extremos min/max |
| IDs de proceso incompatibles entre procesos y contratos SECOP II (CO1.REQ vs CO1.BDOS) | p6dx-8zbt / jbjy-vk9h | 100 % |
| Log de "adiciones" infla modificaciones (documentos post-firma contados como adición) | cb9c-h8sn | 23,2 M eventos para 5,7 M contratos |

**Documentado por terceros:**

- **OCP Data Registry** (ficha Colombia, [data.open-contracting.org/en/publication/61](https://data.open-contracting.org/en/publication/61)): múltiples proveedores vinculados a un contrato sin distribución de valor; IDs de proveedor genéricos ("1"); campos numéricos con estructuras `{"$numberLong": …}` en el JSON OCDS.
- **OCP, "Examining procurement red flags in Latin America"** ([open-contracting.org, 2019](https://www.open-contracting.org/2019/06/27/examining-procurement-red-flags-in-latin-america-with-data/)): ~50 % de procesos colombianos aparecían con "enmiendas" porque cualquier documento posterior a la firma se contaba como modificación.
- **CCE, Manual M-MUDA-02** ([PDF](https://www.colombiacompra.gov.co/wp-content/uploads/2024/09/manual_de_datos_abiertos_actualizado.pdf)): la calidad es responsabilidad de cada entidad (Ley 1712/2014 art. 3); CCE solo transforma caracteres problemáticos; ante valores atípicos recomienda verificar contra el expediente vía la URL del proceso. SECOP I es plataforma de "simple publicidad" (datos digitados a mano ⇒ más error); SECOP II y TVEC son transaccionales.
- **Transparencia por Colombia, "Generalidades para el uso de SECOP"** ([PDF](https://transparenciacolombia.org.co/Documentos/Publicaciones/cuidado-paz/contratacion/generalidades-uso-secop.pdf)): guía de uso que advierte sobre heterogeneidad de registro entre entidades y la necesidad de filtrar estados de proceso.
- Duplicidad estructural: los contratos de 2015–2026 de entidades que migraron pueden aparecer en SECOP I y II a la vez (convenios, cargas retroactivas); `rpmr-utcd` ayuda a detectar el solape pero no lo resuelve (no trae flag de deduplicación).

---

## 7. OCDS (Open Contracting Data Standard)

- Colombia publicó SECOP I + SECOP II + TVEC en OCDS desde septiembre de 2017, vía la API OCDS de CCE (`colombiacompra.gov.co/transparencia/api`, backend `apiocds.colombiacompra.gov.co`).
- **Estado actual: la publicación OCDS está congelada.** El registro de datos de OCP indica cobertura **enero 2011 → abril 2022** y la marca como "ya no actualizada por el publicador" ([data.open-contracting.org/en/publication/61](https://data.open-contracting.org/en/publication/61)). El endpoint histórico `https://apiocds.colombiacompra.gov.co:8443/apiCCE2.0/rest/releases` **no respondió** al probarlo el 2026-07-02 (timeout/connection failed — verificado). La página institucional [operaciones.colombiacompra.gov.co/transparencia/estandar-ocds](https://operaciones.colombiacompra.gov.co/transparencia/estandar-ocds) sigue describiendo búsqueda, CSV y API pero sin enlaces técnicos funcionales.
- **Dónde conseguir OCDS hoy:** los archivos compilados 2011–2022 (JSONL.gz, xlsx, csv.tar.gz, por año o completos) en el **OCP Data Registry** ([data.open-contracting.org/en/search/](https://data.open-contracting.org/en/search/)), recolectados con Kingfisher. Cifras del registro: 21,3 M parties, 11,5 M planning, 10,6 M awards.
- **Implicación para el proyecto:** para datos vivos, la fuente operativa es Socrata; OCDS solo sirve como histórico normalizado hasta abril 2022 o como esquema destino propio.

---

## 8. Fuentes consultadas (2026-07-02)

**API (verificación directa):**
- Catálogo: `https://api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&q=...`
- Conteos/agregados/muestras: `https://www.datos.gov.co/resource/<4x4>.json?$select=...` para f789-7hwg, qddk-cgux, p6dx-8zbt, jbjy-vk9h, rpmr-utcd, rgxm-mmea, 9sue-ezhx, b6m4-qgqv, 4n4q-k399, it5q-hg94, qmzu-gj57, cb9c-h8sn, 7fix-nd37, tauh-5jvn, s484-c9k3
- Metadatos/esquemas: `https://www.datos.gov.co/api/views/<4x4>.json` (mismos 14 datasets)

**Documentación y estudios:**
- CCE — Manual para el uso de Datos Abiertos del SECOP (M-MUDA-02): https://www.colombiacompra.gov.co/wp-content/uploads/2024/09/manual_de_datos_abiertos_actualizado.pdf
- CCE — Conjuntos de datos abiertos: https://www.colombiacompra.gov.co/transparencia/datos-abiertos/conjuntos-de-datos-abiertos
- CCE — Estándar OCDS: https://operaciones.colombiacompra.gov.co/transparencia/estandar-ocds
- CCE Analítica — repositorio de consumo Socrata: https://github.com/ANCP-CCE-Analitica/datos_abiertos/blob/main/SOCRATA_Consulta.ipynb
- OCP Data Registry — Colombia: https://data.open-contracting.org/en/publication/61 y buscador https://data.open-contracting.org/en/search/
- OCP — Red flags en América Latina: https://www.open-contracting.org/2019/06/27/examining-procurement-red-flags-in-latin-america-with-data/
- OCP — Impact Colombia: https://www.open-contracting.org/impact-stories/impact-colombia/
- Transparencia por Colombia — Generalidades para el uso de SECOP: https://transparenciacolombia.org.co/Documentos/Publicaciones/cuidado-paz/contratacion/generalidades-uso-secop.pdf
- Socrata — App tokens y throttling: https://dev.socrata.com/docs/app-tokens.html
- Socrata — $limit/paginación: https://dev.socrata.com/docs/queries/limit.html
- Socrata — Foundry SECOP II Contratos: https://dev.socrata.com/foundry/www.datos.gov.co/jbjy-vk9h

**Requests fallidos (declarados):** `https://dev.socrata.com/docs/paging.html` (404; se usó `queries/limit.html` en su lugar); `https://apiocds.colombiacompra.gov.co:8443/apiCCE2.0/rest/releases` (sin respuesta — endpoint OCDS caído).
