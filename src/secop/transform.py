"""raw -> core: auditable, re-runnable transformation (ADRs 0002-0005).

core.contratos / core.procesos are wide denormalized tables with identity
already resolved (normalized keys + canonical names embedded); the masters
core.entidades / core.contratistas are derived in the same pass. Everything
here re-runs from raw without re-downloading.
"""

MACROS = r"""
CREATE OR REPLACE MACRO clean_digits(s) AS
    regexp_replace(trim(coalesce(s, '')), '[^0-9]', '', 'g');

-- DIAN check-digit over a 9-digit NIT: primes 3,7,13,17,19,23,29,37,41 weigh
-- the digits right-to-left; sum mod 11; 0/1 stay, otherwise 11 - remainder.
CREATE OR REPLACE MACRO dian_dv_sum(n) AS
    CAST(n[1] AS INT) * 41 + CAST(n[2] AS INT) * 37 + CAST(n[3] AS INT) * 29 +
    CAST(n[4] AS INT) * 23 + CAST(n[5] AS INT) * 19 + CAST(n[6] AS INT) * 17 +
    CAST(n[7] AS INT) * 13 + CAST(n[8] AS INT) * 7  + CAST(n[9] AS INT) * 3;

CREATE OR REPLACE MACRO dian_dv(n) AS
    CASE WHEN dian_dv_sum(n) % 11 < 2 THEN dian_dv_sum(n) % 11
         ELSE 11 - dian_dv_sum(n) % 11 END;

-- NIT to its 9-digit base: truncate a 10th digit only when it verifies as the
-- DIAN DV of the first 9. Placeholders -> NULL (opacity stays countable).
CREATE OR REPLACE MACRO norm_nit(s) AS
    CASE
        WHEN clean_digits(s) IN ('', '0') THEN NULL
        WHEN length(clean_digits(s)) = 10
             AND CAST(clean_digits(s)[10] AS INT) = dian_dv(clean_digits(s)[1:9])
            THEN clean_digits(s)[1:9]
        ELSE clean_digits(s)
    END;

CREATE OR REPLACE MACRO null_placeholder(s) AS
    CASE WHEN trim(coalesce(s, '')) IN ('', '0', 'No Definido', 'No Aplica')
         THEN NULL ELSE trim(s) END;

-- Contractor document by type (ADR 0004): the DV rule applies only to NITs —
-- a 10-digit cedula must never be truncated. Numeric docs keep their digits;
-- foreign/non-numeric docs keep their trimmed literal value.
CREATE OR REPLACE MACRO norm_documento(tipo, doc) AS
    CASE
        WHEN null_placeholder(doc) IS NULL THEN NULL
        WHEN upper(coalesce(tipo, '')) LIKE '%NIT%' THEN norm_nit(doc)
        WHEN regexp_replace(trim(doc), '[.,\s-]', '', 'g') ~ '^[0-9]+$'
            THEN clean_digits(doc)
        ELSE trim(doc)
    END;

CREATE OR REPLACE MACRO si_no(s) AS
    CASE WHEN trim(coalesce(s, '')) ILIKE 'si' THEN true
         WHEN trim(coalesce(s, '')) ILIKE 'no' THEN false END;

CREATE OR REPLACE MACRO extract_notice_uid(url) AS
    NULLIF(regexp_extract(coalesce(url, ''), 'CO1\.NTC\.[0-9]+'), '');
"""

# Value above which a contract amount is flagged as a digitation error
# (~500,000 M COP; verified in #7: single mistyped contracts distorted whole
# departmental rankings). Flagged, never deleted or altered.
VALOR_ATIPICO_COP = 500_000_000_000

