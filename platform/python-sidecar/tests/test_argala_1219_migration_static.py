"""Checks of the DRAFT migration 1219 (SS N-61 + Q-L1-04): ownership, count_sql, digest spec, integrity (a29).

Static checks always run. The SQL is also EXECUTED against a disposable local Postgres (initdb into a temp dir,
never the project database) when the binaries are on PATH or in /opt/homebrew/bin; those tests skip otherwise.
They prove: the guards refuse unexpected live state, the patch is idempotent, the ownership list covers every
category the writer emits, and the (a29) conjunct kills the mutants (NULL on an occupied cell, a stale 1.0 on an
empty cell, a missing no_occupant marker) that the old conjunct (e27) lets through.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")
M904 = (MIGRATIONS / "904_nirmana_l1_ga_structural_integrity_check_scope.sql").read_text(encoding="utf-8")
M1219_PATH = MIGRATIONS / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql"
M1219 = M1219_PATH.read_text(encoding="utf-8")

OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


def _spec(text: str) -> dict:
    m = re.search(r"'(\{\"version\":\"nirmana-output-digest-spec-v1\".*?\})'::jsonb", text, re.S)
    assert m
    return json.loads(m.group(1))


def _ownership_pairs() -> list[tuple[str, str]]:
    block = M1219.split("INSERT INTO _own_1219 (fact_category, owning_asset_id) VALUES", 1)[1].split(";", 1)[0]
    return re.findall(r"\('([a-z0-9_]+)', '(ga_[a-z_]+)'\)", block)


# ── static ──────────────────────────────────────────────────────────────────────────────────────

def test_914_sha_is_reproduced_by_the_real_digest_function():
    assert canonical_digest(_spec(M914)) == OLD_SHA


def test_new_spec_is_the_old_spec_plus_exactly_the_new_category_and_its_sha_is_real():
    old, new = _spec(M914), _spec(M1219)
    old_cats = old["components"][0]["where_in"]["fact_category"]
    new_cats = new["components"][0]["where_in"]["fact_category"]
    assert len(old_cats) == 81 and len(new_cats) == 82
    assert set(new_cats) - set(old_cats) == {"argala_graha_natal"} and set(old_cats) <= set(new_cats)
    assert new_cats == sorted(new_cats)
    old["components"][0]["where_in"]["fact_category"] = new_cats
    assert old == new
    assert canonical_digest(new) == NEW_SHA
    assert M1219.count(NEW_SHA) >= 3 and OLD_SHA in M1219


def test_ownership_covers_every_category_the_structural_writer_emits_and_the_argala_row():
    pairs = _ownership_pairs()
    assert ("argala_graha_natal", "ga_structural") in pairs
    structural = {c for c, a in pairs if a == "ga_structural"}
    spec_cats = set(_spec(M914)["components"][0]["where_in"]["fact_category"])
    # every category in the digest spec is either already owned by ga_structural (842 / 410) or added here
    owned_already = {l.strip() for l in (_OWNED_STRUCTURAL.splitlines())}
    assert spec_cats <= (owned_already | structural)
    # the 12 categories of the decision sheet (Q-L1-04) are all there
    twelve = {"virupa_drishti", "karaka_web_per_varga", "significator_path", "panchadha_maitri",
              "conjunction_special_point", "nakshatra_lord_relationship", "tara_bala", "yoga_label",
              "kendradhipati_dosha", "upapada_lagna", "dosha_label", "nakshatra_co_tenancy"}
    assert twelve <= structural
    assert len(pairs) == len(set(pairs))
    assert {a for _, a in pairs} <= {"ga_structural", "ga_strength", "ga_nakshatra", "ga_panchanga", "ga_positions",
                                     "ga_sade_sati", "ga_sensitive", "ga_sensitive_degree", "ga_condition"}


# the 64 categories ga_structural owned on 2026-10-02 (read-only snapshot; 410 + 842), minus nothing
_OWNED_STRUCTURAL = pathlib.Path("/Users/Dev/suvarna-evidence/TrackI/argala_l1/owned_structural.txt").read_text() \
    if pathlib.Path("/Users/Dev/suvarna-evidence/TrackI/argala_l1/owned_structural.txt").exists() else ""


@pytest.mark.skipif(not _OWNED_STRUCTURAL, reason="ownership snapshot is outside the repo")
def test_snapshot_is_the_64_rows_read_live():
    assert len(_OWNED_STRUCTURAL.split()) == 64


def test_the_four_parts_and_no_transaction_statements():
    assert "ON CONFLICT (fact_category, owning_asset_id) DO NOTHING" in M1219
    assert "retired_at = now()" in M1219 and "unrecognised active row" in M1219
    assert "AS integrity_passed" in M1219 and "(a29)" in M1219 and "position('(g28)'" in M1219
    assert "house_bhava_bala_%" in M1219
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", M1219, re.M)


def test_the_category_in_the_spec_is_the_one_the_writer_emits():
    import ga_writers.ga_structural_writer as sut
    rows = sut._build_argala_graha_rows(
        {"Mars": {"sign_num": 1}, "Sun": {"sign_num": 2}}, "D1", "c", "b", "a", "t", "e")
    assert {r["fact_category"] for r in rows} == {"argala_graha_natal"}


# ── executed against a disposable Postgres ──────────────────────────────────────────────────────

def _bin(name: str) -> str | None:
    return shutil.which(name) or (f"/opt/homebrew/bin/{name}" if os.path.exists(f"/opt/homebrew/bin/{name}") else None)


INITDB, PG_CTL, PSQL = _bin("initdb"), _bin("pg_ctl"), _bin("psql")
pytestmark_pg = pytest.mark.skipif(not (INITDB and PG_CTL and PSQL), reason="no local Postgres binaries")


@pytest.fixture(scope="module")
def pg():
    d = tempfile.mkdtemp(prefix="pg1219_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"],
                   check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o",
                    f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d}",
                    "-l", d + "/log", "-w", "start"], check=True, capture_output=True)
    try:
        yield port
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


def _psql(port: int, db: str, sql: str | None = None, file: pathlib.Path | None = None):
    cmd = [PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", db,
           "-v", "ON_ERROR_STOP=1"]
    cmd += ["-f", str(file)] if file else ["-c", sql]
    return subprocess.run(cmd, capture_output=True, text=True)


def _q(port, db, sql):
    r = _psql(port, db, sql)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


SCHEMA = """
CREATE TABLE fact_category_ownership (fact_category text NOT NULL, owning_asset_id text NOT NULL,
  created_at timestamptz DEFAULT now(), PRIMARY KEY (fact_category, owning_asset_id));
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor integer, integrity_check_sql text);
CREATE TABLE asset_output_digest_specs (asset_id text NOT NULL, spec_sha256 text NOT NULL, spec jsonb NOT NULL,
  reviewed_at timestamptz, retired_at timestamptz, UNIQUE (asset_id, spec_sha256));
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, build_id uuid,
  fact_category text, fact_subject text, fact_key text, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb);
