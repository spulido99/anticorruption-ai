# Cruces externos para RF-13 y RF-14: RUES (constitución de empresas) y registros de sancionados

**Fecha de investigación:** 2026-07-02
**Método:** todos los conteos, esquemas, muestras y rangos de fechas fueron verificados con requests directos a la API SODA de datos.gov.co (`https://www.datos.gov.co/resource/<4x4>.json?$select=...`) y a la API de metadatos (`/api/views/<4x4>.json`) en la fecha indicada. Los endpoints web (portal RUES, SIBOR de la Contraloría) se probaron directamente. Donde un dato viene solo de documentación y no fue verificado por API, se dice explícitamente.

**Contexto:** el catálogo de red flags (`docs/research/red-flags-contratacion.md`) dejó dos indicadores de la familia proveedor/red dependientes de fuentes externas:

- **RF-13 (proveedor recién creado que gana grande):** `qmzu-gj57.fecha_creacion` es la fecha de registro en SECOP II, no la de constitución de la empresa. Se necesita la fecha real de matrícula/constitución (RUES).
- **RF-14 (contratación con sancionados):** los datasets de multas del SECOP (`4n4q-k399` + `it5q-hg94`) suman ~2.243 filas — cobertura ínfima. Se necesita un censo real de sancionados/inhabilitados.

---

## 1. Resumen ejecutivo

**RF-13: VIABLE.** Existe un dataset abierto en datos.gov.co con la extracción **nacional** del Registro Mercantil sincronizado en el RUES: **`c82u-588k`** — 9.293.659 matrículas de las **58 cámaras de comercio**, actualización mensual, con `fecha_matricula`, `estado_matricula`, `nit` a **9 dígitos sin DV** (el DV viene en columna separada — exactamente el formato canónico del proyecto), organización jurídica y representante legal con cédula. No hace falta API del RUES ni scraping: el portal RUES no tiene acceso programático abierto (verificado: API oficial caída/credencializada, endpoint no oficial muerto).

**RF-14: VIABLE CON CONDICIONES.** El SIRI de la Procuraduría (`iaeu-rcn6`, 43.275 filas, actualización diaria) es un censo real de sanciones disciplinarias, pero **el 100 % de los registros son personas naturales (cédulas)** — sirve para cruzar contratistas persona natural y representantes legales, no empresas. El dataset de la Contraloría (`jr8e-e8tu`) está **muerto: 60 filas, sin actualizar desde 2022** — descartarlo. El censo real de responsables fiscales (que sí incluye NITs de personas jurídicas y constituye inhabilidad vigente para contratar) es el **Boletín de Responsables Fiscales** de la CGR: público, trimestral, sin login ni captcha, pero **solo en PDF** — requiere pipeline de parsing. Lo que falta: parsear el boletín y aceptar que no hay fuente abierta de antecedentes penales ni del RNMC con identificadores.

---

## 2. RF-13 — Fecha real de constitución: RUES y alternativas

### 2.1 Hallazgo principal: `c82u-588k` — Registro Mercantil nacional (RUES) en datos.gov.co

- **URL:** https://www.datos.gov.co/d/c82u-588k — metadatos: https://www.datos.gov.co/api/views/c82u-588k.json
- **Nombre:** "Personas Naturales, Personas Jurídicas y Entidades Sin Animo de Lucro".
- **Descripción oficial:** "Extracción que contiene los datos básicos del Registro Mercantil que administran las Cámaras de Comercio a nivel Nacional para Personas Naturales, Personas Jurídicas y Entidades Sin Animo de Lucro (ESADLs), que se encuentran sincronizados en el Registro Único Empresarial y Social (RUES)."
- **⚠️ Error de metadatos del portal:** el catálogo lo atribuye a la "Cámara de Comercio de Santa Rosa de Cabal, Risaralda" con cobertura "Departamental", pero la descripción y el contenido demuestran que es la extracción **nacional** del RUES (mismo patrón de error que `rpmr-utcd`/Somondoco documentado en `fuentes-datos-contratacion-colombia.md`). Verificado: `count(distinct camara_comercio)` = **58** (todas las cámaras del país); top por volumen: Bogotá 2.386.975, Medellín 749.763, Cali 560.250, Barranquilla 458.627, Bucaramanga 410.562.
- **Volumen (verificado 2026-07-02):** **9.293.659 filas**. Última actualización de filas: **2026-06-01**; frecuencia declarada: **mensual**.
- **Esquema (36 columnas; las clave para RF-13):**
  - Identidad: `codigo_camara`, `camara_comercio`, `matricula`, `razon_social`, `sigla`, `clase_identificacion` (NIT / CEDULA DE CIUDADANIA / …), `numero_identificacion`, **`nit`**, **`digito_verificacion`** (separado)
  - Fechas: **`fecha_matricula`** (texto `yyyymmdd`), `fecha_renovacion`, `ultimo_ano_renovado`, `fecha_vigencia`, `fecha_cancelacion`, `fecha_actualizacion`
  - Estado y tipo: **`estado_matricula`** (+código), `organizacion_juridica` (+código: PERSONA NATURAL, SAS, LTDA, fundaciones…), `tipo_sociedad`, `categoria_matricula`
  - Actividad: `cod_ciiu_act_econ_pri`, `cod_ciiu_act_econ_sec`, `ciiu3`, `ciiu4`
  - **Bonus red/proveedor:** `representante_legal`, `num_identificacion_representante_legal`, `clase_identificacion_rl`, e `inscripcion_proponente` (RUP)
