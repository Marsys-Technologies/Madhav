import uuid
from pipeline.writers.sensitive_points_writer_a5 import emit_sahams


def _rows(is_day_birth=True):
    return emit_sahams(
        str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
        301.5, 320.5, 48.0, 181.0, 298.0, 57.0, 262.0, 215.0, 158.0, 338.0,
        is_day_birth=is_day_birth,
    )


def test_saham_count_70plus():
    rows = _rows()
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) >= 70, f"Expected >=70 sahams, got {len(subjects)}"


def test_total_row_count_700plus():
    rows = _rows()
    assert len(rows) >= 700, f"Expected >=700 rows, got {len(rows)}"


def test_two_pass_punya():
    rows = _rows()
    punya = [r for r in rows if r['fact_subject'] == 'PUNYA' and r['fact_key'] == 'longitude_sidereal']
    assert len(punya) == 1
    assert punya[0]['verification_pass_status'] == 'two_pass_verified'
    assert 0 <= punya[0]['fact_value_num'] < 360


def test_all_two_pass_verified():
    for r in _rows():
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_longitude_range():
    lon_rows = [r for r in _rows() if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) >= 70
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_day_night_reversal():
    day_rows = {r['fact_subject']: r['fact_value_num']
                for r in _rows(is_day_birth=True) if r['fact_key'] == 'longitude_sidereal'}
    night_rows = {r['fact_subject']: r['fact_value_num']
                  for r in _rows(is_day_birth=False) if r['fact_key'] == 'longitude_sidereal'}
    # At least some sahams must differ between day and night
    diffs = sum(1 for k in day_rows if abs(day_rows[k] - night_rows.get(k, day_rows[k])) > 0.01)
    assert diffs > 0, "Expected day/night formulas to differ for at least some sahams"


def test_required_keys_present():
    rows = _rows()
    punya_rows = [r for r in rows if r['fact_subject'] == 'PUNYA']
    keys = {r['fact_key'] for r in punya_rows}
    for expected in ('longitude_sidereal', 'sign', 'nakshatra', 'formula_id',
                     'formula_provenance_text', 'tolerance_arcsec'):
        assert expected in keys, f"Missing key: {expected}"


def test_citation_ref_format():
    for r in _rows():
        if r['fact_key'] == 'longitude_sidereal':
            assert '@chart=' in r['citation_ref']
            assert r['citation_human'].endswith('.')
