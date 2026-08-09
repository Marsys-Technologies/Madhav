"""
backfill_lel_event_class_resolution.py — SAMPURTI L0f (G14a).

READ-ONLY preview mode (default) OR live persist mode (--persist flag).

Usage (READ-ONLY, default):
    python3 scripts/backfill_lel_event_class_resolution.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa

Usage (persist, Wave-0 gate/deploy only — gated behind --persist):
    python3 scripts/backfill_lel_event_class_resolution.py \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa \\
        --persist

CRITICAL RAIL: this script feeds lel_event_class_resolution (scoring only).
It NEVER touches:
  - ka_kshetra or any bodha layer table
  - chart_facts (L1 sealed, R19)
  - any interpretive layer table

Coverage assertion: classified_count + ambiguous_count == total_input_count
is enforced by the resolver itself (CoverageAssertionError on violation).

R16: every output row carries resolver_version + rule_matched + matched_tokens.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# ── Path setup ────────────────────────────────────────────────────────────────
_SIDECAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SIDECAR)

import psycopg
import psycopg.rows

from brahmagyan.lel_event_class_resolver import (
    CONFIDENCE_AMBIGUOUS,
    RESOLVER_VERSION,
    resolve_batch,
)

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _fetch_life_events(conn, chart_id: str) -> list[dict]:
    """Read life_events rows for a chart (READ-ONLY)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            "SELECT event_id, category, domain "
            "FROM life_events "
            "WHERE chart_id = %s "
            "ORDER BY event_date",
            (chart_id,),
        )
        return cur.fetchall()


def _persist_results(conn, chart_id: str, results) -> int:
    """Upsert resolution results into lel_event_class_resolution. Returns row count."""
    count = 0
    with conn.cursor() as cur:
        for r in results:
            cur.execute(
                """
                INSERT INTO lel_event_class_resolution
                  (chart_id, event_id, resolved_event_class, confidence,
                   rule_matched, matched_tokens, candidates, resolver_version,
                   audit_trail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (chart_id, event_id)
                DO UPDATE SET
                    resolved_event_class = EXCLUDED.resolved_event_class,
                    confidence           = EXCLUDED.confidence,
                    rule_matched         = EXCLUDED.rule_matched,
                    matched_tokens       = EXCLUDED.matched_tokens,
                    candidates           = EXCLUDED.candidates,
                    resolver_version     = EXCLUDED.resolver_version,
                    audit_trail          = EXCLUDED.audit_trail,
                    resolved_at          = now()
                """,
                (
                    chart_id,
                    r.event_id,
                    r.event_class,
                    r.confidence,
                    r.rule_matched,
                    r.matched_tokens,
                    r.candidates or [],
                    r.resolver_version,
                    json.dumps(r.audit_trail),
                ),
            )
            count += 1
    conn.commit()
    return count


def _print_classification_table(results, chart_id: str) -> None:
    """Print the full classification table to stdout."""
    classified = [r for r in results if r.confidence != CONFIDENCE_AMBIGUOUS]
    ambiguous = [r for r in results if r.confidence == CONFIDENCE_AMBIGUOUS]

    print(f"\n{'='*100}")
    print(f"L0f RESOLVER BACKFILL PREVIEW — chart_id={chart_id}")
    print(f"resolver_version={RESOLVER_VERSION}  total_rows={len(results)}")
    print(f"classified={len(classified)}  ambiguous={len(ambiguous)}")
    print(f"{'='*100}\n")

    # Header
    col_w = [52, 22, 14, 34, 14]
    hdr = (
        f"{'event_id':<{col_w[0]}} "
        f"{'event_class':<{col_w[1]}} "
        f"{'confidence':<{col_w[2]}} "
        f"{'rule_matched':<{col_w[3]}} "
        f"{'matched_tokens (trunc)':<{col_w[4]}}"
    )
    print(hdr)
    print("-" * sum(col_w))

    for r in results:
        ec = r.event_class or "—"
        toks = r.matched_tokens[:32] if r.matched_tokens else ""
        print(
            f"{r.event_id:<{col_w[0]}} "
            f"{ec:<{col_w[1]}} "
            f"{r.confidence:<{col_w[2]}} "
            f"{r.rule_matched:<{col_w[3]}} "
            f"{toks:<{col_w[4]}}"
        )

    print(f"\n{'='*100}")
    if ambiguous:
        print(f"\nAMBIGUOUS rows ({len(ambiguous)}) — listed with candidates:\n")
        for r in ambiguous:
            print(f"  event_id={r.event_id}")
            print(f"    category={r.category!r}  domain={r.domain!r}")
            print(f"    rule_matched={r.rule_matched!r}")
            print(f"    candidates={r.candidates!r}")
    else:
        print("\nNo AMBIGUOUS rows.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LEL→event_class resolver backfill (SAMPURTI L0f G14a)"
    )
    parser.add_argument(
        "--chart-id",
        default=CANONICAL_CHART_ID,
        help=f"chart_id to backfill (default: {CANONICAL_CHART_ID})",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write results to lel_event_class_resolution (Wave-0 gate only). "
             "Default is READ-ONLY preview.",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="PostgreSQL connection URL (or set DATABASE_URL env var)",
    )
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: --db-url or DATABASE_URL required", file=sys.stderr)
        sys.exit(1)

    print(f"[L0f resolver] Connecting to DB... (chart_id={args.chart_id})")
    with psycopg.connect(args.db_url) as conn:
        rows = _fetch_life_events(conn, args.chart_id)
        print(f"[L0f resolver] Fetched {len(rows)} life_events rows.")

        # resolve_batch internally calls assert_coverage (raises on silent drop)
        results = resolve_batch(rows)

        _print_classification_table(results, args.chart_id)

        classified = [r for r in results if r.confidence != CONFIDENCE_AMBIGUOUS]
        ambiguous = [r for r in results if r.confidence == CONFIDENCE_AMBIGUOUS]
        assert len(classified) + len(ambiguous) == len(rows), (
            "Coverage assertion: classified + ambiguous must equal total rows"
        )

        if args.persist:
            print(f"[L0f resolver] --persist flag set: writing to lel_event_class_resolution...")
            n = _persist_results(conn, args.chart_id, results)
            print(f"[L0f resolver] Persisted {n} rows (ON CONFLICT DO UPDATE).")
        else:
            print("[L0f resolver] READ-ONLY mode (no --persist). "
                  "No rows written to DB.")

    print(
        f"[L0f resolver] Done. classified={len(classified)} "
        f"ambiguous={len(ambiguous)} total={len(rows)}"
    )


if __name__ == "__main__":
    main()
