"""
UTEE-S3/S4 unit tests — no DB required.
Tests cover:
  - Migration SQL file existence and structure (UTEE-S3)
  - Query function existence and signatures (UTEE-S4)
  - Tool manifest completeness (UTEE-S4)
UTEE-S3/S4 [BUILD-ORCH-STREAM-D-UTEE-S3-S4]
"""
import inspect
import os
import sys

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
MIGRATIONS_DIR = os.path.join(REPO_ROOT, "platform", "migrations")
QUERY_DIR = os.path.join(
    REPO_ROOT, "platform", "python-sidecar", "pipeline", "query"
)
sys.path.insert(0, os.path.join(REPO_ROOT, "platform", "python-sidecar"))

VIEW_SQL_PATH = os.path.join(MIGRATIONS_DIR, "151_temporal_unified_lattice_view.sql")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_view_sql() -> str:
    with open(VIEW_SQL_PATH, "r") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
# UTEE-S3: vw_temporal_unified_lattice migration SQL
# ══════════════════════════════════════════════════════════════════════════════

class TestUteeS3ViewSqlExists:
    """T1: Migration SQL file exists."""

    def test_migration_file_exists(self):
        assert os.path.isfile(VIEW_SQL_PATH), (
            f"Migration file not found: {VIEW_SQL_PATH}"
        )


class TestUteeS3ViewSqlContent:
    """T2-T8: View SQL has CREATE OR REPLACE VIEW and all 7 source asset labels."""

    def test_create_or_replace_view_statement(self):
        sql = _read_view_sql()
        assert "CREATE OR REPLACE VIEW vw_temporal_unified_lattice" in sql

    def test_source_asset_a15(self):
        assert "'A15'" in _read_view_sql()

    def test_source_asset_a16(self):
        assert "'A16'" in _read_view_sql()

    def test_source_asset_a18(self):
        assert "'A18'" in _read_view_sql()

    def test_source_asset_a19(self):
        assert "'A19'" in _read_view_sql()

    def test_source_asset_a20(self):
        assert "'A20'" in _read_view_sql()

    def test_source_asset_a21(self):
        assert "'A21'" in _read_view_sql()

    def test_source_asset_a22(self):
        assert "'A22'" in _read_view_sql()


class TestUteeS3ViewSqlColumns:
    """T9-T13: View SQL references required UTEE columns."""

    def test_has_source_row_id_column(self):
        assert "source_row_id" in _read_view_sql()

    def test_has_event_iso_column(self):
        assert "event_iso" in _read_view_sql()

    def test_has_severity_normalized_0_1_column(self):
        assert "severity_normalized_0_1" in _read_view_sql()

    def test_has_confidence_normalized_0_1_column(self):
        assert "confidence_normalized_0_1" in _read_view_sql()

    def test_has_m6_outcome_tracking_placeholder_jsonb_column(self):
        assert "m6_outcome_tracking_placeholder_jsonb" in _read_view_sql()


class TestUteeS3ViewSqlUnion:
    """T14-T16: View SQL uses UNION ALL correctly."""

    def test_has_six_union_all_statements(self):
        sql = _read_view_sql()
        # 7 subqueries need 6 UNION ALL connectors
        count = sql.upper().count("UNION ALL")
        assert count == 6, f"Expected 6 UNION ALL, found {count}"

    def test_has_comment_on_view(self):
        assert "COMMENT ON VIEW vw_temporal_unified_lattice" in _read_view_sql()

    def test_view_references_all_seven_source_tables(self):
        sql = _read_view_sql()
        expected_tables = [
            "l1_time_synchronicity",
            "l1_phase_locked_anchors",
            "l1_vedha_extended",
            "l1_bhrigu_bindu_transits",
            "l1_tajik_varsha_year_lords",
            "l1_graha_aspects_lifetime",
            "l1_varsha_digest",
        ]
        for table in expected_tables:
            assert table in sql, f"Table not referenced in view SQL: {table}"


# ══════════════════════════════════════════════════════════════════════════════
# UTEE-S4: Query module imports and function signatures
# ══════════════════════════════════════════════════════════════════════════════

class TestUteeS4ModuleImport:
    """T17: query_temporal_events module imports without error."""

    def test_module_importable(self):
        from pipeline.query import query_temporal_events  # noqa: F401


