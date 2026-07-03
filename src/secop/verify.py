"""Post-load verification: raw counts against the live API, and reproduction
of the pilot-selection numbers (#7) that are the operational success criterion
for the v1 ingest (#12)."""

from .datasets import DATASETS
from .ingest import get_state

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

# Reference values from docs/research/seleccion-ambito-piloto.md (#7),
# computed 2026-07-02 over the live API. #7's semantics, reverse-checked
# against its committed metrics.json: API row grain (no dedup), uncapped value
# sums, and 'directa' = exactly the two direct-contracting modalidades.
# Counts drift a few rows per daily dataset update; percentages are stable.
EXPECTED = {
    "boyaca_competitivos": 19_736,
    "boyaca_sb_pct": 54.7,
    "narino_sb_pct": 9.4,
    "boyaca_valor_bn": 14.1,
    "boyaca_directa_pct": 34.7,
}


def check_counts(con, client):
    """Compare raw row counts with live API counts per dataset."""
    results = {}
    for key, ds in DATASETS.items():
        st = get_state(con, key)
        if st is None or not st["complete"]:
            results[key] = {"status": "not loaded", "state": st}
            continue
        local = con.execute(f"SELECT count(*) FROM {ds.raw_table}").fetchone()[0]
        api = client.count(ds, where=st["where_sql"] or None)
        results[key] = {"local": local, "api": api, "diff": local - api}
    return results


def _sb(con, departamento):
    # Raw grain: #7 counted API rows, before core's exact-duplicate removal.
    comp = ", ".join(f"'{m}'" for m in COMPETITIVE)
    dept_filter = "" if departamento is None else \
        f"AND departamento_entidad = '{departamento}'"
    n, single = con.execute(f"""
        SELECT count(*),
               count(*) FILTER (TRY_CAST(proveedores_unicos_con AS INT) = 1
                                OR TRY_CAST(respuestas_al_procedimiento AS INT) = 1)
        FROM raw.secop2_procesos
        WHERE fecha_de_publicacion_del >= '2022-01-01'
          AND adjudicado = 'Si'
          AND modalidad_de_contratacion IN ({comp})
          {dept_filter}
    """).fetchone()
    return {"competitivos": n, "single_bid": single,
            "sb_pct": round(100.0 * single / n, 1) if n else None}


def reproduce_pilot_numbers(con):
    """Recompute the #7 anchor numbers from core; returns got-vs-expected."""
    boyaca = _sb(con, "Boyacá")
    narino = _sb(con, "Nariño")
    nacional = _sb(con, None)

    valor_bn, directa_pct = con.execute("""
        SELECT round(sum(TRY_CAST(valor_del_contrato AS DECIMAL(24,2))) / 1e12, 1),
               round(100.0 * sum(TRY_CAST(valor_del_contrato AS DECIMAL(24,2)))
                         FILTER (modalidad_de_contratacion IN
                                 ('Contratación directa',
                                  'Contratación Directa (con ofertas)'))
                     / sum(TRY_CAST(valor_del_contrato AS DECIMAL(24,2))), 1)
        FROM raw.secop2_contratos
        WHERE departamento = 'Boyacá' AND fecha_de_firma >= '2022-01-01'
    """).fetchone()

    return {
        "boyaca_competitivos": {"got": boyaca["competitivos"],
                                "expected": EXPECTED["boyaca_competitivos"]},
        "boyaca_sb_pct": {"got": boyaca["sb_pct"],
                          "expected": EXPECTED["boyaca_sb_pct"]},
        "narino_sb_pct": {"got": narino["sb_pct"],
                          "expected": EXPECTED["narino_sb_pct"]},
        "nacional_sb_pct": {"got": nacional["sb_pct"], "expected": "~27"},
        "boyaca_valor_bn": {"got": float(valor_bn) if valor_bn is not None else None,
                            "expected": EXPECTED["boyaca_valor_bn"]},
        "boyaca_directa_pct": {"got": float(directa_pct) if directa_pct is not None else None,
                               "expected": EXPECTED["boyaca_directa_pct"]},
    }
