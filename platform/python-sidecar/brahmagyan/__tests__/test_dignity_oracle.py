"""Tests for brahmagyan.dignity_oracle — B-01 Dignity Oracle.

Six goldens per lane spec, plus boundary cases.
All tests must pass with NO live DB (pure-logic, data-driven from
_DIGNITY_REFERENCE — the authoritative static reference in bg_dignity_reference.py).
"""
from __future__ import annotations

import pytest

from brahmagyan.dignity_oracle import classify_dignity


# ── §1 Lane spec goldens (must all pass) ─────────────────────────────────────

def test_jupiter_sagittarius_in_mt_range():
    """Jupiter 0°-10° Sag is moolatrikona, not own."""
    assert classify_dignity("Jupiter", "Sagittarius", 9.79) == "moolatrikona"


def test_jupiter_sagittarius_outside_mt_range():
    """Jupiter at 15° Sag is outside MT range → own (own sign)."""
    assert classify_dignity("Jupiter", "Sagittarius", 15.0) == "own"


def test_rahu_taurus_exalted():
    """Rahu exalted in Taurus — no MT or own tier for nodes."""
    assert classify_dignity("Rahu", "Taurus", 5.0) == "exalted"


def test_ketu_sagittarius_neutral():
    """Ketu in Sagittarius — no MT or own tier for nodes → neutral."""
    assert classify_dignity("Ketu", "Sagittarius", 5.0) == "neutral"


def test_sun_leo_in_mt_range():
    """Sun MT in Leo 0°-20°; at 10° → moolatrikona."""
    assert classify_dignity("Sun", "Leo", 10.0) == "moolatrikona"


def test_sun_leo_outside_mt_range():
    """Sun own in Leo, but at 25° outside MT range (0°-20°) → own."""
    assert classify_dignity("Sun", "Leo", 25.0) == "own"


# ── §2 Additional boundary tests ─────────────────────────────────────────────

def test_sun_exalted_aries():
    assert classify_dignity("Sun", "Aries", 10.0) == "exalted"


def test_sun_debilitated_libra():
    assert classify_dignity("Sun", "Libra", 10.0) == "debilitated"


def test_moon_exalted_taurus():
    assert classify_dignity("Moon", "Taurus", 3.0) == "exalted"


def test_moon_own_cancer():
    """Moon own in Cancer — Cancer is not Moon's MT sign (Taurus is)."""
    assert classify_dignity("Moon", "Cancer", 15.0) == "own"


def test_moon_mt_taurus_within_range():
    """Moon's exaltation sign (Taurus) is also Moon's MT sign (Taurus 4°-30°).
    Exaltation is checked before MT, so in-range returns 'exalted', not 'moolatrikona'.
    This is the classical priority: exalted > moolatrikona when signs coincide."""
    # In Taurus at 10° (within 4°-30° MT range): exaltation wins
    assert classify_dignity("Moon", "Taurus", 10.0) == "exalted"


def test_moon_taurus_below_mt_boundary():
    """Moon in Taurus at 3° — below MT lower bound (4°) AND exalted → exalted."""
    assert classify_dignity("Moon", "Taurus", 3.0) == "exalted"


def test_mercury_mt_virgo():
    """Mercury's exaltation sign (Virgo) is also Mercury's MT sign (Virgo 16°-20°).
    Exaltation is checked before MT, so at 18° (in MT range) → 'exalted', not 'moolatrikona'.
    Classical priority: exalted > moolatrikona when signs coincide."""
    assert classify_dignity("Mercury", "Virgo", 18.0) == "exalted"


def test_mercury_virgo_outside_mt():
    """Mercury in Virgo at 25° — exaltation sign = Virgo, so → exalted (not own).
    Exaltation check fires first; own sign check is never reached for Virgo."""
    assert classify_dignity("Mercury", "Virgo", 25.0) == "exalted"


def test_mars_aries_in_mt_range():
    """Mars MT in Aries 0°-12°; at 5° → moolatrikona."""
    assert classify_dignity("Mars", "Aries", 5.0) == "moolatrikona"


