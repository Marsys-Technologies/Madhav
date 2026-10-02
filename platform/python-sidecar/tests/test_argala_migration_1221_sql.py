"""The real migration file 1221 (the a29 integrity conjunct on ga_structural AND the ga_structural output-digest spec swap),
executed against a disposable Postgres.

HELD migration: it merges only in the S-L1 window, after the ga_structural writer image is deployed. The SQL is read from the
migration file itself (platform/migrations/1221_*.sql); 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1221_A29_INTENT_v1_0.md
carries no SQL copy. Static checks always run; the executed checks use tests/pg_disposable.py (initdb into a temp dir,
never the project database) and skip when no Postgres binaries exist. Self-contained: it needs no other migration of
the argala change (migration 1219 is a separate PR with its own test file).
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
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.output_digest import _validate_spec, compute_output_digest  # noqa: E402
from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402
from tests import argala_registry_fixture as reg  # noqa: E402
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
DOC = (REPO / "00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1221_A29_INTENT_v1_0.md").read_text(encoding="utf-8")
MIGRATIONS = REPO / "platform/migrations"
F1221 = "1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql"
M904 = (MIGRATIONS / "904_nirmana_l1_ga_structural_integrity_check_scope.sql").read_text(encoding="utf-8")
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")
OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"

B = (MIGRATIONS / F1221).read_text(encoding="utf-8")
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


def _code(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def _spec(text: str) -> dict:
    m = re.search(r"'(\{\"version\":\"nirmana-output-digest-spec-v1\".*?\})'::jsonb", text, re.S)
    assert m
    return json.loads(m.group(1))


def _write(tag: str, sql: str) -> pathlib.Path:
    f = pathlib.Path(tempfile.mkdtemp(prefix="intent_")) / f"{tag}.sql"
    f.write_text(sql, encoding="utf-8")
    return f


# ── static ──────────────────────────────────────────────────────────────────────────────────────

def test_the_migration_file_exists_with_the_right_name_and_this_change_adds_no_other_migration_number():
    assert sorted(p.name for p in MIGRATIONS.glob("1221_*")) == [F1221]
    assert "DRAFT, NOT APPLIED" not in B and "INTENDED TEXT" not in B and "owner hold" not in B
    flat = re.sub(r"\s*\n--\s*", " ", B)
    assert "real migration, applied through the normal runner" in flat and "platform/scripts/migrate.ts owns the transaction" in flat
    assert "VERIFIED by production structure" in flat and "Trap 103" in flat
    assert "```sql" not in DOC and F1221 in DOC
    try:
        r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", "origin/main...HEAD", "--", "platform/migrations"],
                           cwd=REPO, capture_output=True, text=True)
    except OSError:                                                       # no git binary: the check is skipped
        r = None
    if r is not None and r.returncode == 0:
        added = {pathlib.PurePosixPath(x).name for x in r.stdout.split()}
        assert added <= {F1221}, added


def test_lock_timeout_is_the_first_statement_and_fails_fast():
    code = [ln.strip() for ln in _code(B).splitlines() if ln.strip()]
    assert code[0] == "SET LOCAL lock_timeout = '5s';"
    flat = re.sub(r"\s*\n--\s*", " ", B)
    assert "must fail fast, not hang a shared deploy" in flat


def test_1221_does_only_the_integrity_patch_and_the_spec_swap_and_states_the_ordering_hazard():
    code = _code(B)
    assert code.count("UPDATE asset_registry") == 1 and "SET integrity_check_sql" in code
    assert code.count("UPDATE asset_output_digest_specs") == 1 and "DELETE" not in code.upper().replace("DETERMINISTIC", "")   # retire, never delete
    for other in ("count_sql", "target_floor", "fact_category_ownership"):
        assert other not in code
    assert code.index("SET integrity_check_sql") < code.index("INSERT INTO asset_output_digest_specs")   # the swap comes AFTER a29
    assert "AS integrity_passed" in code and "(g28)" in code and not re.search(r"^\s*(BEGIN|COMMIT)\s*;", B, re.M)
    flat = re.sub(r"\s*\n--\s*", " ", B)
    assert "NAMED STEP of the S-L1" in flat and "IMMEDIATELY BEFORE the ga_structural launch" in flat
    assert "NEVER BEFORE the ga_structural writer deploy" in flat
    assert "ORDERING HAZARD" in flat and "OLD writer image" in flat and "NEVER applies before the ga_structural writer deploy" in flat
    assert "WITH or AFTER the writer deploy" not in flat                  # the earlier, weaker wording is gone
    assert "RUNNER CONSEQUENCE" in flat and "cannot enforce the rule above" in flat   # merge-timing rule is stated
    assert "HELD" in flat and "ONLY in the S-L1 window" in flat and "LC-1 digest equality" in flat
    assert "0 ACTIVE RUNS AT APPLY" in flat and "Merge = apply" in flat
    # the serving statement (approved text) and the gap direction, as written in the header
    assert ("SERVING EFFECT AT APPLY: ga_structural freshness stale on every chart (a29 UPDATE OF integrity_check_sql) AND its "
            "receipts read receipt_spec_retired until rebuilt; degraded set at W1 = ga_structural (and with 1222/1223/1226: "
            "ga_vargas, ga_dashas, ga_yoga); all rebuilt in the window") in flat
    assert "THE GAP BEFORE THIS FILE" in flat and "the OLD 81-category spec still ACTIVE" in flat
    assert "the build SUCCEEDS" in flat and "SILENT coverage gap" in flat and "not a loud failure" in flat
    assert "does NOT contain argala_graha_natal" in flat and "reads receipt_spec_retired anyway" in flat


def test_the_spec_swap_reproduces_both_shas_is_old_plus_one_sorted_unique_category_and_loads_through_the_real_validator():
    assert canonical_digest(_spec(M914)) == OLD_SHA                         # the real digest function reproduces 914's stored sha
    old, new = _spec(M914), _spec(B)
    oc, nc = old["components"][0]["where_in"]["fact_category"], new["components"][0]["where_in"]["fact_category"]
    assert len(oc) == 81 and len(nc) == 82 and set(nc) - set(oc) == {"argala_graha_natal"} and set(oc) <= set(nc)
    assert nc == sorted(nc) and len(set(nc)) == len(nc)                     # 82 categories sorted and unique
    old["components"][0]["where_in"]["fact_category"] = nc
    assert old == new and canonical_digest(new) == NEW_SHA                  # old + exactly one category = the new spec
    assert B.count(NEW_SHA) >= 3 and OLD_SHA in B
    _validate_spec("ga_structural", _spec(B), NEW_SHA)                      # the real output_digest validator accepts it


# ── executed ───────────────────────────────────────────────────────────────────────────

STANDIN = "SELECT\n  (TRUE)\n  -- (g28) stand-in tail\n  AND NOT EXISTS (SELECT 1 FROM chart_facts WHERE false)\n  AS integrity_passed\n\n"
SCHEMA_B = """
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


