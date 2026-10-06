"""Golden-value narration fidelity tests for bo_pratijna (bo_pratijna_v4_engine).

Covers the three ledger strings the engine composes: DignityResult.detail
(factor_ledger[*].detail), DenialResult.reason (denials[*].reason) and
DusthanaConnection.reason (factor_ledger[*].connections[*].reason). Every
expected sentence is stated by hand from the f-string templates.
"""
from __future__ import annotations

from fractions import Fraction
from types import SimpleNamespace

from pipeline.orchestrator.writers import bo_pratijna_v4_engine as E


def test_pratijna_factor_ledger_detail_golden():
    ref = {"Mars": {"exaltation_sign": 10, "debilitation_sign": 4, "own_signs": [1, 8]}}
    # Mars in Gemini (sign 3, lord Mercury). Mars->Mercury is a natural enemy.
    # Mercury (D1 house 7) sits 3rd from Mars (D1 house 5): a temporary friend.
    # enemy + friend compounds to neutral.
    result = E.dignity_of_with_positions(
        "Mars", 3, 5, {"Mars": 5, "Mercury": 7}, ref,
    )
    detail = result.detail
    assert detail == (
        "naisargika(Mars->Mercury)=enemy, tatkalika(lord_house=7,graha_house=5)=friend "
        "-> panchadha=neutral"
    )


def test_pratijna_denials_reason_golden():
    karyatva = SimpleNamespace(primary_bhava=(7,), karaka_grahas=("Venus",))
    dignities = {
        ("house_lord", "7"): E.DignityResult("Jupiter", 9, "own", 0.8, "x"),
        ("karaka", "Venus"): E.DignityResult("Venus", 2, "friend", 0.6, "y"),
    }
    not_debilitated = E.check_denial_cfg1(karyatva, [], dignities, 1, 4, {})

    # Core house 7: houses 6 and 8 flank it. Saturn sits in 6, Mars in 8, no benefic anywhere.
    ref = {"Saturn": {"natural_benefic": False}, "Mars": {"natural_benefic": False}}
    weights = [E.SlotWeight("house_lord", "7", Fraction(35, 100))]
    hemmed = E.check_denial_cfg3(
        SimpleNamespace(), weights, 7, 2, {6: ["Saturn"], 8: ["Mars"]}, ref,
    )
    one_sided = E.check_denial_cfg3(
        SimpleNamespace(), weights, 7, 2, {6: ["Saturn"], 8: []}, ref,
    )
    assert [not_debilitated.reason, hemmed.reason, one_sided.reason] == [
        "house_lord=own, karaka=friend — not both debilitated",
        "houses 6 and 8 (adjoining core house 7) both malefic-occupied, no benefic reach — pāpakartarī",
        "house 6 malefic-occupied=True, house 8 malefic-occupied=False — hemming test fails",
    ]


def test_pratijna_connections_reason_golden():
    # (a) Venus, the core (7th) lord, sits in the 6th house itself.
    placed = E.dusthana_connection(6, 7, "Venus", 6, 2, "Mercury", 10, 3)
    # (b) Mars, lord of the 8th, sits in house 1: its 7th-house reach lands on core house 7.
    contact = E.dusthana_connection(8, 7, "Venus", 2, 2, "Mars", 1, 1)
    # (c) Mercury (lord of 8th) at house 10 and Venus (core lord, house 2) have no link.
    none = E.dusthana_connection(8, 7, "Venus", 2, 2, "Mercury", 10, 3)
    reasons = [placed.reason, contact.reason, none.reason]
    assert reasons == [
        "Venus (core lord) placed in house 6",
        "Mars (lord of 8) full-contacts core house 7",
        "no lord-in-house/full-contact/parivartana connection to house 8",
    ]
