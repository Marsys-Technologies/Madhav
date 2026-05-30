"""
Tests for pipeline.writers.msr_writer — G4-02 (minimum 20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch, call


CHART_ID = "abc12345-0000-0000-0000-000000000000"
AYANAMSHA_ID = "lahiri"
BUILD_ID = "test_build_001"


def _make_conn():
    return MagicMock()


# ── Import writer ─────────────────────────────────────────────────────────────

from pipeline.writers.msr_writer import (
    write,
    make_fact_id,
    make_citation_ref,
    _build_signal_row,
    _build_placeholder_row,
    ASSET_ID,
    ASSET_LABEL,
    ENGINE_VERSION,
)


# ── Constants ─────────────────────────────────────────────────────────────────

def test_asset_id():
    assert ASSET_ID == "A10_msr"


def test_asset_label():
    assert ASSET_LABEL == "MSR Signal Store"


def test_engine_version():
    assert ENGINE_VERSION.startswith("natal_engine/")


# ── make_fact_id ──────────────────────────────────────────────────────────────

def test_fact_id_deterministic():
    a = make_fact_id("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a == b


def test_fact_id_length_16():
    fid = make_fact_id("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(fid) == 16


def test_fact_id_unique_per_key():
    a = make_fact_id("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("msr_signal", "yoga", "key2", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a != b


# ── make_citation_ref ─────────────────────────────────────────────────────────

def test_citation_ref_contains_chart_prefix():
    ref = make_citation_ref("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID)
    assert "chart=abc12345" in ref


def test_citation_ref_contains_ayanamsha():
    ref = make_citation_ref("msr_signal", "yoga", "key1", CHART_ID, AYANAMSHA_ID)
    assert "ay=lahiri" in ref


# ── _build_signal_row ─────────────────────────────────────────────────────────

def test_signal_row_length():
    sig = {"signal_type": "yoga", "signal_id": "sig_001", "configuration": "Sun-Moon", "computed_salience": 0.8}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert len(row) == 19  # matches _INSERT_SQL columns


def test_signal_row_fact_category():
    sig = {"signal_type": "yoga", "signal_id": "sig_001"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    # fact_category at index 4 (category legacy) and index 8 (fact_category)
    assert row[4] == "msr_signal"
    assert row[8] == "msr_signal"


def test_signal_row_uses_signal_type_as_subject():
    sig = {"signal_type": "yoga_raj", "signal_id": "sig_002"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[9] == "yoga_raj"   # fact_subject


def test_signal_row_uses_signal_id_as_key():
    sig = {"signal_type": "yoga", "signal_id": "sig_XYZ"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[10] == "sig_XYZ"  # fact_key


def test_signal_row_fallback_key_when_no_signal_id():
    sig = {"signal_type": "yoga"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 7)
    assert row[10] == "sig_7"


def test_signal_row_salience_as_value_number():
    sig = {"signal_type": "yoga", "signal_id": "s1", "computed_salience": 0.73}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[12] == pytest.approx(0.73)


def test_signal_row_configuration_as_value_text():
    sig = {"signal_type": "yoga", "signal_id": "s1", "configuration": "Sun in 10H"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[11] == "Sun in 10H"


def test_signal_row_citation_fallback():
    sig = {"signal_type": "yoga", "signal_id": "s1"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[14] == "G12 library"


def test_signal_row_custom_citation():
    sig = {"signal_type": "yoga", "signal_id": "s1", "primary_citation": "BPHS Ch 40"}
    row = _build_signal_row(CHART_ID, AYANAMSHA_ID, BUILD_ID, sig, 0)
    assert row[14] == "BPHS Ch 40"


# ── _build_placeholder_row ────────────────────────────────────────────────────

def test_placeholder_row_value_text():
    row = _build_placeholder_row(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert row[11] == "msr_not_computed"


def test_placeholder_row_key_is_status():
    row = _build_placeholder_row(CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert row[10] == "status"


# ── write() ───────────────────────────────────────────────────────────────────

def test_write_no_signals_returns_1():
    conn = _make_conn()
    with patch("pipeline.writers.msr_writer._upsert_chart_facts") as mock_upsert:
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert count == 1


def test_write_no_signals_calls_upsert_once():
    conn = _make_conn()
    with patch("pipeline.writers.msr_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert mock_upsert.call_count == 1


def test_write_empty_list_returns_1_placeholder():
    conn = _make_conn()
    with patch("pipeline.writers.msr_writer._upsert_chart_facts") as mock_upsert:
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"msr_signals": []}, conn)
    assert count == 1


def test_write_with_signals_returns_correct_count():
    signals = [
        {"signal_type": "yoga", "signal_id": f"s{i}", "computed_salience": 0.5}
        for i in range(5)
    ]
    conn = _make_conn()
    with patch("pipeline.writers.msr_writer._upsert_chart_facts") as mock_upsert:
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"msr_signals": signals}, conn)
    assert count == 5


def test_write_passes_conn_to_upsert():
    conn = _make_conn()
    signals = [{"signal_type": "yoga", "signal_id": "s1"}]
    with patch("pipeline.writers.msr_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"msr_signals": signals}, conn)
    assert mock_upsert.call_args[0][0] is conn
