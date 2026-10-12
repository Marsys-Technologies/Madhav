"""
test_ga_emitters_canonical_nakshatra.py -- FAIL-ON-BASE (SS N-548): the emitting ga_* writers fold the
adapter's / panchang engine's nakshatra spelling onto the L0 lexicon's at emission, through the ONE
normaliser, and refuse an unregistered name. `pyjhora_adapter._names` and `panchang_engine.shastra_tables`
themselves are untouched; on main their text was forwarded verbatim (Mula / Mrigashira / Dhanishta).
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.nakshatra_vocabulary import CANONICAL_NAKSHATRA_NAMES, UnknownNakshatraError  # noqa: E402

LEGACY = ("Mrigashira", "Mula", "Dhanishta")


def _graha(name: str, nak: str) -> dict:
    return {"name": name, "longitude_deg": 250.0, "sign": "Sagittarius", "sign_lord": "Jupiter", "nakshatra": nak,
            "nakshatra_lord": "Ketu", "pada": 1, "house": 9, "sign_id": 9, "degree_in_sign": 10.0,
            "retrograde": False, "combust": False}


def _positions(moon_nak: str, lagna_nak: str = "Ashwini") -> dict:
    from ga_writers.ga_positions_writer import _build_position_rows

    chart_output = {"grahas": [_graha("Moon", moon_nak)],
                    "ascendant": {"longitude_deg": 5.0, "sign": "Aries", "sign_lord": "Mars", "nakshatra": lagna_nak, "pada": 1, "sign_id": 1}}
    rows = _build_position_rows(chart_output, "test-chart", "test-build", "lahiri_chitrapaksha", "lahiri", "2026-01-01T00:00:00Z")
    return {(r["fact_subject"], r["fact_key"]): r["fact_value_text"] for r in rows if r["fact_category"] == "graha_position"}


@pytest.mark.parametrize("adapter,canon", [("Mula", "Moola"), ("Mrigashira", "Mrigasira"), ("Dhanishta", "Dhanishtha"),
                                           ("Moola", "Moola"), ("Purva Bhadrapada", "Purva Bhadrapada")])
def test_ga_positions_emits_the_lexicon_spelling_for_the_graha_row(adapter, canon):
    facts = _positions(adapter)
    assert facts[("MOON", "nakshatra")] == canon     # fails on base: the adapter's text was forwarded verbatim
    assert ("LAGNA", "nakshatra") not in facts        # ga_positions emits no LAGNA nakshatra row (unchanged; the lagna nakshatra is another writer's fact)


def test_ga_positions_every_adapter_name_emits_its_canonical_name_and_the_other_24_are_byte_identical():
    from pyjhora_adapter._names import NAKSHATRA_NAMES

    adapter = [n for n in NAKSHATRA_NAMES if n]
    assert len(adapter) == 27
    for i, name in enumerate(adapter):
        got = _positions(name)[("MOON", "nakshatra")]
        assert got == CANONICAL_NAKSHATRA_NAMES[i], name
        if name not in LEGACY:
            assert got == name


def test_ga_positions_refuses_an_unregistered_nakshatra_name_and_keeps_an_absent_one_empty():
    with pytest.raises(UnknownNakshatraError):
        _positions("NotANakshatra")
    assert _positions("")[("MOON", "nakshatra")] == ""   # an absent adapter name stays "" (as before), never Ashwini


def _panchanga_rows(engine_name: str, nak_id: int) -> dict:
    from ga_writers.ga_panchanga_writer import _emit_nakshatra_moon

    pi = SimpleNamespace(
        nakshatra=SimpleNamespace(id=nak_id, name=engine_name, end_utc=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)),
        nakshatra_attrs=SimpleNamespace(deity=None, pct_elapsed=None),
    )
    rows = _emit_nakshatra_moon(pi, "test-chart", "test-build", "2026-01-01T00:00:00Z", "lahiri_chitrapaksha")
    return {r["fact_key"]: r for r in rows}


def test_ga_panchanga_emits_the_lexicon_spelling_for_the_engines_mrigashira():
    rows = _panchanga_rows("Mrigashira", 5)
    assert rows["name"]["fact_value_text"] == "Mrigasira"            # fails on base: 'Mrigashira' forwarded verbatim
    assert "Mrigasira" in rows["name"]["citation_human"] and "Mrigashira" not in rows["name"]["citation_human"]
    assert rows["number"]["fact_value_num"] == 5.0


def test_ga_panchanga_every_engine_name_emits_its_canonical_name():
    from panchang_engine.shastra_tables import NAKSHATRA_NAMES as ENGINE

    assert len(ENGINE) == 27 and ENGINE[4] == "Mrigashira"            # the engine's own table is untouched
    for i, name in enumerate(ENGINE, start=1):
        assert _panchanga_rows(name, i)["name"]["fact_value_text"] == CANONICAL_NAKSHATRA_NAMES[i - 1], name


def test_ga_panchanga_refuses_an_unregistered_engine_name():
    with pytest.raises(UnknownNakshatraError):
        _panchanga_rows("NotANakshatra", 1)


def test_ga_nakshatra_conjunction_subject_is_the_lexicon_spelling():
    """SS N-568: ga_nakshatra used to write the adapter's spelling ('Mula') as the fact_subject of its
    nakshatra_conjunction rows; the subject is now the lexicon's name. Fails on base."""
    from ga_writers.ga_nakshatra_emitters import PLANET_TO_SUBJECT, emit_dispositor_graph

    chart_output = {"grahas": [{"name": "Moon", "nakshatra": "Mula"}, {"name": "Jupiter", "nakshatra": "Mula"},
                               {"name": "Mars", "nakshatra": "Dhanishta"}, {"name": "Venus", "nakshatra": "Dhanishta"},
                               {"name": "Sun", "nakshatra": "Mrigashira"}],
                    "ascendant": {"nakshatra": "Mrigashira"}}
    rows = emit_dispositor_graph("test-chart", "lahiri_chitrapaksha", "test-build", chart_output,
                                 body_nak_lord={b: b for b in PLANET_TO_SUBJECT})
    conj = {r["fact_subject"]: json.loads(r["fact_value_text"]) for r in rows if r["fact_category"] == "nakshatra_conjunction"}
    assert conj == {"Moola": ["Moon", "Jupiter"], "Dhanishtha": ["Mars", "Venus"], "Mrigasira": ["Sun", "Lagna"]}
    assert not {"Mula", "Dhanishta", "Mrigashira"} & set(conj)


def test_ga_nakshatra_conjunction_refuses_an_unregistered_adapter_name():
    from ga_writers.ga_nakshatra_emitters import PLANET_TO_SUBJECT, emit_dispositor_graph

    with pytest.raises(UnknownNakshatraError):
        emit_dispositor_graph("c", "lahiri_chitrapaksha", "b", {"grahas": [{"name": "Moon", "nakshatra": "NotANakshatra"}], "ascendant": {}},
                              body_nak_lord={b: b for b in PLANET_TO_SUBJECT})
