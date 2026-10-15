"""test_n233_vocab_registered_alias.py: Vocab.alias, SS ruling N-233 R2.

A spelling counts as CANONICAL when it is the canonical form OR a REGISTERED ALIAS: the exact string is in bg_ontology's alias set (the `synonyms` array or the `canonical_name_sa` of a brahma_ontology row of
class planet / sign / nakshatra / house). The set is READ from the table at measure time, never hard-coded; a variant that is not registered stays a real FAIL.

Proved on a DISPOSABLE PostgreSQL whose `brahma_ontology` is seeded from the repo's own ontology source (the test fixture standing in for production; no alias row is invented): the registered spelling reads PASS,
the unregistered variant (a case variant, a padded form, a storage code the ontology does not register) reads FAIL, the SAME column flips when the registered row is deleted (a mutation: the set is read live), an
alias set that cannot be read or comes back empty is NO_DETECTOR, a registered alias beyond the sample (the existence read) is graded like one inside it, and the pure classifier is exercised on a hand-built set.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

PASS, FAIL, PARTIAL, NO_DET = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET


def _ontology_rows():
    ont = ac._load_sidecar_module("brahmagyan/l0_ontology.py", "_t233_ont")
    return [e for e in ont.ENTITIES if e["entity_class"] in ac.VOCAB_REGISTERED_CLASSES]


def _seed(pg, monkeypatch, rows=None):
    point_psql_at(pg, monkeypatch)
    ac.psql("DROP TABLE IF EXISTS brahma_ontology")
    ac.psql("CREATE TABLE brahma_ontology (id serial PRIMARY KEY, entity_class text NOT NULL, canonical_id text NOT NULL, canonical_name_en text NOT NULL, canonical_name_sa text, "
            "synonyms text[] NOT NULL DEFAULT '{}', description text, source_citation text NOT NULL DEFAULT 'x')")
    for e in (_ontology_rows() if rows is None else rows):
        syn = "ARRAY[" + ",".join(ac._vocab_lit(x) for x in e["synonyms"]) + "]::text[]" if e["synonyms"] else "'{}'::text[]"
        sa = ac._vocab_lit(e["canonical_name_sa"]) if e.get("canonical_name_sa") else "NULL"
        ac.psql(f"INSERT INTO brahma_ontology (entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms) VALUES ({ac._vocab_lit(e['entity_class'])}, {ac._vocab_lit(e['canonical_id'])}, "
                f"{ac._vocab_lit(e['canonical_name_en'])}, {sa}, {syn})")
    ac._VOCAB_REGISTERED = None                                  # the detector must LOAD it (the conftest starts every test with the set loaded as empty)


def _mk(table, rows, col="label"):
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} (id serial, {col} text)")
    for r in rows:
        ac.psql(f"INSERT INTO {table} ({col}) VALUES ({ac._vocab_lit(r)})")


def _detect(table, col="label"):
    return ac.vocab_value_detect({table: (["id", col], {"id": "integer", col: "text"})}, None)


# ───────────────────────── the pure parts ─────────────────────────

def test_parse_registers_english_name_sanskrit_name_and_synonyms_keyed_by_casefold():
    reg = ac.vocab_registered_parse(json.dumps([dict(c="planet", id="mars", en="Mars", sa="Mangala", syn=["mangala", "kuja", " pad ", "12", "Kuja\u00a0"])]))
    assert set(reg) == {"mars", "mangala", "kuja"}                                      # padded / NBSP-padded strings and bare numbers are never registered
    assert reg["mangala"]["sources"] == ["canonical_name_sa", "synonyms"] and reg["mars"]["sources"] == ["canonical_name_en"] and reg["kuja"]["classes"] == ["graha"]
    assert reg["mangala"]["forms"] == ["Mangala", "mangala"]


@pytest.mark.parametrize("blob", ["", "null", "[]", "{}", "not json", json.dumps([dict(c="domain", id="x", sa=None, syn=["x"])]), json.dumps(["x"])])
def test_parse_refuses_an_empty_or_malformed_answer(blob):
    with pytest.raises(ac.Unknown):
        ac.vocab_registered_parse(blob)


def test_classify_reads_registered_only_after_the_set_is_loaded_and_by_plain_casefold(monkeypatch):
    ac._VOCAB_REGISTERED = {}
    assert ac.vocab_classify("Mangala")["kind"] == "alias"                               # not loaded / empty: exactly the pre-N-233 reading (stricter)
    ac._VOCAB_REGISTERED = ac.vocab_registered_parse(json.dumps([dict(c="planet", id="mars", en="Mars", sa="Mangala", syn=["mangala"])]))
    for v in ("Mangala", "mangala", "MANGALA", "mAnGaLa"):
        assert ac.vocab_classify(v)["kind"] == "registered", v                           # ruling A: capitalisation is not a spelling variant
    for v in (" Mangala", "Mangala ", "Mangala\u00a0", "\uff2d\uff41\uff4e\uff47\uff41\uff4c\uff41", "Man\u0261ala"):
        assert ac.vocab_classify(v) is None or ac.vocab_classify(v)["kind"] != "registered", v   # padding / NBSP / fullwidth / lookalikes stay unregistered
    assert ac.vocab_classify("Mars")["kind"] == "canonical"                              # a canonical form stays canonical


def test_diacritics_are_not_folded():
    ac._VOCAB_REGISTERED = ac.vocab_registered_parse(json.dumps([dict(c="planet", id="saturn", en="Saturn", sa="Shani", syn=["shani"])]))
    assert ac.vocab_classify("Shani")["kind"] == "registered" and ac.vocab_classify("Sh\u0101ni") is None or ac.vocab_classify("Sh\u0101ni")["kind"] != "registered"


def test_a_registered_alias_that_is_a_canonical_form_is_canonical_not_registered():
    ac._VOCAB_REGISTERED = ac.vocab_registered_parse(json.dumps([dict(c="planet", id="mars", sa="Mars", syn=["Mars"])]))
    assert ac.vocab_classify("Mars")["kind"] == "canonical"


def test_the_registry_text_states_the_rule():
    e = ac.CRITERION_REGISTRY["Vocab.alias"]
    assert "N-233 R2" in e["applicability"] and "REGISTERED ALIAS" in e["applicability"] and "READ from the live table" in e["applicability"] and "CASE-FOLD" in e["applicability"]


# ───────────────────────── real SQL ─────────────────────────

def test_REAL_SQL_registered_aliases_count_as_canonical_and_the_set_is_read_live(monkeypatch, disposable_pg):
    _seed(disposable_pg, monkeypatch)
    t = "n233_a"
    try:
        _mk(t, ["Sun", "Mangala", "Surya", "mangala", "MANGALA", "Mula", "Shani", "jupiTER"])
        rec = _detect(t)
        assert rec["v"] == PASS, rec["measured"]
        f = rec["vocab_values"]["found"][0]
        assert f["spellings"] == [] and {"Mangala", "Shani", "Surya"} <= set(f["registered"]) and "registered bg_ontology alias" in rec["measured"]
        # MUTATION: delete the registered row of Mars from the live table: the SAME data now reads FAIL (the set is read at measure time, not hard-coded)
        ac.psql("DELETE FROM brahma_ontology WHERE canonical_id = 'mars'")
        ac._VOCAB_REGISTERED = None
        rec = _detect(t)
        assert rec["v"] == FAIL and "Mangala" in rec["measured"] and "MANGALA" in rec["measured"], rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


@pytest.mark.parametrize("bad", [" Mangala", "Kuja ", "Mangala\u00a0", "mangalaa"])
def test_REAL_SQL_an_unregistered_variant_stays_a_real_fail(monkeypatch, disposable_pg, bad):
    _seed(disposable_pg, monkeypatch)
    t = "n233_b"
    try:
        _mk(t, ["Sun", "Mangala", bad])
        rec = _detect(t)
        if bad == "mangalaa":                                   # not even a known form: no finding at all about it (the column is the canonical + registered values only)
            assert rec["v"] == PASS, rec["measured"]
        else:
            assert rec["v"] == FAIL and repr(bad) in rec["measured"], rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_storage_codes_the_ontology_does_not_register_are_still_a_fail(monkeypatch, disposable_pg):
    _seed(disposable_pg, monkeypatch)
    t = "n233_c"
    try:
        _mk(t, ["JU", "KE", "MA", "ME", "MO", "RA"], col="fact_kind")
        rec = _detect(t, "fact_kind")
        assert rec["v"] == FAIL and "'JU'" in rec["measured"], rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_registered_house_storage_codes_pass(monkeypatch, disposable_pg):
    _seed(disposable_pg, monkeypatch)
    t = "n233_d"
    try:
        _mk(t, ["HOUSE_01", "HOUSE_7", "house_1"], col="fact_subject")
        rec = _detect(t, "fact_subject")
        assert rec["v"] in (PASS, FAIL)
        sp = rec["vocab_values"]["found"][0]["spellings"]
        assert "HOUSE_01" not in sp and "HOUSE_7" not in sp                                 # registered by the ontology's own storage-code synonyms
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_registered_alias_beyond_the_sample_is_graded_like_one_inside_it(monkeypatch, disposable_pg):
    """The existence read of an incomplete column (SQL `spell` category) must exclude the registered set exactly as the Python classifier does."""
    _seed(disposable_pg, monkeypatch)
    t = "n233_e"
    try:
        ac.psql(f"DROP TABLE IF EXISTS {t}")
        ac.psql(f"CREATE TABLE {t} (id serial, label text)")
        ac.psql(f"INSERT INTO {t} (label) SELECT 'Sun' FROM generate_series(1, {ac.VOCAB_SAMPLE_ROWS + 50})")
        ac.psql(f"INSERT INTO {t} (label) VALUES ('Mangala')")
        rec = _detect(t)
        assert rec["v"] == PASS, rec["measured"]
        ac.psql(f"INSERT INTO {t} (label) VALUES ('JU'), ('KE')")                 # unregistered short codes beyond the sample
        rec = _detect(t)
        assert rec["v"] == FAIL and "'JU'" in rec["measured"], rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_an_empty_or_missing_alias_table_is_no_detector_never_a_verdict(monkeypatch, disposable_pg):
    t = "n233_f"
    _seed(disposable_pg, monkeypatch, rows=[])
    try:
        _mk(t, ["Sun", "Mangala"])
        rec = _detect(t)
        assert rec["v"] == NO_DET and "registered alias set" in rec["measured"], rec
        ac.psql("DROP TABLE brahma_ontology")
        ac._VOCAB_REGISTERED = None
        rec = _detect(t)
        assert rec["v"] == NO_DET and "registered alias set" in rec["measured"], rec
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")
