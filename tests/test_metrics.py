"""core -> metrics: the precomputed red-flag layer skills read (#8: no number
enters a finding without coming from `metrics`). Each test encodes a ficha
rule from docs/research/red-flags-contratacion.md whose silent change would
flip flags downstream."""

import pytest

from secop.metrics import run_metrics
from secop.transform import run_transform

URL_NTC = ("https://community.secop.gov.co/Public/Tendering/OpportunityDetail/"
           "Index?noticeUID=CO1.NTC.123456&isFromPublicArea=True")


def proceso(sid, **over):
    row = {
        "socrata_id": sid,
        "socrata_updated_at": "2026-07-02T00:00:00.000Z",
        "id_del_proceso": f"CO1.REQ.{sid}",
        "entidad": "ALCALDIA DE TUNJA",
        "nit_entidad": "800197268",
        "departamento_entidad": "Boyacá",
        "ciudad_entidad": "Tunja",
        "modalidad_de_contratacion": "Licitación pública",
        "adjudicado": "Si",
        "fecha_de_publicacion_del": "2024-03-01T00:00:00.000",
        "fecha_adjudicacion": "2024-05-10T00:00:00.000",
        "proveedores_unicos_con": "3",
        "respuestas_al_procedimiento": "3",
        "nombre_del_proveedor": "ACME SAS",
        "nit_del_proveedor_adjudicado": "900373913",
        "urlproceso": URL_NTC,
        "estado_resumen": "Adjudicado",
    }
    row.update(over)
    return row


def contrato(sid, **over):
    row = {
        "socrata_id": sid,
        "socrata_updated_at": "2026-07-02T00:00:00.000Z",
        "id_contrato": f"CO1.PCCNTR.{sid}",
        "nombre_entidad": "ALCALDIA DE TUNJA",
        "nit_entidad": "800197268",
        "departamento": "Boyacá",
        "ciudad": "Tunja",
        "orden": "Territorial",
        "sector": "Servicio Público",
        "tipodocproveedor": "Nit de Persona Jurídica",
        "documento_proveedor": "900373913",
        "proveedor_adjudicado": "ACME SAS",
        "modalidad_de_contratacion": "Licitación pública",
        "tipo_de_contrato": "Obra",
        "estado_contrato": "Activo",
        "fecha_de_firma": "2024-05-06T00:00:00.000",
        "valor_del_contrato": "100000000",
        "urlproceso": URL_NTC,
        "es_grupo": "No",
    }
    row.update(over)
    return row


# Thresholds injected directly (the national JSON is calibrated separately);
# values chosen so fixture cases fall on both sides of each cutoff.
UMBRALES = {
    "rf01_min_procesos": 2,
    "rf01_share_outlier": {"Territorial": 0.60},
    "rf02_pct_directa_valor_outlier": {"Territorial": 0.70},
    "rf05_min_contratos_12m": 2,
    "rf05_share_outlier": 0.40,
    "rf06_hhi_alto": 0.25,
    "rf06_min_contratos": 2,
    "rf06_min_contratistas": 2,
    "rf07_ventana": {"Licitación pública|2024": {"p05": 15, "p95": 200}},
    "rf08_pct_diciembre_p90": {"Territorial": 0.50},
    "rf08_preelectoral_p90": {"Territorial": 3.0},
    "rf11_min_pct": 0.5,
    "rf11_pct_prorroga_p90": {"Obra": 0.30},
    "rf19_no_evaluable": 0.20,
}

V_ATIPICO = "600000000000"  # above the 5e11 digitation-error cap


