"""Tests for ka_vedha_gochara (ṢAḌ-DARŚANA W3, registry item 5 — Vedha
application + Sarvatobhadra chakra grid, closes defect R-19).

TDD: written before services/ka_vedha_gochara/writer.py existed. Pure-logic
unit tests only here (no DB) — mirrors tests/l3/test_ka_kota_chakra.py's
split between DB-free helper tests and the writer's own DB-touching
behaviour (tested separately in test_ka_vedha_gochara_writer.py).

Spec: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 5. See
services/ka_vedha_gochara/logic.py's module docstring for the full R-19
honest disclosure this test suite's fixtures are consistent with.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_vedha_gochara.logic import (
    HOUSE_VEDHA,
    SARVATOBHADRA,
    VEDHA_KINDS,
    detect_sign_runs,
    house_from_moon,
    overlap_window,
    sign_from_house,
)


class TestVedhaKinds:
    def test_exactly_two_kinds(self):
        assert VEDHA_KINDS == (HOUSE_VEDHA, SARVATOBHADRA)

    def test_kind_names(self):
        assert HOUSE_VEDHA == "house_vedha"
        assert SARVATOBHADRA == "sarvatobhadra"


class TestHouseFromMoon:
    def test_moon_sign_itself_is_house_1(self):
        assert house_from_moon(sign_idx=5, moon_sign_idx=5) == 1

    def test_next_sign_is_house_2(self):
        assert house_from_moon(sign_idx=6, moon_sign_idx=5) == 2

    def test_wraps_around_12(self):
        # moon in Pisces (11), graha in Aries (0) -> house 2
        assert house_from_moon(sign_idx=0, moon_sign_idx=11) == 2

    def test_wraps_backward(self):
        # moon in Aries (0), graha in Pisces (11) -> house 12
        assert house_from_moon(sign_idx=11, moon_sign_idx=0) == 12

    def test_full_cycle_produces_every_house_exactly_once(self):
        moon = 7
        houses = {house_from_moon(i, moon) for i in range(12)}
        assert houses == set(range(1, 13))


class TestSignFromHouse:
    def test_inverse_of_house_from_moon(self):
        for moon_sign in range(12):
            for sign in range(12):
                house = house_from_moon(sign, moon_sign)
                assert sign_from_house(moon_sign, house) == sign

    def test_house_1_is_moon_sign_itself(self):
        assert sign_from_house(moon_sign_idx=5, house_num=1) == 5


class TestOverlapWindow:
    def test_full_overlap(self):
        ov = overlap_window(date(2026, 1, 1), date(2026, 1, 10), date(2026, 1, 3), date(2026, 1, 6))
        assert ov == {"start": date(2026, 1, 3), "end": date(2026, 1, 6)}

    def test_partial_overlap(self):
        ov = overlap_window(date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 3), date(2026, 1, 10))
        assert ov == {"start": date(2026, 1, 3), "end": date(2026, 1, 5)}

    def test_no_overlap_returns_none(self):
        assert overlap_window(date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)) is None

    def test_touching_edges_is_one_day_overlap(self):
        ov = overlap_window(date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 5), date(2026, 1, 10))
        assert ov == {"start": date(2026, 1, 5), "end": date(2026, 1, 5)}

    def test_identical_windows(self):
        ov = overlap_window(date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 1), date(2026, 1, 5))
        assert ov == {"start": date(2026, 1, 1), "end": date(2026, 1, 5)}


class TestDetectSignRuns:
    """Same generic contiguous-run detection as ka_kota_chakra/
    ka_moorti_nirnaya's own copies — duplicated per this campaign's
    established one-writer-per-module convention."""

    def test_single_run_no_change(self):
        days = [(date(2026, 1, 1 + i), 2) for i in range(4)]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        assert len(runs) == 1
        assert runs[0]["sign_idx"] == 2
        assert runs[0]["start_truncated"] is True
        assert runs[0]["end_truncated"] is True

    def test_two_runs(self):
        days = [
            (date(2026, 1, 1), 2), (date(2026, 1, 2), 2),
            (date(2026, 1, 3), 3), (date(2026, 1, 4), 3),
        ]
        runs = detect_sign_runs(days, horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 4))
        assert len(runs) == 2
        assert runs[0]["end_truncated"] is False
        assert runs[1]["start_truncated"] is False

    def test_empty_input(self):
        assert detect_sign_runs([], horizon_start=date(2026, 1, 1), horizon_end=date(2026, 1, 1)) == []


class TestHouseVedhaScenario:
    """An end-to-end pure-logic scenario matching the writer's own use: a
    graha transiting a vedha-checkable favourable house, with and without an
    obstructing occupant in the paired vedha house — the classical
    cancellation semantics gochara_vedha_pair already implements
    (services/gochara_grammar/primitives.py), re-expressed for this
    standalone per-chart surface."""

    def test_sun_3rd_house_vedha_pair_is_9th(self):
        # BPHS Ch.29: Sun favourable in 3rd from Moon, vedha from 9th
        # (brahmagyan/l0_transit.py BG_TRANSIT_RULES — real data).
        moon_sign_idx = 0  # Aries
        primary_house = house_from_moon(sign_idx=2, moon_sign_idx=moon_sign_idx)  # Gemini = house 3
        assert primary_house == 3
        vedha_house = 9
        vedha_sign_idx = sign_from_house(moon_sign_idx, vedha_house)
        assert vedha_sign_idx == 8  # Sagittarius (0-indexed: Aries=0 .. Sagittarius=8)

    def test_obstruction_active_when_windows_overlap(self):
        primary_start, primary_end = date(2026, 3, 1), date(2026, 3, 20)
        occupant_start, occupant_end = date(2026, 3, 10), date(2026, 3, 15)
        ov = overlap_window(primary_start, primary_end, occupant_start, occupant_end)
        assert ov is not None

    def test_obstruction_inactive_when_windows_do_not_overlap(self):
        primary_start, primary_end = date(2026, 3, 1), date(2026, 3, 20)
        occupant_start, occupant_end = date(2026, 4, 1), date(2026, 4, 10)
        ov = overlap_window(primary_start, primary_end, occupant_start, occupant_end)
        assert ov is None
