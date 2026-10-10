"""test_n431_json_kinds.py: SS N-431 `vocab_json_kinds` on the Vocab.alias value detector.

`vocab_multi_kind` binds a kind to a FLAT column. In a json(b) document different KEYS hold different KINDS (a rashi under one key, a graha code under another, a house id under a third), so the
value detector read bodha_msr_signals.configuration_jsonb as "no single spelling family" (PARTIAL) and, being a bounded sample, as "read by a bounded sample only". `vocab_json_kinds` binds the kind to the
json PATH (the json_leaf_patterns path syntax), is CHECKED against the whole column, and is CLOSED: a vocabulary value at an undeclared path keeps the column unlifted, with the path named.

Almost everything below is proven WITHOUT a database: the engine's read helper is faked with planted per-path results (the shape `vocab_json_kinds_sql` answers), and the SQL text is only syntax-checked with
pglast (PostgreSQL's own parser) when it is installed. The ONE real-SQL class (`test_REAL_SQL_*`) needs the disposable PostgreSQL fixture and runs in the CI shard that has PostgreSQL.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

T, C = "bodha_msr_signals", "configuration_jsonb"
OWN = {T: ([C, "chart_id"], {C: "jsonb", "chart_id": "uuid"}, None)}
EVIDENCE = "platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:4146"
PATHS = [{"path": "$.sign", "class": "rashi", "family": "name"},
         {"path": "$.graha", "class": "graha", "family": "code"},
         {"path": "$.house", "class": "bhava", "family": "registered_alias"}]
HOUSES_REG = [f"house_{n}" for n in range(1, 10)]               # house_1..house_9: registered aliases; house_10..12 are the canonical ids themselves (house_01..house_12 are the canonical bhava ids)
GRAHA_CODES = ["JUP", "KET_MEAN", "MAR", "MER", "MOON", "RAH_MEAN"]
RASHIS = ["Aquarius", "Aries", "Cancer", "Capricorn", "Gemini"]


def decl(**over):
    d = {"table": T, "column": C, "paths": copy.deepcopy(PATHS), "why": "configuration_jsonb keeps a rashi under sign, a graha code under graha and a house id under house: one kind per key", "evidence": EVIDENCE}
    d.update(over)
    return {"vocab_json_kinds": [d]}


def path_decl(*paths):
    return decl(paths=[{"path": p, "class": c, "family": f} for p, c, f in paths])


@pytest.fixture(autouse=True)
def registered_houses(monkeypatch):
    """bg_ontology's registered aliases are read from the database in production: here house_1..house_9 are registered bhava aliases and Mula a registered nakshatra alias."""
    reg = {h.casefold(): {"classes": ["bhava"]} for h in HOUSES_REG} | {"mula": {"classes": ["nakshatra"]}, "house_01x": {"classes": ["bhava"]}}
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", reg)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


def entry(sig, values, n=None, hits=None, nd=None):
    """One per-path answer of the read: `sig` a key sequence (None = an array element), `values` the distinct values, `hits` the vocabulary-looking ones (default: none)."""
    hits = [] if hits is None else hits
    return {"p": list(sig), "n": n if n is not None else len(values) * 3, "nd": nd if nd is not None else len(values), "vals": list(values), "nh": len(hits), "hits": list(hits)}


def read_of(*entries, rows=40, key_hits=()):
    return {"rows": rows, "nsigs": len(entries), "paths": list(entries), "key_hits": list(key_hits)}


def clean_read(extra=()):
    return read_of(entry(["sign"], RASHIS), entry(["graha"], GRAHA_CODES), entry(["house"], HOUSES_REG),
                   entry(["computed_at"], ["2026-10-01T00:00:00Z"]), entry(["varga"], ["D1", "D9"]), *extra)


def spec_of(d=None):
    sets, problems = ac.vocab_json_kind_sets(d or decl(), OWN)
    assert problems == []
    return sets[(T.lower(), C.lower())]


# ───────────────────────── the declaration's shape (forgeries) ─────────────────────────

def test_a_sound_declaration_has_no_problem():
    assert ac.vocab_json_kinds_problem(decl()) is None
    assert ac.vocab_json_kinds_problem({}) is None


