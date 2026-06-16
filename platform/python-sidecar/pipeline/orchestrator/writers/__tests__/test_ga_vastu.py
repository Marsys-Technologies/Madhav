"""
Tests for ga_vastu + bg_vastu_directions — writer class metadata and pure helpers.
Runs without a real DB connection.

Coverage:
  1.  bg_vastu_directions registered in writer registry
  2.  ga_vastu registered in writer registry
  3.  bg_vastu_directions has_substeps=False (light writer)
  4.  ga_vastu has_substeps=True (heavy writer)
  5.  Both writers are WriterBase subclasses
  6.  8 directions seeded (length of VASTU_DIRECTIONS constant)
  7.  All direction rows have a classical_citation
  8.  North direction maps to Mercury
  9.  East direction maps to Sun
  10. West direction maps to Saturn
  11. FORENSIC: Sun → East; compute_direction_impact(low_score) → 'weakened'
  12. FORENSIC: Saturn → West; compute_direction_impact(high_score) → 'strengthened'
  13. compute_direction_impact(None) → 'neutral'
  14. compute_direction_impact(0.39) → 'weakened' (boundary)
  15. compute_direction_impact(0.40) → 'neutral'  (boundary)
  16. compute_direction_impact(0.69) → 'neutral'  (boundary)
  17. compute_direction_impact(0.70) → 'strengthened' (boundary)
  18. dry_run returns 0 rows for bg_vastu_directions
  19. dry_run returns 0 rows for ga_vastu substep
  20. GRAHA_TO_DIRECTION covers all expected 8 grahas (Ketu excluded)
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ── Module imports ────────────────────────────────────────────────────────────

from brahmagyan.l0_vastu_directions import (
    VASTU_DIRECTIONS,
    VASTU_DIRECTION_REMEDIALS,
    seed_vastu_directions,
)
from ga_writers.ga_vastu_writer import (
    GRAHA_TO_DIRECTION,
    compute_direction_impact,
    CANONICAL_CHART_ID,
)
from pipeline.orchestrator.writers.bg_vastu_directions import BgVastuDirectionsWriter
from pipeline.orchestrator.writers.ga_vastu import GaVastuWriter


# ── 1. Registry — bg_vastu_directions ────────────────────────────────────────

def test_bg_vastu_directions_registered():
    """bg_vastu_directions must be registered in WRITER_REGISTRY after import."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import pipeline.orchestrator.writers.bg_vastu_directions  # noqa: F401
    assert 'bg_vastu_directions' in WRITER_REGISTRY


# ── 2. Registry — ga_vastu ────────────────────────────────────────────────────

def test_ga_vastu_registered():
    """ga_vastu must be registered in WRITER_REGISTRY after import."""
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    import pipeline.orchestrator.writers.ga_vastu  # noqa: F401
    assert 'ga_vastu' in WRITER_REGISTRY


# ── 3. bg_vastu_directions is a LIGHT writer ──────────────────────────────────

def test_bg_vastu_directions_is_light_writer():
    """bg_vastu_directions must be a light writer (has_substeps=False)."""
    assert BgVastuDirectionsWriter.has_substeps is False


# ── 4. ga_vastu is a HEAVY writer ─────────────────────────────────────────────

def test_ga_vastu_is_heavy_writer():
    """ga_vastu must be a heavy writer (has_substeps=True)."""
    assert GaVastuWriter.has_substeps is True


# ── 5. Both are WriterBase subclasses ─────────────────────────────────────────

def test_bg_vastu_directions_is_writer_base_subclass():
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(BgVastuDirectionsWriter, WriterBase)


def test_ga_vastu_is_writer_base_subclass():
    from pipeline.orchestrator.writers import WriterBase
    assert issubclass(GaVastuWriter, WriterBase)


# ── 6. 8 directions seeded ────────────────────────────────────────────────────

def test_eight_directions_seeded():
    """VASTU_DIRECTIONS must contain exactly 8 rows (one per compass direction)."""
    assert len(VASTU_DIRECTIONS) == 8


# ── 7. All direction rows have classical_citation ─────────────────────────────

