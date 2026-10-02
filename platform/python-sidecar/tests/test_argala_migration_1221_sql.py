"""The real migration file 1221 (the a29 integrity conjunct on ga_structural, the corrections of its (bb), (c9) and (uu2) conjuncts,
AND the ga_structural output-digest spec swap), executed against a disposable Postgres.

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

# The two live conjuncts (read 2026-10-02 as suvarna_reader from asset_registry.integrity_check_sql of ga_structural, md5 of the whole
# text bb9803524a61427e7f4f179a59911e33), verbatim: comment plus SQL. The migration must replace exactly these.
OLD_BB = r'''  -- (bb) value_jsonb.orb_strength must equal the writer's own per-type formula: 1.0 for yamaya
  -- (exact-degree case); 0.1 for manaau (the fixed "denial" weight); for ithasala/eesarpha,
  -- round(greatest(0, 1 - orb_deg/deeptamsa_sum_deg), 4) -- a genuine cross-field re-derivation
  -- combining two already-stored fields into a third, not a bare restatement. 0/76 violations
  -- live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'aspect_tajik'
      AND (fact_value_jsonb->>'orb_strength')::numeric <>
        CASE fact_key
          WHEN 'yamaya' THEN 1.0
          WHEN 'manaau' THEN 0.1
          ELSE round(
            GREATEST(0.0, 1.0 -
              (fact_value_jsonb->>'orb_deg')::numeric / (fact_value_jsonb->>'deeptamsa_sum_deg')::numeric
            ), 4
          )
        END
  )
'''
OLD_C9 = r'''  -- (c9) composite_strength domain: must be one of the seven achievable values given the
  -- formula's four dignity tiers x three house tiers. 0/450 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'karakatva_strength_per_significance' AND fact_key = 'composite_strength'
      AND fact_value_num NOT IN (0.375, 0.5, 0.625, 0.75, 0.8125, 0.9375, 1.0)
  )
'''
OLD_UU2 = r'''  -- (uu2) chandra_bala_natal_baseline.classification must equal the full re-derivation of the
  -- writer's own formula: transit sign_id is parsed from fact_subject's
  -- "TRANSIT_SIGN_{SANSKRIT_NAME}" suffix via the standard Sanskrit zodiac name table;
  -- birth_nak_id is sourced from panchanga_nakshatra_moon.number for the same chart/ayanamsha --
  -- the same authoritative birth-nakshatra reference already used by tara_bala_natal_baseline
  -- (migration 782) and panchaka_flag (migration 755). Per D-L1-55, a +120 (10*12) margin is
  -- added before the modulo, guaranteeing a positive dividend without changing the result
  -- mod 12. 0/180 violations live.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_facts n ON n.chart_id = a.chart_id AND n.ayanamsha_id = a.ayanamsha_id
      AND n.fact_category = 'panchanga_nakshatra_moon' AND n.fact_subject = 'NAKSHATRA_MOON_BIRTH'
      AND n.fact_key = 'number'
    WHERE a.fact_category = 'chandra_bala_natal_baseline' AND a.fact_key = 'classification'
      AND a.fact_value_text <> (
        CASE (
          (
            (
              (CASE substring(a.fact_subject from 14)
                WHEN 'MESHA' THEN 1 WHEN 'VRISHABHA' THEN 2 WHEN 'MITHUNA' THEN 3 WHEN 'KARKA' THEN 4
                WHEN 'SIMHA' THEN 5 WHEN 'KANYA' THEN 6 WHEN 'TULA' THEN 7 WHEN 'VRISHCHIKA' THEN 8
                WHEN 'DHANU' THEN 9 WHEN 'MAKARA' THEN 10 WHEN 'KUMBHA' THEN 11 WHEN 'MEENA' THEN 12
                ELSE NULL END)
              - ( ((n.fact_value_num::int - 1) * 4) / 9 + 1 )
              + 120
            ) % 12
          ) + 1
        )
          WHEN 1 THEN 'favorable' WHEN 2 THEN 'unfavorable' WHEN 3 THEN 'favorable'
          WHEN 4 THEN 'unfavorable' WHEN 5 THEN 'unfavorable' WHEN 6 THEN 'favorable'
          WHEN 7 THEN 'favorable' WHEN 8 THEN 'unfavorable' WHEN 9 THEN 'neutral'
          WHEN 10 THEN 'favorable' WHEN 11 THEN 'favorable' WHEN 12 THEN 'unfavorable'
          ELSE NULL END
      )
  )
'''
STANDIN = ("SELECT\n  (TRUE)\n" + OLD_BB + OLD_C9 + OLD_UU2 + "  -- (g28) stand-in tail\n  AND NOT EXISTS (SELECT 1 FROM chart_facts WHERE false)\n"
           "  AS integrity_passed\n\n")
SCHEMA_B = """
CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, build_id uuid,
  fact_category text, fact_subject text, fact_key text, fact_value_text text, fact_value_num numeric, fact_value_jsonb jsonb,
  computed_at timestamptz);
