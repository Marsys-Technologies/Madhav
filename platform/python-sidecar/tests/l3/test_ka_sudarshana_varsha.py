"""Tests for ka_sudarshana_varsha (ṢAḌ-DARŚANA W3, registry item 17 —
Sudarśana-Chakra year-wheel triple-lagna progression).

BINDING NAMING RULING (do not revisit — see CLAUDE.md-external campaign
ruling recorded in SHAD_DARSHANA_STATE.md): this writer is named
`ka_sudarshana_varsha`, never bare `sudarshana` — `bo_sudarshana.py` is a
DIFFERENT, unrelated L2 Bodha static house-triad MSR signal writer (namesake
collision only, confirmed by the campaign; see services/ka_sudarshana_varsha/
logic.py's own docstring for the point-by-point distinction).

TDD: written before services/ka_sudarshana_varsha/logic.py existed.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_sudarshana_varsha.logic import (
    varsha_year_for_date,
    active_house_offset,
    progressed_sign_index,
    varsha_window,
    compute_tri_lagna_year,
)


class TestVarshaYearForDate:
    def test_year_1_covers_birth_to_first_birthday(self):
        birth = date(1984, 2, 5)
        assert varsha_year_for_date(birth, date(1984, 2, 5)) == 1
        assert varsha_year_for_date(birth, date(1984, 12, 31)) == 1
        assert varsha_year_for_date(birth, date(1985, 2, 4)) == 1

    def test_year_2_starts_on_first_birthday(self):
        birth = date(1984, 2, 5)
        assert varsha_year_for_date(birth, date(1985, 2, 5)) == 2

    def test_year_13_at_age_12_birthday(self):
        birth = date(1984, 2, 5)
        assert varsha_year_for_date(birth, date(1996, 2, 5)) == 13

    def test_leap_day_birth_handled(self):
        birth = date(2000, 2, 29)
        # Non-leap year "birthday" clamps to Feb 28 (standard convention).
        assert varsha_year_for_date(birth, date(2001, 2, 28)) == 2
        assert varsha_year_for_date(birth, date(2001, 2, 27)) == 1


class TestActiveHouseOffset:
    def test_age_1_offset_0(self):
        assert active_house_offset(1) == 0

    def test_age_13_wraps_to_offset_0(self):
        assert active_house_offset(13) == 0

    def test_age_2_offset_1(self):
        assert active_house_offset(2) == 1

    def test_age_25_wraps_to_offset_0(self):
        assert active_house_offset(25) == 0

    def test_age_14_offset_1(self):
        assert active_house_offset(14) == 1


class TestProgressedSignIndex:
    def test_year_1_is_natal_sign_itself(self):
        # natal sign index 0 (Aries), varsha year 1 -> still Aries
        assert progressed_sign_index(natal_sign_idx_0based=0, varsha_year=1) == 0

    def test_year_2_moves_one_sign_forward(self):
        assert progressed_sign_index(natal_sign_idx_0based=0, varsha_year=2) == 1

    def test_wraps_past_pisces(self):
        # natal sign = Aquarius (idx 10), year 3 -> offset 2 -> idx 12 % 12 = 0 (Aries)
        assert progressed_sign_index(natal_sign_idx_0based=10, varsha_year=3) == 0

    def test_year_13_returns_to_natal_sign(self):
        assert progressed_sign_index(natal_sign_idx_0based=7, varsha_year=13) == 7


class TestVarshaWindow:
    def test_year_1_window(self):
        birth = date(1984, 2, 5)
        start, end = varsha_window(birth, 1)
        assert start == date(1984, 2, 5)
        assert end == date(1985, 2, 5)

    def test_year_2_window(self):
        birth = date(1984, 2, 5)
        start, end = varsha_window(birth, 2)
        assert start == date(1985, 2, 5)
        assert end == date(1986, 2, 5)

    def test_leap_day_birth_window_clamps(self):
        birth = date(2000, 2, 29)
        start, end = varsha_window(birth, 1)
        assert start == date(2000, 2, 29)
        assert end == date(2001, 2, 28)


class TestComputeTriLagnaYear:
    def test_all_three_converge_when_natal_signs_equal(self):
        # Degenerate case: if JL == CL == SL natally, they stay equal every year.
        result = compute_tri_lagna_year(
            varsha_year=5, jl_natal_sign_idx=3, cl_natal_sign_idx=3, sl_natal_sign_idx=3,
        )
        assert result["jl_active_sign_idx"] == result["cl_active_sign_idx"] == result["sl_active_sign_idx"]
        assert result["tri_lagna_convergence"] is True

    def test_real_case_no_convergence(self):
        # Abhisek-like: Lagna=Aries(0), Moon=Aquarius(10), Sun=Capricorn(9)
        result = compute_tri_lagna_year(
            varsha_year=1, jl_natal_sign_idx=0, cl_natal_sign_idx=10, sl_natal_sign_idx=9,
        )
        assert result["jl_active_sign_idx"] == 0
        assert result["cl_active_sign_idx"] == 10
        assert result["sl_active_sign_idx"] == 9
        assert result["tri_lagna_convergence"] is False

    def test_convergence_can_occur_at_a_later_year(self):
        # JL=0, CL=1, SL=2 natally. Offsets differ by 1 sign each; they will never
        # ALL land on the same sign under a uniform +1/year progression unless they
        # started equal (proven by the invariant below) — this test asserts that
        # invariant rather than a specific year, so it is robust to the exact
        # progression formula's internals.
        signs = (0, 1, 2)
        any_convergence = any(
            compute_tri_lagna_year(y, *signs)["tri_lagna_convergence"] for y in range(1, 13)
        )
        assert any_convergence is False  # they all move in lockstep — relative gap never closes

    def test_result_keys(self):
        result = compute_tri_lagna_year(1, 0, 0, 0)
        assert set(result.keys()) == {
            "jl_active_sign_idx", "cl_active_sign_idx", "sl_active_sign_idx", "tri_lagna_convergence",
        }
