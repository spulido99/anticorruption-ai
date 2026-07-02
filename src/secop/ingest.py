"""Load SODA pages into the raw schema with resumable, atomic page commits.

Each page is inserted and the ingest state updated inside one transaction, so
an interrupted multi-hour download resumes from the last committed :id without
duplicating rows. raw keeps every column as text, as published (ADR 0002).
"""

import time
from pathlib import Path

STATE_TABLE = "raw.ingest_state"


def _init(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {STATE_TABLE} (
            dataset VARCHAR PRIMARY KEY,
            where_sql VARCHAR NOT NULL,
            last_id VARCHAR,
            rows_loaded BIGINT NOT NULL,
            complete BOOLEAN NOT NULL,
            started_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)


def get_state(con, dataset_key):
    _init(con)
    row = con.execute(
        f"SELECT dataset, where_sql, last_id, rows_loaded, complete "
        f"FROM {STATE_TABLE} WHERE dataset = ?", [dataset_key]
    ).fetchone()
    if row is None:
        return None
    return {"dataset": row[0], "where_sql": row[1], "last_id": row[2],
            "rows_loaded": row[3], "complete": row[4]}


def _fresh_start(con, dataset, where_sql):
    con.execute(f"DROP TABLE IF EXISTS {dataset.raw_table}")
    con.execute(f"DELETE FROM {STATE_TABLE} WHERE dataset = ?", [dataset.key])
    con.execute(
        f"INSERT INTO {STATE_TABLE} VALUES (?, ?, NULL, 0, false, now(), now())",
        [dataset.key, where_sql],
    )


def load(con, client, dataset, where=None, page_size=50_000, tmp_dir=None,
         restart=False, progress=None):
    _init(con)
    where_sql = where or ""
    st = get_state(con, dataset.key)

    if restart or st is None or st["complete"]:
        _fresh_start(con, dataset, where_sql)
        st = get_state(con, dataset.key)
    elif st["where_sql"] != where_sql:
        raise ValueError(
            f"incomplete load for '{dataset.key}' has a different filter "
            f"({st['where_sql']!r} vs {where_sql!r}); pass restart=True to drop it"
        )

    tmp_dir = Path(tmp_dir) if tmp_dir else Path(".")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / f".page_{dataset.key}.csv"

    t0 = time.time()
    for text, last_id, n in client.pages(
        dataset, where=where or None, page_size=page_size, after_id=st["last_id"]
    ):
        # newline='' keeps quoted newlines inside fields intact on Windows.
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        read = f"read_csv('{tmp.as_posix()}', header=true, all_varchar=true)"
        table_exists = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'raw' AND table_name = ?",
            [dataset.raw_table.split(".", 1)[1]],
        ).fetchone()[0]
        con.execute("BEGIN")
        try:
            if not table_exists:
                con.execute(f"CREATE TABLE {dataset.raw_table} AS SELECT * FROM {read}")
            else:
                con.execute(f"INSERT INTO {dataset.raw_table} BY NAME SELECT * FROM {read}")
            con.execute(
                f"UPDATE {STATE_TABLE} SET last_id = ?, rows_loaded = rows_loaded + ?, "
                f"updated_at = now() WHERE dataset = ?",
                [last_id, n, dataset.key],
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        st["rows_loaded"] += n
        if progress:
            rate = st["rows_loaded"] / max(time.time() - t0, 1e-9)
            progress(f"{dataset.key}: {st['rows_loaded']:,} rows "
                     f"({rate:,.0f} rows/s this run)")

    tmp.unlink(missing_ok=True)
    con.execute(
        f"UPDATE {STATE_TABLE} SET complete = true, updated_at = now() WHERE dataset = ?",
        [dataset.key],
    )
