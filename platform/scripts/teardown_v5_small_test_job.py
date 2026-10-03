"""
teardown_v5_small_test_job.py — Pravāha C38: teardown for the SMALL TEST build
of ka_gochara_v5 staged by dispatch_v5_small_test_job.py (C37), modelled on
the A2.5/A4 teardown in dispatch_a25_v41_candidate_job.py.

ONE transaction, chart/run-scoped, fail-closed. Chart is the pinned canonical
chart 482012f1-710e-4a25-994a-93821f5871aa ONLY — there is no chart argument.
DATABASE_URL comes from the environment only: never on argv, never printed.

REFUSES (loudly, nothing deleted) when ANY of these holds:
  1. a kala_gochara_publication row for the pinned chart at generation '5.0'
     has status 'published' (a published generation is immutable);
  2. a ka_gochara_generation_seal row exists for the pinned chart at
     generation '5.0' (a sealed generation is permanent publication
     history — 1153 §5);
  3. kala_gochara_authority names '5.0' as the pinned chart's
     authoritative_generation (a SERVING generation is never torn down);
  4. a build_runs row for this asset on the pinned chart is
     planned/running/paused (active execution — stop it first);
  5. generation '5.0' rows exist for the pinned chart in any of the four
     kala_gochara_* tables but NO build_runs row names
     triggered_by = 'gochara-v5-small-test' for the chart — those rows were
     NOT produced by a small-test run and this script never touches them.

Then deletes, in one commit:
    DELETE FROM build_run_assets WHERE run_id IN
      (SELECT id FROM build_runs WHERE triggered_by = 'gochara-v5-small-test'
         AND chart_id = '<pinned>');
    DELETE FROM build_runs WHERE triggered_by = 'gochara-v5-small-test'
      AND chart_id = '<pinned>';
    DELETE FROM asset_throughput WHERE asset_id = 'ka_gochara_v5'
      AND chart_id = '<pinned>';
    -- '5.0' rows for the PINNED CHART ONLY — never another chart's '5.0':
    DELETE FROM kala_gochara_windows     WHERE chart_id = '<pinned>' AND generation = '5.0';
    DELETE FROM kala_gochara_contacts    WHERE chart_id = '<pinned>' AND generation = '5.0';
    DELETE FROM kala_gochara_coverage    WHERE chart_id = '<pinned>' AND generation = '5.0';
    DELETE FROM kala_gochara_publication WHERE chart_id = '<pinned>' AND generation = '5.0';

And KEEPS the asset_registry row (migration 1243 inserts it permanently —
deleting it would fail the orchestrator's writer-gap preflight on EVERY
build run): in the SAME transaction the row is restored to its inert state
(UPDATE asset_registry SET is_active = false) and verified field by field
against the 1243 shape.

--dry-run runs every refusal check, then lists the COUNTS per table of what
would be deleted and ROLLS BACK — nothing is written.

Usage:
  cd <repo-root>/platform
  python3 scripts/teardown_v5_small_test_job.py [--dry-run]
  python3 scripts/teardown_v5_small_test_job.py --help
"""
from __future__ import annotations

import argparse
import os
import sys

ASSET_ID = "ka_gochara_v5"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "gochara-v5-small-test"
GENERATION = "5.0"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# The 1243 shape the ka_gochara_v5 registry row must hold after teardown.
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": False,
    "writer_timeout_seconds": 600,
    "depends_on": [],
}

DATA_TABLES = (
    "kala_gochara_windows",
    "kala_gochara_contacts",
    "kala_gochara_coverage",
    "kala_gochara_publication",
)

TEARDOWN_DELETES = (
    """DELETE FROM build_run_assets WHERE run_id IN
         (SELECT id FROM build_runs WHERE triggered_by = %s
            AND chart_id = %s)""",
    "DELETE FROM build_runs WHERE triggered_by = %s AND chart_id = %s",
    "DELETE FROM asset_throughput WHERE asset_id = %s AND chart_id = %s",
    "DELETE FROM kala_gochara_windows     WHERE chart_id = %s AND generation = '5.0'",
    "DELETE FROM kala_gochara_contacts    WHERE chart_id = %s AND generation = '5.0'",
    "DELETE FROM kala_gochara_coverage    WHERE chart_id = %s AND generation = '5.0'",
    "DELETE FROM kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'",
)


