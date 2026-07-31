#!/usr/bin/env python3
"""schema_pin_mimamsa_predictions.py — the real schema HASH pin for `mimamsa_predictions`.

# Implements: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §8.5 (lane B-PB-SCHEMA-PIN)

Context
-------
`MEMO_PB-3_0.md` ruled `mimamsa_predictions` "hash-pinned at BIND" — schema +
the live 286-row count recorded before PB-3's lanes opened, to be re-verified
unchanged at gate close. `REPORT_PB-3.md` §G item 1 discovered that this
demanded schema *hash* pin never actually existed: only a prose sentence
("286 rows matching the BIND pin") was ever written down, plus one recorded
fingerprint (`b730b9f3…`) with **nothing prior to compare it against** and no
script that could reproduce it. This file, plus the baseline JSON it reads
(`MIMAMSA_PREDICTIONS_SCHEMA_PIN.json`, this directory), is the correction:
a genuine, reproducible schema-hash computation, with a committed baseline
and a documented re-derivation path.

What the hash covers
---------------------
The table's full DDL-relevant shape: every column (name, type, nullability,
default), every constraint (`pg_get_constraintdef`), every index (`pg_indexes`
definition) — each section internally ordered deterministically (ordinal
position / name), concatenated into one canonical text, then SHA-256'd.

Row count is tracked SEPARATELY and reported as informational context only —
per `MEMO_PB-3_0`, row count is EXPECTED to move via legitimate L5
STRUCTURAL-mode rebuilds (`mi_bhavisya.py`'s DELETE-then-INSERT idempotency
pattern, CLAUDE.md §N.3) and is deliberately NOT part of the hash. Folding it
into the hash would make every routine rebuild look like schema drift, which
is exactly the false-alarm failure mode this pin must not create.

Modes
-----
  --self-test        DB-free. Proves the hash function is deterministic (same
                     input -> same hash, run twice) AND sensitive to schema
                     change (a single mutated column/constraint/index changes
                     the hash). This is the CI-safe gate (CI has no database).

  --verify           Live-DB mode (requires DATABASE_URL). Re-derives the
                     canonical text + hash from the live table right now and
                     compares against the committed baseline in
                     MIMAMSA_PREDICTIONS_SCHEMA_PIN.json. Reports row-count
                     drift as informational only — it does not affect the
                     PASS/DRIFT verdict.

  --print-canonical  Live-DB mode. Prints the canonical text and its hash
                     without comparing to any baseline — use this to see
                     exactly what a future rebase of the baseline would pin
                     (e.g. after a deliberate, ruled schema change).

Exit codes
----------
  0  clean (self-test passed / live hash matches baseline)
  1  schema drift detected (live hash != baseline hash)
  2  invocation / environment error (no DATABASE_URL, table not found, etc.)
  3  self-test failure (should never happen on unmodified code)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
from typing import Iterable, Sequence

TABLE_FQN = "public.mimamsa_predictions"
BASELINE_PATH = pathlib.Path(__file__).parent / "MIMAMSA_PREDICTIONS_SCHEMA_PIN.json"

_COLUMNS_SQL = """
    SELECT column_name, udt_name, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'mimamsa_predictions'
    ORDER BY ordinal_position;
"""

_CONSTRAINTS_SQL = """
    SELECT conname, contype, pg_get_constraintdef(oid) AS def
    FROM pg_constraint
    WHERE conrelid = 'public.mimamsa_predictions'::regclass
    ORDER BY conname;
"""

_INDEXES_SQL = """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename = 'mimamsa_predictions'
    ORDER BY indexname;
