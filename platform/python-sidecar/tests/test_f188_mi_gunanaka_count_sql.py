"""
tests/test_f188_mi_gunanaka_count_sql.py — PARIŚEṢA-V4 F-188.

Authority: 00_ARCHITECTURE/briefs/parisesa/F188_ACCRETION_EXCEPTION_v1_0.md
           00_ARCHITECTURE/briefs/parisesa/state/OWNER_RULINGS_20260821.md

THE DEFECT (confirmed live, 2026-08-22):
  asset_registry.count_sql for mi_gunanaka was single-table:
    SELECT count(*) FROM mimamsa_multipliers WHERE chart_id = $1
  mi_gunanaka.py::_publish_snapshot() also writes to
  mimamsa_calibration_snapshot — a RATIFIED exception to CLAUDE.md §N.3
  (append-only, key-embeds-time, accretes a new row every rebuild; see the
  doctrine note above). The count_sql silently never counted those rows.
  Live on chart 482012f1-710e-4a25-994a-93821f5871aa: mimamsa_multipliers=9,
  mimamsa_calibration_snapshot=4 — the pre-fix count_sql reported 9, not the
  true 13 rows the asset owns.

THE FIX: count_sql becomes a two-subquery sum ($1 repeated per subquery, the
established convention — see ga_condition's count_sql in the same seed file),
landed in BOTH scripts/seed/asset_registry_seed.ts (fresh environments) AND
migration 584 (the already-deployed row — a seed change alone never revisits
an existing asset_registry row).

WHAT THESE TESTS ACTUALLY MEASURE (§N.8 — a status must have a real detector
behind it, not a proxy):
  1. (offline) The seed's mi_gunanaka count_sql references BOTH tables, not
     just mimamsa_multipliers — this is the "must-fail-before-the-fix" case;
     reverting to the single-table string makes it fail.
  2. (offline) The seed's count_sql and migration 584's UPDATE ... SET
     count_sql literal are BYTE-IDENTICAL. This is the F-146 defect class
     (CLAUDE.md-catalogued: a seed and a migration silently disagreeing on
     the same field) turned into a permanent regression guard, not just a
     one-time fix — a future edit to only one of the two files must fail
     this test.
  3. (@pytest.mark.integration, live DB, skipped if unreachable — same
     convention as test_cr131_gochara_db_reachability.py) The CORRECTED
     count_sql, executed for real against the live chart, returns a number
     > 0 and equals the independently-queried sum of both tables' row
     counts for that chart — proving the SQL is not just textually present
     but actually counts both tables when run.
"""
from __future__ import annotations

import os
import re

import pytest

# ── paths ────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.dirname(_HERE)
_PLATFORM = os.path.dirname(_SIDECAR)

