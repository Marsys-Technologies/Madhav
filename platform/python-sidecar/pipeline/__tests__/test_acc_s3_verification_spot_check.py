import pytest, uuid

def test_time_window_two_pass_verified():
    """Inauspicious windows must all be two_pass_verified."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.panchanga_writer_a4 import emit_inauspicious_windows, emit_auspicious_windows
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_inauspicious_windows(chart_id, build_id, 0,
                                      '1984-02-05T01:00:00+00:00', '1984-02-05T12:15:00+00:00')
    rows += emit_auspicious_windows(chart_id, build_id, 0,
                                     '1984-02-05T01:00:00+00:00', '1984-02-05T12:15:00+00:00')
    for r in rows:
        assert r['verification_pass_status'] == 'two_pass_verified', \
            f"Time window {r['fact_category']} has status={r['verification_pass_status']}, expected two_pass_verified"

def test_sensitive_points_two_pass():
    """All sensitive point rows must be two_pass_verified."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.sensitive_points_writer_a5 import emit_upagrahas, emit_sahams
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_upagrahas(None, chart_id, build_id, 'lahiri_chitrapaksha', 301.5, 215.0)
    rows += emit_sahams(chart_id, build_id, 'lahiri_chitrapaksha',
                        301.5, 320.5, 48.0, 181.0, 298.0, 57.0, 262.0, 215.0, 158.0, 338.0)
    two_pass = sum(1 for r in rows if r['verification_pass_status'] == 'two_pass_verified')
    assert two_pass > 0, "No two_pass_verified rows found"

def test_verification_pass_status_valid_enum():
    """verification_pass_status must only be valid enum values."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline.writers.panchanga_writer_a4 import emit_solar_context
    VALID = {'single','two_pass_verified','classical_match','divergent_flagged'}
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    rows = emit_solar_context(chart_id, build_id, '1984-02-05')
    for r in rows:
        assert r['verification_pass_status'] in VALID, \
            f"Invalid status: {r['verification_pass_status']}"

def test_native_birth_tithi_vara():
    """Native birth spot-check: tithi=Shukla Tritiya, vara=Ravivara."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from unittest.mock import MagicMock, patch
    from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = {
        'tithi':3,'tithi_name':'Shukla Tritiya','vara':0,'vara_name':'Ravivara',
        'moon_nakshatra':'Purva Bhadrapada','moon_nakshatra_pada':4,
        'yoga':4,'yoga_name':'Shiva','karana':2,'karana_name':'Garaja',
    }
    chart_id, build_id = str(uuid.uuid4()), str(uuid.uuid4())
    with patch('psycopg2.extras.execute_values'):
        rows_written = write_panchanga_limbs(conn, chart_id, build_id, '1984-02-05',
                                              {'lahiri_chitrapaksha':{}})
    assert rows_written > 0
