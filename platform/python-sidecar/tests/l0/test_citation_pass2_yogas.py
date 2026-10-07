"""Citation Pass 2 (decision OS-2026-10-05-CITATIONS) applied to bg_yogas: the row kala_sarpa_yoga (brahma_yoga_catalog).

Pinned offline and on a disposable Postgres (never the project database): the one seed row carries the decided K2 object, school 'modern' and the duplicate-authority
note while every other seed row is hashed against a pin; the Ldgr predicate of the census reads no placeholder in the catalog column; readers of the column keep
working with a K2-only entry; migration 1322 derives the new catalog pin from the live table under the verified-pre-state precondition and the pin it writes equals
the hash of the catalog after the REAL seed runs with the new row (on a replica holding the inline + detector rows: the corpus-extracted rows cannot exist offline,
which is exactly why the migration computes the pin in SQL); it is idempotent and never overwrites an unclassifiable state.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[4]
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(REPO / "platform" / "scripts" / "governance"))

from brahmagyan import l0_yogas as Y  # noqa: E402
from tests.pg_disposable import new_db, psql, q, pg, requires_pg  # noqa: E402,F401

MIG = REPO / "platform" / "migrations"
M1322 = MIG / "1322_nirmana_l0_yogas_citation_pass2_reseal.sql"
EC = REPO / "00_ARCHITECTURE" / "briefs" / "suvarna" / "citation_pass2" / "expected_change_bg_yogas.json"
SEALED_PIN = "4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8"      # migration 701's catalog pin
NOTE = "duplicate of dosha kala_sarpa; not fired by ga_yoga_writer (R6A.2)"
K2 = {"kind": "K2", "decision_id": "OS-2026-10-05-CITATIONS", "label": "modern practice / project judgment",
      "note": "not a classical source; duplicate authority: ga_yoga_writer deliberately does not fire this relation; the dosha-form kala_sarpa in ga_structural_writer is the single authority (R6A.2)"}
OLD_CITATIONS = [{"text_id": "classical_tradition"}]
COLS = ("canonical_id,name_sa,name_en,category,formation_rule_jsonb,formation_text,significations_jsonb,significations_text,cancellation_conditions,classical_citations,"
        "source_chunk_ids,school,rare,computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,strength_formula_ref,result_class")
CATALOG_HASH = ("SELECT encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(" + COLS + ")::text, E'\\n' ORDER BY canonical_id COLLATE \"C\"),''),'UTF8')),'hex') "
                "FROM brahma_yoga_catalog")


def _row():
    r = [x for x in Y.YOGAS_CORE + Y.DETECTOR_YOGAS if x["canonical_id"] == "kala_sarpa_yoga"]
    assert len(r) == 1
    return r[0]


# ───────────────────────── pure: the seed ─────────────────────────

def test_the_row_carries_the_decided_k2_object_school_and_note():
    r = _row()
    assert r["classical_citations"] == [K2] and r["school"] == "modern"
    assert r["cancellation_conditions"] == {"bhanga": ["a_planet_outside_the_axis", "strong_benefic_kendra"], "notes": NOTE}
    assert (r["category"], r["name_en"], r["name_sa"]) == ("aristha", "Kala Sarpa Yoga", "Kāla Sarpa Yoga")        # the identity is unchanged
    assert r["formation_rule_jsonb"] == {"requires": [{"relation": "all_seven_planets_hemmed_rahu_ketu_one_side"}]}
    assert r["source_citation"] == Y.CLASSICAL                                                                        # the ontology projection is NOT part of the decision (see CITATION_AMBIGUOUS.md)
    assert K2["decision_id"] == "OS-2026-10-05-CITATIONS" and "text_id" not in K2


def test_every_other_inline_and_detector_row_is_unchanged():
    rest = sorted((x for x in Y.YOGAS_CORE + Y.DETECTOR_YOGAS if x["canonical_id"] != "kala_sarpa_yoga"), key=lambda x: x["canonical_id"])
    blob = json.dumps([[x["canonical_id"], x["school"], x.get("classical_citations"), x.get("cancellation_conditions"), x["formation_rule_jsonb"], x["category"]] for x in rest],
                      ensure_ascii=False, sort_keys=True)
    assert len(rest) == len(Y.YOGAS_CORE) + len(Y.DETECTOR_YOGAS) - 1
    assert hashlib.sha256(blob.encode("utf-8")).hexdigest() == PINNED_OTHER_ROWS
    assert not [x for x in Y.YOGAS_CORE + Y.DETECTOR_YOGAS if x["classical_citations"] == OLD_CITATIONS]               # no placeholder tradition label is left in the seed


PINNED_OTHER_ROWS = "17986c013e4cebb5abe575b012756682b0aae884ed59ac0e0e34efbe088247c6"


def test_the_fingerprint_declarations_evidence_lines_still_name_the_write_statements():
    """FINGERPRINT_DECLARATIONS.json cites the seeder's statements by line number; an edit above them must not move them."""
    decl = json.loads((REPO / "00_ARCHITECTURE" / "control" / "FINGERPRINT_DECLARATIONS.json").read_text(encoding="utf-8"))
    lines = (REPO / "platform" / "python-sidecar" / "brahmagyan" / "l0_yogas.py").read_text(encoding="utf-8").splitlines()
    cited = sorted({int(m.group(1)) for m in re.finditer(r"l0_yogas\.py:(\d+)", json.dumps(decl))})
    assert cited, "no l0_yogas.py evidence lines found in FINGERPRINT_DECLARATIONS.json"
    for n in cited:
        assert re.search(r"INSERT INTO|DELETE FROM|cur\.execute", lines[n - 1]), (n, lines[n - 1])


