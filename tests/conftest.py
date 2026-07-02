import duckdb
import pytest

from secop.datasets import CONTRATOS, PROCESOS


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    yield c
    c.close()


def _create_raw(con, dataset, rows: list[dict]) -> None:
    """Create a raw table with the dataset's full width (all VARCHAR), filling
    columns absent from each row dict with NULL."""
    cols = ["socrata_id", "socrata_updated_at", *dataset.columns]
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    ddl_cols = ", ".join(f'"{c}" VARCHAR' for c in cols)
    con.execute(f"CREATE OR REPLACE TABLE {dataset.raw_table} ({ddl_cols})")
    placeholders = ", ".join("?" for _ in cols)
    for row in rows:
        unknown = set(row) - set(cols)
        assert not unknown, f"fixture uses unknown columns: {unknown}"
        con.execute(
            f"INSERT INTO {dataset.raw_table} VALUES ({placeholders})",
            [row.get(c) for c in cols],
        )


@pytest.fixture
def make_raw_contratos(con):
    return lambda rows: _create_raw(con, CONTRATOS, rows)


@pytest.fixture
def make_raw_procesos(con):
    return lambda rows: _create_raw(con, PROCESOS, rows)