def test_mars_aries_outside_mt_range():
    """Mars in Aries at 15° — outside MT range → own."""
    assert classify_dignity("Mars", "Aries", 15.0) == "own"


def test_jupiter_cancer_exalted():
    assert classify_dignity("Jupiter", "Cancer", 5.0) == "exalted"


def test_jupiter_capricorn_debilitated():
    assert classify_dignity("Jupiter", "Capricorn", 5.0) == "debilitated"


def test_jupiter_pisces_own():
    """Jupiter own in Pisces (not MT sign, which is Sagittarius)."""
    assert classify_dignity("Jupiter", "Pisces", 5.0) == "own"


def test_venus_mt_libra():
    """Venus MT in Libra 0°-15°; at 10° → moolatrikona."""
    assert classify_dignity("Venus", "Libra", 10.0) == "moolatrikona"


def test_venus_libra_outside_mt():
    """Venus in Libra at 20° — outside MT → own."""
    assert classify_dignity("Venus", "Libra", 20.0) == "own"


def test_saturn_mt_aquarius():
    """Saturn MT in Aquarius 0°-20°; at 10° → moolatrikona."""
    assert classify_dignity("Saturn", "Aquarius", 10.0) == "moolatrikona"


def test_saturn_aquarius_outside_mt():
    """Saturn in Aquarius at 25° → own."""
    assert classify_dignity("Saturn", "Aquarius", 25.0) == "own"


def test_neutral_planet():
    """Sun in Gemini — neither exalted, debilitated, own, nor MT → neutral."""
    assert classify_dignity("Sun", "Gemini", 15.0) == "neutral"


def test_ketu_debilitated_taurus():
    """Ketu debilitated in Taurus — node, so only exalted/debilitated/neutral."""
    assert classify_dignity("Ketu", "Taurus", 5.0) == "debilitated"


def test_rahu_debilitated_scorpio():
    assert classify_dignity("Rahu", "Scorpio", 5.0) == "debilitated"


def test_rahu_neutral():
    """Rahu in Gemini — neither exalted (Taurus) nor debilitated (Scorpio) → neutral."""
    assert classify_dignity("Rahu", "Gemini", 15.0) == "neutral"


def test_mt_boundary_exclusive_upper():
    """MT range is [from, to) — the upper bound is exclusive."""
    # Jupiter MT is 0°-10° in Sagittarius: degree=10.0 is NOT in range
    assert classify_dignity("Jupiter", "Sagittarius", 10.0) == "own"


def test_mt_boundary_inclusive_lower():
    """MT range lower bound is inclusive."""
    # Jupiter MT is 0°-10° in Sagittarius: degree=0.0 IS in range
    assert classify_dignity("Jupiter", "Sagittarius", 0.0) == "moolatrikona"


def test_unknown_graha_raises():
    """An unknown graha name raises KeyError."""
    with pytest.raises(KeyError):
        classify_dignity("Neptune", "Aries", 5.0)


# ── §2b PAR-R-2 — exact-boundary goldens for every graha with an MT range ────
#      (PRATINIDHI ruling PAR-R-2: half-open [from, to) confirmed as-built; the
#      ruling REQUIRES the boundary decision be visible as test evidence for
#      every MT-bearing graha, not just Jupiter — "a boundary decided but
#      untested is an undetected boundary", §N.8.)

def test_sun_mt_upper_boundary_is_own():
    """Sun MT is 0-20 Leo: 20°00' is own (upper bound exclusive)."""
    assert classify_dignity("Sun", "Leo", 20.0) == "own"


def test_sun_mt_lower_boundary_is_mt():
    assert classify_dignity("Sun", "Leo", 0.0) == "moolatrikona"


