"""Orchestrator Convergence Phase 3B — per-chart writer generalization.

Proves:
  A. birth_params provider: native → None (writer uses NATIVE_BIRTH); a non-native
     charts row → NATIVE_BIRTH-shaped dict (tz from IANA timezone_id); missing data
     → loud ValueError (never a silently-wrong chart); no row → ValueError (non-native
     chart with no charts row raises rather than silently falling back to native).
  B. ga_dashas birth threading: _birth_jd_utc / _get_moon_position honor an injected
     birth; the native default is unchanged.
  C. FORENSIC native-guard: the native-anchored gate halts for the NATIVE chart but
     does NOT halt a non-native chart (so a non-native build completes), proven on
     ga_dashas.build_system.
"""
import sys
import pathlib
from datetime import date, time
from unittest.mock import patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.birth_params import (  # noqa: E402
    fetch_birth_params, CANONICAL_CHART_ID,
)


# ── Fakes ───────────────────────────────────────────────────────────────────────

class _Cur:
    def __init__(self, row):
        self._row = row

    def execute(self, *a, **k):
        return self

    def fetchone(self):
        return self._row


class _Conn:
    def __init__(self, row):
        self._row = row

    def execute(self, *a, **k):
        return _Cur(self._row)


_ROW = {
    'birth_date': date(1990, 6, 15), 'birth_time': time(14, 30),
    'birth_lat': 28.61, 'birth_lng': 77.21, 'birth_place': 'Delhi',
    'timezone_id': 'Asia/Kolkata', 'label': 'Test Subject',
}


# ── A. birth_params provider ─────────────────────────────────────────────────────

def test_native_returns_none():
    assert fetch_birth_params(_Conn(None), CANONICAL_CHART_ID) is None


def test_non_native_row_maps_to_birth_params():
    bp = fetch_birth_params(_Conn(_ROW), 'some-other-chart')
    assert bp == {
        'datetime_iso': '1990-06-15T14:30:00',
        'latitude_deg': 28.61, 'longitude_deg': 77.21,
        'tz_offset_hours': 5.5, 'place_name': 'Delhi',
        'subject_label': 'Test Subject',
    }


def test_non_native_missing_row_raises():
    """Non-native chart_id with no row in public.charts raises ValueError (no silent native fallback)."""
    with pytest.raises(ValueError, match="no charts row found"):
        fetch_birth_params(_Conn(None), "no-such-chart")


@pytest.mark.parametrize('missing', ['birth_date', 'birth_time', 'birth_lat', 'birth_lng', 'timezone_id'])
def test_missing_required_field_raises(missing):
    row = {**_ROW, missing: None}
    with pytest.raises(ValueError):
        fetch_birth_params(_Conn(row), 'c')


def test_unknown_timezone_raises():
    with pytest.raises(ValueError):
        fetch_birth_params(_Conn({**_ROW, 'timezone_id': 'Not/AZone'}), 'c')


def test_western_negative_offset():
    row = {**_ROW, 'timezone_id': 'America/New_York'}  # EDT in June = -4
    bp = fetch_birth_params(_Conn(row), 'c')
    assert bp['tz_offset_hours'] == -4.0


# ── B + C. ga_dashas birth threading + FORENSIC native-guard ─────────────────────

def _dashas():
    import ga_writers.ga_dashas_writer as gdw
    return gdw


def test_birth_jd_default_is_native():
    gdw = _dashas()
    assert gdw._birth_jd_utc() == gdw._birth_jd_utc(None)


def test_birth_jd_honors_injected_birth():
    gdw = _dashas()
    other = {'datetime_iso': '1990-06-15T14:30:00', 'tz_offset_hours': 5.5}
    assert gdw._birth_jd_utc(other) != gdw._birth_jd_utc(None)


def test_forensic_halts_for_native_chart():
    """Native chart + wrong Moon ⇒ FORENSIC HALT still fires (regression guard intact)."""
    gdw = _dashas()
    wrong_moon = 2.0  # Ashwini → Ketu, not the native's Jupiter anchor
    with patch.object(gdw, '_get_moon_position', side_effect=lambda aya, birth=None: (wrong_moon, gdw._birth_jd_utc())):
        with pytest.raises(ValueError, match='FORENSIC HALT'):
            gdw.build_system('vimshottari', 'lahiri_chitrapaksha',
                             chart_id=CANONICAL_CHART_ID, skip_db=True)


def test_forensic_does_not_halt_for_non_native_chart():
    """Non-native chart + 'wrong' Moon ⇒ NO halt (no native anchor to assert) ⇒ build proceeds.

    Fix 1.2 (Wave 2 carryover): non-native charts must supply birth_params so that
    resolve_birth_params() does not raise ValueError. The test now passes a minimal
    valid birth_params dict — this mirrors the real orchestrator path where
    birth_params is always injected for non-native charts.
    """
    gdw = _dashas()
    wrong_moon = 2.0
    non_native_birth = {
        "datetime_iso": "1990-06-15T08:00:00",
        "latitude_deg": 28.6,
        "longitude_deg": 77.2,
        "tz_offset_hours": 5.5,
        "place_name": "Delhi, India",
        "subject_label": "Test Chart",
    }
    with patch.object(gdw, '_get_moon_position', side_effect=lambda aya, birth=None: (wrong_moon, gdw._birth_jd_utc())):
        result = gdw.build_system('vimshottari', 'lahiri_chitrapaksha',
                                  chart_id='non-native-chart-xyz', skip_db=True,
                                  birth_params=non_native_birth)
    assert result['status'] == 'PASS'
    assert result['rows_computed'] > 0
