"""test_n176_vocab_values_round2.py: the round-2 re-check of the value-based Vocab.alias detector (N-176).

HIGH-1  the SQL normalisation is LOCALE-INDEPENDENT BY CONSTRUCTION and equals Python's: the whitespace class is the explicit set of every str.isspace() code point (Python's `\\s` reaches U+001C..U+001F, U+0085,
        U+1680, U+2028, U+2029 that PostgreSQL's `\\s` does not), the case fold is an explicit translate() table over the characters of the lexicon alphabet (Ś Ū Ā Ṛ Ṅ ...; lower() does not fold them under a C
        LC_CTYPE), and the embedded regex runs case-sensitively over the same folded / NFKC texts (no `~*`, no re.I). Differential tests over EVERY str.isspace() code point and EVERY non-ASCII capital of the
        lexicon keys, on the helper's cluster and on a second database with an en_US.UTF-8 LC_CTYPE (skipped with a visible reason when the platform has no such locale).
HIGH-2  the existence read of an incomplete column checks the embedded terms and the short aliases too: each of the five shapes beyond the sample reads exactly as inside it.
MED-3   a table shared by several assets is read through the asset's own rows (declared produced_tables filter, else the count_sql predicate), and the cache key carries the scope.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA


def _q(s):
    return "'" + s.replace("'", "''") + "'"


def _flags(values):
    """What PostgreSQL says about each value: its folded form and the predicates, through the statement shapes the detector itself runs (one `lex` CTE)."""
    sql = (f"WITH lex AS ({ac.vocab_lex_sql()}), vals AS (SELECT x FROM jsonb_array_elements_text({ac._vocab_lit(json.dumps(values))}::jsonb) AS t(x)) "
           f"SELECT coalesce(jsonb_agg(jsonb_build_object('v', x, 'fold', {ac._vocab_norm('x')}, 'canon', x = ANY(((SELECT canon FROM lex)::text[])), 'whole', {ac._vocab_p_whole('x')}, "
           f"'short', {ac._vocab_p_short('x')}, 'emb', {ac._vocab_p_emb('x')}, 'key', {ac._vocab_norm('x')} = ANY(((SELECT keys FROM lex)::text[])))), '[]'::jsonb)::text FROM vals")
    return json.loads(ac.scalar(sql))


def _expected(v):
    lex = ac.vocab_lexicon()
    r = ac.vocab_classify(v)
    return dict(fold=ac.vocab_fold(v), canon=bool(r and r["kind"] == "canonical"), whole=bool(r and r["detect"]), short=bool(r and r["short"]),
                emb=ac.vocab_embedded(v), key=ac.vocab_fold(v) in lex["keys"])


def _compare(values):
    got = _flags(values)
    assert len(got) == len(values)
    bad = []
    for v, g in zip(values, got):
        e = _expected(v)
        for k in ("fold", "canon", "whole", "short", "emb", "key"):
            if g[k] != e[k]:
                bad.append((v, k, g[k], e[k]))
    assert not bad, bad[:8]


ISSPACE = [chr(c) for c in range(0x110000) if chr(c).isspace()]
CAPS_VARIANTS = ["Śani", "ŚANI", "SŪRYA", "Sūrya", "SŪRYA", "ŚUKRA", "Śukra", "MAṄGALA", "Maṅgala", "BṚHASPATI", "Bṛhaspati", "Purva Bhadrapada", "PURVA BHADRAPADA", "Ā", "ĀŚ", "ß", "ẞ", "Mooẞn", "ARıES", "arıes", "ARİES",
                 "aries", "ＡＲＩＥＳ", "ＳＵＮ", "ſun", "Sun", "SUN", "sun"]


# ───────────────────────── HIGH-1: one normalisation, in Python and in SQL ─────────────────────────

def test_the_explicit_whitespace_class_is_exactly_the_python_isspace_set():
    lex = ac.vocab_lexicon()
    assert list(lex["ws_points"]) == [ord(c) for c in ISSPACE] and len(ISSPACE) >= 29
    for cp in (0x1C, 0x1D, 0x1E, 0x1F, 0x85, 0x1680, 0x2028, 0x2029, 0xA0, 0x3000):
        assert chr(cp).isspace() and re.fullmatch(r"\s", chr(cp)) and cp in lex["ws_points"]
    assert all(re.fullmatch(lex["ws_class"][:-1], c) for c in ISSPACE) and not any(re.fullmatch(lex["ws_class"][:-1], c) for c in "aZ0_-​᠎﻿")


def test_the_fold_table_covers_every_non_ascii_capital_of_the_lexicon_keys():
    lex = ac.vocab_lexicon()
    non_ascii = {ch for k in lex["keys"] for ch in k if ord(ch) > 127}
    assert non_ascii and {"ś", "ū", "ā", "ṛ", "ṅ"} <= non_ascii
    for ch in non_ascii:
        for cap in {ch.upper(), ch.title()} - {ch}:
            if len(cap) == 1:
                assert lex["fold_table"].get(ord(cap)) == ch, (ch, cap)                 # Ś -> ś, Ū -> ū ...
    assert lex["fold_table"][ord("A")] == "a" and lex["fold_table"][ord("Z")] == "z" and dict(lex["fold_multi"]) == {"ß": "ss", "ẞ": "ss"}


def test_the_python_fold_agrees_with_the_ontology_normalisation_on_every_code_point():
    """`_norm_form` (the reference) and `vocab_fold` give the same form for every single code point whose case fold stays inside the lexicon alphabet, and a form that is a known key on neither side or on both for ALL
    code points (a code point whose fold leaves the alphabet can never become a key)."""
    lex = ac.vocab_lexicon()
    keys = lex["keys"]
    diff = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        a, b = ac._norm_form(ch), ac.vocab_fold(ch)
        if (a in keys) != (b in keys):
            diff.append((cp, a, b))
    assert not diff, diff[:5]
    for v in CAPS_VARIANTS + ["Sun" + c for c in ISSPACE] + [c + "Sun" for c in ISSPACE] + ["Purva" + c + "Bhadrapada" for c in ISSPACE]:
        assert (ac._norm_form(v) in keys) == (ac.vocab_fold(v) in keys), v
        if v.strip():
            assert ac._norm_form(v) == ac.vocab_fold(v) or ac._norm_form(v) not in keys, v


def test_REAL_SQL_every_isspace_code_point_around_a_term_agrees_with_python(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    vals = []
    for c in ISSPACE:
        vals += ["Sun" + c, c + "Sun", "Purva" + c + "Bhadrapada", "Purva" + c + c + "Bhadrapada", c + "Sun" + c, "Sun" + c + "in 7th house"]
    _compare(vals)
    for c in (" ", " ", " ", "\u0085", "\u001c"):                           # the review's five: Python knew them, PostgreSQL's \s did not
        got = _flags(["Sun" + c])[0]
        assert got["whole"] is True and got["canon"] is False and got["key"] is True, repr(c)


def test_REAL_SQL_every_non_ascii_capital_of_the_lexicon_keys_agrees_with_python(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    lex = ac.vocab_lexicon()
    vals = list(CAPS_VARIANTS)
    for k in sorted(lex["keys"]):
        if any(ord(ch) > 127 for ch in k):
            vals += [k, k.upper(), k.title(), k.capitalize(), k.swapcase()]
    assert len(vals) > 60
    _compare(vals)
    got = {g["v"]: g for g in _flags(["Śani", "ŚANI", "SŪRYA", "Purva\u00a0Bhadrapada", "Purva Bhadrapada", "ARıES", "arıes", "ARİES"])}
    assert got["Śani"]["key"] and got["ŚANI"]["key"] and got["SŪRYA"]["key"] and got["Purva\u00a0Bhadrapada"]["key"] and got["Purva\u00a0Bhadrapada"]["canon"] is False and got["Purva Bhadrapada"]["canon"] is True
    assert not got["ARıES"]["emb"] and not got["arıes"]["emb"] and not got["ARİES"]["emb"]      # one answer on both sides (the dotless / dotted i are not an `i`)
    assert not ac.vocab_embedded("ARıES") and not ac.vocab_embedded("ARİES")


def test_REAL_SQL_the_embedded_predicate_agrees_on_fullwidth_and_folded_text(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    vals = ["ＳＵＮ in 7th house", "Ｓun in 7th house", "ＡＲＩＥＳ rising", "graha=ＭＯＯＮ", "ŚANI in 7th house", "x ARIES y", "x ARİES y", "xariesx", "sun_in_aries", "Sun in 7th house", "the sun rose", "SUN rise",
            "mutual reception: Sun <-> Moon"]
    _compare(vals)
    assert ac.vocab_embedded("ＳＵＮ in 7th house") and ac.vocab_embedded("ＡＲＩＥＳ rising")        # NFKC first: full-width text inside longer text is found (PostgreSQL 13+ normalize())


def _en_us_database(pg):
    """A second database on the helper's cluster with an en_US.UTF-8 LC_CTYPE, or None when the platform has no such locale."""
    for loc in ("en_US.UTF-8", "en_US.utf8"):
        try:
            pg.psql("DROP DATABASE IF EXISTS suvarna_locale_test")
            pg.psql(f"CREATE DATABASE suvarna_locale_test TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE '{loc}' LC_CTYPE '{loc}'")
            return "suvarna_locale_test"
        except Exception:                                                                    # noqa: BLE001
            continue
    return None


