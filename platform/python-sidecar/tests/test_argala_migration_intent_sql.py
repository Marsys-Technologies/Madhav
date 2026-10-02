"""The real migration files 1219 and 1221, executed against a disposable Postgres.

The SQL is read from the migration files themselves (platform/migrations/1219_*.sql = block A, 1221_*.sql = block B);
the explanatory document 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1219_1221_INTENT_v1_0.md (v1.1) carries no SQL
copy, so there is nothing that can drift from the files. Static checks always run; the executed checks use
tests/pg_disposable.py (initdb into a temp dir, never the project database) and skip when no Postgres binaries exist.

Block A (1219): ownership (incl. the five panchanga categories leaving ga_structural), count_sql with no double claims
and no floor change, digest spec. Block B (1221): the integrity conjunct (a29), argala NULL <=> empty source sign.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402
from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

REPO = pathlib.Path(__file__).resolve().parents[3]
DOC = (REPO / "00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1219_1221_INTENT_v1_0.md").read_text(encoding="utf-8")
MIGRATIONS = REPO / "platform/migrations"
F1219 = "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql"
F1221 = "1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "argala_1219"
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")
M904 = (MIGRATIONS / "904_nirmana_l1_ga_structural_integrity_check_scope.sql").read_text(encoding="utf-8")


A = (MIGRATIONS / F1219).read_text(encoding="utf-8")   # block A
B = (MIGRATIONS / F1221).read_text(encoding="utf-8")   # block B
OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
FIVE = ["bhadra_flag", "chandra_bala_natal_baseline", "eclipse_proximity_natal", "panchaka_flag", "tara_bala_natal_baseline"]
SIX_WRITER_ONLY = {("ashtakavarga_bindu_contributor", "ga_strength"), ("graha_degree_flags", "ga_nakshatra"),
                   ("nakshatra_exchange", "ga_nakshatra"), ("esoteric_point_trisphuta", "ga_sensitive"),
                   ("esoteric_point_chatushphuta", "ga_sensitive"), ("esoteric_point_panchasphuta", "ga_sensitive")}
STRENGTH_LIVE = (FIXTURES / "ga_strength_count_sql.txt").read_text(encoding="utf-8")
CONDITION_LIVE = (FIXTURES / "ga_condition_count_sql.txt").read_text(encoding="utf-8")
OWNED_STRUCTURAL = set((FIXTURES / "owned_structural_2026-10-02.txt").read_text().split())   # the 64 rows read live, in the repo


def _code(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def _spec(text: str) -> dict:
    m = re.search(r"'(\{\"version\":\"nirmana-output-digest-spec-v1\".*?\})'::jsonb", text, re.S)
    assert m
    return json.loads(m.group(1))


def _pairs() -> list[tuple[str, str]]:
    block = A.split("INSERT INTO _own_1219 (fact_category, owning_asset_id) VALUES", 1)[1].split(";", 1)[0]
    return re.findall(r"\('([a-z0-9_]+)', '(ga_[a-z_]+)'\)", block)


def _write(tag: str, sql: str) -> pathlib.Path:
    f = pathlib.Path(tempfile.mkdtemp(prefix="intent_")) / f"{tag}.sql"
    f.write_text(sql, encoding="utf-8")
    return f


# ── static: block A ─────────────────────────────────────────────────────────────────────────────

def test_the_two_migration_files_exist_with_the_right_names_and_no_other_new_migration_number():
    assert sorted(p.name for p in MIGRATIONS.glob("1219_*")) == [F1219]
    assert sorted(p.name for p in MIGRATIONS.glob("1221_*")) == [F1221]
    # they are real migrations, not drafts: no draft/hold wording, normal runner owns the transaction, verified after
    for text in (A, B):
        assert "DRAFT, NOT APPLIED" not in text and "INTENDED TEXT" not in text and "owner hold" not in text
        flat = re.sub(r"\s*\n--\s*", " ", text)
        assert "real migration, applied through the normal runner" in flat and "platform/scripts/migrate.ts owns the transaction" in flat
        assert "VERIFIED by production structure" in flat and "Trap 103" in flat
    # the document is the explanation only: no SQL copy to drift from the files, and it points at both files
    assert "```sql" not in DOC and F1219 in DOC and F1221 in DOC
    # this change adds no migration number other than 1219 and 1221 (skipped when origin/main is not fetchable;
    # empty once the files are on main)
    r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", "origin/main...HEAD", "--", "platform/migrations"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode == 0:
        added = {pathlib.PurePosixPath(x).name for x in r.stdout.split()}
        assert added <= {F1219, F1221}, added


def test_914_sha_is_reproduced_by_the_real_digest_function_and_the_new_spec_is_old_plus_one_category():
    assert canonical_digest(_spec(M914)) == OLD_SHA
    old, new = _spec(M914), _spec(A)
    oc, nc = old["components"][0]["where_in"]["fact_category"], new["components"][0]["where_in"]["fact_category"]
    assert len(oc) == 81 and len(nc) == 82 and set(nc) - set(oc) == {"argala_graha_natal"} and set(oc) <= set(nc)
    old["components"][0]["where_in"]["fact_category"] = nc
    assert old == new and canonical_digest(new) == NEW_SHA
    assert A.count(NEW_SHA) >= 3 and OLD_SHA in A


def test_the_guard_md5s_are_the_live_count_sql_texts_read():
    assert hashlib.md5(STRENGTH_LIVE.encode()).hexdigest() in A
    assert hashlib.md5(CONDITION_LIVE.encode()).hexdigest() in A


def test_ownership_is_complete_self_contained_and_has_no_double_owner_for_the_panchanga_five():
    pairs = _pairs()
    assert ("argala_graha_natal", "ga_structural") in pairs and len(pairs) == len(set(pairs))
    structural = {c for c, a in pairs if a == "ga_structural"}
    spec_cats = set(_spec(M914)["components"][0]["where_in"]["fact_category"])
    assert len(OWNED_STRUCTURAL) == 64
    assert spec_cats <= (OWNED_STRUCTURAL | structural), "every category the structural writer emits must be owned"
    twelve = {"virupa_drishti", "karaka_web_per_varga", "significator_path", "panchadha_maitri", "conjunction_special_point",
              "nakshatra_lord_relationship", "tara_bala", "yoga_label", "kendradhipati_dosha", "upapada_lagna", "dosha_label",
              "nakshatra_co_tenancy"}
    assert twelve <= structural
    assert ("vimsopaka_bala_per_graha", "ga_structural") in pairs and ("graha_saptavargaja_bala_component", "ga_structural") in pairs
    assert not [p for p in pairs if p[0] in ("vimsopaka_bala_per_graha", "graha_saptavargaja_bala_component") and p[1] != "ga_structural"]
    assert all((c, "ga_panchanga") in pairs for c in FIVE)
    assert not (set(FIVE) & structural)                                   # the structural writer never emits them
    assert SIX_WRITER_ONLY <= set(pairs)                                  # emitted, no ownership row today
    assert "DELETE FROM fact_category_ownership" in A and "owning_asset_id = 'ga_structural'" in A


def test_scope_no_floors_no_integrity_in_block_a_and_no_transaction_statements():
    code = _code(A)
    assert not re.search(r"target_floor", code)
    assert "integrity_check_sql" not in code and "(a29)" not in code
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", A, re.M)
    assert "ga_condition_composite" in code                               # the composite part of ga_condition's count is kept
    new_strength = A.split("strength_new constant text := $cs$", 1)[1].split("$cs$;", 1)[0]
    assert "'%bhava_bala%'" not in new_strength and "saptavargaja" not in new_strength and "'%vimsopaka%'" not in new_strength
    new_condition = A.split("condition_new constant text := $cc$", 1)[1].split("$cc$;", 1)[0]
    assert "graha_yuddha" not in new_condition and "graha_avastha_%_per_varga" in new_condition


def test_the_category_in_the_spec_is_the_one_the_writer_emits():
    import ga_writers.ga_structural_writer as sut
    rows = sut._build_argala_graha_rows({"Mars": {"sign_num": 1}, "Sun": {"sign_num": 2}}, "D1", "c", "b", "a", "t", "e")
    assert {r["fact_category"] for r in rows} == {"argala_graha_natal"}


# ── static: block B ─────────────────────────────────────────────────────────────────────────────

def test_block_b_does_only_the_integrity_patch_and_states_the_ordering_hazard():
    code = _code(B)
    assert code.count("UPDATE asset_registry") == 1 and "SET integrity_check_sql" in code
    for other in ("count_sql", "target_floor", "fact_category_ownership", "asset_output_digest_specs"):
        assert other not in code
    assert "AS integrity_passed" in code and "(g28)" in code and not re.search(r"^\s*(BEGIN|COMMIT)\s*;", B, re.M)
    flat = re.sub(r"\s*\n--\s*", " ", B)
    assert "NAMED STEP of the S-L1" in flat and "IMMEDIATELY BEFORE the ga_structural launch" in flat
    assert "NEVER BEFORE the ga_structural writer deploy" in flat
    assert "ORDERING HAZARD" in flat and "OLD writer image" in flat and "NEVER applies before the ga_structural writer deploy" in flat
    assert "WITH or AFTER the writer deploy" not in flat                  # the earlier, weaker wording is gone
    assert "RUNNER CONSEQUENCE" in flat and "cannot enforce the rule above" in flat   # merge-timing rule is stated


def test_block_a_header_states_it_is_a_prerequisite_that_may_apply_independently_of_the_writer_deploy():
    flat = re.sub(r"\s*\n--\s*", " ", A)
    assert "HARD PREREQUISITE of the S-L1 ga_structural rebuild" in flat and "BEFORE that rebuild launches" in flat
    assert "MAY APPLY INDEPENDENTLY of it" in flat
    assert "with or after the writer deploy" not in flat


# ── executed: block A ───────────────────────────────────────────────────────────────────────────

SCHEMA_A = """
CREATE TABLE fact_category_ownership (fact_category text NOT NULL, owning_asset_id text NOT NULL,
  created_at timestamptz DEFAULT now(), PRIMARY KEY (fact_category, owning_asset_id));
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor integer, integrity_check_sql text);
CREATE TABLE asset_output_digest_specs (asset_id text NOT NULL, spec_sha256 text NOT NULL, spec jsonb NOT NULL,
  reviewed_at timestamptz, retired_at timestamptz, UNIQUE (asset_id, spec_sha256));
