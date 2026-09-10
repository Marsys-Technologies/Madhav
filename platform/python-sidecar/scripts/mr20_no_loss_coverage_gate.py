#!/usr/bin/env python3
"""
mr20_no_loss_coverage_gate.py -- PARIṢKĀRA MR-20: the real no-loss coverage gate.

Runs the design §3 / native-ruling-point-3 equivalence report (the SAME
closed-vocabulary comparator `services/w2g/equivalence_report.py` implements)
for ONE chart, reading v1's `kala_gochara_windows` (READ-ONLY, the frozen
validation benchmark) against the CURRENT PRODUCTION gen-3.0 corpus --
`kala_gochara_windows` with generation='3.0' -- not `kala_gochara_windows_v2`.

WHY THIS IS A SEPARATE SCRIPT FROM w2g_equivalence_report.py
--------------------------------------------------------------
`w2g_equivalence_report.py` is a PERMANENT comparator for a DIFFERENT
generation pair by explicit, documented design: v1 vs. `kala_gochara_windows_v2`
generation='2.0' (the W2G/ṢAḌ-DARŚANA Lane G rework). Its own docstring states
that pin is deliberate and permanent for that comparator's role, and its
`--now-date` horizon/table wiring predates the W5.4 UTK-R1 production repoint
this campaign (PARIṢKĀRA MR-40) fixed elsewhere. Repointing it in place would
retroactively change what THAT script has always measured. This script reuses
the SAME pure, DB-free `build_equivalence_report` function (zero duplicated
comparison/classification logic -- see services/w2g/equivalence_report.py)
but wires it against the table the real production authority (W5.4 UTK-R1)
actually serves from: `kala_gochara_windows` generation='3.0'.

READ-ONLY BY CONSTRUCTION. This script issues nothing but SELECT against
`kala_gochara_windows` (autocommit, no BEGIN, no writer invoked) -- it never
constructs a DELETE/UPDATE/INSERT of any kind. Safe to run under an active
production-build yield window: this is evidence work, not a build.

"classes_attempted_by_v3" is derived as DISTINCT event_class actually present
in the gen-3.0 corpus for this chart -- a defensible proxy for "attempted"
(if v3 produced zero rows for a class, that class is out of scope for a
no-loss claim either way; MR-16's own open finding already discloses the
production writer's scope is narrower than v1's, and out-of-scope classes
are reported by `scope_v1_rows` with an explicit, disclosed reason, never
silently dropped).

Usage:
    DATABASE_URL=postgresql://... python3 scripts/mr20_no_loss_coverage_gate.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa [--now-date 2026-08-11]

Exit codes:
    0 -- report generated successfully (a low equivalence rate or several
         needs-review divergences is a FINDING, not a script failure)
    2 -- the report contains an unclassified divergence (should be
         structurally impossible per build_equivalence_report's own
         discipline, but checked explicitly here as a hard gate)
    3 -- the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GENERATION_V3_PROD = "3.0"
PROGRESSIVE_HORIZON_YEARS_DEFAULT = 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument(
        "--now-date", default=None,
        help="ISO date anchoring the +/- horizon (default: today)",
    )
    parser.add_argument(
        "--horizon-years", type=int, default=PROGRESSIVE_HORIZON_YEARS_DEFAULT,
        help="+/- years from --now-date to scope the comparison (default: 3, "
             "matching the writer's own progressive-onboarding horizon convention)",
    )
    parser.add_argument(
        "--classes", nargs="*", default=None,
        help="event_classes v3 attempted (default: DISTINCT event_class actually "
             "present in the gen-3.0 corpus for this chart)",
    )
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

    from datetime import date, timedelta
    from services.w2g.equivalence_report import build_equivalence_report

    now_date = date.fromisoformat(args.now_date) if args.now_date else date.today()
    horizon_start = now_date - timedelta(days=365 * args.horizon_years)
    horizon_end = now_date + timedelta(days=365 * args.horizon_years)

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            if args.classes:
                classes_attempted = list(args.classes)
            else:
                cur.execute(
                    "SELECT DISTINCT event_class FROM kala_gochara_windows "
                    "WHERE chart_id = %s AND generation = %s",
                    [args.chart_id, GENERATION_V3_PROD],
                )
                classes_attempted = [r["event_class"] for r in cur.fetchall()]

            # v1 -- READ-ONLY, the frozen validation benchmark. Never written.
            cur.execute(
                "SELECT event_class, temporal_shape, window_start, window_end, peak_date, "
                "is_adverse, valence, signed_intensity, generation, active_sentences "
                "FROM kala_gochara_windows WHERE chart_id = %s AND generation = 'v1'",
                [args.chart_id],
            )
            v1_rows_raw = cur.fetchall()

            # v3 PRODUCTION -- kala_gochara_windows generation='3.0' (W5.4
            # UTK-R1's actual authority surface; NOT kala_gochara_windows_v2).
            cur.execute(
                "SELECT event_class, temporal_shape, window_start, window_end, peak_date, "
                "is_adverse, valence, signed_intensity, generation, active_sentences "
                "FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s",
                [args.chart_id, GENERATION_V3_PROD],
            )
            v3_rows_raw = cur.fetchall()

    report = build_equivalence_report(
        chart_id=args.chart_id,
        v1_rows_raw=v1_rows_raw,
        v2_rows_raw=v3_rows_raw,  # parameter name is generation-agnostic in the pure function
        horizon_start=horizon_start,
        horizon_end=horizon_end,
        classes_attempted_by_v2=classes_attempted,
    )

    summary = report.summary()
    summary["v1_total_rows"] = len(v1_rows_raw)
    summary["v3_total_rows"] = len(v3_rows_raw)
    summary["comparator_generation"] = GENERATION_V3_PROD
    summary["comparator_table"] = "kala_gochara_windows (production, W5.4 UTK-R1 repoint)"
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
