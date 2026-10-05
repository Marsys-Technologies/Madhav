"""test_e6_f_carr_no_carriage.py — E6 work-list item (f): Carr `no-carriage` on D1, D2, D3 (N-22 ruling principle 7,
provisional until the J1 independent review; SS strict definition 2026-09-30).

`no-carriage` is a check-level N/A CANDIDATE on Carr.D1/D2/D3, emitted ONLY from a positive declaration
(`terminal_by_construction` pointer in asset_declarations.json) that the MEASURED downstream facts do not contradict:
  * measured direct AND transitive dependents are both 0 (the census blocking radius; unmeasured => NO_DETECTOR);
  * `carriage.served_surface` is not true (true = reaches a served surface = carries; null is unknown and does not block);
  * the measured Dens.served verdict is not a found read (PASS/FAIL/PARTIAL), the strict definition's measured half.
Anything else is NO_DETECTOR ("never read as no-carriage") and a contradiction is a `declaration_disagreements` entry.
The candidate releases nothing by itself: NA_RULE_DECISIONS stays EMPTY, so the rollup reads it NO_DETECTOR
"N/A rule undecided". Today NO asset declares terminal_by_construction, so no census cell changes.

Offline: the packet (a) `_stub_layer` harness. No database.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as pa  # noqa: E402

NA, NO_DET = ac.NA, ac.NO_DET
CHECKS = ("Carr.D1", "Carr.D2", "Carr.D3")
PTR = "writer ga_x.py:12 writes nothing any asset or surface reads"


def facts(tbc=PTR, served="absent", direct=0, transitive=0, measured_served=ac.NA, radius="ok"):
    f = {}
    if tbc is not None:
        f["declared_terminal_by_construction"] = tbc
    if served != "absent":
        f["declared_carriage"] = {"served_surface": served}
    if radius == "ok":
        f["blocking_radius"] = dict(direct=direct, transitive=transitive, severity_weight=1 + transitive)
    elif radius != "missing":
        f["blocking_radius"] = radius
    if measured_served != "missing":
        f["measured_served"] = measured_served
    return f


# ───────────────────────── the grader ─────────────────────────

def test_declared_terminal_with_zero_measured_dependents_is_a_na_candidate_with_cause_no_carriage():
    r = ac.grade_carr_no_carriage(facts())
    assert r["v"] == NA and r["cause"] == "no-carriage"
    assert "declaration_disagreements" not in r
    m = r["measured"]
    assert PTR in m and "direct 0" in m and "transitive 0" in m
    assert "declared pointer is the evidence" in m                      # served_surface null: the pointer is the evidence
    assert "served_surface not declared" in m


def test_served_surface_false_is_also_a_candidate_and_the_text_says_declared_false():
    r = ac.grade_carr_no_carriage(facts(served=False))
    assert r["v"] == NA and r["cause"] == "no-carriage"
    assert "served_surface declared false" in r["measured"]


def test_served_surface_null_is_enough_alongside_the_pointer():
    r = ac.grade_carr_no_carriage(facts(served=None))
    assert r["v"] == NA and r["cause"] == "no-carriage"


def test_served_surface_true_contradicts_and_is_not_a_candidate():
    r = ac.grade_carr_no_carriage(facts(served=True))
    assert r["v"] == NO_DET and "cause" not in r
    d = r["declaration_disagreements"]
    assert d == [dict(field="carriage.served_surface", declared=True, terminal_by_construction=PTR)]
    assert "contradict" in r["measured"] and "read as no-carriage" in r["measured"]


@pytest.mark.parametrize("direct,transitive", [(1, 1), (3, 5), (0, 2), (2, 0)])
def test_measured_dependents_contradict_and_are_not_a_candidate(direct, transitive):
    r = ac.grade_carr_no_carriage(facts(direct=direct, transitive=transitive))
    assert r["v"] == NO_DET and "cause" not in r
    assert r["declaration_disagreements"] == [dict(field="terminal_by_construction", declared=PTR,
                                                   measured_dependents=dict(direct=direct, transitive=transitive))]
    assert f"direct {direct}" in r["measured"] and f"transitive {transitive}" in r["measured"]


@pytest.mark.parametrize("radius", [
    "missing", None, {}, dict(direct=None, transitive=None), dict(direct=0), dict(transitive=0),
    dict(direct=0, transitive=None), dict(direct=None, transitive=0), dict(direct=True, transitive=0),
    dict(direct=0, transitive=False), dict(direct="0", transitive="0"), dict(direct=0.0, transitive=0.0),
    dict(direct=-1, transitive=0), dict(direct=0, transitive=-1), [0, 0], "0",
])
def test_an_unmeasured_or_malformed_radius_is_no_detector_never_na(radius):
    r = ac.grade_carr_no_carriage(facts(radius=radius))
    assert r["v"] == NO_DET and "cause" not in r
    assert "declaration_disagreements" not in r          # nothing contradicts: the measurement is simply absent
    assert "unmeasured" in r["measured"] and "read as no-carriage" in r["measured"]


@pytest.mark.parametrize("tbc", [None, "", "   ", "\n\t", 0, 1, True, False, ["pointer"], {"p": 1},
                                "\u200b", "\u2060", "\ufeff", "\u200c", "\u200d", "\u00ad", " \u200b\u2060\ufeff\u200c\u200d\u00ad ",
                                "\u00a0", "\u2028", "\u0000"])
def test_undeclared_or_blank_pointer_is_no_detector_never_na(tbc):
    r = ac.grade_carr_no_carriage(facts(tbc=tbc))
    assert r["v"] == NO_DET and "cause" not in r
    assert "never read as no-carriage" in r["measured"]
    assert "declaration_disagreements" not in r


@pytest.mark.parametrize("served", ["true", "false", "True", 1, 0, [], {}, "", 1.0, "yes"])
def test_a_non_bool_served_surface_is_malformed_no_detector_never_unknown(served):
    """F5: only None or an explicit bool is an accepted form; anything else is malformed, never 'unknown that does not block'."""
    r = ac.grade_carr_no_carriage(facts(served=served))
    assert r["v"] == NO_DET and "cause" not in r
    assert "malformed" in r["measured"] and "served_surface" in r["measured"]


@pytest.mark.parametrize("car", ["x", 1, True, ["served_surface"]])
def test_a_non_dict_carriage_is_malformed_no_detector(car):
    f = facts(); f["declared_carriage"] = car
    r = ac.grade_carr_no_carriage(f)
    assert r["v"] == NO_DET and "malformed" in r["measured"]


def test_a_carriage_dict_without_served_surface_is_unknown_and_does_not_block():
    f = facts(); f["declared_carriage"] = {}
    assert ac.grade_carr_no_carriage(f)["v"] == NA


def test_a_visible_character_among_invisibles_is_a_pointer():
    r = ac.grade_carr_no_carriage(facts(tbc="\u200b x \u2060"))
    assert r["v"] == NA


def test_the_grader_docstring_states_the_rule_must_stay_undeclared_until_an_inverse_readers_detector_exists():
    d = ac.grade_carr_no_carriage.__doc__
    assert "must stay UNDECLARED" in d and "inverse-readers" in d and "undeclared edges" in d


def test_undeclared_with_everything_else_favourable_is_still_no_detector():
    """Zero measured dependents and served null are NEVER proof (CLAUDE.md N.8): only the positive pointer is."""
    r = ac.grade_carr_no_carriage(facts(tbc=None, served=None, direct=0, transitive=0))
    assert r["v"] == NO_DET and "cause" not in r


def test_empty_and_non_dict_facts_are_no_detector():
    for bad in ({}, None, [], "x", 3):
        r = ac.grade_carr_no_carriage(bad)
        assert r["v"] == NO_DET and "cause" not in r


@pytest.mark.parametrize("ms", [ac.PASS, ac.FAIL, ac.PARTIAL])
def test_a_measured_served_read_contradicts_the_strict_definition(ms):
    r = ac.grade_carr_no_carriage(facts(measured_served=ms))
    assert r["v"] == NO_DET and "cause" not in r
    assert r["declaration_disagreements"] == [dict(field="terminal_by_construction", declared=PTR, measured_served=ms)]


def test_only_a_measured_dens_na_exactly_allows_the_candidate():
    r = ac.grade_carr_no_carriage(facts(measured_served=ac.NA))
    assert r["v"] == NA and r["cause"] == "no-carriage" and "Dens.served N/A" in r["measured"]


@pytest.mark.parametrize("ms", [ac.NO_DET, ac.ERRORED, None, "missing", "n/a", "N/a", "NA", "na", "N/A ", " N/A", "weird",
                                "", 0, False, ["N/A"], ac.NOT_GENERIC])
def test_every_other_served_value_is_no_detector_possibly_served(ms):
    """F1: NO_DETECTOR/ERRORED/absent mean 'possibly served' (scan not run, module names the table but no served select
    found, comment-only, outside-roots, unparsed, shared-only): not evidence of no carriage."""
    r = ac.grade_carr_no_carriage(facts(measured_served=ms))
    assert r["v"] == NO_DET and "cause" not in r
    assert "declaration_disagreements" not in r
    assert "possibly served" in r["measured"] and "read as no-carriage" in r["measured"]


def test_every_contradiction_is_listed_together():
    r = ac.grade_carr_no_carriage(facts(served=True, direct=2, transitive=2, measured_served=ac.PASS))
    assert r["v"] == NO_DET
    assert [d["field"] for d in r["declaration_disagreements"]] == [
        "carriage.served_surface", "terminal_by_construction", "terminal_by_construction"]


def test_the_grader_does_not_mutate_its_input():
    f = facts()
    snap = repr(f)
    ac.grade_carr_no_carriage(f)
    assert repr(f) == snap


def test_carr_checks_is_empty_when_nothing_is_declared_and_three_independent_records_otherwise():
    assert ac.carr_checks(facts(tbc=None)) == {} and ac.carr_checks({}) == {} and ac.carr_checks(None) == {}
    assert ac.carr_checks(facts(tbc="  ")) == {}
    out = ac.carr_checks(facts())
    assert tuple(out) == CHECKS
    assert all(r["v"] == NA and r["cause"] == "no-carriage" for r in out.values())
    out["Carr.D1"]["v"] = "FAIL"
    assert out["Carr.D2"]["v"] == NA                      # no shared mutable record
    # a declared-but-contradicted asset still emits (NO_DETECTOR with the disagreement), on all three checks
    out2 = ac.carr_checks(facts(direct=1, transitive=1))
    assert tuple(out2) == CHECKS and all(r["v"] == NO_DET and r["declaration_disagreements"] for r in out2.values())


# ───────────────────────── registry: cause registered, rule NOT declared ─────────────────────────

def test_no_carriage_is_registered_for_d1_d2_d3_only():
    ceiling = {"Carr.D1": "transcription-not-verified", "Carr.D2": "no-per-witness-values", "Carr.D3": "single-derivation"}      # N-156: one declaration-keyed ceiling cause each
    for c in CHECKS:
        assert ac.NA_CAUSES[c] == ("no-carriage", "not-the-declared-carriage", "ratified_judgment", ceiling[c]) + (("not-a-transcription",) if c == "Carr.D1" else ())     # S2 added the two declaration-keyed causes
    assert "Carr.detector" not in ac.NA_CAUSES
    assert [k for k, v in ac.NA_CAUSES.items() if "no-carriage" in v] == list(CHECKS)


def test_no_carr_rule_is_declared():
    # until terminal_by_construction is declared (N-22 row 16); S2 declares only the declaration-keyed not-the-declared-carriage rules
    assert sorted(i for i in ac.NA_RULE_DECISIONS if i.startswith("Carr.") and not i.endswith("#measured:not-the-declared-carriage")) == [
        "Carr.D1#measured:not-a-transcription", "Carr.D1#measured:transcription-not-verified", "Carr.D2#measured:no-per-witness-values", "Carr.D3#measured:single-derivation"]       # N-156; no no-carriage / ratified_judgment rule


def test_cause_keyed_rule_ids_validate_only_for_d1_d2_d3(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-carriage": "SS-test" for c in CHECKS})
    ac.validate_na_rule_decisions()
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Carr.detector#measured:no-carriage": "SS-test"})
    with pytest.raises(ValueError):
        ac.validate_na_rule_decisions()
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Carr.D1#measured": "SS-test"})      # the retired uncaused form
    with pytest.raises(ValueError):
        ac.validate_na_rule_decisions()


# ───────────────────────── the rollup: candidate present, rule undecided ─────────────────────────

def _roll(measurements):
    return ac.rollup_asset("L0", measurements)["Carr"]


def test_the_rollup_reads_the_candidate_no_detector_while_the_rule_is_undecided():
    cell = _roll(ac.carr_checks(facts()))
    by = {c["criterion"]: c for c in cell["checks"]}
    for c in CHECKS:
        assert by[c]["v"] == NO_DET and by[c]["state"] == "MEASURED"
        assert by[c]["rule_id"] == f"{c}#measured:no-carriage" and by[c]["cause"] == "no-carriage"
        assert "N/A rule undecided" in by[c]["reason"]
    assert cell["v"] == NO_DET


def test_a_declared_rule_releases_the_candidate_by_the_existing_mechanism(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-carriage": "SS-test" for c in CHECKS})
    by = {c["criterion"]: c for c in _roll(ac.carr_checks(facts()))["checks"]}
    for c in CHECKS:
        assert by[c]["v"] == NA and by[c]["decision"] == "SS-test"
        assert by[c]["rule_id"] == f"{c}#measured:no-carriage"


def test_a_declared_rule_never_releases_a_contradicted_or_undeclared_asset(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-carriage": "SS-test" for c in CHECKS})
    for ms in (ac.carr_checks(facts(direct=1, transitive=1)), ac.carr_checks(facts(served=True)),
               ac.carr_checks(facts(radius="missing")), ac.carr_checks(facts(tbc=None))):
        by = {c["criterion"]: c for c in _roll(ms)["checks"]}
        assert all(by[c]["v"] == NO_DET for c in CHECKS), ms


def test_a_rule_for_one_check_does_not_release_the_others(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Carr.D2#measured:no-carriage": "SS-test"})
    by = {c["criterion"]: c for c in _roll(ac.carr_checks(facts()))["checks"]}
    assert (by["Carr.D1"]["v"], by["Carr.D2"]["v"], by["Carr.D3"]["v"]) == (NO_DET, NA, NO_DET)


def test_an_unmeasured_asset_reads_exactly_as_before():
    """No record at all: the rollup's own 'not measured' NO_DETECTOR (state UNKNOWN), unchanged by this packet."""
    by = {c["criterion"]: c for c in _roll({})["checks"]}
    for c in CHECKS:
        assert by[c]["v"] == NO_DET and by[c]["state"] == "APPLIES" and by[c]["reason"].startswith("not measured")
        assert "rule_id" not in by[c] and "cause" not in by[c]


