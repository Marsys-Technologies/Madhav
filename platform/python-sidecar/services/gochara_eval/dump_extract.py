"""Candidate extract generation — the EXACT command the Stage-1 freeze records (SI addendum v1.3 §5).

    python3 -m services.gochara_eval.dump_extract --generation {generation} --stage1 {stage1} --pinned-at {pinned_at} --out {out}

Read-only: one SELECT inside a READ ONLY transaction against `kala_gochara_windows` (the DSN comes from the environment variable
GOCHARA_EVAL_READONLY_DSN or, with --libpq-env, the libpq PG* variables — never from the command line). It REFUSES to run unless the Stage-1 freeze verifies (no placeholders,
every pre-extract input hash and the running-code hashes match) — so no candidate extract can be generated before the freeze is
committed. Governed generations ('5.x') are refused outright: they live in the eval-window tables, which have no reader yet
(review packet v1_10 §C2).

The output is DETERMINISTIC: a total `ORDER BY` over every selected column (the plan v1.1 SQL ordered by (event_class, ws) only,
which leaves ties in database-defined order and would make the file hash unstable), the same JSON layout as the pinned '3.0'
extract (indent 1, no trailing newline), and a `pinned_at` that is an argument, not the clock.

`--requalify-3-0` re-dumps generation '3.0' (a baseline, not a candidate; no freeze needed) and reports whether the bytes equal
the pinned extract — the detector that this command dumps what the pinned file contains.
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import json
import os
import sys
from pathlib import Path

from .freeze import FreezeRefused, require_stage1

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
H_START = "1998-01-01"
H_END_EXCL = "2026-04-18"
CANDIDATE_GENERATIONS = ("4.1",)
BASELINE_GENERATIONS = ("3.0",)
DSN_ENV = "GOCHARA_EVAL_READONLY_DSN"
CANONICAL_COMMAND = ("python3 -m services.gochara_eval.dump_extract --generation {generation} --stage1 {stage1} "
                     "--pinned-at {pinned_at} --out {out}")
COLUMNS = ["event_class", "ws", "we", "pk", "si", "valence", "adv", "resolution", "temporal_shape"]
TZ_CONVENTION = "dates converted to IST civil dates via (ts at time zone 'Asia/Kolkata')::date"

SQL_HORIZON = """SELECT COUNT(*) FROM kala_gochara_windows
 WHERE chart_id = %s AND generation = %s
   AND (((window_end at time zone 'Asia/Kolkata')::date) < DATE %s
        OR ((window_start at time zone 'Asia/Kolkata')::date) >= DATE %s)"""
SQL_DUMP = """SELECT event_class,
       (window_start at time zone 'Asia/Kolkata')::date AS ws,
       (window_end   at time zone 'Asia/Kolkata')::date AS we,
       (peak_date    at time zone 'Asia/Kolkata')::date AS pk,
       signed_intensity AS si, valence, is_adverse AS adv, resolution, temporal_shape
  FROM kala_gochara_windows
 WHERE chart_id = %s AND generation = %s
 ORDER BY event_class, ws, we, pk, si, valence, adv, resolution, temporal_shape"""


def _cell(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def header(generation: str, pinned_at: str, row_count: int) -> dict:
    return {"artifact": f"baseline_{generation.replace('.', '_')}_extract", "version": "1.0", "pinned_at": pinned_at,
            "predicate": f"kala_gochara_windows where chart_id='{CHART_ID}' and generation='{generation}'",
            "tz_convention": TZ_CONVENTION, "row_count": row_count, "columns": COLUMNS}


def dump_rows(conn, generation: str, horizon_check: bool) -> list[dict]:
    """READ ONLY transaction; returns the rows as dicts keyed by COLUMNS. `horizon_check`: assert nothing outside the scored horizon."""
    conn.read_only = True
    with conn.cursor() as cur:
        if horizon_check:
            cur.execute(SQL_HORIZON, (CHART_ID, generation, H_START, H_END_EXCL))
            outside = cur.fetchone()[0]
            if outside != 0:
                raise RuntimeError(f"INPUT_REJECTED: {outside} windows of generation {generation} fall outside the scored horizon")
        cur.execute(SQL_DUMP, (CHART_ID, generation))
        return [dict(zip(COLUMNS, (_cell(c) for c in r))) for r in cur.fetchall()]


def rows_multiset_equal(a: list[dict], b: list[dict]) -> bool:
    key = lambda r: json.dumps(r, sort_keys=True)          # noqa: E731
    return sorted(map(key, a)) == sorted(map(key, b))


def render(generation: str, pinned_at: str, rows: list[dict]) -> bytes:
    """Byte layout of the pinned '3.0' extract: indent=1, header key order, no trailing newline."""
    return json.dumps({**header(generation, pinned_at, len(rows)), "rows": rows}, indent=1).encode()


def main(argv: list[str] | None = None, conn_factory=None) -> int:
    ap = argparse.ArgumentParser(prog="dump_extract")
    ap.add_argument("--generation", required=True)
    ap.add_argument("--stage1", help="committed Stage-1 freeze file (required for a candidate generation)")
    ap.add_argument("--inputs-root", help="campaign measurement directory the freeze's input paths are relative to "
                                          "(default: the Stage-1 file's own directory)")
    ap.add_argument("--pinned-at", required=True, help="declared pin date (a frozen argument, not the clock)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--libpq-env", action="store_true",
                    help="connect with the libpq PG* environment variables instead of GOCHARA_EVAL_READONLY_DSN")
    ap.add_argument("--requalify-3-0", metavar="PINNED_SHA256",
                    help="re-dump the '3.0' BASELINE (no freeze) and compare to this pinned sha256")
    ap.add_argument("--compare-to", help="with --requalify-3-0: the pinned extract file; its ROW MULTISET is compared as well "
                                         "(the pinned file's row order within (event_class, ws) ties was database-defined)")
    args = ap.parse_args(argv)

    if args.requalify_3_0:
        if args.generation not in BASELINE_GENERATIONS:
            print(f"REFUSED: --requalify-3-0 re-dumps only {BASELINE_GENERATIONS}", file=sys.stderr)
            return 2
        horizon_check = False
    else:
        if args.generation not in CANDIDATE_GENERATIONS:
            print(f"REFUSED: no extract path for generation {args.generation!r} (candidate generations: "
                  f"{CANDIDATE_GENERATIONS}; governed '5.x' needs the eval-window reader first)", file=sys.stderr)
            return 2
        if not args.stage1:
            print("REFUSED: a candidate extract needs --stage1 (the committed Stage-1 freeze)", file=sys.stderr)
            return 2
        root = args.inputs_root or str(Path(args.stage1).resolve().parent)
        try:
            require_stage1(args.stage1, root, CANONICAL_COMMAND)
        except FreezeRefused as exc:
            print(str(exc), file=sys.stderr)
            return 2
        horizon_check = True

    if conn_factory is None:
        dsn = "" if args.libpq_env else os.environ.get(DSN_ENV)
        if dsn is None or (not dsn and not args.libpq_env):
            print(f"REFUSED: {DSN_ENV} is not set (read-only DSN; or pass --libpq-env)", file=sys.stderr)
            return 2
        import psycopg

        def conn_factory():
            return psycopg.connect(dsn)
    conn = conn_factory()
    try:
        rows = dump_rows(conn, args.generation, horizon_check)
    finally:
        conn.rollback()
        conn.close()
    blob = render(args.generation, args.pinned_at, rows)
    Path(args.out).write_bytes(blob)
    sha = hashlib.sha256(blob).hexdigest()
    print(f"rows={len(rows)} sha256={sha} out={args.out}")
    if args.requalify_3_0:
        byte_ok = sha == args.requalify_3_0
        print("REQUALIFY bytes: " + ("IDENTICAL to the pin" if byte_ok else "DIFFER from the pin"))
        if args.compare_to:
            same = rows_multiset_equal(rows, json.loads(Path(args.compare_to).read_bytes())["rows"])
            print("REQUALIFY rows: " + ("the SAME row multiset as the pinned file" + ("" if byte_ok else " (order differs only)")
                                        if same else "DIFFER from the pinned file's rows"))
            return 0 if same else 1
        return 0 if byte_ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
