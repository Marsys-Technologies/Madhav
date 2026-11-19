"""Migration 1215 (Track I-8): BEHAVIOURAL test of ka_avadhi's scoped `integrity_check_sql` on a fixture.

The static sibling (`test_migration_1215_ka_avadhi_integrity_scope.py`) proves the TEXT; this executes the
SQL (extracted from the migration file) against fixture rows and asserts the boolean it returns.

SAFETY. Opt-in: skips unless `KA_AVADHI_INTEGRITY_TEST_DSN` is set. The DSN must pass the same
disposable-database guard as the destructive P0 harness (`tests/l3/_p0_harness.py`: local host + disposable
db name, refuses `service=`), checked both on the DSN text and on the server's `current_database()`;
otherwise the test RAISES (never skips). It touches nothing durable: every fixture table is a TEMP table
that shadows the real name for this session only (`pg_temp` precedes `public` in the search path), and the
transaction is rolled back at the end.

Scenarios (reviewer's list): a clean canonical fixture passes; canonical chart_dashas with ZERO canonical
avadhi rows FAILS (non-vacuity (f)); another chart's stale bad rows do not affect a clean canonical (1023's
text fails there: that is the I-7 defect); each canonical violation of (a), (b), (c), (d), (e) FAILS; canonical
chara_karaka dashas without chara_karaka avadhi rows FAILS (1023's text passes there: the vocabulary defect).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from tests.l3 import _p0_harness as guard  # noqa: E402  (the shared disposable-DB guard)

_REPO = _HERE.parents[2]
_NEW = _REPO / "platform" / "migrations" / "1215_suvarna_i8_ka_avadhi_integrity_check_chart_scope.sql"
_OLD = _REPO / "platform" / "migrations" / "1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql"
_DSN_ENV = "KA_AVADHI_INTEGRITY_TEST_DSN"

C = "482012f1-710e-4a25-994a-93821f5871aa"
O = "1c826d5a-0000-4000-8000-000000000001"  # a non-canonical chart (stale rows)
SYSTEMS = ["vimshottari", "yogini", "ashtottari", "chara_karaka", "naisargika", "mudda", "kalachakra"]


def _ck(path: Path) -> str:
    t = path.read_text()
    return t[t.index("$ck$") + 4 : t.rindex("$ck$")]


def _connect_checked(dsn: str):
    """Guard (raise, never skip) then connect, then re-check the server's own current_database()."""
    guard.assert_safe_harness_dsn(dsn)
    import psycopg
    import psycopg.rows

    conn = psycopg.connect(dsn, row_factory=psycopg.rows.dict_row, connect_timeout=5)
    try:
        guard.assert_disposable_connection(conn)
    except guard.HarnessSafetyError:
        conn.close()
        raise
    return conn


@pytest.fixture
def cur():
    dsn = os.environ.get(_DSN_ENV)
    if not dsn:
        pytest.skip(f"{_DSN_ENV} not set (opt-in behavioural test against a disposable database)")
    pytest.importorskip("psycopg")
    conn = _connect_checked(dsn)
    c = conn.cursor()
    c.execute("CREATE TEMP TABLE kala_avadhi (chart_id uuid, system_id text, level_n int, period_start date,"
              " period_end date, lord_graha text, dossier jsonb)")
    c.execute("CREATE TEMP TABLE chart_dashas (chart_id uuid, ayanamsha_id text, system_id text, level_n int,"
              " start_date date, end_date date, lord_graha text)")
    c.execute("CREATE TEMP TABLE chart_facts (chart_id uuid, fact_id text)")
    c.execute("CREATE TEMP TABLE bodha_pratijna (chart_id uuid, pratijna_id text)")
    yield c
    conn.rollback()
    conn.close()


def _seed(c, chart, *, systems=SYSTEMS, avadhi_systems=None, refs=True, bad_lord=False):
    """One MD (level 1) and one AD (level 2) per system, lord Sun, with matching avadhi rows."""
    avadhi_systems = systems if avadhi_systems is None else avadhi_systems
    c.execute("INSERT INTO chart_facts VALUES (%s, 'F1')", (chart,))
    c.execute("INSERT INTO bodha_pratijna VALUES (%s, 'p1')", (chart,))
    for s in systems:
        for lvl, (a, b) in ((1, ("2000-01-01", "2010-01-01")), (2, ("2000-01-01", "2002-01-01"))):
            c.execute("INSERT INTO chart_dashas VALUES (%s,'lahiri_chitrapaksha',%s,%s,%s,%s,'Sun')",
                      (chart, s, lvl, a, b))
            if s not in avadhi_systems:
                continue
            dossier = {"lord_condition_fact_refs": [{"fact_id": "F1", "fact_subject": "SUN"}] if refs else [],
                       "activated_pratijna_ids": ["p1"]}
            c.execute("INSERT INTO kala_avadhi VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)",
                      (chart, s, lvl, a, b, "Moon" if bad_lord else "Sun", json.dumps(dossier)))


def _run(c, path=_NEW) -> bool:
    c.execute(_ck(path))
    return bool(next(iter(c.fetchone().values())))


def test_clean_canonical_passes(cur):
    _seed(cur, C)
    assert _run(cur) is True


