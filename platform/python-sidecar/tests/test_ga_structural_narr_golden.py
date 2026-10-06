"""
tests/test_ga_structural_narr_golden.py -- narr golden-value test for ga_structural.

``_build_special_state_rows`` composes ``chart_facts.citation_human`` for the graha special states
(combustion, retrogression, exaltation / debilitation, vargottama). Fixed natal fragment, Aries
lagna, no database connection (conn=None):

  * Sun 292.5 deg and Mars 298.0 deg, both in Capricorn (Mars exalted there): the arc is 5.5 deg,
    inside the classical Mars combustion orb of 17 deg, so Mars is combust AND exalted; the Sun is
    never narrated as combust;
  * Saturn at 190.0 deg (Libra, exalted, retrograde) is 102.5 deg from the Sun -- not combust;
  * with no connection the D9 vargottama flag is not readable, so the sentence must say
    "unavailable" (an honest gap), never a yes/no it did not derive.
"""
from __future__ import annotations

from ga_writers.ga_structural_writer import _build_special_state_rows

_CHART_OUTPUT = {
    "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 5.0},
    "grahas": [
        {"name": "Sun", "longitude": 292.5, "sign": "Capricorn", "sign_id": 10, "house": 10,
         "dignity_status": "neutral", "retrograde": False},
        {"name": "Mars", "longitude": 298.0, "sign": "Capricorn", "sign_id": 10, "house": 10,
         "dignity_status": "exalted", "retrograde": False},
        {"name": "Saturn", "longitude": 190.0, "sign": "Libra", "sign_id": 7, "house": 7,
         "dignity_status": "exalted", "retrograde": True},
    ],
}


def test_citation_human_states_special_states_from_the_graha_row():
    built = _build_special_state_rows(
        _CHART_OUTPUT, "chart-1", "build-1", "lahiri", "2026-01-01T00:00:00Z", "eng-1", None,
    )
    rows = {(r["fact_subject"], r["fact_key"]): r for r in built}

    row = rows[("MAR", "is_combust")]
    assert row["citation_human"] == "Mars combust: yes (lahiri)."

    row = rows[("MAR", "is_exalted")]
    assert row["citation_human"] == "Mars exalted: yes (lahiri)."

    row = rows[("SUN", "is_combust")]
    assert row["citation_human"] == "Sun combust: no (lahiri)."

    row = rows[("SAT", "is_retrograde")]
    assert row["citation_human"] == "Saturn retrograde: yes (lahiri)."

    row = rows[("SAT", "is_combust")]
    assert row["citation_human"] == "Saturn combust: no (lahiri)."

    row = rows[("MAR", "is_vargottama")]
    assert row["citation_human"] == (
        "Mars vargottama: unavailable — ga_vargas' own varga_vargottama_flag "
        "row not yet built for D9 (lahiri)."
    )