# ───────────────────────── measure(): wired end to end, offline ─────────────────────────

def _decl(**per_asset):
    base = dict(kind=None, carriage=None, prose_fields=None, terminal_by_construction=None, cross_asset_writes=None)
    return {aid: {**base, **kw} for aid, kw in per_asset.items()}


SCANNED_NO_REF = dict(scanned=True, modules=[], density=0)       # Dens.served N/A: scanned, no reference


def _run(monkeypatch, tmp_path, reg, declarations, graph=None, graph_error=False, **kw):
    kw.setdefault("cap", dict(SCANNED_NO_REF))
    pa._stub_layer(monkeypatch, tmp_path, reg, **kw)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: declarations)
    if graph_error:
        def boom():
            raise ac.Unknown("dependency read failed")
        monkeypatch.setattr(ac, "dependency_graph", boom, raising=False)
    elif graph is not None:
        monkeypatch.setattr(ac, "dependency_graph", lambda: dict(graph), raising=False)
    return {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}


def _two(**kw):
    return {"t": pa._reg_row("t"), "u": pa._reg_row("u"), **kw}


def test_measure_emits_the_candidate_only_for_the_declared_terminal_asset(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph=dict(t=[], u=[]))
    for c in CHECKS:
        assert ms["t"][c]["v"] == NA and ms["t"][c]["cause"] == "no-carriage", ms["t"].get(c)
        assert c not in ms["u"]


