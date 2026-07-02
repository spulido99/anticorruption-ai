"""Ingest into raw: page-by-page atomic loads with persisted state so a
multi-hour national download survives interruption without duplicating rows."""

import duckdb
import pytest

from secop.datasets import CONTRATOS
from secop.ingest import get_state, load


def csv_page(ids):
    cols = ["socrata_id", "socrata_updated_at", *CONTRATOS.columns]
    header = ",".join(f'"{c}"' for c in cols)
    rows = []
    for i in ids:
        vals = [i, "2026-07-02T00:00:00.000Z"] + [f"v-{c}" for c in CONTRATOS.columns]
        rows.append(",".join(f'"{v}"' for v in vals))
    return "\n".join([header, *rows]) + "\n"


class FakeClient:
    """Yields pre-baked pages, honoring after_id like the real keyset pager."""

    def __init__(self, ids, page_size_expected, fail_after_pages=None):
        self.ids = ids
        self.page_size_expected = page_size_expected
        self.fail_after_pages = fail_after_pages
        self.seen_after_ids = []

    def pages(self, dataset, where=None, page_size=None, after_id=None):
        assert page_size == self.page_size_expected
        self.seen_after_ids.append(after_id)
        remaining = self.ids
        if after_id is not None:
            remaining = self.ids[self.ids.index(after_id) + 1:]
        emitted = 0
        for i in range(0, len(remaining), page_size):
            chunk = remaining[i:i + page_size]
            yield csv_page(chunk), chunk[-1], len(chunk)
            emitted += 1
            if self.fail_after_pages is not None and emitted >= self.fail_after_pages:
                raise ConnectionError("simulated network drop")


@pytest.fixture
def db(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    yield con
    con.close()


def count(con):
    return con.execute(f"SELECT count(*) FROM {CONTRATOS.raw_table}").fetchone()[0]


def test_load_all_pages_marks_complete(db, tmp_path):
    client = FakeClient(["a", "b", "c", "d", "e"], page_size_expected=2)
    load(db, client, CONTRATOS, page_size=2, tmp_dir=tmp_path)
    assert count(db) == 5
    st = get_state(db, CONTRATOS.key)
    assert st["complete"] is True
    assert st["rows_loaded"] == 5
    # Full width: system fields + all published columns.
    ncols = len(db.execute(f"SELECT * FROM {CONTRATOS.raw_table} LIMIT 0").description)
    assert ncols == 2 + len(CONTRATOS.columns)


def test_interrupted_load_resumes_without_duplicates(db, tmp_path):
    ids = ["a", "b", "c", "d", "e"]
    broken = FakeClient(ids, page_size_expected=2, fail_after_pages=1)
    with pytest.raises(ConnectionError):
        load(db, broken, CONTRATOS, page_size=2, tmp_dir=tmp_path)
    assert count(db) == 2
    assert get_state(db, CONTRATOS.key)["complete"] is False

    healthy = FakeClient(ids, page_size_expected=2)
    load(db, healthy, CONTRATOS, page_size=2, tmp_dir=tmp_path)
    # Resumed from the last committed :id, not from scratch.
    assert healthy.seen_after_ids == ["b"]
    assert count(db) == 5
    assert db.execute(
        f"SELECT count(DISTINCT socrata_id) FROM {CONTRATOS.raw_table}"
    ).fetchone()[0] == 5
    assert get_state(db, CONTRATOS.key)["complete"] is True


def test_completed_load_reloads_fresh(db, tmp_path):
    load(db, FakeClient(["a", "b"], 10), CONTRATOS, page_size=10, tmp_dir=tmp_path)
    # A second load over a complete state is a full refresh, not an append.
    load(db, FakeClient(["a", "b", "c"], 10), CONTRATOS, page_size=10, tmp_dir=tmp_path)
    assert count(db) == 3


def test_where_change_on_incomplete_state_requires_restart(db, tmp_path):
    broken = FakeClient(["a", "b", "c"], 2, fail_after_pages=1)
    with pytest.raises(ConnectionError):
        load(db, broken, CONTRATOS, where="x = 1", page_size=2, tmp_dir=tmp_path)
    with pytest.raises(ValueError, match="restart"):
        load(db, FakeClient(["a"], 2), CONTRATOS, where="x = 2", page_size=2, tmp_dir=tmp_path)
    # Explicit restart drops and reloads.
    load(db, FakeClient(["a", "b"], 2), CONTRATOS, where="x = 2", page_size=2,
         tmp_dir=tmp_path, restart=True)
    assert count(db) == 2
