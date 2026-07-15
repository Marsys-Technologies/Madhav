"""Unit tests for bodha_writers/bhavat_bhavam_amplifier.py (D-1.5b Lane B-4, CR-97).

Includes the two real type specimens verified live on chart 482012f1
(482012f1-710e-4a25-994a-93821f5871aa, lahiri_chitrapaksha) via ga_yoga_firings:
  - dhana_yoga_2_5_9_11 / dhana_yoga_house_lords fired in H9 (strength 1.0218);
    H9's Bhavat-Bhavam derived houses are {5, 11}; H11 has fired yogas
    (anapha 1.0101, ardhachandra 1.2054, chatra 1.2054) => amplifier fires.
  - sasa fired in H7 (strength 1.566); H7's derived houses are {4, 10}; H10 has
    fired yogas (anapha, ardhachandra, budha_aditya 1.3863, chatra,
    sarasvati_yoga, vasi) => amplifier fires.

Run: python -m pytest platform/python-sidecar/bodha_writers/__tests__/test_bhavat_bhavam_amplifier.py -v
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from bodha_writers.bhavat_bhavam_amplifier import (
    CLASS_PRIOR,
    SIGNAL_TYPE_CLASS,
    SOURCE_SUBSYSTEM,
    SalientConfig,
    compute_bhavat_bhavam_amplifiers,
    _clamp_below_primary,
)


AYA = "lahiri_chitrapaksha"


# ──────────────────────────────────────────────────────────────────────────────
# DR-3 ratified constants — pin them so a silent edit trips a test, not a build
# ──────────────────────────────────────────────────────────────────────────────

def test_ratified_constants():
    assert CLASS_PRIOR == 0.85
    assert SOURCE_SUBSYSTEM == "structural"
    assert SIGNAL_TYPE_CLASS == "bhavat_bhavam_amplifier"


# ──────────────────────────────────────────────────────────────────────────────
# Real type specimens (chart 482012f1)
# ──────────────────────────────────────────────────────────────────────────────

def test_specimen_dhana_yoga_h9_fires_derived_11th():
    candidates = [
        SalientConfig("dhana_yoga_2_5_9_11", house=9, source="yoga_firing",
                       salience_reference=1.0218, ayanamsha_id=AYA),
        SalientConfig("anapha", house=11, source="yoga_firing",
                       salience_reference=1.0101, ayanamsha_id=AYA),
        SalientConfig("anapha", house=10, source="yoga_firing",
                       salience_reference=1.0101, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    fired = [s for s in out if s.primary_identifier == "dhana_yoga_2_5_9_11" and s.derived_house == 11]
    assert fired, "Dhana-yoga-in-H9 -> derived-11th amplifier must fire (real chart specimen)"
    for sig in fired:
        assert sig.primary_house == 9
        assert sig.computed_salience < sig.primary_salience


def test_specimen_sasa_h7_fires_derived_10th():
    candidates = [
        SalientConfig("sasa", house=7, source="yoga_firing",
                       salience_reference=1.566, ayanamsha_id=AYA),
        SalientConfig("budha_aditya", house=10, source="yoga_firing",
                       salience_reference=1.3863, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    fired = [s for s in out if s.primary_identifier == "sasa" and s.derived_house == 10]
    assert fired, "Sasa-in-H7 -> derived-10th amplifier must fire (real chart specimen)"
    for sig in fired:
        assert sig.primary_house == 7
        assert sig.computed_salience < sig.primary_salience


# ──────────────────────────────────────────────────────────────────────────────
# Restraint rule 1 — NEVER A GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def test_no_generation_without_a_salient_primary():
    """A salient occupant sitting alone in a derived house with no salient
    primary anywhere must never manufacture a signal."""
    candidates = [
        SalientConfig("anapha", house=11, source="yoga_firing",
                       salience_reference=1.0101, ayanamsha_id=AYA),
    ]
    assert compute_bhavat_bhavam_amplifiers(candidates) == []


def test_no_generation_without_a_salient_occupant():
    """A salient primary in H9 with nothing salient in its derived houses
    (5, 11) must not fire."""
    candidates = [
        SalientConfig("dhana_yoga_2_5_9_11", house=9, source="yoga_firing",
                       salience_reference=1.0218, ayanamsha_id=AYA),
    ]
    assert compute_bhavat_bhavam_amplifiers(candidates) == []


def test_empty_input_generates_nothing():
    assert compute_bhavat_bhavam_amplifiers([]) == []


# ──────────────────────────────────────────────────────────────────────────────
# Restraint rule 2 — EVEN HOUSES RECEIVE NOTHING (never fire the class)
# ──────────────────────────────────────────────────────────────────────────────

def test_even_house_primary_never_fires():
    """Even a maximally-favorable setup (salient primary AND a salient
    'occupant' in every other house) must not fire for an even primary house
    — there is no derived house to anchor on."""
    candidates = [
        SalientConfig("career_yoga", house=10, source="yoga_firing",
                       salience_reference=1.5, ayanamsha_id=AYA),
    ] + [
        SalientConfig(f"filler_{h}", house=h, source="yoga_firing",
                      salience_reference=1.5, ayanamsha_id=AYA)
        for h in range(1, 13) if h != 10
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert all(s.primary_house != 10 for s in out)


def test_all_even_primaries_never_fire_even_when_fully_populated():
    """Every house 1..12 is salient at once; only odd primaries may anchor a
    bhavat_bhavam_amplifier signal."""
    candidates = [
        SalientConfig(f"cfg_{h}", house=h, source="yoga_firing",
                      salience_reference=1.2, ayanamsha_id=AYA)
        for h in range(1, 13)
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out, "sanity: odd primaries with fully populated derived houses should fire"
    assert all(s.primary_house % 2 == 1 for s in out)


# ──────────────────────────────────────────────────────────────────────────────
# Restraint rule 3 — NEVER OUTRANKS THE PRIMARY (code guard, not just the 0.85 prior)
# ──────────────────────────────────────────────────────────────────────────────

def test_amplifier_never_exceeds_primary_even_with_a_much_stronger_occupant():
    """DR-3: '0.85 is a scoring input, not a hard cap' — construct a case
    where a naive prior*occupant formula (ignoring the primary) would exceed
    the primary's own salience, and assert the module's clamp still holds."""
    weak_primary_salience = 0.20
    strong_occupant_salience = 100.0  # deliberately absurd to stress the clamp
    candidates = [
        SalientConfig("weak_primary", house=1, source="yoga_firing",
                       salience_reference=weak_primary_salience, ayanamsha_id=AYA),
        SalientConfig("very_strong_occupant", house=7, source="yoga_firing",
                       salience_reference=strong_occupant_salience, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    fired = [s for s in out if s.primary_identifier == "weak_primary"]
    assert fired
    for sig in fired:
        assert sig.computed_salience < weak_primary_salience, (
            "restraint violation: amplifier outranked its (weak) primary"
        )


def test_clamp_below_primary_is_always_strictly_less():
    # raw below primary: clamp is a no-op (still strictly less by construction)
    assert _clamp_below_primary(0.5, 1.0) < 1.0
    # raw far above primary: must still clamp below
    assert _clamp_below_primary(1000.0, 1.0) < 1.0
    # near-zero primary: degenerate branch must not return 0 or negative, and
    # must still stay below the primary
    clamped = _clamp_below_primary(5.0, 0.0000001)
    assert 0.0 <= clamped < 0.0000001


def test_every_emitted_signal_respects_the_outrank_guard_under_randomized_inputs():
    import random
    random.seed(1234)
    candidates = []
    for h in range(1, 13):
        candidates.append(SalientConfig(
            f"rand_{h}", house=h, source="yoga_firing",
            salience_reference=random.uniform(0.01, 5.0), ayanamsha_id=AYA,
        ))
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out
    for sig in out:
        assert sig.computed_salience < sig.primary_salience


# ──────────────────────────────────────────────────────────────────────────────
# Restraint rule 4 — NO CHAINING
# ──────────────────────────────────────────────────────────────────────────────

def test_a_prior_amplifier_signal_is_never_reused_as_a_primary_or_occupant():
    """A candidate list that (incorrectly) includes a previously-emitted
    bhavat_bhavam_amplifier row must have that row excluded from consideration
    entirely — it can neither anchor a new primary nor satisfy a derived-house
    occupant check."""
    candidates = [
        # H9 primary, corroborated once via H11
        SalientConfig("dhana_yoga_2_5_9_11", house=9, source="yoga_firing",
                       salience_reference=1.0218, ayanamsha_id=AYA),
        SalientConfig("anapha", house=11, source="yoga_firing",
                       salience_reference=1.0101, ayanamsha_id=AYA),
        # A (hypothetical) prior amplifier row sitting in H5 (also a derived
        # house of H9) — must NOT be treated as a salient occupant, and must
        # not itself anchor a second-order amplifier via H5's own derived
        # houses {3, 9}.
        SalientConfig("prior_amplifier_in_h5", house=5, source="msr_tier",
                       salience_reference=5.0, ayanamsha_id=AYA,
                       signal_type_class="bhavat_bhavam_amplifier"),
        SalientConfig("some_config_in_h3", house=3, source="yoga_firing",
                       salience_reference=1.1, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    # The chained path (H5 amplifier -> derived H3/H9) must never appear.
    assert all(s.primary_identifier != "prior_amplifier_in_h5" for s in out)
    assert all(s.occupant_identifier != "prior_amplifier_in_h5" for s in out)
    # The legitimate H9->H11 corroboration must still fire.
    assert any(s.primary_identifier == "dhana_yoga_2_5_9_11" and s.derived_house == 11 for s in out)


def test_msr_tier_source_only_counts_as_salient_when_not_the_amplifier_class():
    candidates = [
        SalientConfig("primary_in_h1", house=1, source="yoga_firing",
                       salience_reference=1.0, ayanamsha_id=AYA),
        SalientConfig("amplifier_in_h7", house=7, source="msr_tier",
                       salience_reference=1.0, ayanamsha_id=AYA,
                       signal_type_class="bhavat_bhavam_amplifier"),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out == []  # H1's derived houses are {1, 7}; the only H7 occupant is excluded by no-chaining
