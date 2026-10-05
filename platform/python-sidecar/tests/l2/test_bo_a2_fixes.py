"""
tests/l2/test_bo_a2_fixes.py — A2 remediation tests for bo_karanajala
======================================================================

Covers these fixes:
  B3-consume  — Contradiction detection fires when same graha has yoga + dosha signal
  B8          — Cross-subsystem edge columns populated correctly
  (O4 argala edges: moved to test_bo_karanajala_argala_from_l1.py)

All tests are pure-unit: no database, no orchestrator, no WriterBase invocation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    _build_edges_and_contradictions,
    _graha_from_cfg,
    _parse_cfg,
    MALEFIC_GRAHAS,
    BENEFIC_GRAHAS,
    KNOWN_GRAHAS,
)

# ── Shared fixtures ────────────────────────────────────────────────────────────

CHART_ID  = "482012f1-710e-4a25-994a-93821f5871aa"
AYA       = "lahiri_chitrapaksha"
BUILD_ID  = "build-test-001"
NOW       = datetime.now(timezone.utc).isoformat()

# Minimal node map: graha nodes + domain nodes
NODE_MAP: dict[tuple[str, str], str] = {
    ("graha", "Mars"):    "node-mars-001",
    ("graha", "Jupiter"): "node-jupiter-001",
    ("graha", "Saturn"):  "node-saturn-001",
    ("graha", "Sun"):     "node-sun-001",
    ("graha", "Moon"):    "node-moon-001",
    ("graha", "Mercury"): "node-mercury-001",
    ("graha", "Venus"):   "node-venus-001",
    ("graha", "Rahu"):    "node-rahu-001",
    ("graha", "Ketu"):    "node-ketu-001",
    ("domain", "career"):       "node-domain-career",
    ("domain", "health"):       "node-domain-health",
    ("domain", "wealth"):       "node-domain-wealth",
    ("domain", "relationship"): "node-domain-rel",
}


def _make_signal(
    signal_id: str,
    sig_class: str,
    graha: str,
    domains: list[str],
    tradition: str = "parashari",
    salience: float = 0.7,
    signal_type_id: str = "test_signal",
) -> dict:
    """Build a minimal signal dict as would come from _fetch_signals()."""
    return {
        "signal_id": signal_id,
        "signal_type_class": sig_class,
        "signal_tradition": tradition,
        "configuration_jsonb": {"graha": graha},
        "domains_affected_array": domains,
        "computed_salience": salience,
        "verification_pass_status": "documented_approximation",
        "salience_formula_version": "v1.0",
        "signal_type_id": signal_type_id,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# B3-consume: Contradiction Detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestB3ContradictionDetection:
    """B3-consume: contradiction row emitted when yoga + dosha share graha + domain."""

    def test_null_graha_yields_domain_level_contradiction(self):
        """WP-2.2 / R-44e: no graha in cfg → NO graha-keyed (Class 1) contradiction,
        but the graha-agnostic Class 2 (domain_promise_vs_denial) STILL fires because
        the 'career' domain carries both a yoga (promise) and a dosha (denial). The old
        assertion of 0 encoded the pre-redesign inert engine; the domain-level tension is
        real and graha-independent by design."""
        # Signals with NO graha field in their configuration
        yoga_sig = {
            "signal_id": "yoga-001",
            "signal_type_class": "yoga",
            "signal_tradition": "parashari",
            "configuration_jsonb": {},           # <-- no graha key
            "domains_affected_array": ["career"],
            "computed_salience": 0.8,
            "verification_pass_status": "documented_approximation",
            "salience_formula_version": "v1.0",
            "signal_type_id": "raja_yoga",
        }
        dosha_sig = {
            "signal_id": "dosha-001",
            "signal_type_class": "dosha",
            "signal_tradition": "parashari",
            "configuration_jsonb": {},           # <-- no graha key
            "domains_affected_array": ["career"],
            "computed_salience": 0.6,
            "verification_pass_status": "documented_approximation",
            "salience_formula_version": "v1.0",
            "signal_type_id": "mangal_dosha",
        }
        signals = [yoga_sig, dosha_sig]
        edges, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        # NULL graha → no Class-1 row, but Class-2 domain-level tension fires on "career".
        assert len(contradictions) == 1, (
            "Expected 1 domain-level contradiction when yoga+dosha share a domain, "
            "even with graha absent from configuration_jsonb"
        )
        c = contradictions[0]
        assert c["tension_class"] == "domain_promise_vs_denial"
        basis = json.loads(c["tension_basis_jsonb"])
        assert "graha" not in basis  # graha-agnostic class
        assert basis["shared_domains"] == ["career"]

    def test_contradiction_detected_when_same_graha_has_yoga_and_dosha(self):
        """PASS-AFTER: given yoga + dosha signals on same graha, contradiction row emitted.

        This verifies that once A1 populates configuration_jsonb.graha,
        _build_edges_and_contradictions() correctly identifies the tension.
        """
        yoga_sig  = _make_signal("yoga-mars-001", "yoga",  "Mars", ["career", "wealth"])
        dosha_sig = _make_signal("dosha-mars-001", "dosha", "Mars", ["career", "health"])
        signals = [yoga_sig, dosha_sig]

        edges, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )

        assert len(contradictions) >= 1, (
            "Expected >= 1 contradiction when yoga and dosha share Mars + career domain"
        )
        c = contradictions[0]
        assert c["tension_class"] == "graha_yoga_vs_dosha"
        assert c["signal_a_id"] == "yoga-mars-001"
        assert c["signal_b_id"] == "dosha-mars-001"
        # Shared domain must be "career" (the intersection)
        basis = json.loads(c["tension_basis_jsonb"])
        assert basis["graha"] == "Mars"
        assert "career" in basis["shared_domains"]
        assert "yoga_signal" in basis
        assert "dosha_signal" in basis
        # combined_salience = 0.7 + 0.7
        assert abs(c["combined_salience"] - 1.4) < 1e-5

    def test_no_contradiction_when_domains_disjoint(self):
        """No contradiction when yoga and dosha on same graha have disjoint domains."""
        yoga_sig  = _make_signal("yoga-mars-002", "yoga",  "Mars", ["career"])
        dosha_sig = _make_signal("dosha-mars-002", "dosha", "Mars", ["health"])
        signals = [yoga_sig, dosha_sig]

        edges, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        assert len(contradictions) == 0, (
            "Disjoint domains should produce no contradiction even with same graha"
        )

    def test_different_grahas_yield_domain_not_graha_contradiction(self):
        """WP-2.2 / R-44e: yoga on Mars + dosha on Jupiter share NO graha → NO Class-1
        (graha_yoga_vs_dosha) row, but they share the 'career' domain → Class 2
        (domain_promise_vs_denial) fires. The old assertion of 0 predated the graha-agnostic
        domain class."""
        yoga_sig  = _make_signal("yoga-mars-003", "yoga",  "Mars",    ["career"])
        dosha_sig = _make_signal("dosha-jup-001", "dosha", "Jupiter", ["career"])
        signals = [yoga_sig, dosha_sig]

        edges, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        assert len(contradictions) == 1, (
            "Different grahas sharing a domain should produce exactly one "
            "domain_promise_vs_denial contradiction"
        )
        c = contradictions[0]
        assert c["tension_class"] == "domain_promise_vs_denial"
        # graha-keyed class must NOT fire across different grahas
        assert all(x["tension_class"] != "graha_yoga_vs_dosha" for x in contradictions)

    def test_tension_basis_jsonb_is_meaningful(self):
        """tension_basis_jsonb must be a non-empty dict with required keys."""
        yoga_sig  = _make_signal("yoga-sun-001", "yoga",  "Sun", ["wealth", "career"])
        dosha_sig = _make_signal("dosha-sun-001", "dosha", "Sun", ["wealth"])
        signals = [yoga_sig, dosha_sig]

        _, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        assert len(contradictions) == 1
        c = contradictions[0]

        # Verify tension_basis_jsonb is parseable and has expected keys
        basis = json.loads(c["tension_basis_jsonb"])
        assert isinstance(basis, dict)
        assert "graha" in basis
        assert "yoga_signal" in basis
        assert "dosha_signal" in basis
        assert "shared_domains" in basis
        assert isinstance(basis["shared_domains"], list)
        assert len(basis["shared_domains"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# B8: Cross-Subsystem Edge Columns
# ═══════════════════════════════════════════════════════════════════════════════

class TestB8CrossSubsystemColumns:
    """B8: is_cross_subsystem, subsystem_from, subsystem_to populated on all edges."""

    def test_yoga_domain_edge_is_always_cross_subsystem(self):
        """B8: yoga→domain edges flagged is_cross_subsystem=True, subsystem_to='domain'."""
        yoga_sig = _make_signal("yoga-mars-b8", "yoga", "Mars", ["career"], tradition="parashari")
        signals  = [yoga_sig]

        edges, _ = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        yoga_edges = [e for e in edges if e["edge_type"] == "yoga_domain"]
        assert len(yoga_edges) >= 1

        for e in yoga_edges:
            assert e["is_cross_subsystem"] is True, (
                "yoga→domain edge must be cross_subsystem (graha tradition ≠ 'domain')"
            )
            assert e["subsystem_from"] == "parashari"
            assert e["subsystem_to"] == "domain"

    def test_dosha_domain_edge_is_always_cross_subsystem(self):
        """B8: dosha→domain edges flagged is_cross_subsystem=True, subsystem_to='domain'."""
        dosha_sig = _make_signal("dosha-mars-b8", "dosha", "Mars", ["health"], tradition="jaimini")
        signals   = [dosha_sig]

        edges, _ = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        dosha_edges = [e for e in edges if e["edge_type"] == "dosha_domain"]
        assert len(dosha_edges) >= 1

        for e in dosha_edges:
            assert e["is_cross_subsystem"] is True
            assert e["subsystem_from"] == "jaimini"
            assert e["subsystem_to"] == "domain"

    def test_yoga_domain_edge_carries_tradition_in_subsystem_from(self):
        """B8: subsystem_from matches the signal's tradition (kp example)."""
        yoga_sig = _make_signal("yoga-sat-b8", "yoga", "Saturn", ["career"], tradition="kp")
        signals  = [yoga_sig]

        edges, _ = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        yoga_edges = [e for e in edges if e["edge_type"] == "yoga_domain"]
        assert len(yoga_edges) >= 1
        for e in yoga_edges:
            assert e["subsystem_from"] == "kp"
            assert e["is_cross_subsystem"] is True

    def test_aspect_edge_is_not_cross_subsystem(self):
        """B8: graha→graha aspect edge has is_cross_subsystem=False (same tradition)."""
        aspect_sig = {
            "signal_id": "aspect-sun-moon-001",
            "signal_type_class": "composite_state",
            "signal_tradition": "parashari",
            "configuration_jsonb": {"graha": "Sun", "aspected_graha": "Moon"},
            "domains_affected_array": ["general"],
            "computed_salience": 0.5,
            "verification_pass_status": "documented_approximation",
            "salience_formula_version": "v1.0",
            "signal_type_id": "aspect_sun_moon",
        }
        signals = [aspect_sig]

        edges, _ = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        aspect_edges = [e for e in edges if e["edge_type"] in ("aspect", "conjunction")]
        assert len(aspect_edges) >= 1

        for e in aspect_edges:
            assert e["is_cross_subsystem"] is False
            assert e["subsystem_from"] == "parashari"
            assert e["subsystem_to"] == "parashari"

    def test_all_edges_have_subsystem_columns(self):
        """B8: every edge row has all three subsystem columns present."""
        yoga_sig  = _make_signal("yoga-jup-all", "yoga",  "Jupiter", ["career"])
        dosha_sig = _make_signal("dosha-sat-all", "dosha", "Saturn",  ["wealth"])
        signals   = [yoga_sig, dosha_sig]

        edges, _ = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        assert len(edges) > 0
        for e in edges:
            assert "is_cross_subsystem" in e, f"Missing is_cross_subsystem on edge {e['edge_type']}"
            assert "subsystem_from" in e,     f"Missing subsystem_from on edge {e['edge_type']}"
            assert "subsystem_to" in e,       f"Missing subsystem_to on edge {e['edge_type']}"