def _validate_registry_row(cur) -> None:
    cur.execute(
        """SELECT scope, is_active, has_writer, has_substeps,
                  writer_timeout_seconds, depends_on
           FROM asset_registry WHERE asset_id = %s""",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(
            f"asset_registry row for {ASSET_ID} is missing — migration 1243 "
            "inserts it permanently and the writer-gap preflight fails every "
            "build run without it; restore the row, do not re-run teardown")
    for field, expected in EXPECTED_REGISTRY_ROW.items():
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if actual != expected:
            raise RuntimeError(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — "
                "the registry row must be its inert 1243 self after teardown")


def _refusal_checks(cur) -> None:
    """Every guard, fail-closed. Raises RuntimeError; nothing is deleted."""
    cur.execute(
        """SELECT manifest_id FROM kala_gochara_publication
           WHERE chart_id = %s AND generation = %s AND status = 'published'""",
        (CHART_ID, GENERATION),
    )
    published = cur.fetchone()
    if published:
        raise RuntimeError(
            f"teardown refused: kala_gochara_publication has a PUBLISHED "
            f"'5.0' manifest {published['manifest_id']} for chart {CHART_ID} — "
            "a published generation is immutable")

    cur.execute(
        """SELECT manifest_id FROM ka_gochara_generation_seal
           WHERE chart_id = %s AND generation = %s""",
        (CHART_ID, GENERATION),
    )
    seal = cur.fetchone()
    if seal:
        raise RuntimeError(
            f"teardown refused: ka_gochara_generation_seal records '5.0' "
            f"(manifest {seal['manifest_id']}) for chart {CHART_ID} — a sealed "
            "generation is permanent publication history")

    cur.execute(
        """SELECT authoritative_generation FROM kala_gochara_authority
           WHERE chart_id = %s""",
        (CHART_ID,),
    )
    authority = cur.fetchone()
    if authority and authority["authoritative_generation"] == GENERATION:
        raise RuntimeError(
            f"teardown refused: kala_gochara_authority names '5.0' as the "
            f"authoritative_generation for chart {CHART_ID} — a serving "
            "generation is never torn down")

    cur.execute(
        """SELECT id, state FROM build_runs
           WHERE chart_id = %s AND scope = 'asset_set'
             AND scope_target = %s
             AND state IN ('planned', 'running', 'paused')""",
        (CHART_ID, ASSET_ID),
    )
    active = cur.fetchall()
    if active:
        raise RuntimeError(
            f"teardown refused: active build_runs {[(str(r['id']), r['state']) for r in active]} "
            f"for asset {ASSET_ID} on chart {CHART_ID} — stop active "
            "execution first")

    # The '5.0' data rows may be deleted ONLY when they came from a
    # small-test run. Rows with no small-test run behind them are untouchable.
    data_rows = 0
    for table in DATA_TABLES:
        cur.execute(
            f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s",
            (CHART_ID, GENERATION),
        )
        data_rows += cur.fetchone()["n"]
    if data_rows:
        cur.execute(
            """SELECT count(*) AS n FROM build_runs
               WHERE triggered_by = %s AND chart_id = %s""",
            (TRIGGERED_BY, CHART_ID),
        )
        if cur.fetchone()["n"] == 0:
            raise RuntimeError(
                f"teardown refused: {data_rows} generation '5.0' row(s) exist "
                f"for chart {CHART_ID} but NO build_runs row names "
                f"triggered_by = '{TRIGGERED_BY}' — those rows were not "
                "produced by a small-test run and this script never touches them")


def _dry_run_counts(cur) -> dict[str, int]:
    counts: dict[str, int] = {}
    cur.execute(
        """SELECT count(*) AS n FROM build_run_assets WHERE run_id IN
             (SELECT id FROM build_runs WHERE triggered_by = %s AND chart_id = %s)""",
        (TRIGGERED_BY, CHART_ID),
    )
    counts["build_run_assets"] = cur.fetchone()["n"]
    cur.execute(
        "SELECT count(*) AS n FROM build_runs WHERE triggered_by = %s AND chart_id = %s",
        (TRIGGERED_BY, CHART_ID),
    )
    counts["build_runs"] = cur.fetchone()["n"]
    cur.execute(
        "SELECT count(*) AS n FROM asset_throughput WHERE asset_id = %s AND chart_id = %s",
        (ASSET_ID, CHART_ID),
    )
    counts["asset_throughput"] = cur.fetchone()["n"]
    for table in DATA_TABLES:
        cur.execute(
            f"SELECT count(*) AS n FROM {table} WHERE chart_id = %s AND generation = %s",
            (CHART_ID, GENERATION),
        )
        counts[table] = cur.fetchone()["n"]
    return counts


def teardown(*, dry_run: bool = False) -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        _refusal_checks(cur)
        if dry_run:
            counts = _dry_run_counts(cur)
            conn.rollback()
            print(f"[dry-run] teardown of the v5 small-test run on chart {CHART_ID} "
                  f"would delete (ROLLED BACK, nothing written):", file=sys.stderr)
            for name, n in counts.items():
                print(f"{name}\t{n}")
            return
        for sql in TEARDOWN_DELETES:
            if "build_run_assets" in sql or "FROM build_runs" in sql:
                cur.execute(sql, (TRIGGERED_BY, CHART_ID))
            elif "asset_throughput" in sql:
                cur.execute(sql, (ASSET_ID, CHART_ID))
            else:
                cur.execute(sql, (CHART_ID,))
        # The registry row stays (migration 1243) — restore inertness and
        # verify the landed row field by field in the same transaction.
        cur.execute(
            "UPDATE asset_registry SET is_active = false WHERE asset_id = %s",
            (ASSET_ID,),
        )
        _validate_registry_row(cur)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()
    print(f"[teardown] removed the small-test run bookkeeping and the '5.0' "
          f"rows for chart {CHART_ID}; asset_registry row kept and restored "
          f"to inert (is_active=false) — one transaction", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        prog="teardown_v5_small_test_job.py",
        description="Fail-closed teardown of the ka_gochara_v5 SMALL TEST run "
                    "(triggered_by='gochara-v5-small-test', pinned chart only).")
    p.add_argument("--dry-run", action="store_true",
                   help="run the refusal checks, list would-delete counts per table, roll back")
    args = p.parse_args(argv)
    teardown(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
