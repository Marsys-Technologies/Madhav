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

Corrected check (S-L1 rehearsal P3, SS-ruled; `brahmagyan/fact_identity_check.py`):
every run evaluates and prints it. `--check` makes a FAILED check fatal: the
chart's transaction is rolled back (the prior index is left untouched) and the
script exits 4. In a dry-run, `rows == parsed` has no detector (nothing is
written) and is reported NOT_EVALUATED, never PASS.

RUNBOOK FACTS (W7 read-back):
  * Run this AFTER every ga_* build has finished (start of W7). `chart_fact_identity`
    is FK `ON DELETE CASCADE` to `chart_facts`, so any later delete-then-insert
    rebuild of a ga_* writer empties the rows of every replaced fact; a run in
    the middle of the build window is undone by the next writer.
  * Run as role `amjis_app` or `role_orchestrator`. `data_plane_builder` has no
    privilege on the table.
  * The index is NOT 1,205 rows after this script: 1,205 is the `ga_positions`
    row count (what survives the cascade), not the G-IDX result.

Usage with the gate:
    DATABASE_URL=... python3 scripts/build_fact_identity_index.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa --check

Exit codes:
    0 — completed (per-chart summary printed; an honest 0-row parse for a
        chart with no facts is not a failure unless --check, where an empty
        chart FAILS `facts_present`)
    2 — a chart's population failed (DB error mid-transaction; rolled back)
    3 — the run itself could not proceed (no DATABASE_URL, no driver)
    4 — `--check` and the corrected check FAILED (rolled back, nothing written)
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brahmagyan.fact_identity_check import (  # noqa: E402
    IDENTITY_FREE_REASONS_ALLOWED,
    check_identity_index,
    classify_fact,
)

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
                    kind, payload = classify_fact(fact_category, fact_subject, fact_key)
                    if kind == "parsed":
                        match = payload
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

                    if kind == "identity_free":
                        identity_free += 1
                        identity_free_reasons[payload] = identity_free_reasons.get(payload, 0) + 1
                    else:  # "gap": neither parsed nor a recognised identity-free token
                        gap += 1
                        key = (fact_category, fact_key)
                        if key not in gap_examples:
                            gap_examples[key] = fact_subject

            if rows_to_insert and not dry_run:
                write_cur.executemany(INSERT_SQL, rows_to_insert)

            # The detector behind `rows == parsed`: count what is ACTUALLY in the
            # table for this chart after the insert (same transaction). Not
            # measured in a dry-run -> None (NOT_EVALUATED), never assumed.
            rows_in_table = None
            if not dry_run:
                write_cur.execute(
                    "SELECT count(*) FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                rows_in_table = int(write_cur.fetchone()[0])

    denom = parsed + gap
    coverage_pct = (100.0 * parsed / denom) if denom else 100.0

    return {
        "chart_id": chart_id,
        "deleted_prior_rows": deleted,
        "total_facts": total,
        "parsed": parsed,
        "identity_free": identity_free,
        "gap": gap,
        "rows_in_table": rows_in_table,
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
    parser.add_argument("--check", action="store_true",
                         help="a FAILED corrected check is fatal: roll the chart back, exit 4 "
                              "(the check is always evaluated and printed either way)")
    parser.add_argument("--reasons-mode", choices=("exact", "subset"), default="exact",
                         help="identity_free reason-set rule: 'exact' (SS rule, default: observed == "
                              "the 14 + scope_cap_sentinel) or 'subset' (observed <= allowed; for a "
                              "chart not rebuilt by every S-L1 writer). A NEW reason fails in both.")
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
                result = check_identity_index(
                    summary, exact_reasons=(args.reasons_mode == "exact"),
                )
                if args.dry_run or (args.check and result.failed):
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
        print(f"rows_in_table={summary['rows_in_table']}")
        print(f"corrected_check (allowed reasons: {len(IDENTITY_FREE_REASONS_ALLOWED)}, mode={args.reasons_mode}):")
        print(result.render())
        if result.failed:
            print(f"CHECK: FAIL ({', '.join(i.name for i in result.failed)})"
                  + (" -- rolled back, nothing written" if args.check else " -- NOT fatal without --check"))
            if args.check:
                overall_exit = 4
        elif result.not_evaluated:
            print(f"CHECK: NOT_EVALUATED ({', '.join(i.name for i in result.not_evaluated)}) -- no failures"
                  + (" (dry-run)" if args.dry_run else ""))
        else:
            print("CHECK: PASS")
        if summary["gap_examples"]:
            print("GAP examples (category, key) -> subject:")
            for k, v in summary["gap_examples"].items():
                print(f"  {k} -> {v!r}")

    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
