"""Tests for META-β/γ/δ/ε: pattern_catalog + divergence_ledger + negative_space + derivation_graph.

All tests are pure unit tests (no DB required).
Covers:
  - Migration SQL file integrity (5 tables present)
  - PATTERN_KINDS list completeness (>=16 entries)
  - ABSENCE_DETECTORS structure and keys
  - DIVERGENCE_RULES structure
  - Query function signatures and existence (8 functions)
  - Writer function signatures and existence (9 functions)
Total: >= 26 tests
"""
import importlib
import inspect
import os
import re
import sys
import types

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)

# migrations live under platform/migrations/ relative to repo root
MIGRATION_PATH = os.path.join(
    REPO_ROOT, "platform", "migrations", "153_meta_beta_gamma_delta_epsilon.sql"
)

WRITERS_PKG = os.path.join(REPO_ROOT, "python-sidecar", "pipeline", "writers")
QUERY_PKG = os.path.join(REPO_ROOT, "python-sidecar", "pipeline", "query")

sys.path.insert(0, os.path.join(REPO_ROOT, "python-sidecar"))

# ---------------------------------------------------------------------------
# 1. Migration SQL file integrity (5 tests)
# ---------------------------------------------------------------------------

class TestMigrationFile:
    """Verify migration 153 exists and contains all 5 required tables."""

    def test_migration_file_exists(self):
        assert os.path.isfile(MIGRATION_PATH), (
            f"Migration file not found at {MIGRATION_PATH}"
        )

    def test_migration_has_pattern_catalog_table(self):
        sql = open(MIGRATION_PATH).read()
        assert "l25_pattern_catalog" in sql

    def test_migration_has_divergence_ledger_table(self):
        sql = open(MIGRATION_PATH).read()
        assert "l25_divergence_ledger" in sql

    def test_migration_has_negative_space_map_table(self):
        sql = open(MIGRATION_PATH).read()
        assert "l25_negative_space_map" in sql

    def test_migration_has_derivation_graph_nodes_table(self):
        sql = open(MIGRATION_PATH).read()
        assert "l25_derivation_graph_nodes" in sql

    def test_migration_has_derivation_graph_edges_table(self):
        sql = open(MIGRATION_PATH).read()
        assert "l25_derivation_graph_edges" in sql

    def test_migration_all_tables_idempotent(self):
        sql = open(MIGRATION_PATH).read()
        # All CREATE TABLE statements should be IF NOT EXISTS
        tables = re.findall(r"CREATE TABLE\s+(IF NOT EXISTS\s+)?(\w+)", sql, re.IGNORECASE)
        for (guard, name) in tables:
            assert guard.strip().upper() == "IF NOT EXISTS", (
                f"Table {name!r} is missing IF NOT EXISTS guard"
            )

    def test_migration_all_indexes_idempotent(self):
        sql = open(MIGRATION_PATH).read()
        indexes = re.findall(r"CREATE INDEX\s+(IF NOT EXISTS\s+)?(\w+)", sql, re.IGNORECASE)
        for (guard, name) in indexes:
            assert guard.strip().upper() == "IF NOT EXISTS", (
                f"Index {name!r} is missing IF NOT EXISTS guard"
            )

    def test_migration_has_fk_on_edges(self):
        sql = open(MIGRATION_PATH).read()
        assert "REFERENCES l25_derivation_graph_nodes" in sql


# ---------------------------------------------------------------------------
# 2. PATTERN_KINDS list completeness (2 tests)
# ---------------------------------------------------------------------------

class TestPatternKinds:
    """META-β pattern_catalog_writer PATTERN_KINDS list."""

    @pytest.fixture(autouse=True)
    def _load(self):
        from pipeline.writers.pattern_catalog_writer import PATTERN_KINDS
        self.PATTERN_KINDS = PATTERN_KINDS

    def test_pattern_kinds_has_at_least_16_entries(self):
        assert len(self.PATTERN_KINDS) >= 16

    def test_pattern_kinds_contains_yoga(self):
        assert "yoga" in self.PATTERN_KINDS

    def test_pattern_kinds_contains_dosha(self):
        assert "dosha" in self.PATTERN_KINDS

    def test_pattern_kinds_contains_synchronicity(self):
        assert "synchronicity" in self.PATTERN_KINDS

    def test_pattern_kinds_contains_phase_locked_anchor(self):
        assert "phase_locked_anchor" in self.PATTERN_KINDS

    def test_pattern_kinds_contains_negative_space(self):
        assert "negative_space" in self.PATTERN_KINDS

    def test_pattern_kinds_no_duplicates(self):
        assert len(self.PATTERN_KINDS) == len(set(self.PATTERN_KINDS))


