"""WFIX-A: bg_yogas no longer invents a formation sentence or presents the yoga's name as its signification.

Two parts.

* offline: the extractor's new fallbacks (deterministic restatement of the row's own cited rule; an honest empty
  signification; NULL ontology description) and the Python formatting that the reseal migration must reproduce
  byte for byte against `jsonb::text`;
* a disposable Postgres (never the project database; skipped loudly when no server binaries exist): migration 1334
  derives the new catalog AND ontology pins in SQL from the live tables under the verified-pre-state precondition, and
  the pins it writes equal the hashes of the tables after the REAL seeder writes the new texts; idempotent; catches up
  when the rebuild ran first; never overwrites an unclassifiable state.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[2]))

from brahmagyan import l0_yogas as Y  # noqa: E402
from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

M1334 = REPO / "platform" / "migrations" / "1334_bg_yogas_wfix_a_fallback_reseal.sql"
OLD_CATALOG_PIN = "eb57c4dee246fb3289c8ea66ea088efb292ef4d2506645bcfdd4acb6ca80ea4e"
OLD_ONTOLOGY_PIN = "7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab"
COLS = ("canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,"
        "source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class")
CATALOG_HASH = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(" + COLS + ")::text, E'\\n' ORDER BY canonical_id COLLATE \"C\"),''),'UTF8')),'hex') "
                "FROM brahma_yoga_catalog")
ONTOLOGY_HASH = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation)::text,"
                 " E'\\n' ORDER BY entity_class COLLATE \"C\",canonical_id COLLATE \"C\"),''),'UTF8')),'hex') FROM brahma_ontology WHERE entity_class = 'yoga'")

# the live rules of the four rows the fallback wrote (read-only from production on 2026-10-08)
LIVE_RULES = {
    "kedara_sar": {"requires": [{"relation": "planets_in_four_signs_nabhasa_kedara"}]},
    "vajra_sar": {"requires": [{"relation": "benefics_in_1_7_malefics_in_4_10"}]},
    "vapi_sar": {"requires": [{"relation": "all_planets_in_panapharas_or_apoklimas"}]},
    "yava_sar": {"requires": [{"relation": "malefics_in_1_7_benefics_in_4_10"}]},
}
RESULT = {"kedara_sar": "native signs commencing from the\nescendant,\nChakra yoga is formed."}      # the one row whose chunk states a result


def _extracted(post: bool) -> list[dict]:
    """The corpus-extracted rows as the OLD (post=False) and NEW (post=True) extractor writes them."""
    rows = []
    for cid, rule in LIVE_RULES.items():
        name = cid.split("_")[0].title() + " Yoga (Saravali) Yoga"
        chapter = 359 if cid == "kedara_sar" else 358
        old_formation = f"{name}: formation per PG{chapter}:C1 (bphs Ch.{chapter})"
        sig = RESULT.get(cid, "")
        rows.append({
            "canonical_id": cid, "name_sa": name.removesuffix(" Yoga"), "name_en": name, "category": "other", "school": "parashari",
            "formation_rule_jsonb": rule,
            "formation_text": Y._formation_text("", rule) if post else old_formation,
            "significations_jsonb": {"gives": [], "subcategory": "structured_template", "source_chunk": "c"},
            "significations_text": Y._signification_text(sig, "") if post else (sig or name),
            "cancellation_conditions": {}, "classical_citations": [{"text_id": "bphs", "chapter": chapter}],
            "rare": False, "source_citation": f"BPHS Ch.{chapter} (PG{chapter}:C1)", "_chunk_id_str": None,
        })
    return rows


# ───────────────────────── offline ─────────────────────────

def test_python_formatting_equals_jsonb_text_for_every_live_rule():
    """The migration restates the rule with jsonb::text; the seeder with json.dumps(sort_keys=True): they must agree byte for byte."""
    for rule in LIVE_RULES.values():
        assert Y._formation_text("", rule) == "Structured formation rule: " + json.dumps(rule, sort_keys=True, ensure_ascii=False)
        assert json.dumps(rule, sort_keys=True, ensure_ascii=False) == json.dumps(rule)           # compact-form agrees with PG's `{"k": v}` text
    assert Y._formation_text("", LIVE_RULES["vajra_sar"]) == 'Structured formation rule: {"requires": [{"relation": "benefics_in_1_7_malefics_in_4_10"}]}'


def test_the_migration_carries_the_pins_the_live_tables_were_verified_to_hold():
    t = M1334.read_text(encoding="utf-8")
    assert t.count(OLD_CATALOG_PIN) >= 1 and t.count(OLD_ONTOLOGY_PIN) >= 1
    m = (REPO / "platform" / "migrations" / "1322_nirmana_l0_yogas_citation_pass2_reseal.sql").read_text(encoding="utf-8")
    assert "new_pin := post_hash" in m                      # 1322 is the pattern this migration extends
    assert "LIKE '%: formation per % (% Ch.%)'" in t and "significations_text = name_en" in t


# ───────────────────────── real SQL ─────────────────────────

DDL = """
CREATE TABLE brahma_yoga_catalog (canonical_id text PRIMARY KEY, name_sa text NOT NULL, name_en text NOT NULL, category text NOT NULL,
  formation_rule_jsonb jsonb NOT NULL, formation_text text NOT NULL, significations_jsonb jsonb NOT NULL DEFAULT '{}'::jsonb, significations_text text NOT NULL,
  cancellation_conditions jsonb, classical_citations jsonb, source_chunk_ids bigint[] DEFAULT ARRAY[]::bigint[], school text NOT NULL, rare boolean NOT NULL DEFAULT false,
  computed_strength_formula text, bhanga_rules_jsonb jsonb, partial_formation_threshold numeric, strength_formula_ref text, result_class text,
  created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE brahma_ontology (entity_class text, canonical_id text, canonical_name_en text, canonical_name_sa text, synonyms text[], description text, source_citation text);
CREATE TABLE reference_yogas (canonical_id text PRIMARY KEY, name_en text, category text);
CREATE TABLE brahma_yoga_source_chunks (canonical_id text, source_chunk_id uuid);
"""


def _db(pg_port, monkeypatch, post: bool):
    """The three yoga projections as the REAL seeder writes them from the inline + detector rows plus the four extracted rows (old or new texts)."""
    import psycopg
    db = new_db(pg_port)
    r = psql(pg_port, db, DDL); assert r.returncode == 0, r.stderr
    monkeypatch.setattr(Y, "extract_yogas_from_corpus", lambda conn: _extracted(post))
    conn = psycopg.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db)
    try:
        Y.seed_yogas(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def _registry(pg, db, catalog_pin, ontology_pin):
    chk = f"SELECT true -- catalog pin '{catalog_pin}' -- ontology pin '{ontology_pin}' -- reference pin 'aaaa'"
    r = psql(pg, db, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text)"); assert r.returncode == 0, r.stderr
    r = psql(pg, db, "INSERT INTO asset_registry VALUES ('bg_yogas', $c$" + chk + "$c$)"); assert r.returncode == 0, r.stderr
    return chk


def _migration(cat, ont):
    """The real migration text with its two sealed-pin constants rebased to the replica's pre-state hashes."""
    t = M1334.read_text(encoding="utf-8")
    t = t.replace("old_catalog_pin constant text := '" + OLD_CATALOG_PIN + "'", "old_catalog_pin constant text := '" + cat + "'")
    t = t.replace("old_ontology_pin constant text := '" + OLD_ONTOLOGY_PIN + "'", "old_ontology_pin constant text := '" + ont + "'")
    assert cat in t and ont in t
    return t


def _run(pg, db, text, tmp_path):
    f = tmp_path / "m.sql"
    f.write_text(text, encoding="utf-8")
    return psql(pg, db, file=f)


@requires_pg
def test_REAL_SQL_pre_and_post_states_differ_exactly_where_the_fallback_wrote(pg, monkeypatch):
    pre, post = _db(pg, monkeypatch, False), _db(pg, monkeypatch, True)
    assert q(pg, pre, CATALOG_HASH) != q(pg, post, CATALOG_HASH) and q(pg, pre, ONTOLOGY_HASH) != q(pg, post, ONTOLOGY_HASH)
    assert q(pg, pre, "SELECT count(*) FROM brahma_yoga_catalog WHERE formation_text LIKE '%: formation per % (% Ch.%)'") == "4"
    assert q(pg, post, "SELECT count(*) FROM brahma_yoga_catalog WHERE formation_text LIKE '%: formation per %'") == "0"
    assert q(pg, pre, "SELECT count(*) FROM brahma_yoga_catalog WHERE significations_text = name_en") == "3"
    assert q(pg, post, "SELECT count(*) FROM brahma_yoga_catalog WHERE significations_text = name_en") == "0"
    assert q(pg, post, "SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga' AND description IS NULL") == "3"
    assert q(pg, post, "SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga' AND description = ''") == "0"


@requires_pg
def test_REAL_SQL_the_migration_writes_the_pins_a_rebuild_produces(pg, monkeypatch, tmp_path):
    post_db = _db(pg, monkeypatch, True)
    want_cat, want_ont = q(pg, post_db, CATALOG_HASH), q(pg, post_db, ONTOLOGY_HASH)
    db = _db(pg, monkeypatch, False)
    cat, ont = q(pg, db, CATALOG_HASH), q(pg, db, ONTOLOGY_HASH)
    chk = _registry(pg, db, cat, ont)
    r = _run(pg, db, _migration(cat, ont), tmp_path); assert r.returncode == 0, r.stderr
    stored = q(pg, db, "SELECT integrity_check_sql FROM asset_registry")
    assert stored == chk.replace(cat, want_cat).replace(ont, want_ont)       # ONLY the two pins moved, to what the rebuild produces
    before = q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry")
    r = _run(pg, db, _migration(cat, ont), tmp_path); assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry") == before       # idempotent


@requires_pg
def test_REAL_SQL_the_migration_catches_up_when_the_rebuild_ran_first(pg, monkeypatch, tmp_path):
    pre_db = _db(pg, monkeypatch, False)
    cat, ont = q(pg, pre_db, CATALOG_HASH), q(pg, pre_db, ONTOLOGY_HASH)          # the pins sealed on the old content
    db = _db(pg, monkeypatch, True)                                                # the tables were rebuilt BEFORE the reseal
    _registry(pg, db, cat, ont)
    r = _run(pg, db, _migration(cat, ont), tmp_path); assert r.returncode == 0, r.stderr
    stored = q(pg, db, "SELECT integrity_check_sql FROM asset_registry")
    assert q(pg, db, CATALOG_HASH) in stored and q(pg, db, ONTOLOGY_HASH) in stored and cat not in stored and ont not in stored


@requires_pg
def test_REAL_SQL_an_unclassifiable_state_is_left_untouched_with_a_warning(pg, monkeypatch, tmp_path):
    db = _db(pg, monkeypatch, False)
    cat, ont = q(pg, db, CATALOG_HASH), q(pg, db, ONTOLOGY_HASH)
    chk = _registry(pg, db, cat, ont)
    r = psql(pg, db, "UPDATE brahma_yoga_catalog SET formation_text = formation_text || ' (drift)' WHERE canonical_id = 'sarasvati_yoga'")
    assert r.returncode == 0, r.stderr
    r = _run(pg, db, _migration(cat, ont), tmp_path)
    assert r.returncode == 0 and "WARNING:  migration 1334 skipped" in r.stderr
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry") == chk
    # a missing registry row is a structural problem and refuses; an empty catalog is a notice and a no-op
    db2 = new_db(pg); assert psql(pg, db2, DDL + "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text);").returncode == 0
    r = _run(pg, db2, _migration(cat, ont), tmp_path)
    assert r.returncode != 0 and "refuses" in r.stderr
    db3 = new_db(pg); assert psql(pg, db3, DDL).returncode == 0
    _registry(pg, db3, cat, ont)
    r = _run(pg, db3, _migration(cat, ont), tmp_path)
    assert r.returncode == 0 and "brahma_yoga_catalog is empty" in r.stderr
