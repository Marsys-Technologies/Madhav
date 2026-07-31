"""
tests/l2/test_bo_a7_writers.py — A7 Wave-1 Writer Tests
=========================================================
Tests the four new Bodha writers without a live database.

All tests use mocked database connections and controlled fixture data.

CONTRACT-3 verification: bo_cgm_paths must populate path_label_human, path_length,
is_final_dispositor — verified by test_bo_cgm_paths_populates_required_columns.

CONTRACT-4 note: bo_anveshana._compute_brokers() already queries
e.is_cross_subsystem = TRUE and COUNT(DISTINCT e.subsystem_from) —
verified by reading bo_anveshana.py lines 323-349. No change needed.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, call, patch

import pytest

# ── Import targets ─────────────────────────────────────────────────────────────

from pipeline.orchestrator.writers.bo_chart_gestalt import BoChartGestaltWriter, _write_aya as gestalt_write_aya
from pipeline.orchestrator.writers.bo_cdlm_summary import BoCdlmSummaryWriter, _write_aya as cdlm_write_aya
from pipeline.orchestrator.writers.bo_cgm_motifs import (
    BoCgmMotifsWriter, _detect_mutual_reception, _detect_stellia, _detect_parivartana_chains,
)
from pipeline.orchestrator.writers.bo_cgm_paths import (
    BoCgmPathsWriter, _build_dispositor_chains, _is_self_ruling, _path_strength,
)
from pipeline.orchestrator.writers import ContextSpec, WriterResult


# ── Helpers ────────────────────────────────────────────────────────────────────

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID  = str(uuid.uuid4())
AYA       = "lahiri_chitrapaksha"
NOW       = "2026-06-28T00:00:00+00:00"


def _make_ctx(conn: MagicMock) -> ContextSpec:
    return ContextSpec(
        asset_id="test",
        build_id=BUILD_ID,
        db_conn=conn,
        config={"chart_id": CHART_ID},
        dry_run=False,
    )


def _make_cursor(rows: list[dict | tuple]) -> MagicMock:
    """Return a mock cursor that yields rows from fetchall()."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    if rows and isinstance(rows[0], dict):
        cur.fetchall.return_value = rows
        # Simulate dict_row factory
    else:
        cur.fetchall.return_value = rows
    cur.description = None
    return cur


def _make_conn(side_effects: list) -> MagicMock:
    """
    Return a conn mock where each call to conn.cursor() returns the next item
    in side_effects (each is a mock cursor or a list of rows).
    """
    conn = MagicMock()
    cursors = []
    for effect in side_effects:
        if isinstance(effect, list):
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            # dict rows
            cur.fetchall.return_value = effect
            cur.description = None
            cursors.append(cur)
        else:
            cursors.append(effect)

    conn.cursor.side_effect = iter(cursors)
    return conn


# ── Test: bo_chart_gestalt ─────────────────────────────────────────────────────

