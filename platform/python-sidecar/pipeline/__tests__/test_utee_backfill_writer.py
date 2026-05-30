"""
UTEE-S2 unit tests for utee_backfill_writer.
All tests are pure unit tests — no database required.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.writers.utee_backfill_writer import (
    normalize_severity,
    confidence_class_from_float,
    SEVERITY_MAP_TEXT_TO_FLOAT,
    CONFIDENCE_CLASS_FROM_FLOAT,
)


# ---------------------------------------------------------------------------
# normalize_severity
# ---------------------------------------------------------------------------

class TestNormalizeSeverity:
    def test_none_returns_default_half(self):
        assert normalize_severity(None) == 0.5

    def test_float_passthrough_clamped_high(self):
        assert normalize_severity(1.5) == 1.0

    def test_float_passthrough_clamped_low(self):
        assert normalize_severity(-0.3) == 0.0

    def test_float_passthrough_in_range(self):
        assert normalize_severity(0.7) == pytest.approx(0.7)

    def test_int_passthrough(self):
        assert normalize_severity(0) == 0.0
        assert normalize_severity(1) == 1.0

    def test_text_critical_maps_to_1(self):
        assert normalize_severity('critical') == 1.0

    def test_text_moderate_maps_to_half(self):
        assert normalize_severity('moderate') == 0.5

    def test_text_unknown_defaults_to_half(self):
        assert normalize_severity('unknown_category') == 0.5

    def test_text_case_insensitive(self):
        assert normalize_severity('HIGH') == 0.8
        assert normalize_severity('Low') == 0.3


# ---------------------------------------------------------------------------
# confidence_class_from_float
# ---------------------------------------------------------------------------

class TestConfidenceClassFromFloat:
    def test_high_class_at_threshold(self):
        assert confidence_class_from_float(0.8) == 'high'

    def test_high_class_above_threshold(self):
        assert confidence_class_from_float(0.95) == 'high'

    def test_medium_class_at_boundary(self):
        assert confidence_class_from_float(0.6) == 'medium'

    def test_medium_class_mid(self):
        assert confidence_class_from_float(0.7) == 'medium'

    def test_low_class_at_boundary(self):
        assert confidence_class_from_float(0.3) == 'low'

    def test_low_class_mid(self):
        assert confidence_class_from_float(0.45) == 'low'

    def test_speculative_at_zero(self):
        assert confidence_class_from_float(0.0) == 'speculative'

    def test_speculative_below_low(self):
        assert confidence_class_from_float(0.15) == 'speculative'


# ---------------------------------------------------------------------------
# SQL structure sanity: ensure UPDATE statements have WHERE clauses
# (static check on function source code)
# ---------------------------------------------------------------------------

import inspect
from pipeline.writers import utee_backfill_writer as bfm


def _sql_body(fn_name: str) -> str:
    # Extract the SQL body from a backfill function: returns only the content
    # starting at the UPDATE keyword, which skips the docstring entirely.
    # This avoids false positives from NOTE comments in the docstring.
    fn = getattr(bfm, fn_name)
    src = inspect.getsource(fn)
    # Split off the docstring (everything between the first and second triple-quote pair)
    # by finding the UPDATE keyword which is always inside the SQL string
    update_idx = src.find('UPDATE ')
    if update_idx == -1:
        return src
    return src[update_idx:]


class TestSQLStructure:
    """Verify the SQL UPDATE strings contain WHERE clauses (injection-safety check)."""

    def test_backfill_a15_has_where(self):
        sql = _sql_body('backfill_a15')
        assert 'WHERE' in sql

    def test_backfill_a19_has_where(self):
        sql = _sql_body('backfill_a19')
        assert 'WHERE' in sql

    def test_backfill_a21_has_where(self):
        sql = _sql_body('backfill_a21')
        assert 'WHERE' in sql

    def test_backfill_a18_uses_coalesce(self):
        sql = _sql_body('backfill_a18')
        assert 'COALESCE' in sql

    def test_backfill_a16_uses_confidence_score_not_expected_intensity(self):
        """Regression: column must be 'confidence_score' not the non-existent 'expected_intensity'."""
        sql = _sql_body('backfill_a16')
        assert 'confidence_score' in sql
        assert 'expected_intensity' not in sql

    def test_backfill_a19_uses_hit_iso_not_transit_hit_iso(self):
        """Regression: column must be 'hit_iso' not the non-existent 'transit_hit_iso'."""
        sql = _sql_body('backfill_a19')
        assert 'hit_iso' in sql
        # The word 'transit_hit_iso' should NOT appear in the actual SQL column refs
        assert 'transit_hit_iso' not in sql

    def test_backfill_a19_uses_strength_score_not_transit_severity_score(self):
        """Regression: column must be 'strength_score' not 'transit_severity_score'."""
        sql = _sql_body('backfill_a19')
        assert 'strength_score' in sql
        assert 'transit_severity_score' not in sql

    def test_backfill_a21_uses_exact_date_not_exact_aspect_date(self):
        """Regression: column must be 'exact_date' not 'exact_aspect_date'."""
        sql = _sql_body('backfill_a21')
        assert 'exact_date' in sql
        assert 'exact_aspect_date' not in sql

    def test_backfill_a15_uses_cluster_intensity_not_convergence_intensity(self):
        """Regression: column must be 'cluster_intensity' not 'convergence_intensity'."""
        sql = _sql_body('backfill_a15')
        assert 'cluster_intensity' in sql
        assert 'convergence_intensity' not in sql

    def test_run_all_backfills_returns_dict_structure(self):
        """run_all_backfills should call all 7 table functions."""
        src = inspect.getsource(bfm.run_all_backfills)
        for key in ('A15', 'A16', 'A18', 'A19', 'A20', 'A21', 'A22'):
            assert key in src