"""
BUILD = str(uuid.uuid4())


def _a29() -> str:
    body = B.split("conjunct constant text := $conj$", 1)[1].split("$conj$", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _e27() -> str:
    body = M904.split("-- (e27) argala-offset full re-derivation", 1)[1].split("-- (f27)", 1)[0]
    return "AND NOT EXISTS (" + body.split("AND NOT EXISTS (", 1)[1].rstrip()


def _new_bb_fragment() -> str:
    return B.split("new_bb constant text := $nb$", 1)[1].split("$nb$", 1)[0]


def _new_c9_fragment() -> str:
    return B.split("new_c9 constant text := $nc$", 1)[1].split("$nc$", 1)[0]


def _new_uu2_fragment() -> str:
    return B.split("new_uu2 constant text := $nu$", 1)[1].split("$nu$", 1)[0]


def _conj(fragment: str) -> str:
    """The conjunct (from `AND NOT EXISTS (` on) of a comment-plus-SQL fragment, ready for _violations."""
    return "AND NOT EXISTS (" + fragment.split("AND NOT EXISTS (", 1)[1].rstrip()


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
    assert OLD_BB not in text and OLD_C9 not in text                     # the live (bb) and (c9) are gone ...
    assert text.count(_new_bb_fragment()) == 1 and text.count(_new_c9_fragment()) == 1   # ... replaced once each by the corrected text
    assert text.count("Migration 1221 (bb tolerance)") == 1 and text.count("Migration 1221 (c9 domain)") == 1
    assert OLD_UU2 not in text and text.count(_new_uu2_fragment()) == 1 and text.count("Migration 1221 (uu2 moon sign)") == 1
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
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, 'orb_strength', 'orb_strengthX') WHERE asset_id='ga_structural'",
     "live conjunct (bb) is not present exactly once"),
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, '0.9375', '0.9376') WHERE asset_id='ga_structural'",
     "live conjunct (c9) is not present exactly once"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || $d$" + OLD_BB + "$d$ WHERE asset_id='ga_structural'",
     "live conjunct (bb) is not present exactly once"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || $d$" + OLD_C9 + "$d$ WHERE asset_id='ga_structural'",
     "live conjunct (c9) is not present exactly once"),
    ("UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, 'NAKSHATRA_MOON_BIRTH', 'X') WHERE asset_id='ga_structural'",
     "live conjunct (uu2) is not present exactly once"),
    ("UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || $d$" + OLD_UU2 + "$d$ WHERE asset_id='ga_structural'",
     "live conjunct (uu2) is not present exactly once"),
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


# ── (bb) aspect_tajik orb_strength and (c9) karakatva composite_strength: the two corrected conjuncts ─────────────────

WRITER = (pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "ga_structural_writer.py").read_text(encoding="utf-8")
# the writer's own constants, mirrored from ga_writers/ga_structural_writer.py (static test below asserts the mirror)
DEEPTAMSA = {"Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0, "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0}
KARAKA_STRENGTH = (1.0, 0.875, 0.5, 0.25)          # exalted, own_sign, neutral, debilitated
HOUSE_STRENGTH = (1.0, 0.75, 0.5)                  # kendra, 5/9, other


def test_the_writer_constants_mirrored_in_these_tests_are_the_writers_own():
    """If the writer's tables change, this fails and the (c9) domain and the (bb) tolerance bound must be re-derived."""
    assert '"Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0,' in WRITER and '"Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0,' in WRITER
    assert '{"exalted": 1.0, "own_sign": 0.875, "neutral": 0.5, "debilitated": 0.25}.get(dignity, 0.5)' in WRITER
    assert "house_strength = (1.0 if karaka_house in {1, 4, 7, 10} else 0.75 if karaka_house in {5, 9} else 0.5)" in WRITER
    assert "composite = round((karaka_strength + house_strength) / 2.0, 4)" in WRITER and "composite = 0.5" in WRITER
    assert "orb_strength = round(max(0.0, 1.0 - orb / deeptamsa_sum), 4)" in WRITER      # rounds the UNROUNDED quotient
    assert 'value_jsonb={\n                    "orb_deg": round(orb, 4),' in WRITER      # the stored orb_deg is rounded to 4 dp
    assert min(a + b for a in DEEPTAMSA.values() for b in DEEPTAMSA.values()) == 14.0      # the 5e-5/14 term of the bound