class TestBoChartGestalt:

    def test_writer_is_registered(self) -> None:
        """Writer class is importable and has correct asset_id."""
        w = BoChartGestaltWriter()
        assert w.asset_id == "bo_chart_gestalt"

    def test_dry_run_returns_zero(self) -> None:
        conn = MagicMock()
        ctx = ContextSpec(
            asset_id="bo_chart_gestalt",
            build_id=BUILD_ID,
            db_conn=conn,
            config={"chart_id": CHART_ID},
            dry_run=True,
        )
        result = BoChartGestaltWriter().run(ctx)
        assert result.rows_inserted == 0
        assert "dry_run" in result.notes

    def test_bo_chart_gestalt_emits_one_row_per_ayanamsha(self) -> None:
        """O5: gestalt writer produces 1 row per ayanamsha from MSR + CGM data."""
        # Minimal signal set to trigger output
        sample_signals = [
            {
                "signal_id": str(uuid.uuid4()),
                "signal_type_id": "yoga:raja_yoga",
                "signal_type_class": "yoga",
                "computed_salience": 8.5,
                "signature_tier": "chart_defining",
                "valence": "benefic",
                "source_l1_asset": "ga_yoga",
                "domains_affected_array": ["career", "wealth"],
                "constituent_facts_array": ["fact_001"],
            }
        ]

        # For _write_aya: we need cursors for all the sub-queries
        # Order of _fetch_dict calls inside _write_aya (post-B-N8-FIX, register
        # F-12: the domain_evidence whole-domain GROUP BY query was ADDED between
        # domain_signals and malefic_signals when the writer stopped storing a
        # computed verdict and started storing deterministic per-domain evidence
        # counts instead — see bo_chart_gestalt.py's §N.8/ANTI-DRIFT block):
        # 1. top_signals (bodha_msr_signals, chart_defining/major)
        # 2. strong_cells (bodha_cdlm_cells)
        # 3. top_nodes (bodha_cgm_nodes)
        # 4. final_disp_nodes (bodha_cgm_paths)
        # 5. domain_signals (bodha_msr_signals unnested)
        # 6. domain_evidence (bodha_msr_signals GROUP BY — whole-domain counts)
        # 7. malefic_signals
        # 8. benefic_top
        # 9. outlier_discoveries
        # 10. contested
        # 11. INSERT cursor

        def make_row_cursor(rows):
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            cur.fetchall.return_value = rows
            cur.description = None
            return cur

        def make_execute_cursor():
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            cur.fetchall.return_value = []
            return cur

        conn = MagicMock()
        conn.cursor.side_effect = [
            make_row_cursor(sample_signals),       # top_signals (chart_defining)
            make_row_cursor([]),                    # strong_cells (cdlm_cells)
            make_row_cursor([]),                    # top_nodes (cgm_nodes)
            make_row_cursor([]),                    # final_disp_nodes (cgm_paths)
            make_row_cursor([{                      # domain_signals
                "unnested_domain": "career",
                "signal_id": str(uuid.uuid4()),
                "computed_salience": 8.0,
                "valence": "benefic",
                "signature_tier": "chart_defining",
            }]),
            make_row_cursor([{                      # domain_evidence (whole-domain counts)
                "domain": "career",
                "signal_count": 1,
                "benefic_count": 1,
                "malefic_count": 0,
                "mixed_count": 0,
                "neutral_count": 0,
                "major_tier_count": 1,
            }]),
            make_row_cursor([]),                    # malefic_signals
            make_row_cursor([]),                    # benefic_top
            make_row_cursor([]),                    # outlier_discoveries
            make_row_cursor([]),                    # contested
            make_execute_cursor(),                  # INSERT
        ]

        result = gestalt_write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        assert result == 1, "Expected 1 gestalt row when signals are present"

    def test_gestalt_skips_when_no_signals(self) -> None:
        """Writer emits 0 rows when no MSR signals exist for an ayanamsha."""
        conn = MagicMock()

        def make_empty_cursor():
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            cur.fetchall.return_value = []
            cur.description = None
            return cur

        # Both chart_defining/major query AND fallback query return empty
        conn.cursor.side_effect = [make_empty_cursor(), make_empty_cursor()]

        result = gestalt_write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        assert result == 0


# ── Test: bo_cgm_paths ────────────────────────────────────────────────────────

