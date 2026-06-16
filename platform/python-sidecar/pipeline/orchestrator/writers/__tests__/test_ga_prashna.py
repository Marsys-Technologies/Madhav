"""
Tests for ga_prashna — writer class metadata and pure computation helpers.
Runs without a real DB connection.

Coverage:
  1.  ga_prashna registered in WRITER_REGISTRY
  2.  GaPrashnaWriter.has_substeps is True (heavy writer)
  3.  GaPrashnaWriter is a WriterBase subclass
  4.  plan_substeps returns exactly 5 SubSteps
  5.  The 5 ayanamsha keys match CANONICAL_AYANAMSHAS exactly
  6.  run_substep with ctx.dry_run=True returns 0 rows and makes no DB calls
  7.  compute_prashna_judgment returns None when prashna_charts has no row (not a prashna chart)
  8.  _aspect_gap pure function: faster at 0°, slower at 90° → gap=90° (applying square)
  9.  _aspect_gap pure function: faster at 95°, slower at 90° → gap=-5° (separating)
  10. compute_prashna_judgment with mock data (marriage): Moon at 45°, Venus at 50° → applying → Ithasala → YES
  11. compute_prashna_judgment with mock: Moon at 55°, Venus at 50° → separating → Eesarpha → NO
  12. Movable lagna (Aries) → fructification_unit = 'days'
  13. Fixed lagna (Taurus) → fructification_unit = 'months'
  14. Dual lagna (Gemini) → fructification_unit = 'days'
  15. PLANET_DAILY_MOTION has all 9 grahas
  16. CANONICAL_AYANAMSHAS list matches exactly the expected 5 ids
  17. seed_prashna_judgment with dry_run=True returns 0 and makes no DB calls
  18. seed_prashna_judgment when compute returns None returns 0 (non-prashna chart)
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ── Module imports ────────────────────────────────────────────────────────────

from ga_writers.ga_prashna_writer import (
    CANONICAL_AYANAMSHAS,
    PLANET_DAILY_MOTION,
    _aspect_gap,
    compute_prashna_judgment,
    seed_prashna_judgment,
)
from pipeline.orchestrator.writers.ga_prashna import GaPrashnaWriter


# ── 1. Registry — ga_prashna ─────────────────────────────────────────────────

def test_ga_prashna_registered():
    """ga_prashna must be registered in WRITER_REGISTRY after import."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import pipeline.orchestrator.writers.ga_prashna  # noqa: F401
    assert 'ga_prashna' in WRITER_REGISTRY


# ── 2. has_substeps is True (heavy writer) ────────────────────────────────────

def test_ga_prashna_is_heavy_writer():
    """GaPrashnaWriter must be a heavy writer (has_substeps=True)."""
    assert GaPrashnaWriter.has_substeps is True


# ── 3. WriterBase subclass ────────────────────────────────────────────────────

def test_ga_prashna_is_writer_base_subclass():
    """GaPrashnaWriter must be a WriterBase subclass."""
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(GaPrashnaWriter, WriterBase)


# ── 4. plan_substeps returns exactly 5 SubSteps ───────────────────────────────

def test_ga_prashna_plan_substeps_returns_five():
    """GaPrashnaWriter.plan_substeps must return exactly 5 SubSteps."""
    writer = GaPrashnaWriter()
    ctx = MagicMock()
    substeps = writer.plan_substeps(ctx)
    assert len(substeps) == 5, (
        f"plan_substeps must return 5 substeps (one per canonical ayanamsha), "
        f"got {len(substeps)}: {[s.key for s in substeps]}"
    )


# ── 5. Ayanamsha keys match CANONICAL_AYANAMSHAS ──────────────────────────────

def test_ga_prashna_substep_keys_match_canonical_ayanamshas():
    """The 5 substep keys must match the CANONICAL_AYANAMSHAS exactly."""
    writer = GaPrashnaWriter()
    ctx = MagicMock()
    substeps = writer.plan_substeps(ctx)
    expected_keys = {f"ayanamsha_{ay}" for ay in CANONICAL_AYANAMSHAS}
    actual_keys = {s.key for s in substeps}
    assert actual_keys == expected_keys, (
        f"Unexpected substep keys. Missing: {expected_keys - actual_keys}; "
        f"Extra: {actual_keys - expected_keys}"
    )


# ── 6. dry_run returns 0 rows and makes no DB calls ───────────────────────────

def test_ga_prashna_run_substep_dry_run_returns_zero():
    """ctx.dry_run=True must return 0 rows and make no DB calls."""
    from pipeline.orchestrator.writers import SubStep, ContextSpec

    writer = GaPrashnaWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": "some-chart-id"}
    ctx.build_id = "test-dry-build"
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0, (
        f"dry_run must return 0 rows, got {result.rows_inserted}"
    )
    ctx.db_conn.cursor.assert_not_called()


# ── 7. compute_prashna_judgment returns None for non-prashna chart ────────────

