"""G-10 (ruling sheet M-7): per-contributor BAV matrix (ashtakavarga_bindu_contributor).

Fixture chart semantics: PyJHora prastara must match BPHS ch.66 dot/rekha
semantics — for aṣṭakavarga graha g and contributor c, matrix[g][c][s] == 1
exactly when s is one of the benefic houses of g's table counted from c's
rāśi — and the contributor sum must reproduce the raw BAV row. Nāḍī kakṣyā
rows PG1615/PG1616 attest the doctrine at TESTIMONY grade (N-21).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import swisseph as swe  # noqa: E402

from ga_writers.ga_strength_writer import (  # noqa: E402
    _AV_CLASSICAL_7,
    _AV_CONTRIBUTORS,
    _build_ashtakavarga_rows,
    _derive_ashtakavarga,
    _derive_ashtakavarga_prastara,
)

from .conftest import EPHE_PATH  # noqa: E402


def _restore_ephe_path() -> None:
    # PyJHora's chart calls redirect the global Swiss ephemeris path to its
    # wheel directory (which ships no .se1 files); re-assert the pinned
    # directory so later direct swe.calc_ut calls in this suite keep SWIEPH.
    swe.set_ephe_path(EPHE_PATH)

# Synthetic fixture chart: 1990-01-01 12:00 IST (06:30 UT), Chennai.
# Swiss-ephemeris independent of ayanāṃśa for the rāśi chart.
JD_UT = swe.julday(1990, 1, 1, 6.5)
LAT, LON, TZ = 13.0827, 80.2707, 5.5
AYANAMSHA = "true_chitra"

CHART_ID = "g10-synthetic-fixture"
BUILD_ID = "g10-build"
COMPUTED_AT = "2026-09-24T00:00:00+00:00"
ENG_VER = "test"


@pytest.fixture(scope="module")
def prastara():
    try:
        return _derive_ashtakavarga_prastara(JD_UT, AYANAMSHA, lat=LAT, lon=LON, tz=TZ)
    finally:
        _restore_ephe_path()


@pytest.fixture(scope="module")
def bav():
    try:
        return _derive_ashtakavarga(JD_UT, AYANAMSHA, lat=LAT, lon=LON, tz=TZ)["bindus"]
    finally:
        _restore_ephe_path()


def test_prastara_shape_and_binary_values(prastara):
    assert set(prastara) == set(_AV_CLASSICAL_7)
    for graha, contrib_map in prastara.items():
        assert set(contrib_map) == set(_AV_CONTRIBUTORS)
        for contrib, grid in contrib_map.items():
            assert len(grid) == 12, (graha, contrib)
            assert set(grid) <= {0, 1}, (graha, contrib, grid)


def test_prastara_matches_bphs_ch66_dot_rekha_semantics(prastara):
    """For each (g, c): dots land exactly on the benefic houses of g's table
    counted from c's rāśi (BPHS ch.66; PyJHora const.ashtaka_varga_dict)."""
    from pyjhora_adapter._jhora import charts, const, utils
    from pyjhora_adapter import strength as pst

    place = pst._place(LAT, LON, TZ)
    pst._set_ayanamsha(AYANAMSHA)
    pp = charts.rasi_chart(JD_UT, place)
    chart_1d = utils.get_house_planet_list_from_planet_positions(pp)
    p_to_h = utils.get_planet_to_house_dict_from_chart(chart_1d)
    _restore_ephe_path()

    for gi, graha in enumerate(_AV_CLASSICAL_7):
        benefic_table = const.ashtaka_varga_dict[str(gi)]
        assert len(benefic_table) == 8
        for ci, contrib in enumerate(_AV_CONTRIBUTORS):
            c_sign = p_to_h[const._ascendant_symbol] if ci == 7 else p_to_h[ci]
            expected = {((c_sign + rel - 1) % 12) for rel in benefic_table[ci]}
            actual = {s for s, dot in enumerate(prastara[graha][contrib]) if dot == 1}
            assert actual == expected, (graha, contrib, sorted(actual), sorted(expected))


def test_contributor_sum_reproduces_raw_bav(prastara, bav):
    for graha in _AV_CLASSICAL_7:
        summed = [
            sum(prastara[graha][c][s] for c in _AV_CONTRIBUTORS)
            for s in range(12)
        ]
        assert summed == [int(v) for v in bav[graha]], graha
    # Sarvāṣṭakavarga invariant preserved through the matrix.
    sarva = [
        sum(prastara[g][c][s] for g in _AV_CLASSICAL_7 for c in _AV_CONTRIBUTORS)
        for s in range(12)
    ]
    assert sum(sarva) == 337


def test_row_builder_emits_672_contributor_rows(prastara, bav):
    pinda = {g: {"sodhya": 0, "graha": 0, "raasi": 0} for g in _AV_CLASSICAL_7}
    rows = _build_ashtakavarga_rows(
        bav, pinda, CHART_ID, BUILD_ID, AYANAMSHA,
        COMPUTED_AT, ENG_VER, "single_pass", prastara=prastara,
    )
    contrib_rows = [r for r in rows if r["fact_category"] == "ashtakavarga_bindu_contributor"]
    assert len(contrib_rows) == 7 * 8 * 12

    by_key = {}
    for r in contrib_rows:
        assert r["fact_key"] == "bindus"
        assert r["unit"] == "bindu"
        assert r["fact_value_num"] in (0.0, 1.0)
        assert "PG1615/PG1616" in r["citation_human"]
        assert "testimony grade" in r["citation_human"]
        graha = r["fact_subject"].split("-CONTRIBUTOR_")[0]
        sign = int(r["fact_subject"].rsplit("-SIGN_", 1)[1])
        by_key[(graha, sign)] = by_key.get((graha, sign), 0.0) + r["fact_value_num"]

    bindu_sign = {
        (r["fact_subject"].split("-SIGN_")[0], int(r["fact_subject"].rsplit("-SIGN_", 1)[1])): r["fact_value_num"]
        for r in rows
        if r["fact_category"] == "ashtakavarga_bindu_sign" and r["fact_subject"] != "SARVA"
        and not r["fact_subject"].startswith("SARVA-")
    }
    for (graha, sign), total in by_key.items():
        assert bindu_sign[(graha, sign)] == total, (graha, sign)
