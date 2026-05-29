import uuid
from pipeline.writers.sensitive_points_writer_a5 import (
    emit_aprakasha,
    emit_brahma_vishnu_shiva,
    emit_sri_yantra,
)

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())
AY = 'lahiri_chitrapaksha'

SUN = 301.5
MOON = 320.5
LAGNA = 48.0
SATURN = 215.0
JUP = 95.0


# ── emit_aprakasha ──────────────────────────────────────────────────────────

def _aprakasha_rows():
    return emit_aprakasha(CHART_ID, BUILD_ID, AY, SUN, SATURN, MOON, LAGNA)


def test_aprakasha_five_subjects():
    rows = _aprakasha_rows()
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'DHWAJA', 'PATALA', 'KANDANGA', 'PIDAA', 'VIGHNI'}


def test_aprakasha_all_two_pass_verified():
    rows = _aprakasha_rows()
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_aprakasha_longitude_range():
    rows = _aprakasha_rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 5
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_aprakasha_formula_ids():
    rows = _aprakasha_rows()
    formula_rows = {r['fact_subject']: r['fact_value_text']
                    for r in rows if r['fact_key'] == 'formula_id'}
    assert formula_rows['DHWAJA'] == 'bphs_dhwaja'
    assert formula_rows['PATALA'] == 'bphs_patala'
    assert formula_rows['KANDANGA'] == 'bphs_kandanga'
    assert formula_rows['PIDAA'] == 'bphs_pidaa'
    assert formula_rows['VIGHNI'] == 'bphs_vighni'


def test_aprakasha_category():
    rows = _aprakasha_rows()
    for r in rows:
        assert r['fact_category'] == 'aprakasha_position'


def test_aprakasha_citation_format():
    rows = _aprakasha_rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows:
        assert '@chart=' in r['citation_ref']
        assert r['citation_human'].endswith('.')


# ── emit_brahma_vishnu_shiva ────────────────────────────────────────────────

def _bvs_rows():
    return emit_brahma_vishnu_shiva(CHART_ID, BUILD_ID, AY, LAGNA, SUN, MOON, JUP, SATURN)


def test_bvs_three_subjects():
    rows = _bvs_rows()
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'BRAHMA_POINT', 'VISHNU_POINT', 'SHIVA_POINT'}


def test_bvs_all_two_pass_verified():
    rows = _bvs_rows()
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_bvs_longitude_range():
    rows = _bvs_rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 3
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_bvs_formula_ids():
    rows = _bvs_rows()
    formula_rows = {r['fact_subject']: r['fact_value_text']
                    for r in rows if r['fact_key'] == 'formula_id'}
    assert formula_rows['BRAHMA_POINT'] == 'jaimini_sutram_brahma'
    assert formula_rows['VISHNU_POINT'] == 'jaimini_sutram_vishnu'
    assert formula_rows['SHIVA_POINT'] == 'jaimini_sutram_shiva'


def test_bvs_category_prefix():
    rows = _bvs_rows()
    for r in rows:
        assert r['fact_category'].startswith('esoteric_point_')


def test_bvs_citation_format():
    rows = _bvs_rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows:
        assert '@chart=' in r['citation_ref']
        assert r['citation_human'].endswith('.')


# ── emit_sri_yantra ─────────────────────────────────────────────────────────

def _yantra_rows():
    return emit_sri_yantra(CHART_ID, BUILD_ID, AY, SUN, MOON, LAGNA)


def test_sri_yantra_three_subjects():
    rows = _yantra_rows()
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'SRI_YANTRA_SUN', 'SRI_YANTRA_MOON', 'SRI_YANTRA_LAGNA'}


def test_sri_yantra_all_two_pass_verified():
    rows = _yantra_rows()
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_sri_yantra_longitude_range():
    rows = _yantra_rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 3
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_sri_yantra_triangle_position_range():
    rows = _yantra_rows()
    ypos_rows = [r for r in rows if r['fact_key'] == 'yantra_triangle_position']
    assert len(ypos_rows) == 3
    for r in ypos_rows:
        assert 0.0 <= r['fact_value_num'] < 9.0


def test_sri_yantra_category():
    rows = _yantra_rows()
    for r in rows:
        assert r['fact_category'] == 'esoteric_point_sri_yantra_position'


def test_sri_yantra_required_fields():
    rows = _yantra_rows()
    for r in rows:
        assert r['fact_id']
        assert r['chart_id'] == CHART_ID
        assert r['ayanamsha_id'] == AY
        assert r['engine_version']
        assert r['computed_at'] is not None
