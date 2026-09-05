"""
NIRMĀṆA L3-W3 finding M5 (§N.5, B.10) — the century grid belongs to the chart being built.

THE DEFECT. `ka_gochara_v3_century_materialize` anchored its 100-year grid on two module-level
constants, `BIRTH_JD = 2445736.5` / `BIRTH_YEAR = 1984`, which encode the NATIVE's birth. Every
chart got that grid. The second canonical chart (Abhinandan, born 1985-03-02) was therefore
materialised over 1984-02-05 → 2084-02-05 — **a century beginning 13 months before that native
existed** — with `era_slice_key` labels (`g3_1984_1994`, …) naming decades that are not that
chart's at all. Nothing detected it, because a hardcoded constant cannot disagree with itself.

WHAT IS DELIBERATELY NOT CHANGED. Two epoch anomalies were measured while fixing this and are
reported as separate findings rather than silently corrected, because each moves every window:
  (a) `BIRTH_JD` disagrees with its own comment by a day — the true JD for 1984-02-05 00:00 UT is
      2445735.5; 2445736.5 is 1984-02-06 00:00 UT.
  (b) It disagrees with its own engine by a further half day (`gochara_v3/resolution_hierarchy.py`
      uses `_EPOCH_JD = 2440588.0`).
So `_birth_jd()` reproduces the writer's EXISTING value exactly. The native's grid must not shift
as a side effect of fixing a multi-chart defect. These tests pin that non-movement.
"""
from __future__ import annotations

import datetime as dt

import pytest

from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    BIRTH_JD,
    BIRTH_YEAR,
    DECADE_COUNT,
    DECADE_SLICES,
    _birth_jd,
    _decade_slices_for_chart,
    build_decade_slices,
)

NATIVE_BIRTH = dt.date(1984, 2, 5)
ABHINANDAN_BIRTH = dt.date(1985, 3, 2)


def test_the_natives_grid_does_not_move() -> None:
    """The regression anchor. If this fails, an already-built century has silently shifted."""
    assert _birth_jd(NATIVE_BIRTH) == BIRTH_JD
    assert build_decade_slices() == DECADE_SLICES
    assert DECADE_SLICES[0].era_slice_key == f"g3_{BIRTH_YEAR}_{BIRTH_YEAR + 10}"
    assert DECADE_SLICES[0].start_jd == BIRTH_JD
    assert len(DECADE_SLICES) == DECADE_COUNT


def test_a_second_chart_gets_its_own_grid_not_the_natives() -> None:
    """The defect itself: Abhinandan's century must not start 13 months before he was born."""
    grid = build_decade_slices(_birth_jd(ABHINANDAN_BIRTH), ABHINANDAN_BIRTH.year)

    assert grid[0].era_slice_key == "g3_1985_1995"
    assert grid[0].era_slice_key != DECADE_SLICES[0].era_slice_key
    # 1984-02-05 → 1985-03-02 is 391 days; the grid must start exactly that much later.
    assert grid[0].start_jd - DECADE_SLICES[0].start_jd == pytest.approx(391.0)
    # And the century must not begin before the native it describes was born.
    assert grid[0].start_jd >= _birth_jd(ABHINANDAN_BIRTH)


def test_grid_is_contiguous_and_complete_for_any_epoch() -> None:
    """Whatever the epoch, the 10 slices must tile the century with no gap and no overlap."""
    for birth in (NATIVE_BIRTH, ABHINANDAN_BIRTH, dt.date(2001, 12, 31)):
        grid = build_decade_slices(_birth_jd(birth), birth.year)
        assert len(grid) == DECADE_COUNT
        for earlier, later in zip(grid, grid[1:]):
            assert earlier.end_jd == later.start_jd, "gap or overlap between decade slices"
            assert earlier.year_end == later.year_start
        assert grid[-1].year_end - grid[0].year_start == 100


def test_it_refuses_rather_than_falling_back_to_the_native() -> None:
    """
    §N.8 / B.10: the whole defect was a silent default. An unresolvable birth date must raise,
    not quietly produce someone else's century.
    """
    with pytest.raises(RuntimeError, match="cannot resolve a birth date"):
        # conn=None and no birth_params → resolve_birth_date returns None by design.
        _decade_slices_for_chart(None, "00000000-0000-4000-8000-000000000000", None)


def test_birth_params_alone_is_enough_to_resolve_a_grid() -> None:
    """The orchestrator supplies birth_params in ctx.config; no DB round-trip should be needed."""
    grid = _decade_slices_for_chart(
        None,
        "11111111-1111-4111-8111-111111111111",
        {"datetime_iso": "1985-03-02T00:00:00"},
    )
    assert grid[0].era_slice_key == "g3_1985_1995"
