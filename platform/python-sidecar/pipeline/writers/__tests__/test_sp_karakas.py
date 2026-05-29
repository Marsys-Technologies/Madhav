import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import (
    compute_chara_karakas,
    emit_karakas,
    emit_karakamsa,
    emit_swamsa,
)

# Native chart planet longitudes (1984-02-05, Lahiri/Chitrapaksha)
NATIVE_GRAHA_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0,  'VEN': 262.0, 'SAT': 215.0, 'KET': 338.0, 'RAH': 158.0,
}


def test_karakas_8_per_school():
    rows = emit_karakas(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    subjects = {r['fact_subject'] for r in rows}
    # Each school emits 8 karakas → 16 unique subjects across both schools
    assert len(subjects) >= 8


def test_karakas_16_subjects_two_schools():
    rows = emit_karakas(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    subjects = {r['fact_subject'] for r in rows}
    parashari = [s for s in subjects if 'PARASHARI_7K' in s]
    rao = [s for s in subjects if 'RAO_8K' in s]
    assert len(parashari) == 8
    assert len(rao) == 8


def test_swamsa_12_rows():
    rows = emit_swamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 48.0)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 12
    for i in range(1, 13):
        assert f'SWAMSA_HOUSE_{i}' in subjects


def test_all_two_pass():
    rows = emit_karakas(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_karakamsa_two_pass():
    rows = emit_karakamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_swamsa_two_pass():
    rows = emit_swamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 48.0)
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified'


def test_atmakaraka_is_highest_degree_within_sign():
    """
    Atmakaraka is the planet with highest degree within sign (Jaimini rule).
    Verify compute_chara_karakas assigns AK correctly.
    With NATIVE_GRAHA_LONS:
      SUN 301.5 → 301.5%30 = 1.5°
      MOO 320.5 → 320.5%30 = 20.5°
      MAR 181.0 → 181.0%30 = 1.0°
      MER 298.0 → 298.0%30 = 28.0°  ← highest
      JUP  57.0 →  57.0%30 = 27.0°
      VEN 262.0 → 262.0%30 = 22.0°
      SAT 215.0 → 215.0%30 = 5.0°
      KET 338.0 → 338.0%30 = 8.0°
    MER (28.0°) is the highest → AK = MER (Parashari 7K without Rahu)
    """
    karakas = compute_chara_karakas(NATIVE_GRAHA_LONS, include_rahu=False)
    ak_name, ak_graha, ak_deg = karakas[0]
    assert ak_name == 'ATMAKARAKA'
    assert ak_graha == 'MER'


def test_karakamsa_has_three_fact_keys():
    rows = emit_karakamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    keys = {r['fact_key'] for r in rows}
    assert keys == {'sign', 'ak_graha', 'formula_id'}


def test_karakamsa_category():
    rows = emit_karakamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', NATIVE_GRAHA_LONS)
    for r in rows:
        assert r['fact_category'] == 'karakamsa_position'
        assert r['fact_subject'] == 'KARAKAMSA'


def test_swamsa_house_numbers_sequential():
    rows = emit_swamsa(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha', 60.0)
    house_rows = [r for r in rows if r['fact_key'] == 'house_number']
    nums = sorted(int(r['fact_value_num']) for r in house_rows)
    assert nums == list(range(1, 13))