- **Composición (verificada por agregación):**
  - `clase_identificacion`: CÉDULA 6.277.120 / **NIT 2.719.409** / SIN IDENTIFICACION 232.140 / resto extranjería y otros.
  - `estado_matricula`: CANCELADA 5.040.171 / **ACTIVA 3.836.384** / canceladas Ley 1429 255.217 / trasladadas 87.213 / "MATRÍCULA NUEVA, CONSTITUCIÓN POR TRASLADO" 29.781 / sin estado ~38 K.
  - **Personas jurídicas con NIT y matrícula ACTIVA: 1.866.616.**
- **Calidad de `fecha_matricula` (verificada):** texto `yyyymmdd` con basura en los extremos (`min` = `00000000`, `max` = `99999999`); filas con fecha < 19000101 o > 20261231: **19.929** (0,21 %) — descartables. Matrículas 2025–2026: 513.154 (volumen plausible: Confecámaras reporta ~300 K nuevas matrículas/año).
- **Muestra verificada (SAS de Bogotá):** `nit=900170781`, `digito_verificacion=7`, `fecha_matricula=20070904`, `estado_matricula=ACTIVA`, representante legal con cédula. El NIT viene **a 9 dígitos sin DV** — cruce directo con el NIT canónico del proyecto, sin truncar nada.
- **Complemento:** `nb3d-v3n7` "Establecimientos - Agencias - Sucursales" (Confecámaras, **6.292.257 filas** verificadas, mensual, actualizado 2026-06-01) — establecimientos de comercio con `nit_propietario` + `digito_verificacion` y su propia `fecha_matricula`. Útil para distinguir establecimiento vs sociedad, no necesario para RF-13.

### 2.2 Semántica: ¿`fecha_matricula` = fecha de constitución?

Para personas jurídicas, la matrícula mercantil se solicita al registrar la escritura/documento de constitución en la cámara, de modo que `fecha_matricula` ≈ fecha de constitución con días/semanas de diferencia (Código de Comercio art. 28-33; per documentación, no verificado registro a registro). Dos caveats computables:

1. **Traslado de domicilio:** una empresa que se muda de ciudad recibe matrícula nueva en la cámara destino (29.781 filas "CONSTITUCIÓN POR TRASLADO" verificadas). Mitigación: tomar `min(fecha_matricula)` por NIT sobre todo el dataset (el NIT no cambia con el traslado).
2. **Personas naturales:** su matrícula puede ser muy posterior al inicio de actividad; RF-13 ya excluye personas naturales por diseño.

### 2.3 Portal RUES: sin acceso programático abierto (verificado)

