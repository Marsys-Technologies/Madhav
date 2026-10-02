"""The real migration file 1221 (the a29 integrity conjunct on ga_structural), executed against a disposable Postgres.

HELD migration: it merges only in the S-L1 window, after the ga_structural writer image is deployed. The SQL is read from the
migration file itself (platform/migrations/1221_*.sql); 00_ARCHITECTURE/briefs/suvarna/exec/MIGRATION_1221_A29_INTENT_v1_0.md
carries no SQL copy. Static checks always run; the executed checks use tests/pg_disposable.py (initdb into a temp dir,
never the project database) and skip when no Postgres binaries exist. Self-contained: it needs no other migration of
the argala change (migration 1219 is a separate PR with its own test file).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile
import warnings
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

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

B = (MIGRATIONS / F1221).read_text(encoding="utf-8")
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


def _code(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


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
    assert "HELD" in flat and "ONLY in the S-L1 window" in flat and "LC-1 digest equality" in flat
    assert "0 ACTIVE RUNS AT APPLY" in flat and "Merge = apply" in flat


# ── executed ───────────────────────────────────────────────────────────────────────────

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


@requires_pg
def test_block_b_applies_in_one_transaction_with_lock_timeout_and_a_refusal_changes_nothing(pg):
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
