"""
tests/test_contracts_null_result.py — unit tests for NullResult in contracts.py.

P0.b (2026-08-14): verifies that .resolution = 1/R (F-01 correction), NOT 1/(R+1).
"""
from services.ka_kshetra.contracts import NullResult


def test_null_result_resolution_is_one_over_R():
    for R in [8, 256, 1024]:
        nr = NullResult(replicates=R, max_stats={}, q_threshold=0.95)
        assert nr.resolution == 1.0 / R, f"Expected 1/{R}, got {nr.resolution}"


def test_null_result_not_one_over_R_plus_1():
    nr = NullResult(replicates=256, max_stats={}, q_threshold=0.95)
    assert nr.resolution != 1.0 / 257, "Resolution must be 1/R, not 1/(R+1)"


def test_null_result_is_frozen():
    nr = NullResult(replicates=256, max_stats={}, q_threshold=0.95)
    raised = False
    try:
        nr.replicates = 512  # type: ignore[misc]
    except Exception:
        raised = True
    assert raised, "NullResult must be frozen (immutable)"


def test_null_result_resolution_property_not_stored():
    """resolution is a property, not a stored field — no __init__ argument."""
    # Constructing with only the three required fields must work.
    nr = NullResult(replicates=1024, max_stats={}, q_threshold=None)
    assert nr.resolution == 1.0 / 1024