@pytest.mark.parametrize("bad", [
    {"vocab_json_kinds": "configuration_jsonb"},
    {"vocab_json_kinds": []},
    {"vocab_json_kinds": [decl()["vocab_json_kinds"][0]] * 5},
    decl(paths=[]),
    decl(paths="$.graha"),
    decl(paths=[{"path": "$.graha", "class": "graha", "family": "code"}] * 2),                                        # a path declared twice
    path_decl(("graha", "graha", "code")),                                                                          # no leading $
    path_decl(("$", "graha", "code")),                                                                              # the root is no leaf path
    path_decl(("$.a[0]", "graha", "code")),                                                                         # an index number
    path_decl(("$.a[*][*]", "graha", "code")),
    path_decl(("$..a", "graha", "code")),
    path_decl(("$.a b", "graha", "code")),
    path_decl(("$.a.", "graha", "code")),
    path_decl(("$.a", "planet", "code")),                                                                           # not a vocabulary class
    path_decl(("$.a", "graha", "abbreviation")),                                                                    # not a family
    path_decl(("$.m.*", "graha", "code"), ("$.m.k", "rashi", "name")),                                              # a `*` step and a key could match the same leaf
    path_decl(("$.m.*.x", "graha", "code"), ("$.m.y.x", "rashi", "name")),
    decl(column="configuration_jsonb; DROP TABLE x"),
    decl(table="bodha msr"),
    decl(why=""),
    decl(evidence="unverified: it is probably fine"),
    decl(evidence="platform/python-sidecar/no_such_file.py:1"),
])
def test_a_malformed_declaration_is_refused(bad):
    assert ac.vocab_json_kinds_problem(bad)


def test_a_path_entry_with_an_extra_or_missing_field_is_refused():
    d = decl()
    d["vocab_json_kinds"][0]["paths"][0]["note"] = "x"
    assert "exactly the fields" in ac.vocab_json_kinds_problem(d)
    d = decl()
    del d["vocab_json_kinds"][0]["paths"][0]["family"]
    assert "exactly the fields" in ac.vocab_json_kinds_problem(d)
    d = decl()
    d["vocab_json_kinds"][0]["note"] = "x"
    assert "exactly the fields" in ac.vocab_json_kinds_problem(d)


def test_the_same_column_twice_is_refused():
    d = decl()
    d["vocab_json_kinds"].append(copy.deepcopy(d["vocab_json_kinds"][0]))
    assert "listed twice" in ac.vocab_json_kinds_problem(d)


def test_a_duplicate_path_is_named():
    assert "declared twice" in ac.vocab_json_kinds_problem(path_decl(("$.graha", "graha", "code"), ("$.graha", "graha", "name")))


def test_an_overlap_is_named():
    assert "overlaps" in ac.vocab_json_kinds_problem(path_decl(("$.m.*", "graha", "code"), ("$.m.k", "rashi", "name")))


def test_a_key_and_the_array_under_the_same_key_are_two_paths_and_do_not_overlap():
    """A key that holds a string in one document and a list of strings in another is declared as `$.graha` and `$.graha[*]`."""
    assert ac.vocab_json_kinds_problem(path_decl(("$.graha", "graha", "code"), ("$.graha[*]", "graha", "code"))) is None


def test_a_wildcard_member_path_is_a_sound_path():
    assert ac.vocab_json_kinds_problem(path_decl(("$.by_domain.*.graha", "graha", "code"))) is None


def test_the_validator_raises_on_a_bad_declaration():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl(paths=[]))
    ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl())


def test_the_form_is_a_known_declaration_key():
    assert "vocab_json_kinds" in ac.DECL_FORMGAP_KEYS


# ───────────────────────── the sets: the table / column the declaration names ─────────────────────────

def test_the_sets_resolve_for_an_owned_json_column():
    sets, problems = ac.vocab_json_kind_sets(decl(), OWN)
    assert problems == []
    got = sets[(T, C)]
    assert [(p["path"], p["class"], p["family"]) for p in got] == [(p["path"], p["class"], p["family"]) for p in PATHS]
    assert got[0]["tokens"] == ("sign",)