class TestUteeS4FunctionSignatures:
    """T18-T23: All 6 query functions exist and have correct required parameters."""

    def _get_module(self):
        from pipeline.query import query_temporal_events
        return query_temporal_events

    def test_query_temporal_events_in_range_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_events_in_range", None))

    def test_query_temporal_events_in_range_params(self):
        from pipeline.query.query_temporal_events import query_temporal_events_in_range
        sig = inspect.signature(query_temporal_events_in_range)
        params = list(sig.parameters.keys())
        for required in ("conn", "chart_id", "ayanamsha_id", "start_iso", "end_iso"):
            assert required in params, f"Missing param '{required}' in query_temporal_events_in_range"

    def test_query_temporal_events_next_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_events_next", None))

    def test_query_temporal_events_next_params(self):
        from pipeline.query.query_temporal_events import query_temporal_events_next
        sig = inspect.signature(query_temporal_events_next)
        params = list(sig.parameters.keys())
        for required in ("conn", "chart_id", "ayanamsha_id", "from_date"):
            assert required in params, f"Missing param '{required}' in query_temporal_events_next"

    def test_query_temporal_events_within_a15_cluster_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_events_within_a15_cluster", None))

    def test_query_temporal_events_within_a15_cluster_params(self):
        from pipeline.query.query_temporal_events import query_temporal_events_within_a15_cluster
        sig = inspect.signature(query_temporal_events_within_a15_cluster)
        params = list(sig.parameters.keys())
        assert "conn" in params
        assert "cluster_id" in params

    def test_query_temporal_events_seeded_by_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_events_seeded_by", None))

    def test_query_temporal_events_seeded_by_params(self):
        from pipeline.query.query_temporal_events import query_temporal_events_seeded_by
        sig = inspect.signature(query_temporal_events_seeded_by)
        params = list(sig.parameters.keys())
        assert "conn" in params
        assert "seed_event_id" in params

    def test_query_temporal_events_mitigated_by_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_events_mitigated_by", None))

    def test_query_temporal_events_mitigated_by_params(self):
        from pipeline.query.query_temporal_events import query_temporal_events_mitigated_by
        sig = inspect.signature(query_temporal_events_mitigated_by)
        params = list(sig.parameters.keys())
        assert "conn" in params
        assert "vedha_id" in params

    def test_query_temporal_event_peers_exists(self):
        mod = self._get_module()
        assert callable(getattr(mod, "query_temporal_event_peers", None))

    def test_query_temporal_event_peers_params(self):
        from pipeline.query.query_temporal_events import query_temporal_event_peers
        sig = inspect.signature(query_temporal_event_peers)
        params = list(sig.parameters.keys())
        for required in ("conn", "chart_id", "ayanamsha_id", "source_asset", "source_row_id"):
            assert required in params, f"Missing param '{required}' in query_temporal_event_peers"


# ══════════════════════════════════════════════════════════════════════════════
# UTEE-S4: UTEE_SELECT_COLS content checks
# ══════════════════════════════════════════════════════════════════════════════

class TestUteeS4SelectCols:
    """T24-T26: UTEE_SELECT_COLS contains required fields."""

    def _get_cols(self) -> str:
        from pipeline.query.query_temporal_events import UTEE_SELECT_COLS
        return UTEE_SELECT_COLS

    def test_utee_select_cols_has_source_asset(self):
        assert "source_asset" in self._get_cols()

    def test_utee_select_cols_has_event_iso(self):
        assert "event_iso" in self._get_cols()

    def test_utee_select_cols_has_severity_normalized(self):
        assert "severity_normalized_0_1" in self._get_cols()


# ══════════════════════════════════════════════════════════════════════════════
# UTEE-S4: Tool manifest checks
# ══════════════════════════════════════════════════════════════════════════════

class TestUteeS4ToolManifest:
    """T27-T32: temporal_tools_manifest has 6 tool entries with required fields."""

    def _get_tools(self):
        from pipeline.query.temporal_tools_manifest import TEMPORAL_EVENT_TOOLS
        return TEMPORAL_EVENT_TOOLS

    def test_manifest_has_six_tools(self):
        tools = self._get_tools()
        assert len(tools) == 6, f"Expected 6 tools, got {len(tools)}"

    def test_all_tools_have_tool_id(self):
        for tool in self._get_tools():
            assert "tool_id" in tool, f"Tool missing tool_id: {tool}"

    def test_all_tools_have_description(self):
        for tool in self._get_tools():
            assert "description" in tool and tool["description"], (
                f"Tool missing description: {tool.get('tool_id')}"
            )

    def test_all_tools_have_channels(self):
        for tool in self._get_tools():
            assert "channels" in tool and len(tool["channels"]) > 0, (
                f"Tool missing channels: {tool.get('tool_id')}"
            )

    def test_all_tools_have_tiers(self):
        for tool in self._get_tools():
            assert "tiers" in tool and len(tool["tiers"]) > 0, (
                f"Tool missing tiers: {tool.get('tool_id')}"
            )

    def test_tool_ids_are_unique(self):
        tools = self._get_tools()
        ids = [t["tool_id"] for t in tools]
        assert len(ids) == len(set(ids)), f"Duplicate tool_ids found: {ids}"

    def test_all_tools_have_asset_id_meta_zeta(self):
        for tool in self._get_tools():
            assert tool.get("asset_id") == "META-ζ", (
                f"Tool {tool.get('tool_id')} has wrong asset_id: {tool.get('asset_id')}"
            )

    def test_expected_tool_ids_present(self):
        tools = self._get_tools()
        tool_ids = {t["tool_id"] for t in tools}
        expected = {
            "query_temporal_events_in_range",
            "query_temporal_events_next",
            "query_temporal_events_within_a15_cluster",
            "query_temporal_events_seeded_by",
            "query_temporal_events_mitigated_by",
            "query_temporal_event_peers",
        }
        assert expected == tool_ids, (
            f"Tool ID mismatch. Missing: {expected - tool_ids}. Extra: {tool_ids - expected}"
        )
