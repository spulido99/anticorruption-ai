"""Registry of SECOP datasets on datos.gov.co (Socrata).

Column lists are the published API field names, pinned explicitly because the
ingest selects them together with aliased system fields (:id, :updated_at) —
SODA rejects mixing system fields with `*`.
"""

from dataclasses import dataclass

# System-field aliases prepended to every $select.
SYSTEM_FIELDS = ":id AS socrata_id, :updated_at AS socrata_updated_at"

CONTRATOS_COLUMNS = (
    "nombre_entidad", "nit_entidad", "departamento", "ciudad", "localizaci_n",
    "orden", "sector", "rama", "entidad_centralizada", "proceso_de_compra",
    "id_contrato", "referencia_del_contrato", "estado_contrato",
    "codigo_de_categoria_principal", "descripcion_del_proceso",
    "tipo_de_contrato", "modalidad_de_contratacion",
    "justificacion_modalidad_de", "fecha_de_firma",
    "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato",
    "condiciones_de_entrega", "tipodocproveedor", "documento_proveedor",
    "proveedor_adjudicado", "es_grupo", "es_pyme", "habilita_pago_adelantado",
    "liquidaci_n", "obligaci_n_ambiental", "obligaciones_postconsumo",
    "reversion", "origen_de_los_recursos", "destino_gasto",
    "valor_del_contrato", "valor_de_pago_adelantado", "valor_facturado",
    "valor_pendiente_de_pago", "valor_pagado", "valor_amortizado",
    "valor_pendiente_de", "valor_pendiente_de_ejecucion", "saldo_cdp",
    "saldo_vigencia", "espostconflicto", "dias_adicionados",
    "puntos_del_acuerdo", "pilares_del_acuerdo", "urlproceso",
    "nombre_representante_legal", "nacionalidad_representante_legal",
    "domicilio_representante_legal",
    "tipo_de_identificaci_n_representante_legal",
    "identificaci_n_representante_legal", "g_nero_representante_legal",
    "presupuesto_general_de_la_nacion_pgn", "sistema_general_de_participaciones",
    "sistema_general_de_regal_as",
    "recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_",
    "recursos_de_credito", "recursos_propios", "ultima_actualizacion",
    "codigo_entidad", "codigo_proveedor", "fecha_inicio_liquidacion",
    "fecha_fin_liquidacion", "objeto_del_contrato", "duraci_n_del_contrato",
    "nombre_del_banco", "tipo_de_cuenta", "n_mero_de_cuenta",
    "el_contrato_puede_ser_prorrogado", "fecha_de_notificaci_n_de_prorrogaci_n",
    "nombre_ordenador_del_gasto", "tipo_de_documento_ordenador_del_gasto",
    "n_mero_de_documento_ordenador_del_gasto", "nombre_supervisor",
    "tipo_de_documento_supervisor", "n_mero_de_documento_supervisor",
    "nombre_ordenador_de_pago", "tipo_de_documento_ordenador_de_pago",
    "n_mero_de_documento_ordenador_de_pago", "documentos_tipo",
    "descripcion_documentos_tipo",
)

PROCESOS_COLUMNS = (
    "entidad", "nit_entidad", "departamento_entidad", "ciudad_entidad",
    "ordenentidad", "codigo_pci", "id_del_proceso", "referencia_del_proceso",
    "ppi", "id_del_portafolio", "nombre_del_procedimiento",
    "descripci_n_del_procedimiento", "fase", "fecha_de_publicacion_del",
    "fecha_de_ultima_publicaci", "fecha_de_publicacion_fase",
    "fecha_de_publicacion_fase_1", "fecha_de_publicacion",
    "fecha_de_publicacion_fase_2", "fecha_de_publicacion_fase_3",
    "precio_base", "modalidad_de_contratacion", "justificaci_n_modalidad_de",
    "duracion", "unidad_de_duracion", "fecha_de_recepcion_de",
    "fecha_de_apertura_de_respuesta", "fecha_de_apertura_efectiva",
    "ciudad_de_la_unidad_de", "nombre_de_la_unidad_de",
    "proveedores_invitados", "proveedores_con_invitacion",
    "visualizaciones_del", "proveedores_que_manifestaron",
    "respuestas_al_procedimiento", "respuestas_externas",
    "conteo_de_respuestas_a_ofertas", "proveedores_unicos_con",
    "numero_de_lotes", "estado_del_procedimiento",
    "id_estado_del_procedimiento", "adjudicado", "id_adjudicacion",
    "codigoproveedor", "departamento_proveedor", "ciudad_proveedor",
    "fecha_adjudicacion", "valor_total_adjudicacion", "nombre_del_adjudicador",
    "nombre_del_proveedor", "nit_del_proveedor_adjudicado",
    "codigo_principal_de_categoria", "estado_de_apertura_del_proceso",
    "tipo_de_contrato", "subtipo_de_contrato", "categorias_adicionales",
    "urlproceso", "codigo_entidad", "estado_resumen",
)


@dataclass(frozen=True)
class Dataset:
    key: str
    socrata_id: str
    raw_table: str
    columns: tuple[str, ...]

    @property
    def select_clause(self) -> str:
        return SYSTEM_FIELDS + ", " + ", ".join(self.columns)


CONTRATOS = Dataset(
    key="contratos",
    socrata_id="jbjy-vk9h",
    raw_table="raw.secop2_contratos",
    columns=CONTRATOS_COLUMNS,
)

PROCESOS = Dataset(
    key="procesos",
    socrata_id="p6dx-8zbt",
    raw_table="raw.secop2_procesos",
    columns=PROCESOS_COLUMNS,
)

DATASETS = {d.key: d for d in (CONTRATOS, PROCESOS)}
