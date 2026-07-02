# Analysis asset (wayfinder ticket #7): per-departamento red-flag signal comparison
# to pick the pilot scope for the first publishable finding.
# Server-side SoQL aggregations over the FULL datasets (no sampling), window: 2022-01-01+.
# Run: uv run --with requests python analyze.py   (writes metrics.json next to this file)

import json
import sys
import time
from pathlib import Path

import requests

BASE = "https://www.datos.gov.co/resource"
CONTRACTS = "jbjy-vk9h"  # SECOP II - Contratos Electronicos
PROCESSES = "p6dx-8zbt"  # SECOP II - Procesos
SINCE = "2022-01-01T00:00:00"
DIR = Path(__file__).parent

session = requests.Session()


def soda(dataset: str, params: dict, tries: int = 5):
    for attempt in range(tries):
        r = session.get(f"{BASE}/{dataset}.json", params=params, timeout=300)
        if r.status_code == 429:
            wait = 2 ** (attempt + 2)
            print(f"  429 throttled, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"throttled after {tries} tries: {params}")


metrics: dict = {"window_since": SINCE}

# Modalidades observed in p6dx-8zbt (probed 2026-07-02). RF-01 counts single
# bidding only on competitive procedures (catalog RF-01).
COMPETITIVE = [
    "Licitación pública",
    "Licitación pública Obra Publica",
    "Licitación Pública Acuerdo Marco de Precios",
    "Selección Abreviada de Menor Cuantía",
    "Seleccion Abreviada Menor Cuantia Sin Manifestacion Interes",
    "Selección abreviada subasta inversa",
    "Concurso de méritos abierto",
    "Concurso de méritos con precalificación",
    "Mínima cuantía",
]
COMP_IN = ", ".join("'" + m.replace("'", "''") + "'" for m in COMPETITIVE)

# ---- 1. Contracts: volume + modalidad mix per departamento ------------------
print("== contratos por departamento x modalidad ==", file=sys.stderr)
rows = soda(CONTRACTS, {
    "$select": "departamento, modalidad_de_contratacion as modalidad, count(*) as n, sum(valor_del_contrato) as valor",
    "$where": f"fecha_de_firma >= '{SINCE}'",
    "$group": "departamento, modalidad",
    "$limit": "5000",
})
metrics["contracts_by_dept_modalidad"] = rows

# ---- 2. Contracts: opacity components per departamento ----------------------
print("== opacidad por departamento ==", file=sys.stderr)
metrics["opacity_no_definido"] = soda(CONTRACTS, {
    "$select": "departamento, count(*) as n",
    "$where": f"fecha_de_firma >= '{SINCE}' AND documento_proveedor = 'No Definido'",
    "$group": "departamento", "$limit": "100",
})
metrics["opacity_valor_cero"] = soda(CONTRACTS, {
    "$select": "departamento, count(*) as n",
    "$where": f"fecha_de_firma >= '{SINCE}' AND valor_del_contrato = 0",
    "$group": "departamento", "$limit": "100",
})

# ---- 3. Processes: single bidding per departamento (RF-01) ------------------
print("== single bidding por departamento ==", file=sys.stderr)
base_where = (
    f"fecha_de_publicacion_del >= '{SINCE}' AND adjudicado = 'Si' "
    f"AND modalidad_de_contratacion in ({COMP_IN})"
)
metrics["proc_competitive_adjudicated"] = soda(PROCESSES, {
    "$select": "departamento_entidad as departamento, count(*) as n",
    "$where": base_where,
    "$group": "departamento_entidad", "$limit": "100",
})
metrics["proc_single_bid"] = soda(PROCESSES, {
    "$select": "departamento_entidad as departamento, count(*) as n",
    "$where": base_where + " AND (proveedores_unicos_con = 1 OR respuestas_al_procedimiento = 1)",
    "$group": "departamento_entidad", "$limit": "100",
})

# ---- 4. Provider concentration in top departamentos by value ----------------
# Top provider / top-5 share of contracted value per departamento (excl. placeholders).
by_dept: dict[str, float] = {}
for r in metrics["contracts_by_dept_modalidad"]:
    d = r.get("departamento") or "SIN_DEPTO"
    by_dept[d] = by_dept.get(d, 0.0) + float(r.get("valor") or 0)
top_depts = sorted(by_dept, key=by_dept.get, reverse=True)[:14]
metrics["top_depts_by_value"] = [{"departamento": d, "valor": by_dept[d]} for d in top_depts]

print("== concentración de proveedores (top deptos) ==", file=sys.stderr)
conc = {}
for d in top_depts:
    dd = d.replace("'", "''")
    where = (f"fecha_de_firma >= '{SINCE}' AND departamento = '{dd}' "
             "AND documento_proveedor != 'No Definido'")
    top = soda(CONTRACTS, {
        "$select": "documento_proveedor, proveedor_adjudicado, sum(valor_del_contrato) as valor, count(*) as n",
        "$where": where,
        "$group": "documento_proveedor, proveedor_adjudicado",
        "$order": "valor DESC", "$limit": "5",
    })
    tot = soda(CONTRACTS, {
        "$select": "sum(valor_del_contrato) as valor, count(distinct documento_proveedor) as prov",
        "$where": where,
    })[0]
    conc[d] = {"top5": top, "total_valor": float(tot["valor"] or 0), "proveedores": int(tot["prov"])}
    print(f"  {d}", file=sys.stderr)
metrics["concentration"] = conc

out = DIR / "metrics.json"
out.write_text(json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out}", file=sys.stderr)
