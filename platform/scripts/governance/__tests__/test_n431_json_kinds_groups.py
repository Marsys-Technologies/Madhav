"""test_n431_json_kinds_groups.py: SS N-431 / N-458 `vocab_json_kinds`, EXTENSION (i): a CLASS-LEVEL GROUP of paths.

The base form declares one kind per path and caps a column at 32 declared paths. bo_laksana_rerank's configuration_jsonb holds 54 single-kind graha / rashi paths (graha1, graha2, second_lord, occupants[*] ...).
A bare cap raise would let a declarer list 500 paths and check none of them. A GROUP entry instead lists several paths that share ONE class / family:

    {"paths": ["$.graha1", "$.graha2", "$.second_lord"], "class": "graha", "family": "name", "why": "...", "evidence": "file.py:line" | ["file.py:line", ...]}

It counts as ONE entry toward the 32-entry cap, but every member counts toward a hard total of VOCAB_JSON_KINDS_MAX_TOTAL_PATHS, and it carries a per-class CLOSURE CHECK: every member path is graded
value by value (the existing per-path grading), and a member that matches NO data is reported as `declared but unread` and keeps the cell below PASS (a group cannot claim a path nothing read).
Opt-in: no group, no change (the base file test_n431_json_kinds.py pins that).

Everything here is proven without a database except the `test_REAL_SQL_*` tests (the disposable PostgreSQL fixture).
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
EV2 = "platform/python-sidecar/ga_writers/ga_structural_writer.py:7717"
GRAHA_NAMES = ["Jupiter", "Mars", "Mercury", "Saturn", "Venus"]
GRAHA_CODES = ["JUP", "MAR", "MER", "SAT", "VEN"]
RASHIS = ["Aquarius", "Aries", "Cancer"]
GROUP_PATHS = ["$.graha1", "$.graha2", "$.second_lord", "$.occupants[*]"]


def group(paths=None, cls="graha", family="name", **over):
    g = {"paths": list(GROUP_PATHS if paths is None else paths), "class": cls, "family": family,
         "why": "these paths are written by one producer as Title graha names, one kind for the whole group", "evidence": [EVIDENCE, EV2]}
    g.update(over)
    return g


def single(path="$.sign", cls="rashi", family="name"):
    return {"path": path, "class": cls, "family": family}


def decl(*entries, **over):
    d = {"table": T, "column": C, "paths": copy.deepcopy(list(entries) if entries else [single(), group()]),
         "why": "configuration_jsonb keeps a rashi under sign and graha names under the group paths: one kind per key", "evidence": EVIDENCE}
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


def read_of(*entries, rows=40, key_hits=()):
    return {"rows": rows, "nsigs": len(entries), "paths": list(entries), "key_hits": list(key_hits)}


def group_read(skip=(), extra=()):
    """The read of a column that holds `sign` and every group member (a member in `skip` is absent from the data)."""
    es = [entry(["sign"], RASHIS)]
    for sig, vals in ((["graha1"], GRAHA_NAMES[:2]), (["graha2"], GRAHA_NAMES[2:4]), (["second_lord"], GRAHA_NAMES[:1]), (["occupants", None], GRAHA_NAMES)):
        if ac.vocab_json_sig_label(sig) not in skip:
            es.append(entry(sig, vals))
    return read_of(*es, *extra)


def spec_of(d=None):
    sets, problems = ac.vocab_json_kind_sets(d or decl(), OWN)
    assert problems == []
    return sets[(T.lower(), C.lower())]


# ───────────────────────── the declaration's shape ─────────────────────────

def test_a_group_entry_beside_a_single_path_is_a_sound_declaration():
    assert ac.vocab_json_kinds_problem(decl()) is None
    assert ac.vocab_json_kinds_problem(decl(group(evidence=EVIDENCE))) is None                                       # one evidence pointer as a string


def test_the_group_form_is_a_known_constant_set():
    assert ac.VOCAB_JSON_KINDS_MAX_PATHS == 32 and ac.VOCAB_JSON_KINDS_MAX_TOTAL_PATHS == 128 and ac.VOCAB_JSON_KINDS_MAX_GROUP == 32


def test_a_group_counts_as_one_entry_toward_the_entry_cap_and_every_member_toward_the_total_cap():
    singles = [single(f"$.k{i}", "graha", "name") for i in range(31)]
    assert ac.vocab_json_kinds_problem(decl(*singles, group())) is None                                             # 31 singles + 1 group = 32 entries, 35 paths
    assert "1 to 32" in ac.vocab_json_kinds_problem(decl(*singles, single("$.k99"), group()))                         # 33 entries
    groups = [group([f"$.g{i}_{j}" for j in range(30)]) for i in range(4)]
    assert ac.vocab_json_kinds_problem(decl(*groups)) is None                                                       # 4 entries, 120 paths
    bad = ac.vocab_json_kinds_problem(decl(*groups, group([f"$.h{j}" for j in range(30)])))                          # 150 paths in 5 entries
    assert bad and "128" in bad and "total" in bad


def test_the_hard_total_cap_is_exact():
    full = [group([f"$.g{i}_{j}" for j in range(32)]) for i in range(4)]                                            # 128 paths
    assert ac.vocab_json_kinds_problem(decl(*full)) is None
    assert "128" in ac.vocab_json_kinds_problem(decl(*full, single("$.one")))


@pytest.mark.parametrize("bad", [
    group(paths=["$.only_one"]),                                                                                    # a group is two paths or more
    group(paths=[f"$.m{i}" for i in range(33)]),                                                                    # more than the group cap
    group(paths="$.graha1"),
    group(paths=["$.a", "$.a"]),                                                                                    # a member twice
    group(paths=["$.a", "a.b"]),                                                                                    # a member that is no path
    group(paths=["$.a", "$.a[0]"]),
    group(paths=["$.m.*", "$.m.k"]),                                                                                # two members that could match the same leaf
    group(cls="planet"),
    group(family="abbreviation"),
    group(why=""),
    group(why="x"),
    group(evidence="unverified: it is probably fine, trust me"),
    group(evidence=[]),
    group(evidence=[EVIDENCE] * 13),
    group(evidence=[EVIDENCE, "platform/python-sidecar/no_such_file.py:1"]),
    group(evidence=[3]),
])
def test_a_malformed_group_is_refused(bad):
    assert ac.vocab_json_kinds_problem(decl(single(), bad))


def test_a_group_with_a_missing_or_extra_field_is_refused():
    g = group()
    del g["family"]
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(g))
    g = group()
    g["note"] = "x"
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(g))
    g = group()
    del g["evidence"]
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(g))
    g = group()
    g["path"] = "$.x"                                                                                               # a single path inside a group entry
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(g))


def test_a_member_that_repeats_a_single_path_or_another_group_or_overlaps_one_is_refused():
    assert "declared twice" in ac.vocab_json_kinds_problem(decl(single("$.graha1", "graha", "name"), group()))
    assert "declared twice" in ac.vocab_json_kinds_problem(decl(group(), group(["$.graha1", "$.other"], cls="rashi")))
    assert "overlaps" in ac.vocab_json_kinds_problem(decl(single("$.occupants.*", "graha", "name"), group(["$.a", "$.occupants.x"])))
    assert "overlaps" in ac.vocab_json_kinds_problem(decl(group(["$.m.*", "$.n"]), group(["$.m.k", "$.p"])))


def test_the_group_why_and_evidence_are_required_per_group_not_inherited_from_the_column():
    d = decl()
    d["vocab_json_kinds"][0]["evidence"] = EVIDENCE
    del d["vocab_json_kinds"][0]["paths"][1]["evidence"]
    assert ac.vocab_json_kinds_problem(d)


def test_the_validator_raises_on_a_bad_group():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl(group(paths=["$.only_one"])))
    ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl())


# ───────────────────────── the sets ─────────────────────────

def test_the_sets_flatten_a_group_into_one_spec_per_member_carrying_the_group():
    spec = spec_of()
    assert [s["path"] for s in spec] == ["$.sign", *GROUP_PATHS]
    assert spec[0].get("group") is None
    g = {s["group"] for s in spec[1:]}
    assert len(g) == 1 and None not in g
    assert all(s["class"] == "graha" and s["family"] == "name" for s in spec[1:])
    assert spec[4]["tokens"] == ("occupants", None)


def test_two_groups_get_two_group_ids():
    spec = spec_of(decl(group(["$.a", "$.b"]), group(["$.c", "$.d"], cls="rashi")))
    assert len({s["group"] for s in spec}) == 2


# ───────────────────────── the closure check ─────────────────────────

def test_a_clean_group_is_verified_member_by_member_and_recorded_as_one_class():
    rep = ac.vocab_json_kinds_report(group_read(), spec_of())
    assert rep["ok"] is True and rep["violations"] == [] and rep["unclosed"] == [] and rep["group_unread"] == []
    assert set(rep["paths"]) == {"$.sign", *GROUP_PATHS}
    (g,) = rep["groups"].values()
    assert g["class"] == "graha" and g["family"] == "name" and g["declared"] == 4 and g["read"] == 4 and set(g["verified"]) <= set(GRAHA_NAMES)


@pytest.mark.parametrize("member_sig, planted, needle", [
    (["graha1"], "JUP", "declared family is 'name'"),                          # a code in a names group
    (["graha2"], "Aries", "declared graha"),                                    # another class
    (["second_lord"], "jupiter", "declared family is 'name'"),                  # an id
    (["occupants", None], "banana", "not a graha term at all"),                 # not vocabulary
    (["graha1"], "Jupiter ", "non-canonical spelling"),                         # padded
])
def test_closure_every_value_at_every_member_must_belong_to_the_class_and_family(member_sig, planted, needle):
    es = [entry(["sign"], RASHIS)]
    for sig, vals in ((["graha1"], GRAHA_NAMES[:2]), (["graha2"], GRAHA_NAMES[2:4]), (["second_lord"], GRAHA_NAMES[:1]), (["occupants", None], GRAHA_NAMES)):
        es.append(entry(sig, vals + [planted] if sig == member_sig else vals))
    rep = ac.vocab_json_kinds_report(read_of(*es), spec_of())
    label = ac.vocab_json_sig_label(member_sig)
    assert rep["ok"] is False and rep["n_violations"] == 1, rep["violations"]
    assert label in rep["violations"][0] and repr(planted) in rep["violations"][0] and needle in rep["violations"][0] and "group" in rep["violations"][0]


def test_closure_a_member_the_data_never_has_is_reported_as_declared_but_unread_and_the_cell_is_not_ok():
    rep = ac.vocab_json_kinds_report(group_read(skip=("$.second_lord",)), spec_of())
    assert rep["ok"] is False and rep["violations"] == []
    assert rep["group_unread"] == [{"group": rep["group_unread"][0]["group"], "class": "graha", "family": "name", "declared": 4, "read": 3, "paths": ["$.second_lord"]}]
    assert len(rep["unclosed"]) == 1 and "declared but unread" in rep["unclosed"][0] and "$.second_lord" in rep["unclosed"][0]
    assert "$.second_lord" in rep["declared_never_seen"]                                                              # the base list keeps naming it too


def test_closure_a_group_nothing_reads_at_all_is_unread_in_full():
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS)), spec_of())
    assert rep["ok"] is False and rep["group_unread"][0]["read"] == 0 and rep["group_unread"][0]["paths"] == GROUP_PATHS


def test_a_single_path_never_seen_stays_allowed_as_in_the_base_form():
    """The closure rule is the GROUP's: a single declared path that matches nothing is still only listed."""
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), entry(["varga"], ["D1"])), spec_of(decl(single(), single("$.never", "graha", "name"))))
    assert rep["ok"] is True and rep["declared_never_seen"] == ["$.never"] and rep["unclosed"] == []


