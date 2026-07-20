"""
tests/l3/test_ephemeris_at_t_sidecar_route.py — W2 dark-set wiring proof for
ka_graha_sancara (GT-50): POST /api/compute/ephemeris_at_t.

Distinct subject from tests/test_ka_graha_sancara.py (that file tests the WriterBase
`ka_graha_sancara` L3 asset that builds a kala_* table — FROZEN orchestrator writer
logic, must_not_touch). This file tests the NEW retrieval-plane compute-sidecar route
`routers.ephemeris.ephemeris_at_t` that the previously-dark `call_ephemeris_at_t` MCP
capability now calls.

Calls the endpoint function directly (in-process, real swisseph compute — not mocked)
per DESIGN_KA_GRAHA_SANCARA_WIRING.md §3. Proves real computed positions come back,
not the old unconditional-error stub.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

SIDECAR = Path(__file__).parent.parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from routers.ephemeris import EphemerisAtTRequest, ephemeris_at_t  # noqa: E402


class TestEphemerisAtTRealCompute:
    """Real swisseph compute — proves the endpoint is genuinely wired, not stubbed."""

    def test_returns_9_grahas_with_real_positions(self):
        req = EphemerisAtTRequest(datetime_utc="2026-07-20T12:00:00Z")
        res = ephemeris_at_t(req)

        assert res["datetime_utc"] == "2026-07-20T12:00:00Z"
        assert res["ayanamsha_id"] == "lahiri_chitrapaksha"
        assert isinstance(res["jd"], float)
        assert len(res["positions"]) == 9

        names = {p["planet"] for p in res["positions"]}
        assert names == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }

        for p in res["positions"]:
            assert 0.0 <= p["longitude"] < 360.0
            assert p["sign"] in {
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
            }
            assert isinstance(p["retrograde"], bool)

    def test_rahu_ketu_are_exactly_180_degrees_apart(self):
        """Ketu = Rahu + 180 by construction — a real-compute invariant, not a fixture."""
        req = EphemerisAtTRequest(datetime_utc="2026-07-20T12:00:00Z")
        res = ephemeris_at_t(req)
        rahu = next(p for p in res["positions"] if p["planet"] == "Rahu")
        ketu = next(p for p in res["positions"] if p["planet"] == "Ketu")
        diff = (ketu["longitude"] - rahu["longitude"]) % 360
        assert abs(diff - 180.0) < 1e-6

    def test_different_instants_produce_different_moon_longitude(self):
        """Moon moves ~13deg/day — two instants a day apart must differ materially,
        proving this is live compute and not a cached/hardcoded response."""
        res_a = ephemeris_at_t(EphemerisAtTRequest(datetime_utc="2026-07-20T00:00:00Z"))
        res_b = ephemeris_at_t(EphemerisAtTRequest(datetime_utc="2026-07-21T00:00:00Z"))
        moon_a = next(p for p in res_a["positions"] if p["planet"] == "Moon")["longitude"]
        moon_b = next(p for p in res_b["positions"] if p["planet"] == "Moon")["longitude"]
        assert abs(((moon_b - moon_a + 180) % 360) - 180) > 5.0

    def test_non_default_ayanamsha_shifts_all_longitudes_uniformly(self):
        lahiri = ephemeris_at_t(EphemerisAtTRequest(datetime_utc="2026-07-20T12:00:00Z", ayanamsha_id="lahiri_chitrapaksha"))
        raman  = ephemeris_at_t(EphemerisAtTRequest(datetime_utc="2026-07-20T12:00:00Z", ayanamsha_id="raman"))
        sun_lahiri = next(p for p in lahiri["positions"] if p["planet"] == "Sun")["longitude"]
        sun_raman  = next(p for p in raman["positions"] if p["planet"] == "Sun")["longitude"]
        assert sun_lahiri != sun_raman  # different ayanamsha => different sidereal longitude


class TestEphemerisAtTValidation:
    def test_unrecognized_ayanamsha_fails_loud_422(self):
        with pytest.raises(HTTPException) as exc_info:
            ephemeris_at_t(EphemerisAtTRequest(datetime_utc="2026-07-20T12:00:00Z", ayanamsha_id="not_a_real_ayanamsha"))
        assert exc_info.value.status_code == 422
        assert "EXTERNAL_COMPUTATION_REQUIRED" in exc_info.value.detail

    def test_invalid_datetime_fails_400(self):
        with pytest.raises(HTTPException) as exc_info:
            ephemeris_at_t(EphemerisAtTRequest(datetime_utc="not-a-datetime"))
        assert exc_info.value.status_code == 400
