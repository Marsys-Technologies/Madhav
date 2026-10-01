"""
Suvarna TI-vighnakara (SS ruling N-28) — gandanta junction windows + Rikta tithi set.

THE DEFECTS in ka_vighnakara (before this change):
  1. `_GANDANTA_RANGES` covered the FIRST 3°20' of the water signs (90-93.33, 210-213.33,
     330-333.33). Gandanta is the water-fire JUNCTION: the LAST 3°20' of Cancer/Scorpio/Pisces
     AND the FIRST 3°20' of Leo/Sagittarius/Aries (Ashlesha-Magha, Jyeshtha-Mula, Revati-Ashwini).
     So the writer fired where there is no gandanta and missed all six real arcs.
  2. The panchanga detector fired on a wrapper-local `(4, 9, 14, 15)`. The engine's Rikta set
     is tithi ids {4, 9, 14, 19, 24, 29}; 15 (Purnima) is Poorna, and the krishna-paksha
     Rikta tithis (19/24/29) were missed.

The fix reads ONE definition of each (CLAUDE.md §N.7 item 3): `check_gandanta` from the L1
`ga_sensitive_degree_writer`, and the Rikta classification from `panchang_engine.rich_topics`
(`compute_tithi_attrs`).
"""
from __future__ import annotations

import ast
import math
import re
from datetime import date
from pathlib import Path

import pytest

import panchang_engine
from ga_writers import ga_sensitive_degree_writer as l1
from panchang_engine import rich_topics
from pipeline.orchestrator.writers import ka_vighnakara as kv
from pipeline.orchestrator.writers.ka_vighnakara import (
    _check_gandanta,
    _check_malefic_transit,
    _check_panchanga_obstruction,
)

WRITER_SRC = Path(kv.__file__).read_text(encoding="utf-8")
ARC = 30.0 / 9.0  # 3°20'
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces")

# The three water->fire junctions as (water sign idx, fire sign idx); six arcs in all.
JUNCTIONS = ((3, 4), (7, 8), (11, 0))


class _MoonSwe:
    """swe stub: the Moon (pid 1) sits at a fixed sidereal longitude."""
    FLG_SIDEREAL = 65536
    SIDM_LAHIRI = 1

    def __init__(self, lon: float):
        self._lon = lon

    def set_sid_mode(self, *a, **k):
        pass

    def calc_ut(self, jd, pid, flags=0):
        return ((self._lon, 0.0, 1.0, 0.0, 0.0, 0.0), flags)


def _fires(lon: float) -> bool:
    r = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe(lon))
    return r is not None and not r["detail"].get("stub")


# ── Gandanta ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("water,fire", JUNCTIONS)
def test_water_sign_fires_only_in_its_last_3deg20(water, fire):
    base = water * 30.0
    edge = 30.0 - ARC                       # 26°40' (L1 edge is pinned exactly in the direct tests below)
    assert _fires(base + edge)              # at 26°40' within the writer's 9-decimal rounding
    assert _fires(base + 28.0)
    assert _fires(base + 29.999)
    assert not _fires(base + edge - 0.01)   # just before the arc
    assert not _fires(base + 0.01)          # FIRST 3°20' of a water sign: NOT gandanta (old code fired here)
    assert not _fires(base + 3.0)


@pytest.mark.parametrize("water,fire", JUNCTIONS)
def test_fire_sign_fires_only_in_its_first_3deg20(water, fire):
    base = fire * 30.0
    assert _fires(base + 0.0)               # the junction itself
    assert _fires(base + 0.01)
    assert _fires(base + 3.0)
    assert _fires(base + ARC)               # at 3°20' within the writer's 9-decimal rounding
    assert not _fires(base + ARC + 0.01)    # just past the arc
    assert not _fires(base + 15.0)


@pytest.mark.parametrize("water,fire", JUNCTIONS)
def test_both_sides_of_each_junction_point_fire_and_name_the_sign(water, fire):
    junction = fire * 30.0 if fire else 360.0
    before = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe((junction - 0.5) % 360.0))
    after = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe((junction + 0.5) % 360.0))
    # junction_sign keeps its legacy meaning (the WATER sign of the junction) on both sides;
    # moon_sign is the sign the Moon actually occupies.
    assert before["detail"]["junction_sign"] == SIGNS[water]
    assert after["detail"]["junction_sign"] == SIGNS[water]
    assert before["detail"]["moon_sign"] == SIGNS[water]
    assert after["detail"]["moon_sign"] == SIGNS[fire]
    assert before["detail"]["gandanta_zone"] == f"end_of_{SIGNS[water]}"
    assert after["detail"]["gandanta_zone"] == f"start_of_{SIGNS[fire]}"
    assert before["detail"]["distance_to_junction_deg"] == pytest.approx(0.5, abs=1e-3)


