"""test_n431_json_kinds_keys.py: SS N-431 / N-458 `vocab_json_kinds`, EXTENSION (iii): KEYS whose leaves are not strings (`vocab_keys`).

The base form lists as `key_hits` every json KEY (at any depth) that names a term or a class word, except the key that ENDS a declared string-leaf path (the declaration itself). bo_laksana_rerank's
configuration_jsonb has graha CODES as keys on number leaves (`tally.JUP`, `.MAR` ...) and class words / house synonyms as keys on non-string leaves (`house`, `signs`, `grahas`, `nakshatras`,
`second_house`, `twelfth_house`): no path can be declared for them, so the cell stayed PARTIAL for those keys whatever else was declared.

`vocab_keys` is an opt-in list inside a `vocab_json_kinds` column entry. Each item explains the keys DIRECTLY under one prefix (exact path prefix, exact depth) in one of two ways:

    {"prefix": "$.tally", "key_class": "graha", "key_family": "code", "why": "...", "evidence": "file.py:line"}      # the keys ARE vocabulary terms: each actual key must be a canonical member of that class
                                                                                                                  # and family (the keys' SPELLING is censused); a key outside it is a violation (FAIL)
    {"prefix": "$", "structural_keys": ["house", "signs", ...], "why": "...", "evidence": [... file.py:line ...]}  # an explicit closed list of class-word keys that are structure, not vocabulary; every name must
                                                                                                                  # be a string constant of a cited producer file

Only keys explained this way (exact prefix, exact depth, and for the structural form the listed name) leave `key_hits`; anything else remains a hit. Opt-in: no vocab_keys, no change.
Proven without a database except the `test_REAL_SQL_*` tests (the disposable PostgreSQL fixture).
"""
from __future__ import annotations

import ast
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
EV_TALLY = "platform/python-sidecar/ga_writers/ga_structural_writer.py:6463"
EV_STRUCT = ["platform/python-sidecar/ga_writers/ga_structural_writer.py:4362", "platform/python-sidecar/ga_writers/ga_sensitive_degree_writer.py:242"]
STRUCT_KEYS = ["house", "signs", "grahas", "nakshatras", "second_house", "twelfth_house"]
CODES = ["JUP", "MAR", "MER", "MOON", "SAT", "SUN", "VEN"]
RASHIS = ["Aquarius", "Aries", "Cancer"]
PATHS = [{"path": "$.sign", "class": "rashi", "family": "name"}]


def terms_item(prefix="$.tally", cls="graha", family="code", **over):
    d = {"prefix": prefix, "key_class": cls, "key_family": family, "why": "the tally object keys each count by the graha subject code of the producer", "evidence": EV_TALLY}
    d.update(over)
    return d


def struct_item(keys=None, prefix="$", **over):
    d = {"prefix": prefix, "structural_keys": list(STRUCT_KEYS if keys is None else keys), "why": "these root keys are the object structure the producers write, not graha or house vocabulary",
         "evidence": list(EV_STRUCT)}
    d.update(over)
    return d


def decl(*items, **over):
    d = {"table": T, "column": C, "paths": copy.deepcopy(PATHS), "vocab_keys": copy.deepcopy(list(items) if items else [terms_item(), struct_item()]),
         "why": "configuration_jsonb keeps a rashi under sign; the tally keys are graha codes; the root structure keys are named", "evidence": EVIDENCE}
    d.update(over)
    return {"vocab_json_kinds": [d]}


@pytest.fixture(autouse=True)
def registered_houses(monkeypatch):
    reg = {f"house_{n}": {"classes": ["bhava"]} for n in range(1, 10)} | {"mula": {"classes": ["nakshatra"]}}
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", reg)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


def entry(sig, values, n=None, hits=None, nd=None):
    hits = [] if hits is None else hits
    return {"p": list(sig), "n": n if n is not None else len(values) * 3, "nd": nd if nd is not None else len(values), "vals": list(values), "nh": len(hits), "hits": list(hits)}


def read_of(*entries, rows=40, key_hits=(), key_sets=None):
    r = {"rows": rows, "nsigs": len(entries), "paths": list(entries), "key_hits": list(key_hits)}
    if key_sets is not None:
        r["key_sets"] = key_sets
    return r


def keyset(*keys):
    return {"keys": list(keys)}


