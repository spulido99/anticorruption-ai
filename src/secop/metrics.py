"""core -> metrics: the precomputed red-flag layer (#8, #14).

Deterministic and re-runnable from core. Skills read these tables; per #8,
no number enters a finding without coming from `metrics`. Thresholds are NOT
computed at build time: they are calibrated separately against the national
distribution (`calibrate`) and versioned in umbrales.json, so a build is
reproducible against a given thresholds file.

Fichas: docs/research/red-flags-contratacion.md. Computable on the current
datastore (SECOP II only): RF-01, RF-02, RF-05, RF-06, RF-07, RF-08, RF-11,
RF-19. Deferred until their sources are ingested: RF-09/RF-10 (SECOP I,
u8cx-r425), RF-13/RF-14 (#19), consortium disaggregation (#21).
"""

import json
from pathlib import Path

# Competitive modalidades for RF-01, as probed for #7 (see
# docs/research/assets/seleccion-ambito-piloto/analyze.py).
COMPETITIVE = (
    "Licitación pública",
    "Licitación pública Obra Publica",
    "Licitación Pública Acuerdo Marco de Precios",
    "Selección Abreviada de Menor Cuantía",
    "Seleccion Abreviada Menor Cuantia Sin Manifestacion Interes",
    "Selección abreviada subasta inversa",
    "Concurso de méritos abierto",
    "Concurso de méritos con precalificación",
    "Mínima cuantía",
)

# 'Directa' = exactly the two direct-contracting modalidades (#7 semantics).
DIRECTA = ("Contratación directa", "Contratación Directa (con ofertas)")

# RF-02 strict variant: prestación de servicios is direct by legal design and
# dominates counts; it leaves the numerator, never the denominator.
TIPO_SERVICIOS = "Prestación de servicios"

# RF-08: start of the Ley de Garantías (Ley 996 de 2005) direct-contracting
# restriction, 4 months before each presidential election, with the election
# year the metric row lands on.
LEY_GARANTIAS = (("2018-01-27", 2018), ("2022-01-29", 2022), ("2026-01-31", 2026))

UMBRALES_PATH = Path(__file__).with_name("umbrales.json")


