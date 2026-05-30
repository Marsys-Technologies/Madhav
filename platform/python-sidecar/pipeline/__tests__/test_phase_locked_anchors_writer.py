"""
test_phase_locked_anchors_writer.py — Tests for phase_locked_anchors_writer.py

Test 1: STRUCTURAL_ANCHORS has >= 10 entries
Test 2: all anchors have required keys
Test 3: anchor_type values in allowed set
Test 4: confidence_score values 0.0-1.0
Test 5: cluster_intensity >= 3 for all structural anchors
Test 6: g29_rules_fired are lists (even if empty)
Test 7 (DB): seed_phase_locked_anchors inserts >= 10 rows from fresh; idempotent on second call
Test 8: at least one anchor has window_start >= '2036-01-01' (covers Ketu MD transition)

Stream C — A16 [BUILD-ORCH-STREAM-C-A16-S1]
"""

from __future__ import annotations

import os

import pytest

from pipeline.phase_locked_anchors_writer import (
    ALLOWED_ANCHOR_TYPES,
    STRUCTURAL_ANCHORS,
    seed_phase_locked_anchors,
)

# ---------------------------------------------------------------------------
# DB connectivity
# ---------------------------------------------------------------------------

DB_AVAILABLE = bool(os.environ.get("DB_NAME"))

CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"


def _get_conn():
    """Return a psycopg2 connection using env vars."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5433")),
        dbname=os.environ.get("DB_NAME", "amjis"),
        user=os.environ.get("DB_USER", "amjis_app"),
        password=os.environ.get(
            "DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
        ),
    )


# ---------------------------------------------------------------------------
# Required keys for every anchor
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {
    "chart_id",
    "anchor_label",
    "window_start",
    "window_end",
    "anchor_type",
    "cluster_intensity",
    "g29_rules_fired",
    "systems_active",
    "primary_outcome",
    "alternative_scenario",
    "falsifiability_test",
    "confidence_score",
}


# ---------------------------------------------------------------------------
# Test 1: STRUCTURAL_ANCHORS has >= 10 entries
# ---------------------------------------------------------------------------

def test_structural_anchors_count_at_least_10():
    """Test 1: STRUCTURAL_ANCHORS must have at least 10 entries."""
    assert len(STRUCTURAL_ANCHORS) >= 10, (
        f"Expected >= 10 structural anchors, got {len(STRUCTURAL_ANCHORS)}"
    )


# ---------------------------------------------------------------------------
# Test 2: all anchors have required keys
# ---------------------------------------------------------------------------

def test_all_anchors_have_required_keys():
    """Test 2: every anchor dict must contain all required keys."""
    for i, anchor in enumerate(STRUCTURAL_ANCHORS):
        missing = REQUIRED_KEYS - set(anchor.keys())
        assert not missing, (
            f"Anchor[{i}] '{anchor.get('anchor_label', '?')}' missing keys: {missing}"
        )


# ---------------------------------------------------------------------------
# Test 3: anchor_type values in allowed set
# ---------------------------------------------------------------------------

def test_anchor_type_values_in_allowed_set():
    """Test 3: anchor_type must be one of the allowed values."""
    for i, anchor in enumerate(STRUCTURAL_ANCHORS):
        atype = anchor["anchor_type"]
        assert atype in ALLOWED_ANCHOR_TYPES, (
            f"Anchor[{i}] has invalid anchor_type='{atype}'; "
            f"allowed: {ALLOWED_ANCHOR_TYPES}"
        )


# ---------------------------------------------------------------------------
# Test 4: confidence_score values 0.0-1.0
# ---------------------------------------------------------------------------

def test_confidence_score_in_range():
    """Test 4: confidence_score must be in [0.0, 1.0] for all structural anchors."""
    for i, anchor in enumerate(STRUCTURAL_ANCHORS):
        score = anchor["confidence_score"]
        assert 0.0 <= score <= 1.0, (
            f"Anchor[{i}] '{anchor.get('anchor_label', '?')}' has "
            f"confidence_score={score} outside [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# Test 5: cluster_intensity >= 3 for all structural anchors
# ---------------------------------------------------------------------------

def test_cluster_intensity_at_least_3():
    """Test 5: cluster_intensity >= 3 for all structural anchors."""
    for i, anchor in enumerate(STRUCTURAL_ANCHORS):
        intensity = anchor["cluster_intensity"]
        assert intensity >= 3, (
            f"Anchor[{i}] '{anchor.get('anchor_label', '?')}' has "
            f"cluster_intensity={intensity} < 3"
        )


# ---------------------------------------------------------------------------
# Test 6: g29_rules_fired are lists (even if empty)
# ---------------------------------------------------------------------------

def test_g29_rules_fired_are_lists():
    """Test 6: g29_rules_fired must be a list for every structural anchor."""
    for i, anchor in enumerate(STRUCTURAL_ANCHORS):
        fired = anchor["g29_rules_fired"]
        assert isinstance(fired, list), (
            f"Anchor[{i}] '{anchor.get('anchor_label', '?')}' has "
            f"g29_rules_fired of type {type(fired).__name__}, expected list"
        )


# ---------------------------------------------------------------------------
# Test 7 (DB): seed inserts >= 10 rows from fresh; idempotent on second call
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available")
def test_seed_phase_locked_anchors_inserts_and_is_idempotent():
    """Test 7 (DB): fresh seed inserts >= 10 rows; second call inserts 0 (idempotent)."""
    conn = _get_conn()
    try:
        # Clear existing rows for clean-slate test (established project pattern)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM l1_phase_locked_anchors WHERE chart_id = %s",
                (CHART_ID,),
            )
            conn.commit()

        count1 = seed_phase_locked_anchors(conn, CHART_ID)
        assert count1 >= 10, (
            f"Expected >= 10 rows inserted on first seed, got {count1}"
        )

        # Idempotency: second run should insert 0 (ON CONFLICT DO NOTHING)
        count2 = seed_phase_locked_anchors(conn, CHART_ID)
        assert count2 == 0, (
            f"Expected 0 rows on second run (idempotency), got {count2}"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 8: at least one anchor covers Ketu MD transition (window_start >= 2036-01-01)
# ---------------------------------------------------------------------------

def test_at_least_one_anchor_covers_ketu_md_transition():
    """Test 8: at least one anchor has window_start >= '2036-01-01' (Ketu MD)."""
    late_anchors = [
        a for a in STRUCTURAL_ANCHORS
        if a["window_start"] >= "2036-01-01"
    ]
    assert len(late_anchors) >= 1, (
        "Expected at least one anchor with window_start >= '2036-01-01' "
        "(covering Ketu MD transition 2035-11-01)"
    )