def clean_read(tally=CODES, struct=("house", "signs", "second_house"), **kw):
    return read_of(entry(["sign"], RASHIS), entry(["computed_at"], ["2026-10-01T00:00:00Z"]), key_sets=[keyset(*tally), keyset(*struct)], **kw)


def spec_of(d=None):
    sets, problems = ac.vocab_json_kind_sets(d or decl(), OWN)
    assert problems == []
    return sets[(T.lower(), C.lower())]


# ───────────────────────── the declaration's shape ─────────────────────────

def test_a_declaration_with_both_key_forms_is_sound():
    assert ac.vocab_json_kinds_problem(decl()) is None
    assert ac.vocab_json_kinds_problem(decl(struct_item(keys=["house", "signs"], evidence=EV_STRUCT[0]), terms_item())) is None                 # one evidence pointer as a string
    assert ac.vocab_json_kinds_problem(decl(terms_item("$")) ) is None                                              # the root's own keys


def test_the_keys_form_constants():
    assert ac.VOCAB_JSON_KEYS_MAX == 8 and ac.VOCAB_JSON_KEYS_MAX_STRUCTURAL == 32 and ac.VOCAB_JSON_KEYS_MAX_DISTINCT == 64
    assert "vocab_keys" in ac.VOCAB_JSON_KINDS_OPTIONAL_FIELDS


@pytest.mark.parametrize("bad", [
    terms_item(extra="x"),                                                                                          # an unknown field
    {k: v for k, v in terms_item().items() if k != "why"},
    {k: v for k, v in terms_item().items() if k != "evidence"},
    {k: v for k, v in terms_item().items() if k != "key_family"},                                                   # a class without a family
    terms_item(structural_keys=["house"]),                                                                          # both forms in one item
    terms_item(cls="planet"),
    terms_item(family="abbreviation"),
    terms_item(prefix="tally"),
    terms_item(prefix="$."),
    terms_item(prefix="$..a"),
    terms_item(prefix="$.a[0]"),
    terms_item(prefix="$.a b"),
    terms_item(why=""),
    terms_item(why="x"),
    terms_item(evidence="unverified: it is probably fine, trust me"),
    terms_item(evidence="platform/python-sidecar/no_such_file.py:1"),
    struct_item(keys=[]),
    struct_item(keys=["house", "house"]),
    struct_item(keys=["house", ""]),
    struct_item(keys=["house", "  "]),
    struct_item(keys=["house", 3]),
    struct_item(keys=["house", "bad\x00key"]),
    struct_item(keys=["house", "bad​key"]),
    struct_item(keys=[f"k{i}" for i in range(33)]),
    struct_item(keys="house"),
    struct_item(keys=["house", "no_such_structural_key_in_any_cited_file"]),                                        # not a string constant of any cited producer file
    struct_item(evidence="platform/scripts/governance/asset_declarations.json:1"),                                    # a structural list must be backed by Python source it can be checked in
    struct_item(evidence=[]),
    struct_item(evidence=[EV_STRUCT[0]] * 13),
])
def test_a_malformed_keys_item_is_refused(bad):
    assert ac.vocab_json_kinds_problem(decl(bad))


def test_the_vocab_keys_list_itself_is_bounded_and_prefixes_do_not_repeat_or_overlap():
    assert ac.vocab_json_kinds_problem(decl()) is None
    items = [terms_item(f"$.t{i}") for i in range(9)]
    assert "1 to 8" in ac.vocab_json_kinds_problem(decl(*items))
    assert "1 to 8" in ac.vocab_json_kinds_problem({"vocab_json_kinds": [dict(decl()["vocab_json_kinds"][0], vocab_keys=[])]})
    assert "twice" in ac.vocab_json_kinds_problem(decl(terms_item("$.tally"), struct_item(prefix="$.tally")))
    assert "overlaps" in ac.vocab_json_kinds_problem(decl(terms_item("$.by.*"), terms_item("$.by.x")))
    assert ac.vocab_json_kinds_problem(decl(terms_item("$.by"), terms_item("$.by.deep"))) is None                   # different depths are different prefixes


