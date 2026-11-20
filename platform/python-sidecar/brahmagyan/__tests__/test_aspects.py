"""
Tests for canonical Parāśari aspect authority (BPHS Ch.26).

The natal Parāśari API and yoga writer admit 5th/7th/9th nodal aspects.
Kāla gochara uses its own ratified convention (N-14): neither node casts
transit dṛṣṭi. Keep both assertions so one scope cannot override the other.
"""
from __future__ import annotations


# ── 1. Canonical shared constant ────────────────────────────────────────────

def test_node_parashari_aspects_constant():
    from brahmagyan.aspects import NODE_PARASHARI_ASPECTS
    assert NODE_PARASHARI_ASPECTS == {5: 1.0, 7: 1.0, 9: 1.0}


def test_canonical_aspect_api_normalizes_casing_and_covers_every_profile():
    from brahmagyan.aspects import get_graha_aspects

    assert get_graha_aspects("Sun") == {7: 1.0}
    assert get_graha_aspects("  MARS ") == {4: 1.0, 7: 1.0, 8: 1.0}
    assert get_graha_aspects("jUpItEr") == {5: 1.0, 7: 1.0, 9: 1.0}
    assert get_graha_aspects("SATURN") == {3: 1.0, 7: 1.0, 10: 1.0}
    assert get_graha_aspects("rahu") == {5: 1.0, 7: 1.0, 9: 1.0}
    assert get_graha_aspects("KETU") == {5: 1.0, 7: 1.0, 9: 1.0}


def test_canonical_aspect_api_is_immutable_and_invalid_inputs_are_universal_only():
    from brahmagyan.aspects import get_graha_aspects

    unknown = get_graha_aspects("not-a-graha")
    assert unknown == {7: 1.0}
    assert get_graha_aspects(None) is unknown
    try:
        unknown[4] = 1.0  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError("canonical aspect profiles must be immutable")


# ── 2. Kāla transit convention (N-14) ────────────────────────────────────

def test_transit_nodes_explicitly_cast_no_drishti():
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG

    # An absent key would fall through to the default seventh aspect.
    assert SPECIAL_DRISHTI_DEG["Rahu"] == []
    assert SPECIAL_DRISHTI_DEG["Ketu"] == []
    assert SPECIAL_DRISHTI_DEG["Jupiter"] == [120.0, 180.0, 240.0]


def test_transit_inverse_drishti_applies_no_nodal_aspects():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto

    for target in ("Sagittarius", "Aquarius", "Aries"):
        assert _signs_casting_drishti_onto(target, "Rahu") == []
        assert _signs_casting_drishti_onto(target, "Ketu") == []
        assert "Leo" in _signs_casting_drishti_onto(target, "Jupiter")


# ── 3. ga_yoga_writer.py canonical-oracle consumer ─────────────────────────

def test_yoga_writer_nodal_drishti_correct_houses():
    from ga_writers.ga_yoga_writer import _nb_aspects_house
    assert _nb_aspects_house("Rahu", 1, 5)
    assert _nb_aspects_house("ketu", 1, 9)


def test_yoga_writer_nodal_drishti_matches_jupiter():
    """Nodes must reach the same special offsets as Jupiter."""
    from ga_writers.ga_yoga_writer import _nb_aspects_house
    for target_house in (5, 7, 9):
        assert _nb_aspects_house("rahu", 1, target_house)
        assert _nb_aspects_house("ketu", 1, target_house)
        assert _nb_aspects_house("jupiter", 1, target_house)
