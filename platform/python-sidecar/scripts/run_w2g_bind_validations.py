#!/usr/bin/env python3
"""
run_w2g_bind_validations.py — run the W2G (GOCHARA-2.0) bind-time
validations V1–V6 against a live database and print the report as JSON.

WAVE: W2G (ADJUDICATION-3).

READ-ONLY BY CONSTRUCTION. `services.w2g_validations` issues nothing but
SELECT; this script additionally opens the connection in autocommit and
never issues a write. `kala_gochara_windows` data is an untouchable
(brief §7 / ADJUDICATION-6) and is only read here.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/run_w2g_bind_validations.py
    ... --pilot-year 2013 --summary-only

Exit codes:
    0 — every validation PASSed (the bind gate opens)
    2 — at least one validation FAILed or is INDETERMINATE (gate blocks)
    3 — the run itself could not proceed (no DATABASE_URL, no driver)

Exit code 2 is the EXPECTED outcome while the wave is open: a FAIL is a
finding, and an INDETERMINATE is an honest "not measurable yet". Neither is
a defect in this harness.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.w2g_validations import bind_gate, query_fn_from_conn, run_all  # noqa: E402
from services.w2g_validations.runner import DEFAULT_PILOT_YEAR  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-year", type=int, default=DEFAULT_PILOT_YEAR)
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="print statuses, summaries and findings without the full evidence payload",
    )
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        report = run_all(query_fn_from_conn(conn), pilot_year=args.pilot_year)

    gate = bind_gate(report)
    report["bind_gate"] = gate

    if args.summary_only:
        trimmed = dict(report)
        trimmed["results"] = [
            {k: v for k, v in r.items() if k != "data"} for r in report["results"]
        ]
        print(json.dumps(trimmed, indent=2, default=str))
    else:
        print(json.dumps(report, indent=2, default=str))

    return 0 if gate["may_proceed"] else 2


if __name__ == "__main__":
    sys.exit(main())
