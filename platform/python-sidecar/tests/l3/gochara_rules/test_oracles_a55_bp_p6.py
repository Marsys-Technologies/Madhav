"""Frozen A5.5 test oracles — literal-input implementations.

Oracle set (GOCHARA_TEST_ORACLES_v1_4, given/when/then normative):
O-BP-2, O-BP-3, O-BP-4 (§8 bindu polarity / P5a-P5c); O-P6-TARA (§2 P6).

L1 pins (constants): chart 482012f1-710e-4a25-994a-93821f5871aa,
ayanamsha lahiri_chitrapaksha, natal build 1c092ffb-72eb-4614-8422-552ca6eae985;
AV extract v1_0 sha256 312de09e…88fe83 (96 BAV+SARVA rows, tier single_pass
verbatim; real SARVA per sign Aries 29, Taurus 29, Gemini 27, Cancer 32,
Leo 30, Virgo 26, Libra 34, Scorpio 32, Sagittarius 25, Capricorn 27,
Aquarius 23, Pisces 23). All operands are printed literals — no database is
queried. Synthetic rows are labelled synthetic (R3-S03).
"""
from __future__ import annotations

import pytest

from services.gochara_rules.ashtakavarga import (
    P5C_DISABLED_REASON, SARVA_BY_SIGN, kakshya_of, p5a, p5b, p5c,
    p5c_resolve_donor, qualify_transit,
)
from services.gochara_rules.p6 import annotate, tara
from services.gochara_rules.predicates import (
    ADMITTED, EXCLUDED, UNQUALIFIED, admission_state, evaluate,
)
from services.gochara_rules.registry import RULE_PATHS, RULE_VERSION
from services.gochara_kernel.convention import (
    KAKSHYA_CELL_DEG, KAKSHYA_LORD_ORDER,
)

# L1 natal longitudes (build 1c092ffb), constants.natal verbatim.
LAGNA_DEG = 12.43        # Aries lagna

# O-BP-1/O-BP-2 synthetic rows (fixture=true, explicit keys; R3-S03).
SYNTH_BAV = {"Mars": {"SYN-X": 0}, "Jupiter": {"SYN-X": 5}}
SYNTH_SAV = {"SYN-X": 32}
def test_o_bp_2_case_a_whole_av_build_absent():
    # case A: AV build missing entirely ⇒ ALL P5 forms unqualified (operand
    # named: AV build).
    out = qualify_transit("Mars", "SYN-X", av_build_present=False)
    assert set(out) == {"P5a", "P5b", "P5c", "P5d", "P5e"}
    for form, result in out.items():
        assert result["state"] == "unqualified", form
        assert result["operand"] == "AV build", form


def test_o_bp_2_case_b_donor_matrix_absent_p5c_alone():
    # case B (the CURRENT chart state): build present, per-contributor matrix
    # missing (donor rows pending the native-authorised ga_strength rebuild,
    # writer merged in PR #2731) ⇒ P5c ALONE disabled with the
    # rebuild-pending reason; P5a/P5b results stand.
    out = qualify_transit("Mars", "SYN-X", bav_by_graha=SYNTH_BAV,
                          sav_by_sign=SYNTH_SAV, donor_matrix=None)
    assert out["P5c"]["state"] == "disabled"
    assert "rebuild" in out["P5c"]["reason"]
    assert "#2731" in out["P5c"]["reason"]
    assert out["P5a"]["state"] == "adverse"      # known-zero stands
    assert out["P5a"]["count"] == 0
    assert out["P5b"]["state"] == "favourable"   # SAV 32 > 30 stands
    # mutation guard: case B knocking out P5a (the v1.0 contradiction) fails.
    assert out["P5a"]["state"] != "unqualified"


def test_o_bp_2_case_c_sav_absent_p5b_alone():
    # case C: build present, per-sign BAV present, SAV rows missing ⇒ P5b
    # ALONE unqualified with the missing SAV operand named — P5a stands
    # untouched (each operand gates exactly its own form, §2.2).
    out = qualify_transit("Mars", "SYN-X", bav_by_graha=SYNTH_BAV,
                          sav_by_sign=None)
    assert out["P5b"]["state"] == "unqualified"
    assert out["P5b"]["operand"] == "SAV(SYN-X)"
    assert out["P5a"]["state"] == "adverse"
    # mutation guard: case C knocking out P5a fails.
    assert out["P5a"]["state"] != "unqualified"