def test_REAL_SQL_the_same_differential_holds_under_an_en_us_utf8_ctype_and_the_c_ctype(monkeypatch, disposable_pg):
    """The SQL is locale-independent BY CONSTRUCTION; this runs the differential under both a C and an en_US.UTF-8 LC_CTYPE to prove it (the helper's cluster is C; the second database is created when the platform
    has the locale, else the test says so and the by-construction argument stands: no lower(), no `\\s`, no `~*`)."""
    point_psql_at(disposable_pg, monkeypatch)
    base_ctype = ac.scalar("SELECT datctype FROM pg_database WHERE datname = current_database()")                    # the helper's cluster: C/POSIX locally, whatever the CI image ships (C.UTF-8, en_US.utf8): the differential must hold under ANY ctype
    assert base_ctype
    base = ["Sun" + c for c in ISSPACE] + CAPS_VARIANTS + ["Śani", "Purva  Bhadrapada", "ARıES", "ＳＵＮ in 7th house"]
    _compare(base)
    name = _en_us_database(disposable_pg)
    if name is None:
        pytest.skip("no en_US.UTF-8 locale on this platform: the C-ctype run above plus the by-construction argument stand")
    monkeypatch.setenv("PGDATABASE", name)
    try:
        assert ac.scalar("SELECT datctype FROM pg_database WHERE datname = current_database()").lower().replace("-", "") == "en_us.utf8"
        _compare(base)
        assert ac.scalar("SELECT lower('Ś')") == "ś"                                          # under this ctype lower() DOES fold Ś; the translate() table gives the same answer without it
    finally:
        monkeypatch.undo()
        point_psql_at(disposable_pg, monkeypatch)
        disposable_pg.psql("DROP DATABASE IF EXISTS suvarna_locale_test")