def test_a_table_not_owned_a_missing_column_or_a_non_json_column_is_refused():
    assert "not an owned table" in ac.vocab_json_kind_sets(decl(), {})[1][0]
    assert "not a column" in ac.vocab_json_kind_sets(decl(), {T: (["chart_id"], {"chart_id": "uuid"}, None)})[1][0]
    assert "not a json(b) column" in ac.vocab_json_kind_sets(decl(), {T: ([C], {C: "text"}, None)})[1][0]
    assert "not a json(b) column" in ac.vocab_json_kind_sets(decl(), {T: ([C], {C: "integer"}, None)})[1][0]
    assert ac.vocab_json_kind_sets(decl(), {T: ([C], {C: "json"}, None)})[0] != {}
    assert ac.vocab_json_kind_sets(decl(), {T: (None, None, None)})[0] == {}
    assert ac.vocab_json_kind_sets(decl(), {T: ([C], {}, None)})[0] == {}                                            # column types not read: cannot be checked


def test_a_malformed_declaration_credits_nothing():
    sets, problems = ac.vocab_json_kind_sets(decl(paths=[]), OWN)
    assert sets == {} and "malformed" in problems[0]
    assert ac.vocab_json_kind_sets({}, OWN) == ({}, [])


def test_the_refusal_record_is_no_detector_and_names_the_problem():
    r = ac.vocab_json_kinds_refuse({"vocab_values": {"x": 1}}, ["a: b"], decl())
    assert r["v"] == ac.NO_DET and "a: b" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_json_kinds"


# ───────────────────────── the path syntax ─────────────────────────

@pytest.mark.parametrize("path, tokens", [("$.a", ("a",)), ("$.a.b", ("a", "b")), ("$.a[*]", ("a", None)), ("$.steps[*].note", ("steps", None, "note")), ("$.m.*.k", ("m", "*", "k")), ("$.m.*[*]", ("m", "*", None))])
def test_path_tokens(path, tokens):
    assert ac.vocab_json_path_tokens(path) == tokens


@pytest.mark.parametrize("path, sig, expect", [
    ("$.a", ("a",), True), ("$.a", ("b",), False), ("$.a", ("a", "b"), False), ("$.a", ("a", None), False),
    ("$.a[*]", ("a", None), True), ("$.a[*]", ("a",), False),
    ("$.m.*.k", ("m", "x", "k"), True), ("$.m.*.k", ("m", None, "k"), False), ("$.m.*.k", ("m", "x", "j"), False), ("$.m.*.k", ("m", "k"), False),
])
def test_path_matching_is_exact_in_depth_and_array_steps(path, sig, expect):
    assert ac.vocab_json_path_match(ac.vocab_json_path_tokens(path), sig) is expect


def test_the_sig_label_is_the_declaration_syntax():
    assert ac.vocab_json_sig_label(("steps", None, "note")) == "$.steps[*].note"


# ───────────────────────── one kind per path ─────────────────────────

def test_a_clean_read_verifies_each_path_in_its_own_kind_and_counts_the_non_vocabulary_leaves():
    rep = ac.vocab_json_kinds_report(clean_read(), spec_of())
    assert rep["ok"] is True and rep["violations"] == [] and rep["undeclared_vocabulary"] == [] and rep["unread"] == []
    assert rep["paths"]["$.sign"]["verified"] == sorted(RASHIS) and rep["paths"]["$.graha"]["class"] == "graha"
    assert set(rep["undeclared_non_vocabulary"]) == {"$.computed_at", "$.varga"}
    assert set(rep["values"]) == set(RASHIS) | set(GRAHA_CODES) | set(HOUSES_REG)


def test_forgery_a_graha_code_planted_at_a_path_declared_rashi_is_a_violation_naming_path_and_value():
    rd = read_of(entry(["sign"], RASHIS + ["JUP"]), entry(["graha"], GRAHA_CODES), entry(["house"], HOUSES_REG))
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 1
    assert "$.sign" in rep["violations"][0] and "'JUP'" in rep["violations"][0] and "declared rashi" in rep["violations"][0]