def test_the_migration_replaces_exactly_the_live_conjunct_texts_and_the_new_texts_carry_the_markers():
    assert B.split("old_bb constant text := $ob$", 1)[1].split("$ob$", 1)[0] == OLD_BB
    assert B.split("old_c9 constant text := $oc$", 1)[1].split("$oc$", 1)[0] == OLD_C9
    assert B.split("old_uu2 constant text := $ou$", 1)[1].split("$ou$", 1)[0] == OLD_UU2
    assert "Migration 1221 (uu2 moon sign)" in _new_uu2_fragment() and _new_uu2_fragment().startswith("  -- (uu2) ")
    assert _new_uu2_fragment().endswith("  )\n") and _new_uu2_fragment().count("ORDER BY p.computed_at DESC, p.build_id DESC") == 1
    assert "Migration 1221 (bb tolerance)" in _new_bb_fragment() and "Migration 1221 (c9 domain)" in _new_c9_fragment()
    assert _new_bb_fragment().startswith("  -- (bb) ") and _new_c9_fragment().startswith("  -- (c9) ")
    assert _new_bb_fragment().endswith("  )\n") and _new_c9_fragment().endswith("  )\n")     # the next comment line follows directly, as live
    flat = re.sub(r"\s*\n--\s*", " ", B)
    assert "bb9803524a61427e7f4f179a59911e33" in flat and "THREE CORRECTIONS RIDE WITH a29" in flat
    assert "c56f9e12b2002269eb5f27a7abc42105" in flat and "207959" in flat      # the recorded target md5 (post-apply verification)
    assert "check defects, not writer defects" in flat
    # the (uu2) statements the header must carry
    assert "(uu2) is table-wide (not canonical-scoped) and stays TRUE for the other two charts" in flat
    assert "9 of the 180 chandra_bala_natal_baseline rows differ from the nakshatra-derived baseline" in flat and "canonical chart's surya_siddhanta_classical rows" in flat
    assert "the corrected (uu2) is RED on those stale canonical rows from this apply until the S-L1 ga_panchanga rebuild writes them, and TRUE after it" in flat
    assert "ga_structural depends_on ga_panchanga" in flat and "NO OR of the two derivations" in flat


def _tajik_rows(rows) -> str:
    """rows: (key, orb_deg, deeptamsa_sum, orb_strength). One INSERT, all values as exact decimal text."""
    vals = ", ".join(
        f"('t{i}', '{CANON}', 'a', '{BUILD}', 'aspect_tajik', 'X_Y', '{k}', NULL, {od!r}, "
        f"'{{\"orb_deg\": {od!r}, \"deeptamsa_sum_deg\": {d!r}, \"orb_strength\": {st!r}}}'::jsonb)"
        for i, (k, od, d, st) in enumerate(rows))
    return "INSERT INTO chart_facts VALUES " + vals


def _writer_value(orb: float, d: float) -> tuple[float, float]:
    """(stored orb_deg, stored orb_strength) exactly as the writer computes them for an ithasala / eesarpha row."""
    return round(orb, 4), round(max(0.0, 1.0 - orb / d), 4)


def _row_count_sql(conjunct: str) -> str:
    """The conjunct's own SELECT, counting the violating ROWS instead of testing for existence."""
    inner = conjunct.split("AND NOT EXISTS (", 1)[1].rstrip()
    assert inner.endswith(")")
    return inner[:-1].replace("SELECT 1 FROM", "SELECT count(*) FROM", 1)


def _count(port: int, rows, conjunct: str) -> int:
    db = new_db(port)
    q(port, db, SCHEMA_B)
    if rows:
        q(port, db, _tajik_rows(rows))
    return int(q(port, db, _row_count_sql(conjunct)))


@requires_pg
def test_bb_the_old_text_false_reds_on_the_writers_own_rounding_ties_and_the_new_text_accepts_them(pg):
    import random
    # the rehearsal's own row: orb 13.4585 / deeptamsa 22.0 -> the writer stores 0.3882, the old check expects round(0.38825, 4) = 0.3883
    tie = [("ithasala", 13.4585, 22.0, 0.3882)]
    assert _count(pg, tie, _conj(OLD_BB)) == 1                      # old text: RED on a correct build
    assert _count(pg, tie, _conj(_new_bb_fragment())) == 0          # new text: accepts the writer's value
    # 4000 rows computed exactly the way the writer computes them, over every pairwise deeptamsa_sum, plus 800 constructed AT a
    # rounding boundary of the quotient (the worst case for the tolerance, with the smallest sum 14)
    rnd = random.Random(1221)
    sums = sorted({a + b for a in DEEPTAMSA.values() for b in DEEPTAMSA.values()})
    writer_rows = []
    for _ in range(4000):
        d = rnd.choice(sums)
        orb = rnd.uniform(1.0001, d)
        od, st = _writer_value(orb, d)
        writer_rows.append((rnd.choice(["ithasala", "eesarpha"]), od, d, st))
    for _ in range(800):
        d = rnd.choice([14.0, 14.0, 15.0, 16.0])
        k = rnd.randrange(1, int(d * 100))
        target = 1.0 - (k + 0.5) / 10000.0                          # a quotient on a 4 dp rounding boundary
        orb = d * (1.0 - target) + rnd.choice([-1, 1]) * rnd.uniform(0, 3e-6)
        if 1.0 < orb <= d:
            od, st = _writer_value(orb, d)
            writer_rows.append(("ithasala", od, d, st))
    old_red = _count(pg, writer_rows, _conj(OLD_BB))
    assert old_red >= 20, old_red                                   # the false RED is common on writer-exact rows, not a one-off
    assert _count(pg, writer_rows, _conj(_new_bb_fragment())) == 0  # the corrected text never flags a value the writer computed
    # fixed per-type values stay exact: yamaya 1.0, manaau 0.1
    assert _count(pg, [("yamaya", 0.5, 22.0, 1.0), ("manaau", 25.0, 22.0, 0.1)], _conj(_new_bb_fragment())) == 0