def test_a_group_member_matching_a_leaf_also_matched_by_a_forged_second_member_is_unread_not_double_counted():
    spec = spec_of()
    spec = spec + [dict(spec[0], path="$.dup", tokens=("graha1",))]
    rep = ac.vocab_json_kinds_report(group_read(), spec)
    assert rep["ok"] is False and "ambiguous" in rep["unread"][0]


def test_a_vocabulary_value_at_a_path_outside_every_group_still_keeps_the_column_open():
    rep = ac.vocab_json_kinds_report(group_read(extra=[entry(["third_lord"], ["Mars"], hits=["Mars"])]), spec_of())
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.third_lord"


def test_the_label_names_the_group_and_its_size_on_the_certificate_text():
    rep = ac.vocab_json_kinds_report(group_read(), spec_of())
    text = ac.vocab_json_kinds_label({"json_kinds": rep})
    assert "group" in text and "4 path(s)" in text and "graha/name" in text


# ───────────────────────── end to end through the value detector ─────────────────────────

def _sample(values, complete=False, key_hits=()):
    return dict(values=list(values), emb=[], key_hits=list(key_hits), complete=complete, rows=200, oversized=0, deep=0, leaves=300, keys=40)


@pytest.fixture
def detect(monkeypatch):
    calls = []
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, ck, where=None: {c: (_sample(["Aries", "JUP", "Mars"]) if c == C else dict(_sample(["x"]), complete=True)) for c, _k in ck})
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


