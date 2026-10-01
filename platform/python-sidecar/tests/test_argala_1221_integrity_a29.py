"""Migration 1221 (DRAFT): the integrity conjunct (a29), argala NULL <=> empty source sign (SS N-61, CLAUDE.md N.8).

Executed against a disposable local Postgres (tests/pg_disposable.py). Proves: the guards refuse unexpected state, the
patch is idempotent and touches nothing but integrity_check_sql, and (a29) kills six mutants, including the NULL on an
occupied cell that the older conjunct (e27) lets through.
"""
from __future__ import annotations

import pathlib
import re
import sys
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
M904 = (MIGRATIONS / "904_nirmana_l1_ga_structural_integrity_check_scope.sql").read_text(encoding="utf-8")
M1221_PATH = MIGRATIONS / "1221_nirmana_l1_ga_structural_integrity_a29_argala_null.sql"
M1221 = M1221_PATH.read_text(encoding="utf-8")
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD = str(uuid.uuid4())
STANDIN = "SELECT\n  (TRUE)\n  -- (g28) stand-in tail\n  AND NOT EXISTS (SELECT 1 FROM chart_facts WHERE false)\n  AS integrity_passed\n\n"
SCHEMA = """
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor integer, integrity_check_sql text);
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, build_id uuid,
  fact_category text, fact_subject text, fact_key text, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb);
"""


def _no_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def _a29() -> str:
    body = M1221.split("conjunct constant text := $conj$", 1)[1].split("$conj$", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _e27() -> str:
    body = M904.split("-- (e27) argala-offset full re-derivation", 1)[1].split("-- (f27)", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


# ── static ──────────────────────────────────────────────────────────────────────────────────────

def test_1221_is_its_own_file_and_does_only_the_integrity_patch():
    code = _no_comments(M1221)
    assert "UPDATE asset_registry" in code and code.count("UPDATE asset_registry") == 1
    assert "SET integrity_check_sql" in code
    for other in ("count_sql", "target_floor", "fact_category_ownership", "asset_output_digest_specs"):
        assert other not in code
    assert "AS integrity_passed" in code and "(g28)" in code
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", M1221, re.M)
    assert "NAMED STEP of the S-L1" in M1221 and "IMMEDIATELY BEFORE" in M1221


def test_1219_no_longer_carries_the_conjunct():
    m1219 = (MIGRATIONS / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql").read_text(encoding="utf-8")
    assert "(a29)" not in _no_comments(m1219) and "integrity_check_sql" not in _no_comments(m1219)


# ── executed ────────────────────────────────────────────────────────────────────────────────────

def _fresh(port: int) -> str:
    db = new_db(port)
    q(port, db, SCHEMA)
    q(port, db, f"INSERT INTO asset_registry VALUES ('ga_structural', 'x', 98446, $a${STANDIN}$a$), ('ga_strength', 'y', 1, 'keep')")
    return db


@requires_pg
def test_patch_applies_once_touches_only_integrity_text_and_is_idempotent(pg):
    db = _fresh(pg)
    other = "SELECT count_sql, target_floor FROM asset_registry ORDER BY asset_id"
    other_before = q(pg, db, other)
    assert psql(pg, db, file=M1221_PATH).returncode == 0
    text = q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_structural'")
    assert text.count("(a29)") >= 1 and text.count("AS integrity_passed") == 1 and "(g28)" in text
    assert q(pg, db, other) == other_before
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_strength'") == "keep"
    once = q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'")
    assert psql(pg, db, file=M1221_PATH).returncode == 0
    assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == once
    assert q(pg, db, "SELECT integrity_passed FROM (" + text.rstrip() + ") z") == "t"      # valid SQL, true on empty facts


@requires_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '(g28)', '(zzz)') WHERE asset_id='ga_structural'", "lacks conjunct (g28)"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n  AS integrity_passed' WHERE asset_id='ga_structural'", "anchor is not unique"),
    ("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='ga_structural'", "no integrity_check_sql"),
])
def test_patch_refuses_unexpected_live_state(pg, sabotage, expect):
    db = _fresh(pg)
    q(pg, db, sabotage)
    r = psql(pg, db, file=M1221_PATH)
    assert r.returncode != 0 and expect in r.stderr, r.stderr