@requires_pg
@pytest.mark.parametrize("row", [
    ("ithasala", 13.4585, 22.0, 0.3885),     # two units off the writer's 0.3882
    ("eesarpha", 13.4585, 22.0, 0.3892),
    ("ithasala", 13.4585, 22.0, 0.4585),     # 0.07 off
    ("ithasala", 13.4585, 22.0, 0.0),
    ("ithasala", 13.4585, 22.0, 0.6118),     # orb/sum instead of 1 - orb/sum
    ("ithasala", 5.0, 22.0, 0.7619),         # strength computed with the wrong deeptamsa sum (21.0 gives 0.7619; 22.0 gives 0.7727)
    ("yamaya", 0.5, 22.0, 0.9999),           # yamaya is exactly 1.0
    ("yamaya", 0.5, 22.0, 0.5),
    ("manaau", 25.0, 22.0, 0.1001),          # manaau is exactly 0.1
    ("manaau", 25.0, 22.0, 0.0999),
    ("manaau", 25.0, 22.0, 1.0),
])
def test_bb_a_genuinely_wrong_orb_strength_is_still_false(pg, row):
    assert _count(pg, [row], _conj(_new_bb_fragment())) == 1, row


@requires_pg
def test_bb_a_null_orb_strength_is_not_flagged_before_or_after(pg):
    db = new_db(pg)
    q(pg, db, SCHEMA_B)
    q(pg, db, f"INSERT INTO chart_facts VALUES ('n', '{CANON}', 'a', '{BUILD}', 'aspect_tajik', 'X_Y', 'ithasala', NULL, 5.0, "
              "'{\"orb_deg\": 5.0, \"deeptamsa_sum_deg\": 22.0}'::jsonb)")
    assert _violations(pg, db, _conj(OLD_BB)) == 0 and _violations(pg, db, _conj(_new_bb_fragment())) == 0   # NULL <> x is not true: same on both


@requires_pg
def test_bb_the_writers_zero_clamp_is_kept_a_strength_of_zero_beyond_the_sum_is_accepted_as_before(pg):
    row = [("eesarpha", 23.0, 22.0, 0.0)]                           # max(0.0, 1 - orb/sum) = 0.0, as the writer clamps
    assert _count(pg, row, _conj(OLD_BB)) == 0 and _count(pg, row, _conj(_new_bb_fragment())) == 0
    assert _count(pg, [("eesarpha", 23.0, 22.0, 0.05)], _conj(_new_bb_fragment())) == 1


def _c9_rows(values) -> str:
    vals = ", ".join(f"('c{i}', '{CANON}', 'a', '{BUILD}', 'karakatva_strength_per_significance', 's{i}', 'composite_strength', NULL, {v!r}, NULL)"
                     for i, v in enumerate(values))
    return "INSERT INTO chart_facts VALUES " + vals


def _domain_sql(fragment: str) -> str:
    """The value list of the conjunct's NOT IN (...), so a per-row count can be taken from the migration's own text."""
    return re.search(r"NOT IN \(([^)]*)\)", fragment).group(1)


def _writer_composites() -> list[float]:
    """Every value the writer can store: (karaka_strength + house_strength) / 2 over the 4 x 3 tiers, plus the 0.5 fallback."""
    return sorted({round((k + h) / 2.0, 4) for k in KARAKA_STRENGTH for h in HOUSE_STRENGTH} | {0.5})


@requires_pg
def test_c9_the_domain_is_exactly_what_the_writer_can_store_and_the_old_list_missed_two_values(pg):
    domain = _writer_composites()
    assert domain == [0.375, 0.5, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1.0]
    listed = sorted(float(x) for x in _domain_sql(_new_c9_fragment()).split(","))
    assert listed == domain                                         # the migration's list IS the writer's reachable set
    old_listed = sorted(float(x) for x in _domain_sql(OLD_C9).split(","))
    assert sorted(set(domain) - set(old_listed)) == [0.6875, 0.875] and set(old_listed) <= set(domain)
    db = new_db(pg)
    q(pg, db, SCHEMA_B)
    q(pg, db, _c9_rows(domain))
    assert _violations(pg, db, _conj(OLD_C9)) == 1                 # old text: RED on a correct chart that lands on 0.6875 / 0.875
    assert _violations(pg, db, _conj(_new_c9_fragment())) == 0     # new text: accepts every value the writer can store


@requires_pg
@pytest.mark.parametrize("wrong", [0.7, 0.9, 0.3125, 0.0, 1.0625, 0.8751, 0.6874, 1.5, 0.25])
def test_c9_a_value_the_writer_cannot_store_is_still_false(pg, wrong):
    db = new_db(pg)
    q(pg, db, SCHEMA_B)
    q(pg, db, _c9_rows(_writer_composites() + [wrong]))
    assert _violations(pg, db, _conj(_new_c9_fragment())) == 1, wrong