@pytest.mark.parametrize("path, planted, needle", [
    ("graha", "Jupiter", "declared family is 'code'"),          # a name where the path is codes
    ("graha", "jupiter", "declared family is 'code'"),          # an id
    ("graha", "Aries", "declared graha"),                       # another class
    ("graha", "JUP ", "non-canonical spelling"),                # padded
    ("graha", "jup", "non-canonical spelling"),                 # case variant
    ("graha", "Ju", "non-canonical spelling"),                  # short alias
    ("sign", "aries", "declared family is 'name'"),
    ("sign", "Mula", "but the path is declared rashi"),              # a registered nakshatra alias at a rashi path
    ("house", "house_01", "declared family is 'registered_alias'"),   # the canonical id where the path is registered aliases
    ("house", "First House", "declared family is 'registered_alias'"),
    ("sign", "banana", "not a rashi term at all"),              # not vocabulary at all: a declared vocabulary path holds only that kind
    ("sign", "Aries in 7th", "not a rashi term at all"),
])
def test_forgery_a_value_outside_the_declared_kind_of_its_path_is_a_violation(path, planted, needle):
    base = {"sign": RASHIS, "graha": GRAHA_CODES, "house": HOUSES_REG}
    rd = read_of(*[entry([k], v + [planted] if k == path else v) for k, v in base.items()])
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 1, (planted, rep["violations"])
    assert f"${'.' + path}" in rep["violations"][0] and repr(planted) in rep["violations"][0] and needle in rep["violations"][0]


def test_unpadded_house_ids_mix_registered_aliases_and_canonical_ids_in_one_path():
    """house_1..house_9 are registered aliases of house_01..house_09, but house_10..house_12 ARE canonical ids: one path holding house_1..house_12 mixes two spelling families, and the engine says so."""
    rd = read_of(entry(["house"], [f"house_{n}" for n in range(1, 13)]))
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 3 and all("declared family is 'registered_alias'" in v for v in rep["violations"])


def test_a_registered_alias_is_only_in_its_declared_registered_family():
    spec = ac.vocab_json_kind_sets(path_decl(("$.house", "bhava", "registered_code")), OWN)[0][(T, C)]
    rep = ac.vocab_json_kinds_report(read_of(entry(["house"], ["house_1"])), spec)                                  # house_1 is not the NAME_NN shape
    assert rep["ok"] is False and "registered bg_ontology alias" in rep["violations"][0]
    spec = ac.vocab_json_kind_sets(path_decl(("$.nak", "nakshatra", "name")), OWN)[0][(T, C)]
    rep = ac.vocab_json_kinds_report(read_of(entry(["nak"], ["Ashwini", "Mula"])), spec)                              # a registered alias beside canonical names is a mixed path
    assert rep["ok"] is False and "'Mula'" in rep["violations"][0]
    spec = ac.vocab_json_kind_sets(path_decl(("$.nak", "nakshatra", "registered_alias")), OWN)[0][(T, C)]
    assert ac.vocab_json_kinds_report(read_of(entry(["nak"], ["Mula"])), spec)["ok"] is True


def test_a_declared_path_that_matches_nothing_is_listed_and_nothing_verified_is_not_ok():
    rep = ac.vocab_json_kinds_report(read_of(entry(["varga"], ["D1"])), spec_of())
    assert rep["ok"] is False and rep["declared_never_seen"] == ["$.sign", "$.graha", "$.house"]
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), entry(["varga"], ["D1"])), spec_of())
    assert rep["ok"] is True and rep["declared_never_seen"] == ["$.graha", "$.house"]                                # a declared path never seen is allowed, and reported


def test_a_wildcard_member_path_binds_one_kind_to_every_member_and_an_array_step_is_its_own_path():
    spec = ac.vocab_json_kind_sets(path_decl(("$.dom.*.lord", "graha", "code"), ("$.tags[*]", "rashi", "name")), OWN)[0][(T, C)]
    rd = read_of(entry(["dom", "career", "lord"], ["SAT"]), entry(["dom", "wealth", "lord"], ["JUP"]), entry(["tags", None], ["Aries", "Leo"]))
    rep = ac.vocab_json_kinds_report(rd, spec)
    assert rep["ok"] is True and rep["paths"]["$.dom.*.lord"]["verified"] == ["JUP", "SAT"] and rep["undeclared_vocabulary"] == []
    bad = read_of(entry(["dom", "career", "lord"], ["SAT"]), entry(["tags"], ["Aries"], hits=["Aries"]))              # `tags` as a bare string is not `tags[*]`: undeclared
    rep = ac.vocab_json_kinds_report(bad, spec)
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.tags"


# ───────────────────────── the declaration is closed ─────────────────────────

def test_a_vocabulary_value_at_an_undeclared_path_is_named_and_the_column_is_not_ok():
    rd = clean_read([entry(["lord"], ["Mars"], hits=["Mars"])])
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["violations"] == []
    assert rep["undeclared_vocabulary"] == [{"path": "$.lord", "values": ["Mars"], "leaves": 3}]


