"""Elevation Campaign β.D — writer & data-integrity regression tests.

Covers EL-30 (house_d1 whole-sign convention), EL-47 (house_from_varga_lagna
persistence), and EL-40 (composite_dispositor_strength discrimination). The
fixtures reproduce the ORIGINAL register recipes verbatim on chart 482012f1's
real sidereal longitudes so the before/after is unambiguous.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ga_writers.ga_sensitive_writer import (  # noqa: E402
    _house_d1,
    _build_arudha_rows,
    HOUSE_CONVENTION_ID,
)
from ga_writers.ga_vargas_writer import _build_position_rows  # noqa: E402

# Real sidereal (lahiri_chitrapaksha) longitudes for chart 482012f1 (Abhisek),
# pulled live from chart_facts 2026-07-25. Lagna 12.43° Aries (mid-sign) — the
# exact condition under which the old degree-arc _house_d1 diverged from
# whole-sign counting.
LAGNA_LON = 12.4311495988431
ALL_LONGS = {
    "LAGNA": LAGNA_LON,
    "SUN": 291.962617284992,
    "MOON": 327.055230133129,
    "MAR": 198.519187554622,
    "MER": 270.838753918698,
    "JUP": 249.787497023181,
    "VEN": 259.172696089456,
    "SAT": 202.431986059195,
}


class TestEL30HouseD1Wholesign:
    """The house_d1 field must be a WHOLE-SIGN house from the lagna (1..12),
    never a degree-arc count and never a sign index."""

    def test_house_d1_matches_el30_evidence(self):
        # EL-30 evidence rows: A1 Capricorn(270°)->10, A7 Aquarius(300°)->11,
        # A10 Aries(0°)->1 (the "0° wraparound" that fit NEITHER convention
        # under the old degree-arc formula, which returned 9/10/12).
        assert _house_d1(270.0, LAGNA_LON) == 10
        assert _house_d1(300.0, LAGNA_LON) == 11
        assert _house_d1(0.0, LAGNA_LON) == 1

    def test_house_d1_is_wholesign_not_arc(self):
        # A graha at any degree within Capricorn is house 10 from an Aries lagna,
        # regardless of the lagna's degree within Aries — the whole-sign invariant.
        for deg in (0.0, 5.0, 29.9):
            assert _house_d1(270.0 + deg, LAGNA_LON) == 10

    def test_lagna_sign_is_house_one(self):
        assert _house_d1(LAGNA_LON, LAGNA_LON) == 1
        assert _house_d1(0.0, 0.0) == 1


class TestEL30ArudhaRows:
    def _arudha_by_subject(self):
        rows = _build_arudha_rows(ALL_LONGS, "test-chart", "lahiri_chitrapaksha",
                                  "test-build", "test-eng")
        out: dict[str, dict[str, object]] = {}
        for r in rows:
            out.setdefault(r["fact_subject"], {})[r["fact_key"]] = r
        return out

    def test_arudha_houses_corrected(self):
        by = self._arudha_by_subject()
        assert by["ARUDHA_A1"]["house_d1"]["fact_value_num"] == 10.0
        assert by["ARUDHA_A7"]["house_d1"]["fact_value_num"] == 11.0
        assert by["ARUDHA_A10"]["house_d1"]["fact_value_num"] == 1.0

    def test_house_rows_carry_convention_stamp(self):
        by = self._arudha_by_subject()
        for subj in ("ARUDHA_A1", "ARUDHA_A7", "ARUDHA_A10"):
            assert by[subj]["house_d1"]["formula_id"] == HOUSE_CONVENTION_ID
        # convention id is explicit and self-describing
        assert HOUSE_CONVENTION_ID == "wholesign_from_lagna:1indexed:v2"


class TestEL47VargaHouse:
    def test_house_from_varga_lagna_present_and_wholesign(self):
        # Synthetic D9 varga_data: Lagna in sign 5 (idx 4), a graha in sign 10
        # (idx 9). Whole-sign house from varga lagna = (9-4)%12+1 = 6.
        varga_data = {
            "Lagna": {"sign_idx": 4, "degree_in_sign": 3.0},
            "Sun": {"sign_idx": 9, "degree_in_sign": 12.0},
        }
        rows = _build_position_rows("test-chart", "lahiri_chitrapaksha", "test-build",
                                    9, "D9", varga_data, {})
        houses = {
            r["fact_subject"]: r["fact_value_num"]
            for r in rows if r["fact_key"] == "house_from_varga_lagna"
        }
        # Lagna itself is house 1; Sun is house 6.
        assert houses["D9.LAGNA"] == 1.0
        assert houses["D9.SUN"] == 6.0

    def test_no_house_key_when_no_lagna(self):
        varga_data = {"Sun": {"sign_idx": 9, "degree_in_sign": 12.0}}
        rows = _build_position_rows("test-chart", "lahiri_chitrapaksha", "test-build",
                                    9, "D9", varga_data, {})
        assert not [r for r in rows if r["fact_key"] == "house_from_varga_lagna"]


class TestEL40DispositorChainMean:
    """The composite dispositor strength must discriminate across grahas, not
    collapse to a chart-global constant (the uniform 0.875 defect)."""

    def test_chain_mean_discriminates(self):
        # Reproduce 482012f1's dispositor topology: every chain sinks into
        # Jupiter (own sign) — the exact condition that made the terminal-only
        # formula uniform. The chain-MEAN must still yield >=3 distinct values.
        from ga_writers.ga_structural_writer import _build_structural_relationship_rows

        signs = {
            "Sun": "Capricorn", "Moon": "Aquarius", "Mars": "Libra",
            "Mercury": "Capricorn", "Jupiter": "Sagittarius", "Venus": "Sagittarius",
            "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio",
        }
        dignities = {
            "Jupiter": "own_sign", "Saturn": "exalted",
        }
        grahas = [
            {"name": n, "sign": s, "dignity_status": dignities.get(n, "neutral"),
             "house": 1}
            for n, s in signs.items()
        ]
        chart_output = {"grahas": grahas}
        rows = _build_structural_relationship_rows(
            chart_output, "test-chart", "test-build", "lahiri_chitrapaksha",
            "2026-07-25T00:00:00Z", "test-eng",
        )
        vals = sorted({
            r["fact_value_num"] for r in rows
            if r["fact_category"] == "composite_dispositor_strength"
        })
        assert len(vals) >= 3, f"expected >=3 distinct dispositor strengths, got {vals}"
        # Not the degenerate uniform-0.875 defect.
        assert vals != [0.875]
