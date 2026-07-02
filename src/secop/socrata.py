"""SODA client for datos.gov.co: retrying GETs and keyset paging on :id.

Paging uses `$order=:id` + `$where=:id > '<last>'` (verified live on
jbjy-vk9h). :id order is not lexicographic, so continuation always uses the
last-seen :id verbatim — never max()/min() over stored ids.
"""

import csv
import io
import os
import time

import requests

BASE = "https://www.datos.gov.co/resource"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class SocrataClient:
    def __init__(self, session=None, token=None, base=BASE, max_tries=8):
        self.session = session if session is not None else requests.Session()
        self.base = base
        self.max_tries = max_tries
        if token is None:
            token = os.environ.get("SOCRATA_APP_TOKEN")
        if token:
            self.session.headers["X-App-Token"] = token

    def _get(self, url, params):
        last_error = None
        for attempt in range(self.max_tries):
            try:
                r = self.session.get(url, params=params, timeout=600)
            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
                time.sleep(min(2 ** (attempt + 2), 120))
                continue
            if r.status_code in RETRYABLE_STATUS:
                last_error = RuntimeError(f"HTTP {r.status_code}")
                time.sleep(min(2 ** (attempt + 2), 120))
                continue
            r.raise_for_status()
            return r
        raise RuntimeError(f"gave up after {self.max_tries} tries: {last_error}")

    def get_csv(self, dataset_id, params):
        return self._get(f"{self.base}/{dataset_id}.csv", params)

    def get_json(self, dataset_id, params):
        return self._get(f"{self.base}/{dataset_id}.json", params).json()

    def count(self, dataset, where=None):
        params = {"$select": "count(*) AS n"}
        if where:
            params["$where"] = where
        return int(self.get_json(dataset.socrata_id, params)[0]["n"])

    def pages(self, dataset, where=None, page_size=50_000, after_id=None):
        """Yield (csv_text, last_socrata_id, n_rows) per page until exhausted."""
        last = after_id
        while True:
            params = {
                "$select": dataset.select_clause,
                "$order": ":id",
                "$limit": str(page_size),
            }
            clauses = []
            if where:
                clauses.append(f"({where})")
            if last is not None:
                clauses.append(f":id > '{last}'")
            if clauses:
                params["$where"] = " AND ".join(clauses)

            text = self.get_csv(dataset.socrata_id, params).text
            rows = list(csv.reader(io.StringIO(text)))
            data = rows[1:]  # rows[0] is the header
            if not data:
                return
            last = data[-1][0]
            yield text, last, len(data)
            if len(data) < page_size:
                return