STG_CONTRATOS = f"""
CREATE OR REPLACE TEMP TABLE stg_contratos AS
WITH dedup AS (
    -- Exact duplicates (same row published twice, only :id differs) collapse;
    -- anything differing in any published column is kept.
    SELECT DISTINCT {{contratos_cols}}
    FROM raw.secop2_contratos
)
SELECT
    'SECOP_II' AS fuente,
    id_contrato,
    proceso_de_compra,
    extract_notice_uid(urlproceso) AS notice_uid,
    referencia_del_contrato,
    estado_contrato,
    norm_nit(nit_entidad) AS nit_entidad,
    trim(nombre_entidad) AS nombre_entidad,
    codigo_entidad,
    departamento, ciudad, orden, sector, rama, entidad_centralizada,
    null_placeholder(tipodocproveedor) AS tipo_documento_contratista,
    norm_documento(tipodocproveedor, documento_proveedor) AS documento_contratista,
    (norm_documento(tipodocproveedor, documento_proveedor) IS NOT NULL)
        AS contratista_resuelto,
    CASE WHEN norm_documento(tipodocproveedor, documento_proveedor) IS NOT NULL
         THEN coalesce(null_placeholder(tipodocproveedor), 'SIN_TIPO') || ':' ||
              norm_documento(tipodocproveedor, documento_proveedor)
    END AS contratista_key,
    null_placeholder(proveedor_adjudicado) AS nombre_contratista,
    codigo_proveedor,
    si_no(es_grupo) AS es_grupo,
    si_no(es_pyme) AS es_pyme,
    tipo_de_contrato,
    modalidad_de_contratacion,
    justificacion_modalidad_de AS justificacion_modalidad,
    codigo_de_categoria_principal,
    descripcion_del_proceso,
    objeto_del_contrato,
    TRY_CAST(fecha_de_firma AS DATE) AS fecha_de_firma,
    TRY_CAST(fecha_de_inicio_del_contrato AS DATE) AS fecha_de_inicio,
    TRY_CAST(fecha_de_fin_del_contrato AS DATE) AS fecha_de_fin,
    TRY_CAST(ultima_actualizacion AS DATE) AS ultima_actualizacion,
    TRY_CAST(valor_del_contrato AS DECIMAL(24, 2)) AS valor_del_contrato,
    TRY_CAST(valor_pagado AS DECIMAL(24, 2)) AS valor_pagado,
    TRY_CAST(valor_facturado AS DECIMAL(24, 2)) AS valor_facturado,
    TRY_CAST(valor_pendiente_de_ejecucion AS DECIMAL(24, 2)) AS valor_pendiente_de_ejecucion,
    coalesce(TRY_CAST(valor_del_contrato AS DECIMAL(24, 2)) > {VALOR_ATIPICO_COP}, false)
        AS valor_atipico,
    TRY_CAST(dias_adicionados AS INTEGER) AS dias_adicionados,
    null_placeholder(nombre_representante_legal) AS nombre_representante_legal,
    null_placeholder(tipo_de_identificaci_n_representante_legal)
        AS tipo_identificacion_representante_legal,
    null_placeholder(identificaci_n_representante_legal)
        AS identificacion_representante_legal,
    null_placeholder(nombre_supervisor) AS nombre_supervisor,
    null_placeholder(tipo_de_documento_supervisor) AS tipo_documento_supervisor,
    null_placeholder(n_mero_de_documento_supervisor) AS documento_supervisor,
    origen_de_los_recursos,
    destino_gasto,
    urlproceso,
    CAST(NULL AS VARCHAR) AS duplicado_de
FROM dedup
"""

STG_PROCESOS = """
CREATE OR REPLACE TEMP TABLE stg_procesos AS
WITH dedup AS (
    SELECT DISTINCT {procesos_cols}
    FROM raw.secop2_procesos
)
SELECT
    id_del_proceso,
    referencia_del_proceso,
    extract_notice_uid(urlproceso) AS notice_uid,
    norm_nit(nit_entidad) AS nit_entidad,
    trim(entidad) AS entidad,
    codigo_entidad,
    codigo_pci,
    departamento_entidad,
    ciudad_entidad,
    ordenentidad,
    fase,
    estado_del_procedimiento,
    estado_de_apertura_del_proceso,
    estado_resumen,
    nombre_del_procedimiento,
    descripci_n_del_procedimiento AS descripcion_del_procedimiento,
    modalidad_de_contratacion,
    justificaci_n_modalidad_de AS justificacion_modalidad,
    tipo_de_contrato,
    subtipo_de_contrato,
    codigo_principal_de_categoria,
    TRY_CAST(precio_base AS DECIMAL(24, 2)) AS precio_base,
    TRY_CAST(duracion AS INTEGER) AS duracion,
    unidad_de_duracion,
    TRY_CAST(fecha_de_publicacion_del AS DATE) AS fecha_de_publicacion,
    TRY_CAST(fecha_de_ultima_publicaci AS DATE) AS fecha_de_ultima_publicacion,
    TRY_CAST(fecha_de_recepcion_de AS DATE) AS fecha_de_recepcion_de_respuestas,
    TRY_CAST(fecha_adjudicacion AS DATE) AS fecha_adjudicacion,
    si_no(adjudicado) AS adjudicado,
    null_placeholder(id_adjudicacion) AS id_adjudicacion,
    TRY_CAST(valor_total_adjudicacion AS DECIMAL(24, 2)) AS valor_total_adjudicacion,
    TRY_CAST(proveedores_invitados AS INTEGER) AS proveedores_invitados,
    TRY_CAST(proveedores_con_invitacion AS INTEGER) AS proveedores_con_invitacion,
    TRY_CAST(proveedores_que_manifestaron AS INTEGER) AS proveedores_que_manifestaron,
    TRY_CAST(respuestas_al_procedimiento AS INTEGER) AS respuestas_al_procedimiento,
    TRY_CAST(respuestas_externas AS INTEGER) AS respuestas_externas,
    TRY_CAST(conteo_de_respuestas_a_ofertas AS INTEGER) AS conteo_de_respuestas_a_ofertas,
    TRY_CAST(proveedores_unicos_con AS INTEGER) AS proveedores_unicos_con,
    TRY_CAST(numero_de_lotes AS INTEGER) AS numero_de_lotes,
    TRY_CAST(visualizaciones_del AS INTEGER) AS visualizaciones,
    null_placeholder(nombre_del_proveedor) AS nombre_del_proveedor,
    -- No document-type column here, so the NIT DV-truncation rule cannot be
    -- applied safely (10-digit cedulas would be mangled): digits only.
    CASE WHEN null_placeholder(nit_del_proveedor_adjudicado) IS NULL THEN NULL
         WHEN clean_digits(nit_del_proveedor_adjudicado) = ''
             THEN trim(nit_del_proveedor_adjudicado)
         ELSE clean_digits(nit_del_proveedor_adjudicado)
    END AS documento_proveedor_adjudicado,
    codigoproveedor,
    departamento_proveedor,
    ciudad_proveedor,
    urlproceso
FROM dedup
"""

