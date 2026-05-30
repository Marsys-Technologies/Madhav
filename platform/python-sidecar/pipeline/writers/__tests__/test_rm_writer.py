"""
Tests for pipeline.writers.rm_writer — G4-06 (minimum 20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch

from pipeline.writers.rm_writer import (
    write,
    ASSET_ID,
    ASSET_LABEL,
    _ALL_GRAHAS,
    _GRAHA_REMEDIES,
    _REMEDY_TYPES,
    make_fact_id,
    _rank_grahas_by_weakness,
    _build_remedy_rows,
    _build_placeholder_rows,
)

CHART_ID = "rm123456-0000-0000-0000-000000000000"
AYANAMSHA_ID = "lahiri"
BUILD_ID = "rm_build_001"


def _make_conn():
    return MagicMock()


# ── Constants ─────────────────────────────────────────────────────────────────

def test_asset_id():
    assert ASSET_ID == "A13_rm"


def test_asset_label():
    assert ASSET_LABEL == "RM Resonance Map"


def test_all_grahas_count():
    assert len(_ALL_GRAHAS) == 9


def test_remedy_types():
    assert set(_REMEDY_TYPES) == {"mantra", "gemstone", "charity"}


def test_graha_remedies_all_grahas():
    for g in _ALL_GRAHAS:
        assert g in _GRAHA_REMEDIES


def test_graha_remedies_tuple_length():
    for g, r in _GRAHA_REMEDIES.items():
        assert len(r) == 3


# ── make_fact_id ──────────────────────────────────────────────────────────────

def test_fact_id_deterministic():
    a = make_fact_id("rm_remedy", "sun", "remedy_mantra", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("rm_remedy", "sun", "remedy_mantra", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a == b


# ── _rank_grahas_by_weakness ──────────────────────────────────────────────────

def test_rank_empty_data_all_zero():
    ranked = _rank_grahas_by_weakness({})
    assert all(ratio == 0.0 for _, ratio in ranked)


def test_rank_length():
    ranked = _rank_grahas_by_weakness({})
    assert len(ranked) == 9


def test_rank_weakest_first():
    shadbala = {
        "sun": {"total_shadbala": 10.0},   # ratio = 10/390 = 0.026 (weakest)
        "moon": {"total_shadbala": 720.0},  # ratio = 720/360 = 2.0 (strong)
    }
    ranked = _rank_grahas_by_weakness(shadbala)
    ratios = [r for _, r in ranked]
    assert ratios == sorted(ratios)


def test_rank_strong_graha_at_end():
    shadbala = {"sun": {"total_shadbala": 3900.0}}  # very high
    ranked = _rank_grahas_by_weakness(shadbala)
    last_graha = ranked[-1][0]
    assert last_graha == "sun"


# ── _build_remedy_rows ────────────────────────────────────────────────────────

def test_remedy_rows_count():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "sun", 1)
    assert len(rows) == 3


def test_remedy_row_fact_category():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "sun", 1)
    for row in rows:
        assert row[8] == "rm_remedy"


def test_remedy_row_subject_is_graha():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "saturn", 2)
    for row in rows:
        assert row[9] == "saturn"


def test_remedy_row_key_format():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "sun", 1)
    keys = {row[10] for row in rows}
    assert keys == {"remedy_mantra", "remedy_gemstone", "remedy_charity"}


def test_remedy_row_priority_as_value_number():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "sun", 3)
    for row in rows:
        assert row[12] == pytest.approx(3.0)


def test_remedy_row_length():
    rows = _build_remedy_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, "moon", 1)
    assert all(len(r) == 19 for r in rows)


# ── _build_placeholder_rows ───────────────────────────────────────────────────

def test_placeholder_rows_count():
    rows = _build_placeholder_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(rows) == 9


def test_placeholder_rows_value_text():
    rows = _build_placeholder_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    for row in rows:
        assert row[11] == "rm_not_computed"


def test_placeholder_rows_key_is_status():
    rows = _build_placeholder_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    for row in rows:
        assert row[10] == "status"


# ── write() ───────────────────────────────────────────────────────────────────

def test_write_no_shadbala_returns_9():
    conn = _make_conn()
    with patch("pipeline.writers.rm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert count == 9


def test_write_with_shadbala_returns_27():
    # 9 grahas × 3 remedy types = 27 rows
    shadbala = {g: {"total_shadbala": 300.0} for g in _ALL_GRAHAS}
    conn = _make_conn()
    with patch("pipeline.writers.rm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"shadbala": shadbala}, conn)
    assert count == 27


def test_write_extra_shadbala_used():
    shadbala = {g: {"total_shadbala": 300.0} for g in _ALL_GRAHAS}
    conn = _make_conn()
    with patch("pipeline.writers.rm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn, extra={"shadbala": shadbala})
    assert count == 27


def test_write_calls_upsert_once():
    conn = _make_conn()
    with patch("pipeline.writers.rm_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert mock_upsert.call_count == 1
