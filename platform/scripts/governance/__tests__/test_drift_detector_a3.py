"""Tests for A3 schema enforcement additions to drift_detector.py.

Run from repo root:
  python -m pytest platform/scripts/governance/__tests__/test_drift_detector_a3.py -v
"""
import json
import os
import sys
import pathlib

# Allow import of drift_detector from its directory
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


def test_schema_json_loaded():
    schema_path = 'platform/scripts/governance/CHART_FACTS_SCHEMA.json'
    if os.path.exists(schema_path):
        d = json.load(open(schema_path))
        assert len(d['categories']) >= 140
        assert len(d['channels']) == 4


def test_check_a3_schema_compliance_import():
    from drift_detector import check_a3_schema_compliance
    assert callable(check_a3_schema_compliance)


def test_check_a3_categories_and_mvs_import():
    from drift_detector import check_a3_categories_and_mvs
    assert callable(check_a3_categories_and_mvs)


def test_check_a3_schema_compliance_no_db():
    """check_a3_schema_compliance returns a summary dict even when conn fails."""
    from drift_detector import check_a3_schema_compliance

    class _BadConn:
        def cursor(self):
            raise RuntimeError("no db")

    result = check_a3_schema_compliance(_BadConn())
    assert isinstance(result, dict)
    assert "bad_verification_status_count" in result
    assert "missing_citation_ref_count" in result
    assert "missing_mvs" in result
    assert "hard_violation" in result


def test_validate_a3_schema_import():
    from schema_validator import validate_a3_schema
    assert callable(validate_a3_schema)