CONTRATISTAS = """
CREATE OR REPLACE TABLE core.contratistas AS
WITH stats AS (
    SELECT
        contratista_key,
        any_value(tipo_documento_contratista) AS tipo_documento,
        any_value(documento_contratista) AS documento,
        count(*) AS n_contratos,
        count(DISTINCT nit_entidad) AS n_entidades,
        sum(valor_del_contrato) AS valor_total,
        sum(valor_del_contrato) FILTER (NOT valor_atipico) AS valor_total_sano,
        min(fecha_de_firma) AS primer_contrato,
        max(fecha_de_firma) AS ultimo_contrato
    FROM stg_contratos
    WHERE contratista_key IS NOT NULL
    GROUP BY contratista_key
),
nombres AS (
    SELECT contratista_key, nombre_contratista AS nombre,
           count(*) AS n, max(fecha_de_firma) AS ultima
    FROM stg_contratos
    WHERE contratista_key IS NOT NULL AND nombre_contratista IS NOT NULL
    GROUP BY 1, 2
),
canon AS (
    SELECT contratista_key, nombre,
           row_number() OVER (PARTITION BY contratista_key
                              ORDER BY n DESC, ultima DESC NULLS LAST, nombre) AS rk
    FROM nombres
),
vistos AS (
    SELECT contratista_key, list(nombre ORDER BY n DESC, nombre) AS nombres_vistos
    FROM nombres GROUP BY 1
)
SELECT
    s.tipo_documento, s.documento, s.contratista_key,
    c.nombre AS nombre_canonico,
    v.nombres_vistos,
    s.n_contratos, s.n_entidades, s.valor_total, s.valor_total_sano,
    s.primer_contrato, s.ultimo_contrato
FROM stats s
LEFT JOIN canon c ON c.contratista_key = s.contratista_key AND c.rk = 1
LEFT JOIN vistos v ON v.contratista_key = s.contratista_key
"""

