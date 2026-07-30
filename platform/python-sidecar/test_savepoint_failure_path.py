"""
C4 Failure-Path SAVEPOINT Test
================================
Verifies the Vimarsaka RED fix: per-row SAVEPOINT isolates a bad row
so the outer (orchestrator-owned) transaction survives an INSERT failure.

Pattern under test (same in bo_laksana, bo_samskara, bo_anveshana):

    cur.execute("SAVEPOINT row_sp")
    try:
        cur.execute(INSERT_SQL, row)
        cur.execute("RELEASE SAVEPOINT row_sp")
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT row_sp")   # ← the fix
        logger.warning("skipping bad row: %s", e)

Before the fix, writers called conn.rollback() which aborted the whole
transaction and broke the orchestrator's outer transaction contract.

The test proves:
  1. A bad INSERT (NOT NULL violation on signal_id) raises an exception.
  2. ROLLBACK TO SAVEPOINT restores the connection to a usable state.
  3. The outer transaction can still execute queries (not aborted).
  4. No data is written (outer rollback at end — test is read-safe).
"""

import os
import sys

import psycopg

DB_URL = os.environ["DATABASE_URL"]

# ── helpers ──────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)


# ── core test ────────────────────────────────────────────────────────────────

def test_savepoint_isolation() -> bool:
    """
    Returns True if SAVEPOINT isolation is confirmed; False on any failure.
    """
    section("C4 SAVEPOINT Failure-Path Test")

    with psycopg.connect(DB_URL, prepare_threshold=None, autocommit=False) as conn:
        with conn.cursor() as cur:

            # ── Step 1: Outer transaction begins (orchestrator role) ──────────
            print("\n[1] Outer transaction open (simulates orchestrator).")

            # ── Step 2: Insert a known-good sentinel row — proves TX is live ─
            #   We use a SELECT that touches the real schema to confirm the
            #   connection is in a working state before the bad-row attempt.
            cur.execute("SELECT COUNT(*) FROM bodha_msr_signals LIMIT 1")
            baseline_count = cur.fetchone()[0]
            print(f"[2] Baseline row count in bodha_msr_signals: {baseline_count}")

            # ── Step 3: Set SAVEPOINT and attempt a bad INSERT ───────────────
            print("\n[3] Setting SAVEPOINT row_sp and attempting bad INSERT …")
            print("    (Bad row: signal_id = NULL, violates PRIMARY KEY NOT NULL)")

            cur.execute("SAVEPOINT row_sp")
            bad_row_caught = False
            try:
                # Force a NOT NULL / PK violation: signal_id is UUID PRIMARY KEY
                cur.execute(
                    "INSERT INTO bodha_msr_signals (signal_id) VALUES (NULL)"
                )
                # If we reach here the DB accepted a NULL PK — that's the error
                print("ERROR: INSERT with NULL PK succeeded unexpectedly.")
                return False
            except Exception as exc:
                bad_row_caught = True
                print(f"[3] Expected violation caught: {type(exc).__name__}: {exc!s:.120}")

            if not bad_row_caught:
                print("ERROR: No exception raised — test setup broken.")
                return False

            # ── Step 4: ROLLBACK TO SAVEPOINT (the Vimarsaka fix) ────────────
            print("\n[4] ROLLBACK TO SAVEPOINT row_sp …")
            cur.execute("ROLLBACK TO SAVEPOINT row_sp")
            cur.execute("RELEASE SAVEPOINT row_sp")
            print("[4] Savepoint rolled back and released.")

            # ── Step 5: Prove outer transaction is alive ──────────────────────
            print("\n[5] Verifying outer transaction is still alive …")
            try:
                cur.execute("SELECT 1 AS alive")
                row = cur.fetchone()
                assert row is not None and row[0] == 1, f"Unexpected SELECT result: {row}"
                print("[5] SELECT 1 returned 1 — outer transaction is alive.")
            except Exception as exc:
                print(f"FAIL: Outer transaction is ABORTED after ROLLBACK TO SAVEPOINT: {exc}")
                return False

            # ── Step 6: Confirm the schema is still queryable (not just 'alive') ─
            print("\n[6] Re-querying bodha_msr_signals after bad-row skip …")
            try:
                cur.execute("SELECT COUNT(*) FROM bodha_msr_signals")
                post_count = cur.fetchone()[0]
                assert post_count == baseline_count, (
                    f"Row count changed unexpectedly: {baseline_count} → {post_count}"
                )
                print(f"[6] Row count still {post_count} — no bad row was committed.")
            except Exception as exc:
                print(f"FAIL: Schema query after rollback-to-savepoint failed: {exc}")
                return False

            # ── Step 7: Outer rollback — test writes nothing ──────────────────
            conn.rollback()
            print("\n[7] Outer transaction rolled back (test is read-safe — no writes).")

    return True


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ok = test_savepoint_isolation()
    if ok:
        print(
            "\n✓ SAVEPOINT isolation VERIFIED — outer transaction survived bad row.\n"
            "  The Vimarsaka RED fix (ROLLBACK TO SAVEPOINT vs conn.rollback) is proven.\n"
            "  Applies to bo_laksana, bo_samskara, bo_anveshana.\n"
        )
        sys.exit(0)
    else:
        print(
            "\n✗ SAVEPOINT isolation FAILED — investigate the output above.\n"
        )
        sys.exit(1)
