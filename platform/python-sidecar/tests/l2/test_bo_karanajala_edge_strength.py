"""
Tests for bo_karanajala's DR-7 (DIS.020) edge_strength_v1 formula.

edge_strength = base_relation_weight × valence_factor × ratification_factor
                × consistency_weight, clamped [0.1, 2.0].
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    ViharaLookups,
    EDGE_STRENGTH_FORMULA_VERSION,
    _edge_strength_v1,
    _clamp_edge_strength,
    _vichara_code,
    _occupied_house_by_graha,
)


def _lookups(valence=None, consistency=None, ratification=None, occupied=None):
    """Build a ViharaLookups without touching the DB (bypass __init__)."""
    lk = object.__new__(ViharaLookups)
    lk.valence_by_actor_house = valence or {}
    lk.consistency_by_subject = consistency or {}
    lk.ratification_by_subject_domain = ratification or {}
    lk.occupied_house_by_graha = occupied or {}
    return lk


def test_vichara_code_roundtrip():
    assert _vichara_code("Mars") == "MAR"
    assert _vichara_code("Sun") == "SUN"
    assert _vichara_code("Rahu") == "RAH_MEAN"
    assert _vichara_code("NotAGraha") is None


def test_no_graha_returns_clamped_base_and_no_constituents():
    strength, ids = _edge_strength_v1(0.6, None, None, _lookups())
    assert strength == 0.6
    assert ids == []


def test_no_lookups_returns_clamped_base():
    strength, ids = _edge_strength_v1(0.6, "Mars", None, None)
    assert strength == 0.6
    assert ids == []


def test_strong_benefic_valence_amplifies():
    lk = _lookups(
        valence={("MAR", 7): ("strong_benefic", "v1")},
        occupied={"Mars": 7},
    )
    strength, ids = _edge_strength_v1(0.6, "Mars", None, lk)
    # 0.6 * 1.25 (strong_benefic) * 1.0 * 1.0 = 0.75
    assert strength == pytest.approx(0.75)
    assert ids == ["v1"]


def test_ratification_factor_only_applied_when_domain_tagged():
    lk = _lookups(
        ratification={("MAR", "wealth"): (1.4, "r1")},
        occupied={"Mars": 1},
    )
    # No domains -> ratification_factor stays 1.0
    no_domain_strength, _ = _edge_strength_v1(0.6, "Mars", None, lk)
    assert no_domain_strength == pytest.approx(0.6)

    # Domain-tagged -> ratification_factor applied
    domain_strength, ids = _edge_strength_v1(0.6, "Mars", ["wealth"], lk)
    assert domain_strength == pytest.approx(0.6 * 1.4)
    assert "r1" in ids


def test_consistency_weight_dampens_low_consistency():
    lk = _lookups(consistency={"SAT": (0.0, "c1")})
    strength, ids = _edge_strength_v1(1.0, "Saturn", None, lk)
    # 1.0 * 1.0 * 1.0 * (0.75 + 0.25*0) = 0.75
    assert strength == pytest.approx(0.75)
    assert "c1" in ids


def test_consistency_weight_never_zeroes_out():
    lk = _lookups(consistency={"SAT": (0.0, "c1")})
    strength, _ = _edge_strength_v1(0.1, "Saturn", None, lk)
    assert strength > 0.0


def test_full_formula_composes_all_three_terms():
    lk = _lookups(
        valence={("VEN", 2): ("benefic", "vid")},
        consistency={"VEN": (1.0, "cid")},
        ratification={("VEN", "wealth"): (1.4, "rid")},
        occupied={"Venus": 2},
    )
    strength, ids = _edge_strength_v1(0.6, "Venus", ["wealth"], lk)
    # 0.6 * 1.10 (benefic) * 1.4 (ratification) * 1.0 (full consistency) = 0.924
    assert strength == pytest.approx(0.924)
    assert set(ids) == {"vid", "rid", "cid"}


def test_clamp_bounds():
    assert _clamp_edge_strength(5.0) == 2.0
    assert _clamp_edge_strength(-1.0) == 0.1
    assert _clamp_edge_strength(1.0) == 1.0


def test_anti_vacuous_non_degenerate_distribution():
    """§F1.7(5): edge-strength values must show a real, non-constant
    distribution — not a synthetic placeholder. Verifies the formula produces
    DIFFERENT strengths for graha with different valence/consistency/
    ratification profiles, not one constant value."""
    lk = _lookups(
        valence={("MAR", 1): ("strong_malefic", "v1"), ("VEN", 2): ("benefic", "v2")},
        consistency={"MAR": (0.2, "c1"), "VEN": (0.9, "c2")},
        occupied={"Mars": 1, "Venus": 2},
    )
    s_mars, _ = _edge_strength_v1(0.6, "Mars", None, lk)
    s_venus, _ = _edge_strength_v1(0.6, "Venus", None, lk)
    assert s_mars != s_venus


def test_formula_version_constant():
    assert EDGE_STRENGTH_FORMULA_VERSION == "edge_strength_v1"


def test_occupied_house_by_graha_helper():
    facts = [{"graha": "Mars", "house": 7, "fact_id": "f1"}, {"graha": "Venus", "house": 2, "fact_id": "f2"}]
    result = _occupied_house_by_graha(facts)
    assert result == {"Mars": 7, "Venus": 2}
