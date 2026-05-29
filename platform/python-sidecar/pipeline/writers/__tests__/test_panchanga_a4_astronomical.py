"""
Tests for A4-S6: emit_astronomical()
Native birth date: 1984-02-05, Bhubaneswar (lat=20.27, lon=85.84)
"""
import pytest
from datetime import datetime, timezone
from pipeline.writers.panchanga_writer_a4 import emit_astronomical, _GRAHAS

CHART_ID = "aaaaaaaa-0000-0000-0000-000000000006"
BUILD_ID = "test-build-a4-s6"
NATIVE_DATE = "1984-02-05"


class TestEmitAstronomical:
    def test_sunrise_native(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        sr_rows = [r for r in rows if r['fact_key'] == 'sunrise_iso']
        assert len(sr_rows) >= 1
        # Sunrise for Bhubaneswar should be ~06:00-07:00 IST (00:30-01:30 UTC)
        sr_val = sr_rows[0]['fact_value_text']
        sr_dt = datetime.fromisoformat(sr_val.replace('Z', '+00:00'))
        sr_utc_hour = sr_dt.utctimetuple().tm_hour
        assert 0 <= sr_utc_hour <= 2  # 00:00-02:00 UTC = 05:30-07:30 IST

    def test_graha_rise_set_9(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        subjects_with_rise = {
            r['fact_subject']
            for r in rows
            if 'GRAHA_RISE_SET' in r['fact_subject'] and r['fact_key'] == 'rise_iso'
        }
        assert len(subjects_with_rise) == 9

    def test_all_9_grahas_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for graha in _GRAHAS:
            subj = f"GRAHA_RISE_SET_{graha}"
            keys = {r['fact_key'] for r in rows if r['fact_subject'] == subj}
            assert 'rise_iso' in keys
            assert 'set_iso' in keys
            assert 'transit_iso' in keys

    def test_all_invariant_ayanamsha(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['ayanamsha_id'] == 'INVARIANT'

    def test_fact_category(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['fact_category'] == 'panchanga_astronomical'

    def test_sunset_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        ss_rows = [r for r in rows if r['fact_key'] == 'sunset_iso']
        assert len(ss_rows) >= 1

    def test_day_length_minutes_reasonable(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        dl = next(r for r in rows if r['fact_key'] == 'day_length_minutes')
        # February in Bhubaneswar: ~11-13 hrs = 660-780 min
        assert 600 <= dl['fact_value_num'] <= 840

    def test_night_length_plus_day_equals_1440(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        day = next(r for r in rows if r['fact_key'] == 'day_length_minutes')['fact_value_num']
        night = next(r for r in rows if r['fact_key'] == 'night_length_minutes')['fact_value_num']
        assert abs(day + night - 1440) < 0.01

    def test_solar_noon_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        noon_rows = [r for r in rows if r['fact_key'] == 'solar_noon_iso']
        assert len(noon_rows) >= 1

    def test_sun_altitude_at_birth_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        alt = next((r for r in rows if r['fact_key'] == 'sun_altitude_at_birth_deg'), None)
        assert alt is not None
        assert alt['fact_value_num'] is not None

    def test_sun_azimuth_at_birth_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        az = next((r for r in rows if r['fact_key'] == 'sun_azimuth_at_birth_deg'), None)
        assert az is not None
        assert az['fact_value_num'] is not None

    def test_moon_altitude_and_azimuth_present(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        moon_alt = next((r for r in rows if r['fact_key'] == 'moon_altitude_at_birth_deg'), None)
        moon_az  = next((r for r in rows if r['fact_key'] == 'moon_azimuth_at_birth_deg'), None)
        assert moon_alt is not None
        assert moon_az is not None

    def test_verification_pass_status_single(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['verification_pass_status'] == 'single'

    def test_fact_ids_unique(self):
        rows = emit_astronomical(CHART_ID, BUILD_ID, NATIVE_DATE)
        ids = [r['fact_id'] for r in rows]
        assert len(ids) == len(set(ids))

    def test_graha_list_is_9(self):
        assert len(_GRAHAS) == 9
        assert 'SUN' in _GRAHAS
        assert 'RAH' in _GRAHAS
        assert 'KET' in _GRAHAS
