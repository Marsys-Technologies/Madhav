"""
Tests for pipeline.writers.msr_enrichment — G4-03 (minimum 15 tests).
"""
import pytest
from pipeline.writers.msr_enrichment import enrich_signals
from pipeline.writers.salience import verification_certainty


# ── Basic contract ────────────────────────────────────────────────────────────

def test_empty_list_returns_empty():
    assert enrich_signals([]) == []


def test_returns_list():
    result = enrich_signals([{"signal_type": "yoga"}])
    assert isinstance(result, list)


def test_length_preserved():
    signals = [{"signal_type": f"sig_{i}"} for i in range(10)]
    result = enrich_signals(signals)
    assert len(result) == 10


def test_original_unmodified():
    sig = {"signal_type": "yoga", "signal_id": "s1"}
    original_keys = set(sig.keys())
    enrich_signals([sig])
    assert set(sig.keys()) == original_keys


def test_result_is_new_dicts():
    sig = {"signal_type": "yoga"}
    result = enrich_signals([sig])
    assert result[0] is not sig


# ── source_corroboration_count ────────────────────────────────────────────────

def test_default_count_is_1():
    result = enrich_signals([{"signal_type": "yoga"}])
    assert result[0]["source_corroboration_count"] == 1


def test_existing_count_preserved():
    result = enrich_signals([{"signal_type": "yoga", "source_corroboration_count": 3}])
    assert result[0]["source_corroboration_count"] == 3


def test_zero_count_preserved():
    result = enrich_signals([{"signal_type": "yoga", "source_corroboration_count": 0}])
    assert result[0]["source_corroboration_count"] == 0


# ── verification_certainty ────────────────────────────────────────────────────

def test_vc_added_to_result():
    result = enrich_signals([{"signal_type": "yoga"}])
    assert "verification_certainty" in result[0]


def test_vc_matches_salience_formula_count_1():
    result = enrich_signals([{"signal_type": "yoga"}])
    assert result[0]["verification_certainty"] == pytest.approx(verification_certainty(1))


def test_vc_matches_salience_formula_count_3():
    result = enrich_signals([{"signal_type": "yoga", "source_corroboration_count": 3}])
    assert result[0]["verification_certainty"] == pytest.approx(verification_certainty(3))


def test_vc_matches_salience_formula_count_0():
    result = enrich_signals([{"signal_type": "yoga", "source_corroboration_count": 0}])
    assert result[0]["verification_certainty"] == pytest.approx(verification_certainty(0))


def test_vc_range():
    for count in range(6):
        result = enrich_signals([{"signal_type": "yoga", "source_corroboration_count": count}])
        vc = result[0]["verification_certainty"]
        assert 0.0 <= vc <= 1.0


# ── chart_facts parameter ─────────────────────────────────────────────────────

def test_chart_facts_none_default():
    result = enrich_signals([{"signal_type": "yoga"}], chart_facts=None)
    assert len(result) == 1


def test_chart_facts_passed_does_not_crash():
    result = enrich_signals([{"signal_type": "yoga"}], chart_facts={"some": "data"})
    assert len(result) == 1


# ── Multiple signals ──────────────────────────────────────────────────────────

def test_multiple_signals_each_gets_vc():
    signals = [
        {"signal_type": "yoga", "source_corroboration_count": n}
        for n in range(1, 5)
    ]
    result = enrich_signals(signals)
    for i, sig in enumerate(result):
        expected_vc = verification_certainty(i + 1)
        assert sig["verification_certainty"] == pytest.approx(expected_vc)


def test_original_fields_preserved():
    sig = {
        "signal_type": "yoga_raj",
        "signal_id": "s_001",
        "configuration": "Sun-Moon",
        "computed_salience": 0.88,
    }
    result = enrich_signals([sig])
    enriched = result[0]
    assert enriched["signal_type"] == "yoga_raj"
    assert enriched["signal_id"] == "s_001"
    assert enriched["configuration"] == "Sun-Moon"
    assert enriched["computed_salience"] == pytest.approx(0.88)