# ---------------------------------------------------------------------------
# 3. ABSENCE_DETECTORS structure (4 tests)
# ---------------------------------------------------------------------------

class TestAbsenceDetectors:
    """META-δ negative_space_writer ABSENCE_DETECTORS list."""

    @pytest.fixture(autouse=True)
    def _load(self):
        from pipeline.writers.negative_space_writer import ABSENCE_DETECTORS
        self.ABSENCE_DETECTORS = ABSENCE_DETECTORS

    def test_absence_detectors_is_list(self):
        assert isinstance(self.ABSENCE_DETECTORS, list)

    def test_absence_detectors_has_at_least_4_entries(self):
        assert len(self.ABSENCE_DETECTORS) >= 4

    def test_absence_detectors_all_have_required_keys(self):
        required_keys = {'class', 'feature', 'significance', 'expected', 'classical'}
        for entry in self.ABSENCE_DETECTORS:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Entry missing keys {missing}: {entry}"

    def test_absence_detectors_significance_values_valid(self):
        valid = {'high', 'medium', 'low'}
        for entry in self.ABSENCE_DETECTORS:
            assert entry['significance'] in valid, (
                f"Invalid significance {entry['significance']!r} in entry {entry['class']!r}"
            )

    def test_absence_detectors_no_empty_class(self):
        for entry in self.ABSENCE_DETECTORS:
            assert entry['class'], "Empty 'class' key in ABSENCE_DETECTORS entry"

    def test_absence_detectors_no_empty_feature(self):
        for entry in self.ABSENCE_DETECTORS:
            assert entry['feature'], "Empty 'feature' key in ABSENCE_DETECTORS entry"


# ---------------------------------------------------------------------------
# 4. DIVERGENCE_RULES structure (3 tests)
# ---------------------------------------------------------------------------

class TestDivergenceRules:
    """META-γ divergence_ledger_writer DIVERGENCE_RULES list."""

    @pytest.fixture(autouse=True)
    def _load(self):
        from pipeline.writers.divergence_ledger_writer import DIVERGENCE_RULES
        self.DIVERGENCE_RULES = DIVERGENCE_RULES

    def test_divergence_rules_is_list(self):
        assert isinstance(self.DIVERGENCE_RULES, list)

    def test_divergence_rules_has_at_least_2_entries(self):
        assert len(self.DIVERGENCE_RULES) >= 2

    def test_divergence_rules_all_have_required_keys(self):
        required_keys = {'divergence_class', 'system_a', 'system_b', 'description'}
        for entry in self.DIVERGENCE_RULES:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Entry missing keys {missing}: {entry}"

    def test_divergence_rules_contains_ayanamsha_class(self):
        classes = [r['divergence_class'] for r in self.DIVERGENCE_RULES]
        assert 'ayanamsha_positional_disagreement' in classes

    def test_divergence_rules_contains_tradition_class(self):
        classes = [r['divergence_class'] for r in self.DIVERGENCE_RULES]
        assert 'tradition_interpretation_disagreement' in classes


# ---------------------------------------------------------------------------
# 5. Query function signatures (8 functions)
# ---------------------------------------------------------------------------

class TestQueryFunctions:
    """META-β/γ/δ/ε query_meta_synthesis function existence and signatures."""

    @pytest.fixture(autouse=True)
    def _load(self):
        from pipeline.query import query_meta_synthesis as qm
        self.qm = qm

    def test_query_patterns_exists(self):
        assert hasattr(self.qm, "query_patterns")
        assert callable(self.qm.query_patterns)

    def test_query_patterns_signature(self):
        sig = inspect.signature(self.qm.query_patterns)
        params = list(sig.parameters)
        assert "conn" in params
        assert "chart_id" in params
        assert "ayanamsha_id" in params

    def test_query_pattern_links_exists(self):
        assert hasattr(self.qm, "query_pattern_links")
        assert callable(self.qm.query_pattern_links)

    def test_query_pattern_peers_exists(self):
        assert hasattr(self.qm, "query_pattern_peers")
        assert callable(self.qm.query_pattern_peers)

    def test_query_divergences_exists(self):
        assert hasattr(self.qm, "query_divergences")
        assert callable(self.qm.query_divergences)

    def test_query_divergences_signature(self):
        sig = inspect.signature(self.qm.query_divergences)
        params = list(sig.parameters)
        assert "conn" in params
        assert "chart_id" in params
        assert "status" in params

    def test_query_divergence_at_structural_point_exists(self):
        assert hasattr(self.qm, "query_divergence_at_structural_point")
        assert callable(self.qm.query_divergence_at_structural_point)

    def test_query_negative_space_exists(self):
        assert hasattr(self.qm, "query_negative_space")
        assert callable(self.qm.query_negative_space)

    def test_query_negative_space_signature(self):
        sig = inspect.signature(self.qm.query_negative_space)
        params = list(sig.parameters)
        assert "significance" in params

    def test_query_distinctive_absences_exists(self):
        assert hasattr(self.qm, "query_distinctive_absences")
        assert callable(self.qm.query_distinctive_absences)

    def test_query_derivation_trail_exists(self):
        assert hasattr(self.qm, "query_derivation_trail")
        assert callable(self.qm.query_derivation_trail)

    def test_query_derivation_upstream_exists(self):
        assert hasattr(self.qm, "query_derivation_upstream")
        assert callable(self.qm.query_derivation_upstream)

    def test_query_supporting_l1_facts_exists(self):
        assert hasattr(self.qm, "query_supporting_l1_facts")
        assert callable(self.qm.query_supporting_l1_facts)


