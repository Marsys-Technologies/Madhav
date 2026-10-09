"""test_n260_embedded_keys.py: SS N-260 on the embedded-vocabulary exemption.

(1) KEY basis: a column that is a member of a unique / primary key of its table (read LIVE from the catalog, the identifier check's own rule) holds identifiers, not prose. A declared `vocab_embedded_text` entry may rest on it,
    and `ayanamsha_id` is ONE engine-level rule (no declaration): exempt on a table ONLY IF the table's keys show it in a key. A free-text `ayanamsha_id` outside every key, a table whose keys were not read, a view: NOT exempt.
(2) Only a column with embedded EXAMPLES is lifted: json-KEY hits and unclassified probe hits stay a finding whatever is declared (a misspelled graha key must not be hidden).
(3) The post-check also refuses an exemption whose covering prose_none claim is OPEN or UNREAD, not only contradicted.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

EV = "platform/scripts/governance/asset_census.py"
WHY = "the column holds identifiers that are members of a unique key of the table, not prose"
T = "n260_t"


def _own(cols):
    return {T: (list(cols), {c: "text" for c in cols}, None)}


def _entry(*cols):
    return {"kind": "data", "prose_fields": [], "vocab_embedded_text": [dict(table=T, column=c, why=WHY, evidence=EV) for c in cols]}


# ───────────────────────── (1) key basis ─────────────────────────

def test_key_membership_reads_the_catalog_keys_only():
    keys = {T: [["chart_id", "ayanamsha_id"], ["id"]]}
    assert ac.vocab_embedded_key_member(T, "ayanamsha_id", keys) and ac.vocab_embedded_key_member(T.upper(), "AYANAMSHA_ID", keys)
    assert not ac.vocab_embedded_key_member(T, "note", keys)
    for unread in (None, {}, {"other": [["ayanamsha_id"]]}, {T: None}, {T: []}):
        assert not ac.vocab_embedded_key_member(T, "ayanamsha_id", unread)
    assert not ac.vocab_embedded_key_member(None, "ayanamsha_id", keys) and not ac.vocab_embedded_key_member(T, None, keys)


def test_the_engine_level_rule_exempts_ayanamsha_id_only_where_it_is_a_verified_key_member():
    own = _own(["id", "ayanamsha_id", "note"])
    assert ac.EMBEDDED_KEY_COLUMNS == ("ayanamsha_id",)
    assert ac.vocab_embedded_auto_keys(own, {T: [["chart_id", "ayanamsha_id", "build_id"]]}) == {(T, "ayanamsha_id")}
    # FORGERY: the same column name as free text outside every key; keys unread; a view without keys; a table that does not carry the column
    assert ac.vocab_embedded_auto_keys(own, {T: [["id"]]}) == set()
    assert ac.vocab_embedded_auto_keys(own, None) == set()
    assert ac.vocab_embedded_auto_keys(own, {}) == set()
    assert ac.vocab_embedded_auto_keys({T: (["id", "note"], {}, None)}, {T: [["ayanamsha_id"]]}) == set()
    assert ac.vocab_embedded_auto_keys({T: (None, None, None)}, {T: [["ayanamsha_id"]]}) == set()


def test_a_declared_entry_may_rest_on_key_membership_and_is_refused_otherwise():
    e = _entry("signal_type_id")
    own = _own(["id", "signal_type_id", "note"])
    ok, problems = ac.vocab_embedded_exempt(e, T, own, {T: [["chart_id", "signal_type_id"]]})
    assert ok == {(T, "signal_type_id")} and problems == []
    for keys in (None, {T: [["id"]]}, {}):
        pairs, problems = ac.vocab_embedded_exempt(e, T, own, keys)
        assert pairs == set() and problems and "not shown to be a member of a unique / primary key" in problems[0], (keys, problems)


def test_the_key_basis_does_not_widen_the_coverage_of_a_column_that_is_in_no_key():
    pairs, problems = ac.vocab_embedded_exempt(_entry("note"), T, _own(["id", "note"]), {T: [["id"]]})
    assert pairs == set() and problems


# ───────────────────────── (2) examples only ─────────────────────────

def _col(**o):
    d = dict(table=T, column="c", kind="text", rows_sampled=3, complete=True, carries=False, weak=False, embedded=[], key_hits=[], read="whole column")
    d.update(o)
    return d


def _rec(col, exempt=(), auto=()):
    return ac.vocab_values_record([col], [], [T], embedded_exempt=set(exempt), embedded_exempt_auto=set(auto))


@pytest.mark.parametrize("how", ["declared", "engine key rule"])
def test_embedded_examples_are_lifted_for_both_bases(how):
    kw = dict(exempt={(T, "c")}) if how == "declared" else dict(auto={(T, "c")})
    r = _rec(_col(embedded=["Sun in 7th house"]), **kw)
    assert r["v"] == ac.NA and r["vocab_values"]["embedded_exempt"] == [f"{T}.c"] and "EXEMPTED" in r["measured"] and r["vocab_values"]["embedded"] == []
    assert ac.vocab_values_na_problem("Vocab.alias", r) is None


@pytest.mark.parametrize("kw", [dict(key_hits=["planet"]), dict(key_hits=["Ketu"], embedded=["Sun in 7th house"]), dict(probe_unclassified=True)])
@pytest.mark.parametrize("how", ["declared", "engine key rule"])
def test_FORGERY_json_key_hits_and_unclassified_probe_hits_are_never_lifted(kw, how):
    exempt = dict(exempt={(T, "c")}) if how == "declared" else dict(auto={(T, "c")})
    r = _rec(_col(**kw), **exempt)
    assert r["v"] == ac.PARTIAL and r["vocab_values"]["embedded"] and r["vocab_values"]["embedded_exempt"] == [], r["measured"]


def test_a_column_with_examples_in_one_column_and_key_hits_in_another_lifts_only_the_first():
    cols = [_col(column="a", embedded=["Sun in 7th house"]), _col(column="b", key_hits=["Ketu"])]
    r = ac.vocab_values_record(cols, [], [T], embedded_exempt={(T, "a"), (T, "b")})
    assert r["v"] == ac.PARTIAL and [x["column"] for x in r["vocab_values"]["embedded"]] == ["b"] and r["vocab_values"]["embedded_exempt"] == [f"{T}.a"]


def test_the_engine_level_rule_never_hides_a_whole_value_finding():
    cols = [_col(column="ayanamsha_id", carries=True, classes=["rashi"], canonical=["Aries"], spellings=["ARIES"], embedded=["x Aries y"])]
    r = ac.vocab_values_record(cols, [], [T], embedded_exempt_auto={(T, "ayanamsha_id")})
    assert r["v"] == ac.FAIL                                                       # the spelling finding stands; the key rule exempts nothing here


# ───────────────────────── (3) the post-check ─────────────────────────

@pytest.mark.parametrize("field,line", [("contradicted", f"{T}.ref: not a member of any unique key"), ("open", f"{T}.ref (text)"), ("unread", f"{T}.ref: the closure was not read")])
def test_the_post_check_refuses_a_covering_claim_that_is_contradicted_open_or_unread(field, line):
    narr = {"prose_none": {"contradicted": [], "open": [], "unread": [], field: [line]}}
    out = ac.vocab_embedded_post_check(None, {(T, "ref")}, narr)
    assert out and (("left open" if field == "open" else field) in out[0])
    assert ac.vocab_embedded_post_check(None, {(T, "other")}, narr) == []                          # another column's problem does not void this one


def test_the_post_check_passes_a_clean_block():
    assert ac.vocab_embedded_post_check(None, {(T, "ref")}, {"prose_none": {"contradicted": [], "open": [], "unread": []}}) == []


# ───────────────────────── real SQL: free text ayanamsha_id is not exempt ─────────────────────────

def test_REAL_SQL_the_key_rule_end_to_end(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    for t in ("n260_keyed", "n260_free"):
        ac.psql(f"DROP TABLE IF EXISTS {t}")
    ac.psql("CREATE TABLE n260_keyed (id int, ayanamsha_id text, UNIQUE (id, ayanamsha_id))")
    ac.psql("CREATE TABLE n260_free (id int, ayanamsha_id text)")
    for t in ("n260_keyed", "n260_free"):
        ac.psql(f"INSERT INTO {t} VALUES (1, 'true_chitra'), (2, 'lahiri_chitra')")
    try:
        cols = ["id", "ayanamsha_id"]
        for t, expect_key in (("n260_keyed", True), ("n260_free", False)):
            own = {t: (cols, {"id": "integer", "ayanamsha_id": "text"})}
            keys = {"n260_keyed": [["id", "ayanamsha_id"]], "n260_free": []}                     # what the catalog read returns for these two tables
            auto = ac.vocab_embedded_auto_keys(own, keys)
            assert bool(auto) is expect_key
            base = ac.vocab_value_detect(own, None)
            r = ac.vocab_value_detect(own, None, embedded_exempt_auto=auto)
            assert base["v"] == ac.PARTIAL and "embedded vocabulary" in base["measured"]
            if expect_key:
                assert r["v"] == ac.NA and r["vocab_values"]["embedded_exempt"] == [f"{t}.ayanamsha_id"]
            else:
                assert r["v"] == ac.PARTIAL                                                       # free text with no key: the finding stands
    finally:
        for t in ("n260_keyed", "n260_free"):
            ac.psql(f"DROP TABLE IF EXISTS {t}")
