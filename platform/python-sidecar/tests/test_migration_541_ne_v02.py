"""Tests for migration 541 — ne_v02 corpus widening: `business_launch` N_e prior.

Two tiers, matching the house pattern (`test_bg_class_lifetime_counts.py` /
`TestMigration361` in `test_ka_sangam_a3_fixes.py`):

1. STATIC checks (always run, no DB): the migration file exists, carries the
   zero-padded `ne_v02` corpus version marker, the confirmed value 0.124, all six
   Tier N-i citation elements, the ON CONFLICT idempotency clause, a DOWN block,
   the honest-attrition/coverage note, and no LEL read (anti-circularity).

2. LIVE checks (skipped unless MIGRATION_TEST_DATABASE_URL or DATABASE_URL is
   set — pointed at a THROWAWAY Postgres, never production): the DDL slice of
   migrations 387+522 is applied, the ne_v01 corpus is seeded via the real seed
   module, migration 541 is applied TWICE (idempotency), and then:
     - the row lands at the reserved coordinate with class_prior = 0.124;
     - `ka_kshetra.load_class_lifetime_count` resolves business_launch to ne_v02
       while marriage still resolves to ne_v01 — the EXTEND semantics ruling R1
       ratifies (per-class `ORDER BY prior_version DESC LIMIT 1`);
     - the `brahma_class_priors_lifetime_basis_ck` DATA-HONESTY RAIL rejects an
       unsourced ne_v02 row (the rail applies to the new corpus version too);
     - the six ne_v01 rows are untouched.

ANTI-CIRCULARITY: nothing in this file, or in migration 541, reads the LEL.
"""
from __future__ import annotations

import os
import re

import pytest

_MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "migrations"
)
_MIG_541 = os.path.join(_MIGRATIONS_DIR, "541_ne_v02_business_launch_lifetime_count.sql")
_MIG_522 = os.path.join(_MIGRATIONS_DIR, "522_brahma_class_lifetime_counts.sql")
_MIG_387 = os.path.join(_MIGRATIONS_DIR, "387_brahma_class_priors.sql")

COORDINATE = dict(
    prior_version="ne_v02",
    signal_type_class="business_launch",
    fact_kind="lifetime_count_per_100y",
    source_subsystem="*",
    signal_tradition="*",
)
CONFIRMED_VALUE = 0.124


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def _joined(sql: str) -> str:
    """Join Postgres adjacent-string-literal continuations ('… ' \n '…') so
    phrase-level assertions see the string the DATABASE will store, not the
    line-wrapped source form."""
    return re.sub(r"'\s*\n\s*'", "", sql)


# ══ 1. STATIC ═════════════════════════════════════════════════════════════════

def test_migration_file_exists():
    assert os.path.isfile(_MIG_541), f"Migration file missing: {_MIG_541}"


def test_corpus_version_marker_is_zero_padded_ne_v02():
    """ka_kshetra does `ORDER BY prior_version DESC` — a STRING sort. Unpadded
    `ne_v10` would sort below `ne_v2`. ADJUDICATION-2 item 4 makes the padding
    mandatory; migration 522's header repeats it; this is the ne_v02 guard."""
    sql = _read(_MIG_541)
    assert "'ne_v02'" in sql
    m = re.search(r"'ne_v(\d+)'", sql)
    assert m is not None
    assert len(m.group(1)) >= 2, "prior_version suffix must be zero-padded to >= 2 digits"
    # No stray unpadded variant anywhere in the file.
    assert re.search(r"'ne_v\d'(?!\d)", sql) is None


def test_confirmed_value_and_coordinate_present():
    sql = _read(_MIG_541)
    assert "0.124" in sql
    assert "'business_launch'" in sql
    assert "'lifetime_count_per_100y'" in sql
    assert "'demographic_structural'" in sql