# ── O-BP-3 — citation resolves through the polarity declaration row ──────────
# The declaration row per spec §8.1 (N8): pyjhora_dots = benefic_marks ↔
# rekhā (Santhanam BPHS names the benefic mark rekhā, BPHS2:35666-35684).
POLARITY_DECLARATION = {
    "av_polarity_declaration": {
        "convention": "pyjhora_dots",
        "benefic_mark_name": "rekhā",
        "malefic_mark_name": "no-mark",
        "source_ref": "BPHS2:35666-35684 (Santhanam)",
        "applies_to_fact_categories": [
            "ashtakavarga_bindu_sign", "ashtakavarga_bindu_contributor"],
    },
}


def test_o_bp_3_citation_resolves_through_declaration():
    # given: the citation string 'BPHS ch.66/70' emitted by the P5 path row.
    p5 = RULE_PATHS[("P5", RULE_VERSION)]
    assert "BPHS ch.66" in p5["source_text"]
    assert "ch.70" in p5["source_text"]
    # the path is gated on the declaration row (T0-11; §8.2 inv 1).
    assert ("av_polarity_declaration_exists", RULE_VERSION) in [
        tuple(ref) for ref in p5["prerequisites"]]
    # when: the citation is resolved — then: it resolves through the polarity
    # declaration row (rekhā = benefic), verified by reading the declaration
    # back.
    state = evaluate("declaration_exists", {
        "declarations": POLARITY_DECLARATION,
        "key": "av_polarity_declaration"})
    assert state == "true"
    declaration = POLARITY_DECLARATION["av_polarity_declaration"]
    assert declaration["benefic_mark_name"] == "rekhā"
    assert declaration["convention"] == "pyjhora_dots"
    assert admission_state([state]) == ADMITTED
    # then: a citation emitted with no declaration row is a write-time
    # rejection — the join fails closed, never open.
    absent = evaluate("declaration_exists", {
        "declarations": {}, "key": "av_polarity_declaration"})
    assert absent == "false"
    assert admission_state([absent]) == EXCLUDED
    unknown = evaluate("declaration_exists", {
        "declarations": None, "key": "av_polarity_declaration"})
    assert unknown == "unknown"
    assert admission_state([unknown]) == UNQUALIFIED


# ── O-BP-4 — P5c kakṣyā donor key; absent-matrix path labelled ───────────────
def test_o_bp_4_kakshya_division_order_and_donor_key():
    # given: kakṣyā division order Saturn, Jupiter, Mars, Sun, Venus,
    # Mercury, Moon, Lagna (PG301 śl.18-19).
    assert KAKSHYA_LORD_ORDER == (
        "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
        "Lagna")
    assert KAKSHYA_CELL_DEG == 3.75  # equal-eighths grid
    # a transited degree pinned inside the 2nd division (3°45′–7°30′ =
    # Jupiter's kakṣyā).
    deg = 5.0
    cell, lord = kakshya_of(deg)
    assert (cell, lord) == (2, "Jupiter")
    # (a) synthetic donor-key fixture with Jupiter as a mark-donor: the
    # division resolves through the DECLARED donor key (donor's benefic mark
    # in that division).
    r = p5c_resolve_donor(deg, {"Jupiter": 1})
    assert r["form"] == "P5c"
    assert r["state"] == "resolved"
    assert r["kakshya"] == 2
    assert r["kakshya_lord"] == "Jupiter"
    assert r["donor_mark"] == 1
    # mutation guard: a key-mismatched lookup fails (unresolved, operand
    # named) — resolving through a different contributor key fails.
    wrong = p5c_resolve_donor(deg, {"Saturn": 1})
    assert wrong["state"] == "unresolved"
    assert "Jupiter" in wrong["operand"]