def test_a_column_entry_with_an_unknown_extra_field_is_still_refused():
    d = decl()
    d["vocab_json_kinds"][0]["note"] = "x"
    assert "exactly the fields" in ac.vocab_json_kinds_problem(d)
    d = decl()
    del d["vocab_json_kinds"][0]["evidence"]
    assert "exactly the fields" in ac.vocab_json_kinds_problem(d)
    assert ac.vocab_json_kinds_problem({"vocab_json_kinds": [{k: v for k, v in decl()["vocab_json_kinds"][0].items() if k != "vocab_keys"}]}) is None      # vocab_keys is optional


def test_the_validator_raises_on_a_bad_keys_item():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl(terms_item(prefix="tally")))
    ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl())


# ───────────────────────── the sets ─────────────────────────

def test_the_sets_carry_the_key_specs_on_the_path_list_so_the_call_chain_is_unchanged():
    spec = spec_of()
    assert [s["path"] for s in spec] == ["$.sign"]                                                                  # a plain list of path specs, as before
    ks = spec.key_specs
    assert [(k["prefix"], k["tokens"], k["mode"]) for k in ks] == [("$.tally", ("tally",), "terms"), ("$", (), "structural")]
    assert ks[0]["class"] == "graha" and ks[0]["family"] == "code" and ks[1]["names"] == STRUCT_KEYS


def test_a_declaration_without_vocab_keys_has_no_key_specs():
    d = decl()
    del d["vocab_json_kinds"][0]["vocab_keys"]
    assert list(getattr(spec_of(d), "key_specs", [])) == []


# ───────────────────────── the keys are graded ─────────────────────────

def test_keys_declared_as_terms_are_graded_member_by_member_and_counted_as_values():
    rep = ac.vocab_json_kinds_report(clean_read(), spec_of())
    assert rep["ok"] is True and rep["violations"] == [] and rep["unclosed"] == [] and rep["unread"] == []
    tally = rep["key_decls"]["$.tally"]
    assert tally["mode"] == "terms" and tally["keys"] == CODES and tally["verified"] == CODES
    assert set(CODES) <= set(rep["values"])                                                                         # the spelling of the keys is part of the column's census


@pytest.mark.parametrize("planted, needle", [
    ("Jup", "non-canonical spelling"),                                                                              # a case variant of a code
    ("jup", "non-canonical spelling"),
    ("Jupiter", "declared family is 'code'"),                                                                       # a name where the keys are codes
    ("jupiter", "declared family is 'code'"),
    ("Aries", "declared graha"),                                                                                    # another class
    ("tally_total", "not a graha term at all"),                                                                     # not a term
    ("JUP ", "non-canonical spelling"),
])
def test_a_key_outside_the_declared_class_is_a_violation_naming_prefix_and_key(planted, needle):
    rep = ac.vocab_json_kinds_report(clean_read(tally=CODES + [planted]), spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 1, rep["violations"]
    v = rep["violations"][0]
    assert "$.tally" in v and repr(planted) in v and needle in v and "KEYS" in v


def test_a_structural_key_is_not_graded_and_the_unseen_names_are_listed():
    rep = ac.vocab_json_kinds_report(clean_read(struct=("house", "signs")), spec_of())
    st = rep["key_decls"]["$"]
    assert rep["ok"] is True and st["mode"] == "structural" and st["seen"] == ["house", "signs"]
    assert st["unseen"] == ["grahas", "nakshatras", "second_house", "twelfth_house"]


def test_a_keys_item_that_explains_nothing_is_declared_but_unread_and_blocks_the_cell():
    rep = ac.vocab_json_kinds_report(clean_read(tally=()), spec_of())
    assert rep["ok"] is False and any("declared but unread" in u and "$.tally" in u for u in rep["unclosed"])
    rep = ac.vocab_json_kinds_report(clean_read(struct=()), spec_of())
    assert rep["ok"] is False and any("declared but unread" in u and "'$'" in u for u in rep["unclosed"])


def test_a_structural_name_that_is_a_canonical_term_is_refused_as_structure():
    """`JUP` is a vocabulary spelling: it belongs in key_class (censused), never in the list of keys that are merely structure."""
    d = decl(struct_item(keys=["house", "JUP"]), terms_item("$.tally"))
    rep = ac.vocab_json_kinds_report(clean_read(struct=("house", "JUP")), spec_of(d))
    assert rep["ok"] is False and "'JUP'" in rep["violations"][0] and "canonical" in rep["violations"][0] and "key_class" in rep["violations"][0]


def test_a_structural_alias_key_such_as_second_house_is_structure_not_a_term():
    rep = ac.vocab_json_kinds_report(clean_read(struct=("second_house", "twelfth_house")), spec_of())
    assert rep["ok"] is True


def test_missing_key_sets_in_the_read_are_unread_never_clean():
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS)), spec_of())
    assert rep["ok"] is False and "vocab_keys" in rep["unread"][0]
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), key_sets=[keyset(*CODES)]), spec_of())          # one answer for two items
    assert rep["ok"] is False and rep["unread"]