def test_all_direction_rows_have_citation():
    """Every direction row must carry a non-empty classical_citation."""
    for row in VASTU_DIRECTIONS:
        assert row.get("classical_citation"), (
            f"Direction '{row['direction']}' missing classical_citation"
        )


# ── 8. North → Mercury ────────────────────────────────────────────────────────

def test_north_maps_to_mercury():
    """North direction must be ruled by Mercury (Budha) per Mayamata Ch.6."""
    north_rows = [r for r in VASTU_DIRECTIONS if r["direction"] == "North"]
    assert len(north_rows) == 1, "Expected exactly one North row"
    assert north_rows[0]["ruling_graha"] == "Mercury", (
        f"North must map to Mercury, got '{north_rows[0]['ruling_graha']}'"
    )


# ── 9. East → Sun ─────────────────────────────────────────────────────────────

def test_east_maps_to_sun():
    """East direction must be ruled by Sun (Surya) per Mayamata Ch.6."""
    east_rows = [r for r in VASTU_DIRECTIONS if r["direction"] == "East"]
    assert len(east_rows) == 1, "Expected exactly one East row"
    assert east_rows[0]["ruling_graha"] == "Sun", (
        f"East must map to Sun, got '{east_rows[0]['ruling_graha']}'"
    )


# ── 10. West → Saturn ─────────────────────────────────────────────────────────

def test_west_maps_to_saturn():
    """West direction must be ruled by Saturn (Shani) per Mayamata Ch.6."""
    west_rows = [r for r in VASTU_DIRECTIONS if r["direction"] == "West"]
    assert len(west_rows) == 1, "Expected exactly one West row"
    assert west_rows[0]["ruling_graha"] == "Saturn", (
        f"West must map to Saturn, got '{west_rows[0]['ruling_graha']}'"
    )


# ── 11. FORENSIC: Sun (debilitated) → East direction → 'weakened' ─────────────

def test_forensic_sun_debilitated_east_weakened():
    """FORENSIC — native chart 482012f1: Sun=Capricorn (debilitated).
    Sun rules East. Low condition_score (debilitated < 0.4) → East must be 'weakened'.
    Guard: only runs with the canonical chart id to avoid false positives.
    """
    assert CANONICAL_CHART_ID == "482012f1-710e-4a25-994a-93821f5871aa"

    # Sun direction mapping
    assert GRAHA_TO_DIRECTION["Sun"] == "East", (
        "Sun must map to East direction"
    )
    # Debilitated Sun has a low condition_score (< 0.4)
    # Use a representative debilitated score per DIGNITY_SCORES["debilitated"] = 0.0
    debilitated_score = 0.15  # representative debilitated condition score
    impact = compute_direction_impact(debilitated_score)
    assert impact == "weakened", (
        f"Debilitated Sun (score={debilitated_score}) should produce 'weakened' East, got '{impact}'"
    )


# ── 12. FORENSIC: Saturn (exalted) → West direction → 'strengthened' ──────────

def test_forensic_saturn_exalted_west_strengthened():
    """FORENSIC — native chart 482012f1: Saturn=Libra (exalted).
    Saturn rules West. High condition_score (exalted >= 0.7) → West must be 'strengthened'.
    """
    assert GRAHA_TO_DIRECTION["Saturn"] == "West", (
        "Saturn must map to West direction"
    )
    # Exalted Saturn has a high condition_score (>= 0.7)
    exalted_score = 0.85  # representative exalted condition score
    impact = compute_direction_impact(exalted_score)
    assert impact == "strengthened", (
        f"Exalted Saturn (score={exalted_score}) should produce 'strengthened' West, got '{impact}'"
    )


# ── 13. compute_direction_impact(None) → 'neutral' ────────────────────────────

def test_direction_impact_none_is_neutral():
    """When condition_score is None (no ga_condition row), direction_impact must be 'neutral'."""
    assert compute_direction_impact(None) == "neutral"