def test_measure_emits_nothing_when_no_declarations_exist_or_the_file_is_unreadable(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), {}, graph=dict(t=[], u=[]))
    assert all(c not in m for m in ms.values() for c in CHECKS)

    def bad(*a, **k):
        raise ac.DeclarationsError("unreadable")
    pa._stub_layer(monkeypatch, tmp_path, _two())
    monkeypatch.setattr(ac, "load_asset_declarations", bad)
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert all(c not in m for m in ms.values() for c in CHECKS)


def test_measure_a_dependent_asset_contradicts_the_declaration(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph=dict(t=[], u=["t"]))
    for c in CHECKS:
        r = ms["t"][c]
        assert r["v"] == NO_DET and "cause" not in r
        assert r["declaration_disagreements"][0]["measured_dependents"] == dict(direct=1, transitive=1)


def test_measure_transitive_dependents_contradict_too(monkeypatch, tmp_path):
    reg = _two(v=pa._reg_row("v"))
    ms = _run(monkeypatch, tmp_path, reg, _decl(t=dict(terminal_by_construction=PTR), u={}, v={}),
              graph=dict(t=[], u=["t"], v=["u"]))
    assert ms["t"]["Carr.D1"]["v"] == NO_DET
    assert ms["t"]["Carr.D1"]["declaration_disagreements"][0]["measured_dependents"] == dict(direct=1, transitive=2)


