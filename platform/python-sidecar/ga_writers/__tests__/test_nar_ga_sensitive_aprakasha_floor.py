"""
test_nar_ga_sensitive_aprakasha_floor.py — B-NAR-GA regression test for the
SAMĀPTI_NARRATION_TRIAGE_AND_PARTITION §4.2 / §2.5 CONFIRMED finding at
ga_sensitive_writer.py:2677.

Prior defect: `gulika_long`/`mandi_long` were seeded with a hand-rolled
`Saturn + 6°` / `Saturn + 8°` proxy — a fabrication the M-11 fix already
rejected for the sibling `saturn_derived_point` rows (GULIKA_LAHIRI/MANDI are
floored on adapter error, never guessed) — and then only overwritten with the
real PyJHora value using bare `if v:` truthiness, which also silently
discarded a legitimate `longitude_deg == 0.0` (0°00' Aries). Any adapter
error path returning `{"error": ...}` (still a dict, still with no
`longitude_deg`) let the fabricated seed survive undetected, served as
`aprakasha_position/PIDAA` and `VIGHNI` under an ordinary (non-floored)
verification status and a classical BPHS Ch.8 attribution.

The fix seeds `gulika_long`/`mandi_long` as `None`, checks `is not None`, and
`_build_aprakasha_rows` now floors PIDAA/VIGHNI (verification_pass_status=
"floored" + [EXTERNAL_COMPUTATION_REQUIRED] provenance) when the honest input
is None — mirroring `_build_saturn_derived_rows`'s existing floor-on-error
convention for the identical gulika/maandi lookup.

DB-free: exercises `_build_aprakasha_rows` directly with canned longitude
inputs, following this test directory's existing style
(test_ga_sensitive_enrichment.py imports builder functions directly and
calls them with literal ALL_LONGS/CHART_DATA fixtures).
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from ga_writers.ga_sensitive_writer import _build_aprakasha_rows  # noqa: E402

CHART_ID = "test-chart-id"
AYA_ID = "lahiri"
BUILD_ID = "test-build"
ENG_VER = "1.0"

ALL_LONGS = {
    "SUN": 296.5,
    "MOON": 332.0,
    "MER": 280.0,
    "LAGNA": 10.0,
}


def _rows_for(subject: str, rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["fact_subject"] == subject]


class TestAprakashaFloorsOnMissingGulikaMandi:
    def test_real_gulika_mandi_yields_ordinary_verified_pidaa_vighni(self):
        rows = _build_aprakasha_rows(ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
                                      gulika_long=215.0, mandi_long=225.0)
        pidaa_long = [r for r in _rows_for("PIDAA", rows) if r["fact_key"] == "longitude_sidereal"][0]
        vighni_long = [r for r in _rows_for("VIGHNI", rows) if r["fact_key"] == "longitude_sidereal"][0]
        assert pidaa_long["fact_value_num"] == 215.0
        assert pidaa_long["verification_pass_status"] != "floored"
        assert vighni_long["fact_value_num"] == 245.0  # (225 + 20) % 360
        assert vighni_long["verification_pass_status"] != "floored"

    def test_none_gulika_floors_pidaa_not_a_saturn_plus_6_fabrication(self):
        # THE regression this test locks: pre-fix code could never even
        # reach this branch — gulika_long was never None, it was always at
        # minimum the Saturn+6 proxy. Post-fix, an honest None input must
        # floor PIDAA rather than silently computing a fabricated longitude.
        rows = _build_aprakasha_rows(ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
                                      gulika_long=None, mandi_long=225.0)
        pidaa_rows = _rows_for("PIDAA", rows)
        assert len(pidaa_rows) == 1, "floored PIDAA should emit exactly one row, not the full _long_rows fan-out"
        assert pidaa_rows[0]["verification_pass_status"] == "floored"
        assert pidaa_rows[0]["fact_value_num"] is None
        assert "EXTERNAL_COMPUTATION_REQUIRED" in pidaa_rows[0]["formula_provenance_text"]

    def test_none_mandi_floors_vighni_not_a_saturn_plus_8_fabrication(self):
        rows = _build_aprakasha_rows(ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
                                      gulika_long=215.0, mandi_long=None)
        vighni_rows = _rows_for("VIGHNI", rows)
        assert len(vighni_rows) == 1
        assert vighni_rows[0]["verification_pass_status"] == "floored"
        assert vighni_rows[0]["fact_value_num"] is None
        assert "EXTERNAL_COMPUTATION_REQUIRED" in vighni_rows[0]["formula_provenance_text"]

    def test_pidaa_normalizes_to_0_360_range(self):
        # Prior code assigned `pidaa = gulika_long` with no modulo, unlike
        # vighni's `% 360.0` — a gulika_long near 360° could overflow to
        # 360-366°, which no native sidereal value can produce.
        rows = _build_aprakasha_rows(ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
                                      gulika_long=355.0 + 10.0, mandi_long=225.0)
        pidaa_long = [r for r in _rows_for("PIDAA", rows) if r["fact_key"] == "longitude_sidereal"][0]
        assert 0.0 <= pidaa_long["fact_value_num"] < 360.0
        assert pidaa_long["fact_value_num"] == 5.0

    def test_dhwaja_patala_kandanga_unaffected_by_none_inputs(self):
        # DHWAJA/PATALA/KANDANGA derive from SUN/MOON/MER only — must still
        # be served (and not floored) even when gulika/mandi are both None.
        rows = _build_aprakasha_rows(ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
                                      gulika_long=None, mandi_long=None)
        for subj in ("DHWAJA", "PATALA", "KANDANGA"):
            long_row = [r for r in _rows_for(subj, rows) if r["fact_key"] == "longitude_sidereal"][0]
            assert long_row["fact_value_num"] is not None
            assert long_row["verification_pass_status"] != "floored"