def test_all_six_tier_ni_citation_elements_present():
    """Publisher · edition/survey round · year · indicator/table id ·
    geography+cohort · retrievable URL — the ruling's six elements, verbatim
    anchors from the CONFIRMED verification packet."""
    sql = _read(_MIG_541)
    for anchor in (
        "Entrepreneurship Development Institute",          # publisher
        "Global Entrepreneurship Monitor India Report 2023/24",  # edition/survey round
        "2024",                                            # year
        "Table 3.1",                                       # indicator/table id
        "adults 18-64",                                    # geography+cohort
        "https://ediindia.org/wp-content/uploads/2025/04/GEM_2023-24-1.pdf",  # URL
    ):
        assert anchor in sql, f"missing Tier N-i citation element anchor: {anchor!r}"


def test_conversion_assumptions_and_uncertainty_recorded():
    sql = _joined(_read(_MIG_541))
    # Prevalence convention, not incidence scaling.
    assert "N_e = p" in sql
    assert "N_e = 100*r does NOT apply" in sql
    # Recorded uncertainty range.
    assert "[0.085, 0.25]" in sql
    # Corroboration + cross-check named.
    assert "Annex Table A2" in sql
    assert "Sixth Economic Census" in sql


def test_idempotency_clause_and_down_block():
    sql = _read(_MIG_541)
    assert "ON CONFLICT (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)" in sql
    assert "DO UPDATE SET" in sql
    assert "DOWN (manual rollback)" in sql
    assert "DELETE FROM brahma_class_priors" in sql


def test_honest_attrition_and_coverage_note_present():
    """R3's honest-attrition rail: the header must state what was and was NOT
    evaluated, so absence cannot be read as adjudication."""
    sql = _read(_MIG_541)
    assert "Evaluated, not widened" in sql
    assert "NOT evaluated" in sql
    assert "no_class_prior_row" in sql


def test_anti_circularity_no_lel_read():
    sql = _read(_MIG_541)
    assert "FROM life_events" not in sql
    assert "mimamsa_lel" not in sql


def test_touches_only_brahma_class_priors():
    """One row at one PK — no registry edit, no DDL, no other table (the writer
    and count_sql from 522 already cover the new row)."""
    sql = _read(_MIG_541)
    # Strip comment lines: only executable statements matter for this claim.
    executable = "\n".join(
        ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")
    )
    assert "ALTER TABLE" not in executable
    assert "CREATE TABLE" not in executable
    assert "asset_registry" not in executable
    assert "DELETE FROM" not in executable
    # Exactly one INSERT, targeting brahma_class_priors.
    inserts = re.findall(r"INSERT INTO\s+(\w+)", executable)
    assert inserts == ["brahma_class_priors"]
    # No statement-initial UPDATE (the upsert's `DO UPDATE SET` is not one).
    assert re.search(r"^\s*UPDATE\s", executable, re.MULTILINE) is None


# ══ 2. LIVE (throwaway Postgres) ══════════════════════════════════════════════