@requires_pg
def test_1221_corrections_are_idempotent_and_apply_individually_when_a_part_is_already_there(pg):
    db = _fresh_b(pg)
    f = _write("b", B)
    assert psql(pg, db, file=f).returncode == 0
    full = q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'")
    for old, new_frag in ((OLD_BB, _new_bb_fragment()), (OLD_C9, _new_c9_fragment()), (OLD_UU2, _new_uu2_fragment())):
        # (a29) and the other correction are in; this one is back to the live text: the file corrects just this one, to the same result
        q(pg, db, f"UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, $n${new_frag}$n$, $o${old}$o$) "
                  "WHERE asset_id='ga_structural'")
        assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") != full
        assert psql(pg, db, file=f).returncode == 0
        assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == full
    # (a29) back out (the pre-1221 live shape of a text that already carries both corrections): only a29 is added again
    db2 = _fresh_b(pg)
    q(pg, db2, f"UPDATE asset_registry SET integrity_check_sql = replace(replace(replace(integrity_check_sql, $o${OLD_BB}$o$, $n${_new_bb_fragment()}$n$), "
               f"$o${OLD_C9}$o$, $n${_new_c9_fragment()}$n$), $o${OLD_UU2}$o$, $n${_new_uu2_fragment()}$n$) WHERE asset_id='ga_structural'")
    assert psql(pg, db2, file=f).returncode == 0
    assert q(pg, db2, "SELECT md5(integrity_check_sql) FROM asset_registry WHERE asset_id='ga_structural'") == full


@requires_pg
def test_bb_the_true_extreme_of_the_tolerance_is_accepted_and_a_half_unit_tolerance_would_reject_it(pg):
    """The largest disagreement the writer's own arithmetic can produce between its stored orb_strength and the check's
    recomputation from the stored orb_deg is 16/3 * 1e-5 = 5.333e-5 (1/18750) (deeptamsa_sum 15 and above; found by exhaustive search over
    every pairwise sum), which is MORE than half a unit in the 4th decimal: a tolerance of 0.00005 would false-RED a correct build.
    Concrete case, computed with the writer's arithmetic: orb 7.4902500000000005 (the float just above the tie 7.49025) stores orb_deg 7.4903 and orb_strength 0.5007, while
    1 - 7.4903/15 = 0.50064667 (the review's 9.3742 / 0.375 pair is not reachable: it needs the quotient below 0.37505, i.e.
    orb above 9.37425, which stores orb_deg 9.3743)."""
    from fractions import Fraction
    od, st = _writer_value(7.4902500000000005, 15.0)
    assert (od, st) == (7.4903, 0.5007)
    gap = abs(Fraction(str(st)) - (1 - Fraction(str(od)) / 15))
    assert Fraction(5, 100000) < gap < Fraction(1, 10000) and abs(float(gap) - 16e-5 / 3) < 1e-9     # 5.333e-5
    # nothing the writer can produce exceeds it: exhaustive over the 4 dp orb grid and both rounding edges, every pairwise sum
    worst = Fraction(0)
    for total in sorted({int(a + b) for a in DEEPTAMSA.values() for b in DEEPTAMSA.values()}):
        for k in range(10001, total * 10000 + 1, 7):               # stride 7 keeps this fast; the case above is checked exactly
            y = 1 - Fraction(k, 10000) / total
            for edge in (Fraction(-5, 100000), Fraction(5, 100000)):
                x = max(Fraction(0), 1 - (Fraction(k, 10000) + edge) / total)
                t = x * 10000
                s4 = Fraction(int(t) + (1 if t - int(t) >= Fraction(1, 2) else 0), 10000)
                worst = max(worst, abs(s4 - y))
    assert worst <= Fraction(16, 3 * 100000) < Fraction(1, 10000)
    row = [("ithasala", od, 15.0, st)]
    assert _count(pg, row, _conj(OLD_BB)) == 1                     # the old exact check false-REDs it
    assert _count(pg, row, _conj(_new_bb_fragment())) == 0         # the corrected check accepts it
    assert _count(pg, [("ithasala", od, 15.0, 0.5009)], _conj(_new_bb_fragment())) == 1    # two units off: still false


def _fresh_b_two_rows(port: int) -> str:
    """_fresh_b, but with the registry's primary key dropped and a second ga_structural row, so the single UPDATE matches 2 rows."""
    db = _fresh_b(port)
    q(port, db, "ALTER TABLE asset_registry DROP CONSTRAINT asset_registry_pkey CASCADE")
    q(port, db, "INSERT INTO asset_registry (asset_id, count_sql, target_floor, integrity_check_sql, is_active) "
                "SELECT asset_id, count_sql, target_floor, integrity_check_sql, is_active FROM asset_registry WHERE asset_id = 'ga_structural'")
    return db


def _fresh_b_text_rewriting_trigger(port: int, marker: str = "Migration 1221 (c9 domain)") -> str:
    """_fresh_b plus a BEFORE UPDATE trigger that strips one marker from the text being written: the UPDATE matches one row but
    the stored text lacks a marker."""
    db = _fresh_b(port)
    q(port, db, f"""
      CREATE FUNCTION strip_marker() RETURNS trigger LANGUAGE plpgsql AS $f$
      BEGIN NEW.integrity_check_sql := replace(NEW.integrity_check_sql, '{marker}', 'x'); RETURN NEW; END $f$;
      CREATE TRIGGER strip_marker BEFORE UPDATE OF integrity_check_sql ON asset_registry FOR EACH ROW EXECUTE FUNCTION strip_marker();
    """)
    return db


