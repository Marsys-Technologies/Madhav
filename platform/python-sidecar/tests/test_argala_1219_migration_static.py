"""Checks of the DRAFT migration 1219 (SS N-61 + Q-L1-04): ownership, count_sql (no double claims), digest spec.

Static checks always run. The SQL is also EXECUTED against a disposable local Postgres (tests/pg_disposable.py,
never the project database); those tests skip when no binaries are present. The integrity conjunct (a29) is NOT in
1219: it is migration 1221 (test_argala_1221_integrity_a29.py).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402
from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "argala_1219"
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")
M1219_PATH = MIGRATIONS / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql"
M1219 = M1219_PATH.read_text(encoding="utf-8")

OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"
FIVE = ["bhadra_flag", "chandra_bala_natal_baseline", "eclipse_proximity_natal", "panchaka_flag", "tara_bala_natal_baseline"]
STRENGTH_LIVE = (FIXTURES / "ga_strength_count_sql.txt").read_text(encoding="utf-8")
CONDITION_LIVE = (FIXTURES / "ga_condition_count_sql.txt").read_text(encoding="utf-8")


def _spec(text: str) -> dict:
    m = re.search(r"'(\{\"version\":\"nirmana-output-digest-spec-v1\".*?\})'::jsonb", text, re.S)
    assert m
    return json.loads(m.group(1))


def _pairs() -> list[tuple[str, str]]:
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
    old["components"][0]["where_in"]["fact_category"] = new_cats
    assert old == new and canonical_digest(new) == NEW_SHA
    assert M1219.count(NEW_SHA) >= 3 and OLD_SHA in M1219


def test_the_guard_md5s_are_the_live_texts_read():
    assert hashlib.md5(STRENGTH_LIVE.encode()).hexdigest() in M1219
    assert hashlib.md5(CONDITION_LIVE.encode()).hexdigest() in M1219


def test_ownership_covers_every_category_the_structural_writer_emits_and_the_argala_row():
    pairs = _pairs()
    assert ("argala_graha_natal", "ga_structural") in pairs
    structural = {c for c, a in pairs if a == "ga_structural"}
    spec_cats = set(_spec(M914)["components"][0]["where_in"]["fact_category"])
    owned_already = set(open("/Users/Dev/suvarna-evidence/TrackI/argala_l1/owned_structural.txt").read().split()) \
        if pathlib.Path("/Users/Dev/suvarna-evidence/TrackI/argala_l1/owned_structural.txt").exists() else None
    if owned_already is not None:      # snapshot of the 64 rows read live (outside the repo)
        assert len(owned_already) == 64 and spec_cats <= (owned_already | structural)
    twelve = {"virupa_drishti", "karaka_web_per_varga", "significator_path", "panchadha_maitri",
              "conjunction_special_point", "nakshatra_lord_relationship", "tara_bala", "yoga_label",
              "kendradhipati_dosha", "upapada_lagna", "dosha_label", "nakshatra_co_tenancy"}
    assert twelve <= structural and len(pairs) == len(set(pairs))
    # the two categories ga_structural emits that ga_strength's predicate claimed belong to ga_structural only
    assert ("vimsopaka_bala_per_graha", "ga_structural") in pairs and ("graha_saptavargaja_bala_component", "ga_structural") in pairs
    assert not [p for p in pairs if p[0] in ("vimsopaka_bala_per_graha", "graha_saptavargaja_bala_component") and p[1] != "ga_structural"]
    assert [(c, "ga_panchanga") in pairs for c in FIVE] == [True] * 5


def test_scope_no_floors_no_integrity_no_transaction_statements():
    assert not re.search(r"target_floor\s*=", M1219)                                     # floors are not touched
    assert "integrity_check_sql" not in re.sub(r"--[^\n]*", "", M1219)                    # (a29) is migration 1221
    assert "(a29)" not in re.sub(r"--[^\n]*", "", M1219)
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", M1219, re.M)
    assert "'%bhava_bala%'" not in M1219.split("strength_new constant text", 1)[1].split("$cs$;", 1)[0]


def test_the_category_in_the_spec_is_the_one_the_writer_emits():
    import ga_writers.ga_structural_writer as sut
    rows = sut._build_argala_graha_rows({"Mars": {"sign_num": 1}, "Sun": {"sign_num": 2}}, "D1", "c", "b", "a", "t", "e")
    assert {r["fact_category"] for r in rows} == {"argala_graha_natal"}


# ── executed against a disposable Postgres ──────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE fact_category_ownership (fact_category text NOT NULL, owning_asset_id text NOT NULL,
  created_at timestamptz DEFAULT now(), PRIMARY KEY (fact_category, owning_asset_id));
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text, target_floor integer, integrity_check_sql text);
CREATE TABLE asset_output_digest_specs (asset_id text NOT NULL, spec_sha256 text NOT NULL, spec jsonb NOT NULL,
  reviewed_at timestamptz, retired_at timestamptz, UNIQUE (asset_id, spec_sha256));
"""