def test_moon_taurus_is_always_exalted_mt_currently_unreachable():
    """FLAGGED FINDING (not a PRATINIDHI-resolved boundary — see DIAGNOSIS.md):
    Moon's exaltation sign (Taurus) and MT sign (Taurus) are the SAME sign, and
    classify_dignity's exaltation check is sign-only (no degree gate), checked
    BEFORE moolatrikona in priority order. Consequence: for Moon, "moolatrikona"
    is currently unreachable at ANY degree in Taurus — exalted always wins.
    Asserting actual current behavior at what would otherwise be the MT range
    (4-30) rather than silently omitting Moon's boundary coverage or asserting
    an unverified guess about the classically-correct resolution."""
    assert classify_dignity("Moon", "Taurus", 4.0) == "exalted"
    assert classify_dignity("Moon", "Taurus", 29.999) == "exalted"
    assert classify_dignity("Moon", "Taurus", 3.999) == "exalted"


def test_mars_mt_upper_boundary_is_own():
    """Mars MT is 0-12 Aries: 12°00' is own."""
    assert classify_dignity("Mars", "Aries", 12.0) == "own"


def test_mercury_virgo_is_always_exalted_mt_currently_unreachable():
    """FLAGGED FINDING (same class as Moon/Taurus above): Mercury's exaltation
    sign (Virgo) and MT sign (Virgo) are also the same sign, and Virgo is
    additionally one of Mercury's own signs — a rare triple overlap. Exaltation
    (sign-only, no degree gate) wins over MT at every degree, making Mercury's
    16-20 Virgo MT range currently unreachable too."""
    assert classify_dignity("Mercury", "Virgo", 15.99) == "exalted"
    assert classify_dignity("Mercury", "Virgo", 16.0) == "exalted"
    assert classify_dignity("Mercury", "Virgo", 20.0) == "exalted"


def test_venus_mt_upper_boundary_is_own():
    """Venus MT is 0-15 Libra: 15°00' is own."""
    assert classify_dignity("Venus", "Libra", 15.0) == "own"


def test_saturn_mt_upper_boundary_is_own():
    """Saturn MT is 0-20 Aquarius: 20°00' is own."""
    assert classify_dignity("Saturn", "Aquarius", 20.0) == "own"


# ── §3 Recurrence guard — §N.7 item 3 (no wrapper-local constant may shadow ──
#      an L1-computed value, even when currently correct; a constant can
#      drift from its source, a reference cannot).
#
#      dignity_oracle._DATA is a deliberate static reproduction of
#      bg_dignity_reference._DIGNITY_REFERENCE (the module docstring explains
#      why it does not import the writer module directly — to avoid pulling
#      writer-layer deps into serving-layer code). That tradeoff is only safe
#      if the two are asserted equal in CI; this test is the recurrence guard
#      that makes the next silent divergence fail closed instead of drifting.

def test_data_matches_bg_dignity_reference_source_of_truth():
    """dignity_oracle._DATA must stay byte-for-byte consistent with the
    authoritative L0 reference (bg_dignity_reference._DIGNITY_REFERENCE).
    A future edit to one without the other must fail this test, not ship
    a silent divergence between the two dignity classifiers.
    """
    from brahmagyan.dignity_oracle import _DATA
    from pipeline.orchestrator.writers.bg_dignity_reference import (
        _DIGNITY_REFERENCE,
    )

    ref_by_graha = {row["graha"]: row for row in _DIGNITY_REFERENCE}

    # Same graha set (excluding the two nodes, which bg_dignity_reference
    # also carries — dignity_oracle intentionally keeps them for the
    # nodes early-exit branch).
    assert set(_DATA.keys()) == set(ref_by_graha.keys()), (
        "dignity_oracle._DATA graha set has diverged from "
        "bg_dignity_reference._DIGNITY_REFERENCE"
    )

    for graha, ref_row in ref_by_graha.items():
        local = _DATA[graha]
        assert local["exaltation"] == ref_row["exaltation_sign"], graha
        assert local["debilitation"] == ref_row["debilitation_sign"], graha
        assert local["mt_sign"] == ref_row["moolatrikona_sign"], graha
        assert local["mt_from"] == ref_row["moolatrikona_from"], graha
        assert local["mt_to"] == ref_row["moolatrikona_to"], graha
        assert set(local["own"]) == set(ref_row["own_signs"]), graha
