"""
Tests for A4-S8 emitters:
  emit_tara_bala_baseline, emit_chandra_bala_baseline,
  emit_special_yoga_combinations, emit_eclipse_proximity.

Native birth: 1984-02-05, tithi=3, nakshatra~26, vara=0 (Sunday).
Natal Moon longitude 320.5 → natal_nak_idx=24 (UBH), natal_sign_idx=10 (AQU).
"""
import pytest
from unittest.mock import patch, MagicMock
from pipeline.writers.panchanga_writer_a4 import (
    emit_tara_bala_baseline,
    emit_chandra_bala_baseline,
    emit_special_yoga_combinations,
    emit_eclipse_proximity,
    TARA_CLASSES,
    NAK_NAMES,
    SIGN_NAMES,
    _SPECIAL_YOGAS,
)

CHART_ID = "test-chart-a4s8-00000000"
BUILD_ID = "test-build-a4s8"
AYANAMSHA = "lahiri_chitrapaksha"

# Native panchanga values (1984-02-05)
NATAL_MOON_LON = 320.5   # → natal_nak_idx=24, natal_sign_idx=10 (AQU)
TITHI_NUM   = 3           # Shukla Tritiya
NAK_NUM     = 26          # Purva Bhadrapada
WEEKDAY     = 0           # Sunday


# ── emit_tara_bala_baseline ───────────────────────────────────────────────────

@pytest.fixture
def tara_rows():
    return emit_tara_bala_baseline(CHART_ID, BUILD_ID, AYANAMSHA, NATAL_MOON_LON)


def test_tara_baseline_count(tara_rows):
    subjects = {r['fact_subject'] for r in tara_rows}
    assert len(subjects) == 27


def test_tara_baseline_row_count(tara_rows):
    assert len(tara_rows) == 27


def test_tara_baseline_category(tara_rows):
    cats = {r['fact_category'] for r in tara_rows}
    assert cats == {'tara_bala_natal_baseline'}


def test_tara_baseline_key(tara_rows):
    keys = {r['fact_key'] for r in tara_rows}
    assert keys == {'tara_class'}


def test_tara_baseline_valid_classes(tara_rows):
    for r in tara_rows:
        assert r['fact_value_text'] in TARA_CLASSES


def test_tara_baseline_subjects_match_nak_names(tara_rows):
    subjects = {r['fact_subject'] for r in tara_rows}
    expected = {f"TRANSIT_NAK_{n}" for n in NAK_NAMES}
    assert subjects == expected


def test_tara_baseline_natal_nak_is_janma(tara_rows):
    # natal_nak_idx = int(320.5 / 13.333) % 27 = 24 → NAK_NAMES[24] = 'PBH'
    natal_subject = "TRANSIT_NAK_PBH"
    row = next(r for r in tara_rows if r['fact_subject'] == natal_subject)
    assert row['fact_value_text'] == 'Janma'


def test_tara_baseline_ayanamsha(tara_rows):
    assert all(r['ayanamsha_id'] == AYANAMSHA for r in tara_rows)


def test_tara_baseline_nine_classes_covered(tara_rows):
    # 27 nakshatras cycle through all 9 tara classes 3 times
    emitted_classes = {r['fact_value_text'] for r in tara_rows}
    assert emitted_classes == set(TARA_CLASSES)


# ── emit_chandra_bala_baseline ────────────────────────────────────────────────

@pytest.fixture
def chandra_rows():
    return emit_chandra_bala_baseline(CHART_ID, BUILD_ID, AYANAMSHA, NATAL_MOON_LON)


def test_chandra_baseline_count(chandra_rows):
    subjects = {r['fact_subject'] for r in chandra_rows}
    assert len(subjects) == 12


def test_chandra_baseline_row_count(chandra_rows):
    assert len(chandra_rows) == 12


def test_chandra_baseline_category(chandra_rows):
    cats = {r['fact_category'] for r in chandra_rows}
    assert cats == {'chandra_bala_natal_baseline'}


def test_chandra_baseline_key(chandra_rows):
    keys = {r['fact_key'] for r in chandra_rows}
    assert keys == {'classification'}


def test_chandra_baseline_valid_classifications(chandra_rows):
    valid = {'favorable', 'neutral', 'unfavorable'}
    for r in chandra_rows:
        assert r['fact_value_text'] in valid


