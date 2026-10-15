"""test_n431_json_kinds_identifiers.py: SS N-431 / N-458 `vocab_json_kinds`, EXTENSION (ii): MIXED-KIND paths and TERM-EMBEDDING IDENTIFIERS.

The base form binds ONE (class, family) to a path, and reads a value that is no vocabulary term at a declared path as a violation (an identifier such as `true_chitra`, which embeds the nakshatra word
chitra, can be neither declared nor left undeclared). Two opt-in additions to a single path entry:

  (a) MIXED KINDS:  {"path": "$.fact_subject", "kinds": [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "registered_code"}]}
      a value must be a canonical member of the UNION: exactly one declared class, in that class's declared family (the graded kind of a value is ambiguous by design, but it must still be IN the union;
      the same lexicon, classifier and family rules as the single-kind path, and as `vocab_multi_kind` for flat columns).
  (b) A CLOSED IDENTIFIER SET:  {"path": "$.ayanamsha_id", "identifiers": {"values": ["true_chitra", ...], "why": "...", "evidence": "producer.py:line"}}
      an explicit list (at most 64) of the identifier values the producer can write, each checked VERBATIM as a string constant of the cited producer .py file. A value in the set is an identifier, not spelled
      vocabulary: embedded terms inside it are not findings. A value OUTSIDE the set is a violation (FAIL), so the exemption cannot hide anything else; a value that is itself a whole vocabulary term is never exempted.
      It combines with kinds / class+family on the same path (a term of a declared kind OR a listed identifier).

Opt-in: no kinds / identifiers, no change. Proven without a database except the `test_REAL_SQL_*` test (the disposable PostgreSQL fixture).
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
EV_AYAN = "platform/python-sidecar/ga_writers/ga_ayurdaya_writer.py:60"
EV_POINTS = "platform/python-sidecar/ga_writers/ga_sensitive_writer.py:2649"
AYANAMSHAS = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
POINTS = ["BHAVA_LAGNA", "HORA_LAGNA", "GULIKA", "MANDI"]
CODES = ["JUP", "MAR", "SAT"]
HOUSES = ["HOUSE_01", "HOUSE_02", "HOUSE_12"]
RASHIS = ["Aquarius", "Aries", "Cancer"]
KINDS_SUBJECT = [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "registered_code"}]
SIGN = {"path": "$.sign", "class": "rashi", "family": "name"}


def idents(values=None, evidence=EV_AYAN, **over):
    d = {"values": list(AYANAMSHAS if values is None else values), "why": "the ayanamsha ids are the producer constants of the five supported ayanamshas, identifiers and not spelled vocabulary", "evidence": evidence}
    d.update(over)
    return d


def decl(*paths, **over):
    d = {"table": T, "column": C, "paths": copy.deepcopy(list(paths) if paths else [SIGN, {"path": "$.fact_subject", "kinds": KINDS_SUBJECT}, {"path": "$.ayanamsha_id", "identifiers": idents()}]),
         "why": "configuration_jsonb keeps rashi names under sign, graha codes or house codes under fact_subject and ayanamsha ids under ayanamsha_id", "evidence": EVIDENCE}
    d.update(over)
    return {"vocab_json_kinds": [d]}


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    reg = {f"house_{n}": {"classes": ["bhava"]} for n in range(1, 10)} | {f"house_{n:02d}": {"classes": ["bhava"]} for n in range(1, 13)} | {"mula": {"classes": ["nakshatra"]}}
    monkeypatch.setattr(ac, "_VOCAB_REGISTERED", reg)
    monkeypatch.setattr(ac, "vocab_registered_load", lambda *a, **k: ac._VOCAB_REGISTERED)


def entry(sig, values, n=None, hits=None, nd=None):
    hits = [] if hits is None else hits
    return {"p": list(sig), "n": n if n is not None else len(values) * 3, "nd": nd if nd is not None else len(values), "vals": list(values), "nh": len(hits), "hits": list(hits)}


def read_of(*entries, rows=40, key_hits=()):
    return {"rows": rows, "nsigs": len(entries), "paths": list(entries), "key_hits": list(key_hits)}


def clean_read(subject=None, ayan=None, extra=()):
    return read_of(entry(["sign"], RASHIS), entry(["fact_subject"], CODES + HOUSES if subject is None else subject), entry(["ayanamsha_id"], AYANAMSHAS if ayan is None else ayan), *extra)


def spec_of(d=None):
    sets, problems = ac.vocab_json_kind_sets(d or decl(), OWN)
    assert problems == []
    return sets[(T.lower(), C.lower())]


# ───────────────────────── the declaration's shape ─────────────────────────

def test_mixed_kind_identifier_and_combined_paths_are_sound():
    assert ac.vocab_json_kinds_problem(decl()) is None
    both = {"path": "$.special_point", "class": "graha", "family": "code", "identifiers": idents(POINTS, EV_POINTS)}
    assert ac.vocab_json_kinds_problem(decl(SIGN, both)) is None                                                    # a class+family AND a closed set
    both = {"path": "$.special_point", "kinds": KINDS_SUBJECT, "identifiers": idents(POINTS, EV_POINTS)}
    assert ac.vocab_json_kinds_problem(decl(SIGN, both)) is None                                                    # kinds AND a closed set


def test_the_identifier_constants():
    assert ac.VOCAB_JSON_IDENTIFIERS_MAX == 64 and ac.VOCAB_JSON_KINDS_MAX_KINDS == 6


@pytest.mark.parametrize("bad", [
    {"path": "$.p", "kinds": KINDS_SUBJECT[:1]},                                                                     # one kind is the class + family form
    {"path": "$.p", "kinds": []},
    {"path": "$.p", "kinds": KINDS_SUBJECT + [{"class": "graha", "family": "name"}]},                                # a class twice
    {"path": "$.p", "kinds": [{"class": "graha", "family": "code"}, {"class": "planet", "family": "code"}]},
    {"path": "$.p", "kinds": [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "abbreviation"}]},
    {"path": "$.p", "kinds": [{"class": "graha", "family": "code"}, {"class": "bhava"}]},
    {"path": "$.p", "kinds": [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "id", "note": "x"}]},
    {"path": "$.p", "kinds": "graha"},
    {"path": "$.p", "kinds": [{"class": "graha", "family": "code"}] * 2 + [{"class": c, "family": "id"} for c in ("rashi", "nakshatra", "bhava", "bhava", "graha")]},
    {"path": "$.p", "class": "graha", "family": "code", "kinds": KINDS_SUBJECT},                                      # class+family AND kinds
    {"path": "$.p"},                                                                                                # no kind and no identifiers
    {"path": "$.p", "class": "graha"},                                                                              # a class without its family
    {"path": "$.p", "family": "code"},
    {"path": "$.p", "identifiers": idents(), "note": "x"},
    {"path": "$.p", "identifiers": idents(values=[])},
    {"path": "$.p", "identifiers": idents(values=[f"id{i}" for i in range(65)])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", "true_chitra"])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", ""])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", " raman"])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", 7])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", "a\x00b"])},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", "a​b"])},
    {"path": "$.p", "identifiers": idents(values="true_chitra")},
    {"path": "$.p", "identifiers": idents(values=["true_chitra", "no_such_identifier_in_the_producer_source"])},     # not a string constant of the cited file
    {"path": "$.p", "identifiers": idents(evidence="platform/scripts/governance/asset_declarations.json:1")},         # a closed set is checked in Python source
    {"path": "$.p", "identifiers": idents(evidence="unverified: the producer writes these ids somewhere")},
    {"path": "$.p", "identifiers": idents(evidence="platform/python-sidecar/no_such_file.py:1")},
    {"path": "$.p", "identifiers": idents(evidence=[])},
    {"path": "$.p", "identifiers": idents(why="")},
    {"path": "$.p", "identifiers": idents(why="x")},
    {"path": "$.p", "identifiers": {k: v for k, v in idents().items() if k != "why"}},
    {"path": "$.p", "identifiers": {k: v for k, v in idents().items() if k != "evidence"}},
    {"path": "$.p", "identifiers": ["true_chitra"]},
])
def test_a_malformed_mixed_kind_or_identifier_entry_is_refused(bad):
    assert ac.vocab_json_kinds_problem(decl(SIGN, bad))


def test_the_closed_set_cap_is_exact_with_values_that_are_all_verbatim_producer_constants():
    """65 values that ARE verbatim in the producer isolate the size rule from the verbatim rule."""
    consts, _ = ac._vocab_py_string_constants(EV_AYAN)
    real = sorted(v for v in consts if v == v.strip() and v and len(v) <= 40 and v.isprintable())
    assert len(real) > 70
    assert ac.vocab_json_kinds_problem(decl(SIGN, {"path": "$.p", "identifiers": idents(real[:64])})) is None
    bad = ac.vocab_json_kinds_problem(decl(SIGN, {"path": "$.p", "identifiers": idents(real[:65])}))
    assert bad and "1 to 64" in bad


def test_an_identifier_set_spread_over_two_producer_files_is_checked_across_both():
    assert ac.vocab_json_kinds_problem(decl(SIGN, {"path": "$.m", "identifiers": idents(["true_chitra", "GULIKA"], [EV_AYAN, EV_POINTS])})) is None
    assert ac.vocab_json_kinds_problem(decl(SIGN, {"path": "$.m", "identifiers": idents(["true_chitra", "GULIKA"], EV_AYAN)}))             # GULIKA is not in the ayanamsha producer


def test_a_single_path_missing_its_family_is_still_refused_with_the_base_message():
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl({"path": "$.p", "class": "graha"}))
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl({"path": "$.p", "class": "graha", "family": "code", "note": "x"}))


def test_a_group_entry_cannot_carry_kinds_or_identifiers():
    g = {"paths": ["$.a", "$.b"], "class": "graha", "family": "name", "why": "these paths are written by one producer as Title graha names", "evidence": EVIDENCE}
    assert ac.vocab_json_kinds_problem(decl(SIGN, g)) is None
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(SIGN, dict(g, identifiers=idents())))
    assert "exactly the fields" in ac.vocab_json_kinds_problem(decl(SIGN, {k: v for k, v in dict(g, kinds=KINDS_SUBJECT).items() if k not in ("class", "family")}))


def test_a_mixed_kind_path_is_not_an_overlap_exemption():
    assert "overlaps" in ac.vocab_json_kinds_problem(decl(SIGN, {"path": "$.m.*", "kinds": KINDS_SUBJECT}, {"path": "$.m.k", "identifiers": idents()}))


def test_the_validator_raises_on_a_bad_identifier_set():
    with pytest.raises(ac.DeclarationsError):
        ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl(SIGN, {"path": "$.p", "identifiers": idents(values=[])}))
    ac.validate_vocab_json_kinds_declaration("assets.bo_x", decl())


# ───────────────────────── the sets ─────────────────────────

def test_the_sets_carry_kinds_and_identifiers_per_path():
    spec = {s["path"]: s for s in spec_of()}
    assert spec["$.sign"]["class"] == "rashi" and spec["$.sign"]["kinds"] == [("rashi", "name")] and not spec["$.sign"].get("identifiers")
    assert spec["$.fact_subject"]["kinds"] == [("graha", "code"), ("bhava", "registered_code")] and spec["$.fact_subject"]["class"] is None
    assert spec["$.ayanamsha_id"]["kinds"] == [] and spec["$.ayanamsha_id"]["identifiers"] == AYANAMSHAS


def test_the_identifier_evidence_is_checked_again_when_the_sets_are_resolved(monkeypatch):
    """A producer constant that disappears after the declaration was merged refuses the declaration at measure time (nothing lifted)."""
    monkeypatch.setattr(ac, "_vocab_py_string_constants", lambda ev: ({"raman"}, None))
    sets, problems = ac.vocab_json_kind_sets(decl(), OWN)
    assert sets == {} and problems and "verbatim" in problems[0]


# ───────────────────────── mixed kinds: a value must be IN the union ─────────────────────────

def test_a_value_of_either_declared_kind_in_its_family_is_verified():
    rep = ac.vocab_json_kinds_report(clean_read(), spec_of())
    assert rep["ok"] is True and rep["violations"] == [], rep["violations"]
    rec = rep["paths"]["$.fact_subject"]
    assert rec["kinds"] == [{"class": "graha", "family": "code"}, {"class": "bhava", "family": "registered_code"}] and set(rec["verified"]) == set(CODES + HOUSES)
    assert set(CODES + HOUSES) <= set(rep["values"])


@pytest.mark.parametrize("planted, needle", [
    ("Jupiter", "declared family is 'code'"),                      # a graha NAME where graha codes are declared
    ("jupiter", "declared family is 'code'"),
    ("Aries", "declared kinds"),                                   # a rashi: neither declared class
    ("Moola", "declared kinds"),                                   # a nakshatra
    ("house_01", "declared family"),                               # the bhava canonical ID where the registered CODE is declared
    ("HOUSE_1", "registered bg_ontology alias"),                   # the registered alias in a shape other than NAME_NN is drift
    ("jup", "non-canonical spelling"),
    ("CHART", "not a term of any declared kind"),                  # an identifier that is not in any closed set
    ("D9_SUN", "not a term of any declared kind"),
])
def test_a_value_outside_the_union_is_a_violation_naming_path_value_and_kinds(planted, needle):
    rep = ac.vocab_json_kinds_report(clean_read(subject=CODES + HOUSES + [planted]), spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 1, rep["violations"]
    v = rep["violations"][0]
    assert "$.fact_subject" in v and repr(planted) in v and needle in v and "graha/code" in v and "bhava/registered_code" in v


def test_a_term_canonical_in_two_declared_classes_is_ambiguous_and_refused(monkeypatch):
    real = ac.vocab_classify
    monkeypatch.setattr(ac, "vocab_classify", lambda v: dict(kind="canonical", classes=["graha", "bhava"], detect=True, short=False) if v == "TWIN" else real(v))
    rep = ac.vocab_json_kinds_report(clean_read(subject=CODES + ["TWIN"]), spec_of())
    assert rep["ok"] is False and "more than one declared kind" in rep["violations"][0]


def test_mixed_kinds_do_not_loosen_a_single_kind_path():
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS + ["JUP"]), entry(["fact_subject"], CODES), entry(["ayanamsha_id"], AYANAMSHAS)), spec_of())
    assert rep["ok"] is False and rep["n_violations"] == 1 and "$.sign" in rep["violations"][0]


# ───────────────────────── the closed identifier set ─────────────────────────

def test_listed_identifiers_are_not_vocabulary_findings_even_when_they_embed_a_term():
    assert ac.vocab_embedded("true_chitra") is True                                                                  # the premise: this id embeds the nakshatra word chitra
    rep = ac.vocab_json_kinds_report(clean_read(), spec_of())
    assert rep["ok"] is True and "true_chitra" not in rep["emb"] and "true_chitra" not in rep["values"]
    rec = rep["paths"]["$.ayanamsha_id"]
    assert rec["identifiers_verified"] == sorted(AYANAMSHAS) and rec["identifiers_declared"] == 5


@pytest.mark.parametrize("planted", ["custom_chitra", "TRUE_CHITRA", "true_chitra ", "unknown_ayanamsha", "", "Mars"])
def test_a_value_outside_the_closed_set_is_a_violation_so_the_exemption_hides_nothing_else(planted):
    rep = ac.vocab_json_kinds_report(clean_read(ayan=AYANAMSHAS + [planted]), spec_of())
    assert rep["ok"] is False and rep["n_violations"] >= 1, rep["violations"]
    assert "$.ayanamsha_id" in rep["violations"][0] and repr(planted) in rep["violations"][0]
    assert "closed identifier set" in rep["violations"][0] or "not a term" in rep["violations"][0]


def test_a_whole_vocabulary_term_in_the_set_is_graded_not_exempted():
    d = decl(SIGN, {"path": "$.p", "identifiers": idents(["true_chitra", "GULIKA", "MANDI"], [EV_AYAN, EV_POINTS])})
    spec = spec_of(d)
    spec[1]["identifiers"] = ["true_chitra", "JUP"]                                                                    # a forged set that lists a whole canonical code
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), entry(["p"], ["true_chitra", "JUP"])), spec)
    assert rep["ok"] is False and "'JUP'" in rep["violations"][0] and "vocabulary term" in rep["violations"][0]


def test_identifiers_and_kinds_combine_on_one_path_a_term_of_the_kind_or_a_listed_identifier():
    d = decl(SIGN, {"path": "$.special_point", "class": "graha", "family": "code", "identifiers": idents(POINTS, EV_POINTS)})
    ok = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), entry(["special_point"], CODES + POINTS)), spec_of(d))
    assert ok["ok"] is True
    for planted in ("Jupiter", "NOT_LISTED", "Aries"):
        rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS), entry(["special_point"], CODES + POINTS + [planted])), spec_of(d))
        assert rep["ok"] is False and repr(planted) in rep["violations"][0]


def test_an_identifier_only_path_with_more_distinct_values_than_the_cap_is_a_violation_not_unread():
    """More than 500 distinct values cannot all be in a closed set of at most 64: the answer is known without reading them all."""
    many = [f"id{i:04d}" for i in range(ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1)]
    rd = read_of(entry(["sign"], RASHIS), entry(["ayanamsha_id"], many[:ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1], nd=5000))
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["unread"] == [] and "closed identifier set" in rep["violations"][0] and "5000" in rep["violations"][0]


def test_a_kind_path_with_more_distinct_values_than_the_cap_is_still_unread():
    many = [f"v{i}" for i in range(ac.VOCAB_JSON_KINDS_MAX_DISTINCT + 1)]
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], many, nd=len(many))), spec_of())
    assert rep["ok"] is False and "more than" in rep["unread"][0]


def test_an_embedded_term_at_an_undeclared_path_is_still_a_finding_the_set_exempts_only_its_own_path():
    rd = clean_read(extra=[entry(["other_id"], ["true_chitra"], hits=["true_chitra"])])
    rep = ac.vocab_json_kinds_report(rd, spec_of())
    assert rep["ok"] is False and rep["undeclared_vocabulary"][0]["path"] == "$.other_id"


def test_an_identifier_never_seen_is_not_a_finding_but_a_path_never_seen_is_listed():
    rep = ac.vocab_json_kinds_report(clean_read(ayan=["raman"]), spec_of())
    assert rep["ok"] is True and rep["paths"]["$.ayanamsha_id"]["identifiers_verified"] == ["raman"]
    rep = ac.vocab_json_kinds_report(read_of(entry(["sign"], RASHIS)), spec_of())
    assert rep["declared_never_seen"] == ["$.fact_subject", "$.ayanamsha_id"] and rep["ok"] is True


def test_only_identifiers_verified_is_a_verified_declaration():
    d = decl({"path": "$.ayanamsha_id", "identifiers": idents()})
    assert ac.vocab_json_kinds_report(read_of(entry(["ayanamsha_id"], AYANAMSHAS)), spec_of(d))["ok"] is True
    assert ac.vocab_json_kinds_report(read_of(entry(["ayanamsha_id"], [])), spec_of(d))["ok"] is False


def test_the_label_prints_the_union_and_the_closed_set_on_the_certificate_text():
    text = ac.vocab_json_kinds_label({"json_kinds": ac.vocab_json_kinds_report(clean_read(), spec_of())})
    assert "graha/code" in text and "bhava/registered_code" in text and "closed identifier set" in text and "5 identifier" in text


# ───────────────────────── end to end through the value detector ─────────────────────────

def _sample(values, complete=False, key_hits=()):
    return dict(values=list(values), emb=[], key_hits=list(key_hits), complete=complete, rows=200, oversized=0, deep=0, leaves=300, keys=40)


@pytest.fixture
def detect(monkeypatch):
    monkeypatch.setattr(ac, "vocab_fetch_samples", lambda table, ck, where=None: {c: (_sample(["Aries", "JUP", "HOUSE_01"]) if c == C else dict(_sample(["x"]), complete=True)) for c, _k in ck})
    monkeypatch.setattr(ac, "vocab_fetch_probe", lambda *a, **k: dict(hits=[], key_hits=[], oversized=0, deep=0))
    monkeypatch.setattr(ac, "vocab_fetch_spelling", lambda *a, **k: dict(found=False, sample=[]))

    def run(read, d=None):
        monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps(read))
        sets = ac.vocab_json_kind_sets(d or decl(), OWN)[0]
        return ac.vocab_value_detect({k: v[:2] for k, v in OWN.items()}, None, json_kind_sets=sets)
    return run


def test_the_mixed_and_identifier_paths_lift_the_column_to_pass(detect):
    out = detect(clean_read())
    assert out["v"] == ac.PASS, out["measured"]
    assert "closed identifier set" in out["measured"] and "embedded vocabulary" not in out["measured"]


def test_without_the_closed_set_the_same_identifier_blocks_the_column(detect):
    d = decl(SIGN, {"path": "$.fact_subject", "kinds": KINDS_SUBJECT})
    out = detect(clean_read(extra=[entry(["ayanamsha_id"], ["true_chitra"], hits=["true_chitra"])]), d)
    assert out["v"] == ac.PARTIAL and "$.ayanamsha_id" in out["measured"]


def test_a_value_outside_the_closed_set_fails_the_column_naming_path_and_value(detect):
    out = detect(clean_read(ayan=AYANAMSHAS + ["custom_chitra"]))
    assert out["v"] == ac.FAIL and "$.ayanamsha_id" in out["measured"] and "'custom_chitra'" in out["measured"]


def test_a_value_outside_the_union_fails_the_column(detect):
    out = detect(clean_read(subject=CODES + ["Aries"]))
    assert out["v"] == ac.FAIL and "$.fact_subject" in out["measured"] and "'Aries'" in out["measured"]


# ───────────────────────── real data on a disposable PostgreSQL ─────────────────────────

def _real_table(pg, monkeypatch, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {T}")
    ac.psql(f"CREATE TABLE {T} (chart_id uuid, signal_class text, {C} jsonb)")
    for cid, cls, doc in rows:
        ac.psql(f"INSERT INTO {T} VALUES ({ac._vocab_lit(cid)}, {ac._vocab_lit(cls)}, {ac._vocab_lit(json.dumps(doc))}::jsonb)")


CID = "482012f1-710e-4a25-994a-93821f5871aa"


def test_REAL_SQL_the_real_read_grades_the_union_and_the_closed_set(monkeypatch, disposable_pg):
    rows = [(CID, "a", {"sign": "Aries", "fact_subject": s, "ayanamsha_id": a, "varga": "D1"}) for s, a in zip(CODES + HOUSES, AYANAMSHAS + AYANAMSHAS)]
    _real_table(disposable_pg, monkeypatch, rows)
    try:
        own = {T: ([C, "chart_id", "signal_class"], {C: "jsonb", "chart_id": "uuid", "signal_class": "text"}, None)}
        sets = ac.vocab_json_kind_sets(decl(), own)[0]
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PASS, out["measured"]
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"ayanamsha_id\": \"custom_chitra\"}}'::jsonb)")
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.FAIL and "$.ayanamsha_id" in out["measured"] and "'custom_chitra'" in out["measured"]
        ac.psql(f"DELETE FROM {T} WHERE {C} ->> 'ayanamsha_id' = 'custom_chitra'")
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"fact_subject\": \"Aries\"}}'::jsonb)")
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.FAIL and "$.fact_subject" in out["measured"] and "'Aries'" in out["measured"]
        ac.psql(f"DELETE FROM {T} WHERE {C} ->> 'fact_subject' = 'Aries'")
        ac.psql(f"INSERT INTO {T} VALUES ('{CID}', 'a', '{{\"sign\": \"Leo\", \"note\": \"true_chitra\"}}'::jsonb)")        # the same id at an UNDECLARED path is still a finding
        out = ac.vocab_value_detect({T: own[T][:2]}, None, json_kind_sets=sets)
        assert out["v"] == ac.PARTIAL and "$.note" in out["measured"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {T}")


def test_the_registry_sentence_is_data_next_to_the_form():
    tail = ac.VOCAB_JSON_IDENTIFIERS_APPLICABILITY_ADDITIONS["Vocab.alias"]
    assert tail.startswith("; SS N-431/N-458") and "closed identifier set" in tail and "verbatim" in tail and "no kinds or identifiers declared, no change" in tail
    assert set(ac.VOCAB_JSON_IDENTIFIERS_APPLICABILITY_ADDITIONS) <= set(ac.CRITERION_REGISTRY)


def test_the_new_files_parse_under_the_311_grammar():
    ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"), feature_version=(3, 11))
    ast.parse((HERE.parent / "asset_census.py").read_text(encoding="utf-8"), feature_version=(3, 11))
