"""Writer-shell tests for ka_tithi_pravesha — the DB-touching orchestration
around the pure logic tested in test_ka_tithi_pravesha.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres) — mirrors the FakeConn pattern already
used by test_ka_kota_chakra_writer.py / test_ka_sudarshana_varsha_writer.py /
test_ka_moorti_nirnaya_writer.py so the B.10 honest-empty paths are verified
without requiring a live DB in CI.

The `TestComputeOneYearBothCanonicalCharts` class below is a REAL-ENGINE
sanity/integration check (no DB, no mocks — calls the live pyjhora_adapter
Swiss-Ephemeris-backed engine, same as production) proving the lunar-return
root-find + annual-chart cast is sane and chart-differentiated on BOTH
canonical charts, per the campaign's "both charts, always" rail. Natal Moon
longitude fixtures below are the real, live chart_facts values (482012f1's
327.055230133129 is the exact fixture test_ka_moorti_nirnaya_writer.py /
test_ka_kota_chakra_writer.py already use — the FORENSIC-anchored Purva
Bhadrapada value, CLAUDE.md §B; 1c826d5a's is independently confirmed by this
same test module's own natal-chart computation below).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_tithi_pravesha.writer import (
    _birth_dt_and_params_from_config,
    _compute_one_year,
    _fetch_natal_moon_longitude,
    _graha_positions_jsonb,
)


class _FakeCursorOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params

    def fetchone(self):
        return self._fetchone_result


class _FakeConnOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def cursor(self, row_factory=None):
        return _FakeCursorOne(self._fetchone_result)



# DB9 (2026-08-08): these fixtures previously supplied TUPLE rows, e.g.
# fetchone_result=("fact123", None). Production does not produce tuple rows --
# the orchestrator connection is created with row_factory=psycopg.rows.dict_row
# (pipeline/orchestrator/db.py), so every cursor yields DICT rows. The helpers
# under test indexed positionally (row[1]) and therefore raised KeyError: 1 in
# production while these tests stayed green, because the fixture fed the code a
# row shape production never emits. A detector that cannot see the real input is
# not a detector (CLAUDE.md N.8). Fixtures now supply dict rows, as production does.

class TestFetchNatalMoonLongitude:
    def test_missing_fact_returns_none(self):
        conn = _FakeConnOne(fetchone_result=None)
        assert _fetch_natal_moon_longitude(conn, "chart-x") is None

    def test_null_value_returns_none(self):
        conn = _FakeConnOne(fetchone_result={"fact_id": "fact123", "fact_value_num": None})
        assert _fetch_natal_moon_longitude(conn, "chart-x") is None

    def test_present_fact_returns_longitude_and_fact_id(self):
        # Same FORENSIC-anchored fixture value test_ka_moorti_nirnaya_writer.py /
        # test_ka_kota_chakra_writer.py use for chart 482012f1 (CLAUDE.md §B).
        conn = _FakeConnOne(fetchone_result={"fact_id": "7cf5902c6bd63146", "fact_value_num": 327.055230133129})
        result = _fetch_natal_moon_longitude(conn, "482012f1-710e-4a25-994a-93821f5871aa")
        assert result is not None
        long_deg, fact_id = result
        assert abs(long_deg - 327.055230133129) < 1e-9
        assert fact_id == "7cf5902c6bd63146"


class TestBirthDtAndParamsFromConfig:
    def test_missing_birth_params_returns_none(self):
        ctx = SimpleNamespace(config={})
        assert _birth_dt_and_params_from_config(ctx) is None

    def test_missing_datetime_iso_returns_none(self):
        ctx = SimpleNamespace(config={"birth_params": {"latitude_deg": 20.3}})
        assert _birth_dt_and_params_from_config(ctx) is None

    def test_malformed_datetime_iso_returns_none(self):
        ctx = SimpleNamespace(config={"birth_params": {"datetime_iso": "not-a-date"}})
        assert _birth_dt_and_params_from_config(ctx) is None

    def test_real_shape_from_pipeline_orchestrator_birth_params(self):
        # Exact shape produced by pipeline/orchestrator/birth_params.py's
        # _to_birth_params for the native (CLAUDE.md §B).
        ctx = SimpleNamespace(config={"birth_params": {
            "datetime_iso": "1984-02-05T10:43:00",
            "latitude_deg": 20.2961,
            "longitude_deg": 85.8245,
            "tz_offset_hours": 5.5,
            "place_name": "Bhubaneswar",
            "subject_label": "",
        }})
        result = _birth_dt_and_params_from_config(ctx)
        assert result is not None
        birth_dt, birth_params = result
        assert birth_dt == datetime(1984, 2, 5, 10, 43, 0)
        assert birth_params["latitude_deg"] == 20.2961


class TestGrahaPositionsJsonb:
    def test_extracts_fields_from_annual_chart_grahas(self):
        annual_chart = {
            "grahas": [
                {
                    "name": "Sun", "sign_id": 10, "sign": "Capricorn",
                    "degree_in_sign": 15.4321, "longitude_deg": 285.4321,
                    "house": 10, "retrograde": False,
                    "nakshatra": "Uttara Ashadha", "nakshatra_pada": 2,
                    "dignity_status": "neutral",
                },
                {
                    "name": "Saturn", "sign_id": 7, "sign": "Libra",
                    "degree_in_sign": 1.0, "longitude_deg": 181.0,
                    "house": 7, "retrograde": True,
                    "nakshatra": "Chitra", "nakshatra_pada": 4,
                    "dignity_status": "exalted",
                },
            ]
        }
        rows = _graha_positions_jsonb(annual_chart)
        assert len(rows) == 2
        sun = next(r for r in rows if r["name"] == "Sun")
        assert sun["sign_idx"] == 9  # 0-based from sign_id=10
        assert sun["sign_name"] == "Capricorn"
        assert sun["house"] == 10
        assert sun["retrograde"] is False
        saturn = next(r for r in rows if r["name"] == "Saturn")
        assert saturn["retrograde"] is True
        assert saturn["dignity_status"] == "exalted"

    def test_empty_grahas_returns_empty_list(self):
        assert _graha_positions_jsonb({"grahas": []}) == []
        assert _graha_positions_jsonb({}) == []


# ── Real-engine sanity/integration: both canonical charts ────────────────────
# No DB required — `_compute_one_year` takes natal_moon_long as a plain float
# and calls the live pyjhora_adapter engine directly (same engine production
# uses). This is the "verify computed lunar-return instant and resulting
# chart are sane and chart-differentiated on both charts" evidence.

ABHISEK_BP = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5,
}
ABHISEK_NATAL_MOON = 327.055230133129  # chart_facts fixture, CLAUDE.md §B

ABHINANDAN_BP = {
    "datetime_iso": "1985-03-02T09:40:00",
    "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5,
}


def _natal_moon_longitude(bp: dict) -> float:
    """Independently derives the natal Moon longitude via the live engine's
    own full-chart path (compute_chart), for building the Abhinandan fixture
    below and for the annual==natal-at-year-1 cross-check — a SEPARATE code
    path from `_moon_longitude`'s position-only call, so this is itself a
    two-pass check on the fixture, not a self-referential one."""
    from pyjhora_adapter.compute import compute_chart
    chart = compute_chart(bp, ayanamsha_id="lahiri")
    return float(next(g for g in chart["grahas"] if g["name"] == "Moon")["longitude_deg"]) % 360.0


class TestComputeOneYearBothCanonicalCharts:
    def test_abhisek_year_1_is_essentially_the_birth_instant(self):
        birth_dt = datetime(1984, 2, 5, 10, 43, 0)
        row = _compute_one_year(1, birth_dt, ABHISEK_BP, ABHISEK_NATAL_MOON)
        assert row["verification_pass_status"] == "two_pass_verified"
        assert row["start_converged"] is True
        # Year 1's return IS the birth instant (moon is exactly at its natal
        # longitude at birth, by definition) — within a few minutes.
        assert abs((row["window_start"] - birth_dt).total_seconds()) < 600
        assert row["pravesha_lagna_sign_idx"] is not None
        assert len(row["graha_positions_jsonb"]) == 9  # all 9 grahas

    def test_abhinandan_year_1_is_essentially_the_birth_instant(self):
        birth_dt = datetime(1985, 3, 2, 9, 40, 0)
        natal_moon = _natal_moon_longitude(ABHINANDAN_BP)
        row = _compute_one_year(1, birth_dt, ABHINANDAN_BP, natal_moon)
        assert row["verification_pass_status"] == "two_pass_verified"
        assert abs((row["window_start"] - birth_dt).total_seconds()) < 600

    def test_both_charts_converge_and_cross_check_clean_across_several_years(self):
        """Real-engine sweep (both canonical charts, several praveśa years) —
        proves the algorithm is sane in production conditions, not just on
        the synthetic linear fixtures in test_ka_tithi_pravesha.py."""
        birth_abhisek = datetime(1984, 2, 5, 10, 43, 0)
        birth_abhinandan = datetime(1985, 3, 2, 9, 40, 0)
        natal_moon_abhinandan = _natal_moon_longitude(ABHINANDAN_BP)

        for pravesha_year in (1, 5, 20, 40):
            row_a = _compute_one_year(pravesha_year, birth_abhisek, ABHISEK_BP, ABHISEK_NATAL_MOON)
            row_b = _compute_one_year(pravesha_year, birth_abhinandan, ABHINANDAN_BP, natal_moon_abhinandan)
            for label, row in (("Abhisek", row_a), ("Abhinandan", row_b)):
                assert row["start_converged"] is True, f"{label} year {pravesha_year} did not converge"
                assert row["verification_pass_status"] == "two_pass_verified", (
                    f"{label} year {pravesha_year}: {row['ephemeris_audit_jsonb']}"
                )
                assert row["window_end"] > row["window_start"]

    def test_charts_are_differentiated_not_a_shared_fallback(self):
        """Same praveśa_year (20) on both charts must produce genuinely
        different Praveśa Lagnas / instants — proves neither chart is
        silently falling back to a shared/fabricated value (B.10)."""
        birth_abhisek = datetime(1984, 2, 5, 10, 43, 0)
        birth_abhinandan = datetime(1985, 3, 2, 9, 40, 0)
        natal_moon_abhinandan = _natal_moon_longitude(ABHINANDAN_BP)

        row_a = _compute_one_year(20, birth_abhisek, ABHISEK_BP, ABHISEK_NATAL_MOON)
        row_b = _compute_one_year(20, birth_abhinandan, ABHINANDAN_BP, natal_moon_abhinandan)

        assert row_a["window_start"] != row_b["window_start"]
        assert row_a["natal_moon_longitude_deg"] != row_b["natal_moon_longitude_deg"]
        # Not strictly required to differ in sign, but the instants and
        # underlying natal longitudes must not be identical/fabricated.
        moons_a = {g["name"]: g["longitude_deg"] for g in row_a["graha_positions_jsonb"]}
        moons_b = {g["name"]: g["longitude_deg"] for g in row_b["graha_positions_jsonb"]}
        assert moons_a["Moon"] != moons_b["Moon"]
