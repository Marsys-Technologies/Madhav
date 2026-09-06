"""
tests/test_migration_731_conc7_size_sql.py — L3 Kāla, F-CONC-7:
migration 731 corrects `size_sql` for L3's six temporal-arbiter-adjacent assets
(`ka_sangam`, `ka_vighnakara`, `ka_kalasutra`, `ka_kala_darshana`, `ka_jivana_parva`,
`ka_bhavishya_lekha`) from a bare, chart-unaware `SELECT pg_total_relation_size('<table>')`
to a proportional-share estimate scoped to `chart_id = $1`, per the Conductor's ruling on
#1956 (closed 2026-09-06) — the calling-code half (conditional `$1` binding + the
`size_is_estimate` disclosure flag) shipped in PR #1958.

Second migration in L3's 730-739 range (migration 730 was the first, F-VIGHNA-5).

Same two-layer convention as this session's other 73x migrations:

  1. DB-free (static): exactly six precisely-scoped UPDATEs, one per asset_id, each
     binding `$1` (so `stats/route.ts`'s regex test of `asset.size_sql` for `$1` detects it as
     chart-scoped and sets `size_is_estimate = true`), each carrying an explicit
     `AS size` alias (the column name `stats/route.ts` actually reads — the campaign-wide
     bare pattern this migration deliberately does NOT copy forward, see the migration's
     own header comment), each dividing by `GREATEST(total_count, 1)` to guard the
     zero-row case.

  2. `@pytest.mark.integration` (live Cloud SQL proxy; skips with a clear reason if
     unreachable): runs the ACTUAL migration file against the real `asset_registry` rows
     inside a transaction that is ALWAYS rolled back — never commits. Proves: idempotent,
     the six size_sql values execute without error against the real tables, and the
     computed proportional share is numerically sane (between 0 and the table's own
     total physical size, inclusive).
"""
from __future__ import annotations

import os
import re

import pytest

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "migrations", "731_nirmana_l3_f_conc_7_size_sql_proportional.sql"
)

_ASSET_TABLE = {
    "ka_sangam": "kala_convergence",
    "ka_vighnakara": "kala_obstruction",
    "ka_kalasutra": "kala_activation",
    "ka_kala_darshana": "kala_darshana",
    "ka_jivana_parva": "kala_jivana_parva",
    "ka_bhavishya_lekha": "kala_bhavishya",
}

_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _read_migration() -> str:
    if not os.path.exists(_MIGRATION_PATH):
        pytest.skip(f"migration 731 not found at {_MIGRATION_PATH} (platform/ not checked out alongside python-sidecar)")
    with open(_MIGRATION_PATH, encoding="utf-8") as f:
        return f.read()