def test_a_declared_key_name_at_another_depth_is_a_different_path_and_stays_undeclared():
    """`sign` is declared at the root only: a `sign` nested one level down (or inside an array) is NOT that path, so its rashi is undeclared vocabulary."""
    for sig in (["meta", "sign"], ["sign", None], ["items", None, "sign"]):
        rep = ac.vocab_json_kinds_report(clean_read([entry(sig, ["Aries"], hits=["Aries"])]), spec_of())
        assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == ac.vocab_json_sig_label(sig)


def test_a_graha_code_at_an_undeclared_nested_path_is_named_with_its_array_steps():
    rd = clean_read([entry(["chain", None, "actor"], ["JUP"], hits=["JUP"])])
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.chain[*].actor"


@pytest.mark.parametrize("value", ["Su", "jupiter ", "Sun in the 7th house", "Moon", "Ma"])
def test_every_kind_of_vocabulary_looking_value_at_an_undeclared_path_keeps_the_column_open(value):
    rep = ac.vocab_json_kinds_report(clean_read([entry(["note"], [value], hits=[value])]), spec_of())
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.note" and value in rep["undeclared_vocabulary"][0]["values"]


def test_a_hit_the_sql_predicate_over_reports_is_regraded_and_counted_as_non_vocabulary():
    rd = clean_read([entry(["note"], ["plain words"], hits=["plain words"])])                                       # the SQL predicate is over-inclusive on purpose
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is True and rep["undeclared_non_vocabulary"]["$.note"] == 3


def test_more_hits_than_the_cap_with_none_graded_as_vocabulary_is_unread_not_clean():
    junk = [f"junk{i:03d}" for i in range(ac.VOCAB_JSON_KINDS_HIT_CAP + 1)]
    rep = ac.vocab_json_kinds_report(clean_read([entry(["note"], junk[:5], hits=junk)]), spec_of())
    assert rep["ok"] is False and "cannot tell" in rep["unread"][0]


def test_an_embedded_term_at_an_undeclared_path_is_vocabulary_for_the_closure():
    rep = ac.vocab_json_kinds_report(clean_read([entry(["blurb"], ["Saturn aspects the 7th"], hits=["Saturn aspects the 7th"])]), spec_of())
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.blurb" and rep["emb"] == ["Saturn aspects the 7th"]


# ───────────────────────── a truncated read is unread ─────────────────────────

def test_a_declared_path_with_more_distinct_values_than_the_cap_is_unread():
    many = [f"v{i}" for i in range(ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1)]
    rd = read_of(entry(["sign"], many, nd=len(many)), entry(["graha"], GRAHA_CODES))
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and "more than" in rep["unread"][0] and "$.sign" in rep["unread"][0]


def test_a_path_matching_two_declared_paths_is_unread_never_double_counted():
    spec = spec_of()
    spec = spec + [dict(spec[0], path="$.dup", tokens=("sign",))]                                                    # a forged overlap that got past the validator
    rep = ac.vocab_json_kinds_report(clean_read(), spec)
    assert rep["ok"] is False and "ambiguous" in rep["unread"][0]


def test_the_fetch_reads_a_timeout_a_malformed_answer_and_too_many_paths_as_unread(monkeypatch):
    def boom(sql, *a, **k):
        raise ac.Unknown("ERROR:  canceling statement due to statement timeout")
    monkeypatch.setattr(ac, "scalar", boom)
    assert "statement timeout" in ac.vocab_fetch_json_kinds(T, C, None)["unread"]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1}))
    assert "unread" in ac.vocab_fetch_json_kinds(T, C, None)
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1, "nsigs": 1, "paths": [{"p": ["a"], "n": 1, "nd": 1, "nh": 0, "vals": [3], "hits": []}], "key_hits": []}))
    assert "unread" in ac.vocab_fetch_json_kinds(T, C, None)                                                       # a non-string value
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1, "nsigs": 1, "paths": [{"p": [3], "n": 1, "nd": 1, "nh": 0, "vals": [], "hits": []}], "key_hits": []}))
    assert "unread" in ac.vocab_fetch_json_kinds(T, C, None)                                                       # a key path that is not strings
    many = [entry([f"k{i}"], ["x"]) for i in range(ac.VOCAB_JSON_KINDS_MAX_SIGS + 1)]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps(read_of(*many)))
    assert "more than" in ac.vocab_fetch_json_kinds(T, C, None)["unread"]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1, "nsigs": ac.VOCAB_JSON_KINDS_MAX_SIGS + 5, "paths": [], "key_hits": []}))
    assert "more than" in ac.vocab_fetch_json_kinds(T, C, None)["unread"]                                          # the statement itself says it cut the list
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps(clean_read()))
    got = ac.vocab_fetch_json_kinds(T, C, None)
    assert "unread" not in got and len(got["paths"]) == 5