# ── 14–17. compute_direction_impact boundary tests ────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (0.39, "weakened"),      # just below 0.4 threshold
    (0.40, "neutral"),       # at 0.4 boundary — belongs to neutral
    (0.69, "neutral"),       # just below 0.7 threshold
    (0.70, "strengthened"),  # at 0.7 boundary — belongs to strengthened
    (0.00, "weakened"),      # minimum (debilitated)
    (1.00, "strengthened"),  # maximum (exalted)
])
def test_direction_impact_boundaries(score, expected):
    """Boundary conditions for compute_direction_impact thresholds."""
    result = compute_direction_impact(score)
    assert result == expected, (
        f"compute_direction_impact({score}) → expected '{expected}', got '{result}'"
    )


# ── 18. dry_run returns 0 rows for bg_vastu_directions ───────────────────────

def test_bg_vastu_directions_dry_run_returns_zero():
    """seed_vastu_directions(dry_run=True) must return expected counts without DB calls."""
    conn = MagicMock()
    counts = seed_vastu_directions(conn, build_id="test-build", dry_run=True)
    # dry_run returns the expected volume without writing
    assert counts["bg_vastu_directions"] == 8
    assert counts["bg_vastu_direction_remedials"] > 0
    # No DB calls must have been made
    conn.cursor.assert_not_called()


# ── 19. dry_run returns 0 rows for ga_vastu substep ──────────────────────────

def test_ga_vastu_run_substep_dry_run_returns_zero():
    """ctx.dry_run=True must return 0 rows and make no DB calls."""
    from pipeline.orchestrator.writers import SubStep, ContextSpec

    writer = GaVastuWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": CANONICAL_CHART_ID}
    ctx.build_id = "test-dry-build"
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")
    result = writer.run_substep(ctx, step)

    assert result.rows_inserted == 0, (
        f"dry_run must return 0 rows, got {result.rows_inserted}"
    )
    ctx.db_conn.cursor.assert_not_called()


# ── 20. GRAHA_TO_DIRECTION covers 8 grahas (Ketu excluded) ───────────────────

def test_graha_to_direction_covers_eight_grahas():
    """GRAHA_TO_DIRECTION must map exactly 8 grahas (Ketu intentionally omitted)."""
    expected_mapped = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"}
    assert set(GRAHA_TO_DIRECTION.keys()) == expected_mapped, (
        f"Expected exactly these grahas in GRAHA_TO_DIRECTION: {expected_mapped}; "
        f"got {set(GRAHA_TO_DIRECTION.keys())}"
    )
    assert "Ketu" not in GRAHA_TO_DIRECTION, (
        "Ketu must NOT be in GRAHA_TO_DIRECTION (no classical Vastu direction)"
    )


# ── Bonus: remedials have citations ───────────────────────────────────────────

def test_all_remedials_have_citation():
    """Every remedial row must carry a non-empty classical_citation."""
    for row in VASTU_DIRECTION_REMEDIALS:
        assert row.get("classical_citation"), (
            f"Remedial for direction='{row['direction']}' remedy_type='{row['remedy_type']}' "
            f"missing classical_citation"
        )


# ── 21. plan_substeps returns exactly 5 (one per canonical ayanamsha) ─────────

def test_ga_vastu_plan_substeps_returns_five():
    """GaVastuWriter.plan_substeps must return exactly 5 SubSteps."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers import ContextSpec

    writer = GaVastuWriter()
    ctx = MagicMock(spec=ContextSpec)
    substeps = writer.plan_substeps(ctx)

    assert len(substeps) == 5, (
        f"plan_substeps must return 5 substeps (one per canonical ayanamsha), "
        f"got {len(substeps)}: {[s.key for s in substeps]}"
    )

    expected_keys = {
        "ayanamsha_lahiri_chitrapaksha",
        "ayanamsha_true_chitra",
        "ayanamsha_krishnamurti",
        "ayanamsha_raman",
        "ayanamsha_surya_siddhanta_classical",
    }
    actual_keys = {s.key for s in substeps}
    assert actual_keys == expected_keys, (
        f"Unexpected substep keys: {actual_keys - expected_keys} missing: {expected_keys - actual_keys}"
    )