def test_readers_of_the_citations_column_skip_an_entry_without_text_id():
    """routers/yoga_formation_band._citations lists text_id[:chapter] and skips entries without one: a K2-only column reads as no classical citation (never a crash)."""
    from routers.yoga_formation_band import _citations
    assert _citations({"classical_citations": [K2]}) == []
    assert _citations({"classical_citations": json.dumps([K2, {"text_id": "bphs", "chapter": 39}])}) == ["bphs:39"]


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


def _db(pg_port, monkeypatch):
    """The three yoga projections as the REAL seeder writes them from the inline + detector rows (the corpus extraction returns nothing offline)."""
    import psycopg
    db = new_db(pg_port)
    r = psql(pg_port, db, DDL); assert r.returncode == 0, r.stderr
    monkeypatch.setattr(Y, "extract_yogas_from_corpus", lambda conn: [])
    conn = psycopg.connect(host="127.0.0.1", port=pg_port, user="postgres", dbname=db)
    try:
        Y.seed_yogas(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def _to_pre_state(pg, db):
    """The catalog row as it was BEFORE this change (the old seed's values for the three columns)."""
    old_cancel = json.dumps({"bhanga": ["a_planet_outside_the_axis", "strong_benefic_kendra"]})
    r = psql(pg, db, "UPDATE brahma_yoga_catalog SET school = 'parashari', classical_citations = $j$" + json.dumps(OLD_CITATIONS) + "$j$::jsonb, "
                     "cancellation_conditions = $j$" + old_cancel + "$j$::jsonb WHERE canonical_id = 'kala_sarpa_yoga'")
    assert r.returncode == 0, r.stderr


def _stored_check(pin):
    t = (MIG / "701_bg_yogas_integrity_check_join_scope_fix.sql").read_text(encoding="utf-8")
    chk = re.search(r"yoga_check constant text := \$check\$(.*?)\$check\$;", t, re.S).group(1)
    assert chk.count(SEALED_PIN) == 1
    return chk.replace(SEALED_PIN, pin)


def _registry(pg, db, chk):
    r = psql(pg, db, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text)"); assert r.returncode == 0, r.stderr
    r = psql(pg, db, "INSERT INTO asset_registry VALUES ('bg_yogas', $c$" + chk + "$c$)"); assert r.returncode == 0, r.stderr


def _migration(rebased_to):
    """The real migration text, its sealed-pin constant rebased to the replica's pre-state hash (the replica cannot hold the corpus-extracted rows the real pin covers)."""
    t = M1322.read_text(encoding="utf-8")
    assert t.count(SEALED_PIN) >= 1
    return t.replace(SEALED_PIN, rebased_to)


def _run(pg, db, text, tmp_path):
    f = tmp_path / "m.sql"
    f.write_text(text, encoding="utf-8")
    return psql(pg, db, file=f)


@requires_pg
def test_REAL_SQL_the_migration_writes_the_pin_a_rebuild_produces(pg, monkeypatch, tmp_path):
    db = _db(pg, monkeypatch)
    post_rebuild = q(pg, db, CATALOG_HASH)                                     # the catalog after the REAL seed with the new row
    _to_pre_state(pg, db)
    pre = q(pg, db, CATALOG_HASH)
    assert pre != post_rebuild
    _registry(pg, db, _stored_check(pre))
    r = _run(pg, db, _migration(pre), tmp_path); assert r.returncode == 0, r.stderr
    stored = q(pg, db, "SELECT integrity_check_sql FROM asset_registry")
    assert post_rebuild in stored and pre not in stored
    assert stored == _stored_check(pre).strip().replace(pre, post_rebuild)      # ONLY the catalog pin moved
    # idempotent: a second application changes nothing
    before = q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry")
    r = _run(pg, db, _migration(pre), tmp_path); assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql) FROM asset_registry") == before
    # after the rebuild (here: the row put back to the post-state) the catalog hash IS the pin the migration wrote
    r = psql(pg, db, "UPDATE brahma_yoga_catalog SET school = 'modern', classical_citations = $j$" + json.dumps([K2]) + "$j$::jsonb, cancellation_conditions = "
                     "jsonb_set(cancellation_conditions, '{notes}', to_jsonb($n$" + NOTE + "$n$::text)) WHERE canonical_id = 'kala_sarpa_yoga'"); assert r.returncode == 0, r.stderr
    assert q(pg, db, CATALOG_HASH) == post_rebuild


