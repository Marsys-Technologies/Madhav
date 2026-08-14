#!/usr/bin/env python3
"""
w2g_equivalence_report.py — run the design §3 / native-ruling-point-3
equivalence report for ONE chart, reading v1's `kala_gochara_windows`
(READ-ONLY, the frozen validation benchmark) and this lane's own
`kala_gochara_windows_v2`, and printing the classified report as JSON.

ṢAḌ-DARŚANA W2G (item 19), lane G REWORK.

READ-ONLY BY CONSTRUCTION against v1. This script issues nothing but SELECT
against BOTH tables (autocommit, no BEGIN, no writer invoked) — it never
constructs a DELETE/UPDATE/INSERT statement of any kind, so migration 540's
protection trigger is never even a relevant consideration for this script:
there is no code path here that could raise it or need to override it.
`kala_gochara_windows` data is untouchable (CLAUDE.md §N.3 / the untouchables
rail) and is only ever read here.

The horizon (±3y from `--now-date`, matching the writer's own
`progressive_horizon`) and the attempted-class list (read from
`kala_gochara_v2_build_state` for this chart/generation, falling back to
`--classes` if that table has no rows yet) determine `scope_v1_rows`'s
comparable set — see `services/w2g/equivalence_report.py` for the full
scoping/matching/classification discipline.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/w2g_equivalence_report.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa [--now-date 2026-08-06]

Exit codes:
    0 — report generated successfully (regardless of how much/little
        equivalence it found — a low equivalence rate or several
        needs-review divergences is a FINDING, not a script failure)
    2 — the report contains an unclassified divergence (should be
        structurally impossible per `build_equivalence_report`'s own
        discipline, but checked explicitly here as a hard gate rather than
        trusted silently)
    3 — the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--now-date", default=None, help="ISO date anchoring the ±3y progressive horizon (default: today)")
    parser.add_argument("--classes", nargs="*", default=None,
                         help="event_classes 2.0 attempted this run (default: read from kala_gochara_v2_build_state)")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg
        import psycopg.rows
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    from datetime import date
    from services.w2g.equivalence_report import build_equivalence_report
    from services.w2g.materialize import GENERATION_V2, progressive_horizon

    now_date = date.fromisoformat(args.now_date) if args.now_date else date.today()
    horizon = progressive_horizon(now_date)

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            if args.classes:
                classes_attempted = list(args.classes)
            else:
                cur.execute(
                    "SELECT DISTINCT event_class FROM kala_gochara_v2_build_state "
                    "WHERE chart_id = %s AND generation = %s AND skipped_reason IS NULL",
                    [args.chart_id, GENERATION_V2],
                )
                classes_attempted = [r["event_class"] for r in cur.fetchall()]

            # INTENTIONAL: generation='v1' pin — this script reads the frozen
            # v1 corpus as the validation benchmark that the reworked 2.0 writer
            # is compared against (design §3.1 / native ruling point 3). The v1
            # rows are the ground truth for the equivalence check; reading any
            # other generation here would change the benchmark mid-comparison and
            # invalidate the equivalence report's conclusion. The pin is permanent
            # for this comparator role: if the authority pointer ever flips to 3.0
            # for a chart, this script still deliberately reads v1 as the reference
            # side and 3.0 (via kala_gochara_windows_v2) as the candidate side.
            # See also ADJUDICATION-6 / migration 527. (MR-18)
            cur.execute(
                "SELECT event_class, temporal_shape, window_start, window_end, peak_date, "
                "is_adverse, valence, signed_intensity, generation, active_sentences "
                "FROM kala_gochara_windows WHERE chart_id = %s AND generation = 'v1'",
                [args.chart_id],
            )
            v1_rows_raw = cur.fetchall()

            cur.execute(
                "SELECT event_class, temporal_shape, window_start, window_end, peak_date, "
                "is_adverse, valence, signed_intensity, generation, active_sentences "
                "FROM kala_gochara_windows_v2 WHERE chart_id = %s AND generation = %s",
                [args.chart_id, GENERATION_V2],
            )
            v2_rows_raw = cur.fetchall()

    report = build_equivalence_report(
        chart_id=args.chart_id,
        v1_rows_raw=v1_rows_raw,
        v2_rows_raw=v2_rows_raw,
        horizon_start=horizon.start_date,
        horizon_end=horizon.end_date,
        classes_attempted_by_v2=classes_attempted,
    )

    summary = report.summary()
    print(json.dumps(summary, indent=2, default=str))

    if summary["unclassified_count"] != 0:
        print(
            f"ERROR: {summary['unclassified_count']} divergence(s) unclassified -- "
            f"design §3.2 forbids this from shipping",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
