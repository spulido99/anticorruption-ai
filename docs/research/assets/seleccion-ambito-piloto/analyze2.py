# Stage 2 (wayfinder ticket #7): controls and entity/municipio drill-down.
# - Recompute provider concentration capping absurd values (>5e11 COP, digit errors verified)
# - Single-bidding by modalidad (national vs candidates) to rule out composition effects
# - Entity- and municipio-level single bidding inside candidate departamentos
# Run: uv run --with requests python analyze2.py  (writes metrics2.json)

import json
import sys
import time
from pathlib import Path

import requests

BASE = "https://www.datos.gov.co/resource"
CONTRACTS = "jbjy-vk9h"
PROCESSES = "p6dx-8zbt"
SINCE = "2022-01-01T00:00:00"
CAP = 500_000_000_000  # 5e11 COP: above this, single-contract values proved to be digit errors
DIR = Path(__file__).parent
session = requests.Session()


def soda(dataset: str, params: dict, tries: int = 5):
    for attempt in range(tries):
        r = session.get(f"{BASE}/{dataset}.json", params=params, timeout=300)
        if r.status_code == 429:
            time.sleep(2 ** (attempt + 2))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"throttled: {params}")


COMPETITIVE = [
    "Licitación pública", "Licitación pública Obra Publica",
    "Licitación Pública Acuerdo Marco de Precios",
    "Selección Abreviada de Menor Cuantía",
    "Seleccion Abreviada Menor Cuantia Sin Manifestacion Interes",
    "Selección abreviada subasta inversa",
    "Concurso de méritos abierto", "Concurso de méritos con precalificación",
    "Mínima cuantía",
]
COMP_IN = ", ".join("'" + m + "'" for m in COMPETITIVE)
PROC_WHERE = (f"fecha_de_publicacion_del >= '{SINCE}' AND adjudicado = 'Si' "
              f"AND modalidad_de_contratacion in ({COMP_IN})")
SINGLE = " AND (proveedores_unicos_con = 1 OR respuestas_al_procedimiento = 1)"
CANDIDATES = ["Boyacá", "Magdalena", "Antioquia"]

m: dict = {"window_since": SINCE, "value_cap": CAP}

# ---- 1. Single bidding by modalidad: national + candidates ------------------
print("== SB por modalidad ==", file=sys.stderr)
m["sb_modalidad"] = {}
for scope, extra in [("nacional", "")] + [(d, f" AND departamento_entidad = '{d}'") for d in CANDIDATES]:
    den = soda(PROCESSES, {"$select": "modalidad_de_contratacion as mod, count(*) as n",
                           "$where": PROC_WHERE + extra, "$group": "modalidad_de_contratacion", "$limit": "50"})
    num = soda(PROCESSES, {"$select": "modalidad_de_contratacion as mod, count(*) as n",
                           "$where": PROC_WHERE + extra + SINGLE, "$group": "modalidad_de_contratacion", "$limit": "50"})
    m["sb_modalidad"][scope] = {"den": den, "num": num}
    print(f"  {scope}", file=sys.stderr)

# ---- 2. Entity-level single bidding in candidates ----------------------------
print("== SB por entidad ==", file=sys.stderr)
m["sb_entidad"] = {}
for d in CANDIDATES:
    extra = f" AND departamento_entidad = '{d}'"
    den = soda(PROCESSES, {"$select": "entidad, count(*) as n, sum(valor_total_adjudicacion) as v",
                           "$where": PROC_WHERE + extra, "$group": "entidad",
                           "$order": "n DESC", "$limit": "3000"})
    num = soda(PROCESSES, {"$select": "entidad, count(*) as n",
                           "$where": PROC_WHERE + extra + SINGLE, "$group": "entidad", "$limit": "3000"})
    m["sb_entidad"][d] = {"den": den, "num": num}
    print(f"  {d}", file=sys.stderr)

# ---- 3. Municipio-level single bidding in Boyacá -----------------------------
print("== SB por municipio (Boyacá) ==", file=sys.stderr)
extra = " AND departamento_entidad = 'Boyacá'"
m["sb_municipio_boyaca"] = {
    "den": soda(PROCESSES, {"$select": "ciudad_entidad as ciudad, count(*) as n",
                            "$where": PROC_WHERE + extra, "$group": "ciudad_entidad", "$limit": "300"}),
    "num": soda(PROCESSES, {"$select": "ciudad_entidad as ciudad, count(*) as n",
                            "$where": PROC_WHERE + extra + SINGLE, "$group": "ciudad_entidad", "$limit": "300"}),
}

# ---- 4. Concentration with value cap (fix stage-1 artifact) ------------------
print("== concentración con cap ==", file=sys.stderr)
m["concentration_capped"] = {}
for d in ["Distrito Capital de Bogotá", "Antioquia", "Valle del Cauca", "Atlántico",
          "Cundinamarca", "Santander", "Bolívar", "Boyacá", "Meta", "Tolima",
          "Magdalena", "Norte de Santander", "Caldas", "Cesar"]:
    where = (f"fecha_de_firma >= '{SINCE}' AND departamento = '{d}' "
             f"AND documento_proveedor != 'No Definido' AND valor_del_contrato < {CAP}")
    top = soda(CONTRACTS, {"$select": "documento_proveedor, proveedor_adjudicado, sum(valor_del_contrato) as valor, count(*) as n",
                           "$where": where, "$group": "documento_proveedor, proveedor_adjudicado",
                           "$order": "valor DESC", "$limit": "5"})
    tot = soda(CONTRACTS, {"$select": "sum(valor_del_contrato) as valor", "$where": where})[0]
    m["concentration_capped"][d] = {"top5": top, "total_valor": float(tot["valor"] or 0)}
    print(f"  {d}", file=sys.stderr)

# ---- 5. Directa-heavy entities in candidates (contracts, capped) -------------
print("== directa por entidad ==", file=sys.stderr)
m["directa_entidad"] = {}
for d in CANDIDATES:
    base = (f"fecha_de_firma >= '{SINCE}' AND departamento = '{d}' AND valor_del_contrato < {CAP}")
    tot = soda(CONTRACTS, {"$select": "nombre_entidad, count(*) as n, sum(valor_del_contrato) as v",
                           "$where": base, "$group": "nombre_entidad", "$order": "v DESC", "$limit": "2000"})
    dirv = soda(CONTRACTS, {"$select": "nombre_entidad, count(*) as n, sum(valor_del_contrato) as v",
                            "$where": base + " AND modalidad_de_contratacion in ('Contratación directa', 'Contratación Directa (con ofertas)')",
                            "$group": "nombre_entidad", "$limit": "2000"})
    m["directa_entidad"][d] = {"tot": tot, "dir": dirv}
    print(f"  {d}", file=sys.stderr)

(DIR / "metrics2.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote metrics2.json", file=sys.stderr)