"""


def _fresh_a(port: int) -> str:
    db = new_db(port)
    q(port, db, SCHEMA_A)
    old_spec = json.dumps(_spec(M914)).replace("'", "''")
    q(port, db, f"""
      INSERT INTO fact_category_ownership VALUES ('bhava_bala_lord','ga_structural'), ('graha_avastha_lajjitadi','ga_condition'),
        {", ".join(f"('{c}','ga_structural')" for c in FIVE)};
      INSERT INTO asset_registry VALUES ('ga_strength', $a${STRENGTH_LIVE}$a$, 13621, 'strength-integrity'),
        ('ga_condition', $a${CONDITION_LIVE}$a$, 2880, 'condition-integrity'), ('ga_structural', 'x', 98446, 'structural-integrity');
      INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural', '{OLD_SHA}', '{old_spec}'::jsonb);
    """)
    return db


@requires_pg
def test_block_a_applies_every_part_touches_no_floor_or_integrity_and_is_idempotent(pg):
    db = _fresh_a(pg)
    floors_integrity = "SELECT string_agg(asset_id || target_floor || integrity_check_sql, ',' ORDER BY asset_id) FROM asset_registry"
    before = q(pg, db, floors_integrity)
    f = _write("a", A)
    r = psql(pg, db, file=f)
    assert r.returncode == 0, r.stderr
    pairs = _pairs()
    assert int(q(pg, db, "SELECT count(*) FROM fact_category_ownership")) == 7 - 5 + len(pairs)
    assert q(pg, db, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='argala_graha_natal' AND owning_asset_id='ga_structural'") == "1"
    assert q(pg, db, "SELECT string_agg(DISTINCT owning_asset_id, ',') FROM fact_category_ownership WHERE fact_category = ANY(ARRAY['" + "','".join(FIVE) + "'])") == "ga_panchanga"
    strength = q(pg, db, "SELECT count_sql FROM asset_registry WHERE asset_id='ga_strength'")
    for gone in ("%bhava_bala%", "%vimsopaka%", "saptavargaja"):
        assert gone not in strength
    for kept in ("house_bhava_bala_%", "graha_vimsopaka_%", "ashtakavarga_%", "graha_shadbala_%", "graha_%_bala_per_varga"):
        assert kept in strength
    condition = q(pg, db, "SELECT count_sql FROM asset_registry WHERE asset_id='ga_condition'")
    assert "graha_yuddha" not in condition and "ga_condition_composite" in condition and "graha_avastha_%_per_varga" in condition
    assert q(pg, db, floors_integrity) == before                               # no floor, no integrity text moved
    assert q(pg, db, f"SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NULL AND spec_sha256='{NEW_SHA}'") == "1"
    assert q(pg, db, f"SELECT retired_at IS NOT NULL FROM asset_output_digest_specs WHERE spec_sha256='{OLD_SHA}'") == "t"
    fp = "SELECT (SELECT md5(string_agg(count_sql, '' ORDER BY asset_id)) FROM asset_registry) || (SELECT count(*) FROM fact_category_ownership)"
    first = q(pg, db, fp)
    assert psql(pg, db, file=f).returncode == 0
    assert q(pg, db, fp) == first


@requires_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("INSERT INTO fact_category_ownership VALUES ('virupa_drishti','ga_sensitive')", "already owned by a different asset"),
    ("UPDATE asset_registry SET count_sql = count_sql || ' ' WHERE asset_id='ga_strength'", "ga_strength count_sql narrowing refused"),
    ("UPDATE asset_registry SET count_sql = 'SELECT 1' WHERE asset_id='ga_condition'", "ga_condition count_sql re-declaration refused"),
    ("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural','deadbeef','{}'::jsonb)", "unrecognised active row"),
])
def test_block_a_refuses_unexpected_live_state(pg, sabotage, expect):
    db = _fresh_a(pg)
    q(pg, db, sabotage)
    r = psql(pg, db, file=_write("a", A))
    assert r.returncode != 0 and expect in r.stderr, r.stderr


# ── executed: block B ───────────────────────────────────────────────────────────────────────────

STANDIN = "SELECT\n  (TRUE)\n  -- (g28) stand-in tail\n  AND NOT EXISTS (SELECT 1 FROM chart_facts WHERE false)\n  AS integrity_passed\n\n"
SCHEMA_B = """
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor integer, integrity_check_sql text);
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, build_id uuid,
  fact_category text, fact_subject text, fact_key text, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb);