def test_the_statement_is_one_read_only_recursive_select_over_the_scope():
    sql = ac.vocab_json_kinds_sql(T, C, "chart_id = 'x' AND graph_node_strength_contribution_jsonb IS NOT NULL")
    assert sql.lstrip().upper().startswith("WITH RECURSIVE") and "chart_id = 'x'" in sql and f"LIMIT {ac.VOCAB_JSON_KINDS_MAX_SIGS + 1}" in sql
    assert f"<= {ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1}" in sql and f"<= {ac.VOCAB_JSON_KINDS_HIT_CAP + 1}" in sql
    assert all(w not in sql.upper() for w in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "CREATE "))
    assert "chart_id" not in ac.vocab_json_kinds_sql(T, C, None)
    assert sql.count('"configuration_jsonb"') == 2                                                                  # the column is read once, in the scope CTE (and its NULL test)


def test_the_statement_parses_with_postgresqls_own_parser():
    pglast = pytest.importorskip("pglast")
    for where in (None, "chart_id = 'x'"):
        assert len(pglast.parse_sql(ac.vocab_json_kinds_sql(T, C, where))) == 1


# ───────────────────────── end to end through the value detector ─────────────────────────

def _sample(values, complete=False, key_hits=()):
    return dict(values=list(values), emb=[], key_hits=list(key_hits), complete=complete, rows=200, oversized=0, deep=0, leaves=300, keys=40)


@pytest.fixture
def detect(monkeypatch):
    """`run(read, ...)`: the detector over a bounded first-rows sample (a rashi, a graha code and a house id: mixed spelling families) with the whole-column read answered from `read`."""
    calls = []
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, cols_kinds, where=None: {c: (_sample(["Aries", "JUP", "house_1"]) if c == C else dict(_sample(["x"]), complete=True)) for c, _k in cols_kinds})
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))

    def run(read=None, declared=True, raise_=None, scopes=None, own=None, d=None):
        def scalar(sql, *a, **k):
            calls.append(sql)
            if raise_ is not None:
                raise raise_
            return json.dumps(read)
        monkeypatch.setattr(ac, "scalar", scalar)
        own = own or OWN
        sets = ac.vocab_json_kind_sets(d or decl(), own)[0] if declared else None
        return ac.vocab_value_detect({k: v[:2] for k, v in own.items()}, None, json_kind_sets=sets, scopes=scopes)
    run.calls = calls
    return run


def _col(out):
    return next(c for c in out["vocab_values"]["found"] if c["column"] == C)


def test_without_the_declaration_the_column_is_partial_as_today(detect):
    out = detect(clean_read(), declared=False)
    assert out["v"] == ac.PARTIAL and "MIXED canonical spelling families" in out["measured"] and "read by a bounded sample only" in out["measured"]
    assert detect.calls == []                                                                                       # nothing new is read for an undeclared asset


def test_with_the_declaration_both_findings_are_lifted_over_the_whole_column(detect):
    out = detect(clean_read())
    assert out["v"] == ac.PASS, out["measured"]
    assert "MIXED" not in out["measured"] and "bounded sample" not in out["measured"] and "JSON-KINDS, one kind per path, verified over the whole column" in out["measured"]
    col = _col(out)
    assert col["complete"] is True and col["mixed"] is False and col["json_kinds"]["ok"] is True
    assert out["vocab_values"]["json_kinds"][f"{T}.{C}"]["paths"]["$.graha"]["verified"] == sorted(GRAHA_CODES)
    assert "2 undeclared path(s) hold no vocabulary, not graded" in out["measured"] and "$.computed_at" in out["measured"]    # the limit is printed on the certificate text
    assert len(detect.calls) == 1