@requires_pg
@pytest.mark.parametrize("make_db", [
    _fresh_b_two_rows,
    lambda port: _fresh_b_text_rewriting_trigger(port, "Migration 1221 (c9 domain)"),
    lambda port: _fresh_b_text_rewriting_trigger(port, "Migration 1221 (uu2 moon sign)"),
], ids=["update_matches_two_rows", "stored_text_lacks_the_c9_marker", "stored_text_lacks_the_uu2_marker"])
def test_1221_after_apply_assertion_raises_on_correct_looking_code_and_the_runner_shaped_transaction_changes_nothing(pg, make_db):
    """The guards before the UPDATE all pass here (live text carries (g28), anchor once, each old conjunct once); only the
    after-apply assertion (`n <> 1 OR NOT EXISTS (... markers present, old text gone)` -> 'failed to apply') can catch it."""
    db = make_db(pg)
    snap = "SELECT string_agg(md5(integrity_check_sql), ',' ORDER BY md5(integrity_check_sql)) FROM asset_registry"
    before, fresh_before, specs_before = q(pg, db, snap), reg.freshness_snapshot(pg, db), reg.specs_snapshot(pg, db)
    r = psql(pg, db, file=_write("b", B), single_transaction=True)
    assert r.returncode != 0 and "ga_structural integrity patch failed to apply" in r.stderr, r.stderr
    assert q(pg, db, snap) == before                               # the registry is untouched
    assert reg.freshness_snapshot(pg, db) == fresh_before          # no trigger side effect survived
    assert reg.specs_snapshot(pg, db) == specs_before              # and part 2 (the spec swap) never ran


# ── (uu2) chandra_bala_natal_baseline: the birth Moon sign comes from the position fact, per ayanamsha ──────────────────

import ast  # noqa: E402

PANCH = (pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "ga_panchanga_writer.py").read_text(encoding="utf-8")
SANSKRIT = ["MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA", "TULA", "VRISHCHIKA", "DHANU", "MAKARA", "KUMBHA", "MEENA"]
ENGLISH = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
CHART_M = "aaaaaaaa-0000-4000-8000-0000000000a1"
CHART_Z = "aaaaaaaa-0000-4000-8000-0000000000a2"


def _writer_chandra_bala() -> dict:
    src = PANCH.split("_CHANDRA_BALA: dict[int, str] = ", 1)[1].split("}", 1)[0] + "}"
    return ast.literal_eval(src)


def _cb_class(transit_idx: int, birth_idx: int) -> str:
    """The writer's own formula: position = (transit - birth) % 12 + 1 -> _CHANDRA_BALA (indices are 0-based here)."""
    return _writer_chandra_bala()[(transit_idx - birth_idx) % 12 + 1]


def test_the_chandra_bala_mapping_the_check_encodes_is_the_writers_own_and_the_nakshatra_formula_is_the_one_replaced():
    wb = _writer_chandra_bala()
    assert wb == {1: "favorable", 2: "unfavorable", 3: "favorable", 4: "unfavorable", 5: "unfavorable", 6: "favorable",
                  7: "favorable", 8: "unfavorable", 9: "neutral", 10: "favorable", 11: "favorable", 12: "unfavorable"}
    for frag in (OLD_UU2, _new_uu2_fragment()):                     # the same CASE ladder in both texts
        assert "WHEN 1 THEN 'favorable' WHEN 2 THEN 'unfavorable' WHEN 3 THEN 'favorable'" in frag
        assert "WHEN 9 THEN 'neutral'" in frag and "WHEN 12 THEN 'unfavorable'" in frag
    assert "((n.fact_value_num::int - 1) * 4) / 9 + 1" in OLD_UU2 and "panchanga_nakshatra_moon" not in _new_uu2_fragment().split("ELSE NULL END", 1)[1].replace("-- ", "")


def _cb_rows(chart: str, aya: str, baseline_idx, position_signs, nak, stamp: int = 0) -> list[str]:
    """INSERT value tuples for one (chart, ayanamsha): the 12 baseline rows computed with baseline_idx as the birth sign (None: no
    baseline), one position fact per (computed_at, build, sign) in position_signs, and the nakshatra number (None: none)."""
    out = []
    n = 0

    def row(cat, subj, key, text=None, num=None, at="2026-06-01T00:00:00Z", build="00000000-0000-4000-8000-000000000001"):
        nonlocal n
        n += 1
        t = "NULL" if text is None else "'" + text.replace("'", "''") + "'"
        v = "NULL" if num is None else str(num)
        out.append(f"('{chart[-4:]}{aya[:3]}{stamp}_{n}', '{chart}', '{aya}', '{build}', '{cat}', '{subj}', '{key}', {t}, {v}, NULL, '{at}')")

    if baseline_idx is not None:
        for t_idx, name in enumerate(SANSKRIT):
            row("chandra_bala_natal_baseline", "TRANSIT_SIGN_" + name, "classification", _cb_class(t_idx, baseline_idx))
    for sign, at, build in position_signs:
        row("graha_position", "MOON", "sign", sign, None, at, build)
    if nak is not None:
        row("panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", "number", None, nak)
    return out