def test_old_first_3deg20_of_water_sign_windows_no_longer_fire():
    # The three windows the old table covered: 90-93.333, 210-213.333, 330-333.333.
    for lon in (90.0, 91.5, 93.0, 210.0, 212.0, 213.2, 330.0, 331.0, 333.2):
        assert not _fires(lon), lon


def test_non_junction_signs_never_fire():
    for sign in (1, 2, 5, 6, 9, 10):  # Taurus, Gemini, Virgo, Libra, Capricorn, Aquarius
        for deg in (0.5, 2.0, 15.0, 27.0, 29.9):
            assert not _fires(sign * 30.0 + deg)


def test_writer_reads_the_l1_gandanta_definition_not_a_local_copy():
    assert kv.check_gandanta is l1.check_gandanta
    assert kv.GANDANTA_CITATION is l1.GANDANTA_CITATION
    assert not hasattr(kv, "_GANDANTA_RANGES")
    detector = WRITER_SRC.split("def _check_gandanta")[1].split("# ── Detector 4")[0]
    assert not re.search(r"\b(9[03]|21[03]|33[03])\.\d*", detector), \
        "no hard-coded junction longitudes in the detector"
    r = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe(117.0))
    assert r["detail"]["citation"] == l1.GANDANTA_CITATION
    assert r["detail"]["gandanta_arc_deg"] == round(l1.GANDANTA_ARC, 4)


# ── L1 edge inclusivity, pinned directly on the definition the writer reads ─────

@pytest.mark.parametrize("water,fire", JUNCTIONS)
def test_l1_check_gandanta_edges_are_inclusive_at_exactly_3deg20(water, fire):
    edge_in_water = 30.0 - l1.GANDANTA_ARC   # 26°40' exactly as the L1 module computes it
    assert l1.check_gandanta(water, edge_in_water)["fired"]
    assert not l1.check_gandanta(water, math.nextafter(edge_in_water, 0.0))["fired"]
    assert l1.check_gandanta(water, 29.999999)["fired"]
    assert l1.check_gandanta(fire, l1.GANDANTA_ARC)["fired"]
    assert not l1.check_gandanta(fire, math.nextafter(l1.GANDANTA_ARC, 30.0))["fired"]
    assert l1.check_gandanta(fire, 0.0)["fired"]


def test_writer_effective_edge_is_within_a_nano_degree_of_the_l1_edge():
    # The writer rounds the in-sign degree to 9 decimals (float hygiene), so its effective edge
    # sits at most ~5e-10 deg outward of the exact L1 edge. Pinned so it cannot silently widen:
    # 1e-8 deg past the edge must NOT fire.
    for water, fire in JUNCTIONS:
        assert not _fires(water * 30.0 + (30.0 - ARC) - 1e-8)
        assert not _fires(fire * 30.0 + ARC + 1e-8)


# ── Reason / narration text for the zone ────────────────────────────────────────

def test_reason_text_names_end_vs_start_of_sign_and_distance():
    end = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe(117.0))["detail"]    # Cancer 27 deg
    start = _check_gandanta("2030-01-01", jd=1.0, swe=_MoonSwe(123.0))["detail"]  # Leo 3 deg
    assert "end of Cancer" in end["reason"] and "start of" not in end["reason"]
    assert "3.00° from the water-fire junction" in end["reason"]
    assert "start of Leo" in start["reason"] and "end of" not in start["reason"]
    assert "3.00° from the water-fire junction" in start["reason"]
    assert end["junction_sign"] == start["junction_sign"] == "Cancer"
    assert (end["moon_sign"], start["moon_sign"]) == ("Cancer", "Leo")


# ── The writer FOLLOWS the L1/engine definitions (not just matches them today) ──

def _calls_in(fn_name: str) -> set:
    tree = ast.parse(WRITER_SRC)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name)
    return {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}


