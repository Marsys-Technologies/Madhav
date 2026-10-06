"""N-185: the ENGINE channel reports retrograde=True for the mean nodes at source (pyjhora_adapter/positions.py).

Before: `retrograde = pid in drik.planets_in_retrograde(...)`, which excludes the mean nodes, so chart_output, the
L2.5 builder and the /pyhora/compute response said False for Rahu/Ketu while ga_positions stored `retrograde`.
No database; the real-engine tests need SE_EPHE_PATH (pinned .se1 files) and skip visibly without it.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyjhora_adapter import positions as P

NATIVE = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5, "latitude_deg": 20.2961,
          "longitude_deg": 85.8245, "place_name": "Bhubaneswar", "subject_label": "native"}


def test_the_node_set_is_exactly_rahu_and_ketu():
    assert P.MEAN_NODE_PLANET_IDS == frozenset({7, 8})
    assert P.MEAN_NODE_GRAHA_NAMES == frozenset({"Rahu", "Ketu"})


def test_mean_nodes_are_retrograde_even_when_pyjhora_does_not_list_them():
    assert P._is_retro_body(7, set()) is True and P._is_retro_body(8, set()) is True


def test_every_other_body_keeps_the_pyjhora_flag():
    for pid in range(0, 7):
        assert P._is_retro_body(pid, set()) is False
        assert P._is_retro_body(pid, {pid}) is True


def test_true_nodes_would_not_be_forced(monkeypatch):
    monkeypatch.setattr(P, "_USE_TRUE_NODES", True)
    assert P._is_retro_body(7, set()) is False and P._is_retro_body(7, {7}) is True


def _se1() -> bool:
    return bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])


@pytest.mark.skipif(not _se1(), reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_real_engine_compute_chart_native_all_ayanamshas_nodes_true_sun_moon_false():
    from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS
    from pyjhora_adapter.compute import compute_chart

    for canonical, adapter_id in CANONICAL_AYANAMSHAS.items():
        by = {g["name"]: g["retrograde"] for g in compute_chart(inputs=NATIVE, ayanamsha_id=adapter_id)["grahas"]}
        assert by["Rahu"] is True and by["Ketu"] is True, canonical
        assert by["Sun"] is False and by["Moon"] is False, canonical


def test_pyhora_compute_response_carries_the_adapters_retrograde_flag():
    """The served /pyhora/compute `is_retrograde` read a key the adapter never emits (`is_retrograde` vs
    `retrograde`), so it was False for every graha; it now follows the adapter's `retrograde`."""
    from routers.pyhora import _shape_graha_sthana

    out = _shape_graha_sthana([
        {"name": "Rahu", "retrograde": True}, {"name": "Mars", "retrograde": True},
        {"name": "Sun", "retrograde": False}, {"name": "Moon"},
        {"name": "Legacy", "is_retrograde": True},
    ])
    flags = {g["name"]: g["is_retrograde"] for g in out}
    assert flags == {"Rahu": True, "Mars": True, "Sun": False, "Moon": False, "Legacy": True}


# ── N-185: the retrograde salience nudge is a RULE for the five tara-grahas, not for the nodes ──────────────────

def _graha(name: str, retro: bool) -> dict:
    return {"name": name, "sign_id": 2, "retrograde": retro}          # sign_id 2 vs ascendant 11 -> house 4 (kendra, base 0.85)


def test_l25_salience_nudge_skips_the_nodes_but_keeps_the_fact_and_the_tara_graha_nudge():
    from pyjhora_adapter.l25_builder.build import _msr_coefficient

    asc = 11                                                           # sign_id 2 is house 4 from sign 11
    node_direct, node_retro = _graha("Rahu", False), _graha("Rahu", True)
    assert _msr_coefficient(node_retro, asc)[2] == _msr_coefficient(node_direct, asc)[2] == 0.85   # NO +0.05
    assert _msr_coefficient(_graha("Ketu", True), asc)[2] == 0.85
    for tara in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert _msr_coefficient(_graha(tara, False), asc)[2] == 0.85
        assert _msr_coefficient(_graha(tara, True), asc)[2] == 0.9, tara                           # still +0.05


def test_l25_node_entries_still_show_retrograde_true_in_text_and_attributes():
    from pyjhora_adapter.l25_builder import build as B

    chart = {
        "ascendant": {"sign_id": 1, "sign": "Aries", "longitude_deg": 5.0},
        "grahas": [
            {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude_deg": 40.0, "nakshatra": "Rohini",
             "pada": 1, "dignity_status": "neutral", "retrograde": True, "degree_in_sign": 10.0},
            {"name": "Mars", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude_deg": 41.0, "nakshatra": "Rohini",
             "pada": 1, "dignity_status": "neutral", "retrograde": True, "degree_in_sign": 11.0},
        ],
        "provenance": {},
    }
    rows = B.build_l25_msr_signals(chart, "c", "b")
    by = {r["planets_involved"][0]: r for r in rows if r.get("source_section") == "engine/grahas"}
    assert "retrograde=True" in by["Rahu"]["description"] and "retrograde=True" in by["Mars"]["description"]


def test_ga_condition_vikala_branch_excludes_a_retrograde_node_in_an_enemy_sign():
    """N-185/N-187: a retrograde NODE in an enemy sign is `dina`, not `vikala`; a retrograde tara-graha stays vikala."""
    from ga_writers import ga_condition_writer as cw

    f = cw.avastha_deeptaadi_from_dignity_and_state
    for node in ("Rahu", "Ketu"):
        assert f("enemy_sign", False, True, graha=node) == "dina", node
        assert f("great_enemy_sign", False, True, graha=node) == "dina", node
    for tara in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert f("enemy_sign", False, True, graha=tara) == "vikala", tara
    assert f("enemy_sign", False, True) == "vikala"                  # legacy two-argument callers unchanged
    assert f("neutral_sign", False, True, graha="Rahu") == "shanta"   # nodes' other branches untouched
    assert f("exalted", False, True, graha="Ketu") == "deepta"