def _cb_db(port: int, specs) -> str:
    """specs: (chart, aya, baseline_idx, position_signs, nak) tuples."""
    db = new_db(port)
    q(port, db, SCHEMA_B)
    rows = []
    for i, (chart, aya, b, pos, nak) in enumerate(specs):
        rows += _cb_rows(chart, aya, b, pos, nak, stamp=i)
    q(port, db, "INSERT INTO chart_facts VALUES " + ", ".join(rows))
    return db


def _per_aya(port: int, db: str, fragment: str) -> dict[str, int]:
    """Violating chandra_bala rows per ayanamsha (the conjunct's own SELECT, grouped), so a pass is read ayanamsha by ayanamsha."""
    inner = _conj(fragment).split("AND NOT EXISTS (", 1)[1].rstrip()
    assert inner.endswith(")")
    sql = inner[:-1].replace("SELECT 1 FROM chart_facts a", "SELECT a.ayanamsha_id, count(*) FROM chart_facts a", 1) + " GROUP BY a.ayanamsha_id"
    assert "count(*)" in sql
    out = q(port, db, sql)
    return {ln.split("|")[0]: int(ln.split("|")[1]) for ln in out.splitlines() if ln}


T0, T1 = "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z"
B1, B2 = "00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"


def _mixed(correct: bool, port: int) -> str:
    """One synthetic chart whose Moon sign DIFFERS between ayanamshas, and where the nakshatra-derived sign agrees with the position
    fact on two ayanamshas and disagrees on two: lahiri Aquarius / nak 25 (derived Aquarius, agree); surya_siddhanta Pisces / nak 25
    (derived Aquarius: the canonical case); raman Taurus / nak 3 (Krittika: derived Aries); krishnamurti Gemini / nak 7 (derived Gemini).
    correct=True: baselines as #2969 writes them (from the position fact); False: as the old writer wrote them (nakshatra-derived)."""
    cases = [("lahiri", 10, 25), ("surya", 11, 25), ("raman", 1, 3), ("krishnamurti", 2, 7)]
    specs = []
    for aya, pos_idx, nak in cases:
        derived = ((nak - 1) * 4) // 9
        specs.append((CHART_M, aya, pos_idx if correct else derived, [(ENGLISH[pos_idx], T1, B1)], nak))
    return _cb_db(port, specs)


@requires_pg
def test_uu2_per_ayanamsha_a_correct_baseline_is_false_under_the_old_text_where_the_signs_differ_and_true_under_the_new(pg):
    db = _mixed(True, pg)
    old = _per_aya(pg, db, OLD_UU2)
    assert set(old) == {"surya", "raman"} and all(v > 0 for v in old.values()), old    # false-RED exactly where position and nakshatra disagree
    assert _per_aya(pg, db, _new_uu2_fragment()) == {}                                 # new: no violation on ANY ayanamsha
    assert _violations(pg, db, _conj(OLD_UU2)) == 1 and _violations(pg, db, _conj(_new_uu2_fragment())) == 0


@requires_pg
def test_uu2_per_ayanamsha_the_stale_baseline_is_true_under_the_old_text_and_false_under_the_new_exactly_where_it_differs(pg):
    """The canonical chart today: surya_siddhanta baseline rows written from the nakshatra-derived Aquarius while the position fact
    says Pisces. 9 of the 12 rows differ (the measured 9 of 180 on production, all canonical surya_siddhanta)."""
    db = _mixed(False, pg)
    assert _per_aya(pg, db, OLD_UU2) == {}
    new = _per_aya(pg, db, _new_uu2_fragment())
    assert set(new) == {"surya", "raman"} and new["surya"] == 9 and new["raman"] > 0, new
    assert _violations(pg, db, _conj(OLD_UU2)) == 0 and _violations(pg, db, _conj(_new_uu2_fragment())) == 1


@requires_pg
def test_uu2_a_baseline_from_a_sign_that_is_neither_is_false_under_both_no_or_of_the_two_derivations(pg):
    leo = ENGLISH.index("Leo")
    specs = [(CHART_M, aya, leo, [(ENGLISH[pos], T1, B1)], nak) for aya, pos, nak in (("lahiri", 10, 25), ("surya", 11, 25), ("raman", 1, 3), ("krishnamurti", 2, 7))]
    db = _cb_db(pg, specs)
    for frag in (OLD_UU2, _new_uu2_fragment()):
        got = _per_aya(pg, db, frag)
        assert set(got) == {"lahiri", "surya", "raman", "krishnamurti"} and all(v > 0 for v in got.values()), got
    # one baseline sign wrong on a single ayanamsha: only that ayanamsha is flagged (the others stay clean)
    specs = [(CHART_M, "lahiri", 10, [("Aquarius", T1, B1)], 25), (CHART_M, "krishnamurti", ENGLISH.index("Leo"), [("Gemini", T1, B1)], 7)]
    db2 = _cb_db(pg, specs)
    assert set(_per_aya(pg, db2, _new_uu2_fragment())) == {"krishnamurti"}


