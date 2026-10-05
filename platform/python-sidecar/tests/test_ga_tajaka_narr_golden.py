"""
tests/test_ga_tajaka_narr_golden.py -- narr golden-value test for ga_tajaka.

``_compute_one`` composes ``citation_human`` for a Varsha (annual chart) row: the varsha window,
the Muntha sign, its house from the natal Lagna and its lord, the Varshesha (Vārṣeśa, year lord)
and the Pañcavargīya winner. No database and no ephemeris: the solar-return root-find and the
annual-chart compute are replaced by fixed fakes, and the Tri-Rashipati read by a fake connection.

Fixed case (derived by hand from the Tajika Nilakanthi rules the writer cites):

  * natal Lagna Leo; varsha year 13 -> Muntha advances one sign per year, (13 - 1) = 12 signs, so it
    is back on Leo: house 1 from the natal Lagna, lord the Sun;
  * the five office-bearers (Lagnesa, Munthesa, Janma-Lagnesa, Tri-Rashipati, Dina-Ratri-pati) are
    all the Sun: the annual Lagna is Leo (lord Sun), Muntha lord Sun, natal Lagna lord Sun,
    Tri-Rashipati read as Sun, and the Sun stands in house 8 (7..12, above the horizon -> day -> Sun);
  * so whatever the strength figures, the Varshesha (tajik_classical, with the Muntha lord as the
    fallback when none aspects the Lagna) and the Pancavargiya winner are both the Sun, the two methods
    do not diverge, and the sentence ends with a plain full stop.
"""
from __future__ import annotations

from datetime import datetime

import ga_writers.ga_tajaka_writer as tajaka_module
from ga_writers.ga_tajaka_writer import _compute_one


class _FakeCursor:
    def fetchone(self):
        return {"fact_value_text": "Sun"}


class _FakeConn:
    def execute(self, *_args, **_kwargs):
        return _FakeCursor()


def test_citation_human_states_varsha_window_muntha_and_year_lord(monkeypatch):
    def fake_solar_return(varsha_year, natal_sun_long, aya_adapter, birth_params=None):
        # The varsha window opens on the anniversary of the birth date in 1984 + (year - 1).
        return (datetime(1984 + varsha_year - 1, 2, 5, 10, 43, 0),
                {"converged": True, "diff_deg": 0.001, "bracket_days": 2, "iterations": 20})

    def fake_compute_chart(_birth, ayanamsha_id=None):
        return {
            "ascendant": {"sign_id": 5, "longitude_deg": 125.0},
            "grahas": [{"name": "Sun", "longitude": 200.0, "house": 8}],
        }

    monkeypatch.setattr(tajaka_module, "_solar_return", fake_solar_return)
    monkeypatch.setattr(tajaka_module, "compute_chart", fake_compute_chart)

    natal_chart = {"ascendant": {"sign_id": 5, "degree_in_sign": 10.0}}
    row = _compute_one(
        _FakeConn(), "chart-1", "lahiri_chitrapaksha", "lahiri", 13, natal_chart, 292.5,
        "build-1", birth={"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27,
                          "longitude_deg": 85.84, "tz_offset_hours": 5.5},
    )
    assert row["citation_human"] == (
        "Varsha 13 (1996-02-05→1997-02-05, lahiri_chitrapaksha): Muntha Leo "
        "(1H from Lagna, lord Sun); Vārṣeśa Sun (tajik_classical); "
        "Pañcavargīya winner Sun."
    )
