import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import emit_midpoints, _midpoint

GRAHA_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0,  'VEN': 262.0, 'SAT': 215.0, 'RAH': 158.0, 'KET': 338.0,
}


def test_midpoint_count_54():
    rows = emit_midpoints(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
                          GRAHA_LONS, 48.0, 318.0)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 54, f"Expected 54, got {len(subjects)}"


def test_shorter_arc():
    mid = _midpoint(10, 350)  # shorter arc should give 0° not 180°
    assert mid == 0.0 or abs(mid) < 1.0 or abs(mid - 360) < 1.0


def test_mc_estimate_when_none():
    rows = emit_midpoints(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
                          GRAHA_LONS, 48.0)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 54


def test_rows_per_subject():
    rows = emit_midpoints(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
                          GRAHA_LONS, 48.0, 318.0)
    from collections import Counter
    counts = Counter(r['fact_subject'] for r in rows)
    assert all(v == 12 for v in counts.values()), f"Expected 12 keys per subject: {counts}"


def test_verification_pass_status_single():
    rows = emit_midpoints(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
                          GRAHA_LONS, 48.0, 318.0)
    assert all(r['verification_pass_status'] == 'single' for r in rows)


def test_cross_ayanamsha_divergence_zero():
    rows = emit_midpoints(str(uuid.uuid4()), str(uuid.uuid4()), 'lahiri_chitrapaksha',
                          GRAHA_LONS, 48.0, 318.0)
    divs = [r for r in rows if r['fact_key'] == 'cross_ayanamsha_divergence_arcsec']
    assert all(r['fact_value_num'] == 0.0 for r in divs)
