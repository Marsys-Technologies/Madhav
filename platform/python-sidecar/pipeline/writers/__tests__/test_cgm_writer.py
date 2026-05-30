"""
Tests for pipeline.writers.cgm_writer — G4-05 (minimum 20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch

from pipeline.writers.cgm_writer import (
    write,
    ASSET_ID,
    ASSET_LABEL,
    _ALL_GRAHAS,
    make_fact_id,
    make_citation_ref,
    _build_node_rows,
    _build_edge_rows,
    _build_placeholder_node_rows,
)

CHART_ID = "cgm12345-0000-0000-0000-000000000000"
AYANAMSHA_ID = "lahiri"
BUILD_ID = "cgm_build_001"


def _make_conn():
    return MagicMock()


# ── Constants ─────────────────────────────────────────────────────────────────

def test_asset_id():
    assert ASSET_ID == "A12_cgm"


def test_asset_label():
    assert ASSET_LABEL == "CGM Graph Nodes + Edges"


def test_all_grahas_count():
    assert len(_ALL_GRAHAS) == 9


def test_all_grahas_contents():
    for g in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        assert g in _ALL_GRAHAS


# ── make_fact_id ──────────────────────────────────────────────────────────────

def test_fact_id_deterministic():
    a = make_fact_id("cgm_node", "graha", "sun", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("cgm_node", "graha", "sun", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a == b


def test_fact_id_length():
    fid = make_fact_id("cgm_node", "graha", "sun", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(fid) == 16


# ── _build_node_rows ──────────────────────────────────────────────────────────

def test_node_rows_count_9():
    planets = {g: {"sign": "aries", "shadbala_rank": 0.5} for g in _ALL_GRAHAS}
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, planets)
    assert len(rows) == 9


def test_node_rows_fact_category():
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, {})
    for row in rows:
        assert row[8] == "cgm_node"


def test_node_row_length():
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, {})
    assert all(len(r) == 19 for r in rows)


def test_node_row_sign_used():
    planets = {"sun": {"sign": "leo", "shadbala_rank": 0.9}}
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, planets)
    sun_row = next(r for r in rows if r[10] == "sun")
    assert sun_row[11] == "leo"  # value_text


def test_node_row_shadbala_rank_used():
    planets = {"moon": {"sign": "taurus", "shadbala_rank": 0.75}}
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, planets)
    moon_row = next(r for r in rows if r[10] == "moon")
    assert moon_row[12] == pytest.approx(0.75)  # value_number


def test_node_row_missing_graha_uses_defaults():
    rows = _build_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, {})
    for row in rows:
        assert row[11] == "unknown"
        assert row[12] == pytest.approx(0.0)


# ── _build_edge_rows ──────────────────────────────────────────────────────────

def test_edge_rows_empty():
    rows = _build_edge_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, [])
    assert rows == []


def test_edge_row_count():
    aspects = [
        {"graha1": "sun", "graha2": "moon", "strength": 0.8},
        {"graha1": "mars", "graha2": "saturn", "strength": 0.5},
    ]
    rows = _build_edge_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, aspects)
    assert len(rows) == 2


def test_edge_row_fact_category():
    aspects = [{"graha1": "sun", "graha2": "moon", "strength": 0.8}]
    rows = _build_edge_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, aspects)
    assert rows[0][8] == "cgm_edge"


def test_edge_row_key_format():
    aspects = [{"graha1": "sun", "graha2": "moon", "strength": 0.8}]
    rows = _build_edge_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, aspects)
    assert rows[0][10] == "sun_to_moon"


def test_edge_row_strength_as_value_number():
    aspects = [{"graha1": "sun", "graha2": "moon", "strength": 0.6}]
    rows = _build_edge_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, aspects)
    assert rows[0][12] == pytest.approx(0.6)


# ── _build_placeholder_node_rows ─────────────────────────────────────────────

def test_placeholder_nodes_count():
    rows = _build_placeholder_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(rows) == 9


def test_placeholder_nodes_value_text():
    rows = _build_placeholder_node_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    for row in rows:
        assert row[11] == "cgm_not_computed"


# ── write() ───────────────────────────────────────────────────────────────────

def test_write_no_planets_returns_9_nodes():
    conn = _make_conn()
    with patch("pipeline.writers.cgm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert count == 9


def test_write_with_planets_and_aspects():
    planets = {g: {"sign": "aries", "shadbala_rank": 0.5} for g in _ALL_GRAHAS}
    aspects = [
        {"graha1": "sun", "graha2": "moon", "strength": 0.7},
        {"graha1": "mars", "graha2": "jupiter", "strength": 0.4},
    ]
    conn = _make_conn()
    with patch("pipeline.writers.cgm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"planets": planets, "aspects": aspects}, conn)
    assert count == 11  # 9 nodes + 2 edges


def test_write_calls_upsert_once():
    conn = _make_conn()
    with patch("pipeline.writers.cgm_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert mock_upsert.call_count == 1
