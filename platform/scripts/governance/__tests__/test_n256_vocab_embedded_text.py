"""test_n256_vocab_embedded_text.py: the CHECKED `vocab_embedded_text` declaration (SS N-256, option a).

A named PROSE or IDENTIFIER text column's embedded graha / sign / nakshatra words are not a spelling-census target. The engine checks the declaration: the table is owned and the column known; the column is covered by the
asset's Narr/Null declarations (prose_fields, prose_none transcription / identifier / templated columns, prose_excluded); the column carries no WHOLE-VALUE vocabulary (only the 'embedded vocabulary, spelling unchecked'
PARTIAL is lifted); and the covering prose_none block is not contradicted. Every forgery reads NO_DETECTOR, never PASS and never the lifted reading. Disposable PostgreSQL for the value reads.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

EV = "platform/scripts/governance/asset_census.py"
WHY = "the column holds prose or identifier text whose embedded terms are not a spelling census"
T = "n256_t"


def _entry(*cols, **extra):
    e = {"kind": "data", "prose_fields": ["note"], "prose_none": None,
         "vocab_embedded_text": [dict(table=T, column=c, why=WHY, evidence=EV) for c in cols]}
    e.update(extra)
    return e


def _own(cols):
    return {T: (list(cols), {c: "text" for c in cols}, None)}


# ───────────────────────── the pure checks ─────────────────────────

def test_a_sound_declaration_over_covered_columns_is_accepted():
    e = _entry("note", "ref", prose_none=dict(why="x y z", identifier_columns=[dict(table=T, column="ref", why=WHY, evidence=EV)]))
    ac.validate_vocab_embedded_text_declaration("assets['a']", e)
    pairs, problems = ac.vocab_embedded_exempt(e, T, _own(["id", "note", "ref"]))
    assert pairs == {(T, "note"), (T, "ref")} and problems == []


@pytest.mark.parametrize("name,entry,msg", [
    ("not covered by any Narr/Null declaration", _entry("other"), "not covered by the asset's Narr/Null declarations"),
    ("a closed (whole-value) column is not embedded text", _entry("label", prose_none=dict(why="x y z", closed_columns=[dict(table=T, column="label", values=["Sun"], why=WHY)])), "not covered"),
    ("wrong table", dict(_entry("note"), vocab_embedded_text=[dict(table="other_t", column="note", why=WHY, evidence=EV)]), "not an owned table"),
    ("a column the table does not carry", _entry("ghost", prose_fields=["note", "ghost"]), "is not a column of"),
])
def test_FORGERY_an_unsound_exemption_is_refused_and_exempts_nothing(name, entry, msg):
    pairs, problems = ac.vocab_embedded_exempt(entry, T, _own(["id", "note", "label", "ref", "other"]))
    assert pairs == set() and problems and any(msg in p for p in problems), (name, problems)


def test_FORGERY_one_bad_entry_voids_the_whole_declaration():
    e = _entry("note", "other")
    pairs, problems = ac.vocab_embedded_exempt(e, T, _own(["id", "note", "other"]))
    assert pairs == set() and len(problems) == 1


def test_FORGERY_unread_columns_cannot_be_checked():
    pairs, problems = ac.vocab_embedded_exempt(_entry("note"), T, {T: (None, None, None)})
    assert pairs == set() and "were not read" in problems[0]


@pytest.mark.parametrize("bad", [
    [], "x", [dict(table=T, column="note")], [dict(table=T, column="note", why="short", evidence=EV)], [dict(table=T, column="note", why=WHY, evidence="unverified: ok then")],
    [dict(table=T, column="note", why=WHY, evidence="platform/no/such.py")], [dict(table="bad table", column="note", why=WHY, evidence=EV)],
    [dict(table=T, column="note", why=WHY, evidence=EV, extra=1)], [dict(table=T, column="note", why=WHY, evidence=EV)] * 2,
])
def test_FORGERY_malformed_declarations_are_refused(bad):
    e = dict(_entry("note"), vocab_embedded_text=bad)
    assert ac.vocab_embedded_text_problem(e)
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_embedded_text_declaration("assets['a']", e)
    pairs, problems = ac.vocab_embedded_exempt(e, T, _own(["note"]))
    assert pairs == set() and problems


def test_the_post_check_voids_an_exemption_the_covering_prose_none_block_contradicts():
    narr = {"prose_none": {"contradicted": [f"{T}.ref: a declared identifier column that is not a key of {T}", "other_t.x: nothing"]}}
    assert ac.vocab_embedded_post_check(None, {(T, "ref")}, narr)
    assert ac.vocab_embedded_post_check(None, {(T, "note")}, narr) == []
    assert ac.vocab_embedded_post_check(None, {(T, "ref")}, {"prose_none": {"contradicted": []}}) == []
    assert ac.vocab_embedded_post_check(None, {(T, "ref")}, None) == []


def test_the_refused_record_is_no_detector_with_the_disagreement():
    e = _entry("other")
    r = ac.vocab_embedded_refuse({"vocab_values": {"checked": True}}, ["x.y: nope"], e)
    assert r["v"] == ac.NO_DET and r["declaration_disagreements"][0]["field"] == "vocab_embedded_text" and "refused" in r["measured"]


def test_the_coverage_reads_the_declared_forms_only():
    e = {"prose_fields": ["a", "b.$.k"], "prose_none": {"transcription_columns": [dict(column="t1")], "identifier_columns": [dict(table="o", column="i1")], "templated_columns": [dict(column="m1")],
                                                          "closed_columns": [dict(column="c1")]},
         "prose_excluded": [dict(column="x1")]}
    cov = ac.vocab_embedded_coverage(e, "tt")
    assert set(cov) == {("tt", "a"), ("tt", "b"), ("tt", "t1"), ("o", "i1"), ("tt", "m1"), ("tt", "x1")}


# ───────────────────────── the value reads (disposable DB) ─────────────────────────

def _mk(pg, monkeypatch, ddl, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    ac.psql(f"CREATE TABLE {T} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {T} VALUES ({r})")


def _detect(cols, exempt=frozenset()):
    return ac.vocab_value_detect({T: (["id"] + cols, {"id": "integer", **{c: "text" for c in cols}})}, None, embedded_exempt=exempt)


def test_REAL_SQL_an_exempt_prose_column_lifts_only_the_embedded_finding(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, "id int, note text, ref text", ["1, 'Sun in 7th house', 'sun_in_aries'", "2, 'Moon rises in the east', 'moon_in_taurus'"])
    try:
        base = _detect(["note", "ref"])
        assert base["v"] == ac.PARTIAL and "embedded vocabulary, spelling unchecked" in base["measured"]
        lifted = _detect(["note", "ref"], {(T, "note"), (T, "ref")})
        assert lifted["v"] == ac.NA and lifted["cause"] == "no-vocabulary-values", lifted
        assert sorted(lifted["vocab_values"]["embedded_exempt"]) == [f"{T}.note", f"{T}.ref"] and lifted["vocab_values"]["embedded"] == []
        assert ac.vocab_values_na_problem("Vocab.alias", lifted) is None          # the N/A still rests on the checked block
        part = _detect(["note", "ref"], {(T, "note")})
        assert part["v"] == ac.PARTIAL and f"{T}.ref" in part["measured"] and f"{T}.note" not in part["measured"].split("embedded vocabulary")[1], part["measured"]    # the other column's finding stays
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


@pytest.mark.parametrize("label_rows", [["'Sun'", "'Moon'"], ["'MARS_X'", "'Mars'"], ["'Surya'", "'Mars'"]])
def test_REAL_SQL_FORGERY_a_column_with_whole_value_vocabulary_is_never_exempt(monkeypatch, disposable_pg, label_rows):
    _mk(disposable_pg, monkeypatch, "id int, label text, note text", [f"{i + 1}, {r}, 'Sun in 7th house'" for i, r in enumerate(label_rows)])
    try:
        r = _detect(["label", "note"], {(T, "label"), (T, "note")})
        assert r["v"] == ac.NO_DET and "carry(ies) whole-value vocabulary" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_embedded_text", r
        assert r["v"] != ac.PASS
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_REAL_SQL_a_non_canonical_whole_value_still_fails_when_another_column_is_exempt(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, "id int, label text, note text", ["1, 'JU', 'Sun in 7th house'", "2, 'KE', 'Moon rises'", "3, 'MA', 'x'"])
    try:
        r = _detect(["label", "note"], {(T, "note")})
        assert r["v"] == ac.FAIL, r["measured"]                                 # the whole-value spelling finding is untouched by an exemption of a DIFFERENT column
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_REAL_SQL_a_column_without_any_embedded_finding_is_unchanged_by_its_declaration(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch, "id int, note text", ["1, 'plain words only'", "2, 'nothing here'"])
    try:
        assert _detect(["note"], {(T, "note")})["v"] == _detect(["note"])["v"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


# ───────────────────────── the real declarations ─────────────────────────

def test_every_real_vocab_embedded_text_declaration_is_sound_and_covered():
    """N-260: each real entry rests on EITHER the asset's Narr/Null coverage OR a key-member basis (checked live at measure time); the validator accepts it and the basis is one of the two."""
    decl = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
    n_cov = n_key = 0
    for aid, e in decl.items():
        if e.get("vocab_embedded_text") is None:
            continue
        ac.validate_vocab_embedded_text_declaration(aid, e)
        for d in e["vocab_embedded_text"]:
            cov = ac.vocab_embedded_coverage(e, d["table"])
            if (d["table"].lower(), d["column"].lower()) in cov:
                n_cov += 1
            else:
                assert "unique or primary key" in d["why"], (aid, d["table"], d["column"])
                n_key += 1
    assert n_cov >= 1 and n_key >= 1