@pytest.fixture
def metrics(con, make_raw_contratos, make_raw_procesos):
    make_raw_contratos([
        # -- Entity A (800197268): RF-02 variants and RF-06 concentration.
        contrato("c1"),  # licitación, Obra, 100M, ACME
        contrato("c2", modalidad_de_contratacion="Contratación directa",
                 tipo_de_contrato="Prestación de servicios",
                 tipodocproveedor="Cédula de Ciudadanía",
                 documento_proveedor="1234567", proveedor_adjudicado="JUAN PEREZ",
                 valor_del_contrato="300000000"),
        contrato("c3", modalidad_de_contratacion="Contratación directa",
                 documento_proveedor="800123456", proveedor_adjudicado="OTRO SAS",
                 valor_del_contrato="400000000"),
        # -- Entity B (800000001): RF-08 December concentration.
        contrato("d1", nit_entidad="800000001", nombre_entidad="ALCALDIA B",
                 fecha_de_firma="2024-12-15T00:00:00.000",
                 valor_del_contrato="600000000"),
        contrato("d2", nit_entidad="800000001", nombre_entidad="ALCALDIA B",
                 fecha_de_firma="2024-03-10T00:00:00.000",
                 valor_del_contrato="400000000"),
        # -- Entity C (800000002): RF-19 opacity -> no evaluable.
        contrato("x1", nit_entidad="800000002", nombre_entidad="ALCALDIA C",
                 tipodocproveedor="No Definido", documento_proveedor="No Definido",
                 proveedor_adjudicado="No Definido"),
        contrato("x2", nit_entidad="800000002", nombre_entidad="ALCALDIA C",
                 tipodocproveedor="No Definido", documento_proveedor="No Definido",
                 proveedor_adjudicado="No Definido"),
        contrato("x3", nit_entidad="800000002", nombre_entidad="ALCALDIA C",
                 tipodocproveedor="Cédula de Ciudadanía",
                 documento_proveedor="1234567", proveedor_adjudicado="JUAN PEREZ",
                 valor_del_contrato="0"),
        contrato("x4", nit_entidad="800000002", nombre_entidad="ALCALDIA C",
                 valor_del_contrato=V_ATIPICO),
        # -- Entity D (800000003): RF-05 trailing-12m winner share.
        contrato("w1", nit_entidad="800000003", nombre_entidad="ALCALDIA D",
                 fecha_de_firma="2024-01-10T00:00:00.000",
                 valor_del_contrato="100000000"),
        contrato("w2", nit_entidad="800000003", nombre_entidad="ALCALDIA D",
                 fecha_de_firma="2024-06-10T00:00:00.000",
                 valor_del_contrato="500000000"),
        contrato("w3", nit_entidad="800000003", nombre_entidad="ALCALDIA D",
                 documento_proveedor="800123456", proveedor_adjudicado="OTRO SAS",
                 fecha_de_firma="2023-08-10T00:00:00.000",
                 valor_del_contrato="300000000"),
        # Unresolved contractor: counts in the entity denominator (its spend
        # is real), can never be a pair.
        contrato("w4", nit_entidad="800000003", nombre_entidad="ALCALDIA D",
                 tipodocproveedor="No Definido", documento_proveedor="No Definido",
                 proveedor_adjudicado="No Definido",
                 fecha_de_firma="2024-03-10T00:00:00.000",
                 valor_del_contrato="400000000"),
        # Digitation-error value: excluded from both sides of the share.
        contrato("w5", nit_entidad="800000003", nombre_entidad="ALCALDIA D",
                 fecha_de_firma="2024-05-10T00:00:00.000",
                 valor_del_contrato=V_ATIPICO),
        # -- Entity E (800000004): RF-11 time additions.
        contrato("r1", nit_entidad="800000004", nombre_entidad="ALCALDIA E",
                 fecha_de_inicio_del_contrato="2024-01-01T00:00:00.000",
                 fecha_de_fin_del_contrato="2024-12-31T00:00:00.000",
                 dias_adicionados="150"),
        contrato("r2", nit_entidad="800000004", nombre_entidad="ALCALDIA E",
                 fecha_de_inicio_del_contrato="2024-01-01T00:00:00.000",
                 fecha_de_fin_del_contrato="2024-12-31T00:00:00.000",
                 dias_adicionados="60"),
        contrato("r3", nit_entidad="800000004", nombre_entidad="ALCALDIA E"),
        contrato("r4", nit_entidad="800000004", nombre_entidad="ALCALDIA E",
                 fecha_de_inicio_del_contrato="2024-01-01T00:00:00.000",
                 fecha_de_fin_del_contrato="2024-12-31T00:00:00.000",
                 dias_adicionados="0"),
        # -- Entity F (800000005): RF-08 pre-election spike. Ley de Garantías
        # restriction for the 2022-05-29 election starts 2022-01-29; the two
        # months before it hold 500M of 720M of trailing-12m direct value.
        contrato("f1", nit_entidad="800000005", nombre_entidad="GOBERNACION F",
                 modalidad_de_contratacion="Contratación directa",
                 fecha_de_firma="2021-12-15T00:00:00.000",
                 valor_del_contrato="500000000"),
        contrato("f2", nit_entidad="800000005", nombre_entidad="GOBERNACION F",
                 modalidad_de_contratacion="Contratación directa",
                 fecha_de_firma="2021-06-15T00:00:00.000",
                 valor_del_contrato="100000000"),
        contrato("f3", nit_entidad="800000005", nombre_entidad="GOBERNACION F",
                 modalidad_de_contratacion="Contratación directa",
                 fecha_de_firma="2021-03-10T00:00:00.000",
                 valor_del_contrato="120000000"),
    ])
    make_raw_procesos([
        # Competitive, awarded, one distinct bidder -> RF-01 flag; and a
        # 10-day publication->award window, below p05=15 -> RF-07 'corta'.
        proceso("p1", proveedores_unicos_con="1", respuestas_al_procedimiento="1",
                fecha_adjudicacion="2024-03-11T00:00:00.000"),
        # Competitive, awarded, 3 bidders, 70-day window -> no flags.
        proceso("p2"),
        # Direct contracting: outside the competitive universe -> RF-01 NULL.
        proceso("p3", modalidad_de_contratacion="Contratación directa",
                proveedores_unicos_con="1", respuestas_al_procedimiento="1"),
        # Competitive but not awarded -> excluded from the RF-01 denominator.
        proceso("p4", adjudicado="No", fecha_adjudicacion=None,
                proveedores_unicos_con="0", respuestas_al_procedimiento="2"),
        # unicos NULL but a single response -> still single bid (OR rule),
        # 300-day window, above p95=200 -> RF-07 'larga'.
        proceso("p5", proveedores_unicos_con="No Definido",
                respuestas_al_procedimiento="1",
                fecha_adjudicacion="2024-12-26T00:00:00.000"),
        # Entities G (0% single bid) and H (100%) widen the Territorial
        # share distribution for the calibration test. No award date, so
        # they stay out of the RF-07 day quantiles.
        proceso("g1", nit_entidad="800000006", entidad="ALCALDIA G",
                ordenentidad="Territorial", fecha_adjudicacion=None),
        proceso("h1", nit_entidad="800000007", entidad="ALCALDIA H",
                ordenentidad="Territorial", fecha_adjudicacion=None,
                proveedores_unicos_con="1", respuestas_al_procedimiento="1"),
    ])
    run_transform(con)
    run_metrics(con, UMBRALES)
    return con


