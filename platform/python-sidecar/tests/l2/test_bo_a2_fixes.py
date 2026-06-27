"""
tests/l2/test_bo_a2_fixes.py — A2 remediation tests for bo_karanajala
======================================================================

Covers three fixes:
  B3-consume  — Contradiction detection fires when same graha has yoga + dosha signal
  B8          — Cross-subsystem edge columns populated correctly
  O4          — Argala chain CGM edges emitted with correct direction + class

All tests are pure-unit: no database, no orchestrator, no WriterBase invocation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    _build_edges_and_contradictions,
    _build_argala_edges,
    _house_of_b_from_a,
    _graha_from_cfg,
    _parse_cfg,
    ARGALA_POSITIONS,
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

    def test_no_contradiction_when_graha_is_null(self):
        """FAIL-BEFORE baseline: no graha in cfg → no contradiction emitted.

        This documents the upstream NULL bug that A1 fixes (G1 merge).
        Pre-fix, configuration_jsonb.graha was absent for yoga/dosha signals,
        so _graha_from_cfg returned None and the graha indexes were never populated.
        """
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
        # With NULL graha, no contradiction should be emitted
        assert len(contradictions) == 0, (
            "Expected 0 contradictions when graha is absent from configuration_jsonb"
        )

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
        assert c["tension_class"] == "yoga_vs_dosha"
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

    def test_no_contradiction_when_different_grahas(self):
        """No contradiction when yoga on Mars and dosha on Jupiter."""
        yoga_sig  = _make_signal("yoga-mars-003", "yoga",  "Mars",    ["career"])
        dosha_sig = _make_signal("dosha-jup-001", "dosha", "Jupiter", ["career"])
        signals = [yoga_sig, dosha_sig]

        edges, contradictions = _build_edges_and_contradictions(
            CHART_ID, AYA, BUILD_ID, signals, NODE_MAP, NOW
        )
        assert len(contradictions) == 0, (
            "Different grahas should produce no yoga_vs_dosha contradiction"
        )

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
# O4: Argala Chain CGM Edges
# ═══════════════════════════════════════════════════════════════════════════════

class TestO4ArgalaEdges:
    """O4: argala edges emitted with correct direction, class, and cancellation logic."""

    def test_house_of_b_from_a_basic(self):
        """_house_of_b_from_a: Aries(1)→Taurus(2) = house 2."""
        assert _house_of_b_from_a(1, 2) == 2

    def test_house_of_b_from_a_wrap_around(self):
        """_house_of_b_from_a: Pisces(12)→Aries(1) = house 2 (wraps)."""
        assert _house_of_b_from_a(12, 1) == 2

    def test_house_of_b_from_a_same_sign(self):
        """_house_of_b_from_a: same sign = house 1."""
        assert _house_of_b_from_a(5, 5) == 1

    def test_house_of_b_from_a_11th(self):
        """_house_of_b_from_a: Aries(1)→Aquarius(11) = house 11."""
        assert _house_of_b_from_a(1, 11) == 11

    def test_argala_edges_emitted_for_known_positions(self):
        """O4: graha in 2nd, 4th, or 11th from another emits an argala edge."""
        # Sun in Aries(1), Moon in Taurus(2) → Moon is in 2nd from Sun → argala on Sun
        graha_signs = {
            "Sun":  1,   # Aries
            "Moon": 2,   # Taurus (2nd from Sun → argala)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        # Find edge where Moon (B) → Sun (A)
        argala_edges = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Moon")]
            and e["to_node_id"] == NODE_MAP[("graha", "Sun")]
        ]
        assert len(argala_edges) >= 1, (
            "Moon in 2nd from Sun must generate an argala edge Moon→Sun"
        )
        e = argala_edges[0]
        assert e["edge_type"] == "argala"
        assert e["direction"] == "directed"
        # Moon is benefic → argala_positive
        assert e["relationship_class"] == "argala_positive"
        assert e["cancelled_flag"] is False

    def test_argala_direction_b_to_a(self):
        """O4: argala edge direction is from_node=B (intervener) to_node=A (subject)."""
        # Jupiter in 4th from Mars → Jupiter creates argala on Mars
        graha_signs = {
            "Mars":    1,  # Aries
            "Jupiter": 4,  # Cancer (4th from Aries)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        jup_to_mars = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Jupiter")]
            and e["to_node_id"] == NODE_MAP[("graha", "Mars")]
        ]
        assert len(jup_to_mars) >= 1, "Jupiter in 4th from Mars must emit argala edge Jupiter→Mars"
        e = jup_to_mars[0]
        assert e["relationship_class"] == "argala_positive"  # Jupiter is benefic

    def test_virodha_argala_for_malefic(self):
        """O4: malefic in argala position gets relationship_class='argala_virodha'."""
        # Saturn in 2nd from Sun → virodha-argala (Saturn is malefic)
        graha_signs = {
            "Sun":    1,  # Aries
            "Saturn": 2,  # Taurus (2nd from Sun)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        sat_to_sun = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Saturn")]
            and e["to_node_id"] == NODE_MAP[("graha", "Sun")]
        ]
        assert len(sat_to_sun) >= 1
        assert sat_to_sun[0]["relationship_class"] == "argala_virodha"

    def test_virodha_cancellation_applied(self):
        """O4: malefic argala cancelled when a planet occupies the virodha position."""
        # Saturn in 2nd from Sun → virodha-argala (argala pos=2, virodha pos=12)
        # Jupiter in 12th from Sun → cancels Saturn's virodha-argala
        graha_signs = {
            "Sun":    1,   # Aries
            "Saturn": 2,   # Taurus  (2nd from Sun — virodha-argala)
            "Jupiter": 12, # Pisces  (12th from Sun — virodha position → cancels 2nd argala)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        sat_to_sun = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Saturn")]
            and e["to_node_id"] == NODE_MAP[("graha", "Sun")]
        ]
        assert len(sat_to_sun) >= 1
        assert sat_to_sun[0]["cancelled_flag"] is True, (
            "Saturn's 2nd-position virodha-argala on Sun must be cancelled by Jupiter at 12th"
        )

    def test_argala_not_emitted_for_non_argala_positions(self):
        """O4: no argala edge when B is in 3rd, 5th, 6th, 7th, 8th, 9th, or 10th from A."""
        # Mars in 3rd from Sun — not an argala position
        graha_signs = {
            "Sun":  1,  # Aries
            "Mars": 3,  # Gemini (3rd from Aries — not argala)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        mars_to_sun = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Mars")]
            and e["to_node_id"] == NODE_MAP[("graha", "Sun")]
        ]
        assert len(mars_to_sun) == 0, (
            "Mars in 3rd from Sun is NOT an argala position — no edge should be emitted"
        )

    def test_argala_edge_properties_jsonb(self):
        """O4: edge_properties_jsonb contains argala metadata."""
        graha_signs = {
            "Sun":  1,  # Aries
            "Moon": 11, # Aquarius (11th from Sun → argala)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        moon_to_sun = [
            e for e in edges
            if e["from_node_id"] == NODE_MAP[("graha", "Moon")]
            and e["to_node_id"] == NODE_MAP[("graha", "Sun")]
        ]
        assert len(moon_to_sun) >= 1
        props = json.loads(moon_to_sun[0]["edge_properties_jsonb"])
        assert props["argala_subject"] == "Sun"
        assert props["argala_karaka"] == "Moon"
        assert props["argala_position"] == 11

    def test_argala_edge_subsystem_columns(self):
        """O4: argala edges have is_cross_subsystem=False, tradition='parashari' on both ends."""
        graha_signs = {
            "Sun":  1,
            "Moon": 4,  # 4th from Sun → argala
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        assert len(edges) > 0
        for e in edges:
            assert e["is_cross_subsystem"] is False
            assert e["subsystem_from"] == "parashari"
            assert e["subsystem_to"] == "parashari"

    def test_argala_no_self_loop(self):
        """O4: no argala edge from a graha to itself."""
        graha_signs = {g: i + 1 for i, g in enumerate(sorted(KNOWN_GRAHAS))}
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        for e in edges:
            assert e["from_node_id"] != e["to_node_id"], (
                "Argala self-loop detected — a graha cannot create argala on itself"
            )

    def test_argala_with_full_nine_grahas(self):
        """O4: nine grahas produce a realistic count of argala edges (> 0, ≤ 72)."""
        # Spread grahas across all 12 signs (some signs share grahas)
        graha_signs = {
            "Sun":     1,   # Aries
            "Moon":    2,   # Taurus
            "Mars":    4,   # Cancer
            "Mercury": 1,   # Aries (conjoins Sun)
            "Jupiter": 11,  # Aquarius
            "Venus":   2,   # Taurus (conjoins Moon)
            "Saturn":  7,   # Libra
            "Rahu":    10,  # Capricorn
            "Ketu":    4,   # Cancer (conjoins Mars)
        }
        edges = _build_argala_edges(
            CHART_ID, AYA, BUILD_ID, graha_signs, NODE_MAP, NOW
        )
        # With 9 grahas, max possible argala pairs = 9×3 = 27 (per graha as subject,
        # up to 3 argala positions). Realistically fewer due to positional overlap.
        assert len(edges) > 0, "Expected > 0 argala edges for 9 grahas spread across signs"
        assert len(edges) <= 9 * 8, (
            "Argala edge count cannot exceed 9×8=72 (all ordered pairs, self excluded)"
        )


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