def test_o_bp_4_absent_matrix_disabled_and_fallback_labelled():
    # (b) the absent-matrix path: donor rows pending the native-authorised
    # ga_strength rebuild ⇒ P5c disabled, rebuild-pending reason; NEVER a
    # silent donor resolution.
    d = p5c_resolve_donor(5.0, None)
    assert d["form"] == "P5c"
    assert d["state"] == "disabled"
    assert d["reason"] == P5C_DISABLED_REASON
    assert "rebuild" in d["reason"] and "#2731" in d["reason"]
    assert "donor_mark" not in d
    # the sign-level fallback: the only sign-level qualification available is
    # p5a(), whose form key is P5a — presenting it as P5c is the mutation.
    fallback = p5a("Jupiter", "SYN-X", SYNTH_BAV)
    assert fallback["form"] == "P5a"
    assert fallback["state"] == "unresolved"  # nonzero count, no threshold
    assert fallback["form"] != "P5c"
    # real extract contrast: Aquarius SARVA = 23 (extract v1_0, tier
    # single_pass verbatim) — sign-level P5b band <25 adverse.
    assert SARVA_BY_SIGN["Aquarius"] == 23
    assert p5b("Aquarius", SARVA_BY_SIGN)["state"] == "adverse"


@pytest.mark.xfail(
    reason="A5.5 FINDING: no code path emits the sign-level fallback label "
           "'coarser P5a qualification' (spec §8/O-BP-4); A5.2/A5.3 to "
           "implement on the presentation path",
    strict=True)
def test_o_bp_4_fallback_label_emitted_by_real_path():
    # the oracle's label requirement asserted against the REAL emitter:
    # with the donor matrix absent, the presentation of the sign-level
    # fallback must carry label 'coarser P5a qualification' — never donor
    # evaluation. Today qualify_transit emits the disabled P5c dict and a
    # bare P5a result with no such label (the label exists only in an
    # ashtakavarga.py docstring) — strict xfail records the gap.
    out = qualify_transit("Jupiter", "SYN-X", bav_by_graha=SYNTH_BAV,
                          sav_by_sign=SYNTH_SAV, donor_matrix=None)
    assert out["P5c"]["state"] == "disabled"
    emitted_labels = {
        v.get("label") for v in out.values() if isinstance(v, dict)}
    assert "coarser P5a qualification" in emitted_labels


# ── O-P6-TARA — tārā nine-fold class 6 (twins case), testimony only ──────────
def test_o_p6_tara_class_6_twins_fixture():
    # given: pinned janma-nakṣatra and day nakṣatra — natal star index 24,
    # transit index 20; zero-based inclusive cyclic distance 24 ⇒ nine-fold
    # class 6 (MC PG67/PG79 [D]).
    r = tara(24, 20)
    assert r["count"] == (20 - 24) % 27 + 1 == 24
    assert r["class"] == 24 % 9 == 6
    # then: the tārā term is PRESENT with the correct normalised key and
    # class — a null key (the case-mismatch defect) or absent term fails.
    assert r["operator"] == "tara"
    assert r["class_name"] == "sadhaka"
    assert r["source"] == "MC PG67/PG79 [D]"
    # P6 being testimony, the term annotates and does not weight.
    assert r["operator_role"] == "testimony"
    assert r["weight"] == 0.0
    window = {"window_id": "w-day", "score": 0.42, "annotations": []}
    out = annotate(window, tara(24, 20))
    assert out["score"] == 0.42  # no score movement
    assert out["annotations"][0]["class"] == 6
    # mutation guard: a wrong nine-fold class fails.
    assert r["class"] != 7


@pytest.mark.xfail(
    reason="A5.5 FINDING: no name→index normalisation exists on the P6 path "
           "(tara() takes ints; the case-mismatch defect #5 lives in a "
           "normaliser that is not built); spec §2/O-P6-TARA",
    strict=True)
def test_o_p6_tara_name_to_index_normalisation():
    # the null-key (case-mismatch) guard asserted against the REAL normaliser:
    # a case-variant nakṣatra key must map to the pinned indices (natal 24,
    # transit 20) and never to None. No such function exists on the merged
    # path today — strict xfail records the gap.
    from services.gochara_rules.p6 import nakshatra_index  # expected emitter
    assert nakshatra_index("SHATABHISHA".lower()) == 24   # natal star (twins)
    assert nakshatra_index("purvashadha".upper()) == 20   # day star (twins)