def _seed(port, db, cells):
    """Sun in Capricorn (10), Moon in Aquarius (11). D1 argala cells for target Scorpio (8): offsets 2, 4, 5, 11 read
    signs 9, 11, 12, 6, so only the 4th (Aquarius, Moon) is occupied. `cells` maps source sign -> (num, text)."""
    q(port, db, f"""
      INSERT INTO chart_facts VALUES
       ('d1','{CANON}','a','{BUILD}','graha_dignity_per_varga','D1_SUN','dignity_state',NULL,NULL,'{{"varga":"D1","sign":"Capricorn"}}'),
       ('d2','{CANON}','a','{BUILD}','graha_dignity_per_varga','D1_MOON','dignity_state',NULL,NULL,'{{"varga":"D1","sign":"Aquarius"}}');""")
    for i, (src, off) in enumerate(((9, 2), (11, 4), (12, 5), (6, 11))):
        num, text = cells[src]
        n = "NULL" if num is None else str(num)
        t = "NULL" if text is None else f"'{text}'"
        q(port, db, f"INSERT INTO chart_facts VALUES ('c{i}','{CANON}','a','{BUILD}','argala_natal_matrix','D1_SIGN_8',"
                    f"'from_sign_{src}_offset_{off}',{t},{n},NULL)")


def _violations(port, db, conjunct: str) -> int:
    return int(q(port, db, "SELECT CASE WHEN (SELECT true " + conjunct + ") THEN 0 ELSE 1 END"))


GOOD = {9: (None, "no_occupant"), 11: (1.0, None), 12: (None, "no_occupant"), 6: (None, "no_occupant")}
MUTANTS = {
    "NULL on an occupied cell (the case (e27) passes)": {**GOOD, 11: (None, "no_occupant")},
    "NULL without the text on an occupied cell": {**GOOD, 11: (None, None)},
    "stale 1.0 on an empty cell (today's behaviour)": {**GOOD, 9: (1.0, None)},
    "empty cell NULL but marker missing": {**GOOD, 12: (None, None)},
    "empty cell carries the marker AND a score": {**GOOD, 6: (0.75, "no_occupant")},
    "occupied cell carries the marker": {**GOOD, 11: (1.0, "no_occupant")},
}


@requires_pg
def test_a29_accepts_the_correct_cells_and_kills_every_mutant(pg):
    db = new_db(pg)
    q(pg, db, SCHEMA)
    _seed(pg, db, GOOD)
    assert _violations(pg, db, _a29()) == 0
    for name, cells in MUTANTS.items():
        d = new_db(pg)
        q(pg, d, SCHEMA)
        _seed(pg, d, cells)
        assert _violations(pg, d, _a29()) == 1, f"(a29) let this mutant through: {name}"


@requires_pg
def test_the_old_conjunct_e27_is_vacuous_on_null_which_is_why_a29_exists(pg):
    d = new_db(pg)
    q(pg, d, SCHEMA)
    _seed(pg, d, MUTANTS["NULL on an occupied cell (the case (e27) passes)"])
    assert _violations(pg, d, _e27()) == 0          # (e27) passes the NULL on an occupied cell
    assert _violations(pg, d, _a29()) == 1          # (a29) fails it
    d2 = new_db(pg)
    q(pg, d2, SCHEMA)
    _seed(pg, d2, {**GOOD, 11: (0.75, None)})        # a wrong non-NULL score is still (e27)'s job
    assert _violations(pg, d2, _e27()) == 1 and _violations(pg, d2, _a29()) == 0
