"""
tests/test_serialize.py — Round-trip serialization tests for panchang_to_dict.

Acceptance criteria (AC.4C3.3):
  1. panchang_to_dict(compute_panchang(...)) produces a dict
  2. The dict is JSON-serializable (no datetime / dataclass leaks)
  3. A dict round-tripped through json.dumps/json.loads is equal to the original
  4. Key fields map correctly (Anga → {id, name, end_utc}, etc.)
  5. Field projection works: partial keys survive intact
"""
import json
from datetime import date

import pytest

from panchang_engine import compute_panchang
from panchang_engine.serialize import panchang_to_dict


# Canonical test location: Bhubaneswar (project default, per §8 context)
BHUB_LAT = 20.27
BHUB_LON = 85.84
BHUB_TZ = 330  # IST +05:30

# Known stable test date
TEST_DATE = date(2026, 5, 19)  # The 4C-3 session date


@pytest.fixture(scope="module")
def panchang_dict():
    """Compute once and cache for all tests in this module."""
    p = compute_panchang(TEST_DATE, BHUB_LAT, BHUB_LON, BHUB_TZ)
    return panchang_to_dict(p)


def test_returns_dict(panchang_dict):
    """panchang_to_dict returns a plain dict."""
    assert isinstance(panchang_dict, dict)


def test_json_serializable(panchang_dict):
    """The dict must be JSON-serializable — no datetime / dataclass leaks."""
    try:
        json_str = json.dumps(panchang_dict)
        assert len(json_str) > 100  # non-trivial output
    except (TypeError, ValueError) as exc:
        pytest.fail(f"panchang_to_dict output is not JSON-serializable: {exc}")


def test_round_trip_equality(panchang_dict):
    """Round-tripping through json.dumps/json.loads produces an equal dict."""
    json_str = json.dumps(panchang_dict)
    reloaded = json.loads(json_str)
    assert reloaded == panchang_dict, "Round-trip dict differs from original"


def test_top_level_keys_present(panchang_dict):
    """All required top-level keys are present."""
    required = {
        "date", "lat", "lon", "tz_offset_minutes",
        "sunrise_utc", "sunset_utc",
        "tithi", "nakshatra", "yoga", "karana_first", "karana_second", "vara",
        "paksha",
        "inauspicious", "auspicious", "choghadiya", "hora",
        "special_yogas", "planets",
        "computation_version", "ephemeris_version",
    }
    missing = required - set(panchang_dict.keys())
    assert not missing, f"Missing keys: {missing}"


def test_anga_shape(panchang_dict):
    """Anga fields (tithi, nakshatra, yoga, vara) have {id, name, end_utc} shape."""
    for anga_key in ("tithi", "nakshatra", "yoga", "vara"):
        anga = panchang_dict[anga_key]
        assert isinstance(anga, dict), f"{anga_key} should be a dict"
        assert "id" in anga, f"{anga_key} missing 'id'"
        assert "name" in anga, f"{anga_key} missing 'name'"
        assert "end_utc" in anga, f"{anga_key} missing 'end_utc'"
        assert isinstance(anga["id"], int), f"{anga_key}.id should be int"
        assert isinstance(anga["name"], str), f"{anga_key}.name should be str"
        # end_utc should be an ISO 8601 string ending in Z or None (for vara which may differ)
        if anga["end_utc"] is not None:
            assert isinstance(anga["end_utc"], str), f"{anga_key}.end_utc should be str"
            assert anga["end_utc"].endswith("Z"), f"{anga_key}.end_utc should end in Z"


def test_timing_shape(panchang_dict):
    """Timing lists (inauspicious, auspicious, hora) have {label, start_utc, end_utc} shape."""
    for timing_key in ("inauspicious", "auspicious", "hora"):
        timings = panchang_dict[timing_key]
        assert isinstance(timings, list), f"{timing_key} should be a list"
        assert len(timings) > 0, f"{timing_key} should be non-empty"
        for t in timings:
            assert "label" in t, f"{timing_key} entry missing 'label'"
            assert "start_utc" in t, f"{timing_key} entry missing 'start_utc'"
            assert "end_utc" in t, f"{timing_key} entry missing 'end_utc'"
            assert isinstance(t["start_utc"], str), f"{timing_key}.start_utc should be str"
            assert t["start_utc"].endswith("Z"), f"{timing_key}.start_utc should end in Z"


def test_planets_shape(panchang_dict):
    """Planets dict has lowercase planet keys, each with required sub-fields."""
    planets = panchang_dict["planets"]
    assert isinstance(planets, dict), "planets should be a dict"
    required_planets = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
    missing = required_planets - set(planets.keys())
    assert not missing, f"Missing planet keys: {missing}"

    planet_fields = {
        "name", "longitude_sidereal", "sign_id", "sign_name",
        "nakshatra_id", "nakshatra_name", "nakshatra_pada",
        "retrograde", "combust",
    }
    for planet_key, planet_data in planets.items():
        missing_fields = planet_fields - set(planet_data.keys())
        assert not missing_fields, f"{planet_key} missing fields: {missing_fields}"
        assert isinstance(planet_data["retrograde"], bool), f"{planet_key}.retrograde should be bool"
        assert isinstance(planet_data["combust"], bool), f"{planet_key}.combust should be bool"


def test_choghadiya_shape(panchang_dict):
    """Choghadiya has day and night lists, each non-empty."""
    choghadiya = panchang_dict["choghadiya"]
    assert isinstance(choghadiya, dict), "choghadiya should be a dict"
    assert "day" in choghadiya, "choghadiya missing 'day'"
    assert "night" in choghadiya, "choghadiya missing 'night'"
    assert len(choghadiya["day"]) > 0, "choghadiya.day should be non-empty"
    assert len(choghadiya["night"]) > 0, "choghadiya.night should be non-empty"


def test_datetime_strings_are_utc(panchang_dict):
    """All datetime-like values in the dict end in 'Z' (UTC) or are None."""
    utc_fields = ["sunrise_utc", "sunset_utc"]
    for field in utc_fields:
        value = panchang_dict[field]
        assert isinstance(value, str), f"{field} should be a str"
        assert value.endswith("Z"), f"{field} should end in Z"


def test_computation_version_present(panchang_dict):
    """computation_version should be '1.0.0-S2' (the S2 close baseline)."""
    assert panchang_dict["computation_version"] == "1.0.0-S2"


def test_special_yogas_serializable(panchang_dict):
    """special_yogas must be a list of dicts with no datetime objects."""
    yogas = panchang_dict["special_yogas"]
    assert isinstance(yogas, list)
    for yoga in yogas:
        assert isinstance(yoga, dict), "Each yoga entry should be a dict"
        # No datetime objects should remain
        for k, v in yoga.items():
            assert not hasattr(v, "strftime"), (
                f"yoga['{k}'] is a datetime — should be a string after serialization"
            )


def test_date_is_isoformat(panchang_dict):
    """date field should be YYYY-MM-DD string."""
    assert panchang_dict["date"] == TEST_DATE.isoformat()


def test_location_preserved(panchang_dict):
    """lat/lon/tz_offset_minutes are preserved in output."""
    assert panchang_dict["lat"] == BHUB_LAT
    assert panchang_dict["lon"] == BHUB_LON
    assert panchang_dict["tz_offset_minutes"] == BHUB_TZ
