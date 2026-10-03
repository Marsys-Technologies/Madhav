"""F-5 — the actual P5 evaluators (services/gochara_rules/ashtakavarga.py)
exercised with numerical mismatch, BAV/SAV selection and independent
missingness, plus the AM-7 declaration read-back as a real evaluator path
(steward M20261001T205832-b69b item 2; Codex v1.4 F-5 / ranks 5-6).

Every assertion is on the OUTPUT of production code. Operands are synthetic
and labelled so (O-BP-1: `SYN-X`, fixture rows) or the printed real extract
(SARVA_BY_SIGN, extract v1_0, tier single_pass verbatim). No database.
"""
from __future__ import annotations

import itertools
import math

import pytest

from services.gochara_rules import ashtakavarga as av
from services.gochara_rules.ashtakavarga import (
    DeclarationReadBackRefused, SARVA_BY_SIGN, consume_declaration, p5a, p5b,
    p5d, qualify_transit, typed_operands,
)
from services.gochara_rules.predicates import (
    ADMITTED, EXCLUDED, admission_state, evaluate,
)
from services.gochara_rules.registry import RULE_PATHS, RULE_VERSION

# SYNTHETIC rows (fixture = true), explicit keys — never attributed to the L1 extract.
BAV = {"Mars": {"SYN-X": 0, "SYN-Y": 4}, "Jupiter": {"SYN-X": 5, "SYN-Y": 2},
       "Saturn": {"SYN-Y": 3}}
SAV = {"SYN-X": 32, "SYN-Y": 27}
EXTRACT = {"BAV": BAV, "SAV": SAV}
DECLS = {"av-build:l1:syn:v1": {"convention": "av-build:l1:syn:v1",
                                "applies_to_fact_categories": ["ashtakavarga_bindu"]}}
CAT = "ashtakavarga_bindu"
KEY = "av-build:l1:syn:v1"


# ── P5b numerical bands (BPHS2:42332-42335): >30 favourable / 25-30 medium / <25 adverse ──
@pytest.mark.parametrize("sav,band", [
    (0, "adverse"), (24, "adverse"), (25, "medium"), (26, "medium"),
    (30, "medium"), (31, "favourable"), (40, "favourable")])
def test_p5b_band_boundaries_are_exact(sav, band):
    out = p5b("SYN", {"SYN": sav})
    assert out["state"] == band and out["sav"] == sav
    assert out["rule"] == "BPHS2:42332-42335"


def test_p5b_reads_the_measured_sav_never_a_configured_value():
    # real extract row: Aquarius SARVA = 23 (< 25 ⇒ adverse); Libra 34 ⇒ favourable
    assert p5b("Aquarius", SARVA_BY_SIGN)["state"] == "adverse"
    assert p5b("Libra", SARVA_BY_SIGN)["state"] == "favourable"
    assert p5b("Gemini", SARVA_BY_SIGN)["state"] == "medium"          # 27
    # the output carries the MEASURED figure — a config threshold of 28 never enters
    assert p5b("Aquarius", SARVA_BY_SIGN)["sav"] == 23


@pytest.mark.parametrize("bad", [True, False, "27", 27.0, -1, math.nan, None, [27]])
def test_p5b_invalid_or_missing_sav_is_unqualified_never_a_band(bad):
    out = p5b("SYN", {"SYN": bad})
    assert out["state"] == "unqualified" and out["operand"] == "SAV(SYN)"
    assert "favourable" != out["state"] != "adverse"


# ── P5a: the transiting graha's OWN BAV; known zero adverse; nonzero unresolved ─────────────
def test_p5a_selects_the_transiting_grahas_own_bav_row():
    assert p5a("Mars", "SYN-X", BAV)["state"] == "adverse"           # Mars BAV(SYN-X) = 0
    assert p5a("Jupiter", "SYN-X", BAV)["state"] == "unresolved"      # Jupiter BAV(SYN-X) = 5
    # a wrong-frame read is detectable: swapping the two grahas flips the outcome
    assert p5a("Jupiter", "SYN-X", BAV)["state"] != p5a("Mars", "SYN-X", BAV)["state"]
    out = p5a("Jupiter", "SYN-X", BAV)
    assert out["operand"] == "BAV(Jupiter)(SYN-X)=5"                  # operand named, own row


