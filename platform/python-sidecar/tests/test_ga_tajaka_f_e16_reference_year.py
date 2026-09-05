"""
test_ga_tajaka_f_e16_reference_year.py — F-E16
(L1_W1_ANALYSIS_BATCH_E.md: `DEFAULT_REFERENCE_YEAR = 2026` was a frozen
wall-clock literal). `build_ga_tajaka`'s hybrid-storage window (past + current
+ next 5 years) is anchored on `reference_year`, which the orchestrator never
passes — so production always took whatever literal sat in the file as a
default. Correct only by coincidence in 2026; by 2032 the materialised window
would end *before* the current varsha, with no error and no signal (§N.8: no
code path could ever make the "current" default read false).

DB-free: `_effective_reference_year` is a pure function.
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_tajaka_writer import _effective_reference_year  # noqa: E402


def test_default_derives_from_the_real_clock_not_a_frozen_literal():
    """The core F-E16 regression: no explicit year -> today's year, whatever
    today is -- not a value that was correct only for 2026."""
    assert _effective_reference_year(None) == datetime.now(timezone.utc).year


def test_explicit_year_always_wins_over_the_clock():
    """Reproducibility for tests/backfills is preserved: an explicit value is
    never overridden by the clock."""
    assert _effective_reference_year(2019) == 2019
    assert _effective_reference_year(2031) == 2031


def test_default_never_hardcodes_2026():
    """A literal regression guard: if the fix is reverted to a hardcoded
    year, this must fail every year that isn't that year."""
    resolved = _effective_reference_year(None)
    current_year = datetime.now(timezone.utc).year
    assert resolved == current_year
    if current_year != 2026:
        assert resolved != 2026