ASSETS = ["ga_structural", "ga_strength", "ga_vargas"]


def _fresh_b(port: int) -> str:
    """The real trigger and serving tables, a fresh asset_freshness row per asset, the live ga_structural spec (migration
    914's) active with a receipt on it, a stand-in integrity text carrying (g28) and the single anchor."""
    db = new_db(port)
    q(port, db, SCHEMA_B)
    reg.install(port, db)
    old_spec = json.dumps(_spec(M914)).replace("'", "''")
    q(port, db, f"""
      INSERT INTO asset_registry (asset_id, count_sql, target_floor, integrity_check_sql, is_active) VALUES
        ('ga_structural', 'x', 98446, $a${STANDIN}$a$, true), ('ga_strength', 'y', 1, 'keep', true), ('ga_vargas', 'z', 2, 'v', true);
      INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec, reviewed_at)
        VALUES ('ga_structural', '{OLD_SHA}', '{old_spec}'::jsonb, '2026-09-01T00:00:00Z');
      INSERT INTO asset_provenance_receipts (asset_id, scope_key, partition_key, receipt_version, receipt_state, output_digest_spec_sha256)
        VALUES ('ga_structural', 'chart', 'canonical', 'v1', 'proven', '{OLD_SHA}');
    """)
    reg.seed_fresh(port, db, ASSETS)
    return db