def test_p5a_never_substitutes_another_grahas_row_or_the_sav():
    # Saturn has a row only for SYN-Y: SYN-X must be unqualified for Saturn, not Mars's 0 / the SAV 32
    out = p5a("Saturn", "SYN-X", BAV)
    assert out == {"form": "P5a", "state": "unqualified", "operand": "BAV(Saturn)(SYN-X)"}
    # a graha with no row at all
    assert p5a("Venus", "SYN-X", BAV) == {"form": "P5a", "state": "unqualified", "operand": "BAV(Venus)"}
    assert p5a("Mars", "SYN-X", None)["operand"] == "BAV(Mars)"


@pytest.mark.parametrize("bad", [True, "0", 0.0, -2, math.nan, [0]])
def test_p5a_invalid_count_is_unqualified_not_a_known_zero(bad):
    out = p5a("Mars", "SYN-X", {"Mars": {"SYN-X": bad}})
    assert out["state"] == "unqualified" and out["reason"] == "invalid_operand"
    assert out["state"] != "adverse"        # False/0.0 must NOT masquerade as the known zero


def test_p5a_nonzero_is_unresolved_with_no_invented_threshold():
    for n in (1, 2, 5, 8):
        out = p5a("Jupiter", "SYN-X", {"Jupiter": {"SYN-X": n}})
        assert out["state"] == "unresolved" and "threshold" in out["rule"]
        assert "favourable" not in out and "adverse" != out["state"]


# ── P5d integer discipline ──────────────────────────────────────────────────
@pytest.mark.parametrize("pinda,marks", [(True, 3), (3, True), ("204", 3), (204.0, 3), (-1, 3), (204, -3)])
def test_p5d_invalid_operands_are_unqualified(pinda, marks):
    out = p5d(pinda, marks)
    assert out["state"] == "unqualified" and out["reason"] == "invalid_operand"


def test_p5d_remainder_zero_is_the_27th_nakshatra():
    out = p5d(27, 1)
    assert out["remainder"] == 0 and out["nakshatra_index"] == 27 and out["nakshatra"] == "Revati"
    # 204 x 5 = 1020 = 37 x 27 + 21 -> index 21 (written out by hand, not recomputed here)
    out2 = p5d(204, 5)
    assert (out2["remainder"], out2["nakshatra_index"], out2["nakshatra"]) == (21, 21, "Uttara Ashadha")


# ── independent missingness: EVERY subset of present operands, each form gated alone ────────
FORMS = ("P5a", "P5b", "P5c", "P5d", "P5e")


@pytest.mark.parametrize("present", [s for r in range(6) for s in itertools.combinations(FORMS, r)])
def test_each_operand_gates_exactly_its_own_form(present):
    out = qualify_transit(
        "Mars", "SYN-X", av_build_present=True,
        bav_by_graha=BAV if "P5a" in present else None,
        sav_by_sign=SAV if "P5b" in present else None,
        donor_matrix={"Saturn": 1} if "P5c" in present else None,
        pinda=204 if "P5d" in present else None,
        marks=3 if "P5d" in present else None,
        ingress_substrate={"ok": True} if "P5e" in present else None)
    missing_state = {"P5a": "unqualified", "P5b": "unqualified", "P5c": "disabled",
                     "P5d": "unqualified", "P5e": "unqualified"}
    for form in FORMS:
        state = out[form]["state"]
        if form in present:
            assert state != missing_state[form], f"{form} present but gated off by another operand"
        else:
            assert state == missing_state[form], f"{form} absent but not gated"
    # a missing operand never touches a neighbour: P5a/P5b stand whenever their own operand stands
    if "P5a" in present:
        assert out["P5a"]["state"] == "adverse"
    if "P5b" in present:
        assert out["P5b"]["state"] == "favourable"


