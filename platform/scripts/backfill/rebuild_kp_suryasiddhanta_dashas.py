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
sequence for both `krishnamurti` and `surya_siddhanta_classical`.

CALL PATTERN — matches the real orchestrator adapter, not the standalone `build_ga_dashas()`
------------------------------------------------------------------------------------------------
`build_ga_dashas()`/its CLI `main()` call `build_system(..., birth_params=None)` with no way to
supply birth params outside the orchestrator — `resolve_birth_params()` unconditionally raises on
a falsy `birth_params` (by design: B1 elimination, no hardcoded fallback). The REAL production path
(`pipeline/orchestrator/writers/ga_dashas.py`'s `GaDashasWriter.run_substep`) fetches birth_params
once via `fetch_birth_params()` and passes it into each `build_system(..., birth_params=...)` call.
This script mirrors that — the only way to run this writer outside the orchestrator.

`write_dasha_scope_cap_sentinels()` (the Prana Dasha / KP-beyond-sub_sub sentinel rows, system_id=
'scope_cap', ayanamsha_id='INVARIANT') is deliberately NOT called here: those rows are chart-level
and ayanamsha-INDEPENDENT (already present from the chart's original build) and this rebuild's
`replace_prior_chart_dashas()` delete is scoped to `(chart_id, system_id, ayanamsha_id)` present in
THIS script's own computed rows — since this script never emits `ayanamsha_id='INVARIANT'` rows,
the existing sentinels are never touched. (Separately: `build_ga_dashas()`'s own call to that
function is independently broken — it violates the `cd_level_n_max4` CHECK constraint on a fresh
chart with zero existing sentinels — a latent, unrelated defect, out of scope here.)

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

    from ga_writers.ga_dashas_writer import SYSTEMS, build_system
    from pipeline.orchestrator.birth_params import fetch_birth_params

    with psycopg.connect(dsn) as conn:
        birth_params = fetch_birth_params(conn, args.chart)

    build_id = None
    computed_total = 0
    failed: list[str] = []
    for aya in AYANAMSHAS:
        for system in SYSTEMS:
            try:
                res = build_system(system, aya, args.chart, build_id, birth_params=birth_params)
                build_id = build_id or res.get("build_id")
                computed_total += res.get("rows_computed", 0)
                print(f"  [{system}:{aya}] status={res.get('status')} "
                      f"rows_computed={res.get('rows_computed')}")
            except Exception as exc:
                failed.append(f"{system}:{aya}")
                print(f"  [{system}:{aya}] FAIL: {exc}", file=sys.stderr)

    if failed:
        print(f"HALT: build did not fully PASS: {failed}", file=sys.stderr)
        return 1

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
