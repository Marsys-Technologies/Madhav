"""Aspect regressions at two separately governed boundaries.

KR-1 rewrites the Kāla grammar's node lock to N-14: no node drishti, including
no seventh. Sections 1 and 3 preserve the existing L0/L1 API/consumer tests;
those assets are outside this campaign and are not changed by this refactor.
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


# ── 2. Kāla grammar uses the kernel's N-14 convention ─────────────────────

def test_primitives_nodal_drishti_rahu_has_explicit_entry():
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert SPECIAL_DRISHTI_DEG["Rahu"] == []


def test_primitives_nodal_drishti_ketu_has_explicit_entry():
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert SPECIAL_DRISHTI_DEG["Ketu"] == []


def test_primitives_nodes_cast_no_5th_aspect():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    for node in ("Rahu", "Ketu"):
        assert "Leo" not in _signs_casting_drishti_onto("Sagittarius", node)


def test_primitives_nodes_cast_no_7th_aspect():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    for node in ("Rahu", "Ketu"):
        assert "Leo" not in _signs_casting_drishti_onto("Aquarius", node)


def test_primitives_nodes_cast_no_9th_aspect():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    for node in ("Rahu", "Ketu"):
        assert "Leo" not in _signs_casting_drishti_onto("Aries", node)


def test_primitives_classical_jupiter_aspects_retained():
    from services.gochara_grammar.primitives import _drishti_house_offsets
    assert _drishti_house_offsets("Jupiter") == [5, 7, 9]


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


# ── 4. Golden Kāla cases under N-14 ───────────────────────────────────────

def test_golden_ketu_in_leo_casts_no_5th_onto_sagittarius():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    assert _signs_casting_drishti_onto("Sagittarius", "Ketu") == []


def test_golden_rahu_in_leo_casts_no_5th_onto_sagittarius():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    assert _signs_casting_drishti_onto("Sagittarius", "Rahu") == []


def test_golden_ketu_in_leo_casts_no_9th_onto_aries():
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto
    assert _signs_casting_drishti_onto("Aries", "Ketu") == []
