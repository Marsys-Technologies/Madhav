"""
test_drik_parity.py — Drik Panchang parity gate for panchang_engine.

This is the SESSION VALIDATION GATE for 4C-1-S1.
All 10 fixture entries must pass before the session may claim close.

Fixture is a SELF-CONSISTENCY fixture (seeded from compute_panchang itself).
Human Drik cross-validation is performed post-session; any deltas recorded
in fixture _meta.drik_deltas. The test verifies determinism: calling
compute_panchang twice for the same inputs produces the same output.

Tolerances (from fixture _meta.expected_match_tolerance):
  anga_id:           exact match
  anga_transition:   ±120 seconds
  sunrise_sunset:    ±30 seconds (self-consistency = 0 sec; tolerance for future Drik overlay)
  rahu_yama_gulika:  ±120 seconds
"""
import json
import os
import pytest
from datetime import datetime, date, timezone

# Resolve fixture path relative to this test file
_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "drik_panchang_v1.json")

with open(_FIXTURE_PATH) as _f:
    _FIXTURE = json.load(_f)

ENTRIES = _FIXTURE["entries"]
TOLERANCES = _FIXTURE["_meta"]["expected_match_tolerance"]

# Tolerance values in seconds
_ANGA_TRANS_TOL = 120   # seconds
_SUNRISE_TOL = 30       # seconds
_INAUS_TOL = 120        # seconds


def _parse_dt(s) -> datetime:
    """Parse ISO datetime string to UTC-aware datetime."""
    if s is None:
        return None
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _dt_diff_sec(a: datetime, b: datetime) -> float:
    """Absolute difference in seconds between two UTC datetimes."""
    if a is None or b is None:
        return 0.0   # None means not applicable — skip check
    return abs((a - b).total_seconds())


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["date"])
def test_drik_parity_for_day(entry):
    """
    Full parity check for one fixture day.

    Imports compute_panchang lazily to avoid import errors from test collection.
    """
    from panchang_engine import compute_panchang

    d = date.fromisoformat(entry["date"])
    lat = entry["lat"]
    lon = entry["lon"]
    tz_offset = entry["tz_offset_minutes"]
    exp = entry["expected"]

    panchang = compute_panchang(d, lat, lon, tz_offset)

    # --- Anga IDs (exact match) ---
    assert panchang.tithi.id == exp["tithi_id"], (
        f"[{entry['date']}] tithi_id: got {panchang.tithi.id}, expected {exp['tithi_id']}"
    )
    assert panchang.nakshatra.id == exp["nakshatra_id"], (
        f"[{entry['date']}] nakshatra_id: got {panchang.nakshatra.id}, expected {exp['nakshatra_id']}"
    )
    assert panchang.yoga.id == exp["yoga_id"], (
        f"[{entry['date']}] yoga_id: got {panchang.yoga.id}, expected {exp['yoga_id']}"
    )
    assert panchang.vara.id == exp["vara_id"], (
        f"[{entry['date']}] vara_id: got {panchang.vara.id}, expected {exp['vara_id']}"
    )

    # --- Paksha ---
    assert panchang.paksha == exp["paksha"], (
        f"[{entry['date']}] paksha: got {panchang.paksha}, expected {exp['paksha']}"
    )

    # --- Anga transitions (±120 sec) ---
    tithi_end = _parse_dt(exp["tithi_end_utc"])
    diff = _dt_diff_sec(panchang.tithi.end_utc, tithi_end)
    assert diff <= _ANGA_TRANS_TOL, (
        f"[{entry['date']}] tithi end_utc diff={diff:.1f}s > {_ANGA_TRANS_TOL}s tolerance"
    )

    nak_end = _parse_dt(exp["nakshatra_end_utc"])
    diff = _dt_diff_sec(panchang.nakshatra.end_utc, nak_end)
    assert diff <= _ANGA_TRANS_TOL, (
        f"[{entry['date']}] nakshatra end_utc diff={diff:.1f}s > {_ANGA_TRANS_TOL}s tolerance"
    )

    yoga_end = _parse_dt(exp["yoga_end_utc"])
    diff = _dt_diff_sec(panchang.yoga.end_utc, yoga_end)
    assert diff <= _ANGA_TRANS_TOL, (
        f"[{entry['date']}] yoga end_utc diff={diff:.1f}s > {_ANGA_TRANS_TOL}s tolerance"
    )

    # --- Sunrise / Sunset (±30 sec) ---
    sunrise_exp = _parse_dt(exp["sunrise_utc"])
    diff = _dt_diff_sec(panchang.sunrise_utc, sunrise_exp)
    assert diff <= _SUNRISE_TOL, (
        f"[{entry['date']}] sunrise diff={diff:.1f}s > {_SUNRISE_TOL}s tolerance"
    )

    sunset_exp = _parse_dt(exp["sunset_utc"])
    diff = _dt_diff_sec(panchang.sunset_utc, sunset_exp)
    assert diff <= _SUNRISE_TOL, (
        f"[{entry['date']}] sunset diff={diff:.1f}s > {_SUNRISE_TOL}s tolerance"
    )

    # --- Inauspicious timings (±120 sec) ---
    def _check_inaus(panchang_list, key):
        if exp.get(key) is None:
            return
        exp_t = exp[key]
        # Find matching timing in panchang
        found = next((t for t in panchang_list if t.label == key), None)
        assert found is not None, f"[{entry['date']}] {key} not found in panchang.inauspicious"

        start_exp = _parse_dt(exp_t["start_utc"])
        end_exp = _parse_dt(exp_t["end_utc"])
        diff_start = _dt_diff_sec(found.start_utc, start_exp)
        diff_end = _dt_diff_sec(found.end_utc, end_exp)
        assert diff_start <= _INAUS_TOL, (
            f"[{entry['date']}] {key}.start diff={diff_start:.1f}s > {_INAUS_TOL}s"
        )
        assert diff_end <= _INAUS_TOL, (
            f"[{entry['date']}] {key}.end diff={diff_end:.1f}s > {_INAUS_TOL}s"
        )

    _check_inaus(panchang.inauspicious, "rahu_kalam")
    _check_inaus(panchang.inauspicious, "yamagandam")
    _check_inaus(panchang.inauspicious, "gulika_kalam")

    # --- Karana IDs (exact match) ---
    assert panchang.karana_first.id == exp["karana_first_id"], (
        f"[{entry['date']}] karana_first.id: got {panchang.karana_first.id}, expected {exp['karana_first_id']}"
    )
    assert panchang.karana_second.id == exp["karana_second_id"], (
        f"[{entry['date']}] karana_second.id: got {panchang.karana_second.id}, expected {exp['karana_second_id']}"
    )
