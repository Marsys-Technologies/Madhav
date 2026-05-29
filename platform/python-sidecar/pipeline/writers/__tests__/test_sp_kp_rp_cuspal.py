import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import (
    emit_kp_ruling_planets, emit_kp_cuspal_significators,
    _kp_star_lord, _kp_sub_lord,
)

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())


def test_kp_rp_5_entries():
    rows = emit_kp_ruling_planets(CHART_ID, BUILD_ID, 'krishnamurti', 48.0, 320.5, 0)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) >= 5, f"Expected >= 5 subjects, got {len(subjects)}: {subjects}"


def test_kp_rp_expected_subjects():
    rows = emit_kp_ruling_planets(CHART_ID, BUILD_ID, 'krishnamurti', 48.0, 320.5, 0)
    subjects = {r['fact_subject'] for r in rows}
    for expected in ('RP_ASC_LORD', 'RP_ASC_SUB_LORD', 'RP_MOON_SIGN_LORD', 'RP_MOON_STAR_LORD', 'RP_DAY_LORD'):
        assert expected in subjects, f"Missing subject: {expected}"


def test_kp_rp_ayanamsha_stored():
    rows = emit_kp_ruling_planets(CHART_ID, BUILD_ID, 'krishnamurti', 48.0, 320.5, 0)
    assert all(r['ayanamsha_id'] == 'krishnamurti' for r in rows)


def test_kp_rp_verification_pass_status():
    rows = emit_kp_ruling_planets(CHART_ID, BUILD_ID, 'krishnamurti', 48.0, 320.5, 0)
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_kp_cuspal_12_cusps():
    cusps = [48.0 + i * 30 for i in range(12)]
    rows = emit_kp_cuspal_significators(CHART_ID, BUILD_ID, 'krishnamurti', cusps)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 12, f"Expected 12 cusps, got {len(subjects)}"


def test_kp_cuspal_subject_names():
    cusps = [48.0 + i * 30 for i in range(12)]
    rows = emit_kp_cuspal_significators(CHART_ID, BUILD_ID, 'krishnamurti', cusps)
    subjects = {r['fact_subject'] for r in rows}
    for i in range(1, 13):
        assert f"CUSP_{i}" in subjects


def test_kp_cuspal_keys_per_cusp():
    cusps = [48.0 + i * 30 for i in range(12)]
    rows = emit_kp_cuspal_significators(CHART_ID, BUILD_ID, 'krishnamurti', cusps)
    from collections import Counter
    keys_per_subject = {}
    for r in rows:
        keys_per_subject.setdefault(r['fact_subject'], set()).add(r['fact_key'])
    for subj, keys in keys_per_subject.items():
        assert {'lord', 'star_lord', 'sub_lord'}.issubset(keys), f"{subj} missing required keys: {keys}"


def test_kp_cuspal_verification_pass_status():
    cusps = [48.0 + i * 30 for i in range(12)]
    rows = emit_kp_cuspal_significators(CHART_ID, BUILD_ID, 'krishnamurti', cusps)
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_kp_cuspal_longitude_stored():
    cusps = [48.0 + i * 30 for i in range(12)]
    rows = emit_kp_cuspal_significators(CHART_ID, BUILD_ID, 'krishnamurti', cusps)
    lon_rows = [r for r in rows if r['fact_key'] == 'cusp_longitude']
    assert len(lon_rows) == 12
    assert all(r['fact_value_num'] is not None for r in lon_rows)


def test_kp_sub_lord_returns_valid_graha():
    valid = {'KET', 'VEN', 'SUN', 'MOO', 'MAR', 'RAH', 'JUP', 'SAT', 'MER'}
    for lon in [0.0, 45.0, 90.5, 180.0, 270.33, 359.99]:
        assert _kp_sub_lord(lon) in valid, f"Invalid sub-lord for lon={lon}"


def test_kp_star_lord_returns_valid_graha():
    valid = {'KET', 'VEN', 'SUN', 'MOO', 'MAR', 'RAH', 'JUP', 'SAT', 'MER'}
    for lon in [0.0, 13.5, 27.0, 100.0, 240.0, 359.0]:
        assert _kp_star_lord(lon) in valid, f"Invalid star-lord for lon={lon}"
