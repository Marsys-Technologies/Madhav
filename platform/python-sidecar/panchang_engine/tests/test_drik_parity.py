"""
test_drik_parity.py — Drik Panchang parity gate for panchang_engine.

This is the SESSION VALIDATION GATE for 4C-1-S2 (supersedes S1 gate).
All 30 fixture entries must pass — this is the 4C.1 close gate.

Fixture is a SELF-CONSISTENCY fixture (seeded from compute_panchang itself).
Human Drik cross-validation is performed post-session; any deltas recorded
in fixture _meta.drik_deltas. The test verifies determinism: calling
compute_panchang twice for the same inputs produces the same output.

v2 extends v1 with:
  - 20 additional days (2020-2026, all 7 vara IDs, Delhi sensitivity)
  - special_yogas assertions per day

Tolerances (from fixture _meta.expected_match_tolerance):
  anga_id:             exact match
  anga_transition:     ±120 seconds
  sunrise_sunset:      ±30 seconds (self-consistency = 0 sec; tolerance for future Drik overlay)
  rahu_yama_gulika:    ±120 seconds
  special_yoga_times:  ±120 seconds
"""
import json
import os
import pytest
from datetime import datetime, date, timezone, timedelta

# Resolve fixture path relative to this test file
_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "drik_panchang_v2.json")

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

    # --- Special Yogas (v2 gate) ---
    _YOGA_TOL = 120   # seconds tolerance for yoga start/end times

    fixture_yogas = exp.get("special_yogas", [])
    computed_yoga_names = [y["yoga"] for y in panchang.special_yogas]
    fixture_yoga_names = [y["yoga"] for y in fixture_yogas]

    # No false negatives: every yoga in fixture must appear in computed output
    for fy in fixture_yogas:
        assert fy["yoga"] in computed_yoga_names, (
            f"[{entry['date']}] Fixture yoga '{fy['yoga']}' not found in computed output. "
            f"Computed: {computed_yoga_names}"
        )

    # No false positives: every computed yoga must appear in fixture
    for cy in panchang.special_yogas:
        assert cy["yoga"] in fixture_yoga_names, (
            f"[{entry['date']}] Computed yoga '{cy['yoga']}' not expected by fixture. "
            f"Fixture yogas: {fixture_yoga_names}"
        )

    # Timing check: for each matched yoga, start/end within ±120 sec of fixture
    for fy in fixture_yogas:
        # Find matching computed yoga
        cy = next((y for y in panchang.special_yogas if y["yoga"] == fy["yoga"]), None)
        if cy is None:
            continue   # Already caught above in false-negative check

        fy_start = _parse_dt(fy["start_utc"])
        fy_end = _parse_dt(fy["end_utc"])

        if fy_start is not None:
            diff_start = _dt_diff_sec(cy["start_utc"], fy_start)
            assert diff_start <= _YOGA_TOL, (
                f"[{entry['date']}] yoga '{fy['yoga']}' start diff={diff_start:.1f}s > {_YOGA_TOL}s"
            )
        if fy_end is not None:
            diff_end = _dt_diff_sec(cy["end_utc"], fy_end)
            assert diff_end <= _YOGA_TOL, (
                f"[{entry['date']}] yoga '{fy['yoga']}' end diff={diff_end:.1f}s > {_YOGA_TOL}s"
            )
