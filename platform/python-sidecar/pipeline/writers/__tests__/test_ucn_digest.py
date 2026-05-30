"""
Tests for pipeline.writers.ucn_digest_writer — G4-07 (minimum 20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch

from pipeline.writers.ucn_digest_writer import (
    write,
    ASSET_ID,
    ASSET_LABEL,
    TOP_K,
    _ALL_GRAHAS,
    make_fact_id,
    _top_k_signal_rows,
    _shadbala_rank_rows,
    _top_yoga_rows,
    _dasha_context_rows,
    _system_convergence_row,
    _placeholder_rows,
)

CHART_ID = "ucn12345-0000-0000-0000-000000000000"
AYANAMSHA_ID = "lahiri"
BUILD_ID = "ucn_build_001"

_SHADBALA_FULL = {
    g: {"total_shadbala": (300.0 + i * 30.0)}
    for i, g in enumerate(_ALL_GRAHAS)
}


def _make_conn():
    return MagicMock()


# ── Constants ─────────────────────────────────────────────────────────────────

def test_asset_id():
    assert ASSET_ID == "A14_ucn_digest"


def test_asset_label():
    assert ASSET_LABEL == "UCN Digest"


def test_top_k_value():
    assert TOP_K == 20


# ── make_fact_id ──────────────────────────────────────────────────────────────

def test_fact_id_deterministic():
    a = make_fact_id("ucn_digest", "top_signals", "top_signal_001", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("ucn_digest", "top_signals", "top_signal_001", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a == b


# ── _top_k_signal_rows ────────────────────────────────────────────────────────

def test_top_k_empty_signals():
    rows = _top_k_signal_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, [])
    assert rows == []


def test_top_k_returns_up_to_k():
    signals = [{"signal_id": f"s{i}", "computed_salience": i / 100.0} for i in range(30)]
    rows = _top_k_signal_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, signals)
    assert len(rows) == TOP_K


def test_top_k_sorted_by_salience():
    signals = [
        {"signal_id": "low", "computed_salience": 0.1},
        {"signal_id": "high", "computed_salience": 0.9},
        {"signal_id": "mid", "computed_salience": 0.5},
    ]
    rows = _top_k_signal_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, signals)
    # First row should be the highest salience
    assert rows[0][11] == "high"   # value_text = signal_id


def test_top_k_fact_category():
    signals = [{"signal_id": "s1", "computed_salience": 0.5}]
    rows = _top_k_signal_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, signals)
    assert rows[0][8] == "ucn_digest"


def test_top_k_fact_subject():
    signals = [{"signal_id": "s1", "computed_salience": 0.5}]
    rows = _top_k_signal_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, signals)
    assert rows[0][9] == "top_signals"


# ── _shadbala_rank_rows ───────────────────────────────────────────────────────

def test_shadbala_rank_returns_6_rows():
    # 3 dominant + 3 weakest = 6 rows
    rows = _shadbala_rank_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, _SHADBALA_FULL)
    assert len(rows) == 6


def test_shadbala_rank_dominant_keys():
    rows = _shadbala_rank_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, _SHADBALA_FULL)
    dominant_keys = {r[10] for r in rows if r[9] == "dominant_grahas"}
    assert dominant_keys == {"dominant_1", "dominant_2", "dominant_3"}


def test_shadbala_rank_weakest_keys():
    rows = _shadbala_rank_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, _SHADBALA_FULL)
    weakest_keys = {r[10] for r in rows if r[9] == "weakest_grahas"}
    assert weakest_keys == {"weakest_1", "weakest_2", "weakest_3"}


def test_shadbala_rank_fact_category():
    rows = _shadbala_rank_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, _SHADBALA_FULL)
    for row in rows:
        assert row[8] == "ucn_digest"


# ── _top_yoga_rows ────────────────────────────────────────────────────────────

def test_top_yoga_empty():
    rows = _top_yoga_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, [])
    assert rows == []


def test_top_yoga_returns_up_to_5():
    yogas = [{"yoga_name": f"yoga_{i}", "strength": float(i)} for i in range(10)]
    rows = _top_yoga_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, yogas)
    assert len(rows) == 5


def test_top_yoga_sorted_by_strength():
    yogas = [
        {"yoga_name": "weak_yoga", "strength": 0.2},
        {"yoga_name": "strong_yoga", "strength": 0.9},
    ]
    rows = _top_yoga_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, yogas)
    assert rows[0][11] == "strong_yoga"


# ── _dasha_context_rows ───────────────────────────────────────────────────────

def test_dasha_context_empty():
    rows = _dasha_context_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, {})
    assert rows == []


def test_dasha_context_two_levels():
    dashas = {"vimshottari": {"current_chain": [{"lord": "saturn"}, {"lord": "venus"}]}}
    rows = _dasha_context_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, dashas)
    assert len(rows) == 2


def test_dasha_context_lords():
    dashas = {"vimshottari": {"current_chain": [{"lord": "saturn"}, {"lord": "venus"}]}}
    rows = _dasha_context_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, dashas)
    lords = [row[11] for row in rows]
    assert lords == ["saturn", "venus"]


# ── _system_convergence_row ───────────────────────────────────────────────────

def test_system_convergence_count():
    rows = _system_convergence_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, 4)
    assert len(rows) == 1


def test_system_convergence_value():
    rows = _system_convergence_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, 3)
    assert rows[0][12] == pytest.approx(3.0)


def test_system_convergence_text():
    rows = _system_convergence_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, 5)
    assert "5 of 5" in rows[0][11]


# ── _placeholder_rows ─────────────────────────────────────────────────────────

def test_placeholder_is_one_row():
    rows = _placeholder_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(rows) == 1


def test_placeholder_value_text():
    rows = _placeholder_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert rows[0][11] == "ucn_not_computed"


# ── write() ───────────────────────────────────────────────────────────────────

def test_write_empty_returns_1_placeholder():
    conn = _make_conn()
    with patch("pipeline.writers.ucn_digest_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert count == 1


def test_write_with_shadbala_includes_dominant_weakest():
    conn = _make_conn()
    with patch("pipeline.writers.ucn_digest_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"shadbala": _SHADBALA_FULL}, conn)
    # 6 (dominant/weakest) + 1 (convergence) = 7
    assert count == 7


def test_write_with_signals():
    signals = [{"signal_id": f"s{i}", "computed_salience": i / 100.0} for i in range(5)]
    conn = _make_conn()
    with patch("pipeline.writers.ucn_digest_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"msr_signals": signals}, conn)
    # 5 signal rows + 1 convergence = 6
    assert count == 6


def test_write_calls_upsert_once():
    conn = _make_conn()
    with patch("pipeline.writers.ucn_digest_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert mock_upsert.call_count == 1


def test_write_all_sections():
    signals = [{"signal_id": f"s{i}", "computed_salience": i / 100.0} for i in range(3)]
    yogas = [{"yoga_name": f"y{i}", "strength": float(i)} for i in range(2)]
    dashas = {"vimshottari": {"current_chain": [{"lord": "saturn"}, {"lord": "mercury"}]}}
    conn = _make_conn()
    with patch("pipeline.writers.ucn_digest_writer._upsert_chart_facts"):
        count = write(
            BUILD_ID, CHART_ID, AYANAMSHA_ID,
            {
                "msr_signals": signals,
                "shadbala": _SHADBALA_FULL,
                "yogas": yogas,
                "dashas": dashas,
                "ayanamsha_convergence_count": 3,
            },
            conn,
        )
    # 3 signals + 6 dominant/weakest + 2 yogas + 2 dasha context + 1 convergence = 14
    assert count == 14
