"""ŚODHANA T2 (MC-025b): L1 shadbala is the single authority for weakest graha.

Anti-vacuous: the chart-482012f1 shadbala vector (Venus minimum) must resolve to
Venus, NOT Mercury (the composite-resonance answer bo_upaya's weakest_rank uses).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pipeline.orchestrator.writers.bo_upaya import _weakest_graha_by_shadbala


# Live L1 graha_shadbala_total (rupa) for chart 482012f1, normalized /390 by
# _fetch_shadbala. Venus is the minimum (4.64), Mercury is mid-pack (7.55).
_CHART_482012F1 = {
    "Sun": 8.47 / 390.0,
    "Moon": 5.65 / 390.0,
    "Mars": 5.57 / 390.0,
    "Mercury": 7.55 / 390.0,
    "Jupiter": 7.80 / 390.0,
    "Venus": 4.64 / 390.0,
    "Saturn": 7.83 / 390.0,
}


def test_weakest_is_venus_not_mercury_for_482012f1():
    assert _weakest_graha_by_shadbala(_CHART_482012F1) == "Venus"


def test_argmin_invariant_under_normalization():
    raw = {k: v * 390.0 for k, v in _CHART_482012F1.items()}
    assert _weakest_graha_by_shadbala(raw) == _weakest_graha_by_shadbala(_CHART_482012F1)


def test_empty_shadbala_returns_none():
    assert _weakest_graha_by_shadbala({}) is None


def test_single_graha_returns_it():
    assert _weakest_graha_by_shadbala({"Saturn": 0.1}) == "Saturn"