SPEC_ACTIVE = ("SELECT count(*) FROM asset_provenance_receipts r WHERE EXISTS (SELECT 1 FROM asset_output_digest_specs s "
               "WHERE s.asset_id = r.asset_id AND s.spec_sha256 = r.output_digest_spec_sha256 AND s.retired_at IS NULL)")


@requires_pg
def test_1221_applies_once_touches_only_integrity_text_and_the_spec_and_is_idempotent(pg):
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
    assert q(pg, db, "SELECT string_agg(spec_sha256 || ':' || (retired_at IS NULL)::text, ',' ORDER BY spec_sha256) FROM asset_output_digest_specs") \
        == f"{OLD_SHA}:false,{NEW_SHA}:true"                                # old retired (not deleted), new active, idempotent
    assert q(pg, db, "SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NULL") == "1"


@requires_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '(g28)', '(zzz)') WHERE asset_id='ga_structural'", "lacks conjunct (g28)"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || E'\\n  AS integrity_passed' WHERE asset_id='ga_structural'", "anchor is not unique"),
    ("UPDATE asset_registry SET integrity_check_sql = NULL WHERE asset_id='ga_structural'", "no integrity_check_sql"),
    (f"UPDATE asset_output_digest_specs SET retired_at = now() WHERE spec_sha256 = '{OLD_SHA}'; "
     "INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural', repeat('c', 64), '{}'::jsonb)",
     "unrecognised active row"),
])
def test_1221_refuses_unexpected_live_state(pg, sabotage, expect):
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


