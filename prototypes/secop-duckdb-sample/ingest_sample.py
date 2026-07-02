# Throwaway prototype (wayfinder ticket #5): ingest a stratified sample of SECOP II
# into DuckDB and emit raw quality metrics to metrics.json.
# Run: uv run --with duckdb,requests python ingest_sample.py
# No app token: shared per-IP pool, may hit 429 (handled with backoff).

import json
import re
import time
from pathlib import Path

import duckdb
import requests

BASE = "https://www.datos.gov.co/resource"
CONTRACTS = "jbjy-vk9h"  # SECOP II - Contratos Electronicos (5.66M rows)
PROCESSES = "p6dx-8zbt"  # SECOP II - Procesos (8.75M rows)
DIR = Path(__file__).parent
DATA = DIR / "data"
DATA.mkdir(exist_ok=True)
ROWS_PER_YEAR = 10_000
YEARS = range(2015, 2027)

session = requests.Session()
metrics: dict = {"api": {}, "sample": {}, "feasibility": {}}


def soda_json(dataset: str, params: dict, tries: int = 4):
    for attempt in range(tries):
        r = session.get(f"{BASE}/{dataset}.json", params=params, timeout=180)
        if r.status_code == 429:
            wait = 2 ** (attempt + 2)
            print(f"  429 throttled, waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"throttled after {tries} tries: {params}")


# ---------------------------------------------------------------- server-side
# Full-dataset stats via SoQL: count(col) counts non-null, so null rates over
# ALL 5.66M rows come from one aggregation instead of sample extrapolation.
print("== Server-side full-dataset stats (jbjy-vk9h) ==")
KEY_COLS = [
    "nit_entidad", "documento_proveedor", "tipodocproveedor",
    "proveedor_adjudicado", "id_contrato", "proceso_de_compra",
    "valor_del_contrato", "valor_pagado", "fecha_de_firma",
    "fecha_de_inicio_del_contrato", "urlproceso", "codigo_proveedor",
    "nombre_supervisor", "objeto_del_contrato", "departamento",
]
sel = "count(*) as total, " + ", ".join(f"count({c}) as nn_{c}" for c in KEY_COLS)
row = soda_json(CONTRACTS, {"$select": sel})[0]
total = int(row["total"])
metrics["api"]["total_rows"] = total
metrics["api"]["non_null"] = {c: int(row[f"nn_{c}"]) for c in KEY_COLS}
print(f"  total rows: {total:,}")

# Placeholder values that mean NULL, counted server-side.
# nit_entidad is a number column here, so its quality issue is >9 digits (check
# digit concatenated), not a 'No Definido' placeholder.
placeholders = {}
for col, val in [
    ("documento_proveedor", "No Definido"),
    ("tipodocproveedor", "No Definido"),
]:
    n = soda_json(CONTRACTS, {"$select": "count(*) as n", "$where": f"{col} = '{val}'"})[0]["n"]
    placeholders[col] = int(n)
    print(f"  {col} = '{val}': {int(n):,}")
metrics["api"]["placeholders"] = placeholders

nit_long = soda_json(CONTRACTS, {"$select": "count(*) as n", "$where": "nit_entidad > 999999999"})[0]["n"]
metrics["api"]["nit_entidad_over_9_digits"] = int(nit_long)
print(f"  nit_entidad > 9 digits: {int(nit_long):,}")

zero_val = soda_json(CONTRACTS, {"$select": "count(*) as n", "$where": "valor_del_contrato = 0"})[0]["n"]
metrics["api"]["valor_zero"] = int(zero_val)
neg_val = soda_json(CONTRACTS, {"$select": "count(*) as n", "$where": "valor_del_contrato < 0"})[0]["n"]
metrics["api"]["valor_negative"] = int(neg_val)

by_year = soda_json(CONTRACTS, {
    "$select": "date_extract_y(fecha_de_firma) as y, count(*) as n",
    "$group": "y", "$order": "y",
})
metrics["api"]["rows_by_firma_year"] = {str(r.get("y")): int(r["n"]) for r in by_year}
print(f"  years with contracts: {[r.get('y') for r in by_year]}")

# Duplicate natural key check, server-side (may be slow; tolerate failure).
try:
    dup = soda_json(CONTRACTS, {
        "$select": "id_contrato, count(*) as n",
        "$group": "id_contrato", "$having": "n > 1", "$limit": "10",
    })
    metrics["api"]["dup_id_contrato_sample"] = dup
    print(f"  duplicated id_contrato (first 10): {len(dup)}")
except Exception as e:  # noqa: BLE001 - prototype: record and move on
    metrics["api"]["dup_id_contrato_sample"] = f"query failed: {e}"

# ------------------------------------------------------------------- download
print("== Downloading stratified sample (contracts, per signature year) ==")
t0 = time.time()
downloaded_bytes = 0
for y in YEARS:
    out = DATA / f"contracts_{y}.csv"
    if out.exists():
        downloaded_bytes += out.stat().st_size
        continue
    params = {
        "$where": f"fecha_de_firma >= '{y}-01-01T00:00:00' AND fecha_de_firma < '{y + 1}-01-01T00:00:00'",
        "$order": "id_contrato",
        "$limit": str(ROWS_PER_YEAR),
    }
    for attempt in range(4):
        r = session.get(f"{BASE}/{CONTRACTS}.csv", params=params, timeout=300)
        if r.status_code == 429:
            time.sleep(2 ** (attempt + 2))
            continue
        r.raise_for_status()
        out.write_bytes(r.content)
        downloaded_bytes += len(r.content)
        print(f"  {y}: {len(r.content) / 1e6:.1f} MB")
        break
    else:
        print(f"  {y}: FAILED (throttled)")

out = DATA / "processes_recent.csv"
if not out.exists():
    r = session.get(f"{BASE}/{PROCESSES}.csv", params={
        "$order": "fecha_de_publicacion_del DESC",
        "$limit": "20000",
    }, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)
downloaded_bytes += out.stat().st_size
dl_secs = time.time() - t0
metrics["feasibility"]["download_bytes"] = downloaded_bytes
metrics["feasibility"]["download_secs"] = round(dl_secs, 1)
print(f"  total {downloaded_bytes / 1e6:.0f} MB in {dl_secs:.0f}s "
      f"({downloaded_bytes / max(dl_secs, 1) / 1e6:.1f} MB/s)")

# -------------------------------------------------------------------- duckdb
print("== Loading into DuckDB and profiling ==")
db_path = DIR / "secop_sample.duckdb"
db_path.unlink(missing_ok=True)
con = duckdb.connect(str(db_path))
# all_varchar: profile raw strings as published, cast explicitly in queries
con.execute(f"""
    CREATE TABLE contracts AS
    SELECT * FROM read_csv_auto('{(DATA / "contracts_*.csv").as_posix()}',
                                all_varchar=true, union_by_name=true)
""")
con.execute(f"""
    CREATE TABLE processes AS
    SELECT * FROM read_csv_auto('{(DATA / "processes_recent.csv").as_posix()}',
                                all_varchar=true)
""")
s: dict = {}
s["contracts_rows"] = con.sql("SELECT count(*) FROM contracts").fetchone()[0]
s["processes_rows"] = con.sql("SELECT count(*) FROM processes").fetchone()[0]
s["contracts_cols"] = len(con.sql("SELECT * FROM contracts LIMIT 0").columns)

s["dup_id_contrato_in_sample"] = con.sql("""
    SELECT count(*) FROM (
      SELECT id_contrato FROM contracts GROUP BY id_contrato HAVING count(*) > 1)
""").fetchone()[0]

# NIT length distribution (entity NIT should be 9 digits without check digit)
s["nit_entidad_length_dist"] = {
    str(k): v for k, v in con.sql("""
      SELECT length(regexp_replace(nit_entidad, '[^0-9]', '', 'g')) AS len, count(*) AS n
      FROM contracts GROUP BY len ORDER BY n DESC
    """).fetchall()
}
s["nit_entidad_non_numeric"] = con.sql("""
    SELECT count(*) FROM contracts WHERE nit_entidad !~ '^[0-9]+$'
""").fetchone()[0]

# documento_proveedor quality within sample
s["doc_proveedor_placeholder"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE documento_proveedor IN ('No Definido', 'No Aplica', '0') OR documento_proveedor IS NULL
""").fetchone()[0]
s["doc_proveedor_non_numeric"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE documento_proveedor IS NOT NULL AND documento_proveedor !~ '^[0-9]+$'
""").fetchone()[0]

# Dates: parse failures and out-of-range values
s["fecha_firma_unparseable"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE fecha_de_firma IS NOT NULL AND try_cast(fecha_de_firma AS TIMESTAMP) IS NULL
""").fetchone()[0]
s["fecha_inicio_out_of_range"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE try_cast(fecha_de_inicio_del_contrato AS TIMESTAMP) IS NOT NULL
      AND (try_cast(fecha_de_inicio_del_contrato AS TIMESTAMP) < '1990-01-01'
           OR try_cast(fecha_de_inicio_del_contrato AS TIMESTAMP) > '2046-01-01')
""").fetchone()[0]

# Values: castability and magnitude sanity
s["valor_unparseable"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE try_cast(valor_del_contrato AS DECIMAL(38,2)) IS NULL
""").fetchone()[0]
s["valor_over_1e12"] = con.sql("""
    SELECT count(*) FROM contracts
    WHERE try_cast(valor_del_contrato AS DECIMAL(38,2)) > 1000000000000
""").fetchone()[0]

# noticeUID (CO1.NTC.*) embedded in urlproceso is THE join key contracts<->processes
s["contracts_noticeuid_extractable"] = con.sql(r"""
    SELECT count(*) FROM contracts
    WHERE regexp_extract(urlproceso, 'CO1\.NTC\.[0-9]+') != ''
""").fetchone()[0]
s["processes_noticeuid_extractable"] = con.sql(r"""
    SELECT count(*) FROM processes
    WHERE regexp_extract(urlproceso, 'CO1\.NTC\.[0-9]+') != ''
""").fetchone()[0]

# ID format invariants claimed by the research doc
s["id_contrato_pccntr_pct"] = con.sql("""
    SELECT round(100.0 * count(*) FILTER (id_contrato LIKE 'CO1.PCCNTR.%') / count(*), 2)
    FROM contracts
""").fetchone()[0]
s["proceso_bdos_pct"] = con.sql("""
    SELECT round(100.0 * count(*) FILTER (proceso_de_compra LIKE 'CO1.BDOS.%') / count(*), 2)
    FROM contracts
""").fetchone()[0]

metrics["sample"] = {k: (float(v) if hasattr(v, "as_integer_ratio") and not isinstance(v, int) else v)
                     for k, v in s.items()}

con.close()
db_bytes = db_path.stat().st_size
metrics["feasibility"]["duckdb_bytes"] = db_bytes
metrics["feasibility"]["duckdb_bytes_per_row"] = round(db_bytes / max(s["contracts_rows"] + s["processes_rows"], 1), 1)
metrics["feasibility"]["csv_bytes_per_row"] = round(downloaded_bytes / max(s["contracts_rows"] + s["processes_rows"], 1), 1)

(DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("== Done: metrics.json written ==")
print(json.dumps(metrics["sample"], indent=2, default=str))
