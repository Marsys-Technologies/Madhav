"""
Tests for pipeline.writers.cdlm_writer — G4-04 (minimum 20 tests).
"""
import math
import pytest
from unittest.mock import MagicMock, patch

from pipeline.writers.cdlm_writer import (
    write,
    ASSET_ID,
    ASSET_LABEL,
    DOMAINS,
    make_fact_id,
    make_citation_ref,
    _count_signals_per_domain,
    _shared_factor_count,
    _link_strength,
    _build_rows,
)

CHART_ID = "cdlm1234-0000-0000-0000-000000000000"
AYANAMSHA_ID = "lahiri"
BUILD_ID = "cdlm_build_001"


def _make_conn():
    return MagicMock()


# ── Constants ─────────────────────────────────────────────────────────────────

def test_asset_id():
    assert ASSET_ID == "A11_cdlm"


def test_asset_label():
    assert ASSET_LABEL == "CDLM Cross-Domain Links"


def test_domains_count():
    assert len(DOMAINS) == 9


def test_domains_contents():
    for d in ["career", "relationships", "health", "wealth", "family",
              "learning", "spirituality", "longevity", "character"]:
        assert d in DOMAINS


# ── make_fact_id / make_citation_ref ─────────────────────────────────────────

def test_fact_id_deterministic():
    a = make_fact_id("cdlm", "career", "link_health", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    b = make_fact_id("cdlm", "career", "link_health", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert a == b


def test_fact_id_length_16():
    fid = make_fact_id("cdlm", "career", "link_health", CHART_ID, AYANAMSHA_ID, BUILD_ID)
    assert len(fid) == 16


def test_citation_ref_contains_category():
    ref = make_citation_ref("cdlm", "career", "link_health", CHART_ID, AYANAMSHA_ID)
    assert "cdlm" in ref


# ── _count_signals_per_domain ─────────────────────────────────────────────────

def test_count_signals_empty():
    result = _count_signals_per_domain([])
    assert all(v == 0 for v in result.values())


def test_count_signals_known_domain():
    signals = [{"domain": "career"}, {"domain": "career"}, {"domain": "health"}]
    result = _count_signals_per_domain(signals)
    assert result["career"] == 2
    assert result["health"] == 1


def test_count_signals_unknown_domain_ignored():
    signals = [{"domain": "unknown_domain"}]
    result = _count_signals_per_domain(signals)
    assert all(v == 0 for v in result.values())


# ── _shared_factor_count ──────────────────────────────────────────────────────

def test_shared_factor_count_none():
    signals = [{"domains": ["career", "health"]}]
    assert _shared_factor_count("career", "wealth", signals) == 0


def test_shared_factor_count_one():
    signals = [{"domains": ["career", "health"]}]
    assert _shared_factor_count("career", "health", signals) == 1


def test_shared_factor_count_multiple():
    signals = [
        {"domains": ["career", "health"]},
        {"domains": ["career", "health", "wealth"]},
        {"domains": ["health"]},
    ]
    assert _shared_factor_count("career", "health", signals) == 2


# ── _link_strength ────────────────────────────────────────────────────────────

def test_link_strength_placeholder():
    val, txt = _link_strength("career", "health", {}, [], True)
    assert val == 0.5
    assert txt == "placeholder"


def test_link_strength_zero_shared():
    counts = {"career": 5, "health": 5}
    val, txt = _link_strength("career", "health", counts, [], False)
    assert val == pytest.approx(0.0)
    assert "0 shared factors" in txt


def test_link_strength_formula():
    # 2 shared factors, 4 career signals, 4 health signals
    counts = {"career": 4, "health": 4}
    signals = [
        {"domains": ["career", "health"]},
        {"domains": ["career", "health"]},
    ]
    val, txt = _link_strength("career", "health", counts, signals, False)
    expected = 2 / math.sqrt(4 * 4)
    assert val == pytest.approx(expected)


# ── _build_rows ───────────────────────────────────────────────────────────────

def test_build_rows_count_81():
    rows = _build_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, None, True)
    assert len(rows) == 81  # 9 × 9


def test_build_rows_all_placeholders_when_no_signals():
    rows = _build_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, None, True)
    for row in rows:
        assert row[12] == pytest.approx(0.5)  # value_number
        assert row[11] == "placeholder"        # value_text


def test_build_rows_fact_category_cdlm():
    rows = _build_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, None, True)
    for row in rows:
        assert row[8] == "cdlm"


def test_build_rows_row_length():
    rows = _build_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, None, True)
    assert all(len(r) == 19 for r in rows)


def test_build_rows_fact_key_format():
    rows = _build_rows(CHART_ID, AYANAMSHA_ID, BUILD_ID, None, True)
    fact_keys = {row[10] for row in rows}
    for domain in DOMAINS:
        assert f"link_{domain}" in fact_keys


# ── write() ───────────────────────────────────────────────────────────────────

def test_write_no_signals_returns_81():
    conn = _make_conn()
    with patch("pipeline.writers.cdlm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert count == 81


def test_write_calls_upsert_once():
    conn = _make_conn()
    with patch("pipeline.writers.cdlm_writer._upsert_chart_facts") as mock_upsert:
        write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {}, conn)
    assert mock_upsert.call_count == 1


def test_write_with_signals_returns_81():
    signals = [{"domain": "career", "domains": ["career", "health"]}]
    conn = _make_conn()
    with patch("pipeline.writers.cdlm_writer._upsert_chart_facts"):
        count = write(BUILD_ID, CHART_ID, AYANAMSHA_ID, {"msr_signals": signals}, conn)
    assert count == 81
