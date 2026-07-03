# Proponentes por proceso y grupos de proveedores: verificación de `hgi6-6wh3` y `ceth-n4bn`

**Fecha de investigación:** 2026-07-03
**Método:** metadatos, conteos y agregados verificados con requests directos a la API SODA de datos.gov.co (`/resource/<4x4>.json`) y a la API de metadatos (`/api/views/<4x4>.json`); además, **descarga completa de ambos datasets** (keyset paging sobre `:id`, sin app token) a un DuckDB de trabajo con diff **0** contra el conteo de la API, y cruces contra el datastore local `data/secop.duckdb` (corte de la ingesta de #12). Todos los números de este informe salen de una de esas dos vías; donde algo queda sin verificar, se dice.

**Contexto:** la decisión del catálogo de skills (#8) dejó la skill `red` acotada a campos verificados y condicionó su **variante fina** — ≥2 proponentes del mismo cluster compitiendo en el mismo proceso (RF-15b/c) y rotación de ganadores del mismo cluster en una entidad (RF-16) — a verificar dos datasets identificados en la radiografía de fuentes: `hgi6-6wh3` (proponentes por proceso) y `ceth-n4bn` (grupos/consorcios). La desagregación de consorcios que RF-05/RF-06 requieren depende del segundo.

---

## 1. Resumen ejecutivo

**Ambos datasets son VIABLES y la variante fina de `red` es computable.**

- **`hgi6-6wh3` (Proponentes por Proceso SECOP II): la pieza que faltaba.** 2.235.854 filas / 674.237 procesos, actualización diaria, ids 100 % en el mismo espacio `CO1.REQ.*` que `core.procesos.id_del_proceso` (match 97,8 %). Su conteo de proponentes por proceso coincide **exactamente en 98,0 %** con `proveedores_unicos_con` (la base de RF-01 usada en el piloto de Boyacá; correlación 0,9995) — y a diferencia de ese campo agregado, **nombra a los oferentes**: para los 6.658 procesos single-bid del piloto, cubre 6.649 (99,9 %) con el oferente único identificado.
- **`ceth-n4bn` (Grupos de Proveedores SECOP II): viable como tabla de membresía, no por `nit_grupo`.** 676.754 filas = (grupo, participante) únicos; 305.404 grupos (99,2 % consorcios y UTs). El `nit_grupo` es placeholder en 87,2 % de las filas — la identidad estable del grupo es **`codigo_grupo`**, que cruza **al 100 %** con `core.contratos.codigo_proveedor` de los contratos `es_grupo` (32.648/32.648 proveedores-grupo). Los miembros traen NIT limpio casi siempre y `participacion` suma 99–101 en 96,7 % de los grupos.
- **Señal de colusión demostrada con datos reales:** cruzando ambos, hay **22.296 pares de NITs que comparten grupo y ofertaron por separado en el mismo proceso**, en **62.679 procesos** (229.295 instancias proceso-par). Verificado que no es artefacto de plataforma: cuando un grupo oferta, sus miembros aparecen además como proponentes solo en 2,15 % de los casos.
- **RF-05/RF-06 (desagregación de consorcios): VIABLE.** De los 38.558 contratos adjudicados a grupos de `ceth`, 99,2 % tienen el 100 % de sus miembros con NIT limpio y 99,8 % traen `participacion` completa — se puede repartir el valor del contrato entre miembros con pesos.

Costo de ingesta: ~630 MB CSV (`hgi6`) + ~344 MB (`ceth`), ~1 h sin token a 50 K filas/página; diario en el portal, cabe en el patrón raw → core existente.

---

## 2. `hgi6-6wh3` — Proponentes por Proceso SECOP II

### 2.1 Identidad y frescura (verificadas 2026-07-03)

- **URL:** https://www.datos.gov.co/d/hgi6-6wh3 — atribución: ANCP – Colombia Compra Eficiente. Cobertura declarada: Nacional; frecuencia declarada: **Diaria**.
- **Filas actualizadas:** 2026-07-03 (el mismo día de la consulta). Dataset creado en 2018.
- **Volumen:** **2.235.854 filas**; **674.237** procesos distintos (~3,3 proponentes/proceso).
- **Esquema (9 columnas):** `id_procedimiento` (text), `fecha_publicaci_n` (date), `nombre_procedimiento`, `nit_entidad` (number), `codigo_entidad` (number), `entidad_compradora`, `proveedor`, `nit_proveedor` (text), `codigo_proveedor` (number). Sin nulls en `id_procedimiento`, `nit_proveedor` ni `codigo_proveedor` (verificado); 16.313 filas (0,7 %) sin `fecha_publicaci_n`.
- **Cobertura temporal:** 2015 (723 filas) → crecimiento sostenido → 2025 (373.951), 2026 parcial (167.197).

### 2.2 Grano y duplicados

- Grano real: **(proceso, proponente)**. Pares (id_procedimiento, codigo_proveedor) distintos: 2.201.106 — las 34.748 filas de exceso son **duplicados idénticos en las 9 columnas** (mismo patrón que `jbjy-vk9h`: `DISTINCT` basta).
- 2.018.183 pares (proceso, nit) distintos < pares (proceso, codigo): varios códigos de proveedor comparten NIT placeholder — el grano confiable es por `codigo_proveedor`.

### 2.3 Llave de cruce con procesos (verificada contra el datastore local)

- `id_procedimiento` es **100 % `CO1.REQ.*`** (0 filas fuera del patrón) — el mismo espacio de `core.procesos.id_del_proceso`.
- Match directo: **659.229 / 674.237 procesos (97,8 %)** existen en `core.procesos`. El 2,2 % restante corresponde a procesos que no están en el corte local de `p6dx-8zbt` (sin investigar caso a caso).
- **Cobertura por modalidad** (procesos adjudicados en core): 93–98 % en *todas* las modalidades con ofertas — Mínima cuantía 96,7 %, Selección abreviada menor cuantía 97,0 %, subasta inversa 97,4 %, Licitación pública 97,0 %, Licitación obra pública 97,6 %, Concurso de méritos 96,2 %, Contratación directa con ofertas 95,5 %, régimen especial con ofertas 95,6 %. La contratación directa sin ofertas no aparece — coherente con la semántica del dataset (solo procesos donde se presentan propuestas).

### 2.4 Validación contra `proveedores_unicos_con` (la base de RF-01)

Sobre 490.424 procesos adjudicados comparables (con `proveedores_unicos_con` no nulo y presentes en `hgi6`):

- **Igualdad exacta de conteo: 98,0 %**; correlación 0,9995; `hgi6` ≥ `puc` en 490.421/490.424.
- Procesos con `puc = 1` (single bidding): **222.530, todos con filas en `hgi6` (0 faltantes)**; 222.045 (99,8 %) con exactamente 1 proponente distinto.
- **Piloto Boyacá** (adjudicados competitivos, definición aproximada del informe de #7): 9.346 procesos, 9.020 (96,5 %) con proponentes en `hgi6`; de los 6.658 single-bid, **6.649 (99,9 %) confirmados con el oferente único nombrado**. `hgi6` convierte el "54,7 % con un solo oferente" de Boyacá en una lista de *quiénes*.

### 2.5 Calidad de `nit_proveedor` — usar `codigo_proveedor` como llave

- Longitud 9 (formato canónico): 1.621.494 filas (72,5 %). Placeholder dominante: **"No Definido" 228.247 filas (10,2 %)** repartidas entre 159.959 nombres de proveedor distintos. Otros placeholders verificados: `222222222` (9.022 filas, 11 nombres distintos), `100000003` (8.425 filas). 151.215 filas con 10 dígitos (candidatas a DV pegado — misma patología ya normalizada en core).
- `codigo_proveedor` en cambio tiene **0 nulls** y es el mismo espacio de códigos de `qmzu-gj57` (SECOP II - Proveedores Registrados: 1.580.182 filas, actualización diaria, verificado) — que trae `nit`, representante legal con documento, correo, teléfono y dirección. **Regla operativa: la identidad del proponente es `codigo_proveedor`; el NIT se resuelve vía `qmzu-gj57` y `nit_proveedor` queda de respaldo.**

### 2.6 Los grupos también ofertan

287.475 filas de proponente (13 %) son grupos de `ceth-n4bn` (join por `codigo_proveedor` = `codigo_grupo`), en 58.595 procesos. Es decir, la unidad ofertante puede ser un consorcio/UT — el análisis de red debe tratar al grupo como proponente y expandir a miembros vía `ceth`.

---

## 3. `ceth-n4bn` — Grupos de Proveedores SECOP II

### 3.1 Identidad y frescura (verificadas 2026-07-03)

- **URL:** https://www.datos.gov.co/d/ceth-n4bn — atribución: ANCP – CCE. "Registra la información de las uniones temporales o grupos creados por proveedores para postularse en conjunto a procesos de compra pública". Frecuencia declarada: **Diaria**; filas actualizadas 2026-07-03.
- **Volumen:** **676.754 filas**; grano = **(grupo, participante)** exactamente único (676.754 pares distintos). **305.404 grupos**; 38.189 NITs de participante distintos.
- **Esquema (33 columnas):** identidad del grupo (`codigo_grupo`, `nombre_grupo`, `nit_grupo`, `tipo_empresa_grupo`, `fecha_creaci_n_grupo`, `esta_activo`), contacto y ubicación del grupo, representante legal del grupo (nombre/tipo doc/número/teléfono/correo), y del participante: `codigo_participante`, `nombre_participante`, `nit_participante`, `tipo_empresa_participante`, `fecha_creaci_n_participante`, **`participacion`** (number), **`es_lider_del_grupo`**.
- **Composición:** CONSORCIO 518.425 + UNIÓN TEMPORAL 152.951 = **99,2 %**; resto residual (SAS, promesas de sociedad futura, estructuras plurales…). `esta_activo` = Si en 97,3 %.
- Tamaño de grupo: 2 miembros 232.276 grupos (76 %), 3 miembros 55.038 (18 %), 4+ 9.064; **9.026 grupos con una sola fila** y ~9.003 filas con `codigo_participante` nulo y `es_lider` "No definido" (grupos sin membresía cargada). Líder: exactamente 1 en 296.279 grupos (97,0 %); 34 con 2 líderes.

### 3.2 `nit_grupo` no sirve como llave; `codigo_grupo` sí (100 % verificado)

- `nit_grupo` = "No Definido" en **589.993 filas (87,2 %)**; entre las filas con valor, las longitudes van de 1 a 12 dígitos (9 dígitos solo 47.443 filas; se observaron cédulas del representante en el campo). **Descartarlo como identificador.**
- `numero_doc_representante_legal_grupo` también es placeholder en 87,2 % — el cluster por representante legal no sale de `ceth` sino de `qmzu-gj57` (miembros) más el nombre del representante del grupo (`nombre_representante_legal_grupo`, poblado).
- **`codigo_grupo` ↔ `core.contratos.codigo_proveedor`: match 32.648/32.648 (100 %)** de los proveedores con contratos `es_grupo = true` (38.558 contratos). Y el flag es consistente: ningún contrato con `codigo_proveedor` de grupo tiene `es_grupo = false`.
- 205.123 grupos (67 %) aparecen como proponentes en `hgi6` — el resto se creó y no llegó a ofertar (o su proceso no está cubierto).

### 3.3 Miembros: NITs y participación (la vía para RF-05/RF-06)

- `nit_participante`: 71,0 % a 9 dígitos; 80.178 filas (11,8 %) a 10 dígitos (DV pegado — normalizador existente aplica); "No Definido" solo 1,3 %; 10.553 no numéricos.
- De los **38.558 contratos adjudicados a grupos**: **38.254 (99,2 %) tienen el 100 % de los miembros con NIT numérico limpio** y 38.475 (99,8 %) traen `participacion` en todos los miembros. **`participacion` suma 99–101 en 295.407/305.404 grupos (96,7 %)** — la desagregación ponderada del valor del contrato entre miembros es directa.
- Cruce `nit_participante` → `core.contratistas.documento`: 19.559/37.756 (51,8 %) — esperable: la maestra de contratistas solo contiene quienes han tenido contrato propio; no es un defecto.

---

## 4. La señal de colusión, demostrada (smoke test RF-15b)

Con los dos datasets descargados y `core`:

1. **¿Los proponentes son unidades reales de oferta?** Sí. Cuando un grupo oferta (285.263 pares proceso-grupo), sus miembros aparecen *además* como proponentes individuales solo en **2,15 %** de los casos — las filas de `hgi6` no son una expansión del grupo en miembros. (Ese 2,15 % residual — miembro y grupo ofertando en el mismo proceso — es en sí una señal a examinar.)
2. **Co-oferta de miembros del mismo grupo:** **22.296 pares distintos de NITs** que comparten al menos un grupo en `ceth` ofertaron por separado en el mismo proceso; ocurre en **62.679 procesos** (229.295 instancias proceso-par).

Advertencias para la capa metrics (no invalidan la señal, la afinan):

- Compartir un consorcio es legal y común; el par que co-oferta *y* comparte grupo es un **indicio a componer**, nunca un señalamiento aislado (regla del catálogo: scores compuestos).
- El conteo bruto infla pares que comparten *muchos* grupos efímeros (el mismo dúo crea un consorcio por proceso): la unidad honesta es el **par de NITs**, no el par (proceso, grupo).
- Refinamientos pendientes de diseño: excluir el caso grupo+miembro en el mismo proceso, ponderar por si alguno ganó, ventana temporal entre la membresía y la co-oferta.

---

## 5. Normalización de identificadores (resumen operativo)

| Fuente | Campo | Formato observado (verificado) | Acción |
|---|---|---|---|
| `hgi6-6wh3` | `id_procedimiento` | 100 % `CO1.REQ.*` | cruce directo con `core.procesos.id_del_proceso` |
| `hgi6-6wh3` | `codigo_proveedor` | number, 0 nulls | **llave canónica del proponente**; NIT vía `qmzu-gj57` |
| `hgi6-6wh3` | `nit_proveedor` | 72,5 % a 9 dígitos; 10,2 % "No Definido"; `222222222`/`100000003`; 151 K con DV pegado | respaldo; normalizador NIT existente |
| `ceth-n4bn` | `codigo_grupo` | text numérico, mismo espacio que `codigo_proveedor` | **llave canónica del grupo** (match 100 % con contratos es_grupo) |
| `ceth-n4bn` | `nit_grupo` | 87,2 % "No Definido"; longitudes 1–12 | descartar como llave |
| `ceth-n4bn` | `nit_participante` | 71 % a 9 dígitos; 11,8 % con DV pegado; 1,3 % ND | normalizador NIT existente |
| `ceth-n4bn` | `participacion` | number; suma 99–101 en 96,7 % de grupos | pesos para desagregar RF-05/06 |

---

## 6. Veredictos

- **Variante fina de la skill `red` (RF-15b/c, RF-16): VIABLE.** Cadena verificada: `hgi6` (quién oferta en cada proceso, 97,8 % cruzable a core) + `ceth` (membresía de grupos, llave `codigo_grupo` al 100 %) + `qmzu-gj57` (clusters por representante legal/correo/teléfono, mismo espacio de códigos — verificado el esquema y volumen; su perfilado fino queda para la ingesta). El smoke test produce señal real y computable hoy.
- **Desagregación de consorcios para RF-05/RF-06: VIABLE.** 99,2 % de los contratos a grupos se desagregan a miembros con NIT limpio y pesos de participación.
- **Riesgos residuales:** solo SECOP II (los procesos SECOP I del piloto municipal no tienen proponentes — límite ya conocido del alcance de datos); 2,2 % de procesos de `hgi6` sin match en el corte local (frescura/fases, sin diagnóstico caso a caso); los placeholders de NIT obligan a mantener `codigo_proveedor` como identidad primaria de red, con la maestra de contratistas (tipo+documento) como puente.
- **Siguiente paso natural:** ingesta raw → core de `hgi6-6wh3` + `ceth-n4bn` + `qmzu-gj57` (~1,6 GB CSV total, diaria en portal, cabe en el pipeline de #12), y las reglas de refinamiento de la señal en la capa metrics.

---

## 7. Fuentes consultadas (2026-07-03)

**API (verificación directa):**
- Metadatos/esquemas: `https://www.datos.gov.co/api/views/<4x4>.json` para `hgi6-6wh3`, `ceth-n4bn`, `qmzu-gj57`
- Conteos/agregados: `https://www.datos.gov.co/resource/<4x4>.json?$select=...` (mismos datasets)
- Descarga completa: keyset paging `$order=:id` + `$where=:id > '<last>'`, `$select` con lista explícita de columnas (SODA rechaza mezclar `:id` con `*`), 50 K filas/página, sin app token; `hgi6-6wh3` 2.235.854 filas y `ceth-n4bn` 676.754 filas — **diff 0 contra `count(*)` de la API**

**Cruces locales:** `data/secop.duckdb` (corte de la ingesta #12: 5,66 M contratos, 8,63 M filas de procesos) vía DuckDB `ATTACH`.

**Requests fallidos (declarados):** `$select=:id,*` devuelve 400 (limitación SODA documentada en `src/secop/datasets.py`).
