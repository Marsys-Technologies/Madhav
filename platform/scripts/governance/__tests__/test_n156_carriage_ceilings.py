"""test_n156_carriage_ceilings.py: SS N-156 (the Carr declared ceiling): three DECLARATION-KEYED ruled-N/A rules and the registry flip.

  Carr.D3#measured:single-derivation       nature single_derivation (no independent second route): refused for an asset a reviewed D3 method serves
  Carr.D1#measured:transcription-not-verified   nature unverified_transcription (no passage-level spec)
  Carr.D2#measured:no-per-witness-values   carriage.per_witness_values false (no asset stores per-witness values; supersedes N-118)
and: Carr.D3 is no longer detector NONE, so a measured D3 verdict counts. Nothing reads N/A except on the asset's own declaration; nothing reads PASS that was not measured.
Ordinary tests, no database (the stated reads are monkeypatched with the real writer-row fixtures of test_c1_3_carriage_d3).
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

PASS, PARTIAL, NO_DET, NA = ac.PASS, ac.PARTIAL, ac.NO_DET, ac.NA
EV = "platform/python-sidecar/ga_writers/ga_positions_writer.py:289"
WHY = "the asset stores values computed once by its writer, verified by integrity checks and internal consistency only"
KW = dict(column_types=None, prose_columns=[])


def decl(aid, c):
    return dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: {"kind": "data", "carriage": c}})


def single(**o):
    return dict(applies="D3", nature="single_derivation", why=WHY, evidence=EV, per_witness_values=False, **o)


def unverified(**o):
    return dict(applies="D1", nature="unverified_transcription", why="hand-typed seed rows with no passage-level spec in the held corpus", evidence=EV, per_witness_values=False, **o)


# ───────────────────────── registry ─────────────────────────

def test_the_three_rules_are_declared_with_n156_and_every_cause_is_registered():
    for rid, cause in (("Carr.D3#measured:single-derivation", "single-derivation"), ("Carr.D1#measured:transcription-not-verified", "transcription-not-verified"),
                       ("Carr.D2#measured:no-per-witness-values", "no-per-witness-values")):
        assert "N-156" in ac.NA_RULE_DECISIONS[rid] and cause in ac.NA_CAUSES[rid.split("#")[0]]
    ac.validate_na_rule_decisions()


def test_d3_is_a_real_detector_d2_stays_none():
    assert ac.CRITERION_REGISTRY["Carr.D3"]["detector"] == "asset_census.py:measure()" and ac.CRITERION_REGISTRY["Carr.D3"]["revision"] == 2
    assert ac.CRITERION_REGISTRY["Carr.D2"]["detector"] == "NONE"          # no asset stores per-witness values: D2 is only ever N/A by declaration


# ───────────────────────── the validator ─────────────────────────

def test_validator_accepts_the_two_ceilings_and_the_witness_word():
    ac.validate_declarations(decl("ga_vichara", single()))
    ac.validate_declarations(decl("bg_vidhi_floors", unverified()))
    ac.validate_declarations(decl("bg_vidhi_floors", unverified(citation_state="unsourced")))


@pytest.mark.parametrize("mutate,msg", [
    (lambda c: c.__setitem__("per_witness_values", True), "per_witness_values"),
    (lambda c: c.__setitem__("spec", {"method": "x"}), "carries no `spec`"),
    (lambda c: c.__setitem__("citation_state", "sourced"), "citation_state"),
    (lambda c: c.__setitem__("evidence", "unverified:somewhere in the writer"), "unverified"),
    (lambda c: c.__setitem__("applies", "D1"), "requires applies"),
    (lambda c: c.__setitem__("why", "none"), "why"),
])
def test_validator_refuses_a_malformed_single_derivation(mutate, msg):
    c = single()
    mutate(c)
    with pytest.raises(ac.DeclarationsError, match=msg):
        ac.validate_declarations(decl("ga_vichara", c))


def test_unverified_transcription_refuses_a_spec_a_wrong_check_and_a_bad_state():
    for mutate, msg in ((lambda c: c.__setitem__("spec", {"method": "x"}), "carries no `spec`"), (lambda c: c.__setitem__("applies", "D3"), "requires applies"),
                        (lambda c: c.__setitem__("citation_state", "guess"), "citation_state")):
        c = unverified()
        mutate(c)
        with pytest.raises(ac.DeclarationsError, match=msg):
            ac.validate_declarations(decl("bg_vidhi_floors", c))


def test_a_method_served_asset_cannot_declare_single_derivation():
    for aid in ("ga_positions", "bg_sky_calendar"):
        with pytest.raises(ac.DeclarationsError, match="serves it"):
            ac.validate_declarations(decl(aid, single()))


def test_a_d3_spec_must_name_a_method_that_serves_the_asset():
    import test_c1_3_carriage_d3 as t3
    good = dict(applies="D3", nature="computation", why="graha longitudes re-derived by the Swiss Ephemeris called directly", evidence=EV, spec=t3.pos_spec())
    ac.validate_declarations(decl("ga_positions", good))
    with pytest.raises(ac.DeclarationsError, match="not 'ga_nakshatra'"):
        ac.validate_declarations(decl("ga_nakshatra", good))


# ───────────────────────── the measurement ─────────────────────────

def test_single_derivation_reads_d3_na_by_its_rule_and_the_other_two_by_theirs():
    got = ac.carriage_declared_checks("ga_vichara", single(), "chart_vichara", True, **KW)
    assert (got["Carr.D3"]["v"], got["Carr.D3"]["cause"]) == (NA, "single-derivation")
    assert (got["Carr.D1"]["v"], got["Carr.D1"]["cause"]) == (NA, "not-the-declared-carriage")
    assert (got["Carr.D2"]["v"], got["Carr.D2"]["cause"]) == (NA, "no-per-witness-values")
    cell = ac.rollup_asset("L1", got)["Carr"]
    assert cell["v"] == NA and {c["rule_id"] for c in cell["checks"]} == {"Carr.D3#measured:single-derivation", "Carr.D1#measured:not-the-declared-carriage",
                                                                         "Carr.D2#measured:no-per-witness-values"}


def test_unverified_transcription_reads_d1_na_by_its_rule():
    got = ac.carriage_declared_checks("bg_vidhi_floors", unverified(), "vidhi_floor_items", False, **KW)
    assert (got["Carr.D1"]["v"], got["Carr.D1"]["cause"]) == (NA, "transcription-not-verified")
    assert (got["Carr.D3"]["cause"], got["Carr.D2"]["cause"]) == ("not-the-declared-carriage", "no-per-witness-values")
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == NA


def test_the_witness_word_is_declaration_keyed():
    c = unverified()
    del c["per_witness_values"]
    got = ac.carriage_declared_checks("bg_vidhi_floors", c, "vidhi_floor_items", False, **KW)
    assert got["Carr.D2"]["cause"] == "not-the-declared-carriage"          # without the declared word D2 keeps the old reading (and that rule too is declaration-keyed)


def test_an_undeclared_asset_reads_nothing_here():
    assert ac.carriage_declared_checks("ga_vichara", None, "chart_vichara", True, **KW) == {}
    assert ac.carriage_declared_checks("ga_vichara", {"served_surface": True}, "chart_vichara", True, **KW) == {}


def test_a_contradicted_single_derivation_is_no_detector_and_never_na():
    got = ac.carriage_declared_checks("ga_positions", single(), "chart_facts", True, **KW)            # bypasses the validator: the measure-time guard
    assert got["Carr.D3"]["v"] == NO_DET and got["Carr.D3"]["declaration_disagreements"]
    assert ac.rollup_asset("L1", got)["Carr"]["v"] == NO_DET


def test_a_d3_method_cannot_be_borrowed_at_measure_time():
    import test_c1_3_carriage_d3 as t3
    c = dict(applies="D3", nature="computation", why="graha longitudes re-derived by the Swiss Ephemeris called directly", evidence=EV, spec=t3.pos_spec())
    got = ac.carriage_declared_checks("ga_nakshatra", c, "chart_facts", True, **KW)
    assert got["Carr.D3"]["v"] == NO_DET and "borrow" in got["Carr.D3"]["measured"]


def test_a_measured_d3_pass_counts_now_and_a_method_asset_reads_d1_d2_na(monkeypatch):
    import test_c1_3_carriage_d3 as t3
    pytest.importorskip("swisseph")
    monkeypatch.setattr(ac, "d3_fetch_rows", lambda *a, **k: t3.fix_nodes(t3.pos_rows()))
    monkeypatch.setattr(ac, "d3_fetch_inputs", lambda *a, **k: t3.pos_inputs())
    c = dict(applies="D3", nature="computation", why="graha longitudes re-derived by the Swiss Ephemeris called directly", evidence=EV, spec=t3.pos_spec(), per_witness_values=False)
    got = ac.carriage_declared_checks("ga_positions", c, "chart_facts", True, asset_rows=1205, **KW)
    assert got["Carr.D3"]["v"] == PASS and got["Carr.D2"]["cause"] == "no-per-witness-values"
    cell = ac.rollup_asset("L1", got)["Carr"]
    assert cell["v"] == PASS, cell


def test_a_bare_pass_is_still_not_honoured_and_unrelated_assets_are_unmoved():
    m = {"Carr.D3": dict(v=PASS, measured="hypothetical"), "Carr.D1": dict(v=NA, cause="not-the-declared-carriage", measured="n"),
         "Carr.D2": dict(v=NA, cause="no-per-witness-values", measured="n")}
    c = ac.rollup_asset("L1", m)["Carr"]
    assert c["v"] == NO_DET and next(x for x in c["checks"] if x["criterion"] == "Carr.D3")["v"] == NO_DET
    assert ac.rollup_asset("L1", {})["Carr"]["v"] == NO_DET
