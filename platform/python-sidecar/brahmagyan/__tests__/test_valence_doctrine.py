"""
Tests for the shared valence doctrine module (DR-9 / DIS.022, VAL-ROOT fix).

The DR-9 anti-overcorrection specimen gate is mandatory and runs in BOTH
directions: all-benefic was the bug; all-adverse (or any single-value collapse)
is the same bug with a different constant. These tests ARE that gate, as pure
unit assertions against the doctrine module (the live-chart re-verification runs
post-rebuild).
"""
from __future__ import annotations

import brahmagyan.valence_doctrine as vd


# ── DR-9 mandatory specimens — graha_valence (BOTH directions) ──────────────

def test_specimen_rahu_in_h2_exalted_is_mixed_not_strongly_adverse():
    """Rahu-in-H2 (Taurus, exalted, Rohini) → mixed/adverse-leaning, NOT purely
    adverse. Exalted Rahu in the dhana bhāva is classically dual: unconventional
    gains AND deception/loss exposure. If this emits pure/strong adverse, the fix
    overcorrected."""
    v = vd.graha_valence("RAH_MEAN", contact_type="occupancy", target_house=2,
                         functional_class=None, dignity_state="exalted")
    assert v.valence == vd.MIXED, v
    assert v.is_mixed
    # adverse-leaning but genuinely dual — a real benefic component from exaltation.
    assert v.benefic_component >= 0.4, v
    assert v.malefic_component >= 0.4, v
    assert v.value_num < 0, v  # leans adverse
    # NOT strongly adverse: a purely-malefic reading (benefic_component ~0) is the overcorrection.
    assert v.benefic_component > 0.0


def test_specimen_mars_8th_aspect_on_h2_is_mixed_adverse():
    """Mars-8th-aspect-on-H2 → mixed/adverse. Natural malefic casting its harsh
    8th special aspect onto the wealth house, BUT Mars is Aries's lagneśa
    (functional benefic) — pure-adverse would ignore functional lordship."""
    v = vd.graha_valence("MAR", contact_type="aspect", target_house=2,
                         functional_class="yogakaraka", aspect_offset=8)
    assert v.valence == vd.MIXED, v
    assert v.malefic_component >= 0.4, v   # the harsh-aspect adverse component is real
    assert v.benefic_component >= 0.4, v   # functional lagneśa acknowledged, not ignored
    assert v.value_num <= 0.1, v           # adverse-leaning (or balanced), never clearly benefic


def test_specimen_jupiter_in_h9_remains_supportive():
    """Venus+Jupiter-in-H9 (the Dhana yoga) MUST remain supportive. Any
    regression here fails the fix."""
    jup = vd.graha_valence("JUP", contact_type="occupancy", target_house=9,
                           functional_class="temporal_benefic", dignity_state="own")
    ven = vd.graha_valence("VEN", contact_type="occupancy", target_house=9,
                           functional_class="temporal_benefic", dignity_state="neutral")
    assert jup.valence == vd.BENEFIC, jup
    assert ven.valence == vd.BENEFIC, ven
    assert jup.malefic_component == 0.0
    assert ven.malefic_component == 0.0


# ── DR-9 mandatory specimens — edge_valence / mechanisms (BOTH directions) ──

def test_specimen_mars_saturn_mechanism_is_adverse():
    """Mars↔Saturn mechanism → adverse. Two natural malefics in a hard mutual
    aspect: adverse texture regardless of Mars being Aries's lagneśa (functional
    lordship governs a graha's own house-results, not the affliction texture of
    a malefic↔malefic relationship)."""
    ev = vd.edge_valence("MAR", "SAT", relationship_type="aspect",
                         functional_a="yogakaraka", functional_b="temporal_malefic")
    assert ev == vd.ANTAGONISTIC, ev
    assert vd.mechanism_valence_from_edges([ev]) == vd.MALEFIC


