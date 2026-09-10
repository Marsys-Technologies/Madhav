#!/usr/bin/env python3
"""
mr23_w12_adverse_golden_comparison.py -- PARIṢKĀRA MR-23 remainder, W1.2:
the "golden tests on known corpus configurations" half of W1.2's acceptance
text (the synthetic-configuration half is
`services/gochara_v3/tests/test_mr23_w12_adverse_window_golden.py`).

Compares ADVERSE windows (is_adverse=True) between v1's frozen validation
benchmark (`kala_gochara_windows` generation='v1', READ-ONLY, untouched) and
the CURRENT PRODUCTION v3 corpus (`kala_gochara_windows` generation='3.0',
the W5.4 UTK-R1 production authority -- NOT `kala_gochara_windows_v2`), for
BOTH canonical charts, reporting per-chart: how many adverse windows each
generation has, how many v1-adverse rows are in COMPARABLE scope (point-
shaped, class actually attempted by v3, inside v3's progressive horizon --
`scope_v1_rows`'s own discipline, unchanged), and how many of those match
v3's adverse rows one-to-one within the design §3.1 1-day tolerance.

WHY THIS IS A SEPARATE SCRIPT, NOT A NEW GENERIC-EQUIVALENCE INVOCATION
--------------------------------------------------------------------------
`mr20_no_loss_coverage_gate.py` (MR-20, `parishkara/integration`) runs the
SAME `build_equivalence_report` machinery unfiltered -- it answers "does v3
lose ANY v1 window (any valence)". This script asks the narrower, W1.2-
specific question the campaign plan's own acceptance text names: "a
synthetic afflicted configuration produces an adverse window where v1
produces nothing" -- generalized here to the REAL corpus as "how does the
population of ADVERSE windows compare between v1 and v3, for real charts".
It reuses `services.w2g.equivalence_report`'s `GenerationRow`/`scope_v1_rows`/
`match_rows` (zero duplicated comparison logic) but filters BOTH sides to
`is_adverse=True` before scoping/matching, and reports the adverse-specific
counts `build_equivalence_report`'s own `summary()` does not surface (it
scores ALL valences pooled together, not adverse-only).

A LOW OR ZERO MATCH COUNT IS A FINDING, NOT A SCRIPT FAILURE. W1.2's whole
thesis is that v1 silently clamps afflictions to the class-level prior
(engine.py's own `_compute_activity_v3`/`_compute_signed_channels_v3`
docstrings, and `configuration_activity.py`/`promise.py` in gochara_intensity,
I2-protected) -- so it is architecturally EXPECTED that v1 under-produces
adverse windows relative to v3 for classes where the class-level prior is
non-adverse (e.g. 'marriage', prior='gain'/'neutral') but genuine transiting
affliction exists. Any v3-only adverse row in such a class is a candidate
instance of exactly the bug W1.2 fixes -- this script reports the raw counts
and the matched/unmatched split; it does not editorialize a verdict.

READ-ONLY BY CONSTRUCTION. This script issues nothing but SELECT against
`kala_gochara_windows` (autocommit, no BEGIN, no writer invoked) -- it never
constructs a DELETE/UPDATE/INSERT of any kind. Safe to run under an active
production-build yield window: this is evidence work, not a build.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/mr23_w12_adverse_golden_comparison.py \\
        [--chart-ids 482012f1-710e-4a25-994a-93821f5871aa 1c826d5a-41cb-4450-b4dc-59d440e5f75a] \\
        [--now-date 2026-08-11] [--horizon-years 3]

Exit codes:
    0 -- report generated successfully for every requested chart (a low or
         zero adverse-match count is a FINDING, not a script failure)
    2 -- a chart's comparison could not be scoped honestly (should be
         structurally impossible given `scope_v1_rows`'s own discipline,
         checked explicitly here rather than trusted silently)
    3 -- the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GENERATION_V1 = "v1"
GENERATION_V3_PROD = "3.0"
PROGRESSIVE_HORIZON_YEARS_DEFAULT = 3

# The two canonical charts per CLAUDE.md §B (the native) and the MSR_UCN
# handoff (Abhinandan Mohanty, the L2+ onboarding second chart).
DEFAULT_CHART_IDS = (
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
)

_WINDOW_COLUMNS = (
    "event_class, temporal_shape, window_start, window_end, peak_date, "
    "is_adverse, valence, signed_intensity, generation, active_sentences"
)


def _compare_one_chart(cur, chart_id: str, *, now_date, horizon_years: int) -> dict:
    from datetime import timedelta
    from services.w2g.equivalence_report import GenerationRow, match_rows, scope_v1_rows

    horizon_start = now_date - timedelta(days=365 * horizon_years)
    horizon_end = now_date + timedelta(days=365 * horizon_years)

    # v3 PRODUCTION -- kala_gochara_windows generation='3.0' (W5.4 UTK-R1's
    # actual authority surface; NOT kala_gochara_windows_v2).
    cur.execute(
        f"SELECT {_WINDOW_COLUMNS} FROM kala_gochara_windows "
        f"WHERE chart_id = %s AND generation = %s",
        [chart_id, GENERATION_V3_PROD],
    )
    v3_rows_raw = cur.fetchall()
    v3_rows_all = [GenerationRow.from_db_row(r) for r in v3_rows_raw]
    classes_attempted = sorted({r.event_class for r in v3_rows_all})

    # v1 -- READ-ONLY, the frozen validation benchmark. Never written.
    cur.execute(
        f"SELECT {_WINDOW_COLUMNS} FROM kala_gochara_windows "
        f"WHERE chart_id = %s AND generation = %s",
        [chart_id, GENERATION_V1],
    )
    v1_rows_raw = cur.fetchall()
    v1_rows_all = [GenerationRow.from_db_row(r) for r in v1_rows_raw]

    # Filter BOTH sides to ADVERSE windows only -- this is the W1.2-specific
    # cut `build_equivalence_report`'s pooled-valence summary does not make.
    v1_adverse_all = [r for r in v1_rows_all if r.is_adverse]
    v3_adverse_all = [r for r in v3_rows_all if r.is_adverse]

    # scope_v1_rows's own discipline (point-shaped, class attempted by v3,
    # inside v3's progressive horizon) -- applied to the ADVERSE-only subset.
    v1_adverse_comparable, out_of_scope = scope_v1_rows(
        v1_adverse_all,
        classes_attempted_by_v2=classes_attempted,
        horizon_start=horizon_start,
        horizon_end=horizon_end,
    )

    matched, v1_only, v3_only = match_rows(v1_adverse_comparable, v3_adverse_all)

    valence_agreeing = sum(1 for m in matched if m.valence_agrees)

    return {
        "chart_id": chart_id,
        "horizon_start": horizon_start.isoformat(),
        "horizon_end": horizon_end.isoformat(),
        "classes_attempted_by_v3": classes_attempted,
        "classes_out_of_scope": out_of_scope,
        # Raw, unscoped totals -- the headline counts.
        "v1_total_rows": len(v1_rows_all),
        "v3_total_rows": len(v3_rows_all),
        "v1_adverse_total": len(v1_adverse_all),
        "v3_adverse_total": len(v3_adverse_all),
        # Comparable-scope + matching detail.
        "v1_adverse_comparable_scope": len(v1_adverse_comparable),
        "v1_adverse_out_of_scope": len(v1_adverse_all) - len(v1_adverse_comparable),
        "matched_count": len(matched),
        "matched_valence_agrees_count": valence_agreeing,
        "v1_adverse_unmatched_count": len(v1_only),
        "v3_adverse_unmatched_count": len(v3_only),
        "v3_adverse_unmatched_by_class": sorted(
            {r.event_class for r in v3_only}
        ),
        "v1_adverse_unmatched_peak_dates": [
            {"event_class": r.event_class, "peak_date": r.peak_date.isoformat()}
            for r in v1_only
        ],
        "v3_adverse_unmatched_sample": [
            {
                "event_class": r.event_class,
                "peak_date": r.peak_date.isoformat(),
                "transit_planets": sorted(r.transit_planets),
            }
            for r in v3_only[:25]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-ids", nargs="*", default=list(DEFAULT_CHART_IDS))
    parser.add_argument(
        "--now-date", default=None,
        help="ISO date anchoring the +/- horizon (default: today)",
    )
    parser.add_argument(
        "--horizon-years", type=int, default=PROGRESSIVE_HORIZON_YEARS_DEFAULT,
        help="+/- years from --now-date to scope the comparison (default: 3, "
             "matching the writer's own progressive-onboarding horizon convention)",
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

    from datetime import date

    now_date = date.fromisoformat(args.now_date) if args.now_date else date.today()

    per_chart = []
    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            for chart_id in args.chart_ids:
                try:
                    per_chart.append(
                        _compare_one_chart(
                            cur, chart_id, now_date=now_date,
                            horizon_years=args.horizon_years,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"ERROR: could not honestly scope chart {chart_id}: {exc}",
                        file=sys.stderr,
                    )
                    return 2

    result = {
        "comparator_generation_v1": GENERATION_V1,
        "comparator_generation_v3": GENERATION_V3_PROD,
        "comparator_table": "kala_gochara_windows (both generations; production v3 = W5.4 UTK-R1 repoint)",
        "per_chart": per_chart,
        "totals": {
            "v1_adverse_total": sum(c["v1_adverse_total"] for c in per_chart),
            "v3_adverse_total": sum(c["v3_adverse_total"] for c in per_chart),
            "matched_count": sum(c["matched_count"] for c in per_chart),
            "v1_adverse_unmatched_count": sum(c["v1_adverse_unmatched_count"] for c in per_chart),
            "v3_adverse_unmatched_count": sum(c["v3_adverse_unmatched_count"] for c in per_chart),
        },
    }
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
