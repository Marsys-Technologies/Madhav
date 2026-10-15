#!/usr/bin/env python3
"""sealed_generation_staleness.py — READ-ONLY fresh/stale report for ONE sealed
ka_gochara generation (C35).

A sealed generation is FRESH when the inputs it consumed are still exactly what the
seal pinned. This script asks the database itself — it calls ONLY the EXISTING
migration-1206 functions and never re-implements their logic:

  * public.ka_gochara_search_l1_facts_digest(chart, consumed_fact_ids) — live digest
    of the consumed L1 fact rows, compared against the snapshot's l1_facts_digest;
  * public.ka_gochara_search_dasha_digest(chart, consumed_dasha_row_ids) — same for
    the consumed daśā rows;
  * public.ka_gochara_search_completeness_violations(chart, generation) — the 1206
    completeness/drift census (must return zero rows).

READ-ONLY BY CONSTRUCTION: the session is forced read-only
(SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY) and every statement issued
is a SELECT. The script writes nothing, seals nothing, refreshes nothing.

Usage:
    DATABASE_URL=postgresql://... python3 sealed_generation_staleness.py \
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa --generation 5.0

Exit codes:
    0 — FRESH (snapshot digests match live, zero completeness violations)
    4 — STALE (a digest drifted or the completeness census is non-empty)
    3 — the check could not run (no DATABASE_URL, no driver, no sealed snapshot,
        or a database error) — an ERROR is never reported as FRESH
"""
from __future__ import annotations

import argparse
import json
import os
import sys


class SnapshotMissing(Exception):
    """No ka_gochara_search_input_snapshot row — the generation is not sealed."""


def check_staleness(conn, chart_id: str, generation: str) -> dict:
    """Run the read-only staleness check on an open connection.

    Returns a report dict: {chart_id, generation, status, reasons[]}.
    Raises SnapshotMissing when the generation has no sealed input snapshot.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT consumed_fact_ids, consumed_dasha_row_ids, l1_facts_digest, dasha_digest "
            "FROM public.ka_gochara_search_input_snapshot "
            "WHERE chart_id = %s AND generation = %s",
            [chart_id, generation],
        )
        snap = cur.fetchone()
        if snap is None:
            raise SnapshotMissing(
                f"no sealed input snapshot for chart {chart_id} generation {generation}"
            )
        consumed_fact_ids, consumed_dasha_row_ids, snap_l1, snap_dasha = (
            snap[0], snap[1], snap[2], snap[3],
        )

        cur.execute(
            "SELECT public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[])",
            [chart_id, list(consumed_fact_ids)],
        )
        live_l1 = cur.fetchone()[0]
        cur.execute(
            "SELECT public.ka_gochara_search_dasha_digest(%s::uuid, %s::uuid[])",
            [chart_id, list(consumed_dasha_row_ids)],
        )
        live_dasha = cur.fetchone()[0]

        cur.execute(
            "SELECT event_class, violation, detail "
            "FROM public.ka_gochara_search_completeness_violations(%s::uuid, %s)",
            [chart_id, generation],
        )
        violations = cur.fetchall()

    reasons = []
    if live_l1 != snap_l1:
        reasons.append(
            "l1_facts_digest drift: snapshot "
            f"{snap_l1} vs live {live_l1} — a consumed L1 fact row changed"
        )
    if live_dasha != snap_dasha:
        reasons.append(
            "dasha_digest drift: snapshot "
            f"{snap_dasha} vs live {live_dasha} — a consumed daśā row changed"
        )
    for event_class, violation, detail in violations:
        reasons.append(f"completeness violation [{event_class}] {violation}: {detail}")

    return {
        "chart_id": chart_id,
        "generation": generation,
        "status": "fresh" if not reasons else "stale",
        "reasons": reasons,
    }


def run(conn, chart_id: str, generation: str) -> int:
    """Force the session read-only, run the check, print the JSON report."""
    with conn.cursor() as cur:
        cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    report = check_staleness(conn, chart_id, generation)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "fresh" else 4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", required=True, help="sealed generation, e.g. 5.0")
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

    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            return run(conn, args.chart_id, args.generation)
    except SnapshotMissing as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"ERROR: the staleness check could not run: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