def _row(con, sid, cols):
    return con.execute(
        f"SELECT {cols} FROM metrics.procesos WHERE id_del_proceso = 'CO1.REQ.{sid}'"
    ).fetchone()


def test_rf01_single_bid_only_in_competitive_awarded_universe(metrics):
    # Ficha RF-01: flag = competitive modalidad AND adjudicado AND
    # (proveedores_unicos_con = 1 OR respuestas_al_procedimiento = 1).
    assert _row(metrics, "p1", "es_competitivo, rf01_single_bid") == (True, True)
    assert _row(metrics, "p2", "es_competitivo, rf01_single_bid") == (True, False)
    # Direct contracting can never be "single bidding": NULL, not False.
    assert _row(metrics, "p3", "es_competitivo, rf01_single_bid") == (False, None)
    # Not awarded: out of the denominator (the #7 lesson).
    assert _row(metrics, "p4", "es_competitivo, rf01_single_bid") == (True, None)
    assert _row(metrics, "p5", "rf01_single_bid") == (True,)


def test_rf07_window_flagged_against_modalidad_year_percentiles(metrics):
    # Ficha RF-07: dias = fecha_adjudicacion - fecha_de_publicacion; flag
    # outside [p05, p95] of the modalidad x year group.
    assert _row(metrics, "p1", "rf07_dias, rf07_ventana") == (10, "corta")
    assert _row(metrics, "p2", "rf07_dias, rf07_ventana") == (70, None)
    assert _row(metrics, "p5", "rf07_dias, rf07_ventana") == (300, "larga")
    # No award date -> no window, no flag.
    assert _row(metrics, "p4", "rf07_dias, rf07_ventana") == (None, None)


def _entidad(con, nit, cols, anio=2024):
    return con.execute(
        f"SELECT {cols} FROM metrics.entidad_anio "
        f"WHERE nit_entidad = '{nit}' AND anio = {anio}"
    ).fetchone()


