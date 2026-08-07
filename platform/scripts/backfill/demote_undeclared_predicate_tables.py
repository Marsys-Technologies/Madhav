#!/usr/bin/env python3
"""demote_undeclared_predicate_tables.py — T2 of the post-salvage close-out.

`platform/scripts/audit/verification_invariant.py`'s `check_claim_vs_evidence` flags any table
whose `two_pass_verified` rows have NO entry in `EXAMINED_PREDICATE`: "Undeclared is not exempt —
declare what a verifier reads for this table, or demote the rows." Four tables carry that FAIL
with no predicate defined at all (not a partial-coverage gap — zero declared coverage):

    bodha_cgm_edges, bodha_cgm_nodes, bodha_msr_signals, l1_tajik_varsha_year_lords

Owner ruling (post-salvage close-out, 2026-08-06): take the badge down. Demote every
`two_pass_verified` row in these four tables to the honest `single` tier — the same demotion
class as `backfill_unexamined_dasha_tiers.py` (an overclaim correction, never a promotion).
Genuinely-earned rows would need a real EXAMINED_PREDICATE entry to survive this; since none is
declared for any of the four, none are exempted.

LEGAL-TIER CHECK
----------------
Re-derived at runtime from `pg_constraint`, never assumed: for each table, if a CHECK constraint
on `verification_pass_status` exists, this script parses its allowed literals and refuses to run
unless `single` is among them. If no such CHECK constraint exists (true for all four tables as of
this writing — confirmed via direct query, not asserted here), the tier is unconstrained at the DB
level and the write proceeds.

USAGE
-----
    python demote_undeclared_predicate_tables.py                 # DRY RUN (default)
    python demote_undeclared_predicate_tables.py --execute       # writes, with a TOCTOU re-check
                                                                   # immediately before the UPDATE

DATABASE_URL is read from the environment and is never taken as an argument.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT, VERIFIED_STATUSES  # noqa: E402

TABLES: tuple[str, ...] = (
    "bodha_cgm_edges",
    "bodha_cgm_nodes",
    "bodha_msr_signals",
    "l1_tajik_varsha_year_lords",
)


def _check_constraint_literals(cur, table: str) -> set[str] | None:
    """The CHECK-constrained legal set for `table.verification_pass_status`, or None if no such
    CHECK constraint exists (the column is unconstrained at the DB level)."""
    cur.execute(
        """
        SELECT pg_get_constraintdef(c.oid)
        FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
        WHERE c.contype = 'c' AND t.relname = %s
          AND pg_get_constraintdef(c.oid) ILIKE %s
        """,
        (table, "%verification_pass_status%"),
    )
    rows = cur.fetchall()
    if not rows:
        return None
    literals: set[str] = set()
    for (defn,) in rows:
        literals |= set(re.findall(r"'([^']+)'", defn))
    return literals


def _claiming_count(cur, table: str) -> int:
    cur.execute(
        f'SELECT count(*) FROM "{table}" WHERE verification_pass_status = ANY(%s)',  # noqa: S608
        (sorted(VERIFIED_STATUSES),),
    )
    return cur.fetchone()[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="write (default is a dry run)")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set; refusing to guess.", file=sys.stderr)
        return 2

    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        for tbl in TABLES:
            legal = _check_constraint_literals(cur, tbl)
            shape = sorted(legal) if legal is not None else "(none declared — unconstrained)"
            print(f"{tbl}: CHECK constraint on verification_pass_status = {shape}")
            if legal is not None and UNVERIFIED_DEFAULT not in legal:
                print(
                    f"HALT: {UNVERIFIED_DEFAULT!r} is not legal for {tbl} (CHECK allows: {sorted(legal)}).",
                    file=sys.stderr,
                )
                return 2

        predicted: dict[str, int] = {tbl: _claiming_count(cur, tbl) for tbl in TABLES}
        total_predicted = sum(predicted.values())
        for tbl in TABLES:
            print(
                f"  [{'EXECUTE' if args.execute else 'DRY RUN'}] {tbl}: {predicted[tbl]:,} row(s) "
                f"claiming {sorted(VERIFIED_STATUSES)} with no EXAMINED_PREDICATE "
                f"-> would demote to {UNVERIFIED_DEFAULT!r}"
            )

        if not args.execute:
            print(f"\nWould demote {total_predicted:,} row(s) total across {len(TABLES)} tables.")
            print("Dry run only. Re-run with --execute to write.")
            return 0

        # TOCTOU re-check immediately before writing — refuse silently proceeding on drift.
        for tbl in TABLES:
            n = _claiming_count(cur, tbl)
            if n != predicted[tbl]:
                print(
                    f"HALT: TOCTOU drift on {tbl}: predicted {predicted[tbl]:,}, now {n:,}. "
                    f"Re-run to re-predict.",
                    file=sys.stderr,
                )
                return 3

        actual: dict[str, int] = {}
        for tbl in TABLES:
            cur.execute(
                f'UPDATE "{tbl}" SET verification_pass_status = %s '  # noqa: S608
                f"WHERE verification_pass_status = ANY(%s)",
                (UNVERIFIED_DEFAULT, sorted(VERIFIED_STATUSES)),
            )
            actual[tbl] = cur.rowcount

        conn.commit()

        mismatches = [
            (tbl, predicted[tbl], actual[tbl]) for tbl in TABLES if actual[tbl] != predicted[tbl]
        ]
        for tbl in TABLES:
            print(f"  [EXECUTED] {tbl}: {actual[tbl]:,} row(s) demoted (predicted {predicted[tbl]:,})")

        for tbl in TABLES:
            remaining = _claiming_count(cur, tbl)
            print(f"  [POST-STATE] {tbl}: {remaining} row(s) still claiming a verified tier (expected 0).")

    if mismatches:
        print(f"\nWARNING: predicted-vs-actual mismatch: {mismatches}", file=sys.stderr)
        return 1

    print(f"\nDemoted {sum(actual.values()):,} row(s) total across {len(TABLES)} tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