def _code_only(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


# ── DB-free static guards ────────────────────────────────────────────────────

def test_migration_731_has_exactly_six_precisely_scoped_updates():
    code_only = _code_only(_read_migration())
    updates = re.findall(r"UPDATE\s+\w+.*?;", code_only, re.S)
    assert len(updates) == 6, f"expected exactly 6 UPDATEs (one per asset), found {len(updates)}"
    for asset_id in _ASSET_TABLE:
        assert any(f"WHERE asset_id = '{asset_id}'" in u for u in updates), (
            f"no UPDATE scoped to asset_id = '{asset_id}'"
        )
    # Every UPDATE must be scoped to exactly one asset_id — never a bare unconditional UPDATE.
    for u in updates:
        assert "asset_registry" in u
        assert re.search(r"WHERE asset_id = '\w+'\s*;\s*$", u), (
            f"UPDATE not scoped to a single asset_id: {u}"
        )


@pytest.mark.parametrize("asset_id,table", list(_ASSET_TABLE.items()))
def test_migration_731_binds_dollar1_for_every_asset(asset_id, table):
    """`stats/route.ts` detects chart-scoping via `/\\$1/.test(asset.size_sql)` — every
    one of these six size_sql values must contain a literal `$1`, or the calling-code fix
    (PR #1958) will never actually pass a chart_id and this migration does nothing,
    exactly the failure mode the original filing warned about."""
    code_only = _code_only(_read_migration())
    m = re.search(
        rf"SET\s+size_sql\s*=\s*((?:'[^']*'(?:\s*\|\|\s*)?)+)\s*WHERE\s+asset_id\s*=\s*'{asset_id}'",
        code_only, re.S,
    )
    assert m, f"could not find the SET size_sql = ... clause for {asset_id}"
    concatenated = m.group(1)
    assert "$1" in concatenated, f"{asset_id}'s size_sql does not bind $1"
    assert table in concatenated, f"{asset_id}'s size_sql does not reference its own table {table}"


@pytest.mark.parametrize("asset_id", list(_ASSET_TABLE))
def test_migration_731_aliases_the_result_column_as_size(asset_id):
    """`stats/route.ts` reads `sizeResult.rows[0]?.size` — a column literally named
    `size`. An unaliased `pg_total_relation_size(...)` names its own column
    `pg_total_relation_size`, not `size` — the alias is required, not decorative."""
    code_only = _code_only(_read_migration())
    m = re.search(
        rf"SET\s+size_sql\s*=\s*((?:'[^']*'(?:\s*\|\|\s*)?)+)\s*WHERE\s+asset_id\s*=\s*'{asset_id}'",
        code_only, re.S,
    )
    assert m
    assert "AS size" in m.group(1), f"{asset_id}'s size_sql is missing the required `AS size` alias"


def test_migration_731_guards_division_by_zero():
    code_only = _code_only(_read_migration())
    assert code_only.count("GREATEST(") == 6, "every one of the six formulas must guard its denominator"


def test_migration_731_no_self_transaction_wrapper():
    code_only = _code_only(_read_migration())
    assert not re.search(r"\bBEGIN\s*;", code_only)
    assert not re.search(r"\bCOMMIT\s*;", code_only)


# ── live integration (excluded by -m "not integration"; run manually) ──────

LIVE_DSN = os.environ.get("DATABASE_URL", "")


def _live_conn_or_skip():
    import psycopg

    try:
        conn = psycopg.connect(LIVE_DSN, connect_timeout=10, row_factory=psycopg.rows.dict_row)
    except Exception:
        pytest.skip("live Cloud SQL proxy (127.0.0.1:5433) not reachable in this environment")
    return conn


@pytest.mark.integration
@pytest.mark.parametrize("asset_id,table", list(_ASSET_TABLE.items()))
def test_migration_731_size_sql_executes_and_is_numerically_sane_live(asset_id, table):
    """Runs the actual migration, then executes the resulting size_sql for this asset
    against the real table, scoped to the canonical chart. Proves it runs without error
    and the proportional share is between 0 and the table's own total physical size.
    Rolled back at the end; never persists."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT size_sql FROM asset_registry WHERE asset_id = %s", (asset_id,)
            )
            row = cur.fetchone()
            if row is None:
                pytest.skip(f"{asset_id} not present in asset_registry in this environment")
            size_sql = row["size_sql"]

            # psycopg (unlike node-postgres, which stats/route.ts actually runs on)
            # does not recognize Postgres-native `$1` placeholders in cur.execute() —
            # it only binds its own `%s` style client-side and raises "0 placeholders"
            # for a literal `$1`. Substituting the fixed, hardcoded canonical chart_id
            # constant directly (never user input) sidesteps that psycopg-only gap
            # without touching the migration's own SQL, which IS correct for its real
            # caller. Confirmed this is a pre-existing test-tooling limitation, not
            # something new: test_f188_mi_gunanaka_count_sql.py's own live test hits the
            # identical psycopg error against a different, already-existing $1 query.
            cur.execute(size_sql.replace("$1", f"'{_CANONICAL_CHART_ID}'"))
            size_row = cur.fetchone()
            assert size_row is not None
            assert "size" in size_row, f"result column is not named 'size': {list(size_row.keys())}"
            share = size_row["size"]

            cur.execute(f"SELECT pg_total_relation_size('{table}') AS total")
            total = cur.fetchone()["total"]

        assert share is not None
        assert 0 <= share <= total, (
            f"proportional share {share} out of bounds for total table size {total}"
        )
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.integration
def test_migration_731_is_idempotent_live():
    """Running the migration twice inside one transaction produces the identical
    size_sql text the second time, for all six assets. Rolled back at the end."""
    conn = _live_conn_or_skip()
    sql = _read_migration()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT asset_id FROM asset_registry WHERE asset_id = ANY(%s)",
                (list(_ASSET_TABLE),),
            )
            present = {r["asset_id"] for r in cur.fetchall()}
            if not present:
                pytest.skip("none of the six L3 assets present in asset_registry in this environment")

            cur.execute(sql)
            cur.execute(
                "SELECT asset_id, size_sql FROM asset_registry WHERE asset_id = ANY(%s) ORDER BY asset_id",
                (list(_ASSET_TABLE),),
            )
            first_pass = {r["asset_id"]: r["size_sql"] for r in cur.fetchall()}

            cur.execute(sql)  # second application, same transaction
            cur.execute(
                "SELECT asset_id, size_sql FROM asset_registry WHERE asset_id = ANY(%s) ORDER BY asset_id",
                (list(_ASSET_TABLE),),
            )
            second_pass = {r["asset_id"]: r["size_sql"] for r in cur.fetchall()}

        assert first_pass == second_pass, "migration is not idempotent"
    finally:
        conn.rollback()
        conn.close()
