"""O-BP-* — bindu polarity / P5 form oracles (GOCHARA_DESIGN_SPECS_v1_4 §8,
§2.2 P5).

Synthetic fixture rows (O-BP-1) are labelled synthetic with explicit keys —
never attributed to the L1 extract (R3-S03); real extract rows are cited for
contrast (extract v1_0 has NO zero BAV and NO SAV 24).
"""
from __future__ import annotations

from services.gochara_rules.ashtakavarga import (
    P5C_DISABLED_REASON, SARVA_BY_SIGN, SHODHYA_PINDA, kakshya_of, p5a, p5b,
    p5c, p5c_resolve_donor, p5d, qualify_transit,
)

# O-BP-1 SYNTHETIC fixture rows (fixture=true, explicit keys; R3-S03)
SYNTH_BAV = {"Mars": {"SYN-X": 0}, "Jupiter": {"SYN-X": 5}}
SYNTH_SAV = {"SYN-X": 32}


# ── O-BP-1 (literal) — known-zero adverse; competing-values mutation ─────────
def test_obp1_known_zero_adverse():
    # Mars transits SYN-X under P5a; the operand is the TRANSITING graha's
    # own BAV: Mars BAV(SYN-X) = 0 ⇒ adverse (BPHS ch.70 vv.24-27), with the
    # count shown; NOT unqualified, NOT favourable/medium.
    r = p5a("Mars", "SYN-X", SYNTH_BAV)
    assert r["state"] == "adverse"
    assert r["count"] == 0
    # mutation (competing values): reading the sign's SAV (32 → favourable)
    assert p5b("SYN-X", SYNTH_SAV)["state"] == "favourable"
    assert p5b("SYN-X", SYNTH_SAV)["state"] != r["state"]
    # …or Jupiter's BAV (5 → not zero ⇒ unresolved, not adverse)
    wrong_frame = p5a("Jupiter", "SYN-X", SYNTH_BAV)
    assert wrong_frame["state"] == "unresolved"
    assert wrong_frame["state"] != "adverse"
    # …or emitting unqualified — all fail
    assert r["state"] not in ("unqualified", "favourable", "medium")


def test_obp1_nonzero_comparison_unresolved():
    # any nonzero comparison evaluates to `unresolved` with the operand named
    # (never to a mean or an invented band)
    r = p5a("Mars", "SYN-Y", {"Mars": {"SYN-Y": 4}})
    assert r["state"] == "unresolved"
    assert r["operand"] == "BAV(Mars)(SYN-Y)=4"


# ── O-BP-2 — per-form gating (cases A/B/C) ───────────────────────────────────
def test_obp2_case_a_whole_build_absent():
    # case A: AV build missing entirely ⇒ ALL P5 forms unqualified (operand
    # named: AV build)
    out = qualify_transit("Mars", "SYN-X", av_build_present=False)
    assert set(out) == {"P5a", "P5b", "P5c", "P5d", "P5e"}
    for form in out.values():
        assert form["state"] == "unqualified"
        assert form["operand"] == "AV build"


def test_obp2_case_b_donor_matrix_missing():
    # case B (the CURRENT chart state): build present, per-contributor matrix
    # missing ⇒ P5c ALONE disabled with the rebuild-pending reason;
    # P5a/P5b results stand (missing donor data never erases a known-zero P5a)
    out = qualify_transit("Mars", "SYN-X", bav_by_graha=SYNTH_BAV,
                          sav_by_sign=SYNTH_SAV, donor_matrix=None)
    assert out["P5c"]["state"] == "disabled"
    assert "#2731" in out["P5c"]["reason"]
    assert out["P5a"]["state"] == "adverse"   # known-zero stands
    assert out["P5b"]["state"] == "favourable"
    # mutation: case B knocking out P5a (the v1.0 contradiction) fails
    assert out["P5a"]["state"] != "unqualified"


def test_obp2_case_c_sav_missing():
    # case C: build present, per-sign BAV present, SAV rows missing ⇒ P5b
    # ALONE unqualified with the missing SAV operand named — P5a untouched
    out = qualify_transit("Mars", "SYN-X", bav_by_graha=SYNTH_BAV,
                          sav_by_sign=None)
    assert out["P5b"]["state"] == "unqualified"
    assert out["P5b"]["operand"] == "SAV(SYN-X)"
    assert out["P5a"]["state"] == "adverse"


# ── O-BP-4 — kakṣyā donor key; P5c disabled label honesty ────────────────────
def test_obp4_kakshya_donor_key():
    # division order Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna
    # (PG301 śl.18-19); a degree inside the 2nd division is Jupiter's kakṣyā
    cell, lord = kakshya_of(5.0)  # 3°45′–7°30′
    assert (cell, lord) == (2, "Jupiter")
    # the division resolves through the DECLARED donor key
    r = p5c_resolve_donor(5.0, {"Jupiter": 1})
    assert r["state"] == "resolved"
    assert r["kakshya_lord"] == "Jupiter"
    assert r["donor_mark"] == 1
    # mutation: a key-mismatched lookup fails
    assert p5c_resolve_donor(5.0, {"Saturn": 1})["state"] == "unresolved"
    # donor rows pending ⇒ P5c disabled, labelled with the rebuild-pending
    # reason — a sign-level fallback is never presented as donor evaluation
    d = p5c(None)
    assert d["state"] == "disabled"
    assert d["reason"] == P5C_DISABLED_REASON
    assert "rebuild" in d["reason"]


# ── O-BP-5 (literal) — measured SAV vs config ────────────────────────────────
def test_obp5_measured_sav_not_config():
    # REAL extract row: Aquarius SARVA = 23 (fact_id 36b81039eeb707a7,
    # extract v1_0, tier single_pass verbatim; band <25 → adverse) while
    # config min_sav_score = 28 (would read as 25-30 → medium).
    assert SARVA_BY_SIGN["Aquarius"] == 23
    measured = p5b("Aquarius", SARVA_BY_SIGN)
    assert measured["state"] == "adverse"
    assert measured["sav"] == 23
    # mutation: config-as-measurement (the w21 proxy defect) reads medium —
    # the fixture's band crossing makes the two readings observably different
    config_read = p5b("Aquarius", {"Aquarius": 28})
    assert config_read["state"] == "medium"
    assert config_read["state"] != measured["state"]


# ── P5d operand conventions (spec §2.2) ──────────────────────────────────────
def test_p5d_pinda_marks_mod_27():
    # the textbook worked example: marks 2, piṇḍa 148 → 296 mod 27 = 26 →
    # Uttarabhadra (the text's example, not this chart's data — CORPUS_READS §9)
    r = p5d(148, 2)
    assert r["remainder"] == 26
    assert r["nakshatra"] == "Uttara Bhadrapada"
    # remainder 0 ⇒ the 27th nakṣatra (Revatī)
    r0 = p5d(27, 1)
    assert r0["remainder"] == 0
    assert r0["nakshatra_index"] == 27
    assert r0["nakshatra"] == "Revati"
    # chart operands resolved from extract v1_1 (spec §2.2 P5d, printed)
    assert SHODHYA_PINDA == {"Sun": 204, "Moon": 162, "Mars": 222,
                             "Mercury": 198, "Jupiter": 187, "Venus": 126,
                             "Saturn": 102}
