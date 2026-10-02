"""The real migration file 1219, executed against a disposable Postgres.

The SQL is read from the migration file itself (platform/migrations/1219_*.sql); the explanatory document
00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1219_INTENT_v1_0.md carries no SQL copy, so there is nothing that can
drift from the file. Static checks always run; the executed checks use tests/pg_disposable.py (initdb into a temp
dir, never the project database) and skip when no Postgres binaries exist. (Migration 1221, the a29 integrity
conjunct, is a separate held PR with its own test file.)

1219: ownership (incl. the five panchanga categories leaving ga_structural), count_sql with no double claims and no
floor change, digest spec, lock_timeout.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import warnings

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402
from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, q, pg, requires_pg  # noqa: E402,F401


if not HAVE_PG:
    # LOUD, never failing: a skip must be visible in the pytest warnings summary. PR rule: while these DB-backed tests
    # are skipped here they have NOT run in this environment; the PR must keep saying they were run locally on PG 15 and
    # 17, and must not claim CI exercised them.
    warnings.warn(
        f"{pathlib.Path(__file__).name}: DB-backed migration tests are SKIPPED, not passed. Reason: {PG_SKIP_REASON}. "
        "PR rule: say 'run locally on PG 15 and 17' and do not claim CI ran them.",
        UserWarning, stacklevel=1)

REPO = pathlib.Path(__file__).resolve().parents[3]
DOC = (REPO / "00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1219_INTENT_v1_0.md").read_text(encoding="utf-8")
MIGRATIONS = REPO / "platform/migrations"
F1219 = "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "argala_1219"
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")

A = (MIGRATIONS / F1219).read_text(encoding="utf-8")
OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"
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


# ── static ─────────────────────────────────────────────────────────────────────────────

def test_the_migration_file_exists_with_the_right_name_and_this_change_adds_no_other_migration_number():
    assert sorted(p.name for p in MIGRATIONS.glob("1219_*")) == [F1219]
    # a real migration, not a draft: no draft/hold wording, the normal runner owns the transaction, verified after
    assert "DRAFT, NOT APPLIED" not in A and "INTENDED TEXT" not in A and "owner hold" not in A
    flat = re.sub(r"\s*\n--\s*", " ", A)
    assert "real migration, applied through the normal runner" in flat and "platform/scripts/migrate.ts owns the transaction" in flat
    assert "VERIFIED by production structure" in flat and "Trap 103" in flat
    # 1221 is a separate, held PR: it is not carried here
    assert "SEPARATE, HELD PR" in flat
    # the document is the explanation only: no SQL copy to drift from the file, and it points at the file
    assert "```sql" not in DOC and F1219 in DOC
    # this change adds no migration number other than 1219 (skipped when origin/main is not fetchable;
    # empty once the file is on main)
    try:
        r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", "origin/main...HEAD", "--", "platform/migrations"],
                           cwd=REPO, capture_output=True, text=True)
    except OSError:                                                       # no git binary: the check is skipped
        r = None
    if r is not None and r.returncode == 0:
        added = {pathlib.PurePosixPath(x).name for x in r.stdout.split()}
        assert added <= {F1219}, added


def test_lock_timeout_is_the_first_statement_and_fails_fast():
    code = [ln.strip() for ln in _code(A).splitlines() if ln.strip()]
    assert code[0] == "SET LOCAL lock_timeout = '5s';"
    flat = re.sub(r"\s*\n--\s*", " ", A)
    assert "must fail fast, not hang a shared deploy" in flat


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


def test_scope_no_floors_no_integrity_and_no_transaction_statements():
    code = _code(A)
    assert not re.search(r"target_floor", code)
    assert "integrity_check_sql" not in code and "(a29)" not in code
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", A, re.M)
    assert "ga_condition_composite" in code                               # the composite part of ga_condition's count is kept
    new_strength = A.split("strength_new constant text := $cs$", 1)[1].split("$cs$;", 1)[0]
    assert "'%bhava_bala%'" not in new_strength and "saptavargaja" not in new_strength and "'%vimsopaka%'" not in new_strength
    assert "<> 'ashtakavarga_anubindu'" in new_strength                   # ashtakavarga_anubindu is ga_structural's
    new_condition = A.split("condition_new constant text := $cc$", 1)[1].split("$cc$;", 1)[0]
    assert "graha_yuddha" not in new_condition and "graha_avastha_%_per_varga" in new_condition


def test_the_category_in_the_spec_is_the_one_the_writer_emits():
    import ga_writers.ga_structural_writer as sut
    rows = sut._build_argala_graha_rows({"Mars": {"sign_num": 1}, "Sun": {"sign_num": 2}}, "D1", "c", "b", "a", "t", "e")
    assert {r["fact_category"] for r in rows} == {"argala_graha_natal"}


def test_block_a_header_states_it_is_a_prerequisite_that_may_apply_independently_of_the_writer_deploy():
    flat = re.sub(r"\s*\n--\s*", " ", A)
    assert "HARD PREREQUISITE of the S-L1 ga_structural rebuild" in flat and "BEFORE that rebuild launches" in flat
    assert "MAY APPLY INDEPENDENTLY of it" in flat
    assert "with or after the writer deploy" not in flat


# ── executed ───────────────────────────────────────────────────────────────────────────

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


@requires_pg
def test_block_a_applies_in_one_transaction_with_lock_timeout_and_a_refusal_rolls_everything_back(pg):
    db = _fresh_a(pg)
    ok = psql(pg, db, file=_write("a", A), single_transaction=True)
    assert ok.returncode == 0 and "WARNING" not in ok.stderr, ok.stderr          # SET LOCAL is inside the transaction
    assert q(pg, db, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='argala_graha_natal'") == "1"
    db2 = _fresh_a(pg)
    q(pg, db2, "UPDATE asset_registry SET count_sql = 'SELECT 1' WHERE asset_id='ga_condition'")   # part 2 refuses
    r = psql(pg, db2, file=_write("a", A), single_transaction=True)
    assert r.returncode != 0 and "ga_condition count_sql re-declaration refused" in r.stderr
    # runner-shaped rollback: part 1 (ownership) did not survive the refusal in part 2
    assert q(pg, db2, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='argala_graha_natal'") == "0"
    assert q(pg, db2, "SELECT count(*) FROM fact_category_ownership WHERE owning_asset_id='ga_panchanga'") == "0"


CLAIMS_SQL = """
CREATE TABLE chart_facts (chart_id uuid, fact_category text);
CREATE TABLE ga_condition_composite (chart_id uuid);
CREATE TABLE claims (fact_category text, asset_id text);
DO $$
DECLARE r record; a record; n integer; cid uuid;
BEGIN
  FOR r IN SELECT DISTINCT fact_category FROM (SELECT unnest(string_to_array(%(cats)s, ',')) AS fact_category) u LOOP
    cid := gen_random_uuid();
    INSERT INTO chart_facts VALUES (cid, r.fact_category);
    FOR a IN SELECT asset_id, count_sql FROM asset_registry WHERE asset_id IN ('ga_strength', 'ga_condition') LOOP
      EXECUTE a.count_sql INTO n USING cid;
      IF n > 0 THEN INSERT INTO claims VALUES (r.fact_category, a.asset_id); END IF;
    END LOOP;
  END LOOP;
