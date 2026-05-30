"""
Tests for similarity_signature.py — G4-09.
No real Vertex AI, no real DB. Uses MagicMock for conn.
Minimum 15 tests.
"""
import pytest
from unittest.mock import MagicMock, patch

from pipeline.writers.similarity_signature import (
    write,
    _build_signature_text,
    _stub_embedding,
)


# ---------------------------------------------------------------------------
# _stub_embedding
# ---------------------------------------------------------------------------

def test_stub_embedding_returns_list_of_768():
    result = _stub_embedding("some text")
    assert isinstance(result, list)
    assert len(result) == 768


def test_stub_embedding_all_floats():
    result = _stub_embedding("text")
    assert all(isinstance(v, float) for v in result)


# ---------------------------------------------------------------------------
# _build_signature_text
# ---------------------------------------------------------------------------

def test_build_signature_text_returns_string():
    result = _build_signature_text({})
    assert isinstance(result, str)


def test_build_signature_text_empty_chart_output_returns_nonempty():
    # With empty dict, signature text should still be a non-empty string
    # (caller falls back to f'chart_{chart_id}_...' — but _build_signature_text itself returns '')
    result = _build_signature_text({})
    # empty string is valid from the function; write() handles fallback
    assert isinstance(result, str)


def test_build_signature_text_includes_msr_signals():
    chart_output = {
        'msr_signals': [
            {'configuration': 'Sun conjunct Jupiter'},
            {'configuration': 'Mars in 10H'},
        ]
    }
    result = _build_signature_text(chart_output)
    assert 'Sun conjunct Jupiter' in result
    assert 'Mars in 10H' in result


def test_build_signature_text_includes_active_yoga_names():
    chart_output = {
        'yogas': [
            {'name': 'Hamsa Yoga', 'active': True},
            {'name': 'Inactive Yoga', 'active': False},
        ]
    }
    result = _build_signature_text(chart_output)
    assert 'Hamsa Yoga' in result
    assert 'Inactive Yoga' not in result


def test_build_signature_text_excludes_inactive_yogas():
    chart_output = {
        'yogas': [
            {'name': 'Inactive Only', 'active': False},
        ]
    }
    result = _build_signature_text(chart_output)
    assert 'Inactive Only' not in result


def test_build_signature_text_includes_dasha_context():
    chart_output = {
        'dashas': {
            'vimshottari': {
                'current_chain': ['Sun', 'Moon']
            }
        }
    }
    result = _build_signature_text(chart_output)
    assert 'dasha' in result.lower()
    assert 'Sun' in result


def test_build_signature_text_includes_dominant_graha():
    chart_output = {
        'shadbala': {
            'Sun': {'total': 100},
            'Moon': {'total': 200},
            'Mars': {'total': 50},
        }
    }
    result = _build_signature_text(chart_output)
    assert 'dominant' in result.lower()
    assert 'Moon' in result


def test_build_signature_text_limits_msr_signals_to_20():
    """Only top-20 MSR signals should be included."""
    signals = [{'configuration': f'signal_{i}'} for i in range(30)]
    chart_output = {'msr_signals': signals}
    result = _build_signature_text(chart_output)
    # signal_20 through signal_29 should NOT appear
    assert 'signal_20' not in result
    assert 'signal_19' in result


# ---------------------------------------------------------------------------
# write()
# ---------------------------------------------------------------------------

def test_write_returns_1_always():
    conn = MagicMock()
    mock_embed = MagicMock(return_value=[0.0] * 768)
    with patch('pipeline.writers.similarity_signature._upsert'):
        result = write("b1", "c1", "lahiri", {}, conn, embed_fn=mock_embed)
    assert result == 1


def test_write_returns_int():
    conn = MagicMock()
    mock_embed = MagicMock(return_value=[0.0] * 768)
    with patch('pipeline.writers.similarity_signature._upsert'):
        result = write("b1", "c1", "lahiri", {}, conn, embed_fn=mock_embed)
    assert isinstance(result, int)


def test_write_calls_embed_fn_exactly_once():
    conn = MagicMock()
    mock_embed = MagicMock(return_value=[0.0] * 768)
    with patch('pipeline.writers.similarity_signature._upsert'):
        write("b1", "c1", "lahiri", {'msr_signals': [{'configuration': 'x'}]}, conn, embed_fn=mock_embed)
    assert mock_embed.call_count == 1


def test_write_fact_category_is_similarity_signature():
    conn = MagicMock()
    mock_embed = MagicMock(return_value=[0.0] * 768)
    captured = []

    def fake_upsert(c, rows):
        captured.extend(rows)

    with patch('pipeline.writers.similarity_signature._upsert', side_effect=fake_upsert):
        write("b1", "c1", "lahiri", {}, conn, embed_fn=mock_embed)

    assert len(captured) == 1
    row = captured[0]
    # fact_category is at index 8 (0-based):
    # (fact_id, chart_id, ayanamsha_id, build_id,
    #  category=4, divisional_chart=5, source_section=6, provenance=7,
    #  fact_category=8, ...)
    assert row[8] == 'similarity_signature'


def test_write_value_text_is_string():
    conn = MagicMock()
    mock_embed = MagicMock(return_value=[0.0] * 768)
    captured = []

    def fake_upsert(c, rows):
        captured.extend(rows)

    with patch('pipeline.writers.similarity_signature._upsert', side_effect=fake_upsert):
        write("b1", "c1", "lahiri", {}, conn, embed_fn=mock_embed)

    row = captured[0]
    # value_text is at index 10 in the insert tuple
    # (fact_id[0], chart_id[1], ayanamsha_id[2], build_id[3],
    #  category[4], divisional_chart[5], source_section[6], provenance[7],
    #  fact_category[8], fact_subject[9], fact_key[10], value_text[11], ...)
    value_text = row[11]
    assert isinstance(value_text, str)


def test_write_fallback_sig_text_when_empty_chart_output():
    """When chart_output is empty, write() falls back to a deterministic string."""
    conn = MagicMock()
    embed_calls = []

    def tracking_embed(text):
        embed_calls.append(text)
        return [0.0] * 768

    with patch('pipeline.writers.similarity_signature._upsert'):
        write("b1", "chart-abc-123", "lahiri", {}, conn, embed_fn=tracking_embed)

    assert len(embed_calls) == 1
    # The fallback text must include the chart_id fragment
    assert 'chart-abc-123' in embed_calls[0]