@requires_pg
def test_1221_applies_in_one_transaction_with_lock_timeout_and_a_refusal_changes_nothing(pg):
    db = _fresh_b(pg)
    ok = psql(pg, db, file=_write("b", B), single_transaction=True)
    assert ok.returncode == 0 and "WARNING" not in ok.stderr, ok.stderr          # SET LOCAL is inside the transaction
    assert q(pg, db, "SELECT position('(a29)' in integrity_check_sql) > 0 FROM asset_registry WHERE asset_id='ga_structural'") == "t"
    db2 = _fresh_b(pg)
    q(pg, db2, "UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '(g28)', '(zzz)') WHERE asset_id='ga_structural'")
    before = q(pg, db2, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'")
    r = psql(pg, db2, file=_write("b", B), single_transaction=True)
    assert r.returncode != 0 and "lacks conjunct (g28)" in r.stderr
    assert q(pg, db2, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == before
    # the refusal sits in part 2 (the spec swap) AFTER a29 patched the text: the runner-shaped transaction rolls both back
    db3 = _fresh_b(pg)
    q(pg, db3, f"UPDATE asset_output_digest_specs SET retired_at = now() WHERE spec_sha256 = '{OLD_SHA}'; "
               "INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural', repeat('c', 64), '{}'::jsonb)")
    text_before = q(pg, db3, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'")
    fresh_before = reg.freshness_snapshot(pg, db3)
    r3 = psql(pg, db3, file=_write("b", B), single_transaction=True)
    assert r3.returncode != 0 and "unrecognised active row" in r3.stderr
    assert q(pg, db3, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == text_before
    assert reg.freshness_snapshot(pg, db3) == fresh_before                 # the trigger's stale rolled back with it


# ── the combined serving effect (the REAL trigger function body and trigger definition, read from the live database) ───

@requires_pg
def test_the_combined_effect_ga_structural_freshness_stale_and_its_receipt_spec_retired_nothing_else_moves(pg):
    db = _fresh_b(pg)
    fresh_before = reg.freshness_snapshot(pg, db)
    assert q(pg, db, SPEC_ACTIVE) == "1"                                    # before: the receipt's spec is active (served as resolved)
    r = psql(pg, db, file=_write("b", B), single_transaction=True)          # the migrate.ts shape
    assert r.returncode == 0, r.stderr
    states = dict(line.split("|") for line in q(pg, db, "SELECT asset_id || '|' || freshness_state || ':' || reasons::text FROM asset_freshness").splitlines())
    assert states["ga_structural"] == 'stale:["registry_changed"]'          # a29: UPDATE OF integrity_check_sql fired the trigger
    assert states["ga_strength"] == "fresh:[]" and states["ga_vargas"] == "fresh:[]"   # no other asset is touched
    assert q(pg, db, SPEC_ACTIVE) == "0"                                    # the swap: the old-spec receipt now reads receipt_spec_retired
    assert q(pg, db, "SELECT spec_sha256 FROM asset_output_digest_specs WHERE asset_id = 'ga_structural' AND retired_at IS NULL") == NEW_SHA
    assert reg.freshness_snapshot(pg, db) != fresh_before
    # control: without the swap (a29 alone) the receipt would still read as resolved on its spec: the swap is the only retirement
    db2 = _fresh_b(pg)
    only_a29 = B[:B.index("-- ── 2. ga_structural output-digest spec")]
    assert psql(pg, db2, file=_write("a29", only_a29), single_transaction=True).returncode == 0
    assert q(pg, db2, SPEC_ACTIVE) == "1" and q(pg, db2, "SELECT freshness_state FROM asset_freshness WHERE asset_id = 'ga_structural'") == "stale"


# ── the gap BEFORE this file: old 81-category spec active, the new writer emitting argala_graha_natal ───

CHART_FACTS_REAL = """
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text,
  fact_key text, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb, unit text, citation_ref text,
  citation_human text, source_calculation text, verification_pass_status text, engine_version text, salience_formula_ver text,
  tolerance_arcsec numeric, near_sign_boundary_flag boolean, near_nakshatra_boundary_flag boolean, vargottama_flag_at_point boolean,
  formula_provenance_text text, cross_ayanamsha_divergence_arcsec numeric, formula_id text);
"""


def _digest(port: int, db: str) -> tuple[str, str]:
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=db, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            return compute_output_digest(cur, asset_id="ga_structural")


def _fact(i: int, category: str) -> str:
    return (f"INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_num) "
            f"VALUES ('f{i}', '{CANON}', 'a', '{category}', 'D1_MARS', 'k{i}', {i})")


@requires_pg
def test_the_gap_with_the_old_spec_active_argala_rows_do_not_move_the_digest_and_the_build_would_not_fail(pg):
    """The real compute_output_digest (as asset_runner calls it) on a real cursor: with the OLD spec active, rows of a category
    outside where_in (argala_graha_natal) leave the digest byte-identical: a silent coverage gap, no error. After 1221 the same
    rows move it."""
    db = _fresh_b(pg)
    q(pg, db, "DROP TABLE chart_facts")
    q(pg, db, CHART_FACTS_REAL)
    q(pg, db, _fact(1, "yoga_label"))                                       # a category the old spec covers
    d_old, sha_old = _digest(pg, db)                                        # asset_runner.py:1385
    assert sha_old == OLD_SHA and d_old
    q(pg, db, _fact(2, "argala_graha_natal"))                               # the new writer's rows, outside the old where_in
    q(pg, db, _fact(3, "argala_graha_natal"))
    assert _digest(pg, db) == (d_old, OLD_SHA)                              # no failure, no movement: the silent gap
    q(pg, db, _fact(4, "yoga_label"))
    assert _digest(pg, db)[0] != d_old                                      # control: a covered category does move it
    # after 1221: the swapped-in spec covers argala_graha_natal, so its rows now move the digest
    assert psql(pg, db, file=_write("b", B), single_transaction=True).returncode == 0
    d_new, sha_new = _digest(pg, db)
    assert sha_new == NEW_SHA
    q(pg, db, _fact(5, "argala_graha_natal"))
    assert _digest(pg, db)[0] != d_new
