"""
Tests for B-02 nodal aspects (BPHS Ch.26 Rahu/Ketu graha-drishti).

BPHS graha-drishti: Rahu and Ketu cast the same special aspects as Jupiter
(5th/7th/9th), NOT only the default 7th. These tests cover:
  1. The canonical shared constant in brahmagyan/aspects.py.
  2. The primitives.py SPECIAL_DRISHTI_DEG fix (gochara grammar).
  3. The ga_yoga_writer.py NB_GRAHA_DRISHTI fix.
  4. The golden case: Ketu in Leo casts 5th aspect onto Sagittarius.
"""
from __future__ import annotations


# ── 1. Canonical shared constant ────────────────────────────────────────────

def test_node_parashari_aspects_constant():
    from brahmagyan.aspects import NODE_PARASHARI_ASPECTS
    assert NODE_PARASHARI_ASPECTS == {5: 1.0, 7: 1.0, 9: 1.0}


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


# ── 3. ga_yoga_writer.py NB_GRAHA_DRISHTI ───────────────────────────────────

def test_yoga_writer_nodal_drishti_rahu_explicit():
    from ga_writers.ga_yoga_writer import NB_GRAHA_DRISHTI
    assert "rahu" in NB_GRAHA_DRISHTI, (
        "rahu must have an explicit entry in NB_GRAHA_DRISHTI"
    )


def test_yoga_writer_nodal_drishti_ketu_explicit():
    from ga_writers.ga_yoga_writer import NB_GRAHA_DRISHTI
    assert "ketu" in NB_GRAHA_DRISHTI, (
        "ketu must have an explicit entry in NB_GRAHA_DRISHTI"
    )


def test_yoga_writer_nodal_drishti_correct_houses():
    from ga_writers.ga_yoga_writer import NB_GRAHA_DRISHTI
    assert NB_GRAHA_DRISHTI["rahu"] == frozenset({5, 7, 9})
    assert NB_GRAHA_DRISHTI["ketu"] == frozenset({5, 7, 9})


def test_yoga_writer_nodal_drishti_matches_jupiter():
    """Nodes must have same house set as jupiter."""
    from ga_writers.ga_yoga_writer import NB_GRAHA_DRISHTI
    assert NB_GRAHA_DRISHTI["rahu"] == NB_GRAHA_DRISHTI["jupiter"]
    assert NB_GRAHA_DRISHTI["ketu"] == NB_GRAHA_DRISHTI["jupiter"]


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
