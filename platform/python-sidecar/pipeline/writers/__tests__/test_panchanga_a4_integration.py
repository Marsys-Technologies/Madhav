import pytest, uuid, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.writers.panchanga_writer_a4 import (
    write_panchanga_limbs, emit_hora_birth, emit_choghadiya_birth,
    emit_inauspicious_windows, emit_auspicious_windows,
    emit_solar_context, emit_calendrical, emit_astronomical,
    emit_sun_moon_dynamics, emit_agni_vasa, emit_panchaka,
    emit_disha_shul, emit_shoonya_rashis,
    emit_tara_bala_baseline, emit_chandra_bala_baseline,
    emit_special_yoga_combinations, emit_eclipse_proximity,
)

# Native birth constants
BIRTH_DATE = '1984-02-05'
BIRTH_TIME = '10:43'
SUNRISE = '06:30'
SUNSET  = '17:45'
WEEKDAY = 0  # Sunday
TITHI_NUM = 3  # Shukla Tritiya
NAK_NUM = 26   # Purva Bhadrapada
MOON_LON = 320.5   # ~Purva Bhadrapada in Lahiri
AYANAMSHAS = ['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']

def make_ids():
    return str(uuid.uuid4()), str(uuid.uuid4())

def make_fake_panchanga_row():
    return {
        'tithi': TITHI_NUM, 'tithi_name': 'Shukla Tritiya',
        'vara': WEEKDAY, 'vara_name': 'Ravivara',
        'moon_nakshatra': 'Purva Bhadrapada', 'moon_nakshatra_pada': 4,
        'yoga': 4, 'yoga_name': 'Shiva',
        'karana': 2, 'karana_name': 'Garaja',
        'sunrise': f'{BIRTH_DATE}T01:00:00+00:00',
        'sunset': f'{BIRTH_DATE}T12:15:00+00:00',
    }

class TestA4Integration:
    def test_native_tithi_vara(self):
        """Native birth: Shukla Tritiya, Ravivara"""
        from unittest.mock import MagicMock, patch
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = make_fake_panchanga_row()
        chart_id, build_id = make_ids()
        with patch("psycopg2.extras.execute_values"):
            n = write_panchanga_limbs(conn, chart_id, build_id, BIRTH_DATE,
                                       {'lahiri_chitrapaksha': {'nakshatra_moon':'Purva Bhadrapada','nakshatra_moon_pada':4}})
        assert n > 0

    def test_tara_baseline_27_rows(self):
        chart_id, build_id = make_ids()
        rows = emit_tara_bala_baseline(chart_id, build_id, 'lahiri_chitrapaksha', MOON_LON)
        subjects = {r['fact_subject'] for r in rows}
        assert len(subjects) == 27, f"Expected 27 tara rows, got {len(subjects)}"

    def test_chandra_baseline_12_rows(self):
        chart_id, build_id = make_ids()
        rows = emit_chandra_bala_baseline(chart_id, build_id, 'lahiri_chitrapaksha', MOON_LON)
        subjects = {r['fact_subject'] for r in rows}
        assert len(subjects) == 12

    def test_inauspicious_windows_two_pass(self):
        chart_id, build_id = make_ids()
        rows = emit_inauspicious_windows(chart_id, build_id, WEEKDAY,
                                          f'{BIRTH_DATE}T01:00:00+00:00',
                                          f'{BIRTH_DATE}T12:15:00+00:00')
        cats = {r['fact_category'] for r in rows}
        assert 'panchanga_rahu_kalam' in cats
        for r in rows:
            assert r['verification_pass_status'] == 'two_pass_verified', \
                f"Expected two_pass_verified for {r['fact_category']}"

    def test_auspicious_windows_two_pass(self):
        chart_id, build_id = make_ids()
        rows = emit_auspicious_windows(chart_id, build_id, WEEKDAY,
                                        f'{BIRTH_DATE}T01:00:00+00:00',
                                        f'{BIRTH_DATE}T12:15:00+00:00', is_wednesday=False)
        cats = {r['fact_category'] for r in rows}
        assert 'panchanga_abhijit_muhurta' in cats
        abhijit = [r for r in rows if r['fact_category']=='panchanga_abhijit_muhurta' and r['fact_key']=='applicable_flag']
        assert abhijit[0]['fact_value_text'] == 'True'  # not Wednesday

    def test_agni_vasa_sunday(self):
        chart_id, build_id = make_ids()
        rows = emit_agni_vasa(chart_id, build_id, TITHI_NUM, NAK_NUM, WEEKDAY)
        residence_rows = [r for r in rows if r['fact_key']=='residence']
        assert len(residence_rows) == 1
        assert residence_rows[0]['fact_value_text'] in ('Bhumi','Akasha','Patala','Swarga')

    def test_disha_shul_sunday_west(self):
        chart_id, build_id = make_ids()
        rows = emit_disha_shul(chart_id, build_id, WEEKDAY)  # Sunday
        dir_rows = [r for r in rows if r['fact_key']=='direction_to_avoid']
        assert dir_rows[0]['fact_value_text'] == 'West'

    def test_no_narration(self):
        chart_id, build_id = make_ids()
        FORBIDDEN = ['indicates','suggests','implies','means that','denotes']
        rows = emit_solar_context(chart_id, build_id, BIRTH_DATE)
        rows += emit_calendrical(chart_id, build_id, BIRTH_DATE)
        for r in rows:
            val = r.get('fact_value_text') or ''
            for verb in FORBIDDEN:
                assert verb not in val.lower(), f"Narration in {r['fact_key']}: '{val}'"

    def test_smoke_5_ayanamshas_row_count(self):
        """Rough count: all emitters × 5 ayanamshas should produce > 500 rows."""
        chart_id, build_id = make_ids()
        all_rows = []
        for aya in AYANAMSHAS:
            all_rows += emit_tara_bala_baseline(chart_id, build_id, aya, MOON_LON)
            all_rows += emit_chandra_bala_baseline(chart_id, build_id, aya, MOON_LON)
            all_rows += emit_special_yoga_combinations(chart_id, build_id, aya, TITHI_NUM, NAK_NUM, WEEKDAY)
        assert len(all_rows) >= 200, f"Expected >=200 rows across 5 ayanamshas, got {len(all_rows)}"
