#!/usr/bin/env python3
"""
build_fact_identity_index.py — populate `chart_fact_identity` (migration
552) from `chart_facts` for ONE chart, using the single deterministic
parser at `brahmagyan/fact_identity_parser.py`.

ADHIṢṬHĀNA Campaign A, Lane A5 (THE FACT IDENTITY INDEX).

R19 (chart_facts stays sealed): this script only ever SELECTs from
`chart_facts`. It writes exclusively to `chart_fact_identity` — its own
derived table — and is fully idempotent per CLAUDE.md §N.3 (L1+ standard):
every run first DELETEs this chart's existing `chart_fact_identity` rows,
then INSERTs a fresh set computed from the current `chart_facts` contents.
Rebuild REPLACES, never accretes. Safe to re-run at any time, including
against a chart whose `chart_facts` has since been rebuilt with a new
`build_id` — the Index always reflects whatever is live in `chart_facts`
at run time, nothing cached from a prior run survives.

This script is standalone (NOT a `WriterBase`/`@register` orchestrator
writer) per the lane's explicit scope boundary — Lane A5 stops at a
checkpoint before any orchestrator/engine work.

Usage:
    DATABASE_URL=postgresql://... python3 scripts/build_fact_identity_index.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa [--dry-run]

    # Or against all three canonical charts:
    DATABASE_URL=... python3 scripts/build_fact_identity_index.py --all-canonical

Exit codes:
    0 — completed (per-chart summary printed; an honest 0-row parse for a
        chart with no facts is not a failure)
    2 — a chart's population failed (DB error mid-transaction; rolled back)
    3 — the run itself could not proceed (no DATABASE_URL, no driver)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brahmagyan.fact_identity_parser import classify_unparsed_subject, parse_fact_identity  # noqa: E402

CANONICAL_CHART_IDS = [
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
    "cb73cd3d-9eba-4220-9902-0de91566e980",
]

FETCH_BATCH = 20_000
INSERT_BATCH = 5_000

INSERT_SQL = """
    INSERT INTO chart_fact_identity (
        fact_id, chart_id, entity_kind, graha_code, graha_code_secondary,
        house_num, house_num_secondary, varga_id, sign_num,
        parse_rule, parsed_from, build_id, computed_at
    ) VALUES (
        %(fact_id)s, %(chart_id)s, %(entity_kind)s, %(graha_code)s, %(graha_code_secondary)s,
        %(house_num)s, %(house_num_secondary)s, %(varga_id)s, %(sign_num)s,
        %(parse_rule)s, %(parsed_from)s, %(build_id)s, now()
    )