def test_detectors_call_the_shared_definitions():
    assert "check_gandanta" in _calls_in("_check_gandanta")
    assert "compute_tithi_attrs" in _calls_in("_is_rikta_tithi")
    assert "_is_rikta_tithi" in _calls_in("_check_panchanga_obstruction")


def test_gandanta_detector_follows_the_l1_definition_when_it_changes(monkeypatch):
    monkeypatch.setattr(kv, "check_gandanta", lambda sn, d: {"fired": False, "sign": SIGNS[sn]})
    assert not _fires(117.0)                                   # real gandanta, but L1 says no
    monkeypatch.setattr(kv, "check_gandanta", lambda sn, d: {
        "fired": True, "sign": SIGNS[sn], "gandanta_zone": f"end_of_{SIGNS[sn]}",
        "distance_to_junction_deg": 1.0, "gandanta_arc_deg": 3.3333})
    assert _fires(45.0)                                        # Taurus: not gandanta, but L1 says yes


def test_rikta_detector_follows_the_engine_definition_when_it_changes(monkeypatch):
    class _Attrs:
        def __init__(self, t):
            self.anga_type = "Rikta" if t == 15 else "Poorna"

    monkeypatch.setattr(kv, "compute_tithi_attrs", lambda t: _Attrs(t))
    assert _tithi_hits(monkeypatch, 15)
    assert not _tithi_hits(monkeypatch, 4)


# ── Rikta ───────────────────────────────────────────────────────────────────────

def _tithi_hits(monkeypatch, tithi_id: int) -> bool:
    class _Anga:
        id = tithi_id

    class _Panchang:
        tithi = _Anga()

    monkeypatch.setattr(panchang_engine, "compute_panchang", lambda *a, **k: _Panchang())
    loc = {"lat": 20.2961, "lon": 85.8245, "tz_offset_minutes": 330}
    r = _check_panchanga_obstruction(date(2030, 1, 1), muhurta_service=object(), native_location=loc)
    return r is not None and r["detail"]["panchanga_element"] == "rikta_tithi"


def test_rikta_set_is_the_engine_set_and_nothing_else():
    engine_rikta = {t for t in range(1, 31)
                    if rich_topics.compute_tithi_attrs(t).anga_type == "Rikta"}
    assert engine_rikta == {4, 9, 14, 19, 24, 29}
    assert kv.compute_tithi_attrs is rich_topics.compute_tithi_attrs
    assert {t for t in range(1, 31) if kv._is_rikta_tithi(t)} == engine_rikta
    # no wrapper-local copy of the tuple survives in the detector
    detector = WRITER_SRC.split("def _check_panchanga_obstruction")[1].split("# ── Detector 3")[0]
    assert "(4, 9, 14" not in detector


def test_detector_fires_exactly_on_the_engine_rikta_tithis(monkeypatch):
    fired = {t for t in range(1, 31) if _tithi_hits(monkeypatch, t)}
    assert fired == {4, 9, 14, 19, 24, 29}
    assert fired == {t for t in range(1, 31)
                     if rich_topics.compute_tithi_attrs(t).anga_type == "Rikta"}
    assert 15 not in fired and 30 not in fired          # Purnima / Amavasya are Poorna
    assert {19, 24, 29} <= fired                        # krishna-paksha Rikta, missed before


# ── Reason text for a non-Aries chart (Track I-2 stays closed) ──────────────────

def test_malefic_transit_reason_is_chart_relative_for_non_aries_chart():
    class _Swe:
        FLG_SIDEREAL = 65536
        SIDM_LAHIRI = 1

        def set_sid_mode(self, *a, **k):
            pass

        def calc_ut(self, jd, pid, flags=0):
            # Saturn in Scorpio (the 6th from Gemini lagna), Rahu in Aries (not adverse here)
            lon = {6: 7 * 30 + 10.0, 11: 10.0}[pid]
            return ((lon, 0.0, 1.0, 0.0, 0.0, 0.0), flags)

    r = _check_malefic_transit("2030-01-01", jd=1.0, swe=_Swe(),
                               natal_lagna_lon=2 * 30 + 5.0,    # Gemini lagna
                               natal_moon_lon=11 * 30 + 5.0)    # Pisces Moon
    assert r is not None
    reason = r["detail"]["reason"]
    assert "lagna (Gemini)" in reason and "Moon (Pisces)" in reason
    assert "Aries" not in reason and "Aquarius" not in reason