"""

GA_STRENGTH_SQL = ("SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1 AND (fact_category LIKE 'graha_shadbala_%' "
                   "OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala') OR fact_category LIKE '%vimsopaka%' "
                   "OR fact_category LIKE 'ashtakavarga_%' OR fact_category LIKE '%bhava_bala%' "
                   "OR fact_category = 'graha_saptavargaja_bala_component' OR fact_category LIKE 'graha_%_bala_per_varga')")
GA_CONDITION_SQL = ("SELECT (SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1) + (SELECT count(*) FROM chart_facts "
                    "WHERE chart_id = $1 AND (fact_category LIKE 'graha_avastha_%_per_varga' OR fact_category = 'graha_yuddha')) AS count")
INTEGRITY_STANDIN = "SELECT\n  (TRUE)\n  -- (g28) stand-in tail\n  AND NOT EXISTS (SELECT 1 FROM chart_facts WHERE false)\n  AS integrity_passed\n\n"


def _fresh_db(port: int) -> str:
    db = "t" + uuid.uuid4().hex[:10]
    assert _psql(port, "postgres", f"CREATE DATABASE {db}").returncode == 0
    _q(port, db, SCHEMA)
    old_spec = json.dumps(_spec(M914)).replace("'", "''")
    _q(port, db, f"""
      INSERT INTO fact_category_ownership VALUES ('bhadra_flag','ga_structural'), ('bhava_bala_lord','ga_structural'),
        ('graha_avastha_lajjitadi','ga_condition');
      INSERT INTO asset_registry VALUES ('ga_strength', $a${GA_STRENGTH_SQL}$a$, 13621, NULL),
        ('ga_condition', $a${GA_CONDITION_SQL}$a$, 2880, NULL),
        ('ga_structural', 'x', 98446, $a${INTEGRITY_STANDIN}$a$);
      INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural', '{OLD_SHA}', '{old_spec}'::jsonb);
    """)
    return db


@pytestmark_pg
def test_migration_applies_every_part_and_is_idempotent(pg):
    db = _fresh_db(pg)
    r = _psql(pg, db, file=M1219_PATH)
    assert r.returncode == 0, r.stderr
    pairs = _ownership_pairs()
    # 3 seeded rows + every listed pair (none of the pairs is among the seeded rows)
    assert int(_q(pg, db, "SELECT count(*) FROM fact_category_ownership")) == 3 + len(pairs)
    assert _q(pg, db, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='argala_graha_natal' "
                      "AND owning_asset_id='ga_structural'") == "1"
    # dual ownership of the five panchanga categories: ga_structural kept, ga_panchanga added
    assert _q(pg, db, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='bhadra_flag'") == "2"
    # ga_strength narrowed (the 420 ga_structural bhava_bala_* rows are no longer claimed), floors re-declared
    assert _q(pg, db, "SELECT count_sql LIKE '%house_bhava_bala_%' AND position('LIKE ''%bhava_bala%''' in count_sql) = 0 "
                      "AND target_floor = 13721 FROM asset_registry WHERE asset_id='ga_strength'") == "t"
    assert _q(pg, db, "SELECT count_sql, target_floor FROM asset_registry WHERE asset_id='ga_condition'") == \
        "SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1|45"
    # digest spec: old retired, new active exactly once
    assert _q(pg, db, "SELECT count(*) FROM asset_output_digest_specs WHERE asset_id='ga_structural' AND retired_at IS NULL "
                      f"AND spec_sha256='{NEW_SHA}'") == "1"
    assert _q(pg, db, f"SELECT retired_at IS NOT NULL FROM asset_output_digest_specs WHERE spec_sha256='{OLD_SHA}'") == "t"
    # integrity patched once, still a single `AS integrity_passed`, original tail intact
    text = _q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_structural'")
    assert text.count("(a29)") >= 1 and text.count("AS integrity_passed") == 1 and "(g28)" in text
    before = _q(pg, db, "SELECT (SELECT md5(string_agg(coalesce(integrity_check_sql, '') || coalesce(count_sql, ''), '' ORDER BY asset_id)) FROM asset_registry) || (SELECT count(*) FROM fact_category_ownership)")
    # idempotent re-run: same result, no error
    assert _psql(pg, db, file=M1219_PATH).returncode == 0
    after = _q(pg, db, "SELECT (SELECT md5(string_agg(coalesce(integrity_check_sql, '') || coalesce(count_sql, ''), '' ORDER BY asset_id)) FROM asset_registry) || (SELECT count(*) FROM fact_category_ownership)")
    assert before == after
    # the patched integrity SQL is valid and runs (true on an empty chart_facts)
    assert _q(pg, db, "SELECT integrity_passed FROM (" + text.rstrip() + ") q") == "t"


@pytestmark_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("INSERT INTO fact_category_ownership VALUES ('virupa_drishti','ga_sensitive')", "already owned by a different asset"),
    ("UPDATE asset_registry SET target_floor = 1 WHERE asset_id='ga_strength'", "ga_strength count_sql narrowing refused"),
    ("UPDATE asset_registry SET target_floor = 7 WHERE asset_id='ga_condition'", "ga_condition count_sql re-declaration refused"),
    ("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural','deadbeef','{}'::jsonb)", "unrecognised active row"),
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '(g28)', '(zzz)') WHERE asset_id='ga_structural'", "lacks conjunct (g28)"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\n  AS integrity_passed' WHERE asset_id='ga_structural'", "anchor is not unique"),
])
def test_migration_refuses_unexpected_live_state(pg, sabotage, expect):
    db = _fresh_db(pg)
    _q(pg, db, sabotage)
    r = _psql(pg, db, file=M1219_PATH)
    assert r.returncode != 0 and expect in r.stderr, r.stderr


# ── the (a29) conjunct: it kills what (e27) lets through ────────────────────────────────────────

def _e27() -> str:
    body = M904.split("-- (e27) argala-offset full re-derivation", 1)[1].split("-- (f27)", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _a29() -> str:
    body = M1219.split("-- (a29)", 1)[1]
    body = body.split("AND NOT EXISTS (", 1)[1].split("$conj$", 1)[0]
    return "AND NOT EXISTS (" + body.rstrip()


BUILD = str(uuid.uuid4())


def _seed_cells(port, db, cells):
    """Sun in Capricorn (10), Moon in Aquarius (11); D1 argala cells for target Scorpio (8): offsets 2, 4, 5, 11
    read signs 9, 11, 12, 6, so only the 4th (Aquarius, Moon) is occupied. `cells` maps source sign -> (num, text)."""
    _q(port, db, f"""
      INSERT INTO chart_facts VALUES
       ('d1','{CANON}','a','{BUILD}','graha_dignity_per_varga','D1_SUN','dignity_state',NULL,NULL,'{{"varga":"D1","sign":"Capricorn"}}'),
       ('d2','{CANON}','a','{BUILD}','graha_dignity_per_varga','D1_MOON','dignity_state',NULL,NULL,'{{"varga":"D1","sign":"Aquarius"}}');
    """)
    for i, (src, off) in enumerate(((9, 2), (11, 4), (12, 5), (6, 11))):
        num, text = cells[src]
        n = "NULL" if num is None else str(num)
        t = "NULL" if text is None else f"'{text}'"
        _q(port, db, f"INSERT INTO chart_facts VALUES ('c{i}','{CANON}','a','{BUILD}','argala_natal_matrix','D1_SIGN_8',"
                     f"'from_sign_{src}_offset_{off}',{t},{n},NULL)")


def _violations(port, db, conjunct: str) -> int:
    return int(_q(port, db, "SELECT CASE WHEN (SELECT true " + conjunct + ") THEN 0 ELSE 1 END"))


GOOD = {9: (None, "no_occupant"), 11: (1.0, None), 12: (None, "no_occupant"), 6: (None, "no_occupant")}
MUTANTS = {
    "NULL on an occupied cell (the case (e27) passes)": {**GOOD, 11: (None, "no_occupant")},
    "NULL without the text on an occupied cell": {**GOOD, 11: (None, None)},
    "stale 1.0 on an empty cell (today's behaviour)": {**GOOD, 9: (1.0, None)},
    "empty cell NULL but marker missing": {**GOOD, 12: (None, None)},
    "empty cell carries the marker AND a score": {**GOOD, 6: (0.75, "no_occupant")},
    "occupied cell carries the marker": {**GOOD, 11: (1.0, "no_occupant")},
}


@pytestmark_pg
def test_a29_accepts_the_correct_cells_and_kills_every_mutant(pg):
    db = _fresh_db(pg)
    _seed_cells(pg, db, GOOD)
    assert _violations(pg, db, _a29()) == 0
    for name, cells in MUTANTS.items():
        d = _fresh_db(pg)
        _seed_cells(pg, d, cells)
        assert _violations(pg, d, _a29()) == 1, f"(a29) let this mutant through: {name}"


@pytestmark_pg
def test_the_old_conjunct_e27_is_vacuous_on_null_which_is_why_a29_exists(pg):
    d = _fresh_db(pg)
    _seed_cells(pg, d, MUTANTS["NULL on an occupied cell (the case (e27) passes)"])
    assert _violations(pg, d, _e27()) == 0          # (e27) passes the NULL on an occupied cell
    assert _violations(pg, d, _a29()) == 1          # (a29) fails it
    d2 = _fresh_db(pg)
    _seed_cells(pg, d2, {**GOOD, 11: (0.75, None)})  # a wrong non-NULL score is still (e27)'s job, not (a29)'s
    assert _violations(pg, d2, _e27()) == 1 and _violations(pg, d2, _a29()) == 0
