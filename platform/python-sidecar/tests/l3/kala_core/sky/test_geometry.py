"""KA-1e dṛṣṭi geometry: forward count, directed, nodes cast none (N-14)."""
from __future__ import annotations

import pytest

from services.gochara_grammar.primitives import SPECIAL_DRISHTI_DEG as GRAMMAR_TABLE
from services.gochara_kernel.convention import SPECIAL_DRISHTI_DEG as KERNEL_TABLE
from services.kala_core.sky import aspected_points, aspects, contact_level, drishti_angles


def test_forward_count_is_directed() -> None:
    # Saturn at 0° casts its 3rd on 60°; a graha at 60° is not aspected back.
    assert 60.0 in aspects("Saturn", 0.0, 60.0, orb_deg=1.0)
    assert aspects("Saturn", 60.0, 0.0, orb_deg=1.0) == ()
    # Mars at 10° (Aries) aspects 100° (Cancer) by its 4th, never the reverse.
    assert aspects("Mars", 10.0, 100.0, orb_deg=0.0) == (90.0,)
    assert aspects("Mars", 100.0, 10.0, orb_deg=0.0) == ()


def test_aspected_points_and_contact_level_are_inverse() -> None:
    for angle, point in aspected_points("Jupiter", 350.0):
        assert contact_level(point, angle) == pytest.approx(350.0)
    assert dict(aspected_points("Jupiter", 350.0)) == {120.0: 110.0, 180.0: 170.0, 240.0: 230.0}


@pytest.mark.parametrize("node", ["Rahu", "Ketu", "RAH_MEAN", "ketu"])
def test_nodes_cast_none(node: str) -> None:
    assert drishti_angles(node) == ()
    assert aspected_points(node, 0.0) == ()
    for target in (120.0, 180.0, 240.0):          # the legacy 5th / 7th / 9th
        assert aspects(node, 0.0, target, orb_deg=1.0) == ()


def test_grammar_uses_the_kernel_aspect_table() -> None:
    # KR-1 contracts the old disagreement: there is one Kāla table, including
    # the empty node entries, rather than a copied convention that can drift.
    assert GRAMMAR_TABLE is KERNEL_TABLE
    assert {body: tuple(angles) for body, angles in GRAMMAR_TABLE.items()} == {
        body: drishti_angles(body) for body in GRAMMAR_TABLE}


def test_orb_must_be_declared() -> None:
    with pytest.raises(ValueError, match="orb_deg"):
        aspects("Mars", 0.0, 90.0, orb_deg=float("nan"))