def test_rf01_entity_share_over_awarded_competitive_only(metrics):
    # Entity A: 3 awarded competitive processes (p1, p2, p5), 2 single bid.
    n, sb, share, flag = _entidad(
        metrics, "800197268",
        "rf01_n_competitivos, rf01_n_single_bid, rf01_share, rf01_flag")
    assert (n, sb) == (3, 2)
    assert share == pytest.approx(2 / 3)
    assert flag is True  # > 0.60 cutoff for Territorial, n >= min
    # Entity B has no processes at all: not evaluable for RF-01 -> NULL.
    assert _entidad(metrics, "800000001", "rf01_flag") == (None,)


def test_rf02_directa_share_with_strict_variant(metrics):
    # Ficha RF-02: report count and value shares, plus the strict variant
    # excluding prestación de servicios (direct by legal design).
    row = _entidad(metrics, "800197268",
                   "rf02_pct_directa_n, rf02_pct_directa_valor, "
                   "rf02_pct_directa_n_estricta, rf02_pct_directa_valor_estricta, "
                   "rf02_flag")
    assert row[0] == pytest.approx(2 / 3)
    assert row[1] == pytest.approx(700 / 800)   # the robust variant
    assert row[2] == pytest.approx(1 / 3)
    assert row[3] == pytest.approx(400 / 800)
    assert row[4] is True  # value share 0.875 > 0.70


def test_rf06_hhi_squares_contractor_value_shares(metrics):
    # Entity A 2024: ACME 100M, JUAN 300M, OTRO 400M of 800M.
    hhi, n, flag = _entidad(
        metrics, "800197268", "rf06_hhi, rf06_n_contratistas, rf06_flag")
    assert hhi == pytest.approx(0.125**2 + 0.375**2 + 0.5**2)
    assert n == 3
    assert flag is True  # 0.406 > 0.25, mins satisfied


def test_rf08_december_value_share(metrics):
    pct, flag = _entidad(metrics, "800000001",
                         "rf08_pct_diciembre, rf08_flag")
    assert pct == pytest.approx(0.6)
    assert flag is True
    # Entity A signed nothing in December.
    pct_a, flag_a = _entidad(metrics, "800197268",
                             "rf08_pct_diciembre, rf08_flag")
    assert pct_a == pytest.approx(0.0)
    assert flag_a is False


def test_rf08_preelectoral_spike_lands_on_election_year(metrics):
    # Entity F: 500M of direct value in the 2 months before the 2022-01-29
    # Ley de Garantías restriction vs 720M/12 monthly average -> ratio 4.17.
    ratio, flag = _entidad(metrics, "800000005",
                           "rf08_ratio_preelectoral, rf08_flag_preelectoral",
                           anio=2022)
    assert ratio == pytest.approx((500 / 2) / (720 / 12), rel=1e-6)
    assert flag is True


def test_rf19_opacity_score_marks_no_evaluable_not_clean(metrics):
    # Entity C: 2/4 unresolved contractors, 1/4 zero value, 1/4 absurd value.
    row = _entidad(metrics, "800000002",
                   "rf19_pct_contratistas_no_resueltos, rf19_pct_valor_cero, "
                   "rf19_pct_valor_atipico, rf19_score, rf19_no_evaluable")
    assert row[0] == pytest.approx(0.5)
    assert row[1] == pytest.approx(0.25)
    assert row[2] == pytest.approx(0.25)
    assert row[3] == pytest.approx((0.5 + 0.25 + 0.25) / 3)
    assert row[4] is True
    # Opaque entity is "no evaluable", never "clean": its RF-06 has no sane
    # denominator and must stay NULL, not become a reassuring False.
    assert _entidad(metrics, "800000002", "rf06_hhi") == (None,)
    # A clean entity scores 0 and stays evaluable.
    score, ne = _entidad(metrics, "800197268", "rf19_score, rf19_no_evaluable")
    assert score == pytest.approx(0.0)
    assert ne is False


