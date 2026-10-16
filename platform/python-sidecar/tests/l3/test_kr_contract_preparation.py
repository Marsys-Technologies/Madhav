"""KR-1 preparation that does not depend on unpublished reader mappings.

Reverting the grammar convention restores node casts; reverting the orb rename
restores two unrelated formulas under one public name. Both must fail here.
"""
import importlib.util
from datetime import datetime, timezone

import pytest

from services.gochara_grammar import primitives
from services.gochara_grammar.models import ResonanceTarget


def test_retired_taranga_kernel_is_not_importable():
    # The K6-4 projection integrates the field; the unused harmonic-mean
    # kernel must not remain as a second waveform API after contraction.
    assert importlib.util.find_spec("services.taranga_kernel") is None


def test_internal_kshetra_vedha_moorti_builders_are_retired():
    from services.ka_kshetra import stage1_symbolization

    assert not hasattr(stage1_symbolization, "build_vedha_primitive")
    assert not hasattr(stage1_symbolization, "build_moorti_primitive")


@pytest.mark.parametrize("quality_tier", [1, 2, 3, 4])
def test_moorti_testimony_keeps_upstream_edges_without_computing_strength(quality_tier):
    from services.ka_kshetra.g1_inputs import suppression_primitives

    prims, gaps = suppression_primitives("chart", datetime(2000, 1, 1, tzinfo=timezone.utc),
        [], [{"graha": "Saturn", "t_in": "2000-01-02T00:00:00+00:00",
              "t_out": "2000-01-04T00:00:00+00:00", "moorti_name": "testimony",
              "quality_tier": quality_tier, "source_ref": "candidate:fixture:moorti:Saturn:1"}], [])
    assert len(prims) == 1
    row = prims[0]
    assert (row.t_start, row.t_end) == (1.0, 3.0)
    assert row.primitive_kind == "moorti_testimony"
    assert row.polarity == "neutral"
    assert row.envelope == [(1.0, 0.0), (3.0, 0.0)]
    assert row.source_table == "kala_moorti_nirnaya_candidate"
    assert row.source_pk == "candidate:fixture:moorti:Saturn:1"
    assert gaps == [{"source_ref": row.source_pk,
                     "reason": "moorti_uncited_legacy_testimony;numeric_bridge_not_admitted"}]


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
@pytest.mark.parametrize("sign", primitives.SIGNS)
def test_nodes_cast_no_whole_sign_drishti(node, sign):
    assert primitives._signs_casting_drishti_onto(sign, node) == []


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
def test_nodes_emit_no_point_drishti(node):
    # No Swiss call is needed: N-14's empty angle set rules out every event.
    target = ResonanceTarget("chart", "career", "karaka", "Sun", 1.0,
                             uncited_extension=True, target_longitude_deg=30.0)
    assert primitives.drishti_contact(None, "chart", target, 2451545.0,
                                     2451546.0, planets=[node]) == []


def test_classical_directed_aspects_survive_node_table_retirement():
    assert primitives._drishti_house_offsets("Jupiter") == [5, 7, 9]
    assert primitives._drishti_house_offsets("Mars") == [4, 7, 8]
    assert primitives._drishti_house_offsets("Saturn") == [3, 7, 10]
    assert primitives._drishti_house_offsets("Sun") == [7]
    assert primitives._signs_casting_drishti_onto("Sagittarius", "Jupiter") == [
        "Leo", "Gemini", "Aries"]


def test_ad_hoc_linear_and_legacy_cosine_orbs_have_distinct_public_names():
    from pipeline import transit_search
    from services.ka_sangam import engine

    # PLAN §8: keep the ad-hoc scanner, distinguish the second (I-17) formula.
    assert hasattr(engine, "cosine_orb_strength_score")
    assert not hasattr(engine, "orb_strength_score")
    assert transit_search.orb_strength_score(0.5, 1.0, "applying") == pytest.approx(0.6)
    assert transit_search.orb_strength_score(0.5, 1.0, "separating") == pytest.approx(0.5)
    assert engine.cosine_orb_strength_score(0.5, 1.0, "applying") == pytest.approx(0.5)
    assert engine.cosine_orb_strength_score(0.5, 1.0, "separating") == pytest.approx(0.35)


def test_live_legacy_importers_use_the_renamed_cosine_formula():
    from services.ka_sangam import engine
    from services.kala_trigger import trigger
    from services import taranga_service

    assert hasattr(engine, "cosine_orb_strength_score")
    assert trigger.cosine_orb_strength_score is engine.cosine_orb_strength_score
    assert taranga_service._orb_strength_score is engine.cosine_orb_strength_score
