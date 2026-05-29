import uuid
from pipeline.writers.sensitive_points_writer_a5 import emit_esoteric_bindus

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())
AY = 'lahiri_chitrapaksha'

# Native chart values per brief §3
MOON = 320.5
SUN = 301.5
LAGNA = 48.0
RAHU = 158.0
SATURN = 215.0


def _rows():
    return emit_esoteric_bindus(None, CHART_ID, BUILD_ID, AY, MOON, SUN, LAGNA, RAHU, SATURN)


def test_bhrigu_bindu():
    rows = _rows()
    bb_rows = [r for r in rows if r['fact_subject'] == 'BHRIGU_BINDU']
    assert len(bb_rows) > 0


def test_yogi_two_variants():
    rows = _rows()
    yogi_rows = [r for r in rows if 'YOGI_POINT' in r['fact_subject']]
    subjects = {r['fact_subject'] for r in yogi_rows}
    assert 'YOGI_POINT_BPHS' in subjects and 'YOGI_POINT_ALT' in subjects


def test_avayogi_two_variants():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows if 'AVAYOGI' in r['fact_subject']}
    assert 'AVAYOGI_POINT_BPHS' in subjects and 'AVAYOGI_POINT_ALT' in subjects


def test_mrityu_three_variants():
    rows = _rows()
    mrityu_subjects = {r['fact_subject'] for r in rows if 'MRITYU' in r['fact_subject']}
    assert len(mrityu_subjects) == 3


def test_trisphuta_family_present():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows}
    assert 'TRISPHUTA' in subjects
    assert 'CHATUSHPHUTA' in subjects
    assert 'PANCHASPHUTA_SAT' in subjects
    assert 'PANCHASPHUTA_RAH' in subjects
    assert 'PRANAPADA_SPHUTA' in subjects
    assert 'TRIKONA_DASHA_SPHUTA' in subjects


def test_all_two_pass():
    rows = _rows()
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_longitude_range():
    rows = _rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) > 0
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_citation_format():
    rows = _rows()
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows:
        assert '@chart=' in r['citation_ref']
        assert r['citation_human'].endswith('.')


def test_formula_ids_present():
    rows = _rows()
    formula_rows = {r['fact_subject']: r['fact_value_text']
                    for r in rows if r['fact_key'] == 'formula_id'}
    assert formula_rows['BHRIGU_BINDU'] == 'bphs_midpoint_moon_rahu'
    assert formula_rows['YOGI_POINT_BPHS'] == 'bphs_93_20'
    assert formula_rows['YOGI_POINT_ALT'] == 'alt_96_40'
    assert formula_rows['MRITYU_BPHS'] == 'bphs_ch39'
    assert formula_rows['MRITYU_SARAVALI'] == 'saravali'
    assert formula_rows['MRITYU_TAJIK'] == 'tajik_aapamrityu'


def test_all_rows_have_required_fields():
    rows = _rows()
    for r in rows:
        assert r['fact_id']
        assert r['chart_id'] == CHART_ID
        assert r['ayanamsha_id'] == AY
        assert r['fact_category'].startswith('esoteric_point_')
        assert r['engine_version']
        assert r['computed_at'] is not None
