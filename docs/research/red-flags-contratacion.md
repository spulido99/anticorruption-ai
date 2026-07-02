# Catálogo priorizado de red flags de corrupción computables sobre SECOP

**Fecha de investigación:** 2026-07-02
**Método:** revisión de las cuatro metodologías primarias de referencia (Open Contracting Partnership / cardinal-rs, Fazekas–Tóth–King / Government Transparency Institute / Banco Mundial, IMCO México, Transparencia por Colombia) yendo al documento dueño de cada claim (PDFs de las guías y papers descargados y extraídos íntegros; documentación de cardinal-rs consultada en línea). Cada indicador del catálogo se define computacionalmente **solo sobre los datasets y campos verificados en el informe hermano** [`fuentes-datos-contratacion-colombia.md`](./fuentes-datos-contratacion-colombia.md) (mismo repo, misma fecha); no se usa ningún campo que no esté allí inventariado. Donde una fuente no respondió, se declara en la sección final.

---

## 1. Resumen ejecutivo

La literatura converge en **seis familias** de red flags: (1) **competencia** (single bidding, pocos oferentes, adjudicación pegada al presupuesto), (2) **concentración** (share del ganador en la entidad, HHI), (3) **temporales** (plazos de convocatoria/decisión anómalos, estacionalidad de fin de año/preelectoral, publicación tardía), (4) **modificaciones** (adiciones en valor y tiempo), (5) **proveedor y red** (empresas recién creadas, sancionadas, mismo representante legal, consorcios solapados) y (6) **integridad de datos/transparencia** (campos clave vacíos o placeholder — que en sí mismo es señal de riesgo según OCP e IMCO).

**Qué es computable hoy con SECOP:** todo lo que se calcula sobre el *proceso* o el *contrato* (familias 1–4 y 6) tiene computabilidad alta con `p6dx-8zbt`, `jbjy-vk9h` y `f789-7hwg`/`qddk-cgux`. Lo que requiere datos *a nivel de oferta individual* (precios de cada oferta, exclusiones de oferentes, similitud entre ofertas — el corazón de los indicadores de colusión de OCP/cardinal) **no es computable hoy**: SECOP publica agregados de participación, no las ofertas. La familia 5 es computable a medias (con proxies imperfectos que hay que declarar).

**Top recomendado para la v1 (detalle en §5):** single bidding, proporción de contratación directa por entidad, share entidad–proveedor (winner share), HHI, adiciones en valor, adiciones en tiempo, publicación tardía en SECOP I, ventana publicación→adjudicación anómala, concentración de firmas en diciembre/pre-Ley de Garantías, proveedor recién registrado que gana grande, cruce con sancionados (barato aunque incompleto) e índice de opacidad por entidad (control transversal).

**Advertencia de diseño:** ninguna metodología seria trata un red flag como prueba de corrupción. OCP: los indicadores "no necesariamente demuestran presencia de corrupción; son medidas para señalar riesgos" ([OCP 2024, p.4](https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf)). Fazekas exige *combinar* inputs y outcomes precisamente porque cada indicador aislado tiene error de medición alto. Para un proyecto que puede señalar públicamente a contratistas, la sección de falsos positivos de cada ficha es tan importante como la fórmula.

---

## 2. Revisión por metodología

### 2.1 Open Contracting Partnership (OCP) + cardinal-rs

