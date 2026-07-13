"""Unit test for the WP-2.5 / LCA-16 L0 organ taxonomy seed (Kalapurusha sign→body-part).

Asserts the L0 seed is present and cited (B.10 — no LLM invention; classical source on
every row).
"""
from brahmagyan.l0_medical import SIGN_MEDICAL


def test_sign_medical_has_all_twelve_signs():
    assert len(SIGN_MEDICAL) == 12
    numbers = sorted(r["sign_number"] for r in SIGN_MEDICAL)
    assert numbers == list(range(1, 13))


def test_every_row_is_cited():
    for r in SIGN_MEDICAL:
        assert r["classical_citation"]
        assert "BPHS" in r["classical_citation"] or "Kalapurusha" in r["classical_citation"]


def test_kalapurusha_head_to_feet_anchors():
    by_name = {r["sign_name"]: r for r in SIGN_MEDICAL}
    assert "head" in by_name["Aries"]["body_part"]
    assert "feet" in by_name["Pisces"]["body_part"]


def test_element_and_dosha_present():
    for r in SIGN_MEDICAL:
        assert r["element"] in ("fire", "earth", "air", "water")
        assert r["dosha"] in ("vata", "pitta", "kapha")
