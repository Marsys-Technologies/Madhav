"""TI-ga-positions-node-retro-001 -- Rahu/Ketu `retrograde_flag` must be `retrograde`.

Defect (CARR_SPIKE_REPORT open item 4; known_findings.json ga_positions): ga_positions stores the MEAN
nodes (RAH_MEAN / KET_MEAN). The adapter's `planets_in_retrograde` list excludes the mean nodes, so the
writer stored `direct` on all 10 Rahu/Ketu rows (5 ayanamshas x 2) of a chart, although the mean-node
longitude moves backward at every instant. Only the flag is fixed here (an in-build second calculation is
the engine's N-169 item).

No database. The real-engine test needs the pinned .se1 files (SE_EPHE_PATH) and skips visibly without them.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ga_writers import ga_positions_writer as gpw

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.2961,
    "longitude_deg": 85.8245,
    "place_name": "Bhubaneswar",
    "subject_label": "native",
}
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _graha(name: str, retro: bool) -> dict:
    return {
        "name": name, "longitude_deg": 100.0, "sign": "Cancer", "sign_lord": "Moon", "nakshatra": "Pushya",
        "nakshatra_lord": "Saturn", "pada": 1, "house": 1, "retrograde": retro, "combust": False,
        "degree_in_sign": 10.0, "sign_id": 4,
    }


def _flags(chart_output: dict, ayanamsha: str = "lahiri_chitrapaksha") -> dict[str, str]:
    rows = gpw._build_position_rows(chart_output, CHART_ID, "b", ayanamsha, "lahiri", "2026-10-07T00:00:00+00:00")
    return {r["fact_subject"]: r["fact_value_text"] for r in rows if r["fact_key"] == "retrograde_flag"}


def test_mean_nodes_are_retrograde_even_when_the_adapter_flag_says_direct():
    out = {"grahas": [_graha("Rahu", False), _graha("Ketu", False)], "ascendant": {}}
    assert _flags(out) == {"RAH_MEAN": "retrograde", "KET_MEAN": "retrograde"}


def test_other_grahas_keep_the_adapter_flag_unchanged():
    out = {"grahas": [_graha("Sun", False), _graha("Moon", False), _graha("Mars", True), _graha("Saturn", True)],
           "ascendant": {}}
    flags = _flags(out)
    assert flags["SUN"] == "direct" and flags["MOON"] == "direct"
    assert flags["MAR"] == "retrograde" and flags["SAT"] == "retrograde"


def test_the_node_set_is_exactly_rahu_and_ketu():
    assert gpw.MEAN_NODE_GRAHA_NAMES == frozenset({"Rahu", "Ketu"})


def _se1_available() -> bool:
    return bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])


@pytest.mark.skipif(not _se1_available(), reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_real_engine_native_chart_all_ten_node_rows_retrograde_all_five_ayanamshas():
    from pyjhora_adapter.compute import compute_chart

    seen = 0
    for canonical, adapter_id in gpw.CANONICAL_AYANAMSHAS.items():
        chart = compute_chart(inputs=NATIVE_INPUTS, ayanamsha_id=adapter_id)
        flags = _flags(chart, canonical)
        assert flags["RAH_MEAN"] == "retrograde" and flags["KET_MEAN"] == "retrograde", (canonical, flags)
        seen += 2
    assert seen == 10  # the 10 rows that stored `direct` before the fix


@pytest.mark.skipif(not _se1_available(), reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_mean_node_longitude_really_moves_backward_at_the_native_birth_instant():
    """Independent corroboration of the convention (test-only, direct pyswisseph): the mean node's daily
    speed is negative, so `retrograde` is the truth, not a fudge."""
    import swisseph as swe

    swe.set_ephe_path(os.environ["SE_EPHE_PATH"])
    jd_ut = swe.julday(1984, 2, 5, 10.0 + 43 / 60 - 5.5)
    xx, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SPEED)
    assert xx[3] < 0.0