def test_only_the_whole_av_build_absent_is_cross_form():
    out = qualify_transit("Mars", "SYN-X", av_build_present=False, bav_by_graha=BAV, sav_by_sign=SAV,
                          donor_matrix={"Saturn": 1}, pinda=204, marks=3, ingress_substrate={"ok": True})
    assert {f: out[f]["state"] for f in FORMS} == {f: "unqualified" for f in FORMS}
    assert all(out[f]["operand"] == "AV build" for f in FORMS)


# ── typed operands: the SELECTION rule ──────────────────────────────────────
def test_typed_operands_select_own_bav_and_the_sav_and_record_both():
    ops = typed_operands("Mars", "SYN-Y", bav_by_graha=BAV, sav_by_sign=SAV)
    assert [(o["kind"], o["graha"], o["sign"], o["value"], o["unit"], o["form"]) for o in ops] == [
        ("BAV", "Mars", "SYN-Y", 4, "bindus", "P5a"), ("SAV", None, "SYN-Y", 27, "bindus", "P5b")]
    # Jupiter's BAV(SYN-Y)=2 is NEVER selected for a Mars transit
    assert all(o["value"] != 2 for o in ops if o["kind"] == "BAV")


def test_typed_operands_missingness_is_independent():
    assert [o["kind"] for o in typed_operands("Mars", "SYN-X", bav_by_graha=BAV, sav_by_sign=None)] == ["BAV"]
    assert [o["kind"] for o in typed_operands("Mars", "SYN-X", bav_by_graha=None, sav_by_sign=SAV)] == ["SAV"]
    assert typed_operands("Mars", "SYN-X") == []
    # a graha with no row for the sign contributes no BAV operand (and no substitute)
    assert typed_operands("Saturn", "SYN-X", bav_by_graha=BAV, sav_by_sign=SAV)[0]["kind"] == "SAV"


# ── the AM-7 declaration read-back as an evaluator path (O-BP-3) ────────────
def test_declaration_readback_accepts_matching_figures_and_returns_typed_evidence():
    ops = [dict(o, fact_id=f"F-{o['kind']}", build_id="b1")
           for o in typed_operands("Mars", "SYN-Y", bav_by_graha=BAV, sav_by_sign=SAV)]
    out = consume_declaration(DECLS, KEY, CAT, ops, EXTRACT)
    assert out["state"] == "accepted" and out["declaration"] == KEY and out["governs"] == CAT
    assert [(e["operand"], e["value"], e["unit"], e["scored"], e["fact_id"]) for e in out["evidence"]] == [
        ("BAV", 4, "bindus", False, "F-BAV"), ("SAV", 27, "bindus", False, "F-SAV")]
    # both competing operands are recorded
    assert {e["operand"] for e in out["evidence"]} == {"BAV", "SAV"}


@pytest.mark.parametrize("declarations,key,category,reason", [
    (None, KEY, CAT, "declarations_unavailable"),
    ({}, KEY, CAT, "declaration_absent"),
    (DECLS, "av-build:never-declared", CAT, "declaration_absent"),
    (DECLS, KEY, "some_other_category", "category_not_governed"),
])
def test_declaration_readback_refuses_absent_unavailable_or_ungoverned(declarations, key, category, reason):
    with pytest.raises(DeclarationReadBackRefused) as e:
        consume_declaration(declarations, key, category,
                            typed_operands("Mars", "SYN-X", bav_by_graha=BAV), EXTRACT)
    assert e.value.reason == reason