def test_more_keys_than_the_cap_under_a_terms_prefix_are_unread():
    many = [f"k{i}" for i in range(ac.VOCAB_JSON_KEYS_MAX_DISTINCT + 1)]
    rep = ac.vocab_json_kinds_report(clean_read(tally=many), spec_of())
    assert rep["ok"] is False and any("more than" in u for u in rep["unread"])


def test_key_hits_the_statement_left_are_still_reported_unchanged():
    rep = ac.vocab_json_kinds_report(clean_read(key_hits=["planet"]), spec_of())
    assert rep["key_hits"] == ["planet"]


def test_the_label_prints_the_keys_explained_so_the_limit_is_on_the_certificate_text():
    text = ac.vocab_json_kinds_label({"json_kinds": ac.vocab_json_kinds_report(clean_read(), spec_of())})
    assert "$.tally" in text and "graha/code" in text and "JUP" in text and "structural" in text and "house" in text


# ───────────────────────── the statement ─────────────────────────

def _keys(*items):
    return [{"tokens": k["tokens"], "names": (k["names"] if k["mode"] == "structural" else None)} for k in spec_of(decl(*items)).key_specs]


def test_the_statement_without_keys_is_the_legacy_statement():
    sql = ac.vocab_json_kinds_sql(T, C, None, [("sign",)])
    assert "key_sets" not in sql and ac.vocab_json_kinds_sql(T, C, None, [("sign",)], None) == sql and ac.vocab_json_kinds_sql(T, C, None, [("sign",)], []) == sql


def test_the_statement_explains_only_the_exact_prefix_depth_and_listed_names():
    sql = ac.vocab_json_kinds_sql(T, C, None, [("sign",)], _keys(terms_item(), struct_item()))
    assert "NOT (jsonb_typeof(v) = 'string' AND" in sql                                                            # the declared string-leaf rule is still there
    assert "jsonb_array_length(p) = 2" in sql and "(p -> 0) = to_jsonb('tally'::text)" in sql                       # the exact prefix, one key deeper
    assert "jsonb_array_length(p) = 1" in sql and "= ANY(ARRAY['house','signs'" in sql                              # the structural names are an exact list
    assert "'key_sets'" in sql


def test_a_key_name_is_always_a_quoted_literal_never_spliced_raw():
    keys = [{"tokens": ("it's",), "names": ["o'brien", "x'); DROP TABLE t; --"]}]
    sql = ac.vocab_json_kinds_sql(T, C, None, None, keys)
    assert "'o''brien'" in sql and "'x''); DROP TABLE t; --'" in sql and "to_jsonb('it''s'::text)" in sql


def test_the_statement_with_keys_is_one_read_only_select_and_parses_with_postgresqls_parser():
    pglast = pytest.importorskip("pglast")
    keys = _keys(terms_item(), struct_item(), terms_item("$.by.*.tally"), terms_item("$.rows[*].t"))
    for where in (None, "chart_id = 'x'"):
        sql = ac.vocab_json_kinds_sql(T, C, where, [("sign",), ("by", "*", "lord")], keys)
        assert len(pglast.parse_sql(sql)) == 1
        assert all(w not in sql.upper() for w in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "CREATE "))
    assert f"LIMIT {ac.VOCAB_JSON_KEYS_MAX_DISTINCT + 1}" in sql


