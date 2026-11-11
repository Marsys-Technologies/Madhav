"""
test_currents_and_curve.py -- sanity + regression tests for the curve math
port (curve.py/checks.py, ported from t0_retrodiction's TS originals) and
the currents.py candidate-curve combinators (PERMISSION gate proxy, TRIGGER
signed-term proxy). Not the primary compliance test (see test_split_guard.py
for that) -- these confirm the arithmetic is doing what it claims to do.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from kala_admission.curve import DashaPeriod, build_curve, intensity_at, percentile_threshold  # noqa: E402
from kala_admission.currents import (  # noqa: E402
    CurrentsConfig,
    _guru_shani_proxy,
    _papa_kartari_proxy,
    _saham_proxy,
    permission_gate_at,
    signed_trigger_term_at,
)
from kala_admission.dasha_periods import load_dasha_lord_capability, load_dasha_periods  # noqa: E402


def _toy_periods() -> list[DashaPeriod]:
    return [
        DashaPeriod(1, "Jupiter", date(2000, 1, 1), date(2010, 1, 1)),
        DashaPeriod(2, "Saturn", date(2000, 1, 1), date(2003, 1, 1)),
        DashaPeriod(3, "Mars", date(2000, 1, 1), date(2001, 1, 1)),
        DashaPeriod(3, "Rahu", date(2001, 1, 1), date(2003, 1, 1)),
    ]


def test_intensity_at_sums_depth_weighted_matches():
    periods = _toy_periods()
    # 2000-06-01: MD=Jupiter(no match), AD=Saturn(match, w=2), PD=Mars(match, w=4)
    sig = {"Saturn": 1.0, "Mars": 1.0}
    assert intensity_at(periods, sig, date(2000, 6, 1)) == 2 + 4


def test_intensity_at_zero_when_no_significator_running():
    periods = _toy_periods()
    assert intensity_at(periods, {"Venus": 1.0}, date(2000, 6, 1)) == 0.0


def test_percentile_threshold_nearest_rank():
    from kala_admission.curve import CurvePoint

    curve = [CurvePoint(date(2000, 1, i + 1), float(v)) for i, v in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])]
    assert percentile_threshold(curve, 0.9) == 9.0  # top-decile of 10 points, nearest-rank


@pytest.fixture
def synthetic_periods(tmp_path):
    path = tmp_path / "periods.json"
    path.write_text(json.dumps({"periods": [
        [period.level, period.lord, period.start.isoformat(), period.end.isoformat()]
        for period in _toy_periods()
    ]}))
    return load_dasha_periods(path)


def test_permission_gate_uses_capability_floor(synthetic_periods, tmp_path):
    from services.kala_permission.permission import _CAPABILITY_FLOOR

    path = tmp_path / "capability.json"
    path.write_text(json.dumps({"lords": {
        "Jupiter": {"warning_score": 4},
        "Saturn": {"warning_score": 4},
    }}))
    lord_capability = load_dasha_lord_capability(path)["lords"]
    when = date(2000, 6, 1)
    assert permission_gate_at(synthetic_periods, lord_capability, when) == _CAPABILITY_FLOOR
    assert permission_gate_at(synthetic_periods, {}, when) == 1.0


def test_signed_trigger_term_bounded(synthetic_periods):
    when = date(2000, 6, 1)
    for add_w in (0.2, 0.8):
        for sup_w in (0.2, 0.8):
            val = signed_trigger_term_at(synthetic_periods, when, add_w, sup_w)
            assert -1.0 <= val <= 1.0
    assert signed_trigger_term_at(synthetic_periods, when, 0.8, 0.0) > 0.0
    assert signed_trigger_term_at(synthetic_periods, when, 0.0, 0.8) < 0.0


def test_higher_suppressive_weight_never_increases_signed_term(synthetic_periods):
    """Monotonicity sanity check: raising the suppressive weight (holding
    additive fixed) should never INCREASE the signed trigger term, since
    suppressive only ever subtracts."""
    when = date(2000, 6, 1)
    low = signed_trigger_term_at(synthetic_periods, when, 0.5, 0.2)
    high = signed_trigger_term_at(synthetic_periods, when, 0.5, 0.8)
    assert high < low


def test_guru_shani_proxy_requires_both_planets_concurrently():
    periods = _toy_periods()  # Jupiter MD, Saturn AD, 2000-2001 -> both running
    assert _guru_shani_proxy(periods, date(2000, 6, 1)) == 1.0
    only_jupiter = [DashaPeriod(1, "Jupiter", date(2000, 1, 1), date(2010, 1, 1))]
    assert _guru_shani_proxy(only_jupiter, date(2000, 6, 1)) == 0.0


def test_papa_kartari_proxy_requires_two_distinct_malefics():
    periods = _toy_periods()  # Saturn AD + Rahu PD (2001-2003): 2 distinct malefics
    assert _papa_kartari_proxy(periods, date(2002, 1, 1)) == 1.0
    # 2000-2001: Saturn AD + Mars PD -- also 2 distinct malefics
    assert _papa_kartari_proxy(periods, date(2000, 6, 1)) == 1.0
    only_saturn = [DashaPeriod(2, "Saturn", date(2000, 1, 1), date(2010, 1, 1))]
    assert _papa_kartari_proxy(only_saturn, date(2000, 6, 1)) == 0.0


def test_saham_proxy_fires_on_jupiter_dasha_lord_match():
    periods = _toy_periods()  # Jupiter is MD lord throughout
    assert _saham_proxy(periods, date(2000, 6, 1)) == 0.6
    no_jupiter = [DashaPeriod(1, "Saturn", date(2000, 1, 1), date(2010, 1, 1))]
    assert _saham_proxy(no_jupiter, date(2000, 6, 1)) == 0.0