# ---------------------------------------------------------------------------
# 6. Writer function existence (9 functions)
# ---------------------------------------------------------------------------

class TestWriterFunctions:
    """META-β/γ/δ/ε writer function existence."""

    def test_pattern_catalog_write_from_chart_facts_exists(self):
        from pipeline.writers.pattern_catalog_writer import write_patterns_from_chart_facts
        assert callable(write_patterns_from_chart_facts)

    def test_pattern_catalog_write_from_temporal_events_exists(self):
        from pipeline.writers.pattern_catalog_writer import write_patterns_from_temporal_events
        assert callable(write_patterns_from_temporal_events)

    def test_pattern_catalog_write_from_yoga_register_exists(self):
        from pipeline.writers.pattern_catalog_writer import write_patterns_from_yoga_register
        assert callable(write_patterns_from_yoga_register)

    def test_divergence_scan_ayanamsha_exists(self):
        from pipeline.writers.divergence_ledger_writer import scan_for_ayanamsha_divergences
        assert callable(scan_for_ayanamsha_divergences)

    def test_divergence_scan_tradition_exists(self):
        from pipeline.writers.divergence_ledger_writer import scan_for_tradition_divergences
        assert callable(scan_for_tradition_divergences)

    def test_negative_space_write_exists(self):
        from pipeline.writers.negative_space_writer import write_negative_space
        assert callable(write_negative_space)

    def test_negative_space_write_empty_houses_exists(self):
        from pipeline.writers.negative_space_writer import write_negative_space_from_empty_houses
        assert callable(write_negative_space_from_empty_houses)

    def test_derivation_graph_write_nodes_exists(self):
        from pipeline.writers.derivation_graph_writer import write_derivation_nodes_from_chart_facts
        assert callable(write_derivation_nodes_from_chart_facts)

    def test_derivation_graph_write_edges_exists(self):
        from pipeline.writers.derivation_graph_writer import write_derivation_edges_for_patterns
        assert callable(write_derivation_edges_for_patterns)

    def test_derivation_graph_write_msr_nodes_exists(self):
        from pipeline.writers.derivation_graph_writer import write_derivation_nodes_from_msr_signals
        assert callable(write_derivation_nodes_from_msr_signals)


# ---------------------------------------------------------------------------
# 7. SQL correctness checks (additional)
# ---------------------------------------------------------------------------

class TestMigrationSQLCorrectness:
    """Deeper SQL validation."""

    @pytest.fixture(autouse=True)
    def _sql(self):
        self.sql = open(MIGRATION_PATH).read()

    def test_divergence_severity_check_constraint(self):
        assert "CHECK (divergence_severity IN (" in self.sql or \
               "divergence_severity IN (" in self.sql

    def test_divergence_resolution_status_check_constraint(self):
        assert "resolution_status IN (" in self.sql

    def test_negative_space_significance_check_constraint(self):
        assert "absence_significance IN (" in self.sql

    def test_derivation_node_kind_check_constraint(self):
        assert "node_kind IN (" in self.sql

    def test_derivation_edge_kind_check_constraint(self):
        assert "edge_kind IN (" in self.sql

    def test_pattern_catalog_unique_constraint(self):
        assert "UNIQUE(chart_id, ayanamsha_id, source_asset, source_row_id, pattern_name)" in self.sql

    def test_negative_space_unique_constraint(self):
        assert "UNIQUE(chart_id, ayanamsha_id, absence_class, absent_feature)" in self.sql

    def test_derivation_nodes_unique_constraint(self):
        assert "UNIQUE(chart_id, ayanamsha_id, node_kind, source_table, source_row_id)" in self.sql

    def test_derivation_edges_unique_constraint(self):
        assert "UNIQUE(source_node_id, target_node_id, edge_kind)" in self.sql