- **API oficial (`ruesapi.rues.org.co`):** existe y está documentada para aliados (endpoints tipo `GET api/EstablecimientoResumido?usuario={usuario}&nit={nit}&dv={dv}`), pero requiere usuario/credenciales de convenio con Confecámaras. La página de ayuda `https://ruesapi.rues.org.co/Help` respondió **502 Bad Gateway** al probarla el 2026-07-02.
- **Endpoint no oficial del portal viejo (`https://www.rues.org.co/Home/ConsultaNIT_json`):** probado el 2026-07-02 con POST `txtNIT=900170781` — devuelve el **shell HTML de la SPA**, no JSON. Muerto. El historial comunitario ([gist de cdiaz](https://gist.github.com/cdiaz/a48dc7cbb4fb3dbfa555e016a5aae1dd)) documenta tres generaciones de endpoints rotos (2022, 2024, 2025); el portal actual pega contra un backend Elasticsearch (`elasticprd.rues.org.co`) no documentado y cambiante. **Scrapear el portal es frágil y además innecesario** teniendo `c82u-588k`. Existen APIs comerciales de terceros (Verifik, Apitude) — descartadas: costo y dependencia sin ventaja sobre el dataset abierto.
- **DIAN RUT:** la consulta de estado del RUT es web por NIT individual (muisca), sin API abierta ni bulk; la búsqueda "RUT DIAN" en el catálogo de datos.gov.co no devolvió ningún dataset (verificado). No aporta fecha de constitución; no usar.
- **CCB (Bogotá) y cámaras individuales:** publican datasets parciales en datos.gov.co (ej. `wf53-j577` Bucaramanga 67.982 filas con `fecha_matricula`; `8j5z-5s34` Cúcuta; `3hix-y8er` Tunja) — todos subsumibles en `c82u-588k`; solo servirían como contraste de calidad.

### 2.4 Cruce y cómputo propuesto para RF-13

```
rues := c82u-588k filtrado a clase_identificacion='NIT'
        y fecha_matricula válida (19000101–hoy)
fecha_constitucion(nit) := min(fecha_matricula) por nit          -- maneja traslados
flag(contrato) := fecha_de_firma - fecha_constitucion(documento_proveedor) < 365 días
                  AND valor_del_contrato > P90(UNSPSC × departamento)
```

- Llave: `jbjy-vk9h.documento_proveedor` (tipo "Nit") normalizado a 9 dígitos = `c82u-588k.nit` (ya viene a 9 dígitos). Para SECOP I: `identificacion_del_contratista` con `tipo_identifi_del_contratista` = NIT.
- Cobertura esperada del join: 2,72 M NITs en RUES vs proveedores persona jurídica de SECOP — los no matcheados serán sobre todo entidades públicas contratistas, consorcios/UT (NITs efímeros no matriculados en cámaras) y NITs mal digitados. **Censar la tasa de match es el primer paso del prototipo.**
- Descarga: export completo `https://www.datos.gov.co/api/views/c82u-588k/rows.csv?accessType=DOWNLOAD` + refresco mensual (dataset se reemplaza; no hay campo incremental confiable — `fecha_actualizacion` existe pero basta recargar completo: tamaño manejable).
- Bonus: `representante_legal` + cédula permite reforzar RF-15/RF-16 (redes de proveedores) con datos de cámara, y `inscripcion_proponente` cruza contra el RUP.

**Veredicto RF-13: VIABLE.** La condición del catálogo ("no publicar señalamientos sin verificar la fecha de constitución real") queda satisfecha con fuente abierta, nacional, mensual y con llave NIT limpia. Riesgo residual: continuidad de publicación del dataset (publicado bajo atribución errónea; conviene descargar snapshots) y el 0,21 % de fechas basura.

---

## 3. RF-14 — Censos de sancionados

### 3.1 Procuraduría — Antecedentes de SIRI (`iaeu-rcn6`)

- **URL:** https://www.datos.gov.co/d/iaeu-rcn6 — atribución: Procuraduría General de la Nación.
- **Descripción oficial:** "Sanciones disciplinarias certificables proferidas contra servidores, ex servidores públicos y particulares que desempeñen funciones públicas."
- **Volumen y frescura (verificados):** **43.275 filas**; filas actualizadas el **2026-07-02** (mismo día de la consulta); frecuencia declarada: **diaria**.
- **Esquema (24 columnas, todas `text`):** `numero_siri`, `tipo_inhabilidad`, `calidad_persona`, `tipo_identificacion`/`nombre_tipo_identificacion`, `numero_identificacion`, nombres y apellidos, `cargo`, lugar de los hechos, **`sanciones`**, **`duracion_anos`/`duracion_mes`/`duracion_dias`**, `providencia`, `autoridad`, **`fecha_efectos_juridicos`** (texto `dd/MM/yyyy`), `numero_proceso`, `entidad_sancionado` + ubicación.
- **Hallazgo crítico (verificado por agregación):** `nombre_tipo_identificacion` = CÉDULA DE CIUDADANÍA 43.271 + CÉDULA EXTRANJERÍA 4. **Cero NITs: no hay personas jurídicas.** `calidad_persona`: fuerza pública 26.922, servidor público 16.025, particular que ejerce función pública 148, **contratista 18**, particular 4. Es el censo disciplinario de *personas*, no un registro de empresas inhabilitadas.
- **Contenido de sanciones (verificado):** dominan destituciones e inhabilidades (`INHABILIDAD GENERAL ART.39 NUM.1` 10.109, `DESTITUCION ART.39 NUM.1` 9.013, `INHABILIDAD GENERAL` 8.770…). Filas con "INHABILIDAD" en la sanción: **23.731**. `tipo_inhabilidad`: DISCIPLINARIO 43.117 / PROFESIONES LIBERALES 158.
- **Cobertura temporal (verificada con `$where=fecha_efectos_juridicos like '%/<año>'`):** 2005: 3 → 2010: 218 → 2015: 1.808 → 2020: 2.362 → 2023: 3.188 → 2025: 3.988 → 2026 (parcial): 1.838. Serie viva y creciente.
- **¿Vigente vs histórico?** El dataset no trae flag de vigencia; al ser "sanciones certificables" replica la lógica del certificado SIRI. La vigencia se **computa**: `fecha_fin = fecha_efectos_juridicos + duracion_{anos,mes,dias}` (cuando la duración viene vacía — ej. multas — no genera inhabilidad temporal). Distinguir siempre inhabilidad vigente (normativa) de sanción histórica (reputacional), como ya pide la ficha RF-14.
- **Calidad de identificadores (verificada en muestra):** `numero_identificacion` trae **espacios de relleno a la derecha** (`"7534386        "`) — `TRIM()` obligatorio; cédulas sin puntos. `fecha_efectos_juridicos` es texto `dd/MM/yyyy` — parsear a DATE.
- **Cruce con SECOP:** (a) contratistas persona natural: `jbjy-vk9h.documento_proveedor` donde `tipodocproveedor='Cédula de Ciudadanía'` (ídem SECOP I por `tipo_identifi_del_contratista`); (b) **representantes legales** de proveedores (`qmzu-gj57` y los campos de representante de `jbjy-vk9h`); (c) supervisores y ordenadores del gasto de `jbjy-vk9h` (señal de riesgo del lado entidad). El cruce (b) extiende el alcance a empresas cuyo representante está sancionado — sin afirmar que la empresa esté inhabilitada.
- **Certificado programático:** la expedición del certificado de antecedentes es web ([apps.procuraduria.gov.co/webcert](https://apps.procuraduria.gov.co/webcert/Certificado.aspx), [consulta de antecedentes](https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx)), persona a persona; no hay API pública documentada (las entidades acceden por convenio institucional — per documentación PGN, no verificado). Para uso masivo, el dataset `iaeu-rcn6` es la vía.

### 3.2 Contraloría — Responsabilidad Fiscal (`jr8e-e8tu`): descartado

- **URL:** https://www.datos.gov.co/d/jr8e-e8tu — atribución: Contraloría General de la República.
- **Verificado 2026-07-02:** **60 filas** en total; filas actualizadas por última vez el **2022-03-23**; rango de `fecha_de_resoluci_n_de_la`: 2006-05-16 → 2021-10-28. Es una muestra anecdótica congelada, no un censo.
- **Esquema (14 columnas):** `raz_n_social_de_la_entidad`, `identificaci_n` (tipo: NIT/CC), `n_mero_de_identificaci_n` (**number**), tipo y motivo de la sanción, resolución y fechas (incluida `fecha_de_firmeza_de_la_decisi`), monto (texto con `$` y comas), `fuente` (SIREF).
- **Formato de identificador (verificado en muestra):** NITs **a 10 dígitos con DV pegado** (ej. `8600345941` = 860034594 + DV 1) y almacenados como number — exactamente la patología ya vista en `jbjy-vk9h.nit_entidad`; el normalizador de NIT del proyecto (truncar DV validado) aplica igual.
- **Veredicto:** no usar salvo como fixture de pruebas del normalizador.

### 3.3 Contraloría — Boletín de Responsables Fiscales (SIBOR): el censo real

- **Qué es:** por el art. 60 de la Ley 610 de 2000, la CGR publica **trimestralmente** el boletín con las personas naturales **y jurídicas** con fallo de responsabilidad fiscal en firme **que no han satisfecho la obligación** — es decir, es directamente la lista de **inhabilitados vigentes** para contratar por esta causal (la inclusión cesa al pagar). Fuente: [FBS-CGR, glosario](https://www.fbscgr.gov.co/atencion-al-ciudadano/informacion-de-interes/glosario/boletin-de-responsables-fiscales) y [Resolución Orgánica 5677 de 2005](https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/resolucion_contraloria_5677_2005.htm).
- **Acceso (verificado 2026-07-02):** la página pública [cfiscal.contraloria.gov.co/reportes/consultaboletinestrimestrales.aspx](https://cfiscal.contraloria.gov.co/reportes/consultaboletinestrimestrales.aspx) responde 200 **sin login ni captcha** y lista los boletines trimestrales 2022–2026 **en PDF**; el vigente al consultar es el **Boletín Nº 125, corte 2026-03-31, publicado 2026-04-04**. Dos fricciones verificadas: (1) el certificado TLS del host no valida la cadena completa (hubo que saltar la verificación); (2) los archivos se descargan vía postback ASP.NET (`__doPostBack`), no por URL directa — el descargador debe simular el postback o usar navegador.
- **Formato:** **solo PDF** (la página se titula "Boletín de Responsables Fiscales formato PDF"; no se observó Excel/CSV). El boletín es tabular (nombre, tipo y número de identificación, entidad, fallo, valor) — per documentación; **el parsing del PDF es el costo de ingeniería principal de RF-14** y hay que presupuestarlo (tablas grandes, multi-página).
- **Certificado individual:** [cfiscal.contraloria.gov.co/certificados/certificadopersonanatural.aspx](https://cfiscal.contraloria.gov.co/certificados/certificadopersonanatural.aspx) (y su equivalente persona jurídica) expide el certificado por número de identificación, gratuito, vía web — útil para verificación puntual antes de publicar un hallazgo, no para cruce masivo.
- **Cruce con SECOP:** el boletín identifica por tipo+número de documento (cédulas y NITs). Tras el parsing, normalizar NIT a 9 dígitos y cruzar contra `documento_proveedor`/`identificacion_del_contratista`; la fecha del fallo permite el predicado `fecha_de_firma > fecha_del_fallo`.

### 3.4 Otras fuentes evaluadas

- **RNMC (Registro Nacional de Medidas Correctivas, Policía):** los datasets abiertos (`728x-tk8r` y afines) son **agregados estadísticos** — columnas verificadas: `municipio, articulo, numeral, literal, cantidad_de_comparendos` — sin identificadores de personas. No cruzable; la consulta individual del RNMC es web con datos personales. Descartado para RF-14.
- **Antecedentes penales (Policía Nacional):** solo consulta web individual con captcha; sin dataset abierto. Fuera de alcance.
- **Contralorías territoriales:** publican datasets sueltos (ej. `a654-crdt`/`n2rh-g43v` Cauca) pero el boletín de la CGR ya consolida los fallos de contralorías departamentales/municipales (per Ley 610 art. 60), así que no hace falta agregarlas una a una.
- **Multas SECOP (`4n4q-k399`, `it5q-hg94`):** siguen siendo la única fuente de multas *contractuales* (incumplimientos) con llave directa a contratos; mantenerlas como capa adicional pese a su cobertura ínfima (1.705 + 538 filas, verificadas en la investigación de fuentes).

### 3.5 Veredicto RF-14: VIABLE CON CONDICIONES

| Capa | Fuente | Cobertura verificada | Llave | Estado |
|---|---|---|---|---|
| Disciplinaria (personas) | `iaeu-rcn6` SIRI | 43.275 filas, 2005→hoy, diaria | cédula (TRIM) × contratista PN / representante legal / supervisor | **Lista para usar** |
| Fiscal (personas + empresas, inhabilidad vigente) | Boletín Responsables Fiscales (SIBOR) | Boletín 125, corte 2026-03-31, trimestral, PDF | cédula/NIT (tras parsing) | **Requiere pipeline de parsing PDF** |
| Contractual (multas) | `4n4q-k399` + `it5q-hg94` | 2.243 filas | NIT/cédula y código interno | Usable, cobertura ínfima declarada |
| Fiscal (dataset abierto) | `jr8e-e8tu` | 60 filas, muerto desde 2022 | — | **Descartado** |

Condiciones: (1) parsear el boletín PDF trimestral (esfuerzo de ingeniería acotado pero real, incluyendo el postback ASP.NET y el TLS defectuoso); (2) computar la vigencia de las inhabilidades del SIRI a partir de `fecha_efectos_juridicos` + duración; (3) mantener la regla editorial del catálogo: la ausencia de flag no significa proveedor limpio, y todo señalamiento se verifica contra el certificado individual oficial (SIRI / SIBOR) antes de publicar.

---

## 4. Normalización de identificadores (resumen operativo)

| Fuente | Campo | Formato observado (verificado en muestra) | Acción |
|---|---|---|---|
| `c82u-588k` (RUES) | `nit` + `digito_verificacion` | 9 dígitos sin DV; DV separado | cruce directo; usar DV para validar |
| `c82u-588k` | `fecha_matricula` | texto `yyyymmdd`; 19.929 filas basura | parsear, descartar <1900 y >hoy |
| `iaeu-rcn6` (SIRI) | `numero_identificacion` | cédula con espacios de relleno a la derecha | `TRIM()` |
| `iaeu-rcn6` | `fecha_efectos_juridicos` | texto `dd/MM/yyyy` | parsear a DATE |
| `jr8e-e8tu` (CGR) | `n_mero_de_identificaci_n` | number, NIT a 10 dígitos con DV pegado | truncar DV validado (algoritmo DIAN) |
| Boletín CGR (PDF) | tipo + número de documento | por confirmar al parsear | normalizador NIT existente |

---

## 5. Fuentes consultadas (2026-07-02)

**API (verificación directa):**
- Conteos/agregados/muestras: `https://www.datos.gov.co/resource/<4x4>.json` para `c82u-588k`, `nb3d-v3n7`, `wf53-j577`, `3hix-y8er`, `iaeu-rcn6`, `jr8e-e8tu`, `728x-tk8r`
- Metadatos/esquemas: `https://www.datos.gov.co/api/views/<4x4>.json` (mismos datasets)
- Catálogo: `https://www.datos.gov.co/api/catalog/v1?domains=www.datos.gov.co&q=...` (búsquedas: RUES, confecámaras, registro mercantil, cámara de comercio matrícula, RUT DIAN, responsables fiscales, medidas correctivas, inhabilidades, sanciones procuraduría)
- Portal RUES: `POST https://www.rues.org.co/Home/ConsultaNIT_json` (devuelve shell SPA — endpoint muerto); `https://ruesapi.rues.org.co/Help` (**502 Bad Gateway**)
- SIBOR CGR: `https://cfiscal.contraloria.gov.co/reportes/consultaboletinestrimestrales.aspx` (200 OK, sin login; cadena TLS incompleta)

**Documentación:**
- RUES — portal: https://www.rues.org.co/
- Historial comunitario de endpoints RUES: https://gist.github.com/cdiaz/a48dc7cbb4fb3dbfa555e016a5aae1dd
- Ayuda API oficial RUES (instancia de pruebas): https://pruebasruesapi.rues.org.co/Help
- Procuraduría — SIRI preguntas frecuentes: https://www.procuraduria.gov.co/SIRI/Pages/SIRI-preguntas-frecuentes.aspx
- Procuraduría — consulta de antecedentes: https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx y https://apps.procuraduria.gov.co/webcert/Certificado.aspx
- Contraloría — certificado de antecedentes fiscales: https://www.contraloria.gov.co/en/control-fiscal/responsabilidad-fiscal/certificado-de-antecedentes-fiscales y https://cfiscal.contraloria.gov.co/certificados/certificadopersonanatural.aspx
- FBS-CGR — Boletín de Responsables Fiscales (definición y periodicidad): https://www.fbscgr.gov.co/atencion-al-ciudadano/informacion-de-interes/glosario/boletin-de-responsables-fiscales
- Resolución Orgánica CGR 5677 de 2005 (reglamenta el boletín): https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/resolucion_contraloria_5677_2005.htm
- APIs comerciales de terceros sobre RUES (evaluadas y descartadas): https://docs.verifik.co/business-validation/colombia/colombian-business-information-rues/ y https://apitude.co/es/docs/services/rues-co/

**Requests fallidos (declarados):** `https://ruesapi.rues.org.co/Help` (502); WebFetch directo a `cfiscal.contraloria.gov.co` (error de verificación de certificado — se repitió la request saltando la validación TLS y respondió 200).
