import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import (
    emit_lal_kitab_points,
    emit_maharsi_sphutas,
    emit_bhrigu_nadi_points,
    PAKKA_GHAR,
    NADI_RISHIS_27,
    RISHI_GRAHA_MAP,
)

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())
AY = 'lahiri_chitrapaksha'

GRAHA_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0,  'VEN': 262.0, 'SAT': 215.0, 'RAH': 158.0, 'KET': 338.0,
}


# ---------------------------------------------------------------------------
# emit_lal_kitab_points
# ---------------------------------------------------------------------------

def test_pakka_ghar_sun():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    sun_rows = [r for r in rows if r['fact_subject'] == 'PAKKA_GHAR_SUN' and r['fact_key'] == 'house']
    assert len(sun_rows) == 1
    assert sun_rows[0]['fact_value_num'] == 1.0


def test_pakka_ghar_all_grahas_present():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    subjects = {r['fact_subject'] for r in rows}
    for graha in PAKKA_GHAR:
        assert f"PAKKA_GHAR_{graha}" in subjects, f"Missing subject PAKKA_GHAR_{graha}"


def test_pakka_ghar_row_count():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    # 9 grahas × 4 keys each
    assert len(rows) == 9 * 4


def test_pakka_ghar_verification_pass():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_pakka_ghar_known_values():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    house_rows = {r['fact_subject']: r['fact_value_num']
                  for r in rows if r['fact_key'] == 'house'}
    assert house_rows['PAKKA_GHAR_MOO'] == 4.0
    assert house_rows['PAKKA_GHAR_MAR'] == 3.0
    assert house_rows['PAKKA_GHAR_JUP'] == 2.0
    assert house_rows['PAKKA_GHAR_SAT'] == 8.0
    assert house_rows['PAKKA_GHAR_RAH'] == 4.0
    assert house_rows['PAKKA_GHAR_KET'] == 8.0


def test_pakka_ghar_fact_id_unique():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    fact_ids = [r['fact_id'] for r in rows]
    assert len(fact_ids) == len(set(fact_ids))


def test_pakka_ghar_formula_id_present():
    rows = emit_lal_kitab_points(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    formula_rows = [r for r in rows if r['fact_key'] == 'formula_id']
    for r in formula_rows:
        assert r['fact_value_text'] == 'lal_kitab_pakka_ghar'


# ---------------------------------------------------------------------------
# emit_maharsi_sphutas
# ---------------------------------------------------------------------------

def test_maharsi_sphutas_seven_subjects():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    subjects = {r['fact_subject'] for r in rows}
    expected = {f"{rishi}_SPHUTA" for rishi, _ in RISHI_GRAHA_MAP}
    assert subjects == expected


def test_maharsi_sphutas_row_count():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    # 7 rishis × 5 keys each
    assert len(rows) == 7 * 5


def test_maharsi_sphutas_verification_pass():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_maharsi_vasishtha_longitude():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    lon_rows = [r for r in rows if r['fact_subject'] == 'VASISHTHA_SPHUTA' and r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 1
    # VASISHTHA maps to SUN (301.5)
    assert abs(lon_rows[0]['fact_value_num'] - 301.5) < 0.001


def test_maharsi_nadi_rishi_field():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    nadi_rows = [r for r in rows if r['fact_key'] == 'nadi_rishi']
    assert len(nadi_rows) == 7
    valid_rishis = set(NADI_RISHIS_27)
    for r in nadi_rows:
        assert r['fact_value_text'] in valid_rishis


def test_maharsi_fact_id_unique():
    rows = emit_maharsi_sphutas(CHART_ID, BUILD_ID, AY, GRAHA_LONS)
    fact_ids = [r['fact_id'] for r in rows]
    assert len(fact_ids) == len(set(fact_ids))


# ---------------------------------------------------------------------------
# emit_bhrigu_nadi_points
# ---------------------------------------------------------------------------

def test_bhrigu_nadi_three_subjects():
    rows = emit_bhrigu_nadi_points(
        CHART_ID, BUILD_ID, AY,
        moon_lon=GRAHA_LONS['MOO'],
        rahu_lon=GRAHA_LONS['RAH'],
        sun_lon=GRAHA_LONS['SUN'],
    )
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'BHRIGU_CHAKRA_1', 'BHRIGU_CHAKRA_2', 'BHRIGU_SPECIFIC_VORTEX'}


def test_bhrigu_nadi_row_count():
    rows = emit_bhrigu_nadi_points(
        CHART_ID, BUILD_ID, AY,
        moon_lon=GRAHA_LONS['MOO'],
        rahu_lon=GRAHA_LONS['RAH'],
        sun_lon=GRAHA_LONS['SUN'],
    )
    # 3 subjects × 5 keys each
    assert len(rows) == 3 * 5


def test_bhrigu_chakra_1_longitude():
    moon_lon = GRAHA_LONS['MOO']  # 320.5
    rahu_lon = GRAHA_LONS['RAH']  # 158.0
    expected = ((moon_lon + rahu_lon) / 2) % 360
    rows = emit_bhrigu_nadi_points(CHART_ID, BUILD_ID, AY, moon_lon, rahu_lon, GRAHA_LONS['SUN'])
    lon_rows = [r for r in rows if r['fact_subject'] == 'BHRIGU_CHAKRA_1' and r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 1
    assert abs(lon_rows[0]['fact_value_num'] - expected) < 0.001


def test_bhrigu_vortex_longitude():
    moon_lon = GRAHA_LONS['MOO']  # 320.5
    expected = (moon_lon + 93.333) % 360
    rows = emit_bhrigu_nadi_points(CHART_ID, BUILD_ID, AY, moon_lon, GRAHA_LONS['RAH'], GRAHA_LONS['SUN'])
    lon_rows = [r for r in rows if r['fact_subject'] == 'BHRIGU_SPECIFIC_VORTEX' and r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 1
    assert abs(lon_rows[0]['fact_value_num'] - expected) < 0.001


def test_bhrigu_nadi_verification_pass():
    rows = emit_bhrigu_nadi_points(
        CHART_ID, BUILD_ID, AY,
        moon_lon=GRAHA_LONS['MOO'],
        rahu_lon=GRAHA_LONS['RAH'],
        sun_lon=GRAHA_LONS['SUN'],
    )
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_bhrigu_nadi_tolerance_arcsec():
    rows = emit_bhrigu_nadi_points(
        CHART_ID, BUILD_ID, AY,
        moon_lon=GRAHA_LONS['MOO'],
        rahu_lon=GRAHA_LONS['RAH'],
        sun_lon=GRAHA_LONS['SUN'],
    )
    tol_rows = [r for r in rows if r['fact_key'] == 'tolerance_arcsec']
    assert len(tol_rows) == 3
    for r in tol_rows:
        assert r['fact_value_num'] == 60.0


def test_bhrigu_nadi_fact_id_unique():
    rows = emit_bhrigu_nadi_points(
        CHART_ID, BUILD_ID, AY,
        moon_lon=GRAHA_LONS['MOO'],
        rahu_lon=GRAHA_LONS['RAH'],
        sun_lon=GRAHA_LONS['SUN'],
    )
    fact_ids = [r['fact_id'] for r in rows]
    assert len(fact_ids) == len(set(fact_ids))
