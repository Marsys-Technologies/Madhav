"""test_n176_vocab_values.py: the VALUE-BASED Vocab.alias detector (SS N-176, 2026-10-07).

Vocab.alias was decided by column NAMES (ALIAS_VOCAB_COLUMNS) and by hand declarations (`vocab_alias: no_alias_class`); 67 assets read NO_DETECTOR because the audits removed the false declarations. The check now
applies to an asset if ANY column's VALUES fall in the canonical graha / rashi / nakshatra / bhava vocabulary: a bounded, read-only sample of every text-capable or json(b) column of the asset's owned tables,
matched against the vocabularies the repo already holds. A name (`*_lord`, `planet_id`) only ORDERS the reads; a `no_alias_class` declaration is ADVISORY; a column that could not be sampled reads NO_DETECTOR, never N/A.

Proved here on a DISPOSABLE PostgreSQL: planet names in a text column named innocently (`label`); in a jsonb leaf; none present (N/A with its evidence block); a column that cannot be sampled (NO_DETECTOR); a
`*_lord` column holding non-vocabulary ids (a hint only: no false verdict); canonical vs non-canonical spellings; a sampled-only large table (the existence read); the lexicon is the repo's own (nothing invented);
the merge with the older readings; the rollup guard; every statement bounded.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
ALIAS = "Vocab.alias"
TIMEOUT = "ERROR:  canceling statement due to statement timeout"
TYPES = {"id": "integer", "label": "text", "doc": "jsonb", "tags": "ARRAY", "score": "numeric", "at": "timestamp with time zone", "dasha_lord": "text", "star_lord": "text",
         "note": "text", "kind": "USER-DEFINED"}


def _mk(pg, monkeypatch, table, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {table} VALUES ({r})")


def _own(table, ddl_types):
    return {table: (list(ddl_types), dict(ddl_types))}


def _detect(table, types, declared=None, udts=None):
    return ac.vocab_value_detect(_own(table, types), udts, declared=declared)


# ───────────────────────── the lexicon is the repo's own ─────────────────────────

def test_the_canonical_vocabularies_are_read_from_the_repo_not_invented():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_t_ont", ac.SIDECAR / "brahmagyan" / "l0_ontology.py")
    ont = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ont)
    lex = ac.vocab_lexicon()
    for cls_e, cls in (("planet", "graha"), ("sign", "rashi"), ("nakshatra", "nakshatra"), ("house", "bhava")):
        ents = [e for e in ont.ENTITIES if e["entity_class"] == cls_e]
        assert ents, cls_e
        for e in ents:
            assert e["canonical_id"] in lex["canonical"][cls] and e["canonical_name_en"] in lex["canonical"][cls], (cls, e["canonical_id"])
            for sy in e["synonyms"]:                                    # every alias spelling the ontology holds is a known (non-canonical or canonical) form of its class
                assert cls in lex["keys"].get(ac._norm_form(sy), ()) or re.fullmatch(r"[0-9]+", sy), (cls, sy)
    assert len([e for e in ont.ENTITIES if e["entity_class"] == "nakshatra"]) == 27 and len([e for e in ont.ENTITIES if e["entity_class"] == "sign"]) == 12
    sr = ac._load_sidecar_module("brahmagyan/l0_semantic_release.py", "_t_rel")
    for ent in sr.SEMANTIC_RELEASE["entities"]:                         # the graha identities the normaliser (norm_graha) accepts: the released codes and labels are canonical, every alias a known form
        assert ent["canonical_subject_code"] in lex["canonical"]["graha"] and ent["canonical_label"] in lex["canonical"]["graha"]
        for al in ent["aliases"]:
            assert "graha" in lex["keys"][ac._norm_form(al)], al


@pytest.mark.parametrize("value,kind,cls", [("Sun", "canonical", "graha"), ("SUN", "canonical", "graha"), ("MAR", "canonical", "graha"), ("Mars", "canonical", "graha"),
                                            ("MARS", "alias", "graha"), ("mangala", "alias", "graha"), ("Shani", "alias", "graha"), (" Sun ", "alias", "graha"),
                                            ("Aries", "canonical", "rashi"), ("aries", "canonical", "rashi"), ("Mesha", "alias", "rashi"), ("ARIES", "alias", "rashi"),
                                            ("Ashwini", "canonical", "nakshatra"), ("nak_01_ashwini", "canonical", "nakshatra"), ("ashwini", "alias", "nakshatra"),
                                            ("house_01", "canonical", "bhava"), ("First House", "canonical", "bhava"), ("lagna_bhava", "alias", "bhava")])
def test_classification_canonical_versus_non_canonical_spelling(value, kind, cls):
    got = ac.vocab_classify(value)
    assert got is not None and got["kind"] == kind and cls in got["classes"], (value, got)


@pytest.mark.parametrize("value", ["", "   ", "foo", "a free sentence about Mars and Saturn", "12", "uuid-1111", None, 3, "the Sun rose"])
def test_a_value_that_is_no_term_is_no_vocabulary(value):
    assert ac.vocab_classify(value) is None


def test_a_short_alias_never_makes_a_column_carry_vocabulary_by_itself():
    assert ac.vocab_classify("SA")["detect"] is False and ac.vocab_classify("MA")["detect"] is False and ac.vocab_classify("H1")["detect"] is False
    assert ac.vocab_classify("Sun")["detect"] is True and ac.vocab_classify("MARS")["detect"] is True


# ───────────────────────── every statement is bounded ─────────────────────────

@pytest.mark.parametrize("kind", ["text", "enum", "array", "json"])
def test_the_sample_statement_is_bounded_and_counts_only_the_sample(kind):
    sql = ac.vocab_sample_sql("big_t", "c", kind)
    assert 'FROM "big_t"' in sql and sql.count('FROM "big_t"') == 1 and re.search(r"LIMIT (2000|200)\b", sql)
    assert "ORDER BY" not in sql.upper() and "GROUP BY" not in sql.upper() and 'count(*) FROM "big_t"' not in sql          # the only count(*) is over the LIMITed sample CTE
    assert "SELECT count(*) FROM s" in sql or "SELECT count(*) FROM r" in sql


def test_the_batch_statement_bounds_every_column_and_the_spelling_read_stops_at_its_limit():
    sql = ac.vocab_batch_sql("big_t", [("a", "text"), ("b", "array"), ("c", "json")])
    assert sql.count('FROM "big_t"') == 3 and sql.count(" LIMIT ") >= 3 and all(f"'{c}'," in sql for c in "abc")
    sp = ac.vocab_spelling_sql("big_t", "a", "text")
    assert f"LIMIT {ac.VOCAB_SPELLING_SAMPLE}) s" in sp and "count(" not in sp and "ORDER BY" not in sp.upper() and sp.count('FROM "big_t"') == 1


# ───────────────────────── real SQL: planet names under an innocent column name ─────────────────────────

def test_REAL_SQL_planet_names_in_a_text_column_named_label_are_found_and_graded_canonical(monkeypatch, disposable_pg):
    t = "n176_a"
    _mk(disposable_pg, monkeypatch, t, "id int, label text, score numeric", ["1,'Sun',1.5", "2,'Moon',2", "3,'Sun',3", "4,NULL,4"])
    try:
        rec = _detect(t, {"id": "integer", "label": "text", "score": "numeric"})
        assert rec["v"] == PASS, rec["measured"]                         # values found by value: not N/A, and every one canonical (the whole column was read)
        f = rec["vocab_values"]["found"]
        assert [(x["table"], x["column"], x["classes"], x["canonical"], x["spellings"]) for x in f] == [(t, "label", ["graha"], ["Moon", "Sun"], [])]
        assert rec["vocab_values"]["unread"] == [] and rec["vocab_values"]["rows_sampled"][f"{t}.label"] == 3 and f"{t}.label" in rec["vocab_values"]["complete_columns"]
        assert "label" in rec["measured"] and rec.get("cause") is None
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_non_canonical_spelling_is_a_fail_named_with_its_column(monkeypatch, disposable_pg):
    t = "n176_b"
    _mk(disposable_pg, monkeypatch, t, "id int, label text", ["1,'Sun'", "2,'MARS'", "3,'mangala'", "4,'Moon'"])
    try:
        rec = _detect(t, {"id": "integer", "label": "text"})
        assert rec["v"] == FAIL and "non-canonical spelling" in rec["measured"] and "'MARS'" in rec["measured"] and f"{t}.label" in rec["measured"]
        assert rec["vocab_values"]["found"][0]["spellings"] == ["MARS", "mangala"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_rashi_nakshatra_and_bhava_values_are_found_too(monkeypatch, disposable_pg):
    t = "n176_c"
    _mk(disposable_pg, monkeypatch, t, "id int, a text, b text, c text", ["1,'Aries','Ashwini','house_01'", "2,'Taurus','Bharani','house_02'"])
    try:
        rec = _detect(t, {"id": "integer", "a": "text", "b": "text", "c": "text"})
        assert rec["v"] == PASS
        got = {x["column"]: x["classes"] for x in rec["vocab_values"]["found"]}
        assert got == {"a": ["rashi"], "b": ["nakshatra"], "c": ["bhava"]}
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_vocabulary_value_in_a_jsonb_leaf_is_found(monkeypatch, disposable_pg):
    t = "n176_d"
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", ["1,'{\"a\":{\"b\":[\"Mars\",\"Venus\"]},\"n\":3}'::jsonb", "2,'{\"x\":\"plain words\"}'::jsonb", "3,NULL"])
    try:
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] == PASS and rec["vocab_values"]["found"][0]["column"] == "doc" and rec["vocab_values"]["found"][0]["canonical"] == ["Mars", "Venus"]
        t2 = "n176_d2"
        _mk(disposable_pg, monkeypatch, t2, "id int, doc jsonb", ["1,'{\"a\":{\"b\":\"SATURN\"}}'::jsonb"])
        rec2 = _detect(t2, {"id": "integer", "doc": "jsonb"})
        assert rec2["v"] == FAIL and "'SATURN'" in rec2["measured"]
        ac.psql(f"DROP TABLE IF EXISTS {t2}")
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_text_array_column_is_read_by_its_elements(monkeypatch, disposable_pg):
    t = "n176_e"
    _mk(disposable_pg, monkeypatch, t, "id int, tags text[]", ["1,ARRAY['Sun','free text']", "2,ARRAY['Moon']"])
    try:
        rec = _detect(t, {"id": "integer", "tags": "ARRAY"}, udts={t: {"tags": "_text"}})
        assert rec["v"] == PASS and rec["vocab_values"]["found"][0]["canonical"] == ["Moon", "Sun"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────── none present: N/A with the evidence block ─────────────────────────

def test_REAL_SQL_no_vocabulary_value_in_any_column_reads_na_with_the_columns_read_and_rows_sampled(monkeypatch, disposable_pg):
    t = "n176_f"
    _mk(disposable_pg, monkeypatch, t, "id int, label text, doc jsonb, score numeric", ["1,'weights','{\"k\":\"v\"}'::jsonb,1", "2,'a sentence of prose','{\"k\":3}'::jsonb,2", "3,NULL,NULL,3"])
    try:
        rec = _detect(t, {"id": "integer", "label": "text", "doc": "jsonb", "score": "numeric"})
        assert rec["v"] == NA and rec["cause"] == "no-vocabulary-values"
        b = rec["vocab_values"]
        assert b["checked"] is True and b["found"] == [] and b["unread"] == [] and b["tables"] == [t] and b["columns_read"] == 2
        assert b["rows_sampled"] == {f"{t}.label": 2, f"{t}.doc": 2} and sorted(b["complete_columns"]) == [f"{t}.doc", f"{t}.label"]
        assert "rows sampled" in rec["measured"] and f"{t}.label 2" in rec["measured"]
        # the rollup releases it only with the checked block, under the declared rule
        c = ac._check_contribution(ALIAS, "L0", rec, None)
        assert c["v"] == NA and c["rule_id"] == "Vocab.alias#measured:no-vocabulary-values" and c["decision"].startswith("N-176")
        bare = {k: v for k, v in rec.items() if k != "vocab_values"}
        assert ac._check_contribution(ALIAS, "L0", bare, None)["v"] == NO_DET
        assert not ac._na_released(ALIAS, bare) and ac._na_released(ALIAS, rec)
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_lord_column_of_non_vocabulary_ids_is_a_hint_only_no_false_verdict(monkeypatch, disposable_pg):
    t = "n176_g"
    _mk(disposable_pg, monkeypatch, t, "id int, dasha_lord text, star_lord text, label text",
        ["1,'11111111-2222-3333-4444-555555555555','a1b2c3','prose'", "2,'22222222-2222-3333-4444-555555555555','d4e5f6','more prose'"])
    try:
        cands, _p = ac.vocab_candidate_columns(_own(t, {"id": "integer", "dasha_lord": "text", "star_lord": "text", "label": "text"}))
        assert [c for _t, c, _k in cands][:2] == ["dasha_lord", "star_lord"]                          # the NAME orders the reads: *_lord first
        rec = _detect(t, {"id": "integer", "dasha_lord": "text", "star_lord": "text", "label": "text"})
        assert rec["v"] == NA and rec["vocab_values"]["found"] == []                                  # ... and decides nothing: no vocabulary value anywhere
        t2 = "n176_g2"
        _mk(disposable_pg, monkeypatch, t2, "id int, dasha_lord text, note text", ["1,'Venus','x'", "2,'Saturn','y'"])
        rec2 = _detect(t2, {"id": "integer", "dasha_lord": "text", "note": "text"})
        assert rec2["v"] == PASS and [x["column"] for x in rec2["vocab_values"]["found"]] == ["dasha_lord"]
        ac.psql(f"DROP TABLE IF EXISTS {t2}")
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_an_empty_table_is_vacuous_no_detector_never_na(monkeypatch, disposable_pg):
    t = "n176_h"
    _mk(disposable_pg, monkeypatch, t, "id int, label text", [])
    try:
        rec = _detect(t, {"id": "integer", "label": "text"})
        assert rec["v"] == NO_DET and "vacuous" in rec["measured"] and rec["v"] != NA
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────── a column that cannot be sampled: NO_DETECTOR, never N/A ─────────────────────────

def test_REAL_SQL_an_oversized_json_value_cannot_be_called_free_of_vocabulary(monkeypatch, disposable_pg):
    t = "n176_i"
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", ["1,'{\"k\":\"" + "x" * 400 + "\"}'::jsonb", "2,'{\"k\":\"v\"}'::jsonb"])
    try:
        monkeypatch.setattr(ac, "VOCAB_JSON_MAX_BYTES", 100)                                         # the 'huge' document (a real one is 262144 bytes)
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] == NO_DET and rec["v"] != NA and "could not be sampled" in rec["measured"] and "larger than 100 bytes" in rec["measured"]
        assert rec["vocab_values"]["unread"] and rec["vocab_values"]["found"] == []
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_too_deep_document_is_unsampled_too(monkeypatch, disposable_pg):
    t = "n176_j"
    deep = '{"a":' * 12 + '"Mars"' + "}" * 12
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", [f"1,'{deep}'::jsonb"])
    try:
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] == NO_DET and "deeper than" in rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_a_column_whose_sample_times_out_is_unread_no_detector_and_the_others_are_still_read(monkeypatch):
    def scalar(q):
        if "jsonb_build_object('rows'" in q and '"slow"' in q and "'label'" not in q:          # the per-column retry of the slow column
            raise ac.Unknown(TIMEOUT)
        if q.startswith("SELECT jsonb_build_object('label'"):
            raise ac.Unknown(TIMEOUT)                                                             # the batch fails (one hostile column), so each column is retried alone
        if '"label"' in q:
            return json.dumps(dict(rows=2, values=["prose", "more"]))
        raise AssertionError(q[:80])
    monkeypatch.setattr(ac, "scalar", scalar)
    rec = ac.vocab_value_detect({"t": (["id", "label", "slow"], {"id": "integer", "label": "text", "slow": "text"})})
    assert rec["v"] == NO_DET and "exceeded the statement timeout" in rec["measured"] and "t.slow" in rec["measured"] and rec["v"] != NA
    assert rec["vocab_values"]["columns_read"] == 1                                                  # `label` was read despite `slow`


def test_a_failed_read_with_a_value_found_elsewhere_is_partial_not_pass(monkeypatch):
    def scalar(q):
        if q.startswith("SELECT jsonb_build_object("):
            raise ac.Unknown(TIMEOUT)
        if '"slow"' in q:
            raise ac.Unknown("ERROR:  canceling statement due to statement timeout")
        return json.dumps(dict(rows=1, values=["Sun"]))
    monkeypatch.setattr(ac, "scalar", scalar)
    rec = ac.vocab_value_detect({"t": (["a", "slow"], {"a": "text", "slow": "text"})})
    assert rec["v"] == PARTIAL and "not the whole asset was read" in rec["measured"]


def test_a_vocabulary_source_that_cannot_be_loaded_is_no_detector(monkeypatch):
    monkeypatch.setattr(ac, "_VOCAB_LEX", None)
    monkeypatch.setattr(ac, "SIDECAR", pathlib.Path("/nonexistent/sidecar"))
    rec = ac.vocab_value_detect({"t": (["a"], {"a": "text"})})
    assert rec["v"] == NO_DET and "canonical vocabularies" in rec["measured"]


def test_unread_columns_or_types_are_a_problem_never_no_candidate():
    rec = ac.vocab_value_detect({"t": (None, None)})
    assert rec["v"] == NO_DET and rec["v"] != NA
    rec = ac.vocab_value_detect({"t": (["a", "b"], {"a": "text"})})
    assert rec["v"] == NO_DET and "no type read" in rec["measured"]


# ───────────────────────── sampled-only reads: the existence read decides the rest ─────────────────────────

def test_REAL_SQL_a_large_table_canonical_in_the_sample_and_clean_after_it_is_pass_by_the_existence_read(monkeypatch, disposable_pg):
    t = "n176_k"
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    _mk(disposable_pg, monkeypatch, t, "id int, label text", [f"{i},'Sun'" for i in range(12)])
    try:
        rec = _detect(t, {"id": "integer", "label": "text"})
        f = rec["vocab_values"]["found"][0]
        assert f["complete"] is False and f["spelling_read"] == dict(found=False, sample=[]) and rec["v"] == PASS and f"{t}.label" not in rec["vocab_values"]["complete_columns"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_late_non_canonical_spelling_beyond_the_sample_is_found_by_the_existence_read(monkeypatch, disposable_pg):
    t = "n176_l"
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    _mk(disposable_pg, monkeypatch, t, "id int, label text", [f"{i},'Sun'" for i in range(12)] + ["99,'MARS'"])
    try:
        rec = _detect(t, {"id": "integer", "label": "text"})
        assert rec["v"] == FAIL and rec["vocab_values"]["found"][0]["spelling_read"]["found"] is True and "'MARS'" in rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_large_json_column_canonical_in_the_sample_is_partial_never_pass(monkeypatch, disposable_pg):
    t = "n176_m"
    monkeypatch.setattr(ac, "VOCAB_JSON_SAMPLE_ROWS", 3)
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", [f"{i},'{{\"g\":\"Sun\"}}'::jsonb" for i in range(8)])
    try:
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] == PARTIAL and "bounded sample only" in rec["measured"]                      # json(b) has no existence read: the rest of the table is unread
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_a_failed_batch_is_retried_per_column_so_one_hostile_column_cannot_hide_the_others(monkeypatch):
    seen = []

    def scalar(q):
        seen.append(q)
        if q.startswith("SELECT jsonb_build_object('a'"):
            raise ac.Unknown('ERROR:  cannot cast type "b"')
        if '"b"' in q:
            raise ac.Unknown("ERROR:  something else failed")
        return json.dumps(dict(rows=1, values=["Sun"]))
    monkeypatch.setattr(ac, "scalar", scalar)
    got = ac.vocab_fetch_samples("t", [("a", "text"), ("b", "text"), ("c", "text")])
    assert got["a"]["values"] == ["Sun"] and got["c"]["values"] == ["Sun"] and "the bounded sample failed" in got["b"]["unread"]
    assert len(seen) == 4                                                                             # one batch, then one statement per column


# ───────────────────── the merge with the older readings (declarations are advisory) ─────────────────────

NA_DECL = dict(na="no_alias_class", why="its columns are own identifiers and scores: no vocabulary", evidence="platform/scripts/governance/asset_census.py:1")
FOUND = dict(v=PASS, measured="found", vocab_values=dict(checked=True))
NONE_FOUND = dict(v=NA, measured="none", cause="no-vocabulary-values", vocab_values=dict(checked=True))


def test_an_undeclared_asset_takes_the_value_reading():
    assert ac.vocab_value_merge(None, None, FOUND, True) is FOUND
    assert ac.vocab_value_merge(None, None, None, True) is None                                       # the reading did not run: nothing changes


def test_a_declared_no_alias_class_is_overridden_by_the_data_both_ways():
    declared_na = dict(v=NA, cause="no-alias-class", measured="declared", declared=True)
    assert ac.vocab_value_merge(declared_na, NA_DECL, FOUND, True) is FOUND                           # values present: not N/A, whatever the declaration says
    assert ac.vocab_value_merge(declared_na, NA_DECL, NONE_FOUND, True) is NONE_FOUND                 # none present: N/A by the VALUE reading (its evidence block), not by the declaration
    nd = dict(v=NO_DET, declared=True, declaration_disagreements=[dict(field="vocab_alias.na", measured="the table carries ontology-aliased vocabulary column(s) ['graha']")], measured="x")
    assert ac.vocab_value_merge(nd, NA_DECL, NONE_FOUND, True) is NONE_FOUND                          # the NAME-based refusal decides nothing any more


def test_a_declared_no_alias_class_stays_for_an_asset_with_no_readable_table():
    declared_na = dict(v=NA, cause="no-alias-class", measured="declared", declared=True)
    assert ac.vocab_value_merge(declared_na, NA_DECL, NONE_FOUND, False) is declared_na


def test_a_documented_alias_set_and_a_declared_measured_class_keep_their_own_readings():
    alias_like = dict(v=NO_DET, declared=True, declaration_disagreements=[dict(field="vocab_alias.na", measured="the table carries alias-like column(s) ['synonyms']")], measured="x")
    assert ac.vocab_value_merge(alias_like, NA_DECL, FOUND, True) is alias_like                       # N-73 (4): a documented alias set is a hard disagreement
    measured = dict(v=PASS, declared=True, alias={}, measured="alias census")
    va = dict(**{"class": "planet"}, vocab_column="graha", why="x" * 20, evidence="y")
    assert ac.vocab_value_merge(measured, va, FOUND, True) is measured
    legacy = dict(v=PASS, measured="2 class(es); 0/9 row(s) lack an alias set")
    assert ac.vocab_value_merge(legacy, None, FOUND, True) is legacy


def test_the_declared_form_function_is_unchanged_it_is_the_existing_identity_alias_reading():
    """ALIAS_VOCAB_COLUMNS stays only as the declared-form reading (`vocab_alias_declared_check`); measure() lets the value reading override it."""
    rec = ac.vocab_alias_declared_check("x", NA_DECL, "t", ["id", "graha"])[ALIAS]
    assert rec["v"] == NO_DET and "N-150 R3" in rec["measured"]
    assert ac.ALIAS_VOCAB_COLUMNS == ("graha", "grahas", "planet", "planet_name", "other_graha", "star_lord", "sub_lord", "lord")


# ───────────────────────── the advisory note and the registry ─────────────────────────

def test_a_declared_no_alias_class_is_named_as_advisory_on_the_value_record(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: json.dumps(dict(rows=2, values=["prose", "more"])))
    rec = ac.vocab_value_detect({"t": (["a"], {"a": "text"})}, declared=NA_DECL)
    assert rec["v"] == NA and rec["declared_advisory"]["declared"] == "no_alias_class" and "the data decides" in rec["declared_advisory"]["overridden_by"]


def test_the_registry_carries_the_value_rule_its_revision_and_its_cause():
    e = ac.CRITERION_REGISTRY[ALIAS]
    assert e["revision"] == 4 and "N-176" in e["applicability"] and "VALUE-keyed" in e["applicability"] and "no-vocabulary-values" in e["applicability"]
    assert "no-vocabulary-values" in ac.NA_CAUSES[ALIAS] and "Vocab.alias#measured:no-vocabulary-values" in ac.NA_RULE_DECISIONS
    assert ac.CRITERION_REGISTRY["Vocab.identity"]["revision"] == 2                                   # untouched
    assert ac.REGISTRY_REVISION == 26


def test_every_grade_branch_of_the_pure_record_is_reachable_and_na_needs_a_row_seen():
    col = dict(table="t", column="c", kind="text", rows_sampled=0, complete=True, carries=False, read="whole column")
    assert ac.vocab_values_record([col], [], ["t"])["v"] == NO_DET                                  # 0 rows: vacuous
    col1 = dict(col, rows_sampled=4)
    assert ac.vocab_values_record([col1], [], ["t"])["v"] == NA
    assert ac.vocab_values_record([col1], ["t.x: not read"], ["t"])["v"] == NO_DET
    assert ac.vocab_values_record([], [], ["t"])["v"] == NO_DET                                      # no candidate column read at all: nothing seen, never N/A


# ───────────────────────── measure(): the wiring on the real path ─────────────────────────

def _measure_vocab(monkeypatch, tmp_path, *, declared, batch_answer, tables=None, aid="bg_x", target="vt"):
    """measure() over one L0 asset whose table has a `label` text column; the vocabulary batch read answers `batch_answer` (a {column: sample} object)."""
    import test_e6_n99_build_completion_integrity as n99
    cols = ["id", "label", "score"]
    reg = {aid: dict(n99._reg_row(aid, has_integrity=False), target_table=target, count_sql=f"SELECT count(*) FROM {target}")}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=5)
    types = {"id": "integer", "label": "text", "score": "numeric"}
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={target}, cols={target: cols}, keys={target: [["id"]]}, views=set(), types={target: types}, defaults={target: {}}, types_error=None, udts={}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: ({aid: dict(kind="data", vocab_alias=declared)} if declared else {aid: dict(kind="data")}))
    seen = []

    def fake_psql(sql, sep="\x1f", timeout=None):
        if sql.startswith("SELECT jsonb_build_object('label'"):
            seen.append(sql)
            return [[json.dumps(batch_answer)]]
        if "format_type(a.atttypid" in sql:
            return [["text"]]
        if "IS NOT NULL" in sql:
            return [["5"]]
        if "EXISTS" in sql:
            return [["f"]]
        return []
    monkeypatch.setattr(ac, "psql", fake_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (fake_psql(sql) or [[None]])[0][0])
    m = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}[aid]
    return m[ALIAS], seen


def test_measure_an_undeclared_asset_with_planet_names_under_an_innocent_column_is_graded_by_value(monkeypatch, tmp_path):
    rec, seen = _measure_vocab(monkeypatch, tmp_path, declared=None, batch_answer=dict(label=dict(rows=3, values=["Sun", "Moon"])))
    assert rec["v"] == PASS and rec["vocab_values"]["found"][0]["column"] == "label" and len(seen) == 1
    assert 'FROM "vt"' in seen[0] and "LIMIT 2000" in seen[0]                                         # the read ran, bounded


def test_measure_a_declared_no_alias_class_is_overridden_when_the_data_holds_vocabulary(monkeypatch, tmp_path):
    na = dict(na="no_alias_class", why="its columns are own identifiers and scores: no vocabulary", evidence="platform/scripts/governance/asset_census.py:1")
    rec, _ = _measure_vocab(monkeypatch, tmp_path, declared=na, batch_answer=dict(label=dict(rows=2, values=["MARS", "Moon"])))
    assert rec["v"] == FAIL and rec.get("cause") is None and rec["declared_advisory"]["declared"] == "no_alias_class"       # not N/A, whatever the declaration says


def test_measure_a_declared_no_alias_class_reads_na_only_through_the_value_evidence(monkeypatch, tmp_path):
    na = dict(na="no_alias_class", why="its columns are own identifiers and scores: no vocabulary", evidence="platform/scripts/governance/asset_census.py:1")
    rec, _ = _measure_vocab(monkeypatch, tmp_path, declared=na, batch_answer=dict(label=dict(rows=2, values=["weights", "prose"])))
    assert rec["v"] == NA and rec["cause"] == "no-vocabulary-values" and rec["vocab_values"]["rows_sampled"] == {"vt.label": 2}      # the VALUE reading released it, with its evidence block


def test_measure_a_failed_read_never_reads_na_even_beside_a_declaration(monkeypatch, tmp_path):
    na = dict(na="no_alias_class", why="its columns are own identifiers and scores: no vocabulary", evidence="platform/scripts/governance/asset_census.py:1")
    rec, _ = _measure_vocab(monkeypatch, tmp_path, declared=na, batch_answer={"nope": 1})            # the batch answer does not carry the column: the per-column retry then finds nothing parseable either
    assert rec["v"] == NO_DET and rec["v"] != NA


@pytest.mark.parametrize("col,rank", [("dasha_lord", 0), ("star_lord", 0), ("planet_id", 0), ("graha", 0), ("lord_sign", 0), ("fact_subject", 0), ("label", 1), ("dvara_assignment", 1), ("signature_tier", 1), ("designation", 1)])
def test_a_name_hint_is_a_whole_name_token_and_only_orders_the_reads(col, rank):
    assert ac.vocab_hint_rank(col) == rank
