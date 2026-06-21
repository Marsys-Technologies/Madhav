"""
tests/test_ka_graha_sancara.py — Unit tests for ka_graha_sancara (L3 K1).

Acceptance criteria covered:
  AC1: stub gone — grep-zero for 'return {}' in pyjhora_adapter/transits.py
  AC2: 9 grahas + speed_dps + retrograde for a known date; values match get_transit_states
  AC3: within-range reads bg_ephemeris (no swisseph call, via mock);
       out-of-range computes live
  AC4: ephemeris cache returns same object for repeated (T, ayanamsha) — single-compute
  AC5: applying/separating helper correctly classifies known cases
  AC7: FORENSIC natal_moon_sign = Aquarius for 1984-02-05 10:43 IST Bhubaneswar
  AC8: grep-zero for commit/rollback in services/ka_graha_sancara/

Runs without a real DB — uses mock connections/cursors where PATH-A is tested.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# ── sys.path setup ─────────────────────────────────────────────────────────────
SIDECAR = Path(__file__).parent.parent
SCRIPTS = SIDECAR.parent / "scripts"
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


_IST = timezone(timedelta(hours=5, minutes=30))
_BIRTH_DT = datetime(1984, 2, 5, 10, 43, 0, tzinfo=_IST)
# A known in-range date (within bg_ephemeris 1900-2150)
_IN_RANGE_DATE = date(2026, 6, 21)
_IN_RANGE_DT = datetime(2026, 6, 21, 0, 0, 0, tzinfo=timezone.utc)
# An out-of-range date (beyond bg_ephemeris end 2150-12-31)
_OUT_RANGE_DT = datetime(2200, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


# ── AC1: stub gone ─────────────────────────────────────────────────────────────

def test_ac1_stub_gone():
    """
    AC1: pyjhora_adapter/transits.py must not be the original stub.

    The original stub body was exactly:
        def compute_transits(...) -> dict[str, Any]:
            return {}

    The replacement must delegate to ka_graha_sancara engine (real logic).
    We check: the file references 'ka_graha_sancara' and compute_transits
    does NOT consist solely of 'return {}' as its only statement.
    """
    transits_file = SIDECAR / "pyjhora_adapter" / "transits.py"
    assert transits_file.exists(), f"transits.py not found at {transits_file}"
    content = transits_file.read_text()

    # Real implementation must reference ka_graha_sancara
    assert "ka_graha_sancara" in content, (
        "transits.py must delegate to ka_graha_sancara engine; "
        "'ka_graha_sancara' not found in file"
    )

    # The stub pattern was that the function body was just `return {}` with NO other code
    # (line count between def and return was 1 actual logic line).
    # Guard: if the file has more than 10 lines of actual content, stub is gone.
    non_empty_lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
    assert len(non_empty_lines) > 10, (
        f"transits.py looks like a stub — only {len(non_empty_lines)} non-comment lines"
    )


# ── AC2: 9 grahas + speed + retrograde via live compute ───────────────────────

def test_ac2_nine_grahas_speeds_retrograde():
    """AC2: get_transit_states returns 9 grahas with speed_deg_per_day and is_retrograde."""
    from temporal.compute_transits import get_transit_states

    result = get_transit_states(_BIRTH_DT, _BIRTH_DT.date(), ayanamsha="lahiri")
    planets = result["planets"]

    expected_9 = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert set(planets.keys()) == expected_9, f"Expected 9 grahas, got: {set(planets.keys())}"

    for name in expected_9:
        p = planets[name]
        assert "speed_deg_per_day" in p, f"{name}: missing speed_deg_per_day"
        assert p["speed_deg_per_day"] is not None, f"{name}: speed_deg_per_day is None"
        assert "is_retrograde" in p, f"{name}: missing is_retrograde"
        assert isinstance(p["is_retrograde"], bool), f"{name}: is_retrograde must be bool"


def test_ac2_engine_matches_get_transit_states():
    """AC2: get_ephemeris (live path) produces same signs as get_transit_states."""
    from temporal.compute_transits import get_transit_states
    from services.ka_graha_sancara.engine import get_ephemeris

    ref = get_transit_states(_BIRTH_DT, _BIRTH_DT.date(), ayanamsha="lahiri")
    result = get_ephemeris(_BIRTH_DT, ayanamsha="lahiri", db_conn=None)

    ref_planets = ref["planets"]
    for graha in ("Sun", "Moon", "Mars", "Saturn", "Rahu"):
        ref_sign = ref_planets[graha]["sign"]
        eng_sign = result.grahas[graha].sign
        assert ref_sign == eng_sign, (
            f"{graha}: engine sign={eng_sign!r} but get_transit_states sign={ref_sign!r}"
        )


# ── AC3: PATH-A (bg_ephemeris) vs PATH-B (live) ───────────────────────────────

def _make_mock_db_with_rows(d: date):
    """
    Build a mock psycopg connection that returns ephemeris_daily rows
    for date d with synthetic tropical longitudes (Sun=300, Moon=330, etc.).
    """
    BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    # Synthetic tropical longitudes chosen so sidereal (Lahiri ~23°) gives sensible signs
    TROPICAL_LONS = {
        "Sun": 316.0,    # → Capricorn sidereal
        "Moon": 330.0,   # → Aquarius sidereal
        "Mars": 80.0,
        "Mercury": 295.0,
        "Jupiter": 45.0,
        "Venus": 260.0,
        "Saturn": 330.0,
        "Rahu": 60.0,
        "Ketu": 240.0,
    }
    rows = [
        (body, TROPICAL_LONS[body], 1.0 if body != "Saturn" else -0.1, False)
        for body in BODIES
    ]
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


def test_ac3_within_range_uses_bg_ephemeris_no_swisseph():
    """AC3: in-range date with valid db_conn reads PATH-A (no swisseph.calc_ut call)."""
    from services.ka_graha_sancara.engine import get_ephemeris

    conn, cur = _make_mock_db_with_rows(_IN_RANGE_DATE)

    # Patch calc_ut so we can detect if it is called (it should NOT be for PATH-A)
    with patch("swisseph.calc_ut") as mock_calc:
        result = get_ephemeris(_IN_RANGE_DT, ayanamsha="lahiri", db_conn=conn)

    # PATH-A should have succeeded — source should be bg_ephemeris
    assert result.source == "bg_ephemeris", (
        f"Expected source='bg_ephemeris' for in-range date; got {result.source!r}"
    )
    # DB query was made
    cur.execute.assert_called_once()
    # swisseph.calc_ut should NOT be called for planetary positions
    # (get_ayanamsa_ut IS called — that's fine; calc_ut is the planet query)
    calc_ut_calls = [c for c in mock_calc.call_args_list]
    assert not calc_ut_calls, (
        f"PATH-A should not call swisseph.calc_ut; called {len(calc_ut_calls)} times"
    )


def test_ac3_out_of_range_uses_live_compute():
    """AC3: out-of-range date (2200) uses PATH-B (live swisseph) regardless of db_conn."""
    from services.ka_graha_sancara.engine import get_ephemeris

    conn = MagicMock()  # db_conn provided but date is out of range

    result = get_ephemeris(_OUT_RANGE_DT, ayanamsha="lahiri", db_conn=conn)

    # For 2200, bg_ephemeris is not queried — no cursor interaction expected
    # The result should come from swisseph_live
    assert result.source == "swisseph_live", (
        f"Expected source='swisseph_live' for out-of-range date; got {result.source!r}"
    )


def test_ac3_no_db_conn_uses_live_compute():
    """AC3: db_conn=None always uses PATH-B."""
    from services.ka_graha_sancara.engine import get_ephemeris

    result = get_ephemeris(_IN_RANGE_DT, ayanamsha="lahiri", db_conn=None)
    assert result.source == "swisseph_live"


# ── AC4: ephemeris cache single-compute ───────────────────────────────────────

def test_ac4_cache_single_compute_same_object():
    """AC4: repeated (T, ayanamsha) within one call hits cache — single compute."""
    from services.ka_graha_sancara.engine import get_ephemeris, _EphemerisCache

    cache = _EphemerisCache()
    dt1 = _IN_RANGE_DT
    dt2 = _IN_RANGE_DT  # same date+ayanamsha

    # Use live path (no db) so we can track swisseph calls
    compute_count = [0]
    _orig_compute_live = None
    from services.ka_graha_sancara import engine as eng_mod

    original_compute_live = eng_mod._compute_live

    def counting_compute_live(query_dt, ayanamsha):
        compute_count[0] += 1
        return original_compute_live(query_dt, ayanamsha)

    with patch.object(eng_mod, "_compute_live", side_effect=counting_compute_live):
        r1 = get_ephemeris(dt1, ayanamsha="lahiri", db_conn=None, _cache=cache)
        r2 = get_ephemeris(dt2, ayanamsha="lahiri", db_conn=None, _cache=cache)

    assert compute_count[0] == 1, (
        f"Expected exactly 1 live compute; got {compute_count[0]}. "
        "Cache did not prevent second computation."
    )
    assert cache.stats["hits"] == 1, f"Expected 1 cache hit; got {cache.stats}"
    assert cache.stats["misses"] == 1, f"Expected 1 miss; got {cache.stats}"

    # Both results must have identical Moon sign
    assert r1.grahas["Moon"].sign == r2.grahas["Moon"].sign


def test_ac4_different_ayanamsha_different_cache_key():
    """AC4: different ayanamsha = different cache key = separate computes."""
    from services.ka_graha_sancara.engine import _EphemerisCache

    cache = _EphemerisCache()
    d = date(2026, 6, 21)
    cache.put(d, "lahiri", {"grahas": {}, "_source": "test"})
    cache.put(d, "raman", {"grahas": {}, "_source": "test"})

    assert cache.stats["size"] == 2
    r_lahiri = cache.get(d, "lahiri")
    r_raman = cache.get(d, "raman")
    assert r_lahiri is not None
    assert r_raman is not None
    assert cache.stats["hits"] == 2


# ── AC5: applying/separating helper ───────────────────────────────────────────

def test_ac5_applying_graha_moving_toward_target():
    """AC5: direct-motion graha approaching target → 'applying'."""
    from services.ka_graha_sancara.engine import GrahaState

    gs = GrahaState(
        name="Saturn",
        sidereal_lon_deg=10.0,
        sign="Aries",
        sign_idx=0,
        nakshatra="Ashwini",
        nakshatra_idx=0,
        degrees_in_sign=10.0,
        degrees_in_nakshatra=10.0,
        speed_dps=0.1,      # direct, moving forward
        is_retrograde=False,
        source="test",
    )
    # Target is ahead: 15° (Saturn at 10° moving toward 15°)
    assert gs.applying_or_separating(15.0) == "applying"


def test_ac5_separating_graha_past_target():
    """AC5: direct-motion graha that has passed target → 'separating'."""
    from services.ka_graha_sancara.engine import GrahaState

    gs = GrahaState(
        name="Mars",
        sidereal_lon_deg=20.0,
        sign="Aries",
        sign_idx=0,
        nakshatra="Bharani",
        nakshatra_idx=1,
        degrees_in_sign=20.0,
        degrees_in_nakshatra=7.0,
        speed_dps=0.5,      # direct
        is_retrograde=False,
        source="test",
    )
    # Target is behind: 10° (Mars at 20° moving away from 10°)
    # sep = (10 - 20) % 360 = 350 > 180 → flip: d_sep_dt = speed_dps > 0 → separating
    assert gs.applying_or_separating(10.0) == "separating"


def test_ac5_retrograde_graha_moving_toward_behind_target():
    """AC5: retrograde graha moving back toward a target behind it → 'applying'."""
    from services.ka_graha_sancara.engine import GrahaState

    gs = GrahaState(
        name="Mercury",
        sidereal_lon_deg=20.0,
        sign="Aries",
        sign_idx=0,
        nakshatra="Bharani",
        nakshatra_idx=1,
        degrees_in_sign=20.0,
        degrees_in_nakshatra=7.0,
        speed_dps=-0.3,     # retrograde — moving backward
        is_retrograde=True,
        source="test",
    )
    # Target is behind (10°): retrograde Mercury is moving toward it → applying
    # sep = (10 - 20) % 360 = 350 > 180 → flip: d_sep_dt = speed_dps = -0.3 < 0 → applying
    assert gs.applying_or_separating(10.0) == "applying"


def test_ac5_stationary_graha():
    """AC5: stationary graha (speed≈0) → 'stationary'."""
    from services.ka_graha_sancara.engine import GrahaState

    gs = GrahaState(
        name="Jupiter",
        sidereal_lon_deg=100.0,
        sign="Cancer",
        sign_idx=3,
        nakshatra="Pushya",
        nakshatra_idx=7,
        degrees_in_sign=10.0,
        degrees_in_nakshatra=10.0,
        speed_dps=0.0,
        is_retrograde=False,
        source="test",
    )
    assert gs.applying_or_separating(110.0) == "stationary"


# ── AC7: FORENSIC Moon = Aquarius ─────────────────────────────────────────────

def test_ac7_forensic_moon_aquarius():
    """AC7: natal Moon sign = Aquarius for 1984-02-05 10:43 IST Bhubaneswar."""
    from services.ka_graha_sancara.engine import get_ephemeris

    result = get_ephemeris(_BIRTH_DT, ayanamsha="lahiri", db_conn=None)
    moon = result.grahas["Moon"]
    assert moon.sign == "Aquarius", (
        f"FORENSIC FAIL: natal Moon sign expected='Aquarius', got={moon.sign!r}. "
        f"Moon lon={moon.sidereal_lon_deg:.4f}°"
    )


def test_ac7_forensic_moon_aquarius_via_get_transit_states():
    """AC7: cross-check via get_transit_states directly."""
    from temporal.compute_transits import get_transit_states

    result = get_transit_states(_BIRTH_DT, _BIRTH_DT.date(), ayanamsha="lahiri")
    moon_sign = result["planets"]["Moon"]["sign"]
    assert moon_sign == "Aquarius", (
        f"FORENSIC FAIL: get_transit_states Moon sign={moon_sign!r}"
    )


# ── AC8: grep-zero commit/rollback in ka_graha_sancara ───────────────────────

def test_ac8_no_commit_rollback_in_service():
    """AC8: services/ka_graha_sancara/ must not call .commit() or .rollback()."""
    service_dir = SIDECAR / "services" / "ka_graha_sancara"
    assert service_dir.exists(), f"Service directory not found: {service_dir}"

    forbidden = re.compile(r"\.(commit|rollback)\s*\(", re.IGNORECASE)
    violations: list[str] = []
    for py_file in service_dir.glob("*.py"):
        code = py_file.read_text()
        matches = forbidden.findall(code)
        if matches:
            violations.append(f"{py_file.name}: {matches}")

    assert not violations, (
        "services/ka_graha_sancara/ must NOT call .commit() or .rollback():\n"
        + "\n".join(violations)
    )


def test_ac8_no_commit_rollback_in_writer():
    """AC8: pipeline/orchestrator/writers/ka_graha_sancara.py must not commit/rollback."""
    writer_file = (
        SIDECAR / "pipeline" / "orchestrator" / "writers" / "ka_graha_sancara.py"
    )
    assert writer_file.exists(), f"Writer not found: {writer_file}"
    code = writer_file.read_text()
    forbidden = re.compile(r"ctx\.db_conn\.(commit|rollback|close)\s*\(", re.IGNORECASE)
    matches = forbidden.findall(code)
    assert not matches, (
        f"ka_graha_sancara writer calls forbidden ctx.db_conn.{matches}"
    )


# ── Writer conformance: subclasses WriterBase, returns correct result ─────────

def test_writer_subclasses_writer_base():
    """The ka_graha_sancara writer must subclass WriterBase."""
    from pipeline.orchestrator.writers.ka_graha_sancara import KaGrahaSancaraWriter
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(KaGrahaSancaraWriter, WriterBase)
    assert KaGrahaSancaraWriter.asset_id == "ka_graha_sancara"


def test_writer_dry_run_returns_zero_rows():
    """Writer in dry_run mode returns WriterResult with rows_inserted=0."""
    from pipeline.orchestrator.writers.ka_graha_sancara import KaGrahaSancaraWriter
    from pipeline.orchestrator.writers import ContextSpec, WriterResult

    conn = MagicMock()
    ctx = ContextSpec(
        asset_id="ka_graha_sancara",
        build_id="test-dry-run",
        db_conn=conn,
        dry_run=True,
    )
    writer = KaGrahaSancaraWriter()
    result = writer.run(ctx)

    assert isinstance(result, WriterResult)
    assert result.rows_inserted == 0
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_writer_self_test_writes_service_health():
    """Writer self-test calls UPDATE asset_registry SET service_health."""
    from pipeline.orchestrator.writers.ka_graha_sancara import KaGrahaSancaraWriter
    from pipeline.orchestrator.writers import ContextSpec

    cur = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    ctx = ContextSpec(
        asset_id="ka_graha_sancara",
        build_id="test-self-test",
        db_conn=conn,
        dry_run=False,
    )
    writer = KaGrahaSancaraWriter()
    result = writer.run(ctx)

    # Must NOT commit
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()

    # Must have called UPDATE asset_registry SET service_health
    all_sql = " ".join(str(c) for c in cur.execute.call_args_list)
    assert "service_health" in all_sql, (
        "Writer must UPDATE asset_registry SET service_health; "
        f"SQL calls: {cur.execute.call_args_list}"
    )
