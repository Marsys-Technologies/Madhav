"""E5 station-loop episode detector. Proposition: episodes group contacts by
child contact interval overlap with a station loop, not by peak date; aborted
approaches whose interval reaches past the retrograde station are included;
horizon-truncated loops are marked perfected=False; singletons pass through."""
from _common import *
from datetime import date
from unittest.mock import MagicMock

from services.ka_sangam.engine import group_station_loop_episodes, _date_to_jd

head("S18 — E5 station-loop episodes by contact interval")


def _station_event(event_jd, station_type):
    ev = MagicMock()
    ev.event_jd = event_jd
    ev.extra = {"station_type": station_type}
    return ev


def _contact(peak_date, window_start=None, window_end=None, signal_id="sig-e5"):
    return {
        "mode": "A",
        "window_start": window_start or peak_date,
        "window_end": window_end or peak_date,
        "peak_date": peak_date,
        "convergence_score": 0.5,
        "signal_id": signal_id,
        "constituent_factors": {
            "planet": "Saturn",
            "aspect_deg": 90,
            "target_provenance": {
                "target_fact_id": "f_001",
                "target_type": "graha_position",
                "frame": "longitude_sidereal",
                "ayanamsha_id": "lahiri_chitrapaksha",
                "derivation": "test",
            },
        },
    }


def _service(events):
    svc = MagicMock()
    svc.find_stations = lambda planet, start_jd, end_jd: events
    return svc


sr = _date_to_jd(date(2026, 3, 15))
sd = _date_to_jd(date(2026, 8, 20))
loop_svc = _service([
    _station_event(sr, "retrograde"),
    _station_event(sd, "direct"),
])

# Aborted approach: peak before SR, but interval overlaps the loop.
aborted = _contact(date(2026, 3, 1), window_end=date(2026, 3, 20))
retro = _contact(date(2026, 5, 1))
out = group_station_loop_episodes(
    [aborted, retro], loop_svc,
    _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)),
    chart_id="chart-e5",
)
episodes = [w for w in out if w.get("is_episode")]
children = episodes[0]["episode_children"] if episodes else []
aborted_child = next((c for c in children if c["peak_date"] == "2026-03-01"), None)
retro_child = next((c for c in children if c["peak_date"] == "2026-05-01"), None)

# Singleton pass-through.
singleton_out = group_station_loop_episodes(
    [_contact(date(2026, 5, 1))], loop_svc,
    _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)),
    chart_id="chart-e5",
)

# Horizon-truncated opening (direct station only).
trunc_svc = _service([_station_event(sd, "direct")])
trunc_out = group_station_loop_episodes(
    [_contact(date(2026, 1, 15)), _contact(date(2026, 2, 15))], trunc_svc,
    _date_to_jd(date(2026, 1, 1)), _date_to_jd(date(2026, 12, 31)),
    chart_id="chart-e5",
)
trunc_episodes = [w for w in trunc_out if w.get("is_episode")]

if NEG:
    # Inverted expectations: the detector must fail on correct code.
    prop("aborted approach is grouped into the episode", len(episodes) == 0 or aborted_child is None)
    prop("aborted child labelled loop_phase='approach'", False)
    prop("retrograde child is not approached-never-perfected", False)
    prop("singleton passes through unchanged", len(singleton_out) == 0 or singleton_out[0].get("is_episode"))
    prop("horizon-truncated loop marks perfected=False", len(trunc_episodes) > 0 and trunc_episodes[0].get("perfected") is True)
else:
    prop("aborted approach is grouped into the episode", len(episodes) == 1 and aborted_child is not None)
    prop("aborted child labelled loop_phase='approach'", aborted_child is not None and aborted_child["loop_phase"] == "approach")
    prop("aborted child is approached_never_perfected", aborted_child is not None and aborted_child["approached_never_perfected"] is True)
    prop("retrograde child is not approached-never-perfected", retro_child is not None and retro_child["approached_never_perfected"] is False)
    prop("singleton passes through unchanged", len(singleton_out) == 1 and not singleton_out[0].get("is_episode"))
    prop("horizon-truncated loop marks perfected=False", len(trunc_episodes) == 1 and trunc_episodes[0].get("perfected") is False)

done("POST-FIX BEHAVIOUR")