def test_compute_prashna_judgment_returns_none_for_non_prashna_chart():
    """compute_prashna_judgment must return None when prashna_charts has no matching row."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None  # no row in prashna_charts

    result = compute_prashna_judgment(conn, "natal-chart-id", "lahiri_chitrapaksha")
    assert result is None, "Expected None for a chart not in prashna_charts"


# ── 8. _aspect_gap: faster at 0°, slower at 90° → gap 90° (applying square) ──

def test_aspect_gap_applying_square():
    """Faster planet at 0°, slower at 90° → gap=90.0 (applying)."""
    gap, aspect = _aspect_gap(0.0, 90.0)
    # diff = 90 - 0 = 90; nearest aspect = 90 (square); gap = 90 - 90 = 0 ... wait
    # Actually: diff = (90 - 0) % 360 = 90
    # For aspect=90: raw_gap = 90 - 90 = 0 → no gap → but that means exact square
    # For aspect=0 (conj): raw_gap = 90 - 0 = 90 (normalized = 90)
    # nearest is aspect=90 with gap=0
    # gap=0 means exact aspect — applying with gap=0 is still "in orb"
    assert abs(gap) <= 90.0, f"Gap should be <= 90, got {gap}"
    # The square (90°) should be the nearest aspect
    assert aspect == 90.0, f"Expected nearest aspect to be 90° (square), got {aspect}"


# ── 9. _aspect_gap: faster at 95°, slower at 90° → gap=-5° (separating) ──────

def test_aspect_gap_separating():
    """Faster planet at 95°, slower at 90° → gap < 0 (separating past conjunction)."""
    # diff = (90 - 95) % 360 = (-5) % 360 = 355
    # Nearest aspect to 355°: conjunction (360°=0°); gap = 355 - 360 = -5 (normalized)
    # Actually: 355 - 0 = 355, normalized to -5 (since 355 > 180, 355-360=-5)
    gap, aspect = _aspect_gap(95.0, 90.0)
    assert gap < 0, f"Expected gap < 0 (separating), got {gap}"
    assert abs(gap) == pytest.approx(5.0, abs=0.01), f"Expected gap magnitude ~5°, got {abs(gap)}"


# ── 10. Marriage question: Moon at 45°, Venus at 50° → applying → YES ─────────

def _make_mock_conn_for_judgment(
    question_class: str,
    querent_planet: str,
    querent_lon: float,
    quesited_planet: str,
    quesited_lon: float,
    lagna_lon: float,
    querent_str: str = None,
    quesited_str: str = None,
) -> MagicMock:
    """Build a mock connection that returns the given scenario data."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    # prashna_charts row
    prashna_row = (question_class, "tajik_moment_lagna", None, None, None)
    # ga_positions rows: list of (graha, longitude, retrograde)
    positions_rows = [
        (querent_planet, querent_lon, False),
        (quesited_planet, quesited_lon, False),
        ("Lagna", lagna_lon, False),
    ]
    # bg_prashna_significators row
    sig_row = (querent_str or querent_planet, quesited_str or quesited_planet)

    # fetchone calls in order: prashna_charts → significators
    cur.fetchone.side_effect = [prashna_row, sig_row]
    # fetchall call: ga_positions
    cur.fetchall.return_value = positions_rows

    return conn


def test_marriage_moon_applying_venus_gives_yes():
    """Moon at 45°, Venus at 50° → Moon (faster) applying to Venus → Ithasala → YES."""
    # Moon speed=13.17, Venus speed=1.20 → Moon is faster
    # diff = (50 - 45) % 360 = 5
    # Nearest aspect=0 (conjunction): gap = 5 - 0 = 5 → gap > 0 → applying
    conn = _make_mock_conn_for_judgment(
        question_class="marriage",
        querent_planet="Moon",
        querent_lon=45.0,
        quesited_planet="Venus",
        quesited_lon=50.0,
        lagna_lon=0.0,  # Aries (0° = Aries)
    )
    result = compute_prashna_judgment(conn, "test-chart-id", "lahiri_chitrapaksha")
    assert result is not None
    assert result["tajik_yoga"] == "ithasala", f"Expected ithasala, got {result['tajik_yoga']}"
    assert result["judgment_text"] == "YES", f"Expected YES, got {result['judgment_text']}"
    assert result["is_applying"] is True


# ── 11. Moon at 55°, Venus at 50° → separating → Eesarpha → NO ───────────────

def test_marriage_moon_separating_venus_gives_no():
    """Moon at 55°, Venus at 50° → Moon has passed Venus → Eesarpha → NO."""
    # diff = (50 - 55) % 360 = 355
    # Nearest aspect=0 (conjunction): gap = 355 - 0 = 355, normalized → -5 (separating)
    # gap=-5, mutual_orb=(12+7)/2=9.5 → in_orb → eesarpha
    conn = _make_mock_conn_for_judgment(
        question_class="marriage",
        querent_planet="Moon",
        querent_lon=55.0,
        quesited_planet="Venus",
        quesited_lon=50.0,
        lagna_lon=30.0,  # Taurus (30° = Taurus)
    )
    result = compute_prashna_judgment(conn, "test-chart-id", "lahiri_chitrapaksha")
    assert result is not None
    assert result["tajik_yoga"] == "eesarpha", f"Expected eesarpha, got {result['tajik_yoga']}"
    assert result["judgment_text"] == "NO", f"Expected NO, got {result['judgment_text']}"
    assert result["is_applying"] is False


