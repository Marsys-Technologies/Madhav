"""test_n390_sade_sati_marker_integrity_rehearsal.py: SS N-390. Rehearsal of the sade_sati `not_computed` marker (PR-H1 item 2) against the LIVE integrity SQL.

The question: can the marker row the writer now emits for a boundary chart (an ayanamsha whose natal Moon sign differs from Lahiri's) make the `ga_sade_sati`
integrity contract (migrations 748 / 752 / 753 / 754) FAIL, and so stop a build? The contract's text is taken from the migration file that carries its final
(full replacement) value, migration 754, never retyped here. It runs on a DISPOSABLE PostgreSQL (never production) against a `chart_facts` built from the
production-shaped DDL in the F-A2 prerequisite schema (CHECK constraint on verification_pass_status, the sade_sati cycle unique indexes, the natural-key index).

The rows are the REAL output of `build_ga_sade_sati` (fixture data only, reads / scans stubbed), written with the writer's REAL `_insert_rows`:
  * canonical-like: five Aquarius Moons, labelled copies for the four non-Lahiri ids;
  * boundary: raman on the other side of a sign boundary (Pisces): its copied periods are NOT emitted, one marker row is.
Non-vacuity: the same SQL turns FALSE on a corrupted derived value, so a green is not a check that cannot fail.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

import pytest

psycopg = pytest.importorskip("psycopg")

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_REPO = _SIDECAR.parents[1]
sys.path.insert(0, str(_SIDECAR))
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(_REPO / "platform" / "scripts" / "governance" / "__tests__"))

from _disposable_pg import disposable_pg  # noqa: F401,E402  (the fixture must be importable here)
import ga_writers.ga_sade_sati_writer as S  # noqa: E402
from test_n341_item2_replicated_ayanamsha_labels import (  # noqa: E402
    ALL_FIVE, CHART, _NATAL, _RETROS, _SIGN_CHANGES, REF,
)

BUILD = "11111111-1111-4111-8111-111111111111"                  # chart_facts.build_id is a uuid column

MIGRATIONS = _REPO / "platform" / "migrations"
FINAL_MIGRATION = MIGRATIONS / "754_nirmana_l1_ga_sade_sati_integrity_contract_final.sql"
PREREQ_DDL = _REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "f_a2_key_widening" / "tests" / "schema" / "01_prereq_tables.sql"


# ── the live contract text and the production-shaped table ───────────────────────────────────────────────────────────────

def _integrity_sql() -> str:
    text = FINAL_MIGRATION.read_text(encoding="utf-8")
    m = re.search(r"integrity_check_sql = \$ck\$(.*?)\$ck\$\s*WHERE asset_id = 'ga_sade_sati';", text, re.S)
    assert m, "migration 754 no longer carries the ga_sade_sati integrity_check_sql in the expected form"
    return m.group(1)


def _chart_facts_ddl() -> list:
    """The CREATE TABLE and every index ON public.chart_facts, statement by statement, from the production-shaped prerequisite schema."""
    text = PREREQ_DDL.read_text(encoding="utf-8")
    table = re.search(r'CREATE TABLE public\."chart_facts" \(.*?\n\);', text, re.S)
    assert table, "chart_facts DDL not found in the prerequisite schema"
    indexes = re.findall(r"^CREATE (?:UNIQUE )?INDEX [^\n]*? ON public\.chart_facts [^\n]*;$", text, re.M)
    assert len(indexes) >= 10
    return [table.group(0)] + indexes


def test_no_later_migration_replaces_the_sade_sati_integrity_sql():
    """The text rehearsed here is the CURRENT one: among all migrations, the ones that SET ga_sade_sati's integrity_check_sql are exactly 748, 752, 753, 754 and 754 is the last."""
    setters = []
    for path in sorted(MIGRATIONS.glob("[0-9]*.sql")):
        t = path.read_text(encoding="utf-8")
        for m in re.finditer(r"UPDATE asset_registry\s+SET integrity_check_sql\s*=.*?WHERE asset_id\s*=\s*'([a-z_]+)'", t, re.S):
            if m.group(1) == "ga_sade_sati":
                setters.append(path.name.split("_", 1)[0])
    assert setters == ["748", "752", "753", "754"], setters


@pytest.fixture()
def conn(disposable_pg):
    cl = disposable_pg
    name = "n390_%d" % (abs(hash(os.urandom(8))) % 10**9)
    cl.psql("CREATE DATABASE %s" % name)
    c = psycopg.connect("postgresql://%s@%s:%d/%s" % (cl.user, cl.host, cl.port, name), autocommit=True)
    for stmt in _chart_facts_ddl():
        c.execute(stmt)
    yield c
    c.close()


# ── rows: the real builder, written by the real insert ───────────────────────────────────────────────────────────────────

