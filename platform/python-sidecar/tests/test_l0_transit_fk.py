"""
Integration test: bg_transit_rules writer uses upsert, not delete+insert.
Verifies the fix for the ForeignKeyViolation bug where DELETE FROM
bg_transit_rules was blocked by gochara_resonance_map FK.
"""
import inspect
import pytest
from brahmagyan.l0_transit import seed_transit_rules


def test_no_delete_from_bg_transit_rules():
    """seed_transit_rules must NOT delete from bg_transit_rules (FK violation)."""
    source = inspect.getsource(seed_transit_rules)
    # The source should not contain DELETE FROM bg_transit_rules
    assert 'DELETE FROM bg_transit_rules' not in source, (
        "seed_transit_rules still contains DELETE FROM bg_transit_rules — "
        "this will FK-violate against gochara_resonance_map.source_rule_id"
    )


def test_no_delete_from_bg_transit_engine():
    """seed_transit_rules must NOT delete from bg_transit_engine."""
    source = inspect.getsource(seed_transit_rules)
    assert 'DELETE FROM bg_transit_engine' not in source


def test_no_delete_from_bg_transit_moorti():
    """seed_transit_rules must NOT delete from bg_transit_moorti."""
    source = inspect.getsource(seed_transit_rules)
    assert 'DELETE FROM bg_transit_moorti' not in source


def test_upsert_patterns_present():
    """ON CONFLICT upsert patterns must exist for all three tables."""
    source = inspect.getsource(seed_transit_rules)
    assert 'ON CONFLICT (graha) DO UPDATE' in source, "Missing upsert for bg_transit_engine"
    assert 'ON CONFLICT (graha, rule_type, primary_house) DO UPDATE' in source, "Missing upsert for bg_transit_rules"
    assert 'ON CONFLICT (nakshatra_offset) DO UPDATE' in source, "Missing upsert for bg_transit_moorti"
