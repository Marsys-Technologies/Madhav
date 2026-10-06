"""
tests/test_ga_vargas_narr_golden.py -- narr golden-value test for ga_vargas.

The ga_vargas row builders compose ``chart_divisionals.citation_human`` from the row's own computed
varga fields. Fixed Navamsha (D9) fragment, Aries D9 Lagna, built with the real builders and no
database. Expected sentences are written out by hand from the classical rules:

  * Sun in Aries (12 deg) is exalted; Saturn in Aries (3 deg) is debilitated (its fall sign);
    Mars in Scorpio (10 deg) is in its own sign;
  * house numbering is whole-sign from the varga Lagna: Mars in Scorpio, the 8th sign from Aries,
    occupies house 8; the 11th house from an Aries Lagna is Aquarius, ruled by Saturn;
  * the vargottama sentence follows the sign-equality flag: Sun stays in Aries in D1 and D9 (True),
    Mars is in Cancer in D1 but Scorpio in D9 (False).
"""
from __future__ import annotations

from ga_writers.ga_vargas_writer import (
    _build_dignity_rows,
    _build_house_lord_occupant_rows,
    _build_vargottama_rows,
)

_D9 = {
    "Lagna": {"sign_idx": 0, "degree_in_sign": 5.0},
    "Sun": {"sign_idx": 0, "degree_in_sign": 12.0},
    "Saturn": {"sign_idx": 0, "degree_in_sign": 3.0},
    "Mars": {"sign_idx": 7, "degree_in_sign": 10.0},
}
_D1 = {
    "Sun": {"sign_idx": 0, "degree_in_sign": 12.0},
    "Mars": {"sign_idx": 3, "degree_in_sign": 1.0},
}


def test_citation_human_states_varga_dignity_house_and_vargottama():
    dignity_rows = {
        r["graha"]: r
        for r in _build_dignity_rows("chart-1", "lahiri_chitrapaksha", "build-1", 9, "D9", _D9)
    }
    row = dignity_rows["Sun"]
    assert row["citation_human"] == "Sun's D9 dignity: Exalted (lahiri)."
    row = dignity_rows["Saturn"]
    assert row["citation_human"] == "Saturn's D9 dignity: Debilitated (lahiri)."
    row = dignity_rows["Mars"]
    assert row["citation_human"] == "Mars's D9 dignity: Own (lahiri)."

    house_rows = _build_house_lord_occupant_rows(
        "chart-1", "lahiri_chitrapaksha", "build-1", 9, "D9", _D9)
    occupant = {r["graha"]: r for r in house_rows if r["fact_category"] == "varga_house_occupant"}
    lord = {r["house"]: r for r in house_rows if r["fact_category"] == "varga_house_lord"}
    row = occupant["Mars"]
    assert row["citation_human"] == "Mars occupies house 8 in D9 (lahiri_chitrapaksha)."
    row = lord[11]
    assert row["citation_human"] == "House 11 lord in D9: Saturn (lahiri_chitrapaksha)."

    flag_rows = {
        r["graha"]: r
        for r in _build_vargottama_rows(
            "chart-1", "lahiri_chitrapaksha", "build-1", 9, "D9", _D9, _D1)
    }
    row = flag_rows["Sun"]
    assert row["citation_human"] == "Sun vargottama in D9: True (lahiri_chitrapaksha)."
    row = flag_rows["Mars"]
    assert row["citation_human"] == "Mars vargottama in D9: False (lahiri_chitrapaksha)."