def test_a_clean_group_lifts_the_column_and_the_certificate_text_names_the_group(detect):
    out = detect(group_read())
    assert out["v"] == ac.PASS, out["measured"]
    assert "group" in out["measured"] and "4 path(s)" in out["measured"]
    assert out["vocab_values"]["json_kinds"][f"{T}.{C}"]["groups"]


def test_a_group_member_the_data_never_has_reads_partial_and_says_declared_but_unread(detect):
    out = detect(group_read(skip=("$.second_lord", "$.graha2")))
    assert out["v"] == ac.PARTIAL, out["measured"]
    assert "declared but unread" in out["measured"] and "$.second_lord" in out["measured"] and "$.graha2" in out["measured"]


def test_a_value_outside_the_group_class_fails_naming_the_member_and_the_value(detect):
    es = [entry(["sign"], RASHIS), entry(["graha1"], ["Mars", "Aries"]), entry(["graha2"], ["Mars"]), entry(["second_lord"], ["Mars"]), entry(["occupants", None], ["Mars"])]
    out = detect(read_of(*es))
    assert out["v"] == ac.FAIL and "$.graha1" in out["measured"] and "'Aries'" in out["measured"]


def test_every_group_member_reaches_the_statement_as_a_declared_token(detect):
    detect(group_read())
    sql = detect.calls[0]
    for tok in ("'graha1'", "'graha2'", "'second_lord'", "'occupants'"):
        assert tok in sql