def test_a_graha_code_planted_at_a_rashi_path_makes_the_column_fail_naming_path_and_value(detect):
    rd = read_of(entry(["sign"], RASHIS + ["JUP"]), entry(["graha"], GRAHA_CODES), entry(["house"], HOUSES_REG))
    out = detect(rd)
    assert out["v"] == ac.FAIL and "contradicted by its data" in out["measured"] and "$.sign" in out["measured"] and "'JUP'" in out["measured"]


def test_a_declared_path_holding_only_non_vocabulary_is_a_fail_not_a_vacuous_pass(detect):
    rd = read_of(entry(["sign"], ["banana"]), entry(["graha"], GRAHA_CODES), entry(["house"], HOUSES_REG))
    assert detect(rd)["v"] == ac.FAIL
    rd = read_of(entry(["sign"], ["banana"]))                                                                       # nothing canonical anywhere in the column
    out = detect(rd)
    assert out["v"] == ac.FAIL and "$.sign" in out["measured"]


def test_a_vocabulary_value_at_an_undeclared_path_is_not_lifted_and_the_path_is_named(detect):
    out = detect(clean_read([entry(["lord"], ["Mars"], hits=["Mars"])]))
    assert out["v"] == ac.PARTIAL, out["measured"]
    assert "MIXED canonical spelling families" in out["measured"]                                                   # the finding is NOT lifted
    assert "does not close the column" in out["measured"] and "$.lord" in out["measured"] and "'Mars'" in out["measured"]
    col = _col(out)
    assert col["mixed"] is True and col["json_kind_open"][0]["path"] == "$.lord"
    assert "JSON-KINDS" not in out["measured"]


def test_a_truncated_read_is_no_detector_never_pass(detect):
    out = detect(raise_=ac.Unknown("ERROR:  canceling statement due to statement timeout"))
    assert out["v"] == ac.NO_DET and "could not be read whole" in out["measured"] and "statement timeout" in out["measured"]
    assert "never PASS" in out["measured"]
    many = [entry([f"k{i}"], ["x"]) for i in range(ac.VOCAB_JSON_KINDS_MAX_SIGS + 1)]
    out = detect(read_of(*many))
    assert out["v"] == ac.NO_DET and "more than" in out["measured"]
    out = detect(read_of(entry(["sign"], [f"v{i}" for i in range(ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1)])))
    assert out["v"] == ac.NO_DET and "$.sign" in out["measured"]


def test_a_shared_table_whose_asset_rows_are_not_named_is_refused_without_reading(detect):
    scopes = {T: {"where": None, "label": "shared table, the asset's rows are not named by its count_sql: read whole (every asset's rows in it)"}}
    out = detect(clean_read(), scopes=scopes)
    assert detect.calls == [] and out["v"] == ac.NO_DET and "shared and the asset's own rows are not named" in out["measured"]


def test_a_scoped_shared_table_is_read_with_its_predicate(detect):
    scopes = {T: {"where": "graph_node_strength_contribution_jsonb IS NOT NULL", "label": "scoped"}}
    out = detect(clean_read(), scopes=scopes)
    assert len(detect.calls) == 1 and "graph_node_strength_contribution_jsonb IS NOT NULL" in detect.calls[0] and out["v"] == ac.PASS


def test_the_declaration_only_touches_its_own_column(detect):
    own = {T: ([C, "epistemic_jsonb", "chart_id"], {C: "jsonb", "epistemic_jsonb": "jsonb", "chart_id": "uuid"}, None)}
    out = detect(clean_read(), own=own)
    cols = {c["column"]: c for c in out["vocab_values"]["found"]}
    assert cols[C]["json_kinds"]["ok"] is True
    assert "epistemic_jsonb" not in cols and detect.calls and all('"epistemic_jsonb"' not in q for q in detect.calls)      # the sibling column is neither lifted nor read by the declared read
    assert len(detect.calls) == 1


def test_a_violation_elsewhere_in_the_column_keeps_a_visible_fail_over_an_unread_note(detect, monkeypatch):
    """The ordinary reading of the sample finds ' JUP' (a padded code): a truncated declared read must not turn that FAIL into a NO_DETECTOR."""
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, ck, where=None: {c: (_sample(["Aries", " JUP", "house_1"]) if c == C else dict(_sample(["x"]), complete=True)) for c, _k in ck})
    out = detect(raise_=ac.Unknown("ERROR:  canceling statement due to statement timeout"))
    assert out["v"] == ac.FAIL