_LIVE_URL = os.environ.get("MIGRATION_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

pytestmark_live = pytest.mark.skipif(
    not _LIVE_URL,
    reason="live DB test — set MIGRATION_TEST_DATABASE_URL (throwaway Postgres) to run",
)


def _ddl_slices() -> list[str]:
    """The schema migration 541 needs, sliced from the REAL migration files —
    never re-typed here, so the test cannot drift from the applied DDL.

    387: everything up to its first seed INSERT (the CREATE TABLE + comments).
    522: sections 1-2 (the two columns + the lifetime-basis CHECK), i.e. up to
         the asset_registry section, which a throwaway DB does not carry.
    Both files are applied migrations and are therefore immutable (§N.4
    'NEVER EDIT A MIGRATION FILE AFTER IT HAS BEEN APPLIED'), so slicing on
    their own section markers is stable.
    """
    m387 = _read(_MIG_387)
    marker_387 = "-- ── §2.1"
    assert marker_387 in m387
    ddl_387 = m387.split(marker_387)[0]
    ddl_387 = ddl_387.replace("BEGIN;", "", 1)

    m522 = _read(_MIG_522)
    marker_522 = "-- ── 3. asset_registry"
    assert marker_522 in m522
    ddl_522 = m522.split("BEGIN;", 1)[1].split(marker_522)[0]

    return [ddl_387, ddl_522]


@pytest.fixture()
def live_conn():
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(_LIVE_URL, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            for ddl in _ddl_slices():
                cur.execute(ddl)
        yield conn
        conn.rollback()


def _apply_541(conn) -> None:
    sql = _read(_MIG_541)
    # Strip the transaction wrapper: the fixture owns the (rolled-back) txn.
    body = sql.split("BEGIN;", 1)[1].rsplit("COMMIT;", 1)[0]
    with conn.cursor() as cur:
        cur.execute(body)


@pytestmark_live
def test_live_row_lands_idempotently_and_extends_not_shadows(live_conn):
    from brahmagyan.l0_class_lifetime_counts import seed_class_lifetime_counts
    from services.ka_kshetra.stage4_field import load_class_lifetime_count

    # Seed the ne_v01 corpus through the real module, then apply 541 twice.
    seed_class_lifetime_counts(live_conn, autocommit=False)
    _apply_541(live_conn)
    _apply_541(live_conn)  # idempotency: ON CONFLICT DO UPDATE, no dup, no error

    with live_conn.cursor() as cur:
        cur.execute(
            """SELECT class_prior, prior_basis, source_ref, citation, ratified_by
                 FROM brahma_class_priors
                WHERE prior_version = %(prior_version)s
                  AND signal_type_class = %(signal_type_class)s
                  AND fact_kind = %(fact_kind)s
                  AND source_subsystem = %(source_subsystem)s
                  AND signal_tradition = %(signal_tradition)s""",
            COORDINATE,
        )
        rows = cur.fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert float(row["class_prior"]) == pytest.approx(CONFIRMED_VALUE)
    assert row["prior_basis"] == "demographic_structural"
    assert row["source_ref"] and "ediindia.org" in row["source_ref"]
    assert row["citation"] and "raw_figure:" in row["citation"]
    assert "conversion:" in row["citation"]

    # EXTEND semantics (ruling R1): business_launch resolves to ne_v02; the
    # ne_v01-covered classes keep resolving to ne_v01 — nothing shadowed.
    value, source = load_class_lifetime_count(live_conn, "business_launch")
    assert value == pytest.approx(CONFIRMED_VALUE)
    assert source[1].startswith("ne_v02|")

    value_m, source_m = load_class_lifetime_count(live_conn, "marriage")
    assert value_m == pytest.approx(0.984)
    assert source_m[1].startswith("ne_v01|")

    # The six ne_v01 rows are untouched.
    with live_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS c FROM brahma_class_priors "
            "WHERE prior_version = 'ne_v01' AND fact_kind = 'lifetime_count_per_100y'"
        )
        assert cur.fetchone()["c"] == 6


@pytestmark_live
def test_live_data_honesty_rail_applies_to_ne_v02(live_conn):
    """`brahma_class_priors_lifetime_basis_ck` must reject an unsourced ne_v02
    row exactly as it rejects an unsourced ne_v01 row — the corpus version does
    not relax the rail."""
    psycopg = pytest.importorskip("psycopg")
    _apply_541(live_conn)

    with live_conn.cursor() as cur:
        cur.execute("SAVEPOINT rail_probe")
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                """INSERT INTO brahma_class_priors
                     (prior_version, signal_type_class, fact_kind,
                      source_subsystem, signal_tradition, class_prior)
                   VALUES ('ne_v02', 'unsourced_class', 'lifetime_count_per_100y',
                           '*', '*', 0.5)"""
            )
        cur.execute("ROLLBACK TO SAVEPOINT rail_probe")
