import pytest
import uuid
from pipeline.writers.sensitive_points_writer_a5 import emit_upagrahas, emit_saturn_derived


def test_upagrahas_count():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'DHUMA', 'VYATIPATA', 'PARIVESHA', 'INDRACHAPA', 'UPAKETU', 'KALA'}


def test_saturn_derived_count():
    rows = emit_saturn_derived(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 215.0, weekday=0)
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'GULIKA_LAHIRI', 'GULIKA_HINDU', 'MANDI', 'YAMAGANDA_SPHUTA', 'MAANDI'}


def test_two_pass():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_citation_format():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    for r in lon_rows:
        assert '@chart=' in r['citation_ref']
        assert r['citation_human'].endswith('.')


def test_saturn_derived_two_pass():
    rows = emit_saturn_derived(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 215.0, weekday=3)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_upagrahas_all_keys_present():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    dhuma_rows = [r for r in rows if r['fact_subject'] == 'DHUMA']
    keys = {r['fact_key'] for r in dhuma_rows}
    assert 'longitude_sidereal' in keys
    assert 'sign' in keys
    assert 'nakshatra' in keys
    assert 'formula_id' in keys
    assert 'verification_pass_status' not in keys  # stored on row, not as a key


def test_upagrahas_formula_id():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    formula_rows = [r for r in rows if r['fact_key'] == 'formula_id']
    for r in formula_rows:
        assert r['fact_value_text'] == 'bphs_ch4'


def test_saturn_derived_formula_ids():
    rows = emit_saturn_derived(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 215.0, weekday=0)
    formula_rows = {r['fact_subject']: r['fact_value_text']
                    for r in rows if r['fact_key'] == 'formula_id'}
    assert formula_rows['GULIKA_LAHIRI'] == 'bphs_gulika_lahiri'
    assert formula_rows['GULIKA_HINDU'] == 'bphs_gulika_hindu'
    assert formula_rows['MANDI'] == 'bphs_mandi'
    assert formula_rows['YAMAGANDA_SPHUTA'] == 'bphs_yamaganda'
    assert formula_rows['MAANDI'] == 'bphs_maandi'


def test_upagrahas_longitude_range():
    rows = emit_upagrahas(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 301.5)
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 6
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0


def test_saturn_derived_longitude_range():
    rows = emit_saturn_derived(None, str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 215.0, weekday=0)
    lon_rows = [r for r in rows if r['fact_key'] == 'longitude_sidereal']
    assert len(lon_rows) == 5
    for r in lon_rows:
        assert 0.0 <= r['fact_value_num'] < 360.0
