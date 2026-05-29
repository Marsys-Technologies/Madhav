import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import (
    emit_tajik_hadda,
    emit_tajik_triraashipathi,
    emit_tajik_vargottama,
    HADDA_TABLE,
    SIGNS,
)

CHART_ID = str(uuid.uuid4())
BUILD_ID = str(uuid.uuid4())
AY = 'lahiri_chitrapaksha'

GRAHA_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0,  'VEN': 262.0, 'SAT': 215.0, 'RAH': 158.0, 'KET': 338.0,
}


def test_hadda_60_zones():
    rows = emit_tajik_hadda(CHART_ID, BUILD_ID, AY, GRAHA_LONS, 48.0)
    subjects = {r['fact_subject'] for r in rows}
    assert len(subjects) == 60, f"Expected 60 subjects, got {len(subjects)}"
    assert 'HADDA_1' in subjects
    assert 'HADDA_60' in subjects


def test_hadda_table_structure():
    total_zones = sum(len(v) for v in HADDA_TABLE.values())
    assert total_zones == 60
    assert set(HADDA_TABLE.keys()) == set(SIGNS)


def test_hadda_all_two_pass_verified():
    rows = emit_tajik_hadda(CHART_ID, BUILD_ID, AY, GRAHA_LONS, 48.0)
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_hadda_keys_per_zone():
    rows = emit_tajik_hadda(CHART_ID, BUILD_ID, AY, GRAHA_LONS, 48.0)
    from collections import Counter
    counts = Counter(r['fact_subject'] for r in rows)
    assert all(v == 5 for v in counts.values()), f"Expected 5 keys per zone: {counts}"


def test_triraashipathi_returns_rows():
    rows = emit_tajik_triraashipathi(CHART_ID, BUILD_ID, AY, 48.0, 301.5)
    assert len(rows) == 2
    lords = {r['fact_key']: r['fact_value_text'] for r in rows}
    assert 'lord' in lords
    assert lords['lord'] in ('MAR', 'VEN', 'MER', 'MOO', 'SUN', 'JUP', 'SAT')


def test_triraashipathi_two_pass_verified():
    rows = emit_tajik_triraashipathi(CHART_ID, BUILD_ID, AY, 48.0, 57.0)
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_vargottama_returns_rows():
    rows = emit_tajik_vargottama(CHART_ID, BUILD_ID, AY, 48.0)
    assert len(rows) == 3
    subjects = {r['fact_subject'] for r in rows}
    assert subjects == {'TAJIK_VARGOTTAMA'}


def test_vargottama_two_pass_verified():
    rows = emit_tajik_vargottama(CHART_ID, BUILD_ID, AY, 48.0)
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_all_three_two_pass_verified():
    rows = (
        emit_tajik_hadda(CHART_ID, BUILD_ID, AY, GRAHA_LONS, 48.0)
        + emit_tajik_triraashipathi(CHART_ID, BUILD_ID, AY, 48.0, 301.5)
        + emit_tajik_vargottama(CHART_ID, BUILD_ID, AY, 48.0)
    )
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in rows)


def test_hadda_fact_category():
    rows = emit_tajik_hadda(CHART_ID, BUILD_ID, AY, GRAHA_LONS, 48.0)
    assert all(r['fact_category'] == 'tajik_hadda_lord' for r in rows)