def test_measure_an_unreadable_dependency_graph_is_no_detector_never_na(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph_error=True)
    for c in CHECKS:
        assert ms["t"][c]["v"] == NO_DET and "unmeasured" in ms["t"][c]["measured"]


@pytest.mark.parametrize("cap,verdict", [
    (dict(scanned=True, modules=["m.ts"], density=1, dense=[("m.ts", ["tier"])]), ac.PASS),
    (dict(scanned=True, modules=["m.ts"], density=0, declared=[("m.ts", ["no tier"])]), ac.PARTIAL),
    (dict(scanned=True, modules=["m.ts"], density=0, served=2), ac.FAIL),
])
def test_measure_a_measured_served_read_blocks_the_candidate(monkeypatch, tmp_path, cap, verdict):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}),
              graph=dict(t=[], u=[]), cap=cap)
    assert ms["t"]["Dens.served"]["v"] == verdict
    for c in CHECKS:
        assert ms["t"][c]["v"] == NO_DET and "cause" not in ms["t"][c]
        assert ms["t"][c]["declaration_disagreements"][0]["measured_served"] == verdict


@pytest.mark.parametrize("cap", [
    dict(modules=[], density=0, note="stub"),                                   # the scan did not run
    dict(scanned=True, modules=["m.ts"], density=0),                             # names the table, no served select found
    dict(scanned=True, modules=[], density=0, comment_only=["m.ts"]),            # comment-only
    dict(scanned=True, modules=[], density=0, outside=["x.ts"]),                 # outside the scanned roots
    dict(scanned=True, modules=[], density=0, unparsed=["x.ts"]),                # unparsed
    dict(scanned=True, modules=[], density=0, shared_only=["x.ts"], shared_tokens=["s"]),
])
def test_measure_an_unscanned_or_possibly_served_surface_must_not_produce_a_candidate(monkeypatch, tmp_path, cap):
    """F1 (inverts the packet's first version): Dens.served NO_DETECTOR means 'possibly served', never 'not served'."""
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph=dict(t=[], u=[]),
              cap=cap)
    assert ms["t"]["Dens.served"]["v"] == NO_DET
    for c in CHECKS:
        assert ms["t"][c]["v"] == NO_DET and "cause" not in ms["t"][c] and "possibly served" in ms["t"][c]["measured"]