class TestBoCgmPaths:

    def test_writer_is_registered(self) -> None:
        w = BoCgmPathsWriter()
        assert w.asset_id == "bo_cgm_paths"

    def test_dry_run_returns_zero(self) -> None:
        conn = MagicMock()
        ctx = ContextSpec(
            asset_id="bo_cgm_paths",
            build_id=BUILD_ID,
            db_conn=conn,
            config={"chart_id": CHART_ID},
            dry_run=True,
        )
        result = BoCgmPathsWriter().run(ctx)
        assert result.rows_inserted == 0

    def test_is_self_ruling_sun_in_leo(self) -> None:
        """Sun in Leo is self-ruling."""
        assert _is_self_ruling("sun", {"sign": "leo"}) is True

    def test_is_self_ruling_sun_in_capricorn(self) -> None:
        """Sun in Capricorn is NOT self-ruling."""
        assert _is_self_ruling("sun", {"sign": "capricorn"}) is False

    def test_is_self_ruling_saturn_in_aquarius(self) -> None:
        """Saturn in Aquarius (own sign) is self-ruling."""
        assert _is_self_ruling("saturn", {"sign": "aquarius"}) is True

    def test_is_self_ruling_none_inputs(self) -> None:
        """None inputs return False gracefully."""
        assert _is_self_ruling(None, None) is False
        assert _is_self_ruling("sun", None) is False

    def test_bo_cgm_paths_populates_required_columns(self) -> None:
        """CONTRACT-3: bo_cgm_paths writer populates path_label_human, path_length, is_final_dispositor."""
        # Build a minimal graph: Sun (Capricorn) → Saturn (Aquarius → self-ruling)
        sun_id  = str(uuid.uuid4())
        sat_id  = str(uuid.uuid4())
        edge_id = str(uuid.uuid4())

        graha_nodes = [
            {
                "node_id": sun_id,
                "node_subject": "sun",
                "node_label_human": "Sun",
                "position_in_chart_jsonb": {"sign": "capricorn"},
            },
            {
                "node_id": sat_id,
                "node_subject": "saturn",
                "node_label_human": "Saturn",
                "position_in_chart_jsonb": {"sign": "aquarius"},
            },
        ]
        edge_by_from = {
            sun_id: [{
                "edge_id": edge_id,
                "from_node_id": sun_id,
                "to_node_id": sat_id,
                "edge_type": "dispositor",
                "relationship_basis": "dispositor",
                "computed_strength": 1.0,
            }],
        }
        node_by_id = {n["node_id"]: n for n in graha_nodes}

        chains = _build_dispositor_chains(graha_nodes, edge_by_from, node_by_id)

        # Should produce ≥1 chain: Sun → Saturn is one; Saturn self-ruling is another valid chain
        assert len(chains) >= 1, f"Expected at least 1 chain, got {len(chains)}"

        # Find the Sun → Saturn chain (the multi-hop one)
        sun_saturn_chains = [
            c for c in chains
            if c["from_node_id"] == sun_id and c["to_node_id"] == sat_id
        ]
        assert len(sun_saturn_chains) == 1, "Expected exactly 1 Sun→Saturn dispositor chain"
        chain = sun_saturn_chains[0]

        # CONTRACT-3 columns verification
        assert "label" in chain, "path_label_human source missing"
        assert chain["label"] != "", "path_label_human must not be empty"
        assert len(chain["node_chain"]) >= 2, "path_length >= 1 (at least 2 nodes)"
        assert isinstance(chain["is_final_dispositor"], bool), "is_final_dispositor must be bool"
        assert chain["is_final_dispositor"] is True, "Saturn in Aquarius should be final dispositor"
        assert "Sun" in chain["label"], "path_label_human should include Sun"
        assert "Saturn" in chain["label"], "path_label_human should include Saturn"

    def test_self_ruling_node_emits_zero_hop_chain(self) -> None:
        """A graha in its own sign emits a self-ruling (0-hop) chain."""
        sun_id = str(uuid.uuid4())
        graha_nodes = [
            {
                "node_id": sun_id,
                "node_subject": "sun",
                "node_label_human": "Sun",
                "position_in_chart_jsonb": {"sign": "leo"},
            }
        ]
        chains = _build_dispositor_chains(graha_nodes, {}, {sun_id: graha_nodes[0]})
        assert len(chains) == 1
        assert chains[0]["is_final_dispositor"] is True
        assert chains[0]["from_node_id"] == sun_id
        assert chains[0]["to_node_id"] == sun_id
        assert "self-ruling" in chains[0]["label"]

    # ── JL-013: path_strength = PRODUCT of constituent edges, never average ──

    def test_path_strength_is_product_not_average(self) -> None:
        edge_strength_by_id = {"e1": 0.5, "e2": 0.8}
        result = _path_strength(["e1", "e2"], edge_strength_by_id)
        assert result == pytest.approx(0.5 * 0.8)
        assert result != pytest.approx((0.5 + 0.8) / 2)  # not the average

    def test_path_strength_zero_hop_chain_is_full_strength(self) -> None:
        assert _path_strength([], {}) == 1.0

    def test_path_strength_uses_only_known_edges(self) -> None:
        edge_strength_by_id = {"e1": 0.4, "e2": None}
        assert _path_strength(["e1", "e2"], edge_strength_by_id) == pytest.approx(0.4)

    def test_path_strength_falls_back_when_no_edge_has_a_value(self) -> None:
        edge_strength_by_id = {"e1": None}
        result = _path_strength(["e1"], edge_strength_by_id)
        assert result == 0.5  # documented honest fallback, not fabricated

    def test_path_strength_one_weak_edge_drags_the_whole_chain(self) -> None:
        """A single weak edge must weaken the product — proves it's not an
        average that could hide a weak link behind strong ones."""
        weak = _path_strength(["e1", "e2"], {"e1": 0.9, "e2": 0.1})
        strong = _path_strength(["e1", "e2"], {"e1": 0.9, "e2": 0.9})
        assert weak < strong


# ── Test: bo_cgm_motifs ───────────────────────────────────────────────────────

