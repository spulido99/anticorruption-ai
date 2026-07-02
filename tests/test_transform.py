"""raw -> core: the auditable transformation the whole analysis stands on
(ADRs 0002-0005). Each test encodes a cleaning rule that, if silently changed,
would corrupt red-flag metrics downstream."""

import pytest

from secop.transform import run_transform

URL_NTC = ("https://community.secop.gov.co/Public/Tendering/OpportunityDetail/"
           "Index?noticeUID=CO1.NTC.123456&isFromPublicArea=True")
URL_LOGIN = "https://community.secop.gov.co/STS/Users/Login/Index"


def contrato(sid, **over):
    row = {
        "socrata_id": sid,
        "socrata_updated_at": "2026-07-02T00:00:00.000Z",
        "id_contrato": "CO1.PCCNTR.1",
        "proceso_de_compra": "CO1.BDOS.1",
        "nombre_entidad": "ALCALDIA DE TUNJA",
        "nit_entidad": "800197268",
        "departamento": "Boyacá",
        "ciudad": "Tunja",
        "orden": "Territorial",
        "sector": "Servicio Público",
        "rama": "Ejecutivo",
        "tipodocproveedor": "Cédula de Ciudadanía",
        "documento_proveedor": "1234567",
        "proveedor_adjudicado": "JUAN PEREZ",
        "modalidad_de_contratacion": "Contratación directa",
        "tipo_de_contrato": "Prestación de servicios",
        "estado_contrato": "Activo",
        "fecha_de_firma": "2024-05-06T00:00:00.000",
        "valor_del_contrato": "50000000",
        "urlproceso": URL_NTC,
        "es_grupo": "No",
        "es_pyme": "Si",
    }
    row.update(over)
    return row


def proceso(sid, **over):
    row = {
        "socrata_id": sid,
        "socrata_updated_at": "2026-07-02T00:00:00.000Z",
        "id_del_proceso": "CO1.REQ.1",
        "entidad": "ALCALDIA DE TUNJA",
        "nit_entidad": "800197268",
        "departamento_entidad": "Boyacá",
        "ciudad_entidad": "Tunja",
        "modalidad_de_contratacion": "Licitación pública",
        "adjudicado": "Si",
        "fecha_de_publicacion_del": "2024-03-01T00:00:00.000",
        "proveedores_unicos_con": "1",
        "respuestas_al_procedimiento": "1",
        "precio_base": "100000000",
        "urlproceso": URL_NTC,
        "estado_resumen": "Adjudicado",
    }
    row.update(over)
    return row


@pytest.fixture
def core(con, make_raw_contratos, make_raw_procesos):
    make_raw_contratos([
        # Exact duplicate pair (only socrata_id differs) -> one core row.
        contrato("r1"),
        contrato("r2"),
        # NIT with DV concatenated + placeholder provider doc + absurd value.
        contrato("r3", id_contrato="CO1.PCCNTR.2", nit_entidad="8001972684",
                 documento_proveedor="No Definido", tipodocproveedor="No Definido",
                 proveedor_adjudicado="No Definido",
                 valor_del_contrato="2115000000000000"),
        # Same contractor key under two name spellings; newer, rarer spelling.
        contrato("r4", id_contrato="CO1.PCCNTR.3", documento_proveedor="9003739134",
                 tipodocproveedor="Nit de Persona Jurídica",
                 proveedor_adjudicado="ACME SAS", fecha_de_firma="2023-01-01T00:00:00.000"),
        contrato("r5", id_contrato="CO1.PCCNTR.4", documento_proveedor="900373913",
                 tipodocproveedor="Nit de Persona Jurídica",
                 proveedor_adjudicado="ACME SAS", fecha_de_firma="2024-01-01T00:00:00.000"),
        contrato("r6", id_contrato="CO1.PCCNTR.5", documento_proveedor="900373913",
                 tipodocproveedor="Nit de Persona Jurídica",
                 proveedor_adjudicado="ACME S.A.S.", fecha_de_firma="2025-01-01T00:00:00.000"),
    ])
    make_raw_procesos([
        proceso("p1"),
        proceso("p2"),  # exact duplicate of p1
        proceso("p3", id_del_proceso="CO1.REQ.2", urlproceso=URL_LOGIN,
                estado_resumen="No Definido", adjudicado="No",
                proveedores_unicos_con="No Definido", precio_base="No Definido"),
    ])
    run_transform(con)
    return con


