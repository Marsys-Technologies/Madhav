"""
Tests for canonical Parāśari aspect authority (BPHS Ch.26).

BPHS graha-drishti: Rahu and Ketu cast the same special aspects as Jupiter
(5th/7th/9th), NOT only the default 7th. These tests cover:
  1. The canonical immutable API in brahmagyan/aspects.py.
  2. The primitives.py SPECIAL_DRISHTI_DEG fix (gochara grammar).
  3. The ga_yoga_writer.py canonical-oracle consumer.
  4. The golden case: Ketu in Leo casts 5th aspect onto Sagittarius.
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


# ── 2. primitives.py SPECIAL_DRISHTI_DEG ────────────────────────────────────

def test_primitives_nodal_drishti_rahu_has_explicit_entry():
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert "Rahu" in SPECIAL_DRISHTI_DEG, (
        "Rahu must have an explicit entry in SPECIAL_DRISHTI_DEG "
        "(not fall through to _DEFAULT_DRISHTI_DEG)"
    )


def test_primitives_nodal_drishti_ketu_has_explicit_entry():
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert "Ketu" in SPECIAL_DRISHTI_DEG, (
        "Ketu must have an explicit entry in SPECIAL_DRISHTI_DEG "
        "(not fall through to _DEFAULT_DRISHTI_DEG)"
    )


def test_primitives_nodal_drishti_5th_aspect_120deg():
    """5th aspect = 120° forward (4 signs × 30°).  Both nodes must carry it."""
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert 120.0 in SPECIAL_DRISHTI_DEG["Rahu"], "Rahu must cast 5th (120°) aspect"
    assert 120.0 in SPECIAL_DRISHTI_DEG["Ketu"], "Ketu must cast 5th (120°) aspect"


def test_primitives_nodal_drishti_7th_aspect_180deg():
    """7th aspect = 180°. Both nodes must carry it."""
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert 180.0 in SPECIAL_DRISHTI_DEG["Rahu"], "Rahu must cast 7th (180°) aspect"
    assert 180.0 in SPECIAL_DRISHTI_DEG["Ketu"], "Ketu must cast 7th (180°) aspect"


def test_primitives_nodal_drishti_9th_aspect_240deg():
    """9th aspect = 240°. Both nodes must carry it."""
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    assert 240.0 in SPECIAL_DRISHTI_DEG["Rahu"], "Rahu must cast 9th (240°) aspect"
    assert 240.0 in SPECIAL_DRISHTI_DEG["Ketu"], "Ketu must cast 9th (240°) aspect"


def test_primitives_nodal_drishti_matches_jupiter():
    """Nodes must carry exactly the same degree set as Jupiter (5th/7th/9th)."""
    from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG
    jupiter_degs = set(SPECIAL_DRISHTI_DEG["Jupiter"])
    assert set(SPECIAL_DRISHTI_DEG["Rahu"]) == jupiter_degs
    assert set(SPECIAL_DRISHTI_DEG["Ketu"]) == jupiter_degs


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


# ── 4. Golden case: Ketu in Leo casts 5th aspect onto Sagittarius ───────────

def test_golden_ketu_in_leo_casts_5th_onto_sagittarius():
    """
    BPHS golden case: Ketu occupying Leo (sign index 4, 0-based) casts its
    5th-house special aspect onto the 5th sign forward = Sagittarius (sign
    index 8).

    Before fix: SPECIAL_DRISHTI_DEG.get('Ketu', _DEFAULT_DRISHTI_DEG) returns
    [180.0] only — Sagittarius is NOT in the aspecting-signs list for Ketu.
    After fix: [120.0, 180.0, 240.0] — 120° offset = 4 signs forward = Sag.

    This test uses _signs_casting_drishti_onto directly (the inverse mapping):
    given target=Sagittarius and planet=Ketu, the function must return a list
    that INCLUDES Leo (Ketu at 120° behind Sagittarius casts 5th onto it).
    """
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto

    aspecting_signs = _signs_casting_drishti_onto("Sagittarius", "Ketu")
    assert "Leo" in aspecting_signs, (
        f"Ketu in Leo must cast 5th aspect onto Sagittarius. "
        f"_signs_casting_drishti_onto('Sagittarius', 'Ketu') = {aspecting_signs!r}; "
        f"'Leo' not found — Ketu is missing 5th-aspect entry in SPECIAL_DRISHTI_DEG."
    )


def test_golden_rahu_in_leo_casts_5th_onto_sagittarius():
    """Same golden case for Rahu (symmetric with Ketu per BPHS)."""
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto

    aspecting_signs = _signs_casting_drishti_onto("Sagittarius", "Rahu")
    assert "Leo" in aspecting_signs, (
        f"Rahu in Leo must cast 5th aspect onto Sagittarius. "
        f"_signs_casting_drishti_onto('Sagittarius', 'Rahu') = {aspecting_signs!r}; "
        f"'Leo' not found."
    )


def test_golden_ketu_in_leo_casts_9th_onto_aries():
    """
    Ketu in Leo (sign idx 4) casting 9th aspect = 8 signs forward → Aries
    (sign idx (4+8) % 12 = 0). Inverse: Ketu must be 4 signs BEFORE Aries
    from the backward direction, i.e. in Leo.
    """
    from services.gochara_grammar.primitives import _signs_casting_drishti_onto

    aspecting_signs = _signs_casting_drishti_onto("Aries", "Ketu")
    assert "Leo" in aspecting_signs, (
        f"Ketu in Leo must cast 9th aspect onto Aries. "
        f"_signs_casting_drishti_onto('Aries', 'Ketu') = {aspecting_signs!r}"
    )