"""

_ROW_COUNT_SQL = "SELECT count(*) FROM mimamsa_predictions;"


# ---------------------------------------------------------------------------
# Pure, DB-free canonicalization — the part the self-test exercises directly.
# ---------------------------------------------------------------------------

def build_canonical_text(
    table_fqn: str,
    columns: Sequence[Sequence[object]],
    constraints: Sequence[Sequence[object]],
    indexes: Sequence[Sequence[object]],
) -> str:
    """Deterministically serialize a table's DDL-relevant shape to one string.

    Callers MUST pass columns/constraints/indexes already ordered exactly as
    the SQL above orders them (ordinal position / conname / indexname) — this
    function does not re-sort, so it can be used identically against both a
    live query result and a hand-built self-test fixture.
    """
    lines = [f"TABLE|{table_fqn}"]
    for column_name, udt_name, is_nullable, column_default in columns:
        lines.append(
            f"COL|{column_name}|{udt_name}|{is_nullable}|{column_default or ''}"
        )
    for conname, contype, condef in constraints:
        lines.append(f"CON|{conname}|{contype}|{condef}")
    for indexname, indexdef in indexes:
        lines.append(f"IDX|{indexname}|{indexdef}")
    return "\n".join(lines)


def compute_hash(canonical_text: str) -> str:
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Self-test — DB-free, the CI-safe gate.
# ---------------------------------------------------------------------------

_FIXTURE_COLUMNS = [
    ("chart_id", "uuid", "NO", None),
    ("prediction_id", "text", "NO", None),
    ("created_at", "timestamptz", "NO", "now()"),
]
_FIXTURE_CONSTRAINTS = [
    ("mimamsa_predictions_pkey", "p", "PRIMARY KEY (chart_id, prediction_id)"),
]
_FIXTURE_INDEXES = [
    ("idx_mimamsa_predictions_chart_id", "CREATE INDEX ... USING btree (chart_id)"),
]


def _self_test() -> int:
    base = build_canonical_text(
        TABLE_FQN, _FIXTURE_COLUMNS, _FIXTURE_CONSTRAINTS, _FIXTURE_INDEXES
    )
    h1 = compute_hash(base)
    h2 = compute_hash(
        build_canonical_text(
            TABLE_FQN, _FIXTURE_COLUMNS, _FIXTURE_CONSTRAINTS, _FIXTURE_INDEXES
        )
    )
    if h1 != h2:
        print(f"[schema-pin] FAIL: hash not deterministic on identical input "
              f"({h1} != {h2})", file=sys.stderr)
        return 3

    # Mutate one column's nullability — the hash MUST change.
    mutated_columns = list(_FIXTURE_COLUMNS)
    mutated_columns[-1] = ("created_at", "timestamptz", "YES", "now()")
    h_mutated_col = compute_hash(
        build_canonical_text(TABLE_FQN, mutated_columns, _FIXTURE_CONSTRAINTS, _FIXTURE_INDEXES)
    )
    if h_mutated_col == h1:
        print("[schema-pin] FAIL: mutating a column's nullability did not "
              "change the hash — the pin would be blind to real drift.", file=sys.stderr)
        return 3

    # Mutate a constraint definition — the hash MUST change.
    mutated_constraints = [("mimamsa_predictions_pkey", "p", "PRIMARY KEY (chart_id)")]
    h_mutated_con = compute_hash(
        build_canonical_text(TABLE_FQN, _FIXTURE_COLUMNS, mutated_constraints, _FIXTURE_INDEXES)
    )
    if h_mutated_con == h1:
        print("[schema-pin] FAIL: mutating a constraint definition did not "
              "change the hash.", file=sys.stderr)
        return 3

    # Mutate an index definition — the hash MUST change.
    mutated_indexes = [("idx_mimamsa_predictions_chart_id", "CREATE INDEX ... USING hash (chart_id)")]
    h_mutated_idx = compute_hash(
        build_canonical_text(TABLE_FQN, _FIXTURE_COLUMNS, _FIXTURE_CONSTRAINTS, mutated_indexes)
    )
    if h_mutated_idx == h1:
        print("[schema-pin] FAIL: mutating an index definition did not "
              "change the hash.", file=sys.stderr)
        return 3

    print("[schema-pin] self-test PASS: hash is deterministic and sensitive "
          "to column/constraint/index mutation.")
    return 0


# ---------------------------------------------------------------------------
# Live-DB mode
# ---------------------------------------------------------------------------

def _connect():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("[schema-pin] DATABASE_URL not set — cannot run live-DB mode. "
              "(Use --self-test for the DB-free CI gate.)", file=sys.stderr)
        return None
    try:
        import psycopg  # psycopg3
        return psycopg.connect(dsn)
    except ImportError:
        try:
            import psycopg2  # type: ignore
            return psycopg2.connect(dsn)
        except ImportError:
            print("[schema-pin] neither psycopg nor psycopg2 available.", file=sys.stderr)
            return None


def _fetch_live(conn) -> tuple[list, list, list, int]:
    with conn.cursor() as cur:
        cur.execute(_COLUMNS_SQL)
        columns = cur.fetchall()
        cur.execute(_CONSTRAINTS_SQL)
        constraints = cur.fetchall()
        cur.execute(_INDEXES_SQL)
        indexes = cur.fetchall()
        cur.execute(_ROW_COUNT_SQL)
        row_count = cur.fetchone()[0]
    return columns, constraints, indexes, row_count


def _load_baseline() -> dict:
    if not BASELINE_PATH.exists():
        print(f"[schema-pin] baseline file missing: {BASELINE_PATH}", file=sys.stderr)
        return {}
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _verify() -> int:
    conn = _connect()
    if conn is None:
        return 2
    try:
        columns, constraints, indexes, row_count = _fetch_live(conn)
    finally:
        conn.close()

    if not columns:
        print(f"[schema-pin] table {TABLE_FQN} has no columns — does it exist "
              f"on this database?", file=sys.stderr)
        return 2

    canonical_text = build_canonical_text(TABLE_FQN, columns, constraints, indexes)
    live_hash = compute_hash(canonical_text)

    baseline = _load_baseline()
    baseline_hash = baseline.get("schema_hash_sha256")
    baseline_rows = baseline.get("row_count_at_pin")

    print(f"[schema-pin] table:        {TABLE_FQN}")
    print(f"[schema-pin] live hash:    {live_hash}")
    print(f"[schema-pin] baseline:     {baseline_hash}")
    print(f"[schema-pin] live rows:    {row_count}  (baseline: {baseline_rows}, "
          f"informational only — not part of the hash)")

    if baseline_hash is None:
        print("[schema-pin] no baseline hash recorded — nothing to compare "
              "against.", file=sys.stderr)
        return 2

    if live_hash != baseline_hash:
        print("[schema-pin] DRIFT: live schema hash does not match the pinned "
              "baseline. If this drift is deliberate and DVA-ruled, regenerate "
              "the baseline with --print-canonical and update "
              "MIMAMSA_PREDICTIONS_SCHEMA_PIN.json.", file=sys.stderr)
        return 1

    print("[schema-pin] PASS: live schema matches the pinned baseline.")
    return 0


def _print_canonical() -> int:
    conn = _connect()
    if conn is None:
        return 2
    try:
        columns, constraints, indexes, row_count = _fetch_live(conn)
    finally:
        conn.close()

    canonical_text = build_canonical_text(TABLE_FQN, columns, constraints, indexes)
    print(canonical_text)
    print(f"\n# sha256: {compute_hash(canonical_text)}")
    print(f"# row_count (informational, not part of hash): {row_count}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--print-canonical", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.self_test:
        return _self_test()
    if args.print_canonical:
        return _print_canonical()
    return _verify()


if __name__ == "__main__":
    sys.exit(main())