def load_umbrales(path=UMBRALES_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sql_list(values):
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def _tbl_rf07(con, ventanas):
    con.execute("""CREATE OR REPLACE TEMP TABLE umbral_rf07
                   (grupo VARCHAR, p05 DOUBLE, p95 DOUBLE)""")
    if ventanas:
        con.executemany(
            "INSERT INTO umbral_rf07 VALUES (?, ?, ?)",
            [(g, v["p05"], v["p95"]) for g, v in ventanas.items()],
        )


def _tbl_cutoff(con, name, cutoffs, col):
    con.execute(f"CREATE OR REPLACE TEMP TABLE {name} "
                f"({col} VARCHAR, cutoff DOUBLE)")
    if cutoffs:
        con.executemany(f"INSERT INTO {name} VALUES (?, ?)",
                        list(cutoffs.items()))


PROCESOS = f"""
CREATE OR REPLACE TABLE metrics.procesos AS
WITH base AS (
    SELECT
        id_del_proceso, notice_uid, nit_entidad, departamento_entidad,
        year(fecha_de_publicacion) AS anio,
        modalidad_de_contratacion, adjudicado,
        proveedores_unicos_con, respuestas_al_procedimiento,
        modalidad_de_contratacion IN ({_sql_list(COMPETITIVE)}) AS es_competitivo,
        date_diff('day', fecha_de_publicacion, fecha_adjudicacion) AS rf07_dias
    FROM core.procesos
)
SELECT
    b.* EXCLUDE (rf07_dias),
    CASE WHEN b.es_competitivo AND b.adjudicado THEN
        coalesce(b.proveedores_unicos_con = 1, false)
        OR coalesce(b.respuestas_al_procedimiento = 1, false)
    END AS rf01_single_bid,
    b.rf07_dias,
    CASE
        WHEN b.rf07_dias < u.p05 THEN 'corta'
        WHEN b.rf07_dias > u.p95 THEN 'larga'
    END AS rf07_ventana
FROM base b
LEFT JOIN umbral_rf07 u
    ON u.grupo = b.modalidad_de_contratacion || '|' || b.anio
"""


# Shared per-contract base every metrics table reads: directa semantics,
# value hygiene (sano = present and below the digitation-error cap) and the
# RF-11 original term. Value sums use sano only; counts keep everything.
BASE_CONTRATOS = f"""
CREATE OR REPLACE TEMP TABLE m_contratos AS
SELECT
    id_contrato, nit_entidad, departamento, year(fecha_de_firma) AS anio,
    modalidad_de_contratacion, tipo_de_contrato,
    modalidad_de_contratacion IN ({_sql_list(DIRECTA)}) AS es_directa,
    tipo_de_contrato = '{TIPO_SERVICIOS}' AS es_servicios,
    contratista_key, contratista_resuelto,
    valor_del_contrato AS valor, valor_atipico,
    (valor_del_contrato IS NOT NULL AND NOT valor_atipico) AS valor_sano,
    fecha_de_firma,
    date_diff('day', fecha_de_inicio, fecha_de_fin) - coalesce(dias_adicionados, 0)
        AS plazo_original_dias,
    dias_adicionados
FROM core.contratos_unicos
WHERE nit_entidad IS NOT NULL
"""


def _contratos_sql(umbrales):
    return f"""
CREATE OR REPLACE TABLE metrics.contratos AS
SELECT
    c.id_contrato, c.nit_entidad, c.departamento, c.anio, c.contratista_key,
    c.modalidad_de_contratacion, c.tipo_de_contrato, c.es_directa,
    c.valor, c.valor_atipico,
    c.plazo_original_dias,
    CASE WHEN c.plazo_original_dias > 0
         THEN coalesce(c.dias_adicionados, 0) / c.plazo_original_dias::DOUBLE
    END AS rf11_pct_prorroga,
    CASE WHEN c.plazo_original_dias > 0 AND u.cutoff IS NOT NULL THEN
        coalesce(c.dias_adicionados, 0) / c.plazo_original_dias::DOUBLE
            > {float(umbrales["rf11_min_pct"])}
        AND coalesce(c.dias_adicionados, 0) / c.plazo_original_dias::DOUBLE
            > u.cutoff
    END AS rf11_flag
FROM m_contratos c
LEFT JOIN u_rf11 u ON u.grupo = c.tipo_de_contrato
"""


PARES_12M = """
CREATE OR REPLACE TABLE metrics.entidad_contratista_12m AS
WITH ent_mes AS (
    SELECT nit_entidad, date_trunc('month', fecha_de_firma) AS mes,
           coalesce(sum(valor) FILTER (valor_sano), 0) AS v,
           count(*) FILTER (valor_sano) AS n
    FROM m_contratos
    WHERE fecha_de_firma IS NOT NULL
    GROUP BY 1, 2
),
ent_12m AS (
    SELECT nit_entidad, mes,
           sum(v) OVER w AS valor_entidad_12m,
           sum(n) OVER w AS n_contratos_entidad_12m
    FROM ent_mes
    WINDOW w AS (PARTITION BY nit_entidad ORDER BY mes
                 RANGE BETWEEN INTERVAL 11 MONTH PRECEDING AND CURRENT ROW)
),
par_mes AS (
    SELECT nit_entidad, contratista_key,
           date_trunc('month', fecha_de_firma) AS mes,
           sum(valor) AS v
    FROM m_contratos
    WHERE contratista_resuelto AND valor_sano AND fecha_de_firma IS NOT NULL
    GROUP BY 1, 2, 3
),
par_12m AS (
    SELECT nit_entidad, contratista_key, mes,
           sum(v) OVER w AS valor_12m
    FROM par_mes
    WINDOW w AS (PARTITION BY nit_entidad, contratista_key ORDER BY mes
                 RANGE BETWEEN INTERVAL 11 MONTH PRECEDING AND CURRENT ROW)
)
SELECT
    p.nit_entidad, p.contratista_key, p.mes,
    p.valor_12m, e.valor_entidad_12m, e.n_contratos_entidad_12m,
    p.valor_12m / NULLIF(e.valor_entidad_12m, 0) AS rf05_share,
    CASE WHEN e.n_contratos_entidad_12m >= {rf05_min}
         THEN p.valor_12m / NULLIF(e.valor_entidad_12m, 0) > {rf05_cutoff}
    END AS rf05_flag
FROM par_12m p
JOIN ent_12m e USING (nit_entidad, mes)
"""


def _entidad_anio_sql(umbrales):
    garantias = ", ".join(f"(DATE '{d}', {a})" for d, a in LEY_GARANTIAS)
    return f"""
CREATE OR REPLACE TABLE metrics.entidad_anio AS
WITH contratos AS (
    SELECT * FROM m_contratos
),
c AS (
    SELECT
        nit_entidad, anio,
        count(*) AS n_contratos,
        sum(valor) FILTER (valor_sano) AS valor_total_sano,
        count(*) FILTER (es_directa) / count(*)::DOUBLE AS rf02_pct_directa_n,
        coalesce(sum(valor) FILTER (es_directa AND valor_sano), 0)
            / NULLIF(sum(valor) FILTER (valor_sano), 0) AS rf02_pct_directa_valor,
        count(*) FILTER (es_directa AND NOT es_servicios) / count(*)::DOUBLE
            AS rf02_pct_directa_n_estricta,
        coalesce(sum(valor) FILTER (es_directa AND NOT es_servicios AND valor_sano), 0)
            / NULLIF(sum(valor) FILTER (valor_sano), 0)
            AS rf02_pct_directa_valor_estricta,
        coalesce(sum(valor) FILTER (valor_sano AND month(fecha_de_firma) = 12), 0)
            / NULLIF(sum(valor) FILTER (valor_sano), 0) AS rf08_pct_diciembre,
        count(*) FILTER (NOT contratista_resuelto) / count(*)::DOUBLE
            AS rf19_pct_contratistas_no_resueltos,
        count(*) FILTER (valor IS NULL OR valor = 0) / count(*)::DOUBLE
            AS rf19_pct_valor_cero,
        count(*) FILTER (valor_atipico) / count(*)::DOUBLE
            AS rf19_pct_valor_atipico
    FROM contratos
    GROUP BY 1, 2
),
hhi AS (
    SELECT nit_entidad, anio,
           sum(power(v_k / v_total, 2)) AS rf06_hhi,
           count(*) AS rf06_n_contratistas
    FROM (
        SELECT nit_entidad, anio, contratista_key,
               sum(valor) AS v_k,
               sum(sum(valor)) OVER (PARTITION BY nit_entidad, anio) AS v_total
        FROM contratos
        WHERE contratista_resuelto AND valor_sano AND valor > 0
        GROUP BY 1, 2, 3
    )
    GROUP BY 1, 2
),
p AS (
    SELECT
        m.nit_entidad, m.anio,
        count(*) FILTER (m.es_competitivo AND m.adjudicado) AS rf01_n_competitivos,
        count(*) FILTER (m.rf01_single_bid) AS rf01_n_single_bid,
        count(*) FILTER (m.adjudicado AND cp.documento_proveedor_adjudicado IS NULL)
            / NULLIF(count(*) FILTER (m.adjudicado), 0)::DOUBLE
            AS rf19_pct_procesos_sin_proveedor
    FROM metrics.procesos m
    JOIN core.procesos cp USING (id_del_proceso)
    WHERE m.nit_entidad IS NOT NULL
    GROUP BY 1, 2
),
pre AS (
    SELECT nit_entidad, g.anio,
           (coalesce(sum(valor) FILTER (fecha_de_firma >= g.inicio - INTERVAL 2 MONTH), 0) / 2)
           / NULLIF(sum(valor) / 12, 0) AS rf08_ratio_preelectoral
    FROM contratos, (VALUES {garantias}) AS g(inicio, anio)
    WHERE es_directa AND valor_sano
      AND fecha_de_firma >= g.inicio - INTERVAL 12 MONTH
      AND fecha_de_firma < g.inicio
    GROUP BY 1, 2
),
llaves AS (
    SELECT nit_entidad, anio FROM c
    UNION
    SELECT nit_entidad, anio FROM p
    UNION
    SELECT nit_entidad, anio FROM pre
)
SELECT
    k.nit_entidad, k.anio,
    e.nombre_canonico AS nombre_entidad,
    e.departamento, e.orden,
    c.n_contratos, c.valor_total_sano,
    -- RF-01
    p.rf01_n_competitivos, p.rf01_n_single_bid,
    p.rf01_n_single_bid / NULLIF(p.rf01_n_competitivos, 0)::DOUBLE AS rf01_share,
    CASE WHEN p.rf01_n_competitivos >= {int(umbrales["rf01_min_procesos"])}
         THEN p.rf01_n_single_bid / NULLIF(p.rf01_n_competitivos, 0)::DOUBLE
              > u01.cutoff
    END AS rf01_flag,
    -- RF-02
    c.rf02_pct_directa_n, c.rf02_pct_directa_valor,
    c.rf02_pct_directa_n_estricta, c.rf02_pct_directa_valor_estricta,
    c.rf02_pct_directa_valor > u02.cutoff AS rf02_flag,
    -- RF-06
    h.rf06_hhi, h.rf06_n_contratistas,
    CASE WHEN c.n_contratos >= {int(umbrales["rf06_min_contratos"])}
              AND h.rf06_n_contratistas >= {int(umbrales["rf06_min_contratistas"])}
         THEN h.rf06_hhi > {float(umbrales["rf06_hhi_alto"])}
    END AS rf06_flag,
    -- RF-08
    c.rf08_pct_diciembre,
    c.rf08_pct_diciembre > u08.cutoff AS rf08_flag,
    pre.rf08_ratio_preelectoral,
    pre.rf08_ratio_preelectoral > u08p.cutoff AS rf08_flag_preelectoral,
    -- RF-19
    c.rf19_pct_contratistas_no_resueltos, c.rf19_pct_valor_cero,
    c.rf19_pct_valor_atipico, p.rf19_pct_procesos_sin_proveedor,
    (coalesce(c.rf19_pct_contratistas_no_resueltos, 0)
     + coalesce(c.rf19_pct_valor_cero, 0)
     + coalesce(c.rf19_pct_valor_atipico, 0)
     + coalesce(p.rf19_pct_procesos_sin_proveedor, 0))
    / NULLIF((c.rf19_pct_contratistas_no_resueltos IS NOT NULL)::INT
             + (c.rf19_pct_valor_cero IS NOT NULL)::INT
             + (c.rf19_pct_valor_atipico IS NOT NULL)::INT
             + (p.rf19_pct_procesos_sin_proveedor IS NOT NULL)::INT, 0)
        AS rf19_score,
    coalesce((coalesce(c.rf19_pct_contratistas_no_resueltos, 0)
              + coalesce(c.rf19_pct_valor_cero, 0)
              + coalesce(c.rf19_pct_valor_atipico, 0)
              + coalesce(p.rf19_pct_procesos_sin_proveedor, 0))
             / NULLIF((c.rf19_pct_contratistas_no_resueltos IS NOT NULL)::INT
                      + (c.rf19_pct_valor_cero IS NOT NULL)::INT
                      + (c.rf19_pct_valor_atipico IS NOT NULL)::INT
                      + (p.rf19_pct_procesos_sin_proveedor IS NOT NULL)::INT, 0)
             > {float(umbrales["rf19_no_evaluable"])}, false)
        AS rf19_no_evaluable
FROM llaves k
LEFT JOIN c ON c.nit_entidad = k.nit_entidad AND c.anio IS NOT DISTINCT FROM k.anio
LEFT JOIN hhi h ON h.nit_entidad = k.nit_entidad AND h.anio IS NOT DISTINCT FROM k.anio
LEFT JOIN p ON p.nit_entidad = k.nit_entidad AND p.anio IS NOT DISTINCT FROM k.anio
LEFT JOIN pre ON pre.nit_entidad = k.nit_entidad AND pre.anio IS NOT DISTINCT FROM k.anio
LEFT JOIN core.entidades e ON e.nit_entidad = k.nit_entidad
LEFT JOIN u_rf01 u01 ON u01.orden = e.orden
LEFT JOIN u_rf02 u02 ON u02.orden = e.orden
LEFT JOIN u_rf08 u08 ON u08.orden = e.orden
LEFT JOIN u_rf08p u08p ON u08p.orden = e.orden
"""


def run_metrics(con, umbrales):
    con.execute("CREATE SCHEMA IF NOT EXISTS metrics")
    _tbl_rf07(con, umbrales.get("rf07_ventana", {}))
    _tbl_cutoff(con, "u_rf01", umbrales.get("rf01_share_outlier", {}), "orden")
    _tbl_cutoff(con, "u_rf02", umbrales.get("rf02_pct_directa_valor_outlier", {}), "orden")
    _tbl_cutoff(con, "u_rf08", umbrales.get("rf08_pct_diciembre_p90", {}), "orden")
    _tbl_cutoff(con, "u_rf08p", umbrales.get("rf08_preelectoral_p90", {}), "orden")
    _tbl_cutoff(con, "u_rf11", umbrales.get("rf11_pct_prorroga_p90", {}), "grupo")
    con.execute(BASE_CONTRATOS)
    con.execute(PROCESOS)
    con.execute(_entidad_anio_sql(umbrales))
    con.execute(_contratos_sql(umbrales))
    con.execute(PARES_12M.format(
        rf05_min=int(umbrales["rf05_min_contratos_12m"]),
        rf05_cutoff=float(umbrales["rf05_share_outlier"])))
    con.execute("""CREATE OR REPLACE TABLE metrics.build_info AS
                   SELECT now()::TIMESTAMP AS built_at, ? AS umbrales,
                          (SELECT count(*) FROM core.contratos_unicos) AS n_contratos,
                          (SELECT count(*) FROM core.procesos) AS n_procesos""",
                [json.dumps(umbrales, ensure_ascii=False)])
    for t in ("m_contratos", "umbral_rf07", "u_rf01", "u_rf02", "u_rf08",
              "u_rf08p", "u_rf11"):
        con.execute(f"DROP TABLE IF EXISTS {t}")


# Normative constants that ride along in every calibration: HHI 0.25 is the
# antitrust convention, RF-11's 50% floor echoes the Ley 80 addition cap, the
# RF-06 mins keep tiny buyers from flagging on arithmetic alone, and RF-05's
# 40% is OCP R040's example — its pair-month grain is dominated by micro-pairs
# (national P75 ~0.1%), so an IQR cutoff there would flag everything.
NORMATIVOS = {
    "rf05_share_outlier": 0.4,
    "rf06_hhi_alto": 0.25,
    "rf06_min_contratos": 10,
    "rf06_min_contratistas": 3,
    "rf11_min_pct": 0.5,
}


def _iqr_cutoffs(con, sql, params):
    # Q3 + 1.5*IQR capped at the group's P95: shares live in [0,1] and their
    # national distributions hug 1.0, so the uncapped rule can emit cutoffs
    # above 1 — a flag that can never fire reads as "all clean".
    return {g: float(min(q3 + 1.5 * (q3 - q1), p95))
            for g, q1, q3, p95 in con.execute(sql, params).fetchall()}


def calibrate(con, min_grupo=200, min_procesos=20, min_contratos=20):
    """Derive the umbrales from the loaded distribution (OCP-style
    percentiles/IQR per comparable group). Builds metrics with flag-free
    bootstrap thresholds first, then reads the distributions off the built
    tables, so calibration and build see identical metric semantics."""
    bootstrap = {
        "rf01_min_procesos": min_procesos,
        "rf05_min_contratos_12m": min_contratos,
        "rf19_no_evaluable": 1e18,
        **NORMATIVOS,
    }
    run_metrics(con, bootstrap)

    u = {"rf01_min_procesos": min_procesos,
         "rf05_min_contratos_12m": min_contratos,
         **NORMATIVOS}

    u["rf01_share_outlier"] = _iqr_cutoffs(con, """
        SELECT orden, quantile_cont(rf01_share, 0.25), quantile_cont(rf01_share, 0.75),
               quantile_cont(rf01_share, 0.95)
        FROM metrics.entidad_anio
        WHERE rf01_share IS NOT NULL AND orden IS NOT NULL
          AND rf01_n_competitivos >= ?
        GROUP BY orden HAVING count(*) >= ?""", [min_procesos, min_grupo])

    u["rf02_pct_directa_valor_outlier"] = _iqr_cutoffs(con, """
        SELECT orden, quantile_cont(rf02_pct_directa_valor, 0.25),
               quantile_cont(rf02_pct_directa_valor, 0.75),
               quantile_cont(rf02_pct_directa_valor, 0.95)
        FROM metrics.entidad_anio
        WHERE rf02_pct_directa_valor IS NOT NULL AND orden IS NOT NULL
          AND n_contratos >= ?
        GROUP BY orden HAVING count(*) >= ?""", [min_contratos, min_grupo])

    u["rf07_ventana"] = {
        g: {"p05": float(p05), "p95": float(p95)}
        for g, p05, p95 in con.execute("""
            SELECT modalidad_de_contratacion || '|' || anio,
                   quantile_cont(rf07_dias, 0.05), quantile_cont(rf07_dias, 0.95)
            FROM metrics.procesos
            WHERE rf07_dias IS NOT NULL AND anio IS NOT NULL
            GROUP BY 1 HAVING count(*) >= ?""", [min_grupo]).fetchall()}

    u["rf08_pct_diciembre_p90"] = {g: float(p90) for g, p90 in con.execute("""
        SELECT orden, quantile_cont(rf08_pct_diciembre, 0.90)
        FROM metrics.entidad_anio
        WHERE rf08_pct_diciembre IS NOT NULL AND orden IS NOT NULL
          AND n_contratos >= ?
        GROUP BY orden HAVING count(*) >= ?""",
        [min_contratos, min_grupo]).fetchall()}

    # No activity floor here: the ratio's 12-month window lives in the year
    # BEFORE the election, so the election year's own count is irrelevant.
    u["rf08_preelectoral_p90"] = {g: float(p90) for g, p90 in con.execute("""
        SELECT orden, quantile_cont(rf08_ratio_preelectoral, 0.90)
        FROM metrics.entidad_anio
        WHERE rf08_ratio_preelectoral IS NOT NULL AND orden IS NOT NULL
        GROUP BY orden HAVING count(*) >= ?""", [min_grupo]).fetchall()}

    u["rf11_pct_prorroga_p90"] = {g: float(p90) for g, p90 in con.execute("""
        SELECT tipo_de_contrato, quantile_cont(rf11_pct_prorroga, 0.90)
        FROM metrics.contratos
        WHERE rf11_pct_prorroga IS NOT NULL AND tipo_de_contrato IS NOT NULL
        GROUP BY 1 HAVING count(*) >= ?""", [min_grupo]).fetchall()}

    row = con.execute("""
        SELECT quantile_cont(rf19_score, 0.90) FROM metrics.entidad_anio
        WHERE rf19_score IS NOT NULL""").fetchone()
    u["rf19_no_evaluable"] = float(row[0]) if row[0] is not None else 1.0

    return u
