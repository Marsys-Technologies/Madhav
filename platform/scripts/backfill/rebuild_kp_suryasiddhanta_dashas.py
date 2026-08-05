#!/usr/bin/env python3
"""rebuild_kp_suryasiddhanta_dashas.py — T4 of the post-salvage close-out.

PR #1053 fixed `pyjhora_adapter/_ayanamsha.py`'s `AYANAMSHA_MAP`: the A3 canonical ids
`krishnamurti` (KP) and `surya_siddhanta_classical` were absent from the map and silently fell
back to the Lahiri default via `.get(key, AYANAMSHA_MAP[DEFAULT_AYANAMSHA])`. Every `chart_dashas`
row built for those two ayanamshas before the fix was computed with LAHIRI sidereal positions, not
KP / Surya Siddhanta — a wrong value, not merely an unverified one.

Confirmed by direct query: exactly 3 charts have `chart_dashas` rows for these two ayanamsha ids
(584,607 rows total). Verified by direct recomputation (2026-08-06) that the stored `krishnamurti`
row for chart 482012f1 is BYTE-IDENTICAL to its `lahiri_chitrapaksha` counterpart (moon_sid, lord,
start/end all match) and that the now-fixed engine computes a genuinely different moon_sid / lord
sequence for both `krishnamurti` and `surya_siddhanta_classical` (see PR description for the
before/after values).

This script re-runs `ga_dashas_writer.build_ga_dashas()` scoped to exactly the 2 broken ayanamshas
(the 3 unaffected ayanamshas — lahiri_chitrapaksha, true_chitra, raman — are never touched).
`replace_prior_chart_dashas()` (ga_writers/_idempotency.py) scopes its DELETE to
`(chart_id, system_id, ayanamsha_id)` present in the freshly computed rows, so this is a precise
per-chart, per-ayanamsha replacement, not a whole-chart rebuild. Because the verifier is wired in
(#1056), rebuilt rows earn their `verification_pass_status` tier honestly at write time — this
script never hand-sets a tier.

USAGE
-----
    python rebuild_kp_suryasiddhanta_dashas.py --chart <chart_id>   # one chart (required)
    python rebuild_kp_suryasiddhanta_dashas.py --chart <chart_id> --dry-run  # count only, no write

DATABASE_URL is read from the environment and is never taken as an argument. Charts are processed
one at a time and one must be named explicitly — this is a slow, heavy rebuild (7 systems x 2
ayanamshas per chart) and is deliberately not "rebuild everything" so a timeboxed session can HALT
between charts with a clean resume cursor (just re-run naming the next chart_id).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

AYANAMSHAS = ["krishnamurti", "surya_siddhanta_classical"]


def _counts(cur, chart_id: str) -> dict[str, int]:
    cur.execute(
        "SELECT ayanamsha_id, count(*) FROM chart_dashas "
        "WHERE chart_id = %s AND ayanamsha_id = ANY(%s) GROUP BY 1",
        (chart_id, AYANAMSHAS),
    )
    out = {aya: 0 for aya in AYANAMSHAS}
    out.update(dict(cur.fetchall()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chart", required=True, help="chart_id to rebuild (one at a time)")
    ap.add_argument("--dry-run", action="store_true", help="report counts only; no write")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set; refusing to guess.", file=sys.stderr)
        return 2

    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        before = _counts(cur, args.chart)
    print(f"BEFORE (chart {args.chart}): {before}")

    if args.dry_run:
        print("Dry run only. Re-run without --dry-run to rebuild.")
        return 0

    # TOCTOU re-check immediately before the rebuild.
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        recheck = _counts(cur, args.chart)
    if recheck != before:
        print(
            f"HALT: TOCTOU drift on {args.chart}: predicted {before}, now {recheck}. "
            f"Re-run to re-predict.",
            file=sys.stderr,
        )
        return 3

    from ga_writers.ga_dashas_writer import build_ga_dashas

    summary = build_ga_dashas(args.chart, ayanamshas=AYANAMSHAS)
    print(f"build status: {summary['status']}")
    if summary["status"] != "PASS":
        print(f"HALT: build did not PASS: {summary.get('failed_systems')}", file=sys.stderr)
        return 1

    computed_total = summary["total_rows"]

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        after = _counts(cur, args.chart)

    actual_total = sum(after.values())
    print(f"AFTER  (chart {args.chart}): {after}")
    print(f"writer-reported rows_computed total: {computed_total:,}")
    print(f"actual post-state row total for these 2 ayanamshas: {actual_total:,}")

    if computed_total != actual_total:
        print(
            f"WARNING: writer reported {computed_total:,} rows computed but {actual_total:,} "
            f"rows are present post-write for {AYANAMSHAS}. Investigate before trusting this chart.",
            file=sys.stderr,
        )
        return 1

    print(f"\nChart {args.chart}: {computed_total:,} rows rebuilt for {AYANAMSHAS}, "
          f"writer-computed count matches actual post-state count.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
