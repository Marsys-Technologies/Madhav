"""
Tests for pipeline.orchestrator.kala_derivation_completeness_guard (BA Full
Asset Audit #6/#7 — ka_vighnakara / ka_kala_darshana / ka_bhavishya_lekha
0-row derivation-gap guard). DB-free: exercises the pure evaluate() /
evaluate_throughput_drift() functions only.
"""
from __future__ import annotations

from pipeline.orchestrator import kala_derivation_completeness_guard as g


def test_flags_chart_with_upstream_rows_but_empty_derived_table():
    charts_by_table = {
        "kala_convergence": {"chart-a", "chart-b"},
        "kala_obstruction": {"chart-a"},   # chart-b missing — real gap
        "kala_darshana": {"chart-a", "chart-b"},
        "kala_bhavishya": {"chart-a", "chart-b"},
    }
    hard = g.evaluate(charts_by_table)
    assert any("ka_vighnakara" in h and "chart-b" in h for h in hard), hard
    assert not any("ka_kala_darshana" in h for h in hard)
    assert not any("ka_bhavishya_lekha" in h for h in hard)


def test_clean_when_every_upstream_chart_has_a_derived_row():
    charts_by_table = {
        "kala_convergence": {"chart-a"},
        "kala_obstruction": {"chart-a"},
        "kala_darshana": {"chart-a"},
        "kala_bhavishya": {"chart-a"},
    }
    assert g.evaluate(charts_by_table) == []


def test_no_false_positive_when_upstream_itself_is_empty():
    """A chart absent from kala_convergence entirely must never be flagged —
    the legitimate early-return case (no upstream data at all)."""
    charts_by_table = {
        "kala_convergence": set(),
        "kala_obstruction": set(),
        "kala_darshana": set(),
        "kala_bhavishya": set(),
    }
    assert g.evaluate(charts_by_table) == []


def test_throughput_drift_flags_mismatch():
    throughput_and_live = {
        "ka_vighnakara": (10, 10),
        "ka_kala_darshana": (5, 8),   # stale — live count moved on
        "ka_bhavishya_lekha": (None, 3),  # never recorded — not a drift
    }
    drift = g.evaluate_throughput_drift(throughput_and_live)
    assert any("ka_kala_darshana" in d for d in drift), drift
    assert not any("ka_vighnakara" in d for d in drift)
    assert not any("ka_bhavishya_lekha" in d for d in drift)