def test_the_fetch_checks_the_key_sets_answer(monkeypatch):
    keys = _keys(terms_item(), struct_item())
    ok = dict(clean_read())
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps(ok))
    got = ac.vocab_fetch_json_kinds(T, C, None, [("sign",)], keys)
    assert "unread" not in got and got["key_sets"] == ok["key_sets"]
    for bad in ({"rows": 1, "nsigs": 0, "paths": [], "key_hits": []},                                              # no key_sets at all though keys were asked
                dict(ok, key_sets=[keyset("JUP")]),                                                                # one answer for two items
                dict(ok, key_sets=[keyset("JUP"), {"keys": [3]}]),
                dict(ok, key_sets=[keyset("JUP"), "x"])):
        monkeypatch.setattr(ac, "scalar", lambda *a, _b=bad, **k: json.dumps(_b))
        assert "unread" in ac.vocab_fetch_json_kinds(T, C, None, [("sign",)], keys)
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps(clean_read()))
    assert "unread" not in ac.vocab_fetch_json_kinds(T, C, None, [("sign",)])                                       # nothing asked, nothing checked


# ───────────────────────── end to end through the value detector ─────────────────────────

def _sample(values, complete=False, key_hits=()):
    return dict(values=list(values), emb=[], key_hits=list(key_hits), complete=complete, rows=200, oversized=0, deep=0, leaves=300, keys=40)


@pytest.fixture
def detect(monkeypatch):
    calls = []
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, ck, where=None: {c: (_sample(["Aries", "JUP"]) if c == C else dict(_sample(["x"]), complete=True)) for c, _k in ck})
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))

    def run(read, d=None):
        def scalar(sql, *a, **k):
            calls.append(sql)
            return json.dumps(read)
        monkeypatch.setattr(ac, "scalar", scalar)
        sets = ac.vocab_json_kind_sets(d or decl(), OWN)[0]
        return ac.vocab_value_detect({k: v[:2] for k, v in OWN.items()}, None, json_kind_sets=sets)
    run.calls = calls
    return run


def test_the_explained_keys_lift_the_column_to_pass_and_the_text_names_them(detect):
    out = detect(clean_read())
    assert out["v"] == ac.PASS, out["measured"]
    assert "$.tally" in out["measured"] and "structural" in out["measured"]
    assert out["vocab_values"]["json_kinds"][f"{T}.{C}"]["key_decls"]["$.tally"]["verified"] == CODES
    assert "'key_sets'" in detect.calls[0]


def test_a_key_hit_the_declaration_does_not_explain_keeps_the_column_partial(detect):
    out = detect(clean_read(key_hits=["planet"]))
    assert out["v"] == ac.PARTIAL and "embedded vocabulary, spelling unchecked" in out["measured"] and "planet" in out["measured"]


def test_a_misspelt_code_key_makes_the_column_fail_naming_prefix_and_key(detect):
    out = detect(clean_read(tally=CODES + ["Jup"]))
    assert out["v"] == ac.FAIL and "$.tally" in out["measured"] and "'Jup'" in out["measured"]


def test_a_keys_item_nothing_read_reads_partial_declared_but_unread(detect):
    out = detect(clean_read(tally=()))
    assert out["v"] == ac.PARTIAL and "declared but unread" in out["measured"] and "$.tally" in out["measured"]


def test_a_read_that_lacks_the_key_sets_is_no_detector_never_pass(detect):
    out = detect(read_of(entry(["sign"], RASHIS)))
    assert out["v"] == ac.NO_DET and "vocab_keys" in out["measured"]


def test_without_vocab_keys_the_read_is_asked_the_legacy_way(detect, monkeypatch):
    d = decl()
    del d["vocab_json_kinds"][0]["vocab_keys"]
    out = detect(read_of(entry(["sign"], RASHIS), key_hits=["house"]), d)
    assert out["v"] == ac.PARTIAL and "house" in out["measured"] and "key_sets" not in detect.calls[0]


# ───────────────────────── real SQL on a disposable PostgreSQL ─────────────────────────

