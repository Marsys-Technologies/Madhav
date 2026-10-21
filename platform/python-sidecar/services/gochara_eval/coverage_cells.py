"""Per-(class, year) coverage evidence of a GOVERNED generation — the producer of the `coverage_cells` input of the J-5q report
(`qualification_report.py`; protocol §6.5c: "computed (class, year) cells / horizon cells, >= 50% per scored class").

READ-ONLY: ONE SELECT over the `event_class` partitions of `kala_gochara_coverage` of ONE chart and ONE generation. No window row is read, no
outcome, no life event; no write, no lock, no commit, no close — the connection is the caller's.

A governed generation records ONE completed horizon per event_class partition (the class's search ran, as a whole, over that horizon), so a
(class, year) cell is derivable from the ledger itself — not from the admitted windows (a computed-empty year has none, and a window never proves
the engine completed its year). The cell is

    horizon_covers_year   the partition's completed_horizon (half-open [lo, hi)) contains the whole year's IST days, the final year being cut at
                          the scored horizon's end (2026-04-17); a partial year is NOT covered
    unsearched_reason     the partition's stored reason that part of its search was not run (e.g. "Moon-agent edges are on-demand (AM-4)"), or null
    computed              the cell the report counts, under the declared POLICY:
                            strict       horizon_covers_year AND unsearched_reason is null   (default: a partition that says part of its search
                                         was not run does not claim its years computed — the same reading the report already applies)
                            horizon_only horizon_covers_year   (the owner's reading that an on-demand tier is not an unsearched hole)
                          Which policy applies is an OWNER/STEWARD decision this module does not take: it records the policy it was run under in
                          the output, and every cell carries both facts so either reading can be re-derived from the file.

A class with NO event_class partition gets NO cells (the census stays incomplete and the report reads `insufficient_evidence`) and is listed in
`classes_without_partition`: its absence from the ledger is not evidence that its years were, or were not, computed. A partition whose horizon
bounds are not the half-open [lo, hi) the writer stores is refused by name.

    python -m services.gochara_eval.coverage_cells --chart-id C --generation 5.0 --dsn-env NAME --output cells.json [--unsearched-policy strict]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from .qualification import SCORED_CLASSES, YEARS
from .registry import H0, H1

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
POLICIES = ("strict", "horizon_only")
SCHEMA = "ky.coverage_cells/1"

COVERAGE_SQL = (
    "SELECT c.partition_key, lower(c.completed_horizon), upper(c.completed_horizon),"
    "       lower_inc(c.completed_horizon), upper_inc(c.completed_horizon), c.unsearched_reason"
    " FROM public.kala_gochara_coverage c"
    " WHERE c.chart_id = %s::uuid AND c.generation = %s AND c.partition_kind = 'event_class'"
    " ORDER BY c.partition_key")
STATEMENTS = (COVERAGE_SQL,)


class CoverageRefused(RuntimeError):
    """The ledger cannot be turned into cells honestly (named, never defaulted)."""


def _tuples(rows) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]


def _ist_midnight(day: dt.date) -> dt.datetime:
    return dt.datetime(day.year, day.month, day.day, tzinfo=IST)


def year_window(year: int) -> tuple[dt.datetime, dt.datetime]:
    """The half-open instant range of the year's IST days, the last scored year cut at the scored horizon's end (H1 is an inclusive day)."""
    lo = _ist_midnight(dt.date(year, 1, 1))
    hi = _ist_midnight(H1 + dt.timedelta(days=1)) if year == H1.year else _ist_midnight(dt.date(year + 1, 1, 1))
    return lo, hi


def read_cells(conn, *, chart_id: str, generation: str, unsearched_policy: str = "strict") -> dict:
    if unsearched_policy not in POLICIES:
        raise CoverageRefused(f"unsearched policy {unsearched_policy!r} is not one of {POLICIES}")
    partitions: dict[str, tuple] = {}
    for key, lo, hi, lo_inc, hi_inc, why in _tuples(conn.execute(COVERAGE_SQL, (chart_id, generation)).fetchall()):
        if key in partitions:
            raise CoverageRefused(f"{key}: two event_class partitions")
        if key not in SCORED_CLASSES:
            raise CoverageRefused(f"{key}: an event_class partition outside the 26 endpoint-eligible classes")
        if lo is None or hi is None:
            raise CoverageRefused(f"{key}: the partition carries no completed horizon")
        if lo.tzinfo is None or hi.tzinfo is None:
            raise CoverageRefused(f"{key}: a completed-horizon bound is not timezone-aware")
        if not (lo_inc and not hi_inc):
            raise CoverageRefused(f"{key}: the completed horizon is not the half-open [lo, hi) the writer stores")
        partitions[key] = (lo, hi, why)
    cells = []
    for cls in SCORED_CLASSES:
        if cls not in partitions:
            continue
        lo, hi, why = partitions[cls]
        for year in YEARS:
            y_lo, y_hi = year_window(year)
            covers = lo <= y_lo and y_hi <= hi
            computed = covers and (why is None or unsearched_policy == "horizon_only")
            cells.append({"event_class": cls, "year": year, "computed": computed,
                          "horizon_covers_year": covers, "unsearched_reason": why})
    return {"schema": SCHEMA, "chart_id": chart_id, "generation": generation, "unsearched_policy": unsearched_policy,
            "scored_years": [YEARS[0], YEARS[-1]], "scored_span": [H0.isoformat(), H1.isoformat()],
            "classes_without_partition": [c for c in SCORED_CLASSES if c not in partitions],
            "partitions": {c: {"completed_horizon": [partitions[c][0].isoformat(), partitions[c][1].isoformat()],
                               "unsearched_reason": partitions[c][2]} for c in SCORED_CLASSES if c in partitions},
            "cells": cells}


def main(argv: list[str] | None = None, connect=None) -> int:
    """CLI. The connection string is read from the ENVIRONMENT variable named by --dsn-env (never an argument); the session is opened read-only."""
    import os

    ap = argparse.ArgumentParser(prog="gochara_eval.coverage_cells", description=__doc__.splitlines()[0])
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--dsn-env", required=True, help="NAME of the environment variable holding the connection string")
    ap.add_argument("--output", required=True)
    ap.add_argument("--unsearched-policy", choices=POLICIES, default="strict")
    args = ap.parse_args(argv)
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"environment variable {args.dsn_env} is not set", file=sys.stderr)
        return 2
    if connect is None:
        import psycopg
        connect = psycopg.connect
    with connect(dsn, autocommit=False) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        try:
            doc = read_cells(conn, chart_id=args.chart_id, generation=args.generation, unsearched_policy=args.unsearched_policy)
        except CoverageRefused as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 1
        finally:
            conn.rollback()
    with open(args.output, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False, sort_keys=True)
    print(f"cells written: {args.output} ({len(doc['cells'])} cells, {sum(c['computed'] for c in doc['cells'])} computed, "
          f"{len(doc['classes_without_partition'])} classes without a partition)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