END $$;
"""


def _claimants(port: int, a_sql: str, extra_cats: list[str]) -> dict[str, set[str]]:
    """Apply a_sql, then evaluate the two narrowed count_sql predicates category by category (one chart per category) and
    merge with the ownership rows: category -> every asset that would count it."""
    db = _fresh_a(port)
    assert psql(port, db, file=_write("a", a_sql)).returncode == 0
    cats = sorted({c for c, _ in _pairs()} | set(extra_cats))
    q(port, db, CLAIMS_SQL % {"cats": "'" + ",".join(cats) + "'"})
    out: dict[str, set[str]] = {c: set() for c in cats}
    for line in q(port, db, "SELECT fact_category || '|' || asset_id FROM claims").splitlines():
        c, a = line.split("|")
        out[c].add(a)
    for line in q(port, db, "SELECT fact_category || '|' || owning_asset_id FROM fact_category_ownership").splitlines():
        c, a = line.split("|")
        out.setdefault(c, set()).add(a)
    return out


@requires_pg
def test_no_category_is_counted_by_two_assets_after_1219_including_ashtakavarga_anubindu(pg):
    extra = ["ashtakavarga_anubindu", "graha_avastha_sayanadi", "graha_avastha_lajjitadi", "graha_yuddha",
             "bhava_bala_lord", "graha_vimsopaka_shadvarga"] + FIVE
    claims = _claimants(pg, A, extra)
    assert {c: a for c, a in claims.items() if len(a) != 1} == {}, "a category is counted by two assets"
    assert claims["ashtakavarga_anubindu"] == {"ga_structural"}
    # the other ashtakavarga_* categories the clause matched stay ga_strength's, and are still counted by it
    for c in ("ashtakavarga_bindu", "ashtakavarga_bindu_per_varga", "ashtakavarga_pinda_sarva", "ashtakavarga_bindu_contributor"):
        assert claims[c] == {"ga_strength"}, c
    assert claims["graha_yuddha"] == {"ga_structural"} and claims["bhava_bala_lord"] == {"ga_structural"}


@requires_pg
def test_the_double_claim_check_has_teeth_it_catches_anubindu_if_the_exclusion_is_removed(pg):
    mutant = A.replace("(fact_category LIKE 'ashtakavarga_%' AND fact_category <> 'ashtakavarga_anubindu')",
                       "fact_category LIKE 'ashtakavarga_%'")
    assert mutant != A
    claims = _claimants(pg, mutant, ["ashtakavarga_anubindu"])
    assert claims["ashtakavarga_anubindu"] == {"ga_structural", "ga_strength"}
