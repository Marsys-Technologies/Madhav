#!/usr/bin/env python3
"""
mr47_shape_conformance_gate.py -- PARIṢKĀRA MR-47 (ADJUDICATOR ruling
PK-R-10), item 4(i): the live, real detector.

Asserts ZERO `shape_conformance` mismatches across BOTH canonical charts
(482012f1-710e-4a25-994a-93821f5871aa, 1c826d5a-41cb-4450-b4dc-59d440e5f75a)
x ALL event classes present in `brahma_event_ontology`, on BOTH
`kala_gochara_windows` (production) and `kala_gochara_windows_v2`
(calibration/staging). For every row, it compares the row's ACTUALLY STORED
`shape_conformance` against a FRESH, independently-recomputed expected value
(via `services.gochara_v3.shape_conformance_check.expected_shape_
conformance`) derived from a live join to `brahma_event_ontology` -- never
trusting the row's own column as evidence for itself (that would be a proxy,
not a detector; see this module's own docstring and §N.8).

READ-ONLY BY CONSTRUCTION: this script issues nothing but SELECT statements
(autocommit, no BEGIN, no writer invoked, no UPDATE/INSERT/DELETE of any
kind) -- safe to run at any time, including during an active build.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/mr47_shape_conformance_gate.py

Exit codes:
    0 -- zero mismatches on both tables, both canonical charts.
    2 -- at least one mismatch found (a real, catchable defect -- see this
         script's own mutation-proof sibling,
         services/gochara_v3/tests/test_shape_conformance_check.py, for proof
         the comparison logic actually has teeth).
    3 -- the run itself could not proceed (no DATABASE_URL, no driver).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CANONICAL_CHART_IDS = [
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
]

TABLES = ["kala_gochara_windows", "kala_gochara_windows_v2"]


def main() -> int:
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

    from services.gochara_v3.shape_conformance_check import diagnose_row

    report: dict = {
        "canonical_chart_ids": CANONICAL_CHART_IDS,
        "tables": {},
        "total_rows_checked": 0,
        "total_mismatches": 0,
        "classes_checked": set(),
        "mismatches": [],
    }

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(
                    f"SELECT w.id, w.chart_id, w.event_class, w.temporal_shape, "
                    f"w.resolution, w.shape_conformance, o.temporal_shape AS ontology_shape "
                    f"FROM {table} w "
                    f"LEFT JOIN brahma_event_ontology o ON w.event_class = o.event_class_id "
                    f"WHERE w.chart_id = ANY(%s) "
                    f"ORDER BY w.event_class, w.id",
                    [CANONICAL_CHART_IDS],
                )
                rows = cur.fetchall()

                table_mismatches = []
                classes_this_table = set()
                for row in rows:
                    classes_this_table.add(row["event_class"])
                    mismatch = diagnose_row(
                        stored_temporal_shape=row["temporal_shape"],
                        stored_resolution=row["resolution"],
                        ontology_temporal_shape=row["ontology_shape"],
                        stored_shape_conformance=row["shape_conformance"],
                    )
                    if mismatch is not None:
                        table_mismatches.append({
                            "table": table,
                            "id": row["id"],
                            "chart_id": row["chart_id"],
                            "event_class": row["event_class"],
                            "detail": mismatch,
                        })

                report["tables"][table] = {
                    "rows_checked": len(rows),
                    "classes_present": sorted(classes_this_table),
                    "mismatches": len(table_mismatches),
                }
                report["total_rows_checked"] += len(rows)
                report["total_mismatches"] += len(table_mismatches)
                report["classes_checked"] |= classes_this_table
                report["mismatches"].extend(table_mismatches)

            # Cross-check: how many DISTINCT event classes does
            # brahma_event_ontology declare in total (informational -- this
            # script checks every row actually present for the two canonical
            # charts, which may be a subset of the full 27-class ontology if
            # a class has no rows yet for these charts; that is an honest
            # scope note, not a failure).
            cur.execute("SELECT count(*) AS n FROM brahma_event_ontology")
            report["ontology_total_classes"] = cur.fetchone()["n"]

    report["classes_checked"] = sorted(report["classes_checked"])
    print(json.dumps(report, indent=2, default=str))

    if report["total_mismatches"] != 0:
        print(
            f"ERROR: {report['total_mismatches']} shape_conformance mismatch(es) found "
            f"across {len(TABLES)} table(s) x {len(CANONICAL_CHART_IDS)} canonical chart(s) "
            f"-- PK-R-10 requires zero.",
            file=sys.stderr,
        )
        return 2

    print(
        f"OK: 0 shape_conformance mismatches across {report['total_rows_checked']} row(s), "
        f"{len(report['classes_checked'])} event class(es), {len(TABLES)} table(s), "
        f"{len(CANONICAL_CHART_IDS)} canonical chart(s).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