- **Guía 2016** — *Red Flags for Integrity: Giving the green light to open data solutions* ([PDF](https://www.open-contracting.org/wp-content/uploads/2016/11/OCP2016-Red-flags-for-integrityshared.pdf)): primer mapeo de red flags a OCDS; clasifica los esquemas ilícitos en cuatro: corrupción, bid rigging, colusión y fraude; incluye 6 cálculos trabajados (single bidder, plazo de respuesta corto, oferente nuevo que gana, oferta pegada al presupuesto, ganador único elegible, ofertas separadas por porcentaje exacto).
- **Guía 2024** — *Red flags in public procurement: A guide to using data to detect and mitigate risks* ([página](https://www.open-contracting.org/resources/red-flags-in-public-procurement-a-guide-to-using-data-to-detect-and-mitigate-risks/), [PDF](https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf)): **73 indicadores** con ficha por indicador (definición, fórmula sobre campos OCDS, unidad de análisis, fuente académica). Los agrupa en: *low transparency* (R001, R004, R005, R013, R039, R063), *low competition* (R018, R019, R040, R050, R051), *fraud* (R042–R048, R064–R069, R073), *collusion* (R017, R022–R028, R032–R034, R041, R044, R053, R057, R058, R070–R072) y *bid rigging* (R002, R003, R006–R016, R020, R021, R029–R031, R035–R038, R043, R049, R052, R054–R056, R059–R062). Es la taxonomía de referencia de este catálogo (los códigos R### citados abajo son los suyos).
- **cardinal-rs** — librería open source de OCP que implementa un subconjunto con definición computacional exacta sobre OCDS ([anuncio](https://www.open-contracting.org/2024/06/12/cardinal-an-open-source-library-to-calculate-public-procurement-red-flags/), [docs](https://cardinal.readthedocs.io/en/latest/)): R003 (plazo de presentación corto), R018 (single bid), R024, R025, R028, R030, R035, R036, R038, R048, R058. Ejemplo de precisión: R018 se dispara si `numberOfTenderers == 1` **y** el método es competitivo (`open|selective`, configurable) ([R018](https://cardinal.readthedocs.io/en/latest/cli/indicators/R/018.html)). Nota: de los 11 indicadores de cardinal, 7 requieren datos de ofertas individuales (bids) que SECOP no publica — solo R003 y R018 son trasladables directo.
- **Evidencia contextual Colombia:** OCP documentó en 2019 que ~50 % de los procesos colombianos aparecían con "enmiendas" porque cualquier documento post-firma se contaba como modificación ([Examining procurement red flags in Latin America](https://www.open-contracting.org/2019/06/27/examining-procurement-red-flags-in-latin-america-with-data/)) — coincide con el hallazgo verificado del log `cb9c-h8sn` (23,2 M "adiciones" para 5,7 M contratos).

### 2.2 Fazekas–Tóth–King / GTI / Banco Mundial

*An Objective Corruption Risk Index Using Public Procurement Data* (Fazekas, Tóth & King, European Journal on Criminal Policy and Research 22(3), 2016; [repositorio Cambridge](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0), PDF extraído íntegro). Es la metodología con validación empírica más fuerte:

- **Tres outcomes de corrupción** (proxies del resultado corrupto): (a) **single bidding** (1 oferta recibida), (b) **exclusión de todas las ofertas menos una** (single *valid* bid), (c) **winner's contract share**: valor ganado por el proveedor en la entidad / valor total adjudicado por la entidad en los 12 meses previos.
- **Inputs (técnicas):** solo retienen los que predicen los outcomes en regresión: no publicación del llamado en gaceta oficial, tipo de procedimiento (no abierto), longitud relativa de los criterios de elegibilidad, **plazo de presentación corto** (los umbrales exactos dependen del tipo de procedimiento y los mínimos legales de cada año), precio relativo de los pliegos, modificación del llamado, peso de criterios de evaluación no-precio (relación en U invertida: riesgo alto entre 0,4 y <1), procedimiento anulado y relanzado, **longitud del periodo de decisión** (relación en U: riesgo alto si ≤32 días hábiles o >182; referencia de bajo riesgo 44–182), modificación del contrato, extensión de plazo y aumento de valor del contrato.
- **Agregación:** el CRI es una suma ponderada de flags normalizada a [0,1]; los pesos por categoría salen de los coeficientes de regresión (categoría más impactante = 1, las demás proporcionales), y "3–4 inputs/outputs simultáneos (CRI 0,27–0,36) es casi con certeza muy corrupto" según sus entrevistados. Validación: consistencia entre los tres outcomes, controles por mercado (CPV), año, tamaño; réplica cross-country en [*Uncovering High-Level Corruption* (BJPS)](https://www.cambridge.org/core/journals/british-journal-of-political-science/article/abs/uncovering-highlevel-corruption-crossnational-objective-corruption-risk-indicators-using-public-procurement-data/8A1742693965AA92BE4D2BA53EADFDF0).
- **Detalle clave para Colombia:** la dirección de los indicadores de modificación **se invierte según el outcome** — si hubo competencia real, la renta se extrae *después* vía adiciones (correlación positiva de modificaciones con winner share, negativa con single bidding). Las adiciones son señal sobre todo en contratos que *sí* fueron competidos.
- **Banco Mundial — ProACT:** plataforma conjunta con GTI que publica indicadores de competencia, transparencia e integridad (los de Fazekas) para 46 países ([blog del Banco Mundial](https://blogs.worldbank.org/en/governance/new-global-anticorruption-and-transparency-platform-proact-empowers-stakeholders-use), [GTI](https://www.govtransparency.eu/proact-procurement-anticorruption-and-transparency-platform/)); metodología heredada de [opentender.eu / DIGIWHIST](https://opentender.eu/). Confirma que el núcleo Fazekas (single bidding, procedure type, plazos, concentración) es el estándar de facto multi-país.

### 2.3 IMCO (México) — Índice de Riesgos de Corrupción

[IRC 2024](https://imco.org.mx/indice-de-riesgos-de-corrupcion/) ([reporte PDF](https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf), extraído íntegro; código en [github.com/imco/IRC](https://github.com/imco/IRC)). Score 0–100 **por institución** federal sobre CompraNet. Tras la reforma de CompraNet pasó de 3 ejes / 27 indicadores a **2 ejes / 11 indicadores**:

- **Riesgos de cumplimiento:** contratación con empresas sancionadas (cruce con el directorio de sancionados de la Función Pública), contratación con **empresas de reciente creación** (constituidas en los 12 meses previos al inicio del contrato), adjudicaciones directas que rebasaron el máximo permitido, monto justificado bajo los artículos de excepción, **contratos publicados después de la fecha de inicio**, adjudicaciones sin fundamento legal.
- **Riesgos operacionales y de mercado:** % de procedimientos por adjudicación directa/invitación restringida, monto por esas vías, **Índice Herfindahl-Hirschman**, importe promedio por procedimiento, % de licitaciones con plazos por debajo del mínimo legal.
- Lección directa para SECOP: IMCO perdió el eje de competencia (número de participantes) cuando CompraNet dejó de publicarlo — en Colombia ese dato existe (`p6dx-8zbt`) y hay que explotarlo mientras exista. También agrega a nivel *entidad*, no contrato: útil para rankings públicos menos litigiosos que señalar contratistas individuales.

### 2.4 Transparencia por Colombia (TxC)

- **Así se mueve la corrupción** (Monitor Ciudadano, [radiografía 2016–2020](https://transparenciacolombia.org.co/asi-se-mueve-la-corrupcion-radiografia-de-los-hechos-de-corrupcion-en-colombia-2016-2020/), [PDF 2016–2021](https://transparenciacolombia.org.co/wp-content/uploads/radiografia-2016-2021-02-11-21.pdf)): la contratación pública es el campo con más irregularidades registradas en prensa (177 casos, 42 % de la corrupción administrativa), con patrones de "direccionamiento de contratos con requisitos habilitantes muy específicos y pago del bien o servicio pese a no estar completo".
- **Contratación COVID** ([recomendaciones](https://transparenciacolombia.org.co/recomendaciones-para-evitar-riesgos-de-corrupcion-en-la-contratacion-publica-y-facilitar-ejercicios-ciudadanos/)): sobre ~20.000 contratos alertó **contratistas sin idoneidad** (sin experiencia previa en contratación pública y/o sin RUP), **cargue tardío al SECOP** ("días o incluso meses después de firmados") e inconsistencia de información entre SECOP I, II y TVEC.
- **Elecciones y Contratos** ([monitorciudadano.co](https://www.monitorciudadano.co/elecciones-contratos/)): cruza Cuentas Claras (financiadores de campañas) con SECOP I/II para detectar **financiadores que reciben contratos tras la posesión del elegido**, financiadores anónimos/prohibidos y contratistas en SISBEN que financian campañas. Define la dimensión de riesgo específicamente colombiana: el ciclo político-electoral (Ley de Garantías) y el vínculo financiador–contratista. El cruce con Cuentas Claras queda fuera del alcance de este catálogo (fuente externa a SECOP) pero es la extensión natural.

---

## 3. Qué NO es computable hoy con SECOP (hallazgo)

Indicadores centrales de la literatura que **no** tienen datos en los datasets inventariados:

| Indicador (fuente) | Por qué no |
|---|---|
| Precios de ofertas individuales: oferta pegada a la ganadora (R024), ofertas idénticas (R028), disparidad de precios (R022), múltiplos fijos (R023), Benford sobre ofertas (R029), descuento extremo (R058) | SECOP publica agregados de participación (`respuestas_al_procedimiento`), no el detalle de cada oferta con su valor. `tauh-5jvn`/`hgi6-6wh3` listan proponentes pero sin precio ofertado. |
| Exclusión de oferentes: single *valid* bid de Fazekas, R035/R036/R038 de cardinal | No hay campo de ofertas descalificadas ni causal de rechazo. |
| Peso de criterios de evaluación no-precio (Fazekas), pliegos/criterios de elegibilidad inusuales (R006/R007) | Los pliegos son PDFs adjuntos (índices `ps88-5e3v` etc.), no datos estructurados. Computable solo con NLP sobre documentos — fase posterior. |
| Beneficial ownership real (R032/R033) | No existe registro abierto de beneficiarios finales en Colombia; el proxy disponible es el representante legal (ficha RF-15). |
| Subcontratación (R070–R072) | SECOP no publica subcontratos. |
| Modificación del llamado / anulación y relanzamiento (Fazekas) | `e2u2-swiw` (modificaciones a procesos) existe en el catálogo pero sin esquema verificado; el estado "anulado y relanzado" exigiría reconstruir cadenas de procesos por objeto — investigación aparte. |
| Fechas exactas por fase (submission period fino) | `p6dx-8zbt` trae "fechas por fase" pero su esquema detallado no quedó verificado campo a campo en el informe de fuentes; hasta verificarlo, el plazo fino de presentación queda en computabilidad media (ver RF-07). |

Esto es una conclusión de diseño: **la v1 debe ser fuerte en proceso/contrato/entidad y no prometer detección de colusión entre oferentes**, que es donde la evidencia internacional usa datos que Colombia no publica.

---

## 4. Catálogo priorizado

Convenciones de todas las fichas:

- **Normalización previa obligatoria** (del informe de fuentes §4): NIT canónico a 9 dígitos sin DV; castear a texto; tratar `"No Definido"`, `"No Aplica"`, `0`, vacío como NULL; descartar fechas <1990 o >hoy+20 años; para "contratos reales" en SECOP I filtrar `estado_del_proceso` ∈ {Celebrado, Liquidado, Terminado sin liquidar}; puente SECOP II procesos↔contratos por `noticeUID=CO1.NTC.*` extraído con regex de `urlproceso` (los IDs directos son incompatibles: `CO1.REQ.*` vs `CO1.BDOS.*`).
- **Computabilidad**: alta = campos verificados y poblados; media = requiere cruces frágiles o campos con nulls masivos; baja = cobertura o calidad insuficiente.
- Umbral "literatura" = tomado de la fuente citada; "a calibrar" = propuesta propia que debe calibrarse contra la distribución colombiana (percentiles/IQR, como recomienda OCP 2024 para R040/R060–R062).

---

### RF-01 — Single bidding en proceso competitivo · familia: competencia

- **Concepto:** una sola respuesta en un procedimiento competitivo es la señal más validada de competencia suprimida; es outcome del CRI de Fazekas ([paper](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0)) e indicador R018 de OCP/cardinal ([definición exacta](https://cardinal.readthedocs.io/en/latest/cli/indicators/R/018.html)).
- **Cómputo:** `p6dx-8zbt`, nivel proceso. Flag si `modalidad_de_contratacion` ∈ {licitación pública, selección abreviada, subasta, concurso de méritos, mínima cuantía} **y** `adjudicado='Si'` **y** (`proveedores_unicos_con` = 1 **o** `respuestas_al_procedimiento` = 1). Agregable a entidad: `share_single_bidding = flagged / procesos_competitivos_adjudicados`.
- **Umbral:** binario a nivel proceso (literatura). A nivel entidad, reportar el share y marcar outliers > Q3+1,5·IQR (convención OCP R013/R040).
- **Computabilidad: alta** (campos de competencia exclusivos y verificados de p6dx). Cuidado: solo 854.118 procesos con `adjudicado='Si'` — el denominador correcto son procesos competitivos adjudicados, no todos.
- **Falsos positivos:** mercados genuinamente monopólicos o territorios sin oferta (Fazekas lo acota: <5 % de los mercados tienen ≤3 empresas, pero en municipios pequeños colombianos puede ser más); procesos multi-lote (p6dx trae una fila por proceso, no por lote — un proceso con 10 lotes y 1 oferente por lote no se distingue). Mitigación: condicionar por categoría UNSPSC (`codigo_principal_de_categoria`) y departamento.

### RF-02 — Proporción de contratación directa por entidad · familia: competencia

- **Concepto:** el abuso de procedimientos no competitivos es input del CRI (procedure type, [Fazekas](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0)), red flag R013 de [OCP 2024](https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf) y dos de los once indicadores del [IRC de IMCO](https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf) (% de procedimientos y monto por adjudicación directa/invitación restringida).
- **Cómputo:** `jbjy-vk9h` (+ `f789-7hwg` para SECOP I), nivel entidad×año. `pct_directa_n = count(modalidad_de_contratacion='Contratación directa') / count(*)` y `pct_directa_valor = sum(valor_del_contrato | directa) / sum(valor_del_contrato)`. Excluir del numerador la prestación de servicios profesionales si se quiere la variante estricta (es directa por diseño legal y domina el conteo) — reportar ambas variantes. `justificacion_modalidad_de` permite desagregar causales.
- **Umbral:** a calibrar por percentiles dentro de grupos comparables (mismo `orden`/`sector`, tamaño de gasto similar — IMCO compara dentro de 4 categorías de gasto). OCP sugiere outlier > Q3+1,5·IQR si no hay umbral normativo.
- **Computabilidad: alta.**
- **Falsos positivos:** entidades cuya misión implica directa masiva (convenios interadministrativos — cruzar con `s484-c9k3`; entidades de régimen especial que no licitan por Ley 80). El conteo simple sobre-pondera los miles de contratos de prestación de servicios de bajo valor: la métrica en valor es la robusta.

### RF-03 — Valor adjudicado pegado al precio base · familia: competencia

- **Concepto:** oferta ganadora ≈ presupuesto oficial sugiere filtración del presupuesto o ausencia de presión competitiva (OCP R031 "Winning bid price very close or higher than estimated price"; ya en la guía OCP 2016 como Flag 4).
- **Cómputo:** `p6dx-8zbt`, nivel proceso: `ratio = valor_total_adjudicacion / precio_base`; flag si 0,98 ≤ ratio ≤ 1,00 (o > 1) en modalidad competitiva.
- **Umbral:** 98 % a calibrar (la literatura no fija uno universal; calibrar contra la distribución del ratio por modalidad y UNSPSC).
- **Computabilidad: media.** `precio_base` viene con 0/NULL masivos (mismo patrón que los "valores 0" verificados en el informe de fuentes); en subasta inversa el ratio pegado a 1 no es informativo.
- **Falsos positivos:** presupuestos calculados con precios de mercado muy ajustados (acuerdos marco, tarifas reguladas); subastas donde el precio techo es vinculante.

### RF-04 — Competencia estructuralmente baja por mercado · familia: competencia

- **Concepto:** número de oferentes anómalamente bajo para su categoría de producto/servicio (OCP R019 "Low number of bidders for item category"; Fazekas usa el nº de ganadores por mercado como control).
- **Cómputo:** `p6dx-8zbt`: mediana de `respuestas_al_procedimiento` por `codigo_principal_de_categoria` × departamento; flag a procesos con respuestas < P25 de su mercado; flag a mercados-territorio cuya mediana ≤ 2.
- **Umbral:** a calibrar (P25 propuesto).
- **Computabilidad: alta** (mismos campos que RF-01).
- **Falsos positivos:** categorías UNSPSC mal asignadas por las entidades (frecuente); mercados pequeños reales. Es más útil como *contexto* de RF-01 que como flag autónomo.

### RF-05 — Concentración entidad–proveedor (winner share) · familia: concentración

- **Concepto:** el objetivo de la corrupción institucionalizada es adjudicar recurrentemente al mismo proveedor: winner's contract share es outcome del CRI ([Fazekas](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0)) y OCP R040 ("High share of buyer's contracts", con fórmula S = Σ valor adjudicado al proveedor k por la entidad b en t / Σ valor adjudicado por b en t).
- **Cómputo:** `jbjy-vk9h` (+ `f789-7hwg`/`qddk-cgux` para serie larga), nivel par entidad–proveedor con ventana móvil de 12 meses: `share(k,b,t) = sum(valor_del_contrato | documento_proveedor=k, nit_entidad=b, firma en [t-12m, t]) / sum(valor_del_contrato | nit_entidad=b, misma ventana)`. Requiere NIT canónico en ambos lados.
- **Umbral:** OCP sugiere ejemplo 40 % o outlier > Q3+1,5·IQR sobre la distribución de shares. Condicionar a un mínimo de contratos/valor de la entidad en la ventana (p.ej. ≥ 20 contratos) para no flaggear entidades diminutas.
- **Computabilidad: alta**, con dos taras declaradas: 478.330 filas de jbjy con NIT de entidad >9 dígitos (normalizar DV) y 171.589 con `documento_proveedor='No Definido'` (excluir del numerador, contar en RF-19); consorcios/UT tienen NIT efímero — desagregar miembros vía `ceth-n4bn` antes de computar, o el share del grupo económico queda subestimado.
- **Falsos positivos:** proveedores de servicios esenciales únicos (interventoría continua, software propietario, EPS/operadores); cambio de gobierno que rota legítimamente proveedores (Fazekas lo documenta como sesgo). Reportar siempre junto con la modalidad: share alto ganado en licitaciones abiertas competidas es distinto de share alto por directa.

### RF-06 — HHI de proveedores por entidad · familia: concentración

- **Concepto:** concentración global del gasto de la entidad en pocos proveedores; indicador del eje operacional del [IRC de IMCO](https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf) y OCP R051 ("High market concentration").
- **Cómputo:** `jbjy-vk9h` + `f789-7hwg`, nivel entidad×año: `HHI(b,año) = Σ_k (share_k)²` con share_k = valor contratado con el proveedor k / valor total contratado por b en el año (proveedores desagregados de consorcios vía `ceth-n4bn`). Variante mercado: HHI por `codigo_principal_de_categoria` × departamento para detectar mercados capturados (OCP R050).
- **Umbral:** convención antitrust HHI > 0,25 = altamente concentrado (a calibrar: entidades pequeñas tendrán HHI alto por pocas compras — exigir n mínimo de proveedores/contratos).
- **Computabilidad: alta.**
- **Falsos positivos:** entidades con un solo gran proyecto anual (una obra concentra el gasto legítimamente); HHI es sensible al horizonte temporal — computar sobre 2–3 años móviles además del año.

### RF-07 — Ventana publicación→adjudicación anómala · familia: temporal

- **Concepto:** Fazekas encontró relación en U: periodos de decisión muy cortos (decisión precocinada) o muy largos (litigios/manipulación) predicen single bidding y winner share; su referencia de bajo riesgo es 44–182 días hábiles, con riesgo alto ≤32 y >182 ([paper, Tabla 5](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0)). OCP lo divide en R061/R062 (decision period) y R003/R014 (submission period, implementado en [cardinal R003](https://cardinal.readthedocs.io/en/latest/)).
- **Cómputo (v1, computable hoy):** `p6dx-8zbt`, nivel proceso: `dias = fecha_adjudicacion - fecha_de_publicacion_del`; flag por modalidad si `dias` < P5 o > P95 de la distribución de su modalidad×año. Esta ventana mezcla submission+decision period; la versión fina (solo plazo de presentación de ofertas, contra los mínimos legales del Decreto 1082/2015) requiere verificar los campos de fechas por fase de p6dx, aún no inventariados campo a campo → declarado en §3.
- **Umbral:** percentiles propios (los días exactos de Fazekas son de la ley húngara; los mínimos legales colombianos por modalidad deben tabularse aparte).
- **Computabilidad: alta** para la ventana gruesa; **media** para el plazo fino.
- **Falsos positivos:** procesos suspendidos por causas legítimas (observaciones a pliegos, mesas técnicas) alargan la ventana; adendas que reinician plazos. Un flag temporal aislado vale poco: usarlo como componente de score, no como alerta autónoma.

### RF-08 — Estacionalidad: firmas de diciembre y pico pre-Ley de Garantías · familia: temporal

- **Concepto:** riesgo específicamente colombiano con dos ventanas: (a) la carrera de ejecución presupuestal de fin de vigencia (contratos apurados con planeación pobre), (b) el pico de contratación directa justo antes de que la **Ley 996 de 2005 (Ley de Garantías)** la restrinja en los 4 meses previos a elecciones — el ciclo político-contractual que TxC monitorea en [Elecciones y Contratos](https://www.monitorciudadano.co/elecciones-contratos/). En la taxonomía OCP cae bajo manipulación temporal/planeación deficiente (R012); no tiene código propio — es contextual.
- **Cómputo:** `jbjy-vk9h` + `f789-7hwg`, nivel entidad×año: `pct_diciembre = valor firmado en diciembre / valor anual` (por `fecha_de_firma`); y para años preelectorales, valor firmado por directa en los 2 meses previos al inicio de la restricción vs promedio mensual del año. Flag entidad si > P90 de su grupo comparable.
- **Umbral:** a calibrar (P90 propuesto).
- **Computabilidad: alta.**
- **Falsos positivos:** ciclos presupuestales legítimos (vigencias futuras aprobadas tarde, giros de la Nación en Q4); entidades educativas con calendario propio. El pico preelectoral es *conducta legal* (anticiparse a una prohibición) — señal de riesgo de planeación/clientelismo, no ilegalidad; comunicarlo así.

### RF-09 — Publicación tardía en SECOP · familia: temporal / integridad

- **Concepto:** cargar el contrato mucho después de firmado burla el control ciudadano oportuno; es indicador del IRC de IMCO ("contratos publicados después de la fecha de inicio", [reporte 2024](https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf)) y hallazgo explícito de TxC en COVID ("algunas entidades cargaban contratos… días o incluso meses después de firmados", [recomendaciones](https://transparenciacolombia.org.co/recomendaciones-para-evitar-riesgos-de-corrupcion-en-la-contratacion-publica-y-facilitar-ejercicios-ciudadanos/)). El Decreto 1082/2015 ordena publicar dentro de los 3 días siguientes.
- **Cómputo:** `f789-7hwg`/`qddk-cgux` (SECOP I), nivel contrato y agregado entidad: `dias_tarde = fecha_de_cargue_en_el_secop - fecha_de_firma_del_contrato`; flag si > 3 días hábiles; métrica de entidad = mediana y % de contratos tardíos.
- **Umbral:** 3 días (normativo).
- **Computabilidad: alta en SECOP I** (donde además es donde importa: es plataforma de simple publicidad con digitación manual). **Baja/no aplica en SECOP II**: el contrato nace en la plataforma, la fecha de cargue no existe como campo separado; el equivalente sería retraso en pasar de estado, no inventariado.
- **Falsos positivos:** migraciones y cargas retroactivas masivas (convenios de depuración de datos); errores de digitación de `fecha_de_firma` en SECOP I. Winsorizar valores absurdos (>2 años).

### RF-10 — Adiciones en valor · familia: modificaciones

- **Concepto:** aumentos del valor tras la firma como vía de extracción de renta pactada ("contract value increase" en el [CRI de Fazekas](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0); OCP R064/R069). En Colombia el tope legal es el **50 % del valor inicial en SMMLV (Ley 80 de 1993, art. 40, parágrafo)** — acercarse sistemáticamente al tope es la señal.
- **Cómputo:** SECOP I (directo): `f789-7hwg`, nivel contrato: `pct_adicion = valor_total_de_adiciones / cuantia_contrato` (con cuantia_contrato > 0); flags escalonados: >20 % (suave), >45 % (fuerte, pegado al tope), >50 % (presunta irregularidad — verificar contra expediente antes de publicar). SECOP II: **no usar `cb9c-h8sn`** para valores (log de eventos inflado, verificado: 23,2 M eventos; y OCP documentó el mismo artefacto en 2019) — usar `u8cx-r425` (Modificaciones a contratos, esquema por verificar) o reconstruir contra `valor_del_contrato` histórico vía `ultima_actualizacion`. Nivel agregado: % del valor adicionado por entidad y por proveedor.
- **Umbral:** 50 % normativo; escalones intermedios a calibrar.
- **Computabilidad: alta en SECOP I, media en SECOP II** (el dataset fino de modificaciones con valores no quedó verificado en el informe de fuentes).
- **Falsos positivos:** masivos si no se filtra — adiciones legítimas por diseño (interventorías atadas a la obra, emergencias declaradas); en SECOP II el propio valor inicial puede venir en 0 (193.827 contratos con valor 0). Recordar el hallazgo de Fazekas: la adición es más señal en contratos que fueron *competidos* — cruzar con RF-01/RF-02 al puntuar.

### RF-11 — Adiciones en tiempo · familia: modificaciones

- **Concepto:** prórrogas como mecanismo gemelo de la adición en valor ("contract lengthening", [Fazekas](https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0); OCP R064).
- **Cómputo:** SECOP I: `f789-7hwg.tiempo_adiciones_en_dias` (+`_meses`) relativo al plazo original (`fecha_fin_ejec_contrato - fecha_ini_ejec_contrato`): `pct_prorroga = dias_adicionados / plazo_original`. SECOP II: `jbjy-vk9h.dias_adicionados` contra `fecha_de_fin_del_contrato - fecha_de_inicio_del_contrato`. Detalle por evento en `7fix-nd37` (`adicion_en_dias/meses`, cruza por `id_adjudicacion`).
- **Umbral:** Fazekas encontró señal en extensiones de 0–16,2 %; proponer flag > 50 % del plazo original y > percentil 90 del tipo de contrato, a calibrar.
- **Computabilidad: alta** (ambas plataformas tienen el campo agregado).
- **Falsos positivos:** suspensiones por fuerza mayor (invierno, orden público — reales en Colombia), prórrogas de convenios de funcionamiento continuo. Distinguir prórroga (más plazo) de suspensión (`u99c-7mfm`) cuando ese dataset se verifique.

### RF-12 — Brecha adjudicación → contrato final · familia: modificaciones

- **Concepto:** diferencia grande entre el valor adjudicado y el valor final del contrato firmado (OCP R059 "Large difference between the award value and final contract amount"; R060 mide el tiempo award→firma).
- **Cómputo:** puente `p6dx-8zbt` ↔ `jbjy-vk9h` por `noticeUID` (regex sobre `urlproceso` de ambos): `gap_valor = (valor_del_contrato - valor_total_adjudicacion) / valor_total_adjudicacion`; `gap_dias = fecha_de_firma - fecha_adjudicacion`. Flag si |gap_valor| > 10 % o gap_dias > P95 de la modalidad.
- **Umbral:** a calibrar.
- **Computabilidad: media** — depende de la tasa de éxito del join por noticeUID (verificado en muestras, no censado) y de que solo 854 K procesos tienen `adjudicado='Si'`.
- **Falsos positivos:** procesos multi-lote (la adjudicación total no es comparable al contrato individual); contratos en otras monedas.

### RF-13 — Proveedor recién registrado que gana grande · familia: proveedor/red

- **Concepto:** empresas creadas ad hoc para capturar contratos; indicador de cumplimiento del [IRC de IMCO](https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf) (constituidas <12 meses antes del contrato) y alerta empírica de TxC en COVID (contratistas sin experiencia ni RUP). Emparenta con OCP Flag 3 de la guía 2016 ("bidder that has never bid previously wins tender") y R052 (compra inicial pequeña seguida de compras mucho mayores).
- **Cómputo:** `qmzu-gj57` × `jbjy-vk9h`, nivel contrato/proveedor: resolver `codigo_proveedor` → `qmzu-gj57.codigo`, flag si `fecha_de_firma - qmzu.fecha_creacion < 365 días` **y** `valor_del_contrato` > P90 de su UNSPSC×departamento. Variante conducta: primer contrato del proveedor en SECOP (min histórica de fecha de firma sobre jbjy+f789+qddk por NIT) reciente + valor alto.
- **Umbral:** 12 meses (IMCO) + P90 de valor (a calibrar).
- **Computabilidad: media, con caveat crítico:** `qmzu-gj57.fecha_creacion` es la fecha de **registro del proveedor en SECOP II, no de constitución de la empresa**. Empresas antiguas que se registran al migrar a SECOP II parecen "nuevas". La fecha de constitución real está en RUES/Confecámaras (fuente externa, no en este inventario). La variante "primer contrato histórico en SECOP" mitiga parcialmente usando las tres bases.
- **Falsos positivos:** los del caveat (dominantes en 2020–2022, años de migración masiva a SECOP II); spin-offs y uniones temporales nuevas de empresas viejas; personas naturales (cédulas) recién registradas para prestación de servicios — excluir persona natural de esta ficha. **No publicar señalamientos individuales con este flag sin verificar la fecha de constitución real.**

### RF-14 — Contratación con proveedores sancionados/multados · familia: proveedor/red

- **Concepto:** contratar con quien ya fue sancionado señala falta de debida diligencia; indicador del IRC de IMCO (cruce con el directorio de sancionados de la SFP — 2.506 MDP detectados en 2023) y OCP R046 ("Bidder is debarred or on sanctions list").
- **Cómputo:** `4n4q-k399` (SECOP I: `documento_contratista`, `fecha_de_firmeza`) + `it5q-hg94` (SECOP II: proveedor por código interno → resolver contra `qmzu-gj57`), cruzados con `jbjy-vk9h`/`f789-7hwg`: flag a contratos con `fecha_de_firma > fecha_de_firmeza` de una sanción del mismo NIT. Ampliar con los datasets externos ya identificados: SIRI Procuraduría (`iaeu-rcn6`) y Responsabilidad Fiscal Contraloría (`jr8e-e8tu`).
- **Umbral:** binario (normativo cuando la sanción es inhabilidad vigente; reputacional si ya venció).
- **Computabilidad: media-baja por cobertura, no por técnica:** el cruce es trivial pero los datasets SECOP de multas tienen 1.705 + 538 filas — cobertura ínfima verificada. Con SIRI/Contraloría sube a media. La ausencia de flag **no** significa proveedor limpio; decirlo siempre.
- **Falsos positivos:** homónimos por NIT mal digitado; sanciones apeladas o revocadas (el dataset SECOP II trae `estado` — filtrar); inhabilidades ya cumplidas presentadas como vigentes.

### RF-15 — Mismo representante legal en múltiples proveedores · familia: proveedor/red

- **Concepto:** proxy colombiano del beneficial ownership compartido (OCP R032/R033 "bidders share same beneficial owner/major shareholder"); si además esos proveedores compiten entre sí en los mismos procesos, es señal de colusión simulando competencia.
- **Cómputo:** (a) Red estática: `qmzu-gj57` agrupado por documento del representante legal → clusters de proveedores con el mismo rep. legal; enriquecer con teléfono/correo compartido (mismos campos). También `jbjy-vk9h` y `f789-7hwg` traen rep. legal por contrato (`identific_representante_legal` en SECOP I). (b) Conducta: cruzar clusters con `tauh-5jvn`/`hgi6-6wh3` (proponentes por proceso): flag a procesos donde ≥2 proponentes pertenecen al mismo cluster. (c) Ganadores del mismo cluster alternándose en una entidad (aprox. de OCP R057 bid rotation).
- **Umbral:** binario para (b); para (a) reportar como red, no como flag.
- **Computabilidad: media.** Los campos existen y están poblados, pero: documentos de identidad con calidad heterogénea, homónimos si solo hay nombre, representantes legales profesionales (abogados que figuran en decenas de empresas legítimamente). La variante (b) exige que `hgi6-6wh3` (proponentes SECOP II) se verifique en detalle — solo `tauh-5jvn` (SECOP I, 119.942 filas) está conteado.
- **Falsos positivos:** grupos empresariales declarados (legal); gestores/apoderados profesionales; familiares con negocios independientes. Este flag **jamás** debe publicarse automatizado: es generador de hipótesis para investigación humana.

### RF-16 — Consorcios/UT con miembros solapados o NIT efímero recurrente · familia: proveedor/red

- **Concepto:** alta prevalencia de consorcios y miembros que rotan entre consorcios competidores es riesgo de colusión (OCP R026 "Prevalence of consortia").
- **Cómputo:** `ceth-n4bn` (grupos de proveedores) + `jbjy-vk9h` (`es_grupo='Si'`): tasa de contratos a grupos por entidad; solapamiento de miembros entre grupos que compiten (vía proponentes) o que se reparten una entidad.
- **Umbral:** a calibrar (no hay umbral en la literatura).
- **Computabilidad: media** — `ceth-n4bn` está identificado pero su esquema no fue verificado en detalle en el informe de fuentes.
- **Falsos positivos:** consorcios son la forma normal de contratar obra grande en Colombia; el solapamiento parcial de miembros en mercados especializados (p.ej. interventoría) es común y legal.

### RF-17 — Fraccionamiento bajo umbrales de cuantía · familia: fraccionamiento/planeación

- **Concepto:** partir compras para quedar bajo el umbral que permite un procedimiento menos competitivo — bunching bajo el umbral. OCP R011 ("Splitting purchases to avoid procurement thresholds"), R002 (manipulación de umbrales), R049/R055 (múltiples adjudicaciones directas al mismo proveedor justo bajo el umbral); IMCO mide la variante mexicana (adjudicaciones que rebasaron el máximo del art. 42 LAASSP). En Colombia los umbrales relevantes son la **menor cuantía** (escalonada por presupuesto de la entidad en SMMLV, Ley 1150 de 2007, art. 2) y la **mínima cuantía** (10 % de la menor cuantía, Ley 1474 de 2011) — verificar el texto legal vigente al implementar.
- **Cómputo:** dos variantes sobre `jbjy-vk9h`/`f789-7hwg`, nivel entidad y par entidad–proveedor: (a) *bunching*: histograma de `valor_del_contrato/SMMLV(año)` para contratos de mínima cuantía y directa; flag a entidades con exceso de masa en (0,9·umbral, umbral] contra la densidad esperada (McCrary-style, y ver las fuentes de OCP R002: [*Bunching Below Thresholds to Manipulate Public Procurement*](https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf)); (b) *fraccionamiento directo*: ≥N contratos de la misma entidad al mismo proveedor (o misma familia UNSPSC) en ≤90 días cuya **suma** supera el umbral que cada uno individualmente respeta.
- **Umbral:** el legal por entidad-año. **Problema:** el umbral depende del presupuesto anual de la entidad en SMMLV, que **no está en SECOP** — hay que estimarlo (inferirlo del propio patrón de modalidades usadas) o traer tabla externa de presupuestos. Declararlo en la implementación.
- **Computabilidad: media** (la variante (b) es alta si se fija un solo umbral conservador, p.ej. el de la mínima cuantía más común).
- **Falsos positivos:** compras recurrentes legítimas de bajo valor (papelería mensual); precios de mercado que naturalmente caen cerca del umbral. La variante (b) con mismo proveedor y ventana corta es mucho más específica que el bunching agregado.

### RF-18 — Contratación por fuera del Plan Anual de Adquisiciones · familia: planeación

- **Concepto:** compras no planeadas o adjudicaciones directas que contradicen el plan (OCP R012 "Direct awards in contravention to the provisions of the procurement plan", R001 sobre documentos de planeación).
- **Cómputo:** `9sue-ezhx` (PAA detalle, quedándose con la última `version_del_paa` por entidad-año) vs procesos/contratos del año: % del valor contratado sin línea de PAA correspondiente (match por `procesos_relacionados` cuando existe; si no, por entidad + UNSPSC + rango de valor); y ratio `valor ejecutado / valor_total_esperado` por entidad (desviaciones extremas en ambas direcciones).
- **Umbral:** a calibrar.
- **Computabilidad: media-baja:** el PAA es versionado (11,4 M filas infladas por versión), el vínculo `procesos_relacionados` no está censado, el matching por UNSPSC es difuso, y las entidades re-planifican legalmente durante el año (el PAA no es vinculante).
- **Falsos positivos:** emergencias legítimas; entidades que actualizan el PAA correctamente antes de contratar (eso es cumplimiento, no riesgo) — el flag solo tiene sentido contra la *última* versión del PAA.

### RF-19 — Índice de opacidad por entidad · familia: integridad de datos

- **Concepto:** los vacíos de información son en sí un red flag de baja transparencia (OCP R005 "Key tender information and documents are not available", R063 "Contract is not published"; IMCO abandonó su eje de transparencia solo cuando la plataforma forzó la publicación). Además es el control de calidad que el resto del catálogo necesita: un flag calculado sobre datos podridos no es evidencia.
- **Cómputo:** `jbjy-vk9h` + `f789-7hwg` + `p6dx-8zbt`, nivel entidad×año: % de registros con `documento_proveedor`/`identificacion_del_contratista` = 'No Definido', `valor_del_contrato`/`cuantia_contrato` = 0, `nit_entidad` malformado (>9 dígitos), fechas imposibles, `nit_del_proveedor_adjudicado='No Definido'` en procesos adjudicados. Score compuesto simple (promedio de tasas).
- **Umbral:** reporte de ranking, no flag binario.
- **Computabilidad: alta** — las magnitudes globales ya están verificadas (541.635 contratistas 'No Definido' en f789; 193.827 valores 0 y 171.589 proveedores 'No Definido' en jbjy).
- **Falsos positivos / uso correcto:** parte de los 'No Definido' de f789 son procesos no adjudicados (legítimo) — computar sobre estados Celebrado/Liquidado. Este índice **modula** los demás: entidades con opacidad alta no deben aparecer como "limpias" en los rankings de RF-01..RF-18 sino como "no evaluables".

---

## 5. Priorización final para la v1

Criterio: computabilidad hoy × evidencia de validez en la literatura × relevancia para el contexto colombiano. Doce indicadores en tres tandas:

**Tanda 1 — núcleo con máxima evidencia y computabilidad (implementar primero):**

| # | Indicador | Por qué primero |
|---|---|---|
| RF-01 | Single bidding | El proxy más validado de la literatura (outcome del CRI, R018 de cardinal con definición ejecutable); campos exclusivos de p6dx verificados. |
| RF-02 | % contratación directa por entidad | Tres metodologías lo usan (Fazekas, OCP R013, IMCO ×2); trivial de computar; el debate público colombiano ya gira sobre él. |
| RF-05 | Winner share entidad–proveedor 12m | Outcome del CRI; detecta la captura recurrente que es el objetivo final de la corrupción institucionalizada. |
| RF-06 | HHI por entidad | Complemento agregado de RF-05; ranking por entidad estilo IMCO, menos litigioso que señalar contratistas. |
| RF-19 | Índice de opacidad | Prerrequisito de credibilidad de todo lo demás; computable de inmediato con magnitudes ya verificadas. |

**Tanda 2 — modificaciones y tiempo (segunda iteración):**

| # | Indicador | Nota |
|---|---|---|
| RF-10 | Adiciones en valor | Umbral normativo claro (50 % Ley 80); alta en SECOP I ya; SECOP II requiere verificar `u8cx-r425`. |
| RF-11 | Adiciones en tiempo | Campos agregados en ambas plataformas. |
| RF-09 | Publicación tardía (SECOP I) | Umbral normativo (3 días); respaldado por IMCO y por hallazgo TxC específico de Colombia. |
| RF-07 | Ventana publicación→adjudicación | Versión gruesa computable ya; validación en U de Fazekas. |
| RF-08 | Diciembre / pre-Ley de Garantías | Barato, específicamente colombiano, conecta con la agenda de TxC. |

**Tanda 3 — proveedor/red (con controles editoriales fuertes):**

| # | Indicador | Nota |
|---|---|---|
| RF-14 | Sancionados | Cruce trivial; cobertura ínfima declarada; ampliar con SIRI/Contraloría. |
| RF-13 | Proveedor recién registrado gana grande | Solo con el caveat de `fecha_creacion` = registro en plataforma; nunca señalamiento individual automático. |

Quedan para fases posteriores: RF-03/RF-04 (dependen de calidad de `precio_base` y UNSPSC), RF-12 (depende del censo del join por noticeUID), RF-15/RF-16 (generadores de hipótesis, requieren verificación de `hgi6-6wh3`/`ceth-n4bn` y política editorial), RF-17 (requiere resolver el umbral por entidad), RF-18 (matching difuso contra PAA). Y explícitamente fuera del alcance de datos actuales: colusión a nivel de ofertas (§3).

**Regla transversal de publicación:** seguir a Fazekas — publicar *scores compuestos* (varios flags simultáneos) antes que flags individuales, y seguir a CCE (Manual M-MUDA-02): ante valores atípicos, verificar contra el expediente vía la URL del proceso antes de cualquier señalamiento.

---

## 6. Fuentes consultadas (2026-07-02)

**OCP / cardinal:**
- OCP 2024, *Red flags in public procurement: A guide to using data to detect and mitigate risks* (73 indicadores, fórmulas OCDS): https://www.open-contracting.org/resources/red-flags-in-public-procurement-a-guide-to-using-data-to-detect-and-mitigate-risks/ — PDF: https://www.open-contracting.org/wp-content/uploads/2024/12/OCP2024-RedFlagProcurement-1.pdf (descargado y extraído íntegro)
- OCP 2016, *Red Flags for Integrity*: https://www.open-contracting.org/resources/red-flags-integrity-giving-green-light-open-data-solutions/ — PDF: https://www.open-contracting.org/wp-content/uploads/2016/11/OCP2016-Red-flags-for-integrityshared.pdf (descargado y extraído)
- cardinal-rs docs (lista de indicadores): https://cardinal.readthedocs.io/en/latest/ — R018: https://cardinal.readthedocs.io/en/latest/cli/indicators/R/018.html
- OCP, *Cardinal, an open-source library…*: https://www.open-contracting.org/2024/06/12/cardinal-an-open-source-library-to-calculate-public-procurement-red-flags/
- OCP, *Examining procurement red flags in Latin America*: https://www.open-contracting.org/2019/06/27/examining-procurement-red-flags-in-latin-america-with-data/

**Fazekas / GTI / Banco Mundial:**
- Fazekas, Tóth & King (2016), *An Objective Corruption Risk Index Using Public Procurement Data*: https://www.repository.cam.ac.uk/items/017e6178-864b-4dd8-a22f-6cb8818c8ac0 (PDF descargado del repositorio de Cambridge y extraído íntegro — Tablas 1, 2, 3 y 5 con definiciones, umbrales y pesos)
- Fazekas & King, *Uncovering High-Level Corruption* (BJPS): https://www.cambridge.org/core/journals/british-journal-of-political-science/article/abs/uncovering-highlevel-corruption-crossnational-objective-corruption-risk-indicators-using-public-procurement-data/8A1742693965AA92BE4D2BA53EADFDF0
- Banco Mundial, blog de lanzamiento de ProACT: https://blogs.worldbank.org/en/governance/new-global-anticorruption-and-transparency-platform-proact-empowers-stakeholders-use
- GTI, página ProACT: https://www.govtransparency.eu/proact-procurement-anticorruption-and-transparency-platform/

**IMCO:**
- IRC 2024 (reporte, 11 indicadores/2 ejes): https://imco.org.mx/wp-content/uploads/2024/12/ReporteIRC.pdf (descargado y extraído íntegro)
- Página del índice: https://imco.org.mx/indice-de-riesgos-de-corrupcion/ — código: https://github.com/imco/IRC

**Transparencia por Colombia:**
- Recomendaciones contratación COVID: https://transparenciacolombia.org.co/recomendaciones-para-evitar-riesgos-de-corrupcion-en-la-contratacion-publica-y-facilitar-ejercicios-ciudadanos/
- Así se mueve la corrupción (radiografías Monitor Ciudadano): https://transparenciacolombia.org.co/asi-se-mueve-la-corrupcion-radiografia-de-los-hechos-de-corrupcion-en-colombia-2016-2020/ — PDF 2016–2021: https://transparenciacolombia.org.co/wp-content/uploads/radiografia-2016-2021-02-11-21.pdf
- Elecciones y Contratos: https://www.monitorciudadano.co/elecciones-contratos/

**Contexto local:** `docs/research/fuentes-datos-contratacion-colombia.md` (este repo, 2026-07-02) — inventario verificado de datasets, campos y problemas de calidad de SECOP en datos.gov.co sobre el que se definen todas las fichas.

**Referencias normativas colombianas citadas en fichas** (de conocimiento estándar, verificar texto vigente al implementar): Ley 80 de 1993 art. 40 (tope 50 % adiciones), Ley 1150 de 2007 art. 2 (menor cuantía por presupuesto en SMMLV), Ley 1474 de 2011 (mínima cuantía = 10 % menor cuantía), Ley 996 de 2005 (Ley de Garantías), Decreto 1082 de 2015 (plazos de publicación).

**Requests fallidos (declarados):**
- `https://cardinal.readthedocs.io/en/latest/topics/indicators/` → 404 (la lista de indicadores está en el índice raíz de las docs).
- `https://cardinal.readthedocs.io/en/cli/indicators/R/018.html` (URL que reporta el propio índice de las docs) → 404; la ruta correcta es `/en/latest/cli/indicators/R/018.html`.
- Anexo metodológico IMCO 2018 (27 indicadores de la metodología anterior, `imco.org.mx/wp-content/uploads/2018/03/AnexoMetodologicoIRC_06-03-2018.pdf`) — identificado pero **no consultado**; este informe se basa en la metodología vigente 2024 (11 indicadores).
- PDF completo del informe TxC "Así se mueve la corrupción" — no extraído íntegro; los hallazgos citados provienen de la página oficial de TxC y de la búsqueda sobre fuentes que lo reseñan.
- Los cuerpos de los 3 PDFs (OCP 2016, OCP 2024, Fazekas, IMCO 2024) no eran legibles vía WebFetch (binarios); se descargaron y se extrajo el texto localmente con PyMuPDF — extracción exitosa en los 4 casos.