# ───────────────────────── the statement ─────────────────────────

def test_the_statement_for_the_full_total_cap_parses_and_stays_bounded():
    pglast = pytest.importorskip("pglast")
    tokens = [(f"k{i}", "*", "v") for i in range(64)] + [(f"m{i}", None) for i in range(64)]
    sql = ac.vocab_json_kinds_sql(T, C, "chart_id = 'x'", tokens)
    assert len(pglast.parse_sql(sql)) == 1
    assert len(sql) < 200_000                                                                                       # the 128 declared paths do not blow the statement up
    assert sql.count("jsonb_array_length(p) = 3") == 64 and sql.count("jsonb_array_length(p) = 2") == 64


# ───────────────────────── real SQL on a disposable PostgreSQL ─────────────────────────

def _real_table(pg, monkeypatch, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    ac.psql(f"CREATE TABLE {T} (chart_id uuid, signal_class text, {C} jsonb)")
    for cid, cls, doc in rows:
        ac.psql(f"INSERT INTO {T} VALUES ({ac._vocab_lit(cid)}, {ac._vocab_lit(cls)}, {ac._vocab_lit(json.dumps(doc))}::jsonb)")


CID = "482012f1-710e-4a25-994a-93821f5871aa"


def test_REAL_SQL_every_group_member_that_ends_a_string_leaf_explains_its_key_and_nothing_else_does(monkeypatch, disposable_pg):
    """The class words `planet` and `graha` are key hits unless a DECLARED path ends on them at a string leaf: a group member counts as declared, a neighbour key does not."""
    rows = [(CID, "a", {"planet": "Mars", "graha": "Venus", "lord": "Saturn", "house": 7, "sign": "Aries"})]
    _real_table(disposable_pg, monkeypatch, rows)
    try:
        assert ac.vocab_fetch_json_kinds(T, C, None)["key_hits"] == ["graha", "house", "planet", "sign"]            # nothing declared: every class-word key is a hit
        spec = spec_of(decl(group(["$.planet", "$.graha", "$.lord"]), single("$.sign")))
        got = ac.vocab_fetch_json_kinds(T, C, None, [s["tokens"] for s in spec])
        assert got["key_hits"] == ["house"]                                                                        # the member keys planet / graha and the single sign are the declaration; house is not
        spec2 = spec_of(decl(group(["$.planet", "$.lord"])))
        got = ac.vocab_fetch_json_kinds(T, C, None, [s["tokens"] for s in spec2])
        assert got["key_hits"] == ["graha", "house", "sign"]                                                       # graha was not declared in this group
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_REAL_SQL_the_detector_grades_a_group_against_the_real_data_closure_included(monkeypatch, disposable_pg):
    rows = [(CID, "a", {"sign": "Aries", "graha1": "Mars", "graha2": "Venus", "second_lord": "Saturn", "occupants": ["Jupiter", "Mercury"]})]
    _real_table(disposable_pg, monkeypatch, rows)
    try:
        own = {T: ([C, "chart_id", "signal_class"], {C: "jsonb", "chart_id": "uuid", "signal_class": "text"}, None)}
        sets = ac.vocab_json_kind_sets(decl(), own)[0]
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PASS, out["measured"]
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"graha1\": \"JUP\"}}'::jsonb)")           # a code in the names group
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.FAIL and "$.graha1" in out["measured"] and "'JUP'" in out["measured"]
        ac.psql(f"DELETE FROM {T} WHERE {C} ->> 'graha1' = 'JUP'")
        ac.psql(f"UPDATE {T} SET {C} = {C} - 'second_lord'")                                                        # the member second_lord is no longer in any document
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PARTIAL and "declared but unread" in out["measured"] and "$.second_lord" in out["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_the_new_files_parse_under_the_311_grammar():
    ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"), feature_version=(3, 11))
    ast.parse((HERE.parent / "asset_census.py").read_text(encoding="utf-8"), feature_version=(3, 11))


def test_the_registry_sentence_is_data_next_to_the_form_and_not_yet_in_the_registry():
    """The sentence waits for the revision bump (REGISTRY_REVISION and the registry text are not touched here); the bump generator appends `...ADDITIONS[crit]` to that criterion applicability."""
    tail = ac.VOCAB_JSON_GROUPS_APPLICABILITY_ADDITIONS["Vocab.alias"]
    assert tail.startswith("; SS N-431/N-458") and "128" in tail and "declared but unread" in tail and "no group declared, no change" in tail
    assert set(ac.VOCAB_JSON_GROUPS_APPLICABILITY_ADDITIONS) <= set(ac.CRITERION_REGISTRY)
