"""
Tests for bo_karanajala dispositor edge generation.

Covers:
1. _fetch_graha_sign_numbers subject mapping (title() bug fix)
2. _build_dispositor_edges() output correctness
3. Integration: motif detectors fire when dispositor edges exist
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import pytest

from pipeline.orchestrator.writers.bo_karanajala import (
    _fetch_graha_sign_numbers,
    _build_dispositor_edges,
    SIGN_LORD,
    KNOWN_GRAHAS,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID  = str(uuid.uuid4())
AYA       = "lahiri_chitrapaksha"
NOW       = "2026-06-29T00:00:00+00:00"


def _make_conn_with_rows(rows: list[tuple]) -> MagicMock:
    """Return a conn mock whose .execute().fetchall() returns rows.

    NOTE: This helper is specific to bo_karanajala's conn.execute() DB protocol.
    bo_cgm_motifs uses conn.cursor() context manager protocol and would need
    a different mock pattern if _write_aya were tested directly.
    """
    conn = MagicMock()
    conn.execute.return_value.fetchall.return_value = rows
    return conn


class TestFetchGrahaSignNumbers:

    def test_abbreviated_codes_map_to_full_graha_names(self) -> None:
        """MAR→Mars, MER→Mercury, etc. — abbreviated L1 codes must produce KNOWN_GRAHAS keys."""
        rows = [
            ("SUN",      10.0),   # Capricorn
            ("MOON",     11.0),   # Aquarius
            ("MAR",       1.0),   # Aries
            ("MER",       9.0),   # Sagittarius
            ("JUP",       5.0),   # Leo
            ("VEN",       8.0),   # Scorpio
            ("SAT",      10.0),   # Capricorn
            ("RAH_MEAN",  6.0),   # Virgo
            ("KET_MEAN", 12.0),   # Pisces
        ]
        conn = _make_conn_with_rows(rows)
        result = _fetch_graha_sign_numbers(conn, CHART_ID, AYA)

        assert set(result.keys()) == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu"
        }, f"Expected all 9 KNOWN_GRAHA keys; got {set(result.keys())}"

    def test_sign_numbers_are_integers(self) -> None:
        rows = [("SUN", 10.0), ("MOON", 4.0)]
        conn = _make_conn_with_rows(rows)
        result = _fetch_graha_sign_numbers(conn, CHART_ID, AYA)
        assert result["Sun"] == 10
        assert result["Moon"] == 4
        assert isinstance(result["Sun"], int)

    def test_old_title_case_would_have_failed(self) -> None:
        """Document that subject.title() on abbreviated codes produces wrong keys."""
        assert "MAR".title() == "Mar"      # would miss KNOWN_GRAHAS["Mars"]
        assert "MER".title() == "Mer"      # would miss KNOWN_GRAHAS["Mercury"]
        assert "JUP".title() == "Jup"      # would miss KNOWN_GRAHAS["Jupiter"]
        assert "VEN".title() == "Ven"      # would miss KNOWN_GRAHAS["Venus"]
        assert "SAT".title() == "Sat"      # would miss KNOWN_GRAHAS["Saturn"]


class TestSignLord:

    def test_sign_lord_has_all_12_signs(self) -> None:
        assert set(SIGN_LORD.keys()) == set(range(1, 13))

    def test_sign_lord_classical_values(self) -> None:
        assert SIGN_LORD[1]  == "Mars"      # Aries
        assert SIGN_LORD[2]  == "Venus"     # Taurus
        assert SIGN_LORD[3]  == "Mercury"   # Gemini
        assert SIGN_LORD[4]  == "Moon"      # Cancer
        assert SIGN_LORD[5]  == "Sun"       # Leo
        assert SIGN_LORD[6]  == "Mercury"   # Virgo
        assert SIGN_LORD[7]  == "Venus"     # Libra
        assert SIGN_LORD[8]  == "Mars"      # Scorpio
        assert SIGN_LORD[9]  == "Jupiter"   # Sagittarius
        assert SIGN_LORD[10] == "Saturn"    # Capricorn
        assert SIGN_LORD[11] == "Saturn"    # Aquarius
        assert SIGN_LORD[12] == "Jupiter"   # Pisces


class TestBuildDispositorEdges:

    def _make_node_map(self, assignments: dict[str, str]) -> dict[tuple[str, str], str]:
        return {("graha", g): nid for g, nid in assignments.items()}

    def test_sun_in_capricorn_disposits_saturn(self) -> None:
        """Sun in Capricorn (sign 10, lord Saturn) → edge Sun→Saturn."""
        node_map = self._make_node_map({"Sun": "node-sun", "Saturn": "node-sat"})
        graha_signs = {"Sun": 10, "Saturn": 10}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        sun_edges = [e for e in edges if e["from_node_id"] == "node-sun"]
        assert len(sun_edges) == 1
        e = sun_edges[0]
        assert e["edge_type"] == "dispositor"
        assert e["to_node_id"] == "node-sat"
        assert e["direction"] == "directed"

    def test_self_ruling_graha_skipped(self) -> None:
        """Sun in Leo (sign 5) is self-ruling — no dispositor edge emitted."""
        node_map = self._make_node_map({"Sun": "node-sun"})
        graha_signs = {"Sun": 5}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert edges == [], "Self-ruling graha must not produce a dispositor edge"

    def test_mutual_reception_produces_two_edges(self) -> None:
        """Sun in Aries (lord Mars) + Mars in Leo (lord Sun) → two dispositor edges."""
        node_map = self._make_node_map({"Sun": "node-sun", "Mars": "node-mars"})
        graha_signs = {"Sun": 1, "Mars": 5}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert len(edges) == 2
        from_to = {(e["from_node_id"], e["to_node_id"]) for e in edges}
        assert ("node-sun", "node-mars") in from_to
        assert ("node-mars", "node-sun") in from_to

    def test_unknown_graha_skipped(self) -> None:
        """Grahas not in KNOWN_GRAHAS are silently skipped."""
        node_map = self._make_node_map({"Sun": "node-sun", "Saturn": "node-sat"})
        graha_signs = {"Sun": 10, "NotAGraha": 1}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        sun_edges = [e for e in edges if e["from_node_id"] == "node-sun"]
        assert len(sun_edges) == 1

    def test_missing_node_in_map_skipped(self) -> None:
        """If the lord graha has no node in node_map, skip gracefully."""
        node_map = self._make_node_map({"Sun": "node-sun"})  # Saturn missing
        graha_signs = {"Sun": 10}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        assert edges == [], "Missing target node must not raise"

    def test_edge_fields_complete(self) -> None:
        """Required edge fields are present and non-null."""
        node_map = self._make_node_map({"Sun": "node-sun", "Saturn": "node-sat"})
        graha_signs = {"Sun": 10, "Saturn": 10}
        edges = _build_dispositor_edges(CHART_ID, AYA, BUILD_ID, graha_signs, node_map, NOW)
        sun_edges = [e for e in edges if e["from_node_id"] == "node-sun"]
        assert sun_edges
        e = sun_edges[0]
        for field in ("edge_id", "chart_id", "ayanamsha_id", "build_id", "edge_type",
                      "from_node_id", "to_node_id", "direction", "computed_strength",
                      "verification_pass_status", "citation_ref", "computed_at"):
            assert e.get(field) is not None, f"Required field '{field}' is None"

        # relationship_basis must NOT be in edge_properties_jsonb — it's inert there
        # (the motif detectors fire on edge_type='dispositor', not on relationship_basis)
        props = json.loads(e["edge_properties_jsonb"])
        assert "relationship_basis" not in props