_SEED = os.path.join(_PLATFORM, "scripts", "seed", "asset_registry_seed.ts")
_MIGRATION = os.path.join(
    _PLATFORM, "supabase", "migrations", "584_mi_gunanaka_count_sql_accretion_fix.sql"
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
LIVE_DSN = os.environ.get("DATABASE_URL", "")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_asset_block(src: str, asset_id: str) -> str:
    """Return the text of the seed object whose asset_id matches.

    Same depth-aware brace-walk heuristic as test_mr07_cockpit_count_sql.py —
    the seed file is consistently formatted so this is sufficient.
    """
    pattern = rf"asset_id:\s*['\"]({re.escape(asset_id)})['\"]"
    m = re.search(pattern, src)
    if m is None:
        return ""
    start = src.rfind("{", 0, m.start())
    if start == -1:
        return ""
    depth = 0
    pos = start
    while pos < len(src):
        ch = src[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[start : pos + 1]
        pos += 1
    return src[start:]


def _extract_seed_count_sql(asset_block: str) -> str:
    """Pull the count_sql value out of a seed asset block.

    mi_gunanaka's count_sql is a template literal (backtick-delimited,
    because it needs no interpolation but the multi-table form is easiest to
    write unquoted); fall back to a single/double-quoted match for other
    assets' single-table forms.
    """
    m = re.search(r"count_sql\s*:\s*`([^`]+)`", asset_block)
    if m:
        return m.group(1).strip()
    m = re.search(r"count_sql\s*:\s*['\"]([^'\"]+)['\"]", asset_block)
    assert m, f"no count_sql found in block: {asset_block[:300]!r}"
    return m.group(1).strip()


def _extract_migration_count_sql(migration_src: str) -> str:
    """Pull the $sql$...$sql$-delimited value out of migration 584's UPDATE."""
    m = re.search(r"SET count_sql = \$sql\$(.+?)\$sql\$", migration_src, re.DOTALL)
    assert m, "migration 584 does not contain the expected $sql$-delimited UPDATE"
    return m.group(1).strip()


# ── Test 1: seed count_sql references both tables (must-fail-before-fix) ────


def test_mi_gunanaka_count_sql_references_both_tables():
    """mi_gunanaka's seed count_sql must count mimamsa_multipliers AND
    mimamsa_calibration_snapshot. Before F-188 this was single-table
    (mimamsa_multipliers only) and silently missed the accretion table
    _publish_snapshot() writes to every rebuild — see the F-188 doctrine
    note. Revert the seed to the single-table string and this test fails."""
    src = _read(_SEED)
    block = _extract_asset_block(src, "mi_gunanaka")
    assert block, "mi_gunanaka entry not found in asset_registry_seed.ts"

    count_sql = _extract_seed_count_sql(block)
    assert "mimamsa_multipliers" in count_sql, (
        f"mi_gunanaka count_sql must still count mimamsa_multipliers (found: {count_sql!r})"
    )
    assert "mimamsa_calibration_snapshot" in count_sql, (
        "mi_gunanaka count_sql must count mimamsa_calibration_snapshot — the "
        "ratified §N.3 accretion table _publish_snapshot() writes to. "
        f"(found: {count_sql!r})"
    )
    # $1 must be repeated per subquery — the established multi-table
    # convention (see ga_condition's count_sql in the same file).
    assert count_sql.count("$1") >= 2, (
        f"mi_gunanaka count_sql must repeat $1 per subquery (found: {count_sql!r})"
    )


# ── Test 2: seed and migration 584 agree — the F-146 defect class ───────────


def test_mi_gunanaka_seed_and_migration_count_sql_agree():
    """The seed's count_sql (fresh environments) and migration 584's UPDATE
    (the already-deployed row) must carry the IDENTICAL SQL string. A seed
    and a migration silently disagreeing on the same field is the F-146
    defect class this finding is the second confirmed instance of — this
    test is the permanent regression guard against a future edit landing in
    only one of the two files."""
    assert os.path.exists(_MIGRATION), (
        f"migration 584 not found at {_MIGRATION} — F-188 requires both a seed "
        "fix and a migration (the seed alone never revisits an already-seeded "
        "asset_registry row)"
    )
    seed_src = _read(_SEED)
    block = _extract_asset_block(seed_src, "mi_gunanaka")
    seed_count_sql = _extract_seed_count_sql(block)

    migration_src = _read(_MIGRATION)
    migration_count_sql = _extract_migration_count_sql(migration_src)

    assert seed_count_sql == migration_count_sql, (
        "mi_gunanaka count_sql has diverged between the seed and migration 584 "
        "— this is exactly the F-146 defect class (a seed and a migration "
        "silently disagreeing on the same field).\n"
        f"seed:      {seed_count_sql!r}\n"
        f"migration: {migration_count_sql!r}"
    )


# ── Test 3: live integration — the corrected SQL actually counts both ───────


def _live_conn_or_skip():
    import psycopg

    try:
        conn = psycopg.connect(LIVE_DSN, row_factory=psycopg.rows.dict_row, connect_timeout=2)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")
    return conn


@pytest.mark.integration
def test_corrected_count_sql_returns_nonzero_and_counts_both_tables_live():
    """Executes the CORRECTED count_sql for real against the live chart and
    asserts (a) it returns > 0 and (b) it equals the independently-queried
    sum of mimamsa_multipliers + mimamsa_calibration_snapshot row counts for
    that chart. This is the assertion that closes the finding — a textually
    correct count_sql is not the same as a count_sql that actually counts
    both tables when Postgres runs it."""
    src = _read(_SEED)
    block = _extract_asset_block(src, "mi_gunanaka")
    count_sql = _extract_seed_count_sql(block)

    conn = _live_conn_or_skip()
    try:
        with conn.cursor() as cur:
            cur.execute(count_sql, (CHART_ID,))
            row = cur.fetchone()
            reported = list(row.values())[0] if row else None

            cur.execute(
                "SELECT count(*) AS n FROM mimamsa_multipliers WHERE chart_id = %s",
                (CHART_ID,),
            )
            multipliers_n = cur.fetchone()["n"]

            cur.execute(
                "SELECT count(*) AS n FROM mimamsa_calibration_snapshot WHERE chart_id = %s",
                (CHART_ID,),
            )
            snapshot_n = cur.fetchone()["n"]
    finally:
        conn.close()

    assert reported is not None
    assert reported > 0, (
        f"corrected mi_gunanaka count_sql returned {reported!r} for chart "
        f"{CHART_ID} — expected > 0 (this chart has rows in both source tables)"
    )
    expected = multipliers_n + snapshot_n
    assert reported == expected, (
        f"corrected mi_gunanaka count_sql returned {reported}, but "
        f"mimamsa_multipliers ({multipliers_n}) + mimamsa_calibration_snapshot "
        f"({snapshot_n}) = {expected} — the count_sql is not summing both "
        "tables correctly."
    )
    # Regression guard against the pre-fix single-table undercounting: if the
    # snapshot table has accreted at all, the true count must exceed the
    # multipliers-only count the old count_sql reported.
    if snapshot_n > 0:
        assert reported > multipliers_n, (
            f"mimamsa_calibration_snapshot has {snapshot_n} row(s) for this chart "
            f"but the corrected count_sql ({reported}) did not exceed the "
            f"multipliers-only count ({multipliers_n}) — the accretion table is "
            "not actually being counted."
        )