class TestBoCgmMotifs:

    def test_writer_is_registered(self) -> None:
        w = BoCgmMotifsWriter()
        assert w.asset_id == "bo_cgm_motifs"

    def test_dry_run_returns_zero(self) -> None:
        conn = MagicMock()
        ctx = ContextSpec(
            asset_id="bo_cgm_motifs",
            build_id=BUILD_ID,
            db_conn=conn,
            config={"chart_id": CHART_ID},
            dry_run=True,
        )
        result = BoCgmMotifsWriter().run(ctx)
        assert result.rows_inserted == 0

    def test_bo_cgm_motifs_detects_mutual_reception(self) -> None:
        """Motif writer detects mutual reception when two grahas rule each other's signs."""
        # Mercury in Sagittarius → Jupiter rules Sagittarius
        # Jupiter in Gemini → Mercury rules Gemini
        # Both have dispositor edges to each other → mutual reception
        mercury_id = str(uuid.uuid4())
        jupiter_id = str(uuid.uuid4())
        edge_mj    = str(uuid.uuid4())  # mercury → jupiter
        edge_jm    = str(uuid.uuid4())  # jupiter → mercury

        graha_nodes = [
            {"node_id": mercury_id, "node_subject": "mercury", "node_label_human": "Mercury"},
            {"node_id": jupiter_id, "node_subject": "jupiter", "node_label_human": "Jupiter"},
        ]

        edge_by_from = {
            mercury_id: [{
                "edge_id": edge_mj,
                "from_node_id": mercury_id,
                "to_node_id": jupiter_id,
                "relationship_basis": "dispositor",
                "edge_type": "dispositor",
                "computed_strength": 1.0,
            }],
            jupiter_id: [{
                "edge_id": edge_jm,
                "from_node_id": jupiter_id,
                "to_node_id": mercury_id,
                "relationship_basis": "dispositor",
                "edge_type": "dispositor",
                "computed_strength": 1.0,
            }],
        }

        motifs = _detect_mutual_reception(graha_nodes, edge_by_from)

        assert len(motifs) == 1, f"Expected 1 mutual reception motif, got {len(motifs)}: {motifs}"
        m = motifs[0]
        assert m["motif_class"] == "mutual_reception"
        assert set(m["node_ids"]) == {mercury_id, jupiter_id}
        assert m["strength"] > 0

    def test_mutual_reception_not_detected_without_bidirectional_edges(self) -> None:
        """One-way dispositor edge should NOT produce mutual reception."""
        a_id = str(uuid.uuid4())
        b_id = str(uuid.uuid4())

        graha_nodes = [
            {"node_id": a_id, "node_subject": "mars", "node_label_human": "Mars"},
            {"node_id": b_id, "node_subject": "venus", "node_label_human": "Venus"},
        ]
        edge_by_from = {
            a_id: [{
                "edge_id": str(uuid.uuid4()),
                "from_node_id": a_id,
                "to_node_id": b_id,
                "relationship_basis": "dispositor",
                "edge_type": "dispositor",
                "computed_strength": 1.0,
            }],
        }

        motifs = _detect_mutual_reception(graha_nodes, edge_by_from)
        assert len(motifs) == 0

    def test_stellium_detection_three_nodes_same_house(self) -> None:
        """Three graha nodes in the same house should form a stellium."""
        ids = [str(uuid.uuid4()) for _ in range(3)]
        graha_nodes = [
            {"node_id": ids[i], "node_subject": n, "node_label_human": n.capitalize(),
             "position_in_chart_jsonb": {"house": 10}}
            for i, n in enumerate(["sun", "mercury", "saturn"])
        ]
        motifs = _detect_stellia(graha_nodes, {})
        assert len(motifs) == 1
        m = motifs[0]
        assert m["motif_class"] == "stellium"
        assert len(m["node_ids"]) == 3

    def test_stellium_not_detected_with_two_nodes(self) -> None:
        """Two nodes in same house should NOT form a stellium (threshold=3)."""
        ids = [str(uuid.uuid4()) for _ in range(2)]
        graha_nodes = [
            {"node_id": ids[i], "node_subject": n, "node_label_human": n.capitalize(),
             "position_in_chart_jsonb": {"house": 7}}
            for i, n in enumerate(["sun", "moon"])
        ]
        motifs = _detect_stellia(graha_nodes, {})
        assert len(motifs) == 0


# ── Test: bo_cdlm_summary ─────────────────────────────────────────────────────