@requires_pg
def test_uu2_both_texts_are_true_where_the_two_derivations_agree(pg):
    specs = [(CHART_Z, "lahiri", 10, [("Aquarius", T1, B1)], 25), (CHART_Z, "krishnamurti", 2, [("Gemini", T1, B1)], 7),
             (CHART_Z, "raman", 10, [("Aquarius", T1, B1)], 25)]
    db = _cb_db(pg, specs)
    assert _per_aya(pg, db, OLD_UU2) == {} and _per_aya(pg, db, _new_uu2_fragment()) == {}
    assert _violations(pg, db, _conj(OLD_UU2)) == 0 and _violations(pg, db, _conj(_new_uu2_fragment())) == 0


@requires_pg
def test_uu2_the_position_fact_is_bound_to_its_own_ayanamsha_and_its_latest_generation_is_the_one_used(pg):
    # (1) per-ayanamsha binding: the position facts' computed_at rises with the ayanamsha, so a clause that ignored the ayanamsha would
    # take the LAST one (krishnamurti's Gemini) for every ayanamsha and false-RED the rest: the correct baselines must pass.
    specs = [(CHART_M, "lahiri", 10, [("Aquarius", "2026-06-01T01:00:00Z", B1)], 25), (CHART_M, "surya", 11, [("Pisces", "2026-06-01T02:00:00Z", B1)], 25),
             (CHART_M, "raman", 1, [("Taurus", "2026-06-01T03:00:00Z", B1)], 3), (CHART_M, "krishnamurti", 2, [("Gemini", "2026-06-01T04:00:00Z", B1)], 7)]
    db = _cb_db(pg, specs)
    assert _per_aya(pg, db, _new_uu2_fragment()) == {}
    # (1b) per-chart binding: two charts on the SAME ayanamsha with different Moon signs, the later-stamped chart's fact must not leak
    # into the other chart's rows
    two = _cb_db(pg, [(CHART_M, "lahiri", 10, [("Aquarius", "2026-06-01T01:00:00Z", B1)], 25),
                      (CHART_Z, "lahiri", 2, [("Gemini", "2026-06-01T05:00:00Z", B2)], 7)])
    assert _per_aya(pg, two, _new_uu2_fragment()) == {}
    # (2) generations: an older generation says Aquarius, the latest says Pisces; the baseline follows the latest: TRUE. The same
    # holds when the two generations share computed_at and only build_id orders them (the writer's DISTINCT ON order).
    for older, newer in (((T0, B2), (T1, B1)), ((T1, B1), (T1, B2))):
        db2 = _cb_db(pg, [(CHART_M, "surya", 11, [("Aquarius", older[0], older[1]), ("Pisces", newer[0], newer[1])], 25)])
        assert _per_aya(pg, db2, _new_uu2_fragment()) == {}, (older, newer)
        # and a baseline following the OLDER generation is false
        db3 = _cb_db(pg, [(CHART_M, "surya", 10, [("Aquarius", older[0], older[1]), ("Pisces", newer[0], newer[1])], 25)])
        assert _per_aya(pg, db3, _new_uu2_fragment()).get("surya", 0) > 0, (older, newer)


@requires_pg
def test_uu2_null_and_vacuity_are_as_before_nothing_is_checked_without_a_baseline_a_position_fact_or_a_known_sign(pg):
    # no position fact: the conjunct does not check that ayanamsha (the old text likewise skipped a chart with no nakshatra fact)
    db = _cb_db(pg, [(CHART_M, "lahiri", 3, [], 25)])
    assert _violations(pg, db, _conj(_new_uu2_fragment())) == 0 and _per_aya(pg, db, _new_uu2_fragment()) == {}
    # a sign name outside the twelve (Sanskrit, not English): NULL arithmetic, not flagged
    db2 = _cb_db(pg, [(CHART_M, "lahiri", 3, [("Kumbha", T1, B1)], 25)])
    assert _violations(pg, db2, _conj(_new_uu2_fragment())) == 0
    # a NULL classification is not flagged (NULL <> x is not true), as before
    db3 = _cb_db(pg, [(CHART_M, "lahiri", 10, [("Aquarius", T1, B1)], 25)])
    q(pg, db3, "UPDATE chart_facts SET fact_value_text = NULL WHERE fact_category = 'chandra_bala_natal_baseline' AND fact_subject = 'TRANSIT_SIGN_MESHA'")
    assert _violations(pg, db3, _conj(_new_uu2_fragment())) == 0 and _violations(pg, db3, _conj(OLD_UU2)) == 0
    # non-vacuous: the same data with one wrong classification is flagged
    q(pg, db3, "UPDATE chart_facts SET fact_value_text = 'neutral' WHERE fact_category = 'chandra_bala_natal_baseline' AND fact_subject = 'TRANSIT_SIGN_VRISHABHA'")
    assert _violations(pg, db3, _conj(_new_uu2_fragment())) == 1


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