def test_numeric_mismatch_between_recorded_and_extract_bindu_is_refused_with_both_figures():
    ops = typed_operands("Mars", "SYN-Y", bav_by_graha=BAV, sav_by_sign=SAV)
    ops[0] = dict(ops[0], value=3)                      # recorded BAV 3 vs extract 4
    with pytest.raises(DeclarationReadBackRefused) as e:
        consume_declaration(DECLS, KEY, CAT, ops, EXTRACT)
    assert e.value.reason == "bindu_mismatch"
    assert e.value.detail == {"kind": "BAV", "graha": "Mars", "sign": "SYN-Y", "recorded": 3, "extract": 4}
    # the SAV operand mismatches independently
    ops = typed_operands("Mars", "SYN-Y", bav_by_graha=BAV, sav_by_sign=SAV)
    ops[1] = dict(ops[1], value=28)
    with pytest.raises(DeclarationReadBackRefused) as e2:
        consume_declaration(DECLS, KEY, CAT, ops, EXTRACT)
    assert (e2.value.reason, e2.value.detail["kind"], e2.value.detail["recorded"], e2.value.detail["extract"]) == (
        "bindu_mismatch", "SAV", 28, 27)


def test_the_real_extract_row_is_not_replaced_by_a_config_value():
    # O-BP-5: Aquarius SARVA = 23 measured; a recorded 28 (the config min_sav_score) must be refused
    real = {"BAV": {}, "SAV": SARVA_BY_SIGN}
    ops = [{"kind": "SAV", "graha": None, "sign": "Aquarius", "value": 28, "unit": "bindus", "form": "P5b"}]
    with pytest.raises(DeclarationReadBackRefused) as e:
        consume_declaration(DECLS, KEY, CAT, ops, real)
    assert e.value.reason == "bindu_mismatch" and e.value.detail["extract"] == 23
    ok = consume_declaration(DECLS, KEY, CAT, [dict(ops[0], value=23)], real)
    assert ok["evidence"][0]["value"] == 23


def test_operand_absent_from_the_extract_is_refused_not_assumed():
    ops = [{"kind": "BAV", "graha": "Venus", "sign": "SYN-X", "value": 4, "unit": "bindus", "form": "P5a"}]
    with pytest.raises(DeclarationReadBackRefused) as e:
        consume_declaration(DECLS, KEY, CAT, ops, EXTRACT)
    assert e.value.reason == "operand_missing_from_extract"
    with pytest.raises(DeclarationReadBackRefused) as e2:
        consume_declaration(DECLS, KEY, CAT, [{"kind": "XYZ", "sign": "SYN-X", "value": 1}], EXTRACT)
    assert e2.value.reason == "operand_missing_from_extract"
    with pytest.raises(DeclarationReadBackRefused):
        consume_declaration(DECLS, KEY, CAT, ops, None)


def test_citation_resolves_through_the_declaration_only_after_a_successful_readback():
    # the P5 path is gated on the declaration row (T0-11); a successful read-back is what makes the
    # prerequisite TRUE; a refused read-back means NO record — never a stored false/unknown.
    p5 = RULE_PATHS[("P5", RULE_VERSION)]
    assert ("av_polarity_declaration_exists", RULE_VERSION) in [tuple(r) for r in p5["prerequisites"]]
    ops = typed_operands("Jupiter", "SYN-X", bav_by_graha=BAV, sav_by_sign=SAV)
    accepted = consume_declaration(DECLS, KEY, CAT, ops, EXTRACT)
    state = evaluate("declaration_exists", {"declarations": DECLS, "key": accepted["declaration"]})
    assert state == "true" and admission_state([state]) == ADMITTED
    with pytest.raises(DeclarationReadBackRefused):
        consume_declaration({}, KEY, CAT, ops, EXTRACT)
    # (the stored-false path exists only in the predicate evaluator, not in a written record)
    assert admission_state([evaluate("declaration_exists", {"declarations": {}, "key": KEY})]) == EXCLUDED