def test_specimen_jupiter_venus_mechanism_is_supportive():
    """Jupiter↔Venus mechanism → supportive."""
    ev = vd.edge_valence("JUP", "VEN", relationship_type="aspect",
                         functional_a="temporal_benefic", functional_b="temporal_benefic")
    assert ev == vd.HARMONIOUS, ev
    assert vd.mechanism_valence_from_edges([ev]) == vd.BENEFIC


def test_benefic_malefic_edge_is_mixed():
    """A clearly-benefic ↔ clearly-malefic relationship is genuinely MIXED, not
    collapsed to neutral (the old _mechanism_valence lost this)."""
    ev = vd.edge_valence("JUP", "SAT", relationship_type="aspect",
                         functional_a="temporal_benefic", functional_b="temporal_malefic")
    assert ev == vd.EDGE_MIXED, ev
    assert vd.mechanism_valence_from_edges([ev]) == vd.MIXED
    # co-present harmonious + antagonistic edges also → mixed
    assert vd.mechanism_valence_from_edges([vd.HARMONIOUS, vd.ANTAGONISTIC]) == vd.MIXED


# ── Distribution sanity: the vocabulary must genuinely spread ────────────────

def test_distribution_is_not_single_valued():
    """All-benefic was the bug; all-adverse is the same bug with a different
    constant. A representative sweep must touch ≥3 of the 4 vocabulary values."""
    cases = [
        vd.graha_valence("JUP", contact_type="occupancy", target_house=9,
                         functional_class="temporal_benefic", dignity_state="own").valence,
        vd.graha_valence("SAT", contact_type="occupancy", target_house=2,
                         functional_class="temporal_malefic", dignity_state="neutral").valence,
        vd.graha_valence("RAH_MEAN", contact_type="occupancy", target_house=2,
                         functional_class=None, dignity_state="exalted").valence,
        vd.graha_valence("MER", contact_type="occupancy", target_house=10,
                         functional_class="temporal_malefic", dignity_state="neutral").valence,
    ]
    assert len(set(cases)) >= 3, cases


def test_pure_malefic_no_mitigation_is_malefic():
    """Saturn (natural malefic) as a temporal malefic occupying the dhana house
    with no dignity mitigation → clearly malefic (the previously-impossible
    output)."""
    v = vd.graha_valence("SAT", contact_type="occupancy", target_house=2,
                         functional_class="temporal_malefic", dignity_state="neutral")
    assert v.valence == vd.MALEFIC, v
    assert v.benefic_component == 0.0


def test_structural_edge_types_stay_neutral():
    """Topology edge types (lordship/occupancy/yoga_member/bhava_aspect) carry no
    benefic/malefic polarity — they describe structure, not texture."""
    for rt in ("lordship", "occupancy", "yoga_member", "bhava_aspect"):
        assert vd.edge_valence("MAR", "JUP", relationship_type=rt) == vd.EDGE_NEUTRAL


def test_moon_waxing_conditional_nature():
    """Moon natural nature is conditional on waxing (DR-9 dimension 1)."""
    waxing = vd.graha_valence("MOON", contact_type="occupancy", target_house=4,
                              functional_class="functional_benefic", moon_waxing=True)
    waning = vd.graha_valence("MOON", contact_type="occupancy", target_house=4,
                              functional_class=None, moon_waxing=False)
    assert waxing.natural_score > 0
    assert waning.natural_score < 0


def test_verdict_carries_signed_components_for_partitioned_serve():
    """DR-9 Part B needs both components exposed so a mixed signal can route into
    the adverse layer on its malefic_component regardless of net sign."""
    v = vd.graha_valence("RAH_MEAN", contact_type="occupancy", target_house=2,
                         dignity_state="exalted")
    assert set(("valence", "value_num", "benefic_component", "malefic_component",
                "is_mixed", "citation", "formula_version")).issubset(vars(v).keys())
    assert v.formula_version == vd.VALENCE_DOCTRINE_VERSION
