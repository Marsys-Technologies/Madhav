import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import emit_arudhas

# Synthetic house cusps and graha lons matching the brief §2 test vectors
HOUSE_CUSPS = [48.0, 78.0, 108.0, 138.0, 168.0, 198.0, 228.0, 258.0, 288.0, 318.0, 348.0, 18.0]
GRAHA_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0,  'VEN': 262.0, 'SAT': 215.0, 'RAH': 158.0, 'KET': 338.0,
}

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())
AYANAMSHA = 'lahiri_chitrapaksha'


def _rows():
    return emit_arudhas(CHART_ID, BUILD_ID, AYANAMSHA, HOUSE_CUSPS, GRAHA_LONS)


def test_arudha_count_19():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 19
    assert 'ARUDHA_A1' in subjects and 'ARUDHA_A12' in subjects
    assert 'ARUDHA_SU' in subjects and 'ARUDHA_SA' in subjects


def test_arudha_asc_range():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows}
    for h in range(1, 13):
        assert f'ARUDHA_A{h}' in subjects


def test_arudha_graha_all_seven():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows}
    for code in ['SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA']:
        assert f'ARUDHA_{code}' in subjects


def test_all_two_pass():
    rows = _rows()
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_fact_category():
    rows = _rows()
    for r in rows:
        assert r['fact_category'] == 'arudha_pada'


def test_ul_alias_on_a12():
    rows = _rows()
    a12_alias_rows = [r for r in rows if r['fact_subject'] == 'ARUDHA_A12' and r['fact_key'] == 'alias']
    assert len(a12_alias_rows) == 1
    assert a12_alias_rows[0]['fact_value_text'] == 'UL'


def test_gl_alias_on_a11():
    rows = _rows()
    a11_alias_rows = [r for r in rows if r['fact_subject'] == 'ARUDHA_A11' and r['fact_key'] == 'alias']
    assert len(a11_alias_rows) == 1
    assert a11_alias_rows[0]['fact_value_text'] == 'GL'


def test_dp_alias_on_a9():
    rows = _rows()
    a9_alias_rows = [r for r in rows if r['fact_subject'] == 'ARUDHA_A9' and r['fact_key'] == 'alias']
    assert len(a9_alias_rows) == 1
    assert a9_alias_rows[0]['fact_value_text'] == 'DP'


def test_longitude_in_range():
    rows = _rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_sign_is_valid():
    valid_signs = {'ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS'}
    rows = _rows()
    for r in rows:
        if r['fact_key'] == 'sign':
            assert r['fact_value_text'] in valid_signs