# ═══════════════════════════════════════════════════════════════════════════════
# O4: Argala Chain CGM Edges — MOVED
# ═══════════════════════════════════════════════════════════════════════════════
# The argala edge tests moved to tests/l2/test_bo_karanajala_argala_from_l1.py (I.ARG, N-61): L2 no longer
# computes argala from sign positions (the old position-based tests here exercised the removed
# ARGALA_POSITIONS / VIRODHA_POSITIONS / _house_of_b_from_a and the old 4-3 / 11-10 pairing); it READS the L1
# argala_graha_natal facts by fact_id, and the new file feeds it the rows the real L1 builder emits.


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests for helper functions (regression guards)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHelpers:
    """Low-level unit tests for extraction helpers."""

    def test_graha_from_cfg_direct_key(self):
        assert _graha_from_cfg({"graha": "Mars"}) == "Mars"

    def test_graha_from_cfg_primary_graha(self):
        assert _graha_from_cfg({"primary_graha": "Jupiter"}) == "Jupiter"

    def test_graha_from_cfg_lord(self):
        assert _graha_from_cfg({"lord": "Venus"}) == "Venus"

    def test_graha_from_cfg_from_graha(self):
        assert _graha_from_cfg({"from_graha": "Saturn"}) == "Saturn"

    def test_graha_from_cfg_fact_key_colon(self):
        # fact_key may contain "Mars:sign_number" form
        assert _graha_from_cfg({"fact_key": "Mars:sign_number"}) == "Mars"

    def test_graha_from_cfg_unknown_value_returns_none(self):
        assert _graha_from_cfg({"graha": "NotAGraha"}) is None

    def test_graha_from_cfg_empty_returns_none(self):
        assert _graha_from_cfg({}) is None

    def test_parse_cfg_dict_passthrough(self):
        cfg = {"graha": "Sun", "foo": 42}
        assert _parse_cfg({"configuration_jsonb": cfg}) == cfg

    def test_parse_cfg_string_json(self):
        cfg = {"graha": "Moon"}
        sig = {"configuration_jsonb": json.dumps(cfg)}
        assert _parse_cfg(sig) == cfg

    def test_parse_cfg_invalid_string_returns_empty(self):
        sig = {"configuration_jsonb": "not-json{{{"}
        assert _parse_cfg(sig) == {}

    def test_parse_cfg_none_returns_empty(self):
        assert _parse_cfg({"configuration_jsonb": None}) == {}