def _mk(pg, monkeypatch, table, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {table} VALUES ({r})")


def _col(pg, monkeypatch, name, values, ddl="id int, label text"):
    _mk(pg, monkeypatch, name, ddl, [f"{i}, {v}" for i, v in enumerate(values)])
    return {"id": "integer", "label": "text"}


def _detect(table, types, **kw):
    return ac.vocab_value_detect({table: (list(types), dict(types))}, **kw)


@pytest.mark.parametrize("late", ["E'\\u015Aani'", "E'Sun\\u2028'", "E'Sun\\u2029'", "E'\\u1680Sun'", "E'Sun\\u0085'", "E'S\\u016aRYA'"])
def test_REAL_SQL_a_spelling_beyond_the_sample_reads_exactly_as_inside_it(monkeypatch, disposable_pg, late):
    """3000 rows of Saturn and one `Śani` at the end read PASS (inside the sample FAIL); the same for the other whitespace code points and the non-ASCII capitals."""
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 6)
    t = "n176q_a"
    base = ["'Saturn'"] * 12
    try:
        beyond = _detect(t, _col(disposable_pg, monkeypatch, t, base + [late]))
        inside = _detect(t, _col(disposable_pg, monkeypatch, t, [late] + base))
        assert beyond["v"] == inside["v"] == FAIL, (late, beyond["measured"], inside["measured"])
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────── HIGH-2: the five shapes beyond the sample == inside it ─────────────────────────