def test_key_hits_of_the_whole_column_are_never_lifted(detect):
    out = detect(clean_read() | {"key_hits": ["planet"]})
    assert out["v"] == ac.PARTIAL and "embedded vocabulary, spelling unchecked" in out["measured"] and "planet" in out["measured"]


def test_the_flat_form_is_untouched_by_the_new_keyword(monkeypatch):
    """vocab_value_detect without json_kind_sets reads a json column exactly as before (the sample)."""
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, cols_kinds, where=None: {c: _sample(["Aries", "JUP"]) for c, _k in cols_kinds})
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: pytest.fail("no whole-column read may happen without the declaration"))
    out = ac.vocab_value_detect({k: v[:2] for k, v in OWN.items()}, None)
    assert out["v"] == ac.PARTIAL and "MIXED" in out["measured"]


# ───────────────────────── real SQL on a disposable PostgreSQL (CI shard with PostgreSQL; NOT run on the loaded local Mac, SS N-436) ─────────────────────────

def _real_table(pg, monkeypatch, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    ac.psql(f"CREATE TABLE {T} (chart_id uuid, signal_class text, {C} jsonb)")
    for cid, cls, doc in rows:
        body = "NULL" if doc is None else ac._vocab_lit(json.dumps(doc)) + "::jsonb"
        ac.psql(f"INSERT INTO {T} VALUES ({ac._vocab_lit(cid)}, {ac._vocab_lit(cls)}, {body})")


CID = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "00000000-0000-0000-0000-000000000001"


def test_REAL_SQL_the_read_groups_leaves_by_key_path_scoped_and_capped(monkeypatch, disposable_pg):
    rows = [(CID, "a", {"sign": "Aries", "graha": "JUP", "house": "house_1", "varga": "D1", "steps": [{"note": "Mars"}, {"note": "plain words"}], "n": 3, "by": {"career": {"lord": "SAT"}}}),
            (CID, "a", {"sign": "Aries", "graha": "MAR", "computed_at": "2026-10-01T00:00:00Z"}),
            (CID, "b", {"sign": "Leo", "tags": ["Aries", "Leo"]}),
            (OTHER, "a", {"sign": "Jupiter", "stray": "Mars"}),
            (CID, "a", None)]
    _real_table(disposable_pg, monkeypatch, rows)
    try:
        got = ac.vocab_fetch_json_kinds(T, C, f"chart_id = '{CID}' AND signal_class = 'a'")
        assert "unread" not in got, got
        assert got["rows"] == 2
        by = {tuple(e["p"]): e for e in got["paths"]}
        assert by[("sign",)]["vals"] == ["Aries"] and by[("sign",)]["n"] == 2 and by[("graha",)]["vals"] == ["JUP", "MAR"]
        assert by[("steps", None, "note")]["vals"] == ["Mars", "plain words"] and by[("steps", None, "note")]["nh"] >= 1 and "Mars" in by[("steps", None, "note")]["hits"]
        assert by[("by", "career", "lord")]["vals"] == ["SAT"] and ("n",) not in by                                   # a number is no string leaf
        assert ("stray",) not in by and ("tags",) not in by                                                          # the other chart / the other signal class are out of scope
        assert got["key_hits"] == []
        whole = ac.vocab_fetch_json_kinds(T, C, None)
        assert {tuple(e["p"]) for e in whole["paths"]} >= {("stray",), ("tags", None)}
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_REAL_SQL_the_detector_lifts_a_clean_declared_column_and_names_an_undeclared_vocabulary_path(monkeypatch, disposable_pg):
    clean = [(CID, "a", {"sign": s, "graha": g, "house": h, "varga": "D1"}) for s, g, h in zip(RASHIS, GRAHA_CODES, HOUSES_REG)]
    _real_table(disposable_pg, monkeypatch, clean)
    try:
        own = {T: ([C, "chart_id", "signal_class"], {C: "jsonb", "chart_id": "uuid", "signal_class": "text"}, None)}
        sets = ac.vocab_json_kind_sets(decl(), own)[0]
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PASS, out["measured"]
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Aries\", \"lord\": \"Mars\"}}'::jsonb)")
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PARTIAL and "$.lord" in out["measured"] and "MIXED" in out["measured"]
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"JUP\"}}'::jsonb)")
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.FAIL and "$.sign" in out["measured"] and "'JUP'" in out["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")
