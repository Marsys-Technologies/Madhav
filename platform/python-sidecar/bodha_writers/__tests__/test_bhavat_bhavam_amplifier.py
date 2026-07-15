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
    to_msr_row,
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


# ──────────────────────────────────────────────────────────────────────────────
# CR-97 Bug-2 fix — BOUNDED EMISSION (no unbounded N×M cross-join)
# ──────────────────────────────────────────────────────────────────────────────

def test_emission_is_bounded_not_cross_product_with_many_duplicate_candidates():
    """Reproduces the real-chart scale defect: dozens of near-duplicate
    already-salient candidates piled into a single (primary_house,
    derived_house) pair. The old implementation emitted one row per
    (primary, occupant) pair — N x M. The fix must emit exactly ONE row for
    this (H9, H11) relationship, not N x M."""
    n_primaries = 40
    m_occupants = 40
    candidates = [
        SalientConfig(f"primary_{i}", house=9, source="yoga_firing",
                      salience_reference=1.0 + (i * 0.001), ayanamsha_id=AYA)
        for i in range(n_primaries)
    ] + [
        SalientConfig(f"occupant_{j}", house=11, source="yoga_firing",
                      salience_reference=1.0 + (j * 0.001), ayanamsha_id=AYA)
        for j in range(m_occupants)
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    h9_to_h11 = [s for s in out if s.primary_house == 9 and s.derived_house == 11]
    assert len(h9_to_h11) == 1, (
        f"expected exactly 1 bounded amplifier row for (H9, H11), got {len(h9_to_h11)} "
        f"(N*M would have been {n_primaries * m_occupants})"
    )
    # The representative chosen must be the highest-salience candidate in each house.
    assert h9_to_h11[0].primary_identifier == f"primary_{n_primaries - 1}"
    assert h9_to_h11[0].occupant_identifier == f"occupant_{m_occupants - 1}"


def test_total_emission_bounded_across_full_chart_scale_candidate_pool():
    """A realistic full-chart-scale pool (~60 candidates per house, matching
    the live 482012f1 rebuild finding) across all 12 houses must still emit
    at most one row per (primary_house, derived_house) pair — at most 12
    rows total (6 odd houses x up to 2 derived houses each), never
    thousands."""
    import random
    random.seed(99)
    candidates = []
    for h in range(1, 13):
        for i in range(60):
            candidates.append(SalientConfig(
                f"h{h}_cfg_{i}", house=h, source="yoga_firing",
                salience_reference=random.uniform(0.01, 5.0), ayanamsha_id=AYA,
            ))
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out, "sanity: a fully populated chart-scale pool should still fire"
    assert len(out) <= 12, f"expected <=12 bounded rows, got {len(out)}"
    # No duplicate (primary_house, derived_house) pairs.
    pairs = [(s.primary_house, s.derived_house) for s in out]
    assert len(pairs) == len(set(pairs))


# ──────────────────────────────────────────────────────────────────────────────
# CR-97 Bug-1 fix — constituent_facts_array / constituent_signals_array never None
# ──────────────────────────────────────────────────────────────────────────────

def test_to_msr_row_never_has_null_constituent_facts_array():
    """bodha_msr_signals.constituent_facts_array is NOT NULL — the emitted row
    dict must never carry None there (or in constituent_signals_array, its
    L2-over-L2 counterpart)."""
    candidates = [
        SalientConfig("dhana_yoga_2_5_9_11", house=9, source="yoga_firing",
                       salience_reference=1.0218, ayanamsha_id=AYA,
                       constituent_facts=("fact_a", "fact_b")),
        SalientConfig("anapha", house=11, source="yoga_firing",
                       salience_reference=1.0101, ayanamsha_id=AYA,
                       constituent_facts=("fact_c",)),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out
    for sig in out:
        row = to_msr_row(sig, chart_id="482012f1-710e-4a25-994a-93821f5871aa",
                          build_id="test-build", now="2026-07-16T00:00:00Z")
        assert row["constituent_facts_array"] is not None
        assert isinstance(row["constituent_facts_array"], list)
        assert row["constituent_signals_array"] is not None
        assert isinstance(row["constituent_signals_array"], list)
    # The real fact lineage from both legs must be present (deduped union).
    fired = [s for s in out if s.derived_house == 11]
    assert fired
    row = to_msr_row(fired[0], chart_id="x", build_id="b", now="n")
    assert set(row["constituent_facts_array"]) == {"fact_a", "fact_b", "fact_c"}


def test_to_msr_row_constituent_facts_array_is_empty_list_not_none_when_no_lineage():
    """A candidate with no constituent_facts at all (the SalientConfig default)
    must still yield [] — never None — since the DB column is NOT NULL."""
    candidates = [
        SalientConfig("primary_no_lineage", house=1, source="yoga_firing",
                       salience_reference=1.5, ayanamsha_id=AYA),
        SalientConfig("occupant_no_lineage", house=7, source="yoga_firing",
                       salience_reference=1.2, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    assert out
    row = to_msr_row(out[0], chart_id="x", build_id="b", now="n")
    assert row["constituent_facts_array"] == []
    assert row["constituent_signals_array"] == []


def test_constituent_signals_array_carries_msr_tier_signal_ids():
    """An msr_tier-sourced primary/occupant's own signal_id must land in
    constituent_signals_array (the L2-over-L2 lineage field) — yoga_firing
    candidates contribute nothing there (no MSR row to reference)."""
    candidates = [
        SalientConfig("primary_msr", house=9, source="msr_tier",
                       salience_reference=1.5, ayanamsha_id=AYA,
                       signal_id="11111111-1111-1111-1111-111111111111"),
        SalientConfig("occupant_yoga", house=11, source="yoga_firing",
                       salience_reference=1.0, ayanamsha_id=AYA),
    ]
    out = compute_bhavat_bhavam_amplifiers(candidates)
    fired = [s for s in out if s.derived_house == 11]
    assert fired
    assert "11111111-1111-1111-1111-111111111111" in fired[0].constituent_signals_array
    row = to_msr_row(fired[0], chart_id="x", build_id="b", now="n")
    assert "11111111-1111-1111-1111-111111111111" in row["constituent_signals_array"]