def _fresh(port: int) -> str:
    db = new_db(port)
    q(port, db, SCHEMA)
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
def test_migration_applies_every_part_touches_no_floor_or_integrity_and_is_idempotent(pg):
    db = _fresh(pg)
    before_other = q(pg, db, "SELECT string_agg(asset_id || target_floor || integrity_check_sql, ',' ORDER BY asset_id) FROM asset_registry")
    r = psql(pg, db, file=M1219_PATH)
    assert r.returncode == 0, r.stderr
    pairs = _pairs()
    # 7 seeded rows - 5 deleted + every listed pair (the 5 panchanga pairs are among them)
    assert int(q(pg, db, "SELECT count(*) FROM fact_category_ownership")) == 7 - 5 + len(pairs)
    assert q(pg, db, "SELECT count(*) FROM fact_category_ownership WHERE fact_category='argala_graha_natal' AND owning_asset_id='ga_structural'") == "1"
    # the five panchanga categories belong to ga_panchanga only now
    assert q(pg, db, "SELECT string_agg(DISTINCT owning_asset_id, ',') FROM fact_category_ownership WHERE fact_category = ANY(ARRAY['" + "','".join(FIVE) + "'])") == "ga_panchanga"
    # count_sql narrowed; no floor and no integrity text moved
    strength = q(pg, db, "SELECT count_sql FROM asset_registry WHERE asset_id='ga_strength'")
    for gone in ("%bhava_bala%", "%vimsopaka%", "saptavargaja"):
        assert gone not in strength
    for kept in ("house_bhava_bala_%", "graha_vimsopaka_%", "ashtakavarga_%", "graha_shadbala_%", "graha_%_bala_per_varga"):
        assert kept in strength
    assert q(pg, db, "SELECT count_sql FROM asset_registry WHERE asset_id='ga_condition'") == "SELECT COUNT(*) FROM ga_condition_composite WHERE chart_id = $1"
    assert q(pg, db, "SELECT string_agg(asset_id || target_floor || integrity_check_sql, ',' ORDER BY asset_id) FROM asset_registry") == before_other
    # digest spec: old retired, new active exactly once
    assert q(pg, db, f"SELECT count(*) FROM asset_output_digest_specs WHERE retired_at IS NULL AND spec_sha256='{NEW_SHA}'") == "1"
    assert q(pg, db, f"SELECT retired_at IS NOT NULL FROM asset_output_digest_specs WHERE spec_sha256='{OLD_SHA}'") == "t"
    fp = "SELECT (SELECT md5(string_agg(count_sql, '' ORDER BY asset_id)) FROM asset_registry) || (SELECT count(*) FROM fact_category_ownership)"
    first = q(pg, db, fp)
    assert psql(pg, db, file=M1219_PATH).returncode == 0
    assert q(pg, db, fp) == first                                    # idempotent re-run


@requires_pg
@pytest.mark.parametrize("sabotage,expect", [
    ("INSERT INTO fact_category_ownership VALUES ('virupa_drishti','ga_sensitive')", "already owned by a different asset"),
    ("UPDATE asset_registry SET count_sql = count_sql || ' ' WHERE asset_id='ga_strength'", "ga_strength count_sql narrowing refused"),
    ("UPDATE asset_registry SET count_sql = 'SELECT 1' WHERE asset_id='ga_condition'", "ga_condition count_sql re-declaration refused"),
    ("INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) VALUES ('ga_structural','deadbeef','{}'::jsonb)", "unrecognised active row"),
])
def test_migration_refuses_unexpected_live_state(pg, sabotage, expect):
    db = _fresh(pg)
    q(pg, db, sabotage)
    r = psql(pg, db, file=M1219_PATH)
    assert r.returncode != 0 and expect in r.stderr, r.stderr
