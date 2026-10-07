"""test_n176_vocab_values_review.py: the independent review of the value-based Vocab.alias detector (N-176): HIGH-1 .. HIGH-4 and MED-5.

HIGH-1  an INCOMPLETE column (the sample is not the whole column) that showed nothing is UNSAMPLED: an existence PROBE of the whole column decides, and only a probe that reaches the end empty lets it count.
HIGH-2  the nine short abbreviations (Su Mo Ma Me Ju Ve Sa Ra Ke) are a vocabulary column, one of them alone is a WEAK signal (PARTIAL), never N/A.
HIGH-3  vocabulary INSIDE longer text (`Sun in 7th house`, `graha=Sun,sign=Aries`, `Mutual Reception: Sun <-> Moon`, `sun_in_aries`) and json KEYS (`{"planet": 5}`) are PARTIAL 'embedded vocabulary, spelling unchecked', never N/A.
HIGH-4  the SQL predicates use the SAME normalisation as the Python classifier (a differential test over 40 spellings on a real PostgreSQL).
MED-5   one canonical spelling FAMILY per column: `Moon` and `MOON` in one column is PARTIAL, not PASS.
All on a DISPOSABLE PostgreSQL (real tables, `point_psql_at`); the cap constants are lowered with monkeypatch so a 12-row table stands for the 2000-row sample.
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
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
TIMEOUT = "ERROR:  canceling statement due to statement timeout"


def _mk(pg, monkeypatch, table, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {table} VALUES ({r})")


def _detect(table, types):
    return ac.vocab_value_detect({table: (list(types), dict(types))})


def _text_table(pg, monkeypatch, name, values, ddl="id int, label text"):
    _mk(pg, monkeypatch, name, ddl, [f"{i}, {v}" for i, v in enumerate(values)])
    return {"id": "integer", "label": "text"}


def _q(s):
    return "'" + s.replace("'", "''") + "'"


# ───────────────────────── HIGH-1: an incomplete column is UNSAMPLED until a probe reaches its end ─────────────────────────

def test_REAL_SQL_a_term_only_beyond_the_sample_is_found_by_the_probe_not_read_as_na(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    t = "n176r_a"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(f"filler {i}") for i in range(8)] + ["'Sun'"] + [_q(f"filler {i}") for i in range(8, 12)])
    try:
        rec = _detect(t, types)
        assert rec["v"] != NA and rec["v"] in (PASS, PARTIAL) and rec["vocab_values"]["found"][0]["canonical"] == ["Sun"]        # row 9 of 14 is past the 5-row sample
        assert rec["vocab_values"]["found"][0]["complete"] is False
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_text_array_whose_first_rows_lack_the_term_is_probed(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 3)
    t = "n176r_b"
    _mk(disposable_pg, monkeypatch, t, "id int, tags text[]", [f"{i}, ARRAY['x{i}','y']" for i in range(6)] + ["99, ARRAY['z','Moon']"])
    try:
        rec = _detect(t, {"id": "integer", "tags": "ARRAY"})
        assert rec["v"] != NA and rec["vocab_values"]["found"][0]["canonical"] == ["Moon"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_jsonb_column_whose_first_rows_lack_the_term_is_probed(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_JSON_SAMPLE_ROWS", 3)
    t = "n176r_c"
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", [f"{i}, '{{\"k\":\"v{i}\"}}'::jsonb" for i in range(6)] + ["99, '{\"g\":{\"p\":\"Venus\"}}'::jsonb"])
    try:
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] != NA and rec["vocab_values"]["found"][0]["canonical"] == ["Venus"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_distinct_value_list_that_overflows_does_not_drop_the_term_at_random(monkeypatch, disposable_pg):
    """The sample keeps at most VOCAB_MAX_VALUES distinct values (DISTINCT ... LIMIT drops the rest in no defined order): the term can be among the dropped ones, so the column is incomplete and probed."""
    monkeypatch.setattr(ac, "VOCAB_MAX_VALUES", 20)
    t = "n176r_d"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(f"distinct filler {i:04d}") for i in range(60)] + ["'Sun'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] != NA and rec["vocab_values"]["found"][0]["canonical"] == ["Sun"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_an_incomplete_clean_column_is_na_only_through_a_probe_that_reached_its_end(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    t = "n176r_e"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(f"plain filler {i}") for i in range(12)])
    try:
        rec = _detect(t, types)
        b = rec["vocab_values"]
        assert rec["v"] == NA and rec["cause"] == "no-vocabulary-values" and b["probed_columns"] == [f"{t}.label"] and b["complete_columns"] == [f"{t}.label"]
        assert "existence probe that reached the end" in rec["measured"] and "WHAT WAS SEARCHED" in rec["measured"] and "NOT searched" in rec["measured"]
        assert ac._check_contribution("Vocab.alias", "L0", rec, None)["v"] == NA
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_an_incomplete_column_whose_probe_is_cancelled_or_fails_is_no_detector_never_na(monkeypatch):
    for err in (ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)"), ac.Unknown("ERROR:  something else")):
        def scalar(q, err=err):
            if "'values'" in q:
                return json.dumps(dict(rows=ac.VOCAB_SAMPLE_ROWS, values=["filler"], emb=[]))              # a FULL sample: not the whole column
            raise err
        monkeypatch.setattr(ac, "scalar", scalar)
        rec = ac.vocab_value_detect({"t": (["a"], {"a": "text"})})
        assert rec["v"] == NO_DET and rec["v"] != NA and "t.a" in rec["measured"] and ("the rest of the column was not read" in rec["measured"])


def test_a_json_column_the_probe_found_oversized_or_too_deep_is_unsampled(monkeypatch):
    def scalar(q):
        if "'values'" in q:
            return json.dumps(dict(rows=ac.VOCAB_JSON_SAMPLE_ROWS, values=["v"], emb=[], oversized=0, deep=0, leaves=1, keys=1, key_hits=[]))
        return json.dumps(dict(hits=[], key_hits=[], oversized=True, deep=False))
    monkeypatch.setattr(ac, "scalar", scalar)
    rec = ac.vocab_value_detect({"t": (["d"], {"d": "jsonb"})})
    assert rec["v"] == NO_DET and "could not be sampled" in rec["measured"]


def test_the_na_guard_requires_every_column_read_to_be_complete():
    base = dict(v=NA, cause="no-vocabulary-values", measured="m", vocab_values=dict(checked=True, tables=["t"], found=[], unread=[], embedded=[], weak=[], rows_sampled={"t.a": 5, "t.b": 5}, complete_columns=["t.a", "t.b"]))
    assert ac.vocab_values_na_problem("Vocab.alias", base) is None
    for mut in (dict(complete_columns=["t.a"]), dict(embedded=[dict(column="a")]), dict(weak=[dict(column="a")]), dict(complete_columns=None)):
        bad = json.loads(json.dumps(base))
        bad["vocab_values"].update(mut)
        assert ac.vocab_values_na_problem("Vocab.alias", bad), mut
    legacy = json.loads(json.dumps(base))
    del legacy["vocab_values"]["embedded"]                                                          # a record from before the review lacks the new keys: not a release
    assert ac.vocab_values_na_problem("Vocab.alias", legacy)


# ───────────────────────── HIGH-2: the short abbreviations ─────────────────────────

NINE = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]


def test_REAL_SQL_a_column_of_the_nine_short_abbreviations_is_a_vocabulary_column(monkeypatch, disposable_pg):
    t = "n176r_f"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(x) for x in NINE])
    try:
        rec = _detect(t, types)
        assert rec["v"] == FAIL and rec["v"] != NA and sorted(rec["vocab_values"]["found"][0]["spellings"]) == sorted(NINE)      # >= 2 distinct short aliases: carries, and they are non-canonical spellings
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_one_short_alias_alone_is_a_weak_signal_partial_never_na_and_beside_a_canonical_value_it_is_a_spelling(monkeypatch, disposable_pg):
    t = "n176r_g"
    types = _text_table(disposable_pg, monkeypatch, t, ["'Sa'", "'plain words'", "'more words'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == PARTIAL and rec["v"] != NA and rec["vocab_values"]["weak"][0]["short_aliases"] == ["Sa"] and "short alias" in rec["measured"] and "never N/A" in rec["measured"]
        assert ac.vocab_values_na_problem("Vocab.alias", dict(rec, v=NA, cause="no-vocabulary-values"))                       # and a forged N/A on it is refused
        ac.psql(f"INSERT INTO {t} VALUES (9, 'Sun')")
        rec2 = _detect(t, types)
        assert rec2["v"] == FAIL and "Sa" in rec2["vocab_values"]["found"][0]["spellings"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_classify_marks_the_short_aliases_and_two_letter_words_are_not_the_nine():
    for a in NINE:
        r = ac.vocab_classify(a)
        assert r is not None and r["kind"] == "alias" and r["detect"] is False and r["short"] is True, a
    assert ac.vocab_classify("to") is None and ac.vocab_classify("is") is None


# ───────────────────────── HIGH-3: vocabulary inside longer text, and json keys ─────────────────────────

EMBEDDED = ["Sun in 7th house", "graha=Sun,sign=Aries", "Mutual Reception: Sun <-> Moon", "sun_in_aries", "Jupiter aspects the 9th", "Saturn-Moon conjunction"]


@pytest.mark.parametrize("value", EMBEDDED)
def test_REAL_SQL_each_embedded_shape_is_partial_never_na(monkeypatch, disposable_pg, value):
    t = "n176r_h"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(value), "'plain filler'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == PARTIAL and rec["v"] != NA and "embedded vocabulary, spelling unchecked" in rec["measured"] and rec["vocab_values"]["embedded"][0]["examples"] == [value]
        assert not ac.vocab_embedded("plain filler") and ac.vocab_embedded(value)
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_an_embedded_term_beyond_the_sample_is_found_by_the_probe(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 4)
    t = "n176r_i"
    types = _text_table(disposable_pg, monkeypatch, t, [_q(f"plain filler {i}") for i in range(10)] + ["'Sun in 7th house'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == PARTIAL and "Sun in 7th house" in rec["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


@pytest.mark.parametrize("doc,label", [('{"planet": 5}', "planet"), ('{"graha": {"id": 3}}', "graha"), ('{"a": [{"house": 7}]}', "house"), ('{"Sun": 5, "n": 1}', "Sun"), ('{"x": {"mars": 2}}', "mars")])
def test_REAL_SQL_a_json_key_naming_a_term_or_a_class_with_an_integer_value_is_partial_never_na(monkeypatch, disposable_pg, doc, label):
    """Decision (stated in the registry text): the KEY is read as well as the leaf values. A key that names a term (`Sun`) or a class word (`planet`, `house`) with a number under it (an ontology ID) is
    vocabulary whose values are not terms: PARTIAL 'planet id column, values are ids', never N/A. The key NAME only ever downgrades an N/A to PARTIAL; it can never make a PASS or a FAIL."""
    t = "n176r_j"
    _mk(disposable_pg, monkeypatch, t, "id int, doc jsonb", [f"1, '{doc}'::jsonb", "2, '{\"other\": 1}'::jsonb"])
    try:
        rec = _detect(t, {"id": "integer", "doc": "jsonb"})
        assert rec["v"] == PARTIAL and rec["v"] != NA and label in rec["vocab_values"]["embedded"][0]["key_hits"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_prose_that_only_contains_the_words_in_other_senses_stays_na(monkeypatch, disposable_pg):
    t = "n176r_k"
    types = _text_table(disposable_pg, monkeypatch, t, ["'the sun rose over the hills'", "'a moonstone ring'", "'sunday market'", "'master of arts'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == NA                                                                         # lower-case `sun`, `Moonstone`, `Sunday`: not terms between token boundaries
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_the_embedded_regex_python_and_postgres_agree_on_the_shapes(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    lex = ac.vocab_lexicon()
    values = EMBEDDED + ["plain filler", "the sun rose", "Moonstone", "MARS", "SUN", "Sun", "mars bar", "Marsh", "sun", "SUNDAY", "x_Mars_y", "7Moon", "Moon8", "Rahu (true node) here", "Ketu(true node)"]
    for v in values:
        sql = f"SELECT ({_q(v)} ~* {ac._vocab_lit(lex['emb_ci_re'])} OR {_q(v)} ~ {ac._vocab_lit(lex['emb_cs_re'])})::text"
        assert (ac.scalar(sql) == "true") is ac.vocab_embedded(v), v


# ───────────────────────── HIGH-4: one normalisation, in Python and in SQL ─────────────────────────

SPELLINGS = ["Sun", "Sun\n", "Sun\t", "Sun ", " Sun", " Sun", "Sun ", "SUN", "sun", "ＳＵＮ", "ｓｕｎ", "Purva Bhadrapada", "Purva  Bhadrapada", "Purva Bhadrapada", "Purva\tBhadrapada",
             "Purva\r\nBhadrapada", "PURVA BHADRAPADA", "purva bhadrapada", "Purva Bhadrapada", "MARS", "mangala", "Mangala", "Sūrya", "Sūrya", "ſun", "Mo", "MO", "Sa", "foo", "", " ", "house_01", "HOUSE_01",
             "House 01", "First House", "first house", "FIRST  HOUSE", "ASHWINI", "ashwini", "Ashvini", "nak_01_ashwini", "Rahu (true node)", "rahu  (true  node)", "Ａries", "aries", "ARIES"]


def test_REAL_SQL_the_python_classifier_and_the_sql_predicate_agree_on_forty_spellings(monkeypatch, disposable_pg):
    """Differential: for every spelling the Python classifier (canonical / alias / short / none) and the SQL predicates (exact canonical, normalised known form, normalised short form) give the same answer."""
    point_psql_at(disposable_pg, monkeypatch)
    assert len(SPELLINGS) >= 40
    for v in SPELLINGS:
        py = ac.vocab_classify(v)
        sql = (f"WITH lex AS ({ac.vocab_lex_sql()}) SELECT jsonb_build_object('canon', {_q(v)} = ANY(((SELECT canon FROM lex)::text[])), "
               f"'key', {ac._vocab_norm(_q(v))} = ANY(((SELECT keys FROM lex)::text[])), 'detect', {ac._vocab_norm(_q(v))} = ANY(((SELECT detect FROM lex)::text[])), "
               f"'short', {ac._vocab_norm(_q(v))} = ANY(((SELECT short FROM lex)::text[])), 'whole', {ac._vocab_p_whole(_q(v))})::text")
        got = json.loads(ac.scalar(sql))
        assert got["canon"] is (py is not None and py["kind"] == "canonical"), (v, py, got)
        assert (got["canon"] or got["key"]) is (py is not None), (v, py, got)
        assert got["whole"] is bool(py and py["detect"]), (v, py, got)
        assert got["short"] is bool(py and py["short"]), (v, py, got)


def test_REAL_SQL_a_spelling_beyond_the_sample_is_a_fail_exactly_as_inside_it(monkeypatch, disposable_pg):
    """`Sun\\n` and a double-spaced `Purva  Bhadrapada` far past the sample used to read PASS (the SQL compared lower(btrim(v)) only) but FAIL inside the sample."""
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    for late, name in (("E'Sun\\n'", "n176r_l1"), ("E'Purva  Bhadrapada'", "n176r_l2"), ("E'Sun\\u00a0'", "n176r_l3")):
        base = ["'Sun'"] * 8 if name != "n176r_l2" else ["'Purva Bhadrapada'"] * 8
        types = _text_table(disposable_pg, monkeypatch, name, base + [late])
        try:
            rec = _detect(name, types)
            assert rec["v"] == FAIL and rec["vocab_values"]["found"][0]["spelling_read"]["found"] is True, (name, rec["measured"])
            inside = _text_table(disposable_pg, monkeypatch, name + "x", [late] + base)
            assert _detect(name + "x", inside)["v"] == FAIL                                           # the same value inside the sample
            ac.psql(f"DROP TABLE IF EXISTS {name}x")
        finally:
            ac.psql(f"DROP TABLE IF EXISTS {name}")


# ───────────────────────── MED-5: one canonical spelling family per column ─────────────────────────

def test_the_spelling_families_are_id_name_and_code():
    assert ac.vocab_families(["Moon", "Sun"]) == frozenset({"name"}) and ac.vocab_families(["SUN", "MAR"]) == frozenset({"code"}) and ac.vocab_families(["sun", "moon"]) == frozenset({"id"})
    assert ac.vocab_families(["Moon", "MOON"]) == frozenset() and ac.vocab_families(["Sun", "sun"]) == frozenset() and ac.vocab_families(["Aries", "Ashwini", "First House"]) == frozenset({"name"})
    assert "MOON" in ac.vocab_off_family(["Moon"]) and "Moon" not in ac.vocab_off_family(["Moon"]) and ac.vocab_off_family(["Moon", "MOON"]) == []


def test_REAL_SQL_a_column_mixing_moon_and_moon_is_partial_not_pass_and_one_family_is_pass(monkeypatch, disposable_pg):
    t = "n176r_m"
    types = _text_table(disposable_pg, monkeypatch, t, ["'Moon'", "'MOON'", "'Sun'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == PARTIAL and "MIXED canonical spelling families" in rec["measured"] and "not PASS" in rec["measured"] and rec["vocab_values"]["found"][0]["mixed"] is True
        ac.psql(f"DELETE FROM {t} WHERE label = 'MOON'")
        assert _detect(t, types)["v"] == PASS                                                         # 'Moon' and 'Sun' are one family (the display name)
        ac.psql(f"INSERT INTO {t} VALUES (9, 'SUN')")
        assert _detect(t, types)["v"] == PARTIAL
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_second_family_beyond_the_sample_is_found_by_the_existence_read(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 5)
    t = "n176r_n"
    types = _text_table(disposable_pg, monkeypatch, t, ["'Moon'"] * 9 + ["'MOON'"])
    try:
        rec = _detect(t, types)
        assert rec["v"] == PARTIAL and rec["vocab_values"]["found"][0]["mixed"] is True and "MOON" in rec["measured"] + json.dumps(rec["vocab_values"])
        clean = _text_table(disposable_pg, monkeypatch, t, ["'Moon'"] * 10)
        assert _detect(t, clean)["v"] == PASS
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────── every new statement is bounded ─────────────────────────

@pytest.mark.parametrize("kind", ["text", "array", "json"])
def test_the_probe_and_the_new_sample_parts_are_bounded(kind):
    probe = ac.vocab_probe_sql("big_t", "c", kind)
    assert "ORDER BY" not in probe.upper() and "GROUP BY" not in probe.upper() and "count(" not in probe and probe.count(" LIMIT 3") >= 1
    sample = ac.vocab_sample_sql("big_t", "c", kind)
    assert sample.count('FROM "big_t"') == 1 and "ORDER BY" not in sample.upper() and 'count(*) FROM "big_t"' not in sample
    assert sample.startswith("WITH lex AS (") and probe.startswith("WITH lex AS (")


# ───────────────────────── a table shared by several assets is read once per layer run ─────────────────────────

def test_the_samples_and_probes_of_a_shared_table_are_read_once_per_cache(monkeypatch):
    calls = []

    def scalar(q):
        calls.append(q[:40])
        if "'values'" in q:
            return json.dumps(dict(rows=ac.VOCAB_SAMPLE_ROWS, values=["filler"], emb=[]))
        return json.dumps(dict(hits=[], key_hits=[]))
    monkeypatch.setattr(ac, "scalar", scalar)
    own, cache = {"chart_facts": (["fact_value"], {"fact_value": "text"})}, {}
    first = ac.vocab_value_detect(own, cache=cache)
    n = len(calls)
    second = ac.vocab_value_detect(own, cache=cache)                                                  # a second asset on the same table
    assert len(calls) == n and first["v"] == second["v"] == NA
    ac.vocab_value_detect(own)                                                                        # without a cache nothing is remembered
    assert len(calls) == 2 * n