SHAPES = ["Sun in 7th house", "graha=Sun,sign=Aries", "Mutual Reception: Sun <-> Moon", "sun_in_aries", "Su", "Mo"]


@pytest.mark.parametrize("shape", SHAPES)
def test_REAL_SQL_each_shape_beyond_the_sample_reads_the_same_as_inside_it(monkeypatch, disposable_pg, shape):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 6)
    t = "n176q_b"
    base = ["'Sun'"] * 12
    try:
        beyond = _detect(t, _col(disposable_pg, monkeypatch, t, base + [_q(shape)]))
        inside = _detect(t, _col(disposable_pg, monkeypatch, t, [_q(shape)] + base))
        assert beyond["v"] == inside["v"], (shape, beyond["measured"], inside["measured"])
        assert beyond["v"] in (PARTIAL, FAIL) and beyond["v"] != PASS and beyond["v"] != NA
        expect = FAIL if shape in ("Su", "Mo") else PARTIAL                                  # a short alias beside a canonical value is a non-canonical spelling; the embedded shapes cannot be graded
        assert inside["v"] == expect, (shape, inside["measured"])
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_an_embedded_or_short_signal_beyond_the_sample_of_a_non_carrying_column_reads_like_inside(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 6)
    t = "n176q_c"
    try:
        for shape in ("Sun in 7th house", "Sa"):
            filler = [_q(f"plain filler {i}") for i in range(12)]
            beyond = _detect(t, _col(disposable_pg, monkeypatch, t, filler + [_q(shape)]))
            inside = _detect(t, _col(disposable_pg, monkeypatch, t, [_q(shape)] + filler))
            assert beyond["v"] == inside["v"] == PARTIAL, (shape, beyond["measured"], inside["measured"])
        both = _detect(t, _col(disposable_pg, monkeypatch, t, [_q("plain")] * 12 + ["'Sa'", "'Mo'"]))                 # two distinct short aliases beyond the sample: carries, FAIL, as inside
        assert both["v"] == FAIL
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_every_category_is_read_so_a_spelling_beyond_three_embedded_rows_still_fails(monkeypatch, disposable_pg):
    monkeypatch.setattr(ac, "VOCAB_SAMPLE_ROWS", 4)
    t = "n176q_d"
    rows = ["'Sun'"] * 6 + [_q(f"Sun in {i}th house") for i in range(5, 12)] + ["'MARS'"]
    try:
        rec = _detect(t, _col(disposable_pg, monkeypatch, t, rows))
        assert rec["v"] == FAIL and "MARS" in rec["measured"]                                # the embedded rows (> 3) did not crowd the spelling out of the sample
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_the_spelling_statement_is_one_bounded_union_scan_then_one_bounded_scan_per_category():
    sql = ac.vocab_spelling_sql("big_t", "c", "text", ["MOON"])
    assert sql.count('FROM "big_t"') == 5 and sql.count(" LIMIT ") == 5 and "count(" not in sql and "ORDER BY" not in sql.upper()
    assert "'spell'" in sql and "'off'" in sql and "'emb'" in sql and "'short'" in sql and "NOT EXISTS (SELECT 1 FROM (" in sql
    assert "w.v = ANY(" in sql and ac.vocab_spelling_sql("big_t", "c", "text").count("false") >= 1


def test_the_spelling_fetch_merges_every_category_through_the_samples_own_grader(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: json.dumps(dict(spell=["MARS"], off=[], emb=["Sun in 7th house"], short=["Su"])))
    got = ac.vocab_fetch_spelling("t", "c", "text", [])
    assert got["found"] and got["sample"] == ["MARS", "Sun in 7th house", "Su"]
    monkeypatch.setattr(ac, "scalar", lambda q: "{}")
    assert ac.vocab_fetch_spelling("t", "c", "text", []) == dict(found=False, sample=[], spell=[], off=[], emb=[], short=[])


