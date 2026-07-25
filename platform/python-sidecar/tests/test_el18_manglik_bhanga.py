"""
test_el18_manglik_bhanga.py — EL-18 (Elevation Campaign v2.1, Lane β.D2).

Regression guard for the Manglik / Kuja Dosha bhanga (cancellation) wiring.

Root cause this fixes (verified empirically 2026-07-25 against the live
elev/beta code): the generic `_evaluate_catalog_rule` has NO handler for the
`{"houses","planet","reference"}` formation shape that
brahma_dosha_catalog.manglik stores, so manglik failed closed with
`rule_format_unimplemented`, never formed, and the fully-built, BPHS-cited
`_cancel_manglik` cancellation callable (already registered in
DOSHA_CANCELLATIONS since 2026-07-16) was UNREACHABLE dead code. The fix is a
bespoke `_detect_manglik` restoring formation from the catalog's own stored
formation_rule_jsonb.

No live DB required — pure deterministic detector/cancellation logic on
hand-built D1 position dicts. The two canonical charts are exercised with
their real L1 house/sign placements (Abhisek 482012f1, Abhinandan 1c826d5a),
giving opposite, both-grounded outcomes:
  * Abhisek     — Mars in 7th (Libra): Manglik forms, NO cancellation ground
                  → bhanga_active is False (honest "you are Manglik").
  * Abhinandan  — Mars in 12th (Pisces): Manglik forms, cancelled by
                  Jupiter-in-kendra (10th) AND the sign-specific Pisces-in-12th
                  ground → bhanga_active is True.

Every assertion traces to brahma_dosha_catalog.manglik.cancellation_conditions
(BPHS ch.81 tradition) — no fabricated doctrine (B.10).
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_structural_writer import (  # noqa: E402
    BESPOKE_DOSHA_DETECTORS,
    DOSHA_CANCELLATIONS,
    _cancel_manglik,
    _detect_manglik,
    _evaluate_catalog_rule,
)

# Real L1 D1 placements (lahiri_chitrapaksha) for the two canonical charts.
_ABHISEK = {"grahas": [
    {"name": "Mars", "house": 7, "sign": "Libra"},
    {"name": "Moon", "house": 11, "sign": "Aquarius"},
    {"name": "Venus", "house": 9, "sign": "Sagittarius"},
    {"name": "Jupiter", "house": 9, "sign": "Sagittarius"},
    {"name": "Sun", "house": 10, "sign": "Capricorn"},
]}
_ABHINANDAN = {"grahas": [
    {"name": "Mars", "house": 12, "sign": "Pisces"},
    {"name": "Moon", "house": 3, "sign": "Gemini"},
    {"name": "Venus", "house": 12, "sign": "Pisces"},
    {"name": "Jupiter", "house": 10, "sign": "Capricorn"},
    {"name": "Sun", "house": 11, "sign": "Aquarius"},
]}
# Mars in no Manglik house from any reference.
_NO_MANGLIK = {"grahas": [
    {"name": "Mars", "house": 3, "sign": "Gemini"},
    {"name": "Moon", "house": 6, "sign": "Virgo"},
    {"name": "Venus", "house": 5, "sign": "Leo"},
    {"name": "Jupiter", "house": 1, "sign": "Aries"},
]}

# The manglik formation rule EXACTLY as stored in brahma_dosha_catalog.
_MANGLIK_RULE = {"houses": [1, 2, 4, 7, 8, 12], "planet": "mars",
                 "reference": ["lagna", "moon", "venus"]}


def test_generic_evaluator_cannot_form_manglik_documents_the_gap():
    """The root cause: the generic evaluator does not implement manglik's
    formation shape, so without the bespoke detector the dosha stays dark and
    the cancellation is unreachable. This asserts the gap the fix closes."""
    fires, reason = _evaluate_catalog_rule(_MANGLIK_RULE, _ABHISEK)
    assert fires is False
    assert reason == "rule_format_unimplemented"


def test_manglik_registered_in_both_registries():
    assert BESPOKE_DOSHA_DETECTORS.get("manglik") is _detect_manglik
    assert "manglik" in DOSHA_CANCELLATIONS


def test_detect_manglik_fires_abhisek_from_lagna():
    finding = _detect_manglik(_ABHISEK)
    assert finding is not None
    assert finding["mars_house"] == 7
    assert finding["constituent_planets"] == ["Mars"]
    assert "lagna" in finding["references"]


def test_detect_manglik_fires_abhinandan_multi_reference():
    finding = _detect_manglik(_ABHINANDAN)
    assert finding is not None
    assert finding["mars_house"] == 12
    # Mars is in the 12th from lagna AND the 1st from Venus (Venus in h12).
    assert "lagna" in finding["references"]
    assert any(r.startswith("venus") for r in finding["references"])


def test_detect_manglik_honest_absence():
    assert _detect_manglik(_NO_MANGLIK) is None


def test_cancel_manglik_abhisek_uncancelled():
    """Mars in 7th (Libra): not own/exalt, Jupiter (h9) does not aspect house 7,
    neither Jupiter nor Venus in a kendra, and Libra is not a house-7 sign-
    specific cancellation → Manglik stands uncancelled (an honest, cited
    verdict, not a silent omission)."""
    finding = _detect_manglik(_ABHISEK)
    verdict = _cancel_manglik(finding, _ABHISEK, None, "chart_a", "lahiri_chitrapaksha")
    assert verdict["bhanga_active"] is False
    assert verdict["bhanga_rule_fired"] is None
    assert verdict["citation_ref"] == "bphs:manglik:own_exalt_or_jupiter_aspect_or_sign_specific_cancels"


def test_cancel_manglik_abhinandan_cancelled_with_grounds():
    """Mars in 12th (Pisces): Jupiter in the 10th (a kendra) AND Mars in Pisces
    in the 12th (the classical sign-specific ground) → cancelled, both grounds
    cited to BPHS ch.81 via brahma_dosha_catalog.manglik."""
    finding = _detect_manglik(_ABHINANDAN)
    verdict = _cancel_manglik(finding, _ABHINANDAN, None, "chart_b", "lahiri_chitrapaksha")
    assert verdict["bhanga_active"] is True
    assert "jupiter_in_kendra_h10" in verdict["bhanga_rule_fired"]
    assert "sign_specific_cancel:mars_h12_Pisces" in verdict["bhanga_rule_fired"]
    assert "BPHS ch.81" in verdict["citation_human"]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