"""


def _parsed_from(fact_subject: str, fact_key: str | None) -> str:
    return f"fact_subject={fact_subject!r};fact_key={fact_key!r}"


def build_index_for_chart(conn, chart_id: str, dry_run: bool = False) -> dict:
    """Delete-then-insert scoped to `chart_id` (§N.3). Returns a summary
    dict with the real, computed counts (§N.8 — every number here comes
    from an actual detector query / actual row count, not an estimate)."""
    import psycopg
    from psycopg.rows import tuple_row

    t0 = time.time()
    total = parsed = identity_free = gap = 0
    entity_kind_counts: dict[str, int] = {}
    identity_free_reasons: dict[str, int] = {}
    gap_examples: dict[tuple, str] = {}

    with conn.cursor(row_factory=tuple_row) as read_cur:
        read_cur.execute(
            "SELECT fact_id, fact_category, fact_subject, fact_key, build_id "
            "FROM chart_facts WHERE chart_id = %s",
            (chart_id,),
        )
        rows_to_insert = []

        with conn.cursor() as write_cur:
            if not dry_run:
                write_cur.execute(
                    "DELETE FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                deleted = write_cur.rowcount
            else:
                deleted = None

            while True:
                batch = read_cur.fetchmany(FETCH_BATCH)
                if not batch:
                    break
                for fact_id, fact_category, fact_subject, fact_key, build_id in batch:
                    total += 1
                    match = parse_fact_identity(fact_subject, fact_key, fact_category)
                    if match is not None:
                        parsed += 1
                        entity_kind_counts[match.entity_kind] = entity_kind_counts.get(match.entity_kind, 0) + 1
                        rows_to_insert.append({
                            "fact_id": fact_id,
                            "chart_id": chart_id,
                            "entity_kind": match.entity_kind,
                            "graha_code": match.graha_code,
                            "graha_code_secondary": match.graha_code_secondary,
                            "house_num": match.house_num,
                            "house_num_secondary": match.house_num_secondary,
                            "varga_id": match.varga_id,
                            "sign_num": match.sign_num,
                            "parse_rule": match.parse_rule,
                            "parsed_from": _parsed_from(fact_subject, fact_key),
                            "build_id": str(build_id) if build_id else None,
                        })
                        if len(rows_to_insert) >= INSERT_BATCH and not dry_run:
                            write_cur.executemany(INSERT_SQL, rows_to_insert)
                            rows_to_insert = []
                        continue

                    cls = classify_unparsed_subject(fact_subject, fact_category)
                    if cls is not None:
                        identity_free += 1
                        identity_free_reasons[cls] = identity_free_reasons.get(cls, 0) + 1
                    else:
                        gap += 1
                        key = (fact_category, fact_key)
                        if key not in gap_examples:
                            gap_examples[key] = fact_subject

            if rows_to_insert and not dry_run:
                write_cur.executemany(INSERT_SQL, rows_to_insert)

    denom = parsed + gap
    coverage_pct = (100.0 * parsed / denom) if denom else 100.0

    return {
        "chart_id": chart_id,
        "deleted_prior_rows": deleted,
        "total_facts": total,
        "parsed": parsed,
        "identity_free": identity_free,
        "gap": gap,
        "coverage_of_identity_bearing_pct": round(coverage_pct, 4),
        "entity_kind_counts": entity_kind_counts,
        "identity_free_reasons": identity_free_reasons,
        "gap_examples": gap_examples,
        "elapsed_sec": round(time.time() - t0, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chart-id")
    group.add_argument("--all-canonical", action="store_true",
                        help="run for all three canonical charts sequentially")
    parser.add_argument("--dry-run", action="store_true",
                         help="parse and report only; no DELETE/INSERT")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL is required", file=sys.stderr)
        return 3

    try:
        import psycopg  # noqa: F401
    except ImportError as exc:
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        return 3

    chart_ids = CANONICAL_CHART_IDS if args.all_canonical else [args.chart_id]

    overall_exit = 0
    for chart_id in chart_ids:
        print(f"\n{'=' * 78}\nBuilding chart_fact_identity for chart_id={chart_id} "
              f"(dry_run={args.dry_run})\n{'=' * 78}")
        try:
            with psycopg.connect(dsn) as conn:
                summary = build_index_for_chart(conn, chart_id, dry_run=args.dry_run)
                if args.dry_run:
                    conn.rollback()
                else:
                    conn.commit()
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: chart {chart_id} failed: {exc}", file=sys.stderr)
            overall_exit = 2
            continue

        print(f"total_facts={summary['total_facts']}")
        print(f"deleted_prior_rows={summary['deleted_prior_rows']}")
        print(f"parsed={summary['parsed']}")
        print(f"identity_free={summary['identity_free']}")
        print(f"gap={summary['gap']}")
        print(f"coverage_of_identity_bearing_pct={summary['coverage_of_identity_bearing_pct']}")
        print(f"elapsed_sec={summary['elapsed_sec']}")
        print("entity_kind_counts:")
        for k, v in sorted(summary["entity_kind_counts"].items(), key=lambda kv: -kv[1]):
            print(f"  {v:8d}  {k}")
        print("identity_free_reasons:")
        for k, v in sorted(summary["identity_free_reasons"].items(), key=lambda kv: -kv[1]):
            print(f"  {v:8d}  {k}")
        if summary["gap_examples"]:
            print("GAP examples (category, key) -> subject:")
            for k, v in summary["gap_examples"].items():
                print(f"  {k} -> {v!r}")

    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
