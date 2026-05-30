"""
BRIDGE-S1/S2/S3 unit tests.
All tests are pure unit tests — no database required.
Tests cover:
  - compute_interaction_class for all strength thresholds
  - VEDHA_MITIGATION_STRENGTH mapping coverage
  - query_vedha_anchor_interactions SQL construction (mock cursor)
  - Migration file existence and table name
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.writers.vedha_anchor_bridge_writer import (
    compute_interaction_class,
    VEDHA_MITIGATION_STRENGTH,
    _DEFAULT_MITIGATION_STRENGTH,
)
from pipeline.query.query_vedha_anchor_interactions import (
    query_vedha_anchor_interactions,
)

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', 'migrations',
    '150_vedha_anchor_interactions.sql',
)


# ---------------------------------------------------------------------------
# compute_interaction_class thresholds
# ---------------------------------------------------------------------------

class TestComputeInteractionClass:
    def test_full_mitigation_at_0_80(self):
        assert compute_interaction_class(0.80) == 'full_mitigation'

    def test_full_mitigation_above_0_80(self):
        assert compute_interaction_class(0.95) == 'full_mitigation'
        assert compute_interaction_class(1.0)  == 'full_mitigation'

    def test_partial_mitigation_at_0_55(self):
        assert compute_interaction_class(0.55) == 'partial_mitigation'

    def test_partial_mitigation_mid_range(self):
        assert compute_interaction_class(0.65) == 'partial_mitigation'

    def test_neutralizing_at_0_30(self):
        assert compute_interaction_class(0.30) == 'neutralizing'

    def test_neutralizing_mid_range(self):
        assert compute_interaction_class(0.40) == 'neutralizing'

    def test_amplification_below_0_30(self):
        assert compute_interaction_class(0.10) == 'amplification'

    def test_amplification_near_zero(self):
        assert compute_interaction_class(0.01) == 'amplification'

    def test_cancellation_zero_maps_to_amplification(self):
        # vedha with strength=0.0 (cancellation case) — no mitigation effect
        assert compute_interaction_class(0.0) == 'amplification'


# ---------------------------------------------------------------------------
# VEDHA_MITIGATION_STRENGTH coverage
# ---------------------------------------------------------------------------

class TestVedhaMitigationStrengthMapping:
    def test_strong_maps_to_high_value(self):
        assert VEDHA_MITIGATION_STRENGTH['strong'] >= 0.75

    def test_moderate_maps_to_mid_value(self):
        v = VEDHA_MITIGATION_STRENGTH['moderate']
        assert 0.40 <= v < 0.75

    def test_weak_maps_to_low_value(self):
        v = VEDHA_MITIGATION_STRENGTH['weak']
        assert v < 0.40

    def test_cancellation_maps_to_zero(self):
        assert VEDHA_MITIGATION_STRENGTH['cancellation'] == 0.0

    def test_all_four_severity_values_present(self):
        """All CHECK constraint values from migration 144 must have a mapping."""
        required = {'strong', 'moderate', 'weak', 'cancellation'}
        assert required.issubset(set(VEDHA_MITIGATION_STRENGTH.keys()))

    def test_default_strength_is_reasonable(self):
        assert 0.0 < _DEFAULT_MITIGATION_STRENGTH < 1.0


# ---------------------------------------------------------------------------
# query_vedha_anchor_interactions SQL construction (mock cursor)
# ---------------------------------------------------------------------------

class TestQueryVedhaAnchorInteractions:
    def _make_mock_conn(self, rows=None, colnames=None):
        """Build a mock psycopg2 connection with configurable cursor result."""
        if rows is None:
            rows = []
        if colnames is None:
            colnames = [
                'interaction_id', 'chart_id', 'ayanamsha_id', 'build_id',
                'vedha_id', 'anchor_id', 'interaction_class', 'mitigation_strength',
                'expected_outcome_modification_class', 'severity_after_mitigation',
                'confidence_after_mitigation', 'classical_resolution_methodology',
                'classical_citation', 'computed_at',
            ]
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(c,) for c in colnames]
        mock_cursor.fetchall.return_value = rows

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    def test_basic_call_executes_query(self):
        conn, cur = self._make_mock_conn()
        query_vedha_anchor_interactions(conn, 'chart-1', 'lahiri')
        assert cur.execute.called

    def test_returns_list_of_dicts(self):
        row = ('id1', 'chart1', 'lahiri', 'build1', '10', '20',
               'full_mitigation', 0.8, 'vedha_mitigates',
               0.3, 0.65, 'Tajika', 'Tajika Neelakanthi', '2026-05-30')
        conn, cur = self._make_mock_conn(rows=[row])
        results = query_vedha_anchor_interactions(conn, 'chart-1', 'lahiri')
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert results[0]['interaction_class'] == 'full_mitigation'

    def test_build_id_filter_adds_condition(self):
        conn, cur = self._make_mock_conn()
        query_vedha_anchor_interactions(conn, 'chart-1', 'lahiri', build_id='build-999')
        sql_called = cur.execute.call_args[0][0]
        assert 'build_id' in sql_called

    def test_interaction_class_filter_adds_condition(self):
        conn, cur = self._make_mock_conn()
        query_vedha_anchor_interactions(
            conn, 'chart-1', 'lahiri',
            interaction_class_filter='partial_mitigation'
        )
        sql_called = cur.execute.call_args[0][0]
        assert 'interaction_class' in sql_called

    def test_min_mitigation_strength_adds_condition(self):
        conn, cur = self._make_mock_conn()
        query_vedha_anchor_interactions(
            conn, 'chart-1', 'lahiri',
            min_mitigation_strength=0.5
        )
        sql_called = cur.execute.call_args[0][0]
        assert 'mitigation_strength' in sql_called

    def test_limit_is_parameterized(self):
        conn, cur = self._make_mock_conn()
        query_vedha_anchor_interactions(conn, 'chart-1', 'lahiri', limit=25)
        params = cur.execute.call_args[0][1]
        assert 25 in params

    def test_empty_result_returns_empty_list(self):
        conn, cur = self._make_mock_conn(rows=[])
        results = query_vedha_anchor_interactions(conn, 'chart-1', 'lahiri')
        assert results == []


# ---------------------------------------------------------------------------
# Migration file existence + table name check
# ---------------------------------------------------------------------------

class TestMigration150:
    def _read_migration(self):
        path = os.path.normpath(MIGRATION_PATH)
        with open(path, 'r') as f:
            return f.read()

    def test_migration_file_exists(self):
        path = os.path.normpath(MIGRATION_PATH)
        assert os.path.isfile(path), f"Migration file not found at {path}"

    def test_migration_contains_correct_table_name(self):
        content = self._read_migration()
        assert 'l25_vedha_anchor_interactions' in content

    def test_migration_contains_bigint_vedha_id(self):
        """vedha_id FK must be BIGINT to match BIGSERIAL PK in l1_vedha_extended."""
        content = self._read_migration()
        assert 'BIGINT' in content

    def test_migration_contains_interaction_class_check(self):
        content = self._read_migration()
        assert 'interaction_class' in content
        assert 'full_mitigation' in content

    def test_migration_is_idempotent(self):
        """Must use CREATE TABLE IF NOT EXISTS."""
        content = self._read_migration()
        assert 'CREATE TABLE IF NOT EXISTS' in content