def test_exact_duplicates_collapse(core):
    assert core.execute(
        "SELECT count(*) FROM core.contratos WHERE id_contrato = 'CO1.PCCNTR.1'"
    ).fetchone()[0] == 1
    assert core.execute(
        "SELECT count(*) FROM core.procesos WHERE id_del_proceso = 'CO1.REQ.1'"
    ).fetchone()[0] == 1


def test_nit_normalized_and_notice_uid_materialized(core):
    nits = {r[0] for r in core.execute("SELECT nit_entidad FROM core.contratos").fetchall()}
    assert nits == {"800197268"}  # the DV-concatenated variant was truncated
    uid = core.execute(
        "SELECT notice_uid FROM core.contratos WHERE id_contrato = 'CO1.PCCNTR.1'"
    ).fetchone()[0]
    assert uid == "CO1.NTC.123456"
    # Draft process whose urlproceso is the login page -> no notice_uid.
    assert core.execute(
        "SELECT notice_uid FROM core.procesos WHERE id_del_proceso = 'CO1.REQ.2'"
    ).fetchone()[0] is None


def test_unresolved_contractor_counted_not_dropped(core):
    row = core.execute("""
        SELECT documento_contratista, contratista_resuelto
        FROM core.contratos WHERE id_contrato = 'CO1.PCCNTR.2'
    """).fetchone()
    assert row == (None, False)
    assert core.execute("SELECT count(*) FROM core.contratos").fetchone()[0] == 5


def test_absurd_value_marked_not_deleted(core):
    val, flag = core.execute("""
        SELECT valor_del_contrato, valor_atipico
        FROM core.contratos WHERE id_contrato = 'CO1.PCCNTR.2'
    """).fetchone()
    assert float(val) == 2115000000000000.0  # value kept for traceability
    assert flag is True
    assert core.execute(
        "SELECT count(*) FROM core.contratos WHERE valor_atipico").fetchone()[0] == 1


def test_contratista_master_resolves_canonical_name(core):
    nombre, vistos, n = core.execute("""
        SELECT nombre_canonico, nombres_vistos, n_contratos
        FROM core.contratistas WHERE documento = '900373913'
    """).fetchone()
    assert nombre == "ACME SAS"  # most frequent spelling wins over most recent
    assert set(vistos) == {"ACME SAS", "ACME S.A.S."}
    assert n == 3
    # Canonical name embedded back into the wide table (ADR 0003).
    assert core.execute("""
        SELECT DISTINCT nombre_contratista_canonico FROM core.contratos
        WHERE documento_contratista = '900373913'
    """).fetchall() == [("ACME SAS",)]


def test_entidad_master_spans_contratos_and_procesos(core):
    n_contratos, n_procesos = core.execute("""
        SELECT n_contratos, n_procesos FROM core.entidades WHERE nit_entidad = '800197268'
    """).fetchone()
    assert n_contratos == 5
    assert n_procesos == 2


def test_procesos_typed_fields(core):
    adjudicado, unicos, precio = core.execute("""
        SELECT adjudicado, proveedores_unicos_con, precio_base
        FROM core.procesos WHERE id_del_proceso = 'CO1.REQ.1'
    """).fetchone()
    assert adjudicado is True
    assert unicos == 1
    assert float(precio) == 100000000.0
    # 'No Definido' in numeric fields -> NULL, not a crash.
    assert core.execute("""
        SELECT proveedores_unicos_con, precio_base
        FROM core.procesos WHERE id_del_proceso = 'CO1.REQ.2'
    """).fetchone() == (None, None)


def test_contratos_unicos_view_and_fuente(core):
    assert core.execute("SELECT DISTINCT fuente FROM core.contratos").fetchall() == [("SECOP_II",)]
    # No SECOP I ingested yet: view == table.
    assert core.execute("SELECT count(*) FROM core.contratos_unicos").fetchone()[0] == 5
