#!/usr/bin/env python3
"""drain_prohibited_verification_status.py — normalise the label residue in
`verification_pass_status` left behind when the writers were fixed but the data never was.

WHAT THIS DOES, AND WHAT IT DOES NOT
------------------------------------
It rewrites three stored spellings to the single canonical member the settled vocabulary
already designates:

    'PASS'        -> 'single'   PROHIBITED (DVA Ruling 13) — names no pass that ran
    'pass'        -> 'single'   PROHIBITED (same)
    'single_pass' -> 'single'   LEGAL but `deprecated_alias_of="single"`

It changes **no claim**. `isVerifiedPassStatus()` (platform/src/lib/retrieval/envelope.ts)
counts exactly one member as grounding — `two_pass_verified` — so all three source values and
the target value are equally unverified to every serve-layer consumer. Measured on the live DB
before writing this script: `grounding_score` is identical before and after for every affected
fact_category (all 0.0000), so no epistemic grade and no warranty sentence moves.

It is NOT the demotion. The ~392,001 unearned `two_pass_verified` rows keep their tier; that
decision is the native's and is still open.

TARGETS AND CONSTRAINTS
-----------------------
Most target tables carry no CHECK constraint on this column at all; a handful do. Guard 1
re-derives the full CHECK-constrained-table set from `pg_constraint` at runtime — this
docstring deliberately does not name those tables or count them, so it cannot go stale again
the next time a new CHECK-constrained table appears (as `kala_tithi_pravesha` did after this
paragraph was first written, self-halting the run safely until the guard below was corrected
to match).

For each CHECK-constrained table found at runtime, the guard HALTs only if the CHECK permits
at least one of the retired source spellings (`'PASS'`, `'pass'`, `'single_pass'`) while
rejecting the target (`'single'`) — that is the only shape that could raise a live
CheckViolation. A table whose CHECK permits none of the source values structurally cannot
hold a drain-eligible row (nothing this drain would ever try to write there was legal to
store in the first place), so the guard emits an informational NOTE instead of halting. A
table whose CHECK already permits the target passes silently.

USAGE
-----
    python drain_prohibited_verification_status.py                # DRY RUN (default) — counts only
    python drain_prohibited_verification_status.py --execute      # writes, one transaction per table

DATABASE_URL is read from the environment. This script never takes a credential as an argument.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

from brahmagyan.verification_vocab import (  # noqa: E402
    PROHIBITED_STATUSES,
    RESTRICTED_TABLES,
    UNVERIFIED_DEFAULT,
    canonical,
)

#: Every source spelling this drain retires, resolved through the vocabulary module itself
#: rather than restated as literals. `canonical()` maps the deprecated alias; the prohibited
#: pair has no vocabulary entry at all (that is what "prohibited" means), so it maps to the
#: module's declared default for "no detector ran".
SOURCE_VALUES: tuple[str, ...] = tuple(sorted(PROHIBITED_STATUSES | {"single_pass"}))


def target_for(value: str) -> str:
    """The canonical replacement for a retired spelling."""
    resolved = canonical(value)
    return UNVERIFIED_DEFAULT if resolved == value and value in PROHIBITED_STATUSES else resolved


def guard1_verdict(tbl: str, defn: str) -> tuple[bool, list[str]]:
    """Guard 1's per-table verdict for one CHECK constraint definition string.

    Pure text check over `defn` (the constraint definition already fetched from
    `pg_constraint`) — no DB access, so it is unit-testable with a fabricated `defn`.

    Returns `(halt, messages)`. `halt` is True only when the CHECK permits at least one
    of the retired SOURCE_VALUES while rejecting the target (UNVERIFIED_DEFAULT) — the
    only shape that could raise a live CheckViolation on this drain's UPDATE. A table
    whose CHECK permits none of the source values structurally cannot hold a
    drain-eligible row, so that case is reported as an informational NOTE, never a HALT
    (this is the `kala_tithi_pravesha` fix: its CHECK permits only
    `two_pass_verified`/`divergent_flagged` — none of our sources — so rejecting the
    target there is not a hazard). `messages` are pre-formatted lines, each prefixed
    `HALT:` or `NOTE:`, for the caller to print (HALT lines to stderr, NOTE to stdout).
    """
    permits_target = f"'{UNVERIFIED_DEFAULT}'" in defn
    permitted_sources = [v for v in SOURCE_VALUES if f"'{v}'" in defn]

    if permitted_sources and not permits_target:
        return True, [
            f"HALT: {tbl}'s CHECK permits source value(s) {permitted_sources} "
            f"but rejects {UNVERIFIED_DEFAULT!r}: {defn}"
        ]

    messages: list[str] = []
    if not permits_target and not permitted_sources:
        messages.append(
            f"NOTE: {tbl}'s CHECK permits none of the source values "
            f"{list(SOURCE_VALUES)} (nor the target {UNVERIFIED_DEFAULT!r}); "
            f"structurally no row there can ever need this drain: {defn}"
        )
    if tbl not in RESTRICTED_TABLES:
        messages.append(f"NOTE: {tbl} carries a CHECK the vocabulary module does not list.")
    return False, messages


def tables_with_column(cur) -> list[str]:
    cur.execute(
        """
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'verification_pass_status' AND table_schema = 'public'
          AND table_name NOT LIKE %s
        ORDER BY table_name
        """,
        ("%\\_\\_ssv\\_%",),
    )
    return [r[0] for r in cur.fetchall()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="write (default is a dry run)")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set; refusing to guess.", file=sys.stderr)
        return 2

    import psycopg

    plan = {v: target_for(v) for v in SOURCE_VALUES}
    print(f"Vocabulary-resolved plan: {plan}")
    if set(plan.values()) != {UNVERIFIED_DEFAULT}:
        print(f"Unexpected target set {set(plan.values())} — halting.", file=sys.stderr)
        return 2

    total = 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Guard 1: no target table may reject the replacement value.
            cur.execute(
                """
                SELECT c.relname, pg_get_constraintdef(con.oid)
                FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
                WHERE con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%%verification_pass_status%%'
                """
            )
            for tbl, defn in cur.fetchall():
                halt, messages = guard1_verdict(tbl, defn)
                for msg in messages:
                    print(msg, file=sys.stderr if halt else sys.stdout)
                if halt:
                    return 1

            for tbl in tables_with_column(cur):
                cur.execute(
                    f'SELECT verification_pass_status, count(*) FROM "{tbl}" '  # noqa: S608 - identifier from information_schema
                    "WHERE verification_pass_status = ANY(%s) GROUP BY 1 ORDER BY 1",
                    (list(SOURCE_VALUES),),
                )
                before = cur.fetchall()
                if not before:
                    continue
                n = sum(c for _, c in before)
                total += n
                detail = ", ".join(f"{v}={c}" for v, c in before)
                if not args.execute:
                    print(f"[DRY RUN] {tbl}: would rewrite {n} row(s) -> {UNVERIFIED_DEFAULT}  ({detail})")
                    continue

                cur.execute(
                    f'UPDATE "{tbl}" SET verification_pass_status = %s '  # noqa: S608
                    "WHERE verification_pass_status = ANY(%s)",
                    (UNVERIFIED_DEFAULT, list(SOURCE_VALUES)),
                )
                changed = cur.rowcount
                cur.execute(
                    f'SELECT count(*) FROM "{tbl}" '  # noqa: S608
                    "WHERE verification_pass_status = ANY(%s)",
                    (list(SOURCE_VALUES),),
                )
                remaining = cur.fetchone()[0]
                if remaining != 0:
                    conn.rollback()
                    print(f"HALT: {tbl} still has {remaining} residual row(s) after update; rolled back.", file=sys.stderr)
                    return 1
                conn.commit()
                print(f"[EXECUTED] {tbl}: {detail} -> {UNVERIFIED_DEFAULT} ({changed} row(s)), 0 remaining")

    print(f"\n{'Would rewrite' if not args.execute else 'Rewrote'} {total} row(s) in total.")
    if not args.execute:
        print("Dry run only. Re-run with --execute to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