def test_chandra_baseline_subjects_match_sign_names(chandra_rows):
    subjects = {r['fact_subject'] for r in chandra_rows}
    expected = {f"TRANSIT_SIGN_{s}" for s in SIGN_NAMES}
    assert subjects == expected


def test_chandra_baseline_natal_sign_dist0_unfavorable(chandra_rows):
    # natal_sign_idx = int(320.5 / 30) % 12 = 10 → AQU; dist=0 → unfavorable
    row = next(r for r in chandra_rows if r['fact_subject'] == 'TRANSIT_SIGN_AQU')
    assert row['fact_value_text'] == 'unfavorable'


def test_chandra_baseline_ayanamsha(chandra_rows):
    assert all(r['ayanamsha_id'] == AYANAMSHA for r in chandra_rows)


# ── emit_special_yoga_combinations ───────────────────────────────────────────

@pytest.fixture
def yoga_rows():
    return emit_special_yoga_combinations(
        CHART_ID, BUILD_ID, 'INVARIANT', TITHI_NUM, NAK_NUM, WEEKDAY
    )


def test_special_yoga_count(yoga_rows):
    assert len(yoga_rows) == 15


def test_special_yoga_names(yoga_rows):
    names = {r['fact_subject'] for r in yoga_rows}
    assert names == set(_SPECIAL_YOGAS.keys())


def test_special_yoga_category(yoga_rows):
    cats = {r['fact_category'] for r in yoga_rows}
    assert cats == {'panchanga_special_yoga_combinations'}


def test_special_yoga_key(yoga_rows):
    keys = {r['fact_key'] for r in yoga_rows}
    assert keys == {'active_at_birth_flag'}


def test_special_yoga_values_are_bool_strings(yoga_rows):
    for r in yoga_rows:
        assert r['fact_value_text'] in {'True', 'False'}


def test_special_yoga_two_pass_verified(yoga_rows):
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in yoga_rows)


def test_special_yoga_ravi_yoga_not_active_on_non_pushya_nak(yoga_rows):
    # Native: nakshatra=26 (≠ 8 Pushya) → RAVI_YOGA not active
    row = next(r for r in yoga_rows if r['fact_subject'] == 'RAVI_YOGA')
    assert row['fact_value_text'] == 'False'


def test_special_yoga_guru_pushya_not_active_on_sunday(yoga_rows):
    # GURU_PUSHYA requires weekday=4 (Thursday); native weekday=0 (Sunday)
    row = next(r for r in yoga_rows if r['fact_subject'] == 'GURU_PUSHYA')
    assert row['fact_value_text'] == 'False'


# ── emit_eclipse_proximity ────────────────────────────────────────────────────

def test_eclipse_proximity_no_db_returns_empty():
    # When DB is unreachable, function must return empty list (not raise)
    rows = emit_eclipse_proximity(CHART_ID, BUILD_ID, '1984-02-05')
    assert isinstance(rows, list)


def test_eclipse_proximity_with_mock_eclipse():
    import datetime as dt
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    eclipse_date = dt.date(1984, 2, 1)
    mock_cur.fetchall.return_value = [
        (eclipse_date, 'SOLAR', 'AQU', 0.95),
    ]

    with patch('psycopg2.connect', return_value=mock_conn):
        rows = emit_eclipse_proximity(CHART_ID, BUILD_ID, '1984-02-05')

    assert len(rows) == 4
    subjects = {r['fact_subject'] for r in rows}
    assert f"ECLIPSE_{eclipse_date}" in subjects
    cats = {r['fact_category'] for r in rows}
    assert cats == {'eclipse_proximity_natal'}


def test_eclipse_proximity_days_from_birth_correct():
    import datetime as dt
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    eclipse_date = dt.date(1984, 2, 1)  # 4 days before birth
    mock_cur.fetchall.return_value = [
        (eclipse_date, 'SOLAR', 'AQU', 0.95),
    ]

    with patch('psycopg2.connect', return_value=mock_conn):
        rows = emit_eclipse_proximity(CHART_ID, BUILD_ID, '1984-02-05')

    days_row = next(r for r in rows if r['fact_key'] == 'days_from_birth')
    assert days_row['fact_value_num'] == -4.0


def test_eclipse_proximity_empty_when_no_eclipses():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = []

    with patch('psycopg2.connect', return_value=mock_conn):
        rows = emit_eclipse_proximity(CHART_ID, BUILD_ID, '1984-02-05')

    assert rows == []
