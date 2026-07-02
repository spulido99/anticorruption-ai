"""Keyset paging over SODA: resumable, snapshot-stable (`$order=:id`), with
throttling backoff. Verified live: `:id > '<last>'` is accepted and :id order
is NOT lexicographic, so continuation must use the last-seen :id verbatim."""

import pytest

from secop.datasets import CONTRATOS
from secop.socrata import SocrataClient


class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        return self.responses.pop(0)


def csv_page(ids):
    header = '"socrata_id","socrata_updated_at","id_contrato"'
    rows = [f'"{i}","2026-07-02T00:00:00.000Z","CO1.PCCNTR.{n}"' for n, i in enumerate(ids)]
    return "\n".join([header, *rows]) + "\n"


def test_pages_keyset_advances_by_last_id_and_stops_on_short_page():
    session = FakeSession([
        FakeResponse(text=csv_page(["row-aa", "row-bb"])),
        FakeResponse(text=csv_page(["row-cc"])),  # short page -> stop
    ])
    client = SocrataClient(session=session, token=None)
    pages = list(client.pages(CONTRATOS, page_size=2))

    assert [(last, n) for _, last, n in pages] == [("row-bb", 2), ("row-cc", 1)]
    # First call: no :id filter. Second call: keyset on the last :id verbatim.
    assert "$where" not in session.calls[0][1]
    assert session.calls[1][1]["$where"] == ":id > 'row-bb'"
    assert session.calls[0][1]["$order"] == ":id"


def test_pages_combines_user_where_with_keyset():
    session = FakeSession([
        FakeResponse(text=csv_page(["row-aa"])),
    ])
    client = SocrataClient(session=session, token=None)
    list(client.pages(CONTRATOS, where="departamento = 'Boyacá'", page_size=5))
    assert session.calls[0][1]["$where"] == "(departamento = 'Boyacá')"


def test_pages_resumes_after_given_id():
    session = FakeSession([FakeResponse(text=csv_page(["row-zz"]))])
    client = SocrataClient(session=session, token=None)
    list(client.pages(CONTRATOS, page_size=5, after_id="row-yy"))
    assert session.calls[0][1]["$where"] == ":id > 'row-yy'"


def test_get_retries_on_429(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    session = FakeSession([
        FakeResponse(status_code=429),
        FakeResponse(text="ok"),
    ])
    client = SocrataClient(session=session, token=None)
    assert client.get_csv("jbjy-vk9h", {}).text == "ok"
    assert len(session.calls) == 2


def test_app_token_header_set_when_provided():
    session = FakeSession([])
    SocrataClient(session=session, token="SECRET")
    assert session.headers["X-App-Token"] == "SECRET"


def test_count_parses_scalar():
    session = FakeSession([FakeResponse(json_data=[{"n": "42"}])])
    client = SocrataClient(session=session, token=None)
    assert client.count(CONTRATOS, where="x = 1") == 42
    assert session.calls[0][1]["$where"] == "x = 1"