@requires_pg
def test_REAL_SQL_the_migration_also_catches_up_when_the_catalog_was_rebuilt_first(pg, monkeypatch, tmp_path):
    db = _db(pg, monkeypatch)
    post_rebuild = q(pg, db, CATALOG_HASH)
    _to_pre_state(pg, db)
    pre = q(pg, db, CATALOG_HASH)
    _registry(pg, db, _stored_check(pre))
    _db_state_back = psql(pg, db, "UPDATE brahma_yoga_catalog SET school = 'modern', classical_citations = $j$" + json.dumps([K2]) + "$j$::jsonb, cancellation_conditions = "
                          "jsonb_set(cancellation_conditions, '{notes}', to_jsonb($n$" + NOTE + "$n$::text)) WHERE canonical_id = 'kala_sarpa_yoga'")
    assert _db_state_back.returncode == 0 and q(pg, db, CATALOG_HASH) == post_rebuild
    r = _run(pg, db, _migration(pre), tmp_path); assert r.returncode == 0, r.stderr
    assert post_rebuild in q(pg, db, "SELECT integrity_check_sql FROM asset_registry")


@requires_pg
def test_REAL_SQL_an_unclassifiable_state_is_left_untouched_with_a_notice(pg, monkeypatch, tmp_path):
    db = _db(pg, monkeypatch)
    _to_pre_state(pg, db)
    pre = q(pg, db, CATALOG_HASH)
    chk = _stored_check(pre)
    _registry(pg, db, chk)
    r = psql(pg, db, "UPDATE brahma_yoga_catalog SET formation_text = formation_text || ' (drift)' WHERE canonical_id = 'sarasvati_yoga'")   # an unrelated row differs from the sealed state
    assert r.returncode == 0, r.stderr
    r = _run(pg, db, _migration(pre), tmp_path)
    assert r.returncode == 0 and "skipped" in r.stderr
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry") == chk.strip()
    assert "WARNING:  migration 1322 skipped" in r.stderr                        # loud: a WARNING, not a NOTICE
    # a missing registry row still refuses (a structural problem); an EMPTY catalog (no kala_sarpa_yoga row) is a notice and a no-op, never a blocked deploy
    db2 = _db(pg, monkeypatch)
    r = psql(pg, db2, "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text)"); assert r.returncode == 0
    r = _run(pg, db2, _migration(pre), tmp_path)
    assert r.returncode != 0 and "refuses" in r.stderr
    db3 = _db(pg, monkeypatch)
    _registry(pg, db3, chk)
    r = psql(pg, db3, "DELETE FROM brahma_yoga_catalog"); assert r.returncode == 0, r.stderr
    r = _run(pg, db3, _migration(pre), tmp_path)
    assert r.returncode == 0 and "no kala_sarpa_yoga row" in r.stderr
    assert q(pg, db3, "SELECT integrity_check_sql FROM asset_registry") == chk.strip()


@requires_pg
def test_REAL_SQL_the_census_ldgr_predicate_reads_the_k2_object_as_a_source_and_the_old_label_as_a_placeholder(pg, monkeypatch):
    import asset_census as ac
    db = _db(pg, monkeypatch)
    lacking = ac._ldgr_lacking("classical_citations", "json")
    assert q(pg, db, f"SELECT count(*) FILTER (WHERE {lacking}) FROM brahma_yoga_catalog") == "0"
    _to_pre_state(pg, db)
    assert q(pg, db, f"SELECT count(*) FILTER (WHERE {lacking}) FROM brahma_yoga_catalog") == "1"       # not vacuous: the old tradition label IS what the census counted as a placeholder


@requires_pg
def test_REAL_SQL_the_expected_change_file_loads_and_its_row_count_is_the_unit(pg, monkeypatch):
    import fingerprint_declarations as fd
    import suvarna_global_asset_dispatch as gad
    spec, _sha = gad.load_expected_change(str(EC), "bg_yogas")
    decls = gad.load_declarations_or_refuse(fd.DEFAULT_DECLARATIONS)
    unit = gad.declared_unit_or_refuse(decls, "bg_yogas", gad.writer_siblings(str(REPO), "bg_yogas"))
    assert unit == "bg_yogas+grp_brahma_ontology"                       # own tables (catalog, reference, source chunks) + the whole shared brahma_ontology
    assert spec["decision"] == "OS-2026-10-05-CITATIONS" and spec["expected_post_row_count"] == 233 + 233 + 85 + 741
    assert spec["expected_post_fingerprint"] is None                    # NOT declared: the unit includes the corpus-extracted rows, which cannot be derived offline


def test_the_migration_constant_is_the_pin_migration_701_sealed():
    t = (MIG / "701_bg_yogas_integrity_check_join_scope_fix.sql").read_text(encoding="utf-8")
    chk = re.search(r"yoga_check constant text := \$check\$(.*?)\$check\$;", t, re.S).group(1)
    assert SEALED_PIN in chk and "FROM brahma_yoga_catalog)" in chk.split(SEALED_PIN, 1)[1][:60]