def _real_table(pg, monkeypatch, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    ac.psql(f"CREATE TABLE {T} (chart_id uuid, signal_class text, {C} jsonb)")
    for cid, cls, doc in rows:
        ac.psql(f"INSERT INTO {T} VALUES ({ac._vocab_lit(cid)}, {ac._vocab_lit(cls)}, {ac._vocab_lit(json.dumps(doc))}::jsonb)")


CID = "482012f1-710e-4a25-994a-93821f5871aa"
DOC = {"sign": "Aries", "graha": "Mars", "tally": {"JUP": 3, "MAR": 2, "SUN": 1}, "house": 7, "signs": ["Aries", "Leo"], "second_house": 2, "nest": {"house": 3, "tally": {"VEN": 1}}}


def test_REAL_SQL_only_the_exact_prefix_depth_and_names_leave_key_hits(monkeypatch, disposable_pg):
    _real_table(disposable_pg, monkeypatch, [(CID, "a", DOC)])
    try:
        declared = [("sign",), ("graha",)]
        got = ac.vocab_fetch_json_kinds(T, C, None, declared)
        assert got["key_hits"] == ["JUP", "MAR", "SUN", "VEN", "house"]                                           # LIMIT 5, ordered: nothing explains the number-leaf keys
        got = ac.vocab_fetch_json_kinds(T, C, None, declared, _keys(terms_item()))
        assert got["key_hits"] == ["VEN", "house", "second_house", "signs"]                                       # the root tally's keys leave; the NESTED tally.VEN is another prefix and stays
        assert got["key_sets"] == [{"keys": ["JUP", "MAR", "SUN"]}]                                               # exactly the keys directly under the prefix, distinct and ordered
        got = ac.vocab_fetch_json_kinds(T, C, None, declared, _keys(terms_item(), struct_item(keys=["house", "signs", "second_house"])))
        assert got["key_hits"] == ["VEN", "house"]                                                                # the root structural names leave; the nested `house` (depth 2) stays a hit
        assert got["key_sets"][1] == {"keys": ["house", "second_house", "signs"]}
        got = ac.vocab_fetch_json_kinds(T, C, None, declared, _keys(terms_item(), struct_item(keys=["house", "signs"])))
        assert got["key_hits"] == ["VEN", "house", "second_house"]                                                # an unlisted name under the prefix is not explained by the list
        got = ac.vocab_fetch_json_kinds(T, C, None, declared, _keys(terms_item("$.nest.tally"), terms_item("$.nest")))
        assert got["key_hits"] == ["JUP", "MAR", "SUN", "house", "second_house"]                                  # a deeper prefix explains its own keys only; `nest.house` goes with the `$.nest` keys
        assert got["key_sets"] == [{"keys": ["VEN"]}, {"keys": ["house", "tally"]}]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_REAL_SQL_the_detector_lifts_the_explained_keys_and_fails_a_misspelt_one(monkeypatch, disposable_pg):
    doc = {"sign": "Aries", "tally": {"JUP": 3, "MOON": 2, "SUN": 1}, "house": 7, "signs": [1, 2], "second_house": 2}
    _real_table(disposable_pg, monkeypatch, [(CID, "a", doc)])
    try:
        own = {T: ([C, "chart_id", "signal_class"], {C: "jsonb", "chart_id": "uuid", "signal_class": "text"}, None)}
        d = decl(terms_item(), struct_item(keys=["house", "signs", "second_house"]))
        sets = ac.vocab_json_kind_sets(d, own)[0]
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PASS, out["measured"]
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"planet\": 4}}'::jsonb)")              # an unexplained class-word key
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PARTIAL and "planet" in out["measured"]
        ac.psql(f"DELETE FROM {T} WHERE {C} ? 'planet'")
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"tally\": {{\"Jup\": 1}}}}'::jsonb)")     # a case variant of a code, as a key
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.FAIL and "$.tally" in out["measured"] and "'Jup'" in out["measured"]
        ac.psql(f"DELETE FROM {T} WHERE {C} -> 'tally' ? 'Jup'")
        ac.psql(f"UPDATE {T} SET {C} = {C} - 'tally'")                                                              # the tally is gone from every document: the item reads nothing
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PARTIAL and "declared but unread" in out["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_the_registry_sentence_is_data_next_to_the_form():
    tail = ac.VOCAB_JSON_KEYS_APPLICABILITY_ADDITIONS["Vocab.alias"]
    assert tail.startswith("; SS N-431/N-458") and "vocab_keys" in tail and "key_hits" in tail and "no vocab_keys, no change" in tail
    assert set(ac.VOCAB_JSON_KEYS_APPLICABILITY_ADDITIONS) <= set(ac.CRITERION_REGISTRY)


def test_the_new_files_parse_under_the_311_grammar():
    ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"), feature_version=(3, 11))
    ast.parse((HERE.parent / "asset_census.py").read_text(encoding="utf-8"), feature_version=(3, 11))