ENTIDADES = """
CREATE OR REPLACE TABLE core.entidades AS
WITH fuentes AS (
    SELECT nit_entidad, nombre_entidad AS nombre, departamento, orden,
           fecha_de_firma AS fecha
    FROM stg_contratos WHERE nit_entidad IS NOT NULL
    UNION ALL
    SELECT nit_entidad, entidad, departamento_entidad, ordenentidad,
           fecha_de_publicacion
    FROM stg_procesos WHERE nit_entidad IS NOT NULL
),
nombres AS (
    SELECT nit_entidad, nombre, count(*) AS n, max(fecha) AS ultima
    FROM fuentes WHERE nombre IS NOT NULL GROUP BY 1, 2
),
canon AS (
    SELECT nit_entidad, nombre,
           row_number() OVER (PARTITION BY nit_entidad
                              ORDER BY n DESC, ultima DESC NULLS LAST, nombre) AS rk
    FROM nombres
),
vistos AS (
    SELECT nit_entidad, list(nombre ORDER BY n DESC, nombre) AS nombres_vistos
    FROM nombres GROUP BY 1
),
depto AS (
    SELECT nit_entidad, departamento,
           row_number() OVER (PARTITION BY nit_entidad ORDER BY count(*) DESC, departamento) AS rk
    FROM fuentes WHERE departamento IS NOT NULL GROUP BY 1, 2
),
ordenes AS (
    SELECT nit_entidad, orden,
           row_number() OVER (PARTITION BY nit_entidad ORDER BY count(*) DESC, orden) AS rk
    FROM fuentes WHERE orden IS NOT NULL GROUP BY 1, 2
),
sectores AS (
    SELECT nit_entidad, sector,
           row_number() OVER (PARTITION BY nit_entidad ORDER BY count(*) DESC, sector) AS rk
    FROM stg_contratos WHERE nit_entidad IS NOT NULL AND sector IS NOT NULL GROUP BY 1, 2
),
stats_c AS (
    SELECT nit_entidad, count(*) AS n_contratos,
           sum(valor_del_contrato) FILTER (NOT valor_atipico) AS valor_contratado_sano,
           min(fecha_de_firma) AS primer_contrato,
           max(fecha_de_firma) AS ultimo_contrato
    FROM stg_contratos WHERE nit_entidad IS NOT NULL GROUP BY 1
),
stats_p AS (
    SELECT nit_entidad, count(*) AS n_procesos
    FROM stg_procesos WHERE nit_entidad IS NOT NULL GROUP BY 1
),
llaves AS (SELECT DISTINCT nit_entidad FROM fuentes)
SELECT
    k.nit_entidad,
    c.nombre AS nombre_canonico,
    v.nombres_vistos,
    d.departamento,
    o.orden,
    se.sector,
    coalesce(sc.n_contratos, 0) AS n_contratos,
    coalesce(sp.n_procesos, 0) AS n_procesos,
    sc.valor_contratado_sano,
    sc.primer_contrato,
    sc.ultimo_contrato
FROM llaves k
LEFT JOIN canon c ON c.nit_entidad = k.nit_entidad AND c.rk = 1
LEFT JOIN vistos v ON v.nit_entidad = k.nit_entidad
LEFT JOIN depto d ON d.nit_entidad = k.nit_entidad AND d.rk = 1
LEFT JOIN ordenes o ON o.nit_entidad = k.nit_entidad AND o.rk = 1
LEFT JOIN sectores se ON se.nit_entidad = k.nit_entidad AND se.rk = 1
LEFT JOIN stats_c sc ON sc.nit_entidad = k.nit_entidad
LEFT JOIN stats_p sp ON sp.nit_entidad = k.nit_entidad
"""

FINAL = """
CREATE OR REPLACE TABLE core.contratos AS
SELECT
    s.* EXCLUDE (nombre_entidad, nombre_contratista),
    s.nombre_entidad,
    e.nombre_canonico AS nombre_entidad_canonico,
    s.nombre_contratista,
    ct.nombre_canonico AS nombre_contratista_canonico
FROM stg_contratos s
LEFT JOIN core.entidades e USING (nit_entidad)
LEFT JOIN core.contratistas ct USING (contratista_key);

CREATE OR REPLACE TABLE core.procesos AS
SELECT
    s.* EXCLUDE (entidad),
    s.entidad,
    e.nombre_canonico AS nombre_entidad_canonico
FROM stg_procesos s
LEFT JOIN core.entidades e USING (nit_entidad);

CREATE OR REPLACE VIEW core.contratos_unicos AS
SELECT * FROM core.contratos WHERE duplicado_de IS NULL;
"""


def install_macros(con):
    con.execute(MACROS)


def run_transform(con):
    install_macros(con)
    con.execute("CREATE SCHEMA IF NOT EXISTS core")
    from .datasets import CONTRATOS, PROCESOS
    con.execute(STG_CONTRATOS.format(
        contratos_cols=", ".join(CONTRATOS.columns)))
    con.execute(STG_PROCESOS.format(
        procesos_cols=", ".join(PROCESOS.columns)))
    con.execute(CONTRATISTAS)
    con.execute(ENTIDADES)
    con.execute(FINAL)
    con.execute("DROP TABLE IF EXISTS stg_contratos")
    con.execute("DROP TABLE IF EXISTS stg_procesos")
