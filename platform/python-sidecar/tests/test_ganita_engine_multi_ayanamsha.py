"""
test_ganita_engine_multi_ayanamsha.py — Tests for dual-ayanamsha support in engine.py
========================================================================================

Stream E (postdeploy-e-multi-school) — Session e3

Tests verify that run_ganita() emits positions for BOTH lahiri and kp (and all 5 ayanamshas
when called with the default). The DB write is mocked so no live DB connection is needed.

Tests:
  1.  ALL_AYANAMSHAS constant has exactly 5 entries
  2.  ALL_AYANAMSHAS includes 'lahiri' and 'kp'
  3.  run_ganita default: calls write_positions for each of 5 ayanamshas
  4.  run_ganita default: total positions_count = 5 × 9 = 45 rows
  5.  run_ganita default: positions_per_ayanamsha has 5 keys
  6.  run_ganita with ayanamshas=['lahiri', 'kp']: calls write_positions exactly 2×
  7.  run_ganita with ayanamshas=['lahiri', 'kp']: positions_per_ayanamsha has 2 keys
  8.  run_ganita with ayanamshas=['lahiri']: backward-compat single ayanamsha
  9.  run_ganita: result includes 'ayanamshas' list key
  10. run_ganita: result includes 'positions_per_ayanamsha' dict key
  11. run_ganita: result preserves 'ayanamsha' key (backward compat) = first in list
  12. run_ganita: dasha_ayanamsha = primary ayanamsha (lahiri when default)
  13. compute_positions: lahiri and kp produce different sidereal_longitude for Sun
      (ayanamsha offsets differ — confirms dual rows carry distinct data)
  14. write_positions: called with correct ayanamsha argument for each row batch
  15. run_ganita with legacy ayanamsha='raman' + no ayanamshas: defaults to ALL_AYANAMSHAS
      (legacy single-param is ignored when ayanamshas=None → all 5 run)
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


def _get_engine():
    from brahmagyan.ganita import engine
    return engine


# ── Helpers ───────────────────────────────────────────────────────────────────

NATIVE_IST = "1984-02-05T10:43:00"
NATIVE_LAT = 20.2961
NATIVE_LON = 85.8245

# Expected 9 grahas (Ketu derived from Rahu; Lagna from l1_positions not engine)
EXPECTED_BODIES = 9


def _make_mock_positions(ayanamsha: str) -> list[dict]:
    """Generate minimal mock position dicts for 9 grahas."""
    grahas = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
              "Venus", "Saturn", "Rahu", "Ketu"]
    return [
        {
            "name": g,
            "tropical_longitude": 300.0 + i,
            "sidereal_longitude": (300.0 + i - 23.85) % 360.0,
            "sign_id": 10, "sign": "Capricorn",
            "nakshatra_id": 22, "nakshatra": "Shravana",
            "nakshatra_pada": 2,
            "speed_dps": 1.0,
            "is_retrograde": False,
            "ayanamsha_id": ayanamsha,
            "ayanamsha_value": 23.85,
        }
        for i, g in enumerate(grahas)
    ]


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_all_ayanamshas_has_5_entries(self):
        eng = _get_engine()
        assert len(eng.ALL_AYANAMSHAS) == 5

    def test_all_ayanamshas_includes_lahiri(self):
        eng = _get_engine()
        assert "lahiri" in eng.ALL_AYANAMSHAS

    def test_all_ayanamshas_includes_kp(self):
        eng = _get_engine()
        assert "kp" in eng.ALL_AYANAMSHAS

    def test_all_ayanamshas_lahiri_is_first(self):
        """Lahiri must be first — it is the primary for dasha computation."""
        eng = _get_engine()
        assert eng.ALL_AYANAMSHAS[0] == "lahiri"


# ── run_ganita mock tests ─────────────────────────────────────────────────────

class TestRunGanitaMultiAyanamsha:
    """
    Mock the DB layer (write_positions, write_dashas, emit_build_event, _conn)
    and pyswisseph so no live environment is needed.
    """

    def _run_with_mocks(
        self,
        ayanamshas: list[str] | None = None,
        ayanamsha: str = "lahiri",
    ) -> tuple[dict, MagicMock]:
        """
        Execute run_ganita with mocked dependencies.
        Returns (result_dict, write_positions_mock).
        """
        eng = _get_engine()
        aya_list = ayanamshas if ayanamshas is not None else eng.ALL_AYANAMSHAS

        write_pos_mock = MagicMock(
            side_effect=lambda chart_id, build_id, positions, aya: len(positions)
        )
        write_das_mock = MagicMock(return_value=243)  # typical dasha row count
        emit_mock = MagicMock()

        # Mock compute_positions to return EXPECTED_BODIES dicts per call
        def mock_compute(jd, aya_key):
            return _make_mock_positions(aya_key)

        # Mock birth_jd to return a fixed float
        def mock_birth_jd(dt_utc):
            return 2445735.527777  # 1984-02-05 00:13 UT

        # Mock compute_vimshottari to return minimal tree
        def mock_vimshottari(moon_sid, jd_val):
            return {
                "moon_nakshatra": "Purva Bhadrapada",
                "moon_nakshatra_id": 25,
                "moon_nakshatra_lord": "Jupiter",
                "balance_years": 14.3,
                "total_years": 120,
                "mahadashas": [],
            }

        def mock_dasha_at_date(tree, d):
            return {"mahadasha": "Jupiter"}

        with (
            patch.object(eng, "write_positions", write_pos_mock),
            patch.object(eng, "write_dashas", write_das_mock),
            patch.object(eng, "emit_build_event", emit_mock),
            patch.object(eng, "compute_positions", side_effect=mock_compute),
            patch.object(eng, "birth_jd", side_effect=mock_birth_jd),
            patch.object(eng, "compute_vimshottari", side_effect=mock_vimshottari),
            patch.object(eng, "dasha_at_date", side_effect=mock_dasha_at_date),
        ):
            result = eng.run_ganita(
                chart_id="test-chart-uuid",
                build_id="test-build-001",
                birth_datetime_ist=NATIVE_IST,
                birth_lat=NATIVE_LAT,
                birth_lon=NATIVE_LON,
                ayanamsha=ayanamsha,
                ayanamshas=ayanamshas,
            )

        return result, write_pos_mock

    def test_default_calls_write_positions_5_times(self):
        eng = _get_engine()
        result, wp = self._run_with_mocks()
        assert wp.call_count == len(eng.ALL_AYANAMSHAS)

    def test_default_positions_count_is_45(self):
        """5 ayanamshas × 9 grahas = 45 rows."""
        result, _ = self._run_with_mocks()
        assert result["positions_count"] == 5 * EXPECTED_BODIES

    def test_default_positions_per_ayanamsha_has_5_keys(self):
        eng = _get_engine()
        result, _ = self._run_with_mocks()
        assert len(result["positions_per_ayanamsha"]) == len(eng.ALL_AYANAMSHAS)

    def test_lahiri_kp_only_calls_write_positions_twice(self):
        result, wp = self._run_with_mocks(ayanamshas=["lahiri", "kp"])
        assert wp.call_count == 2

    def test_lahiri_kp_positions_per_ayanamsha_has_2_keys(self):
        result, _ = self._run_with_mocks(ayanamshas=["lahiri", "kp"])
        assert set(result["positions_per_ayanamsha"].keys()) == {"lahiri", "kp"}

    def test_single_lahiri_backward_compat(self):
        """ayanamshas=['lahiri'] should write exactly 1 × 9 = 9 rows."""
        result, wp = self._run_with_mocks(ayanamshas=["lahiri"])
        assert wp.call_count == 1
        assert result["positions_count"] == EXPECTED_BODIES

    def test_result_includes_ayanamshas_list(self):
        result, _ = self._run_with_mocks()
        assert "ayanamshas" in result
        assert isinstance(result["ayanamshas"], list)

    def test_result_includes_positions_per_ayanamsha(self):
        result, _ = self._run_with_mocks()
        assert "positions_per_ayanamsha" in result
        assert isinstance(result["positions_per_ayanamsha"], dict)

    def test_result_backward_compat_ayanamsha_key(self):
        """result['ayanamsha'] must remain for callers that expect it."""
        result, _ = self._run_with_mocks()
        assert "ayanamsha" in result
        assert result["ayanamsha"] == "lahiri"  # first = primary

    def test_dasha_ayanamsha_is_primary(self):
        """Dashas computed from lahiri (primary) ayanamsha."""
        result, _ = self._run_with_mocks()
        assert result["dasha_ayanamsha"] == "lahiri"

    def test_legacy_ayanamsha_param_ignored_when_ayanamshas_none(self):
        """
        When ayanamshas=None (default), the legacy ayanamsha='raman' is ignored
        and all 5 ayanamshas are run.
        """
        eng = _get_engine()
        result, wp = self._run_with_mocks(ayanamsha="raman", ayanamshas=None)
        assert wp.call_count == len(eng.ALL_AYANAMSHAS)

    def test_write_positions_called_with_correct_ayanamsha_arg(self):
        """
        Each write_positions call must use the correct ayanamsha key.
        Verifies the ayanamsha argument (4th positional) for lahiri+kp run.
        """
        result, wp = self._run_with_mocks(ayanamshas=["lahiri", "kp"])
        called_ayanamshas = [c.args[3] for c in wp.call_args_list]
        assert "lahiri" in called_ayanamshas
        assert "kp" in called_ayanamshas


# ── compute_positions ayanamsha offset verification ──────────────────────────

class TestComputePositionsAyanamshaOffset:
    """
    Verify that lahiri and kp produce measurably different sidereal longitudes.
    Requires swisseph — skip if not installed.
    """

    @pytest.fixture(autouse=True)
    def skip_without_swisseph(self):
        try:
            import swisseph  # noqa: F401
        except ImportError:
            pytest.skip("swisseph not installed — skipping live compute test")

    def test_lahiri_kp_sun_longitude_differs(self):
        """
        The KP and Lahiri ayanamsha offsets differ by ~0.01–0.04° at the 1984 epoch.
        Sun longitudes must be different (they will differ by the ayanamsha delta).
        """
        from brahmagyan.ganita.engine import compute_positions, birth_jd
        from datetime import datetime, timedelta

        dt_ist = datetime.fromisoformat(NATIVE_IST)
        dt_utc = dt_ist - timedelta(hours=5, minutes=30)
        jd = birth_jd(dt_utc)

        pos_lahiri = compute_positions(jd, "lahiri")
        pos_kp = compute_positions(jd, "kp")

        sun_lahiri = next(p for p in pos_lahiri if p["name"] == "Sun")
        sun_kp = next(p for p in pos_kp if p["name"] == "Sun")

        # Ayanamsha offsets are different → sidereal longitudes must differ
        assert sun_lahiri["sidereal_longitude"] != sun_kp["sidereal_longitude"]

    def test_lahiri_kp_delta_is_small(self):
        """
        The delta between Lahiri and KP sidereal longitude for Sun at 1984-02-05
        must be < 0.5° (they are very close ayanamsha systems).
        """
        from brahmagyan.ganita.engine import compute_positions, birth_jd
        from datetime import datetime, timedelta

        dt_ist = datetime.fromisoformat(NATIVE_IST)
        dt_utc = dt_ist - timedelta(hours=5, minutes=30)
        jd = birth_jd(dt_utc)

        pos_lahiri = compute_positions(jd, "lahiri")
        pos_kp = compute_positions(jd, "kp")

        sun_lahiri = next(p for p in pos_lahiri if p["name"] == "Sun")
        sun_kp = next(p for p in pos_kp if p["name"] == "Sun")

        delta = abs(sun_lahiri["sidereal_longitude"] - sun_kp["sidereal_longitude"])
        assert delta < 0.5, f"Lahiri-KP delta {delta}° exceeds expected < 0.5°"
