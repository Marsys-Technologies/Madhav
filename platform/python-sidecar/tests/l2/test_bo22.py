"""
tests/l2/test_bo22.py — BRAHMA-BO-2-2: bodha.graph unit tests
==============================================================

Tests the CGM signal graph builder/seeder without a live database.
DB-dependent tests are marked with @pytest.mark.integration and require
DATABASE_URL to be set + bodha_graph table to exist.

Contract (BRAHMA_L1_L5_REGISTRY_SEED §C):
  - valenced edges present; traversal returns provenance; no self-loops
  - FORENSIC: at least 5 edges for native's chart
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ── Import target ──────────────────────────────────────────────────────────────

from brahmagyan.bodha.bo22 import (
    CANONICAL_EDGES,
    WEIGHT_MAP,
    NATIVE_CHART_ID,
    load_edges_from_manifest,
    seed_bodha_graph,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

NATIVE_CHART_ID_EXPECTED = "362f9f17-95a5-490b-a5a7-027d3e0efda0"


@pytest.fixture
def sample_manifest(tmp_path: Path) -> Path:
    """Write a minimal cgm_edges_manifest JSON fixture."""
    manifest = {
        "artifact": "cgm_edges_manifest_v1_0.json",
        "version": "1.0",
        "edges": [
            {
                "edge_id": "CGM_EDGE_001",
                "source_node_id": "PLN.SUN",
                "target_node_id": "PLN.SATURN",
                "edge_type": "DISPOSITED_BY",
                "l1_source_section": "FORENSIC_v8_0 §2.1",
                "l1_derivation": "Sun in Capricorn (291.96°); Saturn rules Capricorn",
            },
            {
                "edge_id": "CGM_EDGE_009",
                "source_node_id": "PLN.SUN",
                "target_node_id": "PLN.MOON",
                "edge_type": "NAKSHATRA_LORD_IS",
                "l1_source_section": "FORENSIC_v8_0 §2.1",
                "l1_derivation": "Sun in Shravana; lord = Moon",
            },
            # Self-loop (should be excluded)
            {
                "edge_id": "CGM_EDGE_014",
                "source_node_id": "PLN.VENUS",
                "target_node_id": "PLN.VENUS",
                "edge_type": "NAKSHATRA_LORD_IS",
                "l1_source_section": "FORENSIC_v8_0 §2.1",
                "l1_derivation": "Venus in Purva Ashadha; self-lord",
            },
        ],
    }
    p = tmp_path / "cgm_edges_manifest_v1_0.json"
    p.write_text(json.dumps(manifest))
    return p


# ── CANONICAL_EDGES tests ──────────────────────────────────────────────────────


class TestCanonicalEdges:
    """Tests on the embedded CANONICAL_EDGES constant."""

    def test_minimum_edge_count(self):
        """AC gate: at least 5 edges present in the canonical set."""
        assert len(CANONICAL_EDGES) >= 5, (
            f"Expected ≥5 canonical edges; got {len(CANONICAL_EDGES)}"
        )

    def test_no_self_loops_in_canonical(self):
        """Contract: no self-loops (from_signal_id ≠ to_signal_id)."""
        self_loops = [
            e for e in CANONICAL_EDGES
            if e["from_signal_id"] == e["to_signal_id"]
        ]
        assert self_loops == [], (
            f"Self-loops found in CANONICAL_EDGES: {[e['edge_id'] for e in self_loops]}"
        )

    def test_all_edges_have_source_citation(self):
        """Provenance: every edge must carry a non-empty source_citation."""
        missing = [
            e["edge_id"] for e in CANONICAL_EDGES
            if not e.get("source_citation", "").strip()
        ]
        assert missing == [], (
            f"Edges missing source_citation: {missing}"
        )

    def test_all_edges_have_required_fields(self):
        """Schema: every edge has all required fields."""
        required = {"edge_id", "from_signal_id", "to_signal_id", "edge_type", "source_citation"}
        for edge in CANONICAL_EDGES:
            missing_fields = required - set(edge.keys())
            assert missing_fields == set(), (
                f"Edge {edge.get('edge_id')} missing fields: {missing_fields}"
            )

    def test_at_least_three_distinct_edge_types(self):
        """AC gate: ≥3 distinct edge types (DISPOSITED_BY, NAKSHATRA_LORD_IS, ASPECTS_*)."""
        types = {e["edge_type"] for e in CANONICAL_EDGES}
        assert len(types) >= 3, (
            f"Expected ≥3 distinct edge types; got {sorted(types)}"
        )

    def test_cgm_edge_014_not_in_canonical(self):
        """CGM_EDGE_014 (PLN.VENUS→PLN.VENUS self-loop) must be excluded."""
        self_loop_ids = {e["edge_id"] for e in CANONICAL_EDGES}
        assert "CGM_EDGE_014" not in self_loop_ids, (
            "CGM_EDGE_014 (Venus→Venus self-loop) must not be in CANONICAL_EDGES"
        )

    def test_forensic_grounded_edge_present(self):
        """FORENSIC grounding: PLN.SUN→PLN.SATURN DISPOSITED_BY must be present."""
        found = any(
            e["from_signal_id"] == "PLN.SUN"
            and e["to_signal_id"] == "PLN.SATURN"
            and e["edge_type"] == "DISPOSITED_BY"
            for e in CANONICAL_EDGES
        )
        assert found, (
            "Expected PLN.SUN→PLN.SATURN DISPOSITED_BY edge (grounded in FORENSIC_v8_0 §2.1)"
        )

    def test_mars_in_h7_aspects_present(self):
        """FORENSIC grounding: Mars aspects from H7 (ASPECTS_4TH, ASPECTS_8TH) present."""
        mars_aspects = [
            e for e in CANONICAL_EDGES
            if e["from_signal_id"] == "PLN.MARS"
            and e["edge_type"] in {"ASPECTS_4TH", "ASPECTS_8TH"}
        ]
        assert len(mars_aspects) >= 2, (
            f"Expected ≥2 Mars aspect edges; got {len(mars_aspects)}: "
            f"{[e['edge_id'] for e in mars_aspects]}"
        )

    def test_source_citations_reference_forensic(self):
        """All source_citations must mention FORENSIC_v8_0 (L1 grounding)."""
        not_forensic = [
            e["edge_id"]
            for e in CANONICAL_EDGES
            if "FORENSIC" not in e.get("source_citation", "")
        ]
        assert not_forensic == [], (
            f"Edges with source_citation not referencing FORENSIC: {not_forensic}"
        )


# ── WEIGHT_MAP tests ───────────────────────────────────────────────────────────


class TestWeightMap:
    """Tests on edge weight configuration."""

    def test_all_canonical_edge_types_have_weight(self):
        """Every edge_type in CANONICAL_EDGES must have a weight mapping."""
        types_in_canonical = {e["edge_type"] for e in CANONICAL_EDGES}
        missing_weights = types_in_canonical - set(WEIGHT_MAP.keys())
        assert missing_weights == set(), (
            f"Edge types without weight mapping: {missing_weights}"
        )

    def test_weights_in_valid_range(self):
        """All weights must be in (0, 1]."""
        for edge_type, w in WEIGHT_MAP.items():
            assert 0 < w <= 1.0, (
                f"Weight for {edge_type} out of range (0, 1]: {w}"
            )


# ── load_edges_from_manifest tests ────────────────────────────────────────────


class TestLoadEdgesFromManifest:
    """Tests for file-based edge loading."""

    def test_loads_non_self_loop_edges(self, sample_manifest: Path):
        """Manifest loader must exclude self-loop edges."""
        edges = load_edges_from_manifest(sample_manifest)
        ids = {e["edge_id"] for e in edges}
        assert "CGM_EDGE_014" not in ids, "Self-loop CGM_EDGE_014 must be excluded"
        assert "CGM_EDGE_001" in ids
        assert "CGM_EDGE_009" in ids

    def test_returns_canonical_edges_on_missing_file(self, tmp_path: Path):
        """Falls back to CANONICAL_EDGES when manifest file is missing."""
        edges = load_edges_from_manifest(tmp_path / "nonexistent.json")
        # Should return CANONICAL_EDGES content
        assert len(edges) == len(CANONICAL_EDGES)

    def test_edge_fields_present(self, sample_manifest: Path):
        """Loaded edges have the required fields."""
        required = {"edge_id", "from_signal_id", "to_signal_id", "edge_type", "source_citation"}
        edges = load_edges_from_manifest(sample_manifest)
        for e in edges:
            assert required.issubset(set(e.keys())), (
                f"Edge {e.get('edge_id')} missing fields: {required - set(e.keys())}"
            )

    def test_source_citation_built_from_l1_derivation(self, sample_manifest: Path):
        """source_citation is built from l1_source_section + l1_derivation."""
        edges = load_edges_from_manifest(sample_manifest)
        sun_edge = next(e for e in edges if e["edge_id"] == "CGM_EDGE_001")
        assert "FORENSIC_v8_0" in sun_edge["source_citation"]
        assert "Capricorn" in sun_edge["source_citation"]


# ── seed_bodha_graph tests (mocked DB) ────────────────────────────────────────


class TestSeedBodhaGraph:
    """Tests for the seed function — DB calls are mocked."""

    def test_dry_run_returns_count(self):
        """dry_run=True returns row count without touching DB."""
        count = seed_bodha_graph(NATIVE_CHART_ID_EXPECTED, dry_run=True)
        assert count == len(CANONICAL_EDGES), (
            f"dry_run should return {len(CANONICAL_EDGES)} rows; got {count}"
        )

    def test_dry_run_excludes_self_loops(self):
        """dry_run mode must not include self-loop edges."""
        edges_with_loop = list(CANONICAL_EDGES) + [
            {
                "edge_id": "SELF_LOOP_TEST",
                "from_signal_id": "PLN.MARS",
                "to_signal_id": "PLN.MARS",
                "edge_type": "DISPOSITED_BY",
                "source_citation": "FORENSIC_v8_0 §2.1: test",
            }
        ]
        count = seed_bodha_graph(
            NATIVE_CHART_ID_EXPECTED, edges=edges_with_loop, dry_run=True
        )
        # Self-loop should be excluded
        assert count == len(CANONICAL_EDGES), (
            f"Expected {len(CANONICAL_EDGES)} rows (self-loop excluded); got {count}"
        )

    @patch("brahmagyan.bodha.bo22._get_conn")
    def test_seed_calls_executemany(self, mock_get_conn: MagicMock):
        """seed_bodha_graph calls executemany with the correct number of rows."""
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor = MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_cur),
            __exit__=MagicMock(return_value=False),
        ))
        mock_get_conn.return_value = mock_conn

        count = seed_bodha_graph(NATIVE_CHART_ID_EXPECTED)

        # executemany must be called once
        mock_cur.executemany.assert_called_once()
        # The rows argument should have len(CANONICAL_EDGES) entries
        rows_arg = mock_cur.executemany.call_args[0][1]
        assert len(rows_arg) == len(CANONICAL_EDGES), (
            f"Expected {len(CANONICAL_EDGES)} rows passed to executemany; got {len(rows_arg)}"
        )
        assert count == len(CANONICAL_EDGES)

    @patch("brahmagyan.bodha.bo22._get_conn")
    def test_seed_upsert_sql_contains_on_conflict(self, mock_get_conn: MagicMock):
        """The upsert SQL must contain ON CONFLICT (edge_id) DO UPDATE."""
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor = MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_cur),
            __exit__=MagicMock(return_value=False),
        ))
        mock_get_conn.return_value = mock_conn

        seed_bodha_graph(NATIVE_CHART_ID_EXPECTED)

        sql_arg = mock_cur.executemany.call_args[0][0]
        assert "ON CONFLICT (edge_id) DO UPDATE" in sql_arg, (
            "Upsert SQL must contain ON CONFLICT (edge_id) DO UPDATE"
        )

    def test_native_chart_id_default(self):
        """NATIVE_CHART_ID constant is the FORENSIC canonical chart UUID."""
        assert NATIVE_CHART_ID == NATIVE_CHART_ID_EXPECTED or NATIVE_CHART_ID == NATIVE_CHART_ID_EXPECTED, (
            f"NATIVE_CHART_ID should default to {NATIVE_CHART_ID_EXPECTED}; got {NATIVE_CHART_ID}"
        )


# ── Integration tests (require DATABASE_URL + seeded bodha_graph) ─────────────


@pytest.mark.integration
class TestAcceptanceGateIntegration:
    """
    Integration tests against a real DB.
    Run with: pytest -m integration tests/l2/test_bo22.py
    Requires: DATABASE_URL set + bodha_graph table created + native chart seeded.
    """

    def test_seed_then_gate_passes(self):
        """Seed native chart and confirm acceptance gate passes."""
        from brahmagyan.bodha.bo22 import run_acceptance_gate, seed_bodha_graph

        seed_bodha_graph(NATIVE_CHART_ID_EXPECTED, dry_run=False)
        result = run_acceptance_gate(NATIVE_CHART_ID_EXPECTED)
        assert result["gate_passed"], (
            f"Acceptance gate failed: {[c for c in result['checks'] if not c['passed']]}"
        )

    def test_traversal_saturn_mars_returns_edges(self):
        """PLN.SATURN + PLN.MARS traversal returns ≥3 edges with provenance."""
        from brahmagyan.bodha.bo22 import query_cgm_subgraph

        result = query_cgm_subgraph(
            NATIVE_CHART_ID_EXPECTED,
            signal_ids=["PLN.SATURN", "PLN.MARS"],
            hops=1,
        )
        assert result["edge_count"] >= 3, (
            f"Traversal on PLN.SATURN + PLN.MARS should return ≥3 edges; "
            f"got {result['edge_count']}"
        )
        for edge in result["edges"]:
            assert edge.get("source_citation", "").strip(), (
                f"Edge {edge['edge_id']} missing source_citation"
            )

    def test_no_self_loops_in_db(self):
        """Confirm no self-loops exist in the seeded bodha_graph."""
        import psycopg
        import os

        url = os.environ.get("DATABASE_URL", "")
        if not url:
            pytest.skip("DATABASE_URL not set")

        with psycopg.connect(url) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM bodha_graph "
                "WHERE chart_id = %s AND from_signal_id = to_signal_id",
                (NATIVE_CHART_ID_EXPECTED,),
            ).fetchone()
            self_loops = int(row[0]) if row else 0

        assert self_loops == 0, f"Found {self_loops} self-loop(s) in bodha_graph"