def test_measure_a_scanned_no_reference_surface_allows_the_candidate(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph=dict(t=[], u=[]))
    assert ms["t"]["Dens.served"]["v"] == NA
    assert all(ms["t"][c]["v"] == NA for c in CHECKS)


def test_measure_emits_the_candidate_even_when_the_asset_is_a_service_or_has_a_writer(monkeypatch, tmp_path):
    """`kind` is irrelevant: the rule keys on the declared fact, never a kind."""
    reg = {"t": pa._reg_row("t", asset_kind="service", has_writer=True), "u": pa._reg_row("u")}
    ms = _run(monkeypatch, tmp_path, reg, _decl(t=dict(kind="service", terminal_by_construction=PTR), u={}),
              graph=dict(t=[], u=[]))
    assert all(ms["t"][c]["v"] == NA for c in CHECKS)


def test_measure_candidate_flows_through_the_rollup_as_no_detector_undecided(monkeypatch, tmp_path):
    ms = _run(monkeypatch, tmp_path, _two(), _decl(t=dict(terminal_by_construction=PTR), u={}), graph=dict(t=[], u=[]))
    cell = ac.rollup_asset("L0", ms["t"])["Carr"]
    by = {c["criterion"]: c for c in cell["checks"]}
    assert all(by[c]["v"] == NO_DET and "N/A rule undecided" in by[c]["reason"] for c in CHECKS)
    assert cell["v"] == NO_DET
    # and the same asset with the rule declared in the test only
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-carriage": "SS-test" for c in CHECKS})
    by = {c["criterion"]: c for c in ac.rollup_asset("L0", ms["t"])["Carr"]["checks"]}
    assert all(by[c]["v"] == NA for c in CHECKS)
    # E6 item (i): the meta-check is retired, so Carr is exactly D1-D3 and the declared candidates alone decide the cell
    assert "Carr.detector" not in by and sorted(by) == sorted(CHECKS)
    assert ac.rollup_asset("L0", ms["t"])["Carr"]["v"] == NA