def test_canonical_dashas_but_zero_avadhi_rows_fails_nonvacuity(cur):
    _seed(cur, C, avadhi_systems=[])
    assert _run(cur) is False
    # the reviewer's finding: 1023's text certifies the empty canonical table
    assert _run(cur, _OLD) is True


def test_other_charts_stale_bad_rows_do_not_affect_a_clean_canonical(cur):
    _seed(cur, C)
    _seed(cur, O, refs=False)  # stale: empty lord_condition_fact_refs on every graha-lord row (violates (c))
    assert _run(cur) is True
    assert _run(cur, _OLD) is False  # the I-7 defect: table-wide scan fails on the OTHER chart's rows


def test_zero_canonical_rows_fails_even_when_another_chart_has_rows(cur):
    _seed(cur, C, avadhi_systems=[])
    _seed(cur, O)  # (f) must be scoped to the canonical chart: another chart's rows are not canonical non-vacuity
    assert _run(cur) is False


def _other_bad_a(c):  # a stale row with no chart_dashas counterpart
    c.execute("INSERT INTO kala_avadhi VALUES (%s,'vimshottari',1,'1990-01-01','1991-01-01','Sun','{}'::jsonb)", (O,))


def _other_bad_b(c):  # partial coverage
    c.execute("DELETE FROM kala_avadhi WHERE chart_id = %s AND system_id = 'yogini'", (O,))


def _other_bad_c(c):  # empty refs
    c.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{lord_condition_fact_refs}', '[]') WHERE chart_id = %s", (O,))


def _other_bad_d(c):  # ref names the wrong lord
    c.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{lord_condition_fact_refs,0,fact_subject}', '\"MOON\"')"
              " WHERE chart_id = %s", (O,))


def _other_bad_e(c):  # dead pratijna id
    c.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{activated_pratijna_ids}', '[\"dead\"]') WHERE chart_id = %s", (O,))


@pytest.mark.parametrize("mutate", [_other_bad_a, _other_bad_b, _other_bad_c, _other_bad_d, _other_bad_e],
                         ids=list("abcde"))
def test_each_conjunct_ignores_another_charts_violation(cur, mutate):
    """Scope proof per conjunct: a violation of (a)..(e) confined to a NON-canonical chart does not fail the check."""
    _seed(cur, C)
    _seed(cur, O)
    mutate(cur)
    assert _run(cur) is True
    assert _run(cur, _OLD) is False  # 1023's table-wide text trips on it


@pytest.mark.parametrize("system", SYSTEMS)
def test_every_declared_system_is_covered_by_conjunct_b(cur, system):
    _seed(cur, C, avadhi_systems=[s for s in SYSTEMS if s != system])
    assert _run(cur) is False


def test_violation_c_empty_refs_on_canonical_fails(cur):
    _seed(cur, C, refs=False)
    assert _run(cur) is False


def test_violation_d_wrong_subject_and_unresolved_fact_fail(cur):
    _seed(cur, C)
    cur.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{lord_condition_fact_refs,0,fact_subject}', '\"MOON\"')"
                " WHERE system_id = 'yogini' AND level_n = 1")
    assert _run(cur) is False
    cur.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{lord_condition_fact_refs,0,fact_subject}', '\"SUN\"')")
    assert _run(cur) is True
    cur.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{lord_condition_fact_refs,0,fact_id}', '\"NOPE\"')"
                " WHERE system_id = 'mudda' AND level_n = 2")
    assert _run(cur) is False


def test_violation_e_unresolved_pratijna_id_fails(cur):
    _seed(cur, C)
    cur.execute("UPDATE kala_avadhi SET dossier = jsonb_set(dossier, '{activated_pratijna_ids}', '[\"dead\"]')"
                " WHERE system_id = 'kalachakra' AND level_n = 1")
    assert _run(cur) is False


def test_violation_a_row_not_matching_l1_spine_fails(cur):
    _seed(cur, C, bad_lord=True)  # avadhi lord differs from chart_dashas lord
    assert _run(cur) is False
    cur.execute("DELETE FROM kala_avadhi")
    _seed_extra = ("INSERT INTO kala_avadhi VALUES (%s,'vimshottari',1,'1990-01-01','1991-01-01','Sun','{}'::jsonb)")
    _seed(cur, C)
    cur.execute(_seed_extra, (C,))  # a stale row with no chart_dashas counterpart
    assert _run(cur) is False


def test_violation_b_partial_coverage_fails(cur):
    _seed(cur, C)
    cur.execute("DELETE FROM kala_avadhi WHERE system_id = 'vimshottari' AND level_n = 2")
    assert _run(cur) is False


def test_canonical_chara_karaka_dashas_without_avadhi_rows_fail(cur):
    _seed(cur, C, avadhi_systems=[s for s in SYSTEMS if s != "chara_karaka"])
    assert _run(cur) is False
    # 1023 ignored chara_karaka coverage (it listed 'chara'): the vocabulary defect
    assert _run(cur, _OLD) is True


@pytest.mark.parametrize("dsn", [
    "postgresql://u@127.0.0.1:5432/madhav_prod",
    "postgresql://u@prod-db.example.com:5432/kala_harness",
    "service=prod",
])
def test_guard_refuses_a_production_dsn_before_connecting(dsn):
    # a raise (never a skip); runs without any database or psycopg
    with pytest.raises(guard.HarnessSafetyError):
        _connect_checked(dsn)
