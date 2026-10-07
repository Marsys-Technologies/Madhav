"""K0a-1a boundary oracles for the vocabulary defects F-A1 and F-A3."""
from __future__ import annotations

import pytest

from brahmagyan.l0_semantic_release import SEMANTIC_RELEASE
from ga_writers.ga_dashas_writer import SYSTEMS as L1_DASHA_SYSTEMS
from ga_writers.ga_dashas_writer import YOGINI_SEQUENCE as L1_YOGINI_SEQUENCE
from services.kala_core.vocab import (
    DashaSystemId, EVENT_CLASS_IDS, FrameId, FrameKind, GrahaId,
    LordId, LordKind, SignId, YoginiId, YOGINI_GRAHA, event_class_id,
    frame_id, graha_id, graha_node_id, l1_system_id, lord_node_id,
    parse_graha_node, period_lord, route_contains_lord, system_id,
)
from services.gochara_rules.registry import CLASS_BY_NAME


def test_every_released_graha_has_a_canonical_round_trip() -> None:
    for entity in SEMANTIC_RELEASE["entities"]:
        code = entity["canonical_subject_code"]
        assert graha_id(entity["canonical_label"]) is GrahaId(code)
        assert graha_id(code) is GrahaId(code)
    for graha in GrahaId:
        assert graha_id(graha.value) is graha


def test_promise_graph_wire_ids_round_trip_without_collapsing_node_models() -> None:
    for graha in (
        GrahaId.SUN, GrahaId.MOON, GrahaId.MARS, GrahaId.MERCURY,
        GrahaId.JUPITER, GrahaId.VENUS, GrahaId.SATURN,
        GrahaId.RAHU_MEAN, GrahaId.KETU_MEAN,
    ):
        assert parse_graha_node(graha_node_id(graha)) is graha
    assert graha_node_id("Jupiter") == "graha:Ju"
    assert graha_node_id("Jupiter") != "graha:Jupiter"  # hazard.py:277 mutant
    with pytest.raises(ValueError, match="no promise-graph node"):
        graha_node_id(GrahaId.RAHU_TRUE)
    with pytest.raises(ValueError, match="unknown graha node"):
        parse_graha_node("graha:Jupiter")
    with pytest.raises(ValueError):
        graha_id("unrecorded planet")


def test_every_dasha_method_round_trips_without_merging_distinct_methods() -> None:
    for method in DashaSystemId:
        assert system_id(method.value) is method
        if method not in (DashaSystemId.KARAKA_KENDRADI, DashaSystemId.MULA):
            assert system_id(l1_system_id(method)) is method
    assert system_id("chara_karaka") is DashaSystemId.CHARA
    assert l1_system_id(DashaSystemId.CHARA) == "chara_karaka"
    assert DashaSystemId.CHARA is not DashaSystemId.KARAKA_KENDRADI
    for unbuilt in (DashaSystemId.KARAKA_KENDRADI, DashaSystemId.MULA):
        with pytest.raises(ValueError, match="no L1 period producer"):
            l1_system_id(unbuilt)
    with pytest.raises(ValueError):
        system_id("invented_system")


def test_every_l1_produced_system_uses_its_declared_period_identity() -> None:
    assert len(L1_DASHA_SYSTEMS) == len(set(L1_DASHA_SYSTEMS))
    for stored_id in L1_DASHA_SYSTEMS:
        assert l1_system_id(system_id(stored_id)) == stored_id


def test_lord_kind_prevents_the_full_name_clock_mutant_and_wrong_cara_coercion() -> None:
    jupiter = period_lord("vimshottari", "Jupiter")
    assert jupiter == LordId(LordKind.GRAHA, GrahaId.JUPITER)
    assert lord_node_id(jupiter) == "graha:Ju"
    assert route_contains_lord(jupiter, ("graha:Ju", "event_class:career_change"))
    assert not route_contains_lord(jupiter, ("graha:Jupiter",))

    cara = period_lord("chara_karaka", "Aries")
    assert cara == LordId(LordKind.SIGN, SignId.ARIES)
    assert lord_node_id(cara) == "rashi:Aries"
    assert not route_contains_lord(cara, ("graha:Ma",))
    with pytest.raises(ValueError):
        period_lord("chara", "Mars")


@pytest.mark.parametrize("system", ["kalachakra", "narayana"])
def test_l1_sign_periods_keep_sign_lords_out_of_graha_routes(system: str) -> None:
    # ga_dashas_writer stores both systems' period lords as zodiac signs.
    assert l1_system_id(system) == system
    lord = period_lord(system, "Aries")
    assert lord == LordId(LordKind.SIGN, SignId.ARIES)
    assert lord_node_id(lord) == "rashi:Aries"
    assert not route_contains_lord(lord, ("graha:Ma",))
    with pytest.raises(ValueError):
        period_lord(system, "Mars")


def test_all_eight_yogini_names_are_typed_and_map_to_the_l1_graha() -> None:
    expected = (
        GrahaId.MOON, GrahaId.SUN, GrahaId.JUPITER, GrahaId.MARS,
        GrahaId.MERCURY, GrahaId.SATURN, GrahaId.VENUS, GrahaId.RAHU_MEAN,
    )
    assert tuple(YOGINI_GRAHA.values()) == expected
    for deity, graha in zip(YoginiId, expected, strict=True):
        lord = period_lord("yogini", deity.value)
        assert lord == LordId(LordKind.YOGINI, deity)
        assert lord_node_id(lord) == graha_node_id(graha)
    assert period_lord("yogini", "Mangala").value is YoginiId.MANGALA
    assert period_lord("vimshottari", "Mangala").value is GrahaId.MARS


def test_yogini_mapping_matches_the_l1_producer_sequence() -> None:
    assert len(L1_YOGINI_SEQUENCE) == len(YoginiId)
    for name, graha_name, _years in L1_YOGINI_SEQUENCE:
        deity = YoginiId(name)
        lord = period_lord("yogini", name)
        assert lord == LordId(LordKind.YOGINI, deity)
        assert YOGINI_GRAHA[deity] is graha_id(graha_name)
        assert lord_node_id(lord) == graha_node_id(graha_name)


def test_frame_and_event_class_are_closed() -> None:
    for frame in (FrameId(FrameKind.LAGNA), FrameId(FrameKind.MOON),
                  FrameId(FrameKind.ARUDHA), FrameId(FrameKind.GRAHA, GrahaId.MARS)):
        assert frame_id(frame.wire_id) == frame
    assert EVENT_CLASS_IDS == frozenset(CLASS_BY_NAME)
    assert {event_class_id(value) for value in EVENT_CLASS_IDS} == EVENT_CLASS_IDS
    with pytest.raises(ValueError):
        event_class_id("not_a_class")
    with pytest.raises(ValueError):
        FrameId(FrameKind.GRAHA)
    with pytest.raises(ValueError):
        FrameId(FrameKind.MOON, GrahaId.MOON)