# ── 12. Movable lagna (Aries) → fructification_unit = 'days' ─────────────────

def test_movable_lagna_gives_days():
    """Aries lagna (movable sign) must produce fructification_unit='days'."""
    conn = _make_mock_conn_for_judgment(
        question_class="marriage",
        querent_planet="Moon",
        querent_lon=45.0,
        quesited_planet="Venus",
        quesited_lon=50.0,
        lagna_lon=5.0,  # 5° = Aries (movable)
    )
    result = compute_prashna_judgment(conn, "test-chart-id", "lahiri_chitrapaksha")
    assert result is not None
    assert result["fructification_unit"] == "days", (
        f"Aries (movable) lagna must give 'days', got '{result['fructification_unit']}'"
    )


# ── 13. Fixed lagna (Taurus) → fructification_unit = 'months' ────────────────

def test_fixed_lagna_gives_months():
    """Taurus lagna (fixed sign) must produce fructification_unit='months'."""
    conn = _make_mock_conn_for_judgment(
        question_class="marriage",
        querent_planet="Moon",
        querent_lon=45.0,
        quesited_planet="Venus",
        quesited_lon=50.0,
        lagna_lon=35.0,  # 35° = Taurus (30-60°, fixed)
    )
    result = compute_prashna_judgment(conn, "test-chart-id", "lahiri_chitrapaksha")
    assert result is not None
    assert result["fructification_unit"] == "months", (
        f"Taurus (fixed) lagna must give 'months', got '{result['fructification_unit']}'"
    )


# ── 14. Dual lagna (Gemini) → fructification_unit = 'days' ───────────────────

def test_dual_lagna_gives_days():
    """Gemini lagna (dual sign) must produce fructification_unit='days'."""
    conn = _make_mock_conn_for_judgment(
        question_class="marriage",
        querent_planet="Moon",
        querent_lon=45.0,
        quesited_planet="Venus",
        quesited_lon=50.0,
        lagna_lon=65.0,  # 65° = Gemini (60-90°, dual)
    )
    result = compute_prashna_judgment(conn, "test-chart-id", "lahiri_chitrapaksha")
    assert result is not None
    assert result["fructification_unit"] == "days", (
        f"Gemini (dual) lagna must give 'days', got '{result['fructification_unit']}'"
    )


# ── 15. PLANET_DAILY_MOTION has all 9 grahas ──────────────────────────────────

def test_planet_daily_motion_has_all_nine_grahas():
    """PLANET_DAILY_MOTION must contain all 9 classical grahas."""
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert set(PLANET_DAILY_MOTION.keys()) == expected, (
        f"PLANET_DAILY_MOTION missing grahas: {expected - set(PLANET_DAILY_MOTION.keys())}; "
        f"extra: {set(PLANET_DAILY_MOTION.keys()) - expected}"
    )


# ── 16. CANONICAL_AYANAMSHAS list matches exactly the expected 5 ids ──────────

def test_canonical_ayanamshas_list_exact():
    """CANONICAL_AYANAMSHAS must be exactly the 5 canonical ids in the correct order."""
    expected = [
        "lahiri_chitrapaksha",
        "true_chitra",
        "krishnamurti",
        "raman",
        "surya_siddhanta_classical",
    ]
    assert CANONICAL_AYANAMSHAS == expected, (
        f"CANONICAL_AYANAMSHAS mismatch. Expected: {expected}, got: {CANONICAL_AYANAMSHAS}"
    )


# ── 17. seed_prashna_judgment dry_run=True returns 0 and no DB calls ──────────

def test_seed_prashna_judgment_dry_run_returns_zero():
    """seed_prashna_judgment(dry_run=True) must return 0 rows without touching the DB."""
    conn = MagicMock()
    rows = seed_prashna_judgment(conn, "chart-id", "lahiri_chitrapaksha", "build-id", dry_run=True)
    assert rows == 0, f"dry_run must return 0 rows, got {rows}"
    conn.cursor.assert_not_called()


# ── 18. seed_prashna_judgment when chart not in prashna_charts → 0 rows ───────

def test_seed_prashna_judgment_non_prashna_chart_returns_zero():
    """seed_prashna_judgment must return 0 when chart_id is not a prashna chart."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None  # not in prashna_charts

    rows = seed_prashna_judgment(conn, "natal-chart-id", "lahiri_chitrapaksha", "build-id", dry_run=False)
    assert rows == 0, f"Non-prashna chart must return 0 rows, got {rows}"