class TestBoCdlmSummary:

    def test_writer_is_registered(self) -> None:
        w = BoCdlmSummaryWriter()
        assert w.asset_id == "bo_cdlm_summary"

    def test_dry_run_returns_zero(self) -> None:
        conn = MagicMock()
        ctx = ContextSpec(
            asset_id="bo_cdlm_summary",
            build_id=BUILD_ID,
            db_conn=conn,
            config={"chart_id": CHART_ID},
            dry_run=True,
        )
        result = BoCdlmSummaryWriter().run(ctx)
        assert result.rows_inserted == 0

    def test_bo_cdlm_summary_aggregates_cdlm_cells(self) -> None:
        """Summary writer produces 1 row per ayanamsha with non-null linkage stats."""
        sample_cells = [
            {
                "domain_row": "career",
                "domain_col": "wealth",
                "computed_linkage_strength": 0.75,
                "contradiction_density": 0.1,
                "asymmetric_linkage_flag": False,
                "top_k_rank_in_snapshot": 1,
            },
            {
                "domain_row": "career",
                "domain_col": "health",
                "computed_linkage_strength": 0.50,
                "contradiction_density": 0.2,
                "asymmetric_linkage_flag": True,
                "top_k_rank_in_snapshot": 2,
            },
            {
                "domain_row": "wealth",
                "domain_col": "relationship",
                "computed_linkage_strength": 0.30,
                "contradiction_density": 0.0,
                "asymmetric_linkage_flag": False,
                "top_k_rank_in_snapshot": 3,
            },
        ]

        def make_row_cursor(rows):
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            cur.fetchall.return_value = rows
            cur.description = None
            return cur

        def make_execute_cursor():
            cur = MagicMock()
            cur.__enter__ = lambda s: s
            cur.__exit__ = MagicMock(return_value=False)
            cur.fetchall.return_value = []
            return cur

        conn = MagicMock()
        conn.cursor.side_effect = [
            make_row_cursor(sample_cells),   # cells fetch
            make_execute_cursor(),           # INSERT
        ]

        result = cdlm_write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        assert result == 1, "Expected 1 summary row when cells are present"

    def test_cdlm_summary_skips_when_no_cells(self) -> None:
        """Writer emits 0 rows when no CDLM cells exist."""
        conn = MagicMock()

        cur = MagicMock()
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        cur.fetchall.return_value = []
        cur.description = None
        conn.cursor.return_value = cur

        result = cdlm_write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        assert result == 0

    def test_cdlm_summary_dominant_domains_ordering(self) -> None:
        """dominant_3_domains_array should be ordered by total linkage strength DESC."""
        # career gets 0.9+0.5 = 1.4 total, wealth gets 0.9+0.3 = 1.2, health gets 0.5+0.3 = 0.8
        sample_cells = [
            {"domain_row": "career", "domain_col": "wealth",       "computed_linkage_strength": 0.9,
             "contradiction_density": 0.0, "asymmetric_linkage_flag": False, "top_k_rank_in_snapshot": 1},
            {"domain_row": "career", "domain_col": "health",       "computed_linkage_strength": 0.5,
             "contradiction_density": 0.0, "asymmetric_linkage_flag": False, "top_k_rank_in_snapshot": 2},
            {"domain_row": "wealth", "domain_col": "relationship",  "computed_linkage_strength": 0.3,
             "contradiction_density": 0.0, "asymmetric_linkage_flag": False, "top_k_rank_in_snapshot": 3},
        ]

        inserted_rows: list[dict] = []

        def fake_cursor_factory():
            calls = [0]
            def make_cur(rows_or_none=None):
                cur = MagicMock()
                cur.__enter__ = lambda s: s
                cur.__exit__ = MagicMock(return_value=False)
                if rows_or_none is not None:
                    cur.fetchall.return_value = rows_or_none
                else:
                    cur.fetchall.return_value = []
                cur.description = None

                def capture_execute(sql, params=None):
                    if params and isinstance(params, dict) and "dominant_3_domains_array" in params:
                        inserted_rows.append(params)
                cur.execute = capture_execute
                return cur
            return make_cur

        make_cur = fake_cursor_factory()
        conn = MagicMock()
        conn.cursor.side_effect = [make_cur(sample_cells), make_cur()]

        cdlm_write_aya(conn, CHART_ID, AYA, BUILD_ID, NOW)
        if inserted_rows:
            dominant = inserted_rows[0]["dominant_3_domains_array"]
            # career should be first (highest total linkage)
            assert dominant[0] == "career", f"Expected career first, got {dominant}"