"""
BUILD = str(uuid.uuid4())


def _a29() -> str:
    body = B.split("conjunct constant text := $conj$", 1)[1].split("$conj$", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _e27() -> str:
    body = M904.split("-- (e27) argala-offset full re-derivation", 1)[1].split("-- (f27)", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _fresh_b(port: int) -> str:
    db = new_db(port)
    q(port, db, SCHEMA_B)
    q(port, db, f"INSERT INTO asset_registry VALUES ('ga_structural', 'x', 98446, $a${STANDIN}$a$), ('ga_strength', 'y', 1, 'keep')")
    return db


@requires_pg
def test_block_b_applies_once_touches_only_integrity_text_and_is_idempotent(pg):
    db = _fresh_b(pg)
    other = "SELECT count_sql, target_floor FROM asset_registry ORDER BY asset_id"
    other_before = q(pg, db, other)
    f = _write("b", B)
    assert psql(pg, db, file=f).returncode == 0
    text = q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_structural'")
    assert text.count("(a29)") >= 1 and text.count("AS integrity_passed") == 1 and "(g28)" in text
    assert q(pg, db, other) == other_before
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ga_strength'") == "keep"
    once = q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'")
    assert psql(pg, db, file=f).returncode == 0
    assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == once
    assert q(pg, db, "SELECT integrity_passed FROM (" + text.rstrip() + ") z") == "t"


@requires_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '(g28)', '(zzz)') WHERE asset_id='ga_structural'", "lacks conjunct (g28)"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n  AS integrity_passed' WHERE asset_id='ga_structural'", "anchor is not unique"),
    ("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='ga_structural'", "no integrity_check_sql"),
])
def test_block_b_refuses_unexpected_live_state(pg, sabotage, expect):
    db = _fresh_b(pg)
    q(pg, db, sabotage)
    r = psql(pg, db, file=_write("b", B))
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
    q(pg, db, SCHEMA_B)
    _seed(pg, db, GOOD)
    assert _violations(pg, db, _a29()) == 0
    for name, cells in MUTANTS.items():
        d = new_db(pg)
        q(pg, d, SCHEMA_B)
        _seed(pg, d, cells)
        assert _violations(pg, d, _a29()) == 1, f"(a29) let this mutant through: {name}"


@requires_pg
def test_the_old_conjunct_e27_is_vacuous_on_null_which_is_why_a29_exists(pg):
    d = new_db(pg)
    q(pg, d, SCHEMA_B)
    _seed(pg, d, MUTANTS["NULL on an occupied cell (the case (e27) passes)"])
    assert _violations(pg, d, _e27()) == 0
    assert _violations(pg, d, _a29()) == 1
    d2 = new_db(pg)
    q(pg, d2, SCHEMA_B)
    _seed(pg, d2, {**GOOD, 11: (0.75, None)})
    assert _violations(pg, d2, _e27()) == 1 and _violations(pg, d2, _a29()) == 0
