"""
Tests for bo_yantra_mechanism (D-2 Lane V-4, CR-24/CR-25/CR-86).

Covers the general cycle/chain detector (pure logic, no DB) and the
motif->mechanism promotion helpers (valence/edge-strength/centrality
aggregation).
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_yantra_mechanism import (
    _find_cycles,
    _find_convergent_chains,
    _mechanism_valence,
    _edge_strength_summary,
    _centrality_summary,
    _fingerprint,
)


def test_find_cycles_detects_a_real_circuit():
    """Synthetic proof the detector correctly finds a closed circuit when one
    genuinely exists — e.g. the CR-24-shaped '10 -> 8 -> 12 -> 10' specimen,
    here as houses (as strings, matching the writer's node-key convention)."""
    adj = {"10": "8", "8": "12", "12": "10"}
    cycles = _find_cycles(adj)
    assert len(cycles) == 1
    cycle = cycles[0]
    assert set(cycle) == {"10", "8", "12"}
    # cyclic order preserved starting from whichever node was visited first
    assert len(cycle) == 3


def test_find_cycles_excludes_self_loops():
    """A self-ruling graha/house (node -> itself) is the classical 'final
    dispositor' state — not a circuit."""
    adj = {"9": "9"}
    assert _find_cycles(adj) == []


def test_find_cycles_no_cycle_on_acyclic_chain():
    """Matches the LIVE finding on 482012f1: houses converge to a terminal via
    an acyclic chain — no closed circuit."""
    adj = {"1": "7", "7": "9", "9": "9"}
    assert _find_cycles(adj) == []


def test_find_convergent_chains_groups_by_terminal():
    adj = {"Sun": "Saturn", "Moon": "Saturn", "Saturn": "Venus", "Venus": "Jupiter"}
    convergent = _find_convergent_chains(adj, min_converging=2)
    terminals = {t: set(starts) for t, starts in convergent}
    assert "Jupiter" in terminals
    assert {"Sun", "Moon", "Saturn", "Venus"}.issubset(terminals["Jupiter"])


def test_find_convergent_chains_respects_min_converging():
    adj = {"Sun": "Saturn", "Saturn": "Jupiter"}
    assert _find_convergent_chains(adj, min_converging=3) == []


def test_mechanism_valence_all_harmonious_is_benefic():
    assert _mechanism_valence(["harmonious", "harmonious"]) == "benefic"


def test_mechanism_valence_all_antagonistic_is_malefic():
    assert _mechanism_valence(["antagonistic"]) == "malefic"


def test_mechanism_valence_mixed():
    assert _mechanism_valence(["harmonious", "antagonistic"]) == "mixed"


def test_mechanism_valence_neutral_default():
    assert _mechanism_valence(["neutral", None]) == "neutral"


def test_edge_strength_summary_anti_vacuous():
    edges = [{"computed_strength": 0.5}, {"computed_strength": 1.2}, {"computed_strength": 0.8}]
    avg, lo, hi = _edge_strength_summary(edges)
    assert lo == 0.5
    assert hi == 1.2
    assert lo < avg < hi  # non-degenerate — not all equal


def test_edge_strength_summary_empty():
    assert _edge_strength_summary([]) == (None, None, None)


def test_centrality_summary_averages_present_values_only():
    nodes = [
        {"pagerank_score": 0.2, "eigenvector_centrality": None, "betweenness_centrality": 0.1, "harmonic_centrality": 0.3},
        {"pagerank_score": 0.4, "eigenvector_centrality": 0.5, "betweenness_centrality": 0.3, "harmonic_centrality": 0.1},
    ]
    summary = _centrality_summary(nodes)
    assert summary["pagerank_avg"] == 0.3
    assert summary["eigenvector_avg"] == 0.5  # only one non-null value
    assert summary["member_count"] == 2


def test_fingerprint_is_order_independent_and_class_scoped():
    fp1 = _fingerprint(["a", "b", "c"], "yoga_cluster")
    fp2 = _fingerprint(["c", "b", "a"], "yoga_cluster")
    fp3 = _fingerprint(["a", "b", "c"], "dispositor_cycle")
    assert fp1 == fp2
    assert fp1 != fp3