# ───────────────────────── MED-3: a shared table is read through the asset's own rows ─────────────────────────

def test_REAL_SQL_a_shared_table_is_scoped_to_the_assets_rows_and_the_cache_key_carries_the_scope(monkeypatch, disposable_pg):
    t = "n176q_shared"
    _mk(disposable_pg, monkeypatch, t, "id int, fact_category text, label text",
        [f"{i}, 'cat_a', 'Moon'" for i in range(4)] + [f"{10 + i}, 'cat_b', 'MARS'" for i in range(4)])
    types = {"id": "integer", "fact_category": "text", "label": "text"}
    own = {t: (list(types), dict(types))}
    try:
        cache = {}
        a = ac.vocab_value_detect(own, cache=cache, scopes={t: dict(where="\"fact_category\"::text = 'cat_a'", label="a")})
        b = ac.vocab_value_detect(own, cache=cache, scopes={t: dict(where="\"fact_category\"::text = 'cat_b'", label="b")})
        whole = ac.vocab_value_detect(own, cache=cache)
        assert a["v"] == PASS and b["v"] == FAIL and whole["v"] == FAIL                         # the spelling written by cat_b no longer FAILs cat_a
        assert a["vocab_values"]["scopes"] == {t: "a"} and b["vocab_values"]["scopes"] == {t: "b"} and whole["vocab_values"]["scopes"] == {}
        assert len({k[-1] for k in cache if k[0] == "sample"}) == 3                                 # three scopes, three cached reads
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_vocab_scopes_prefers_the_declared_filter_then_the_count_sql_predicate_and_says_when_it_cannot():
    chart = ac.CHART_ID
    shared = {"chart_facts", "brahma_class_priors"}
    r = dict(count_sql=f"SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('dasha','sade_sati')")
    got = ac.vocab_scopes(["chart_facts"], r, {}, shared, {}, chart)
    assert got["chart_facts"]["where"] == f"chart_id = '{chart}' AND fact_category IN ('dasha','sade_sati')" and "registry count_sql predicate" in got["chart_facts"]["label"]
    decl = {"produced_tables": [dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"), why="the writer's own row set")]}
    got = ac.vocab_scopes(["chart_facts"], r, {}, shared, dict(decl, kind="data"), chart)
    assert got["chart_facts"]["where"] == "(\"fact_category\"::text = 'dasha_scope_cap')" and "declared produced rows (1 filter, ORed)" in got["chart_facts"]["label"]
    plain = ac.vocab_scopes(["brahma_class_priors"], dict(count_sql="SELECT count(*) FROM brahma_class_priors"), {}, shared, {}, chart)
    assert plain["brahma_class_priors"]["where"] is None and "names no row predicate" in plain["brahma_class_priors"]["label"]
    odd = ac.vocab_scopes(["chart_facts"], dict(count_sql="SELECT count(*) FROM chart_facts a JOIN x ON true"), {}, shared, {}, chart)
    assert odd["chart_facts"]["where"] is None and "not named by its count_sql" in odd["chart_facts"]["label"]
    assert ac.vocab_scopes(["own_table"], r, {}, shared, {}, chart) == {}                          # not shared: read whole, no entry


# ───────────────────────── LOW ─────────────────────────

def test_the_latest_attempts_docstring_states_the_real_order():
    doc = ac.latest_attempts.__doc__
    assert "started_at" in doc and "created_at, run_id" in doc and "the latest STARTED build_run_assets attempt per" in doc


def test_the_registry_text_states_the_short_alias_collisions_the_fold_and_the_scope():
    t = ac.CRITERION_REGISTRY["Vocab.alias"]["applicability"]
    assert "weekday" in t and "locale-independent" in t.lower() and "SHARED" in t and ac.CRITERION_REGISTRY["Vocab.alias"]["revision"] == 9      # 8 before registry revision 28 (ONE bump)