def test_a_candidate_does_not_close_a_ledger_gap_while_the_rule_is_undecided():
    for c in CHECKS:
        rec = ac.carr_checks(facts())[c]
        assert ac._na_released(c, rec) is False


def test_a_released_candidate_closes_only_once_the_rule_is_declared(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Carr.D1#measured:no-carriage": "SS-test"})
    out = ac.carr_checks(facts())
    assert ac._na_released("Carr.D1", out["Carr.D1"]) is True
    assert ac._na_released("Carr.D2", out["Carr.D2"]) is False


# ───────────────────────── F4: a pointer must contain a visible character (reader, validator and grader) ─────────────────────────

INVISIBLE = ["​", "⁠", "﻿", "‌", "‍", "­", "​⁠﻿‌‍­", " ", " "]


def _vdoc(tbc):
    return dict(version="1.0.0", kind_enum=list(ac.DECLARED_KINDS), assets=dict(a=dict(terminal_by_construction=tbc)))


@pytest.mark.parametrize("tbc", INVISIBLE)
def test_the_declarations_validator_rejects_an_invisible_only_pointer(tbc):
    with pytest.raises(ac.DeclarationsError, match="terminal_by_construction"):
        ac.validate_declarations(_vdoc(tbc))


def test_the_declarations_validator_still_accepts_a_real_pointer_and_null():
    ac.validate_declarations(_vdoc("no reader by design"))
    ac.validate_declarations(_vdoc(None))


@pytest.mark.parametrize("tbc", INVISIBLE)
def test_declared_facts_does_not_read_an_invisible_only_pointer_as_a_declaration(tbc):
    f = ac.declared_facts({"a": dict(terminal_by_construction=tbc)}, "a")
    assert "declared_terminal_by_construction" not in f and "declared_carries_downstream" not in f


def test_declared_facts_still_reads_a_real_pointer():
    f = ac.declared_facts({"a": dict(terminal_by_construction="no reader by design")}, "a")
    assert f["declared_terminal_by_construction"] == "no reader by design" and f["declared_carries_downstream"] is False


@pytest.mark.parametrize("tbc", INVISIBLE)
def test_carr_checks_emits_nothing_for_an_invisible_only_pointer(tbc):
    assert ac.carr_checks(facts(tbc=tbc)) == {}
