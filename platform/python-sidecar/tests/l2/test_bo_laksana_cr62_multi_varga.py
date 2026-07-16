"""
Tests for bo_laksana's CR-62 multi-varga map (D-2 Lane V-4).

wealth uses {D1,D2,D9,D11}; career uses {D1,D9,D10}. A varga-scoped signal's
'wealth'/'career' domain tag is gated by which varga it actually lives in.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_laksana import (
    _apply_cr62_multi_varga_gate,
    _assign_domains,
    CR62_WEALTH_VARGAS,
    CR62_CAREER_VARGAS,
)


def test_wealth_varga_map_matches_cr62():
    assert CR62_WEALTH_VARGAS == frozenset({"D1", "D2", "D9", "D11"})


def test_career_varga_map_matches_cr62():
    assert CR62_CAREER_VARGAS == frozenset({"D1", "D9", "D10"})


def test_d10_signal_drops_wealth_keeps_career():
    out = _apply_cr62_multi_varga_gate(["wealth", "career", "character"], "D10")
    assert "wealth" not in out
    assert "career" in out
    assert "character" in out


def test_d2_signal_keeps_wealth_drops_career():
    out = _apply_cr62_multi_varga_gate(["wealth", "career"], "D2")
    assert "wealth" in out
    assert "career" not in out


def test_d1_signal_keeps_both():
    out = _apply_cr62_multi_varga_gate(["wealth", "career"], "D1")
    assert set(out) == {"wealth", "career"}


def test_varga_agnostic_signal_ungated():
    out = _apply_cr62_multi_varga_gate(["wealth", "career"], None)
    assert set(out) == {"wealth", "career"}


def test_gate_never_empties_domains_entirely():
    # A D2-only signal tagged ONLY 'career' (not in CR62_CAREER_VARGAS for D2)
    # must not become domain-less — falls back to the ungated list (B.10).
    out = _apply_cr62_multi_varga_gate(["career"], "D2")
    assert out == ["career"]


def test_case_insensitive_varga_id():
    # lowercase 'd10' normalizes to 'D10' (not a wealth varga); with a second
    # domain present the gate can actually drop 'wealth' without emptying the list.
    out = _apply_cr62_multi_varga_gate(["wealth", "character"], "d10")
    assert out == ["character"]


def test_assign_domains_gates_lord_in_house_signal_by_varga():
    # lord_in_house_per_varga is domain-mapped to career+wealth+relationship
    # in _DOMAIN_MAP; a D10 instance must lose 'wealth'.
    d10_domains = _assign_domains("lord_in_house_per_varga", "structural", varga_id="D10")
    assert "wealth" not in d10_domains
    assert "career" in d10_domains

    d2_domains = _assign_domains("lord_in_house_per_varga", "structural", varga_id="D2")
    assert "wealth" in d2_domains
    assert "career" not in d2_domains

    d1_domains = _assign_domains("lord_in_house_per_varga", "structural", varga_id="D1")
    assert "wealth" in d1_domains and "career" in d1_domains