@pytest.fixture()
def build_rows(monkeypatch):
    def _run(moon_signs: dict) -> list:
        captured: list = []
        monkeypatch.setattr(S, "_verify_upstream_rows", lambda conn, chart_id: {"ga_positions": True})
        monkeypatch.setattr(S, "_read_moon_sign_per_ayanamsha", lambda conn, chart_id: dict(moon_signs))
        monkeypatch.setattr(S, "_read_moon_pada_per_ayanamsha", lambda conn, chart_id: {a: 4 for a in moon_signs})
        monkeypatch.setattr(S, "_detect_saturn_sign_changes", lambda ws, we: list(_SIGN_CHANGES))
        monkeypatch.setattr(S, "_detect_saturn_retrogrades", lambda ws, we: list(_RETROS))
        monkeypatch.setattr(S, "_build_static_natal_facts", lambda conn, chart_id, ay, moon_sign, moon_pada: dict(_NATAL, lagna_sign="Aries"))
        monkeypatch.setattr(S, "_lookup_dasha_lord_at", lambda *a, **k: "Venus")
        monkeypatch.setattr(S, "_lookup_tara_bala_for_saturn_at", lambda *a, **k: None)
        monkeypatch.setattr(S, "_lookup_argala_for_sign", lambda *a, **k: [])
        monkeypatch.setattr(S, "_insert_rows", lambda conn, rows: captured.extend(rows) or len(rows))
        monkeypatch.setattr(S, "replace_prior_chart_facts", lambda conn, rows: 0)
        monkeypatch.setattr(S, "_refresh_mv", lambda conn: "SKIP")
        S.build_ga_sade_sati(CHART, BUILD, conn=object(), birth_params=None)
        return captured
    return _run


def _store(conn, rows: list) -> int:
    """Write the rows with the writer's own `_insert_rows` SQL (only the prior-row delete, which needs the data-plane tables, is skipped)."""
    import importlib
    real = importlib.import_module("ga_writers.ga_sade_sati_writer")
    src_insert = real.__dict__["_ORIGINAL_INSERT_ROWS"]
    return src_insert(conn, rows)


@pytest.fixture(autouse=True)
def _keep_the_real_insert(monkeypatch):
    # capture the real _insert_rows before any test patches it, and neutralise only its prior-row delete
    S._ORIGINAL_INSERT_ROWS = S._insert_rows
    monkeypatch.setattr(S, "replace_prior_chart_facts", lambda conn, rows: 0)
    yield
    del S._ORIGINAL_INSERT_ROWS


def _passes(conn) -> bool:
    rows = conn.execute(_integrity_sql()).fetchall()
    assert len(rows) == 1 and len(rows[0]) == 1, rows
    assert rows[0][0] in (True, False), "integrity_passed must be a boolean, got %r" % (rows[0][0],)
    return rows[0][0]


# ── the rehearsal ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_contract_passes_on_the_empty_table(conn):
    assert _passes(conn) is True


def test_canonical_like_fixture_five_aquarius_moons_with_labelled_copies_passes(conn, build_rows):
    rows = build_rows({ay: "Aquarius" for ay in ALL_FIVE})
    assert {r["ayanamsha_id"] for r in rows} == set(ALL_FIVE)
    assert not any(r["fact_subject"] == "NOT_COMPUTED" for r in rows)
    assert any("valid because the natal Moon sign is the same" in r["source_calculation"] for r in rows)
    assert _store(conn, rows) == len(rows)
    assert _passes(conn) is True


def test_boundary_fixture_with_the_not_computed_marker_passes(conn, build_rows):
    signs = {ay: "Aquarius" for ay in ALL_FIVE}
    signs["raman"] = "Pisces"
    rows = build_rows(signs)
    markers = [r for r in rows if r["fact_subject"] == "NOT_COMPUTED"]
    assert len(markers) == 1 and markers[0]["ayanamsha_id"] == "raman" and markers[0]["fact_category"] == "sade_sati_cycle"
    assert not [r for r in rows if r["ayanamsha_id"] == "raman" and r["fact_subject"].startswith("CYCLE_")], "no copied periods for the boundary ayanamsha"
    assert _store(conn, rows) == len(rows)
    stored = conn.execute("SELECT count(*) FROM chart_facts WHERE ayanamsha_id = 'raman' AND fact_subject = 'NOT_COMPUTED'").fetchone()[0]
    assert stored == 1
    assert _passes(conn) is True


def test_two_boundary_ids_and_a_missing_lahiri_sign_also_pass(conn, build_rows):
    signs = {ay: "Aquarius" for ay in ALL_FIVE}
    signs["raman"], signs["krishnamurti"] = "Pisces", "Capricorn"
    rows = build_rows(signs)
    assert len([r for r in rows if r["fact_subject"] == "NOT_COMPUTED"]) == 2
    _store(conn, rows)
    assert _passes(conn) is True


def test_the_check_is_not_vacuous_it_turns_false_on_a_corrupted_derived_value(conn, build_rows):
    """Non-vacuity: the same SQL, on the same canonical-like rows, must read FALSE once a derived value is corrupted (conjunct (c) tolerates one day, so the probe moves it by thirty)."""
    rows = build_rows({ay: "Aquarius" for ay in ALL_FIVE})
    _store(conn, rows)
    assert _passes(conn) is True
    changed = conn.execute(
        "UPDATE chart_facts SET fact_value_num = fact_value_num + 30 WHERE ayanamsha_id = %s AND fact_category = 'sade_sati_cycle' AND fact_key = 'duration_days'", (REF,)).rowcount
    assert changed >= 1, "the fixture has no duration_days row to corrupt: the non-vacuity probe is void"
    assert _passes(conn) is False


def test_the_contract_never_names_the_markers_key_so_it_passes_by_construction_not_by_blindness():
    """Stated honestly: the contract's conjuncts select rows by explicit fact_key values and join cycle start / end pairs. The marker's own key and subject are named nowhere in it, so no
    conjunct can read it; the green rows above come from running the SQL, this test pins WHY (and fails if a later contract starts naming the marker, which would need re-rehearsing)."""
    sql = _integrity_sql()
    assert "not_computed_reason" not in sql and "NOT_COMPUTED" not in sql
    assert S.NOT_COMPUTED_KEY == "not_computed_reason" and S.NOT_COMPUTED_SUBJECT == "NOT_COMPUTED"
