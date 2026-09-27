"""
Tests for ka_sangam E5 — station-loop episodes with child contact intervals
and ka_taranga occupancy union in the chart's birth timezone.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.engine import (
    group_station_loop_episodes,
    _date_to_jd,
)
from pipeline.orchestrator.writers.ka_taranga import KaTarangaWriter

_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _station_event(event_jd, station_type):
    """Minimal TransitEvent-like object for station loops."""
    ev = MagicMock()
    ev.event_jd = event_jd
    ev.extra = {"station_type": station_type}
    return ev


def _contact(peak_date, window_start=None, window_end=None, planet="Saturn",
             aspect_deg=90, signal_id="sig-001", score=0.5, target_fact_id="f_001"):
    ws = window_start or peak_date
    we = window_end or peak_date
    return {
        "mode": "A",
        "window_start": ws,
        "window_end": we,
        "peak_date": peak_date,
        "convergence_score": score,
        "signal_id": signal_id,
        "constituent_factors": {
            "planet": planet,
            "aspect_deg": aspect_deg,
            "target_provenance": {
                "target_fact_id": target_fact_id,
                "target_type": "graha_position",
                "frame": "longitude_sidereal",
                "ayanamsha_id": "lahiri_chitrapaksha",
                "derivation": "test",
            },
        },
    }


class TestStationLoopGrouping:
    """services.ka_sangam.engine.group_station_loop_episodes"""

    def _service(self, events):
        svc = MagicMock()
        svc.find_stations = lambda planet, start_jd, end_jd: events
        return svc

    def test_single_loop_groups_multiple_contacts_into_one_episode(self):
        sr = _date_to_jd(date(2026, 3, 15))
        sd = _date_to_jd(date(2026, 8, 20))
        svc = self._service([
            _station_event(sr, "retrograde"),
            _station_event(sd, "direct"),
        ])
        contacts = [
            _contact(date(2026, 4, 1)),
            _contact(date(2026, 5, 1)),
            _contact(date(2026, 6, 1)),
        ]
        out = group_station_loop_episodes(
            contacts, svc, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        episodes = [w for w in out if w.get("is_episode")]
        assert len(episodes) == 1
        ep = episodes[0]
        assert ep["peak_date"] is None
        assert ep["perfected"] is True
        assert len(ep["episode_children"]) == 3
        assert ep["episode_hull"]["window_start"] == "2026-04-01"
        assert ep["episode_hull"]["window_end"] == "2026-06-01"

    def test_singleton_passes_through_unchanged(self):
        sr = _date_to_jd(date(2026, 3, 15))
        sd = _date_to_jd(date(2026, 8, 20))
        svc = self._service([
            _station_event(sr, "retrograde"),
            _station_event(sd, "direct"),
        ])
        contacts = [_contact(date(2026, 4, 1))]
        out = group_station_loop_episodes(
            contacts, svc, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        assert len(out) == 1
        assert out[0].get("is_episode") is not True

    def test_horizon_truncated_loop_marks_perfected_false(self):
        sd = _date_to_jd(date(2026, 8, 20))
        svc = self._service([
            _station_event(sd, "direct"),
        ])
        contacts = [
            _contact(date(2026, 1, 15)),
            _contact(date(2026, 2, 15)),
        ]
        out = group_station_loop_episodes(
            contacts, svc, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        episodes = [w for w in out if w.get("is_episode")]
        assert len(episodes) == 1
        assert episodes[0]["perfected"] is False
        # Truncated opening has no real SR in horizon, so every overlapping
        # contact is classified as retrograde (no approach phase exists).
        assert episodes[0]["episode_children"][0]["loop_phase"] == "retrograde"

    def test_no_gochara_service_returns_windows_unchanged(self):
        contacts = [_contact(date(2026, 4, 1)), _contact(date(2026, 5, 1))]
        out = group_station_loop_episodes(
            contacts, None, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        assert len(out) == 2
        assert all(not w.get("is_episode") for w in out)

    def test_different_contracts_do_not_group_together(self):
        sr = _date_to_jd(date(2026, 3, 15))
        sd = _date_to_jd(date(2026, 8, 20))
        svc = self._service([
            _station_event(sr, "retrograde"),
            _station_event(sd, "direct"),
        ])
        contacts = [
            _contact(date(2026, 4, 1), signal_id="sig-001"),
            _contact(date(2026, 5, 1), signal_id="sig-002"),
        ]
        out = group_station_loop_episodes(
            contacts, svc, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        assert len([w for w in out if not w.get("is_episode")]) == 2

    def test_aborted_approach_child_labelled(self):
        sr = _date_to_jd(date(2026, 3, 15))
        sd = _date_to_jd(date(2026, 8, 20))
        svc = self._service([
            _station_event(sr, "retrograde"),
            _station_event(sd, "direct"),
        ])
        contacts = [
            # Peak before SR but interval reaches past it -> aborted approach,
            # grouped by contact interval even though peak lies outside loop.
            _contact(date(2026, 3, 1), window_end=date(2026, 3, 20)),
            _contact(date(2026, 5, 1)),   # between -> perfected
        ]
        out = group_station_loop_episodes(
            contacts, svc, _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)), chart_id=_CHART_ID
        )
        ep = [w for w in out if w.get("is_episode")][0]
        children = ep["episode_children"]
        assert any(c["loop_phase"] == "approach" and c["approached_never_perfected"] is True for c in children)
        assert any(c["loop_phase"] == "retrograde" and c["approached_never_perfected"] is False for c in children)


class TestTarangaOccupancy:
    """ka_taranga birth-timezone occupancy helpers."""

    def test_occupied_local_months_splits_months_by_birth_timezone(self):
        # UTC offset +5:30 (IST). A window covering 2026-01-31 in UTC occupies
        # both 2026-01 and 2026-02 in IST because Jan 31 23:00 UTC = Feb 1 04:30 IST.
        intervals = [(date(2026, 1, 31), date(2026, 1, 31))]
        months = KaTarangaWriter._occupied_local_months(
            intervals, tz_offset_minutes=330, clip_start=date(1950, 1, 1), clip_end=date(2100, 12, 1)
        )
        assert date(2026, 1, 1) in months
        assert date(2026, 2, 1) in months

    def test_occupied_local_months_unions_episode_children(self):
        intervals = [
            (date(2026, 3, 10), date(2026, 3, 12)),
            (date(2026, 3, 20), date(2026, 3, 22)),
        ]
        months = KaTarangaWriter._occupied_local_months(
            intervals, tz_offset_minutes=0, clip_start=date(1950, 1, 1), clip_end=date(2100, 12, 1)
        )
        assert months == {date(2026, 3, 1)}

    def test_window_identity_distinguishes_episode_and_contact(self):
        ep = {"is_episode": True, "episode_uuid": "uuid-1"}
        ct = {"is_episode": False, "signal_id": "sig-1", "mode": "A", "peak_date": date(2026, 3, 1)}
        assert KaTarangaWriter._window_identity(ep) == ("episode", "uuid-1")
        assert KaTarangaWriter._window_identity(ct)[0] == "contact"

    def test_duplicate_contact_contributes_once_per_month(self):
        row = {
            "domain": "career",
            "window_start": date(2026, 3, 1),
            "window_end": date(2026, 3, 31),
            "convergence_score": 0.8,
            "is_episode": False,
            "signal_id": "sig-1",
            "mode": "A",
            "peak_date": date(2026, 3, 15),
        }
        counted = {}
        months = KaTarangaWriter._occupied_local_months(
            [(row["window_start"], row["window_end"])], 0, date(1950, 1, 1), date(2100, 12, 1)
        )
        for m in months:
            key = (m, row["domain"], KaTarangaWriter._window_identity(row))
            if key in counted:
                continue
            counted[key] = float(row["convergence_score"])
        # Insert the same row a second time (duplicate).
        for m in months:
            key = (m, row["domain"], KaTarangaWriter._window_identity(row))
            if key in counted:
                continue
            counted[key] = float(row["convergence_score"])
        assert len(counted) == 1
        assert sum(counted.values()) == pytest.approx(0.8)


class TestTarangaBirthTimezoneMonthBoundaries:
    """End-to-end occupancy computation in birth timezone."""

    def test_partial_month_utc_straddles_two_local_months(self):
        # Window 2026-01-31 UTC with +5:30 offset should contribute to both
        # January and February local months.
        row = {
            "domain": "career",
            "window_start": date(2026, 1, 31),
            "window_end": date(2026, 1, 31),
            "convergence_score": 0.8,
            "is_episode": False,
            "signal_id": "sig-1",
            "mode": "A",
            "peak_date": date(2026, 1, 31),
        }
        months = KaTarangaWriter._occupied_local_months(
            [(row["window_start"], row["window_end"])], 330, date(1950, 1, 1), date(2100, 12, 1)
        )
        assert {date(2026, 1, 1), date(2026, 2, 1)} == months
