"""CLI: python -m secop {load,transform,verify} --db data/secop.duckdb

`load --where` scopes a load territorially/temporally (used for smoke tests
and, later, the ally's bounded local setup)."""

import argparse
import json
import sys
from pathlib import Path

import duckdb

from .datasets import DATASETS
from .ingest import load
from .socrata import SocrataClient
from .transform import run_transform
from .verify import check_counts, reproduce_pilot_numbers


def main(argv=None):
    p = argparse.ArgumentParser(prog="secop")
    p.add_argument("--db", default="data/secop.duckdb")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_load = sub.add_parser("load", help="download into raw (resumable)")
    p_load.add_argument("--dataset", choices=[*DATASETS, "all"], default="all")
    p_load.add_argument("--where", default=None, help="SoQL filter for a scoped load")
    p_load.add_argument("--page-size", type=int, default=50_000)
    p_load.add_argument("--restart", action="store_true",
                        help="drop the raw table and its state, start over")

    sub.add_parser("transform", help="rebuild core from raw")
    sub.add_parser("verify", help="counts vs API + #7 pilot numbers")

    args = p.parse_args(argv)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)

    if args.cmd == "load":
        client = SocrataClient()
        keys = list(DATASETS) if args.dataset == "all" else [args.dataset]
        for key in keys:
            ds = DATASETS[key]
            print(f"== load {key} ({ds.socrata_id}) ==", flush=True)
            load(con, client, ds, where=args.where, page_size=args.page_size,
                 tmp_dir=Path(args.db).parent, restart=args.restart,
                 progress=lambda msg: print(msg, flush=True))
            print(f"== {key} complete ==", flush=True)
    elif args.cmd == "transform":
        run_transform(con)
        for t in ("contratos", "procesos", "entidades", "contratistas"):
            n = con.execute(f"SELECT count(*) FROM core.{t}").fetchone()[0]
            print(f"core.{t}: {n:,} rows")
    elif args.cmd == "verify":
        client = SocrataClient()
        out = {"counts": check_counts(con, client),
               "pilot_numbers": reproduce_pilot_numbers(con)}
        print(json.dumps(out, indent=1, ensure_ascii=False, default=str))

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