def test_rf11_prorroga_relative_to_original_term(metrics):
    # fecha_de_fin already includes the addition (verified on the national
    # load: <0.6% of contracts contradict it), so the original term is
    # (fin - inicio) - dias_adicionados.
    rows = {r[0]: r[1:] for r in metrics.execute("""
        SELECT id_contrato, plazo_original_dias, rf11_pct_prorroga, rf11_flag
        FROM metrics.contratos WHERE nit_entidad = '800000004'
    """).fetchall()}
    plazo, pct, flag = rows["CO1.PCCNTR.r1"]
    assert plazo == 215  # 365 - 150
    assert pct == pytest.approx(150 / 215)
    assert flag is True  # > 0.5 and > p90 for Obra
    plazo, pct, flag = rows["CO1.PCCNTR.r2"]
    assert pct == pytest.approx(60 / 305)
    assert flag is False
    assert rows["CO1.PCCNTR.r4"][1] == pytest.approx(0.0)
    assert rows["CO1.PCCNTR.r4"][2] is False
    # No dates -> nothing to measure.
    assert rows["CO1.PCCNTR.r3"] == (None, None, None)


def _par(con, mes, contratista="900373913"):
    return con.execute(f"""
        SELECT valor_12m, valor_entidad_12m, n_contratos_entidad_12m,
               rf05_share, rf05_flag
        FROM metrics.entidad_contratista_12m
        WHERE nit_entidad = '800000003' AND mes = DATE '{mes}'
          AND contratista_key LIKE '%:{contratista}'
    """).fetchone()


def test_rf05_trailing_12m_share_with_exclusions(metrics):
    # Ficha RF-05: share over a 12-month window; unresolved contractors stay
    # in the entity denominator, digitation-error values leave both sides.
    v, vt, n, share, flag = _par(metrics, "2024-06-01")
    assert float(v) == 600_000_000  # ACME: 100M (Jan) + 500M (Jun)
    assert float(vt) == 1_300_000_000  # + OTRO 300M + unresolved 400M, no atipico
    assert n == 4
    assert share == pytest.approx(600 / 1300)
    assert flag is True  # > 0.40, entity has >= 2 contracts in window
    # In January the window ends before the June spike: share 100/400.
    v, vt, n, share, flag = _par(metrics, "2024-01-01")
    assert share == pytest.approx(100 / 400)
    assert flag is False
    # A pair whose window holds a single entity contract: below the activity
    # floor -> NULL, not a 100%-share alarm.
    v, vt, n, share, flag = _par(metrics, "2023-08-01", contratista="800123456")
    assert share == pytest.approx(1.0)
    assert n == 1
    assert flag is None


def test_build_info_records_umbrales_for_traceability(metrics):
    import json
    built_at, umbrales_json = metrics.execute(
        "SELECT built_at, umbrales FROM metrics.build_info").fetchone()
    assert built_at is not None
    assert json.loads(umbrales_json) == UMBRALES


def test_calibrate_derives_cutoffs_from_the_loaded_distribution(metrics):
    from secop.metrics import calibrate

    # Group-size floors lowered so the fixture's tiny groups participate.
    u = calibrate(metrics, min_grupo=1, min_procesos=1, min_contratos=1)
    # Territorial single-bid shares: G 0, A 2/3, H 1. Q3 + 1.5*IQR = 1.58
    # would make the flag unfireable (shares live in [0,1]), so the cutoff
    # caps at the group's P95 = 2/3 + 0.9*(1 - 2/3). Verified on the national
    # load: the uncapped rule emits 1.28 for Territorial.
    assert u["rf01_share_outlier"]["Territorial"] == pytest.approx(2 / 3 + 0.9 / 3)
    # RF-05's pair-month grain is dominated by micro-pairs (national P75
    # ~0.1%), so an IQR cutoff flags everything: the share cutoff is the
    # normative 40% (OCP R040's example), not calibrated.
    assert u["rf05_share_outlier"] == 0.4
    # RF-07 percentiles over [10, 70, 300] days (linear interpolation).
    v = u["rf07_ventana"]["Licitación pública|2024"]
    assert v["p05"] == pytest.approx(16.0)   # 10 + 0.1 * 60
    assert v["p95"] == pytest.approx(277.0)  # 70 + 0.9 * 230
    # Normative constants ride along so the JSON is self-contained.
    assert u["rf06_hhi_alto"] == 0.25
    assert u["rf11_min_pct"] == 0.5
    # The result must be JSON-serializable as-is (it gets versioned).
    import json
    json.loads(json.dumps(u))
