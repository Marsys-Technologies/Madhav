"""
Tests for panchanga_writer_a4 — A4-S2: hora + choghadiya birth windows.

Native birth: 1984-02-05, 10:43 IST, Bhubaneswar (Sunday = weekday 0).
Sunrise ≈ 06:30 IST, Sunset ≈ 18:00 IST.

Hora calculation (Sunday, sunrise 06:30, birth 10:43):
  elapsed = 253 min → hora_num = int(253/60)+1 = 5
  Sunday sequence: [SUN, VEN, MER, MOO, SAT, JUP, MAR]
  index (5-1)%7 = 4 → SAT → ashubh
  day_or_night = 'day' (hora_num <= 12)

Choghadiya calculation (Sunday, sunrise 06:30, sunset 18:00, birth 10:43):
  day_secs = 41400s, segment_secs = 5175s (86.25 min)
  elapsed_secs = 15180s → seg_idx = int(15180/5175) = 2
  Sunday day sequence: [Udveg, Char, Labh, Amrit, Kaal, Shubh, Rog, Udveg]
  index 2 → Labh → lord=MER → shubh
"""
import uuid

import pytest

CHART_ID = str(uuid.uuid4())
BUILD_ID = "test-build-a4s2"
BIRTH_DATE = "1984-02-05"
BIRTH_TIME = "10:43"
SUNRISE_TIME = "06:30"
SUNSET_TIME = "18:00"
WEEKDAY = 0  # Sunday


def test_emit_hora_birth_returns_6_rows():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    assert len(rows) == 6


def test_emit_hora_birth_keys_present():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    keys = {r[10] for r in rows}  # fact_key is index 10 in _row tuple
    assert keys == {'hora_number', 'lord', 'day_or_night', 'classification', 'start_iso', 'end_iso'}


def test_emit_hora_birth_native_lord_is_saturn():
    """Sunday 10:43, sunrise 06:30 → hora 5 → lord=SAT."""
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    lord_row = next(r for r in rows if r[10] == 'lord')
    # fact_value_text is index 11
    assert lord_row[11] == 'SAT'


def test_emit_hora_birth_native_hora_number():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    num_row = next(r for r in rows if r[10] == 'hora_number')
    # fact_value_num is index 12
    assert num_row[12] == 5.0


def test_emit_hora_birth_native_classification():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    cls_row = next(r for r in rows if r[10] == 'classification')
    assert cls_row[11] == 'ashubh'  # SAT is ashubh


def test_emit_hora_birth_native_day_or_night():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    dn_row = next(r for r in rows if r[10] == 'day_or_night')
    assert dn_row[11] == 'day'


def test_emit_hora_birth_iso_fields_present():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    start_row = next(r for r in rows if r[10] == 'start_iso')
    end_row = next(r for r in rows if r[10] == 'end_iso')
    assert start_row[11].startswith('1984-02-05')
    assert end_row[11].startswith('1984-02-05')
    # start < end
    assert start_row[11] < end_row[11]


def test_emit_hora_birth_ayanamsha_invariant():
    from pipeline.writers.panchanga_writer_a4 import emit_hora_birth

    rows = emit_hora_birth(CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, WEEKDAY, BIRTH_DATE)
    for r in rows:
        assert r[2] == 'INVARIANT'  # ayanamsha_id index 2


def test_emit_choghadiya_birth_returns_6_rows():
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    assert len(rows) == 6


def test_emit_choghadiya_birth_keys_present():
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    keys = {r[10] for r in rows}
    assert keys == {'choghadiya_number', 'name', 'lord', 'classification', 'start_iso', 'end_iso'}


def test_emit_choghadiya_birth_native_name():
    """Sunday day chog seg_idx=2 → Labh."""
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    name_row = next(r for r in rows if r[10] == 'name')
    assert name_row[11] == 'Labh'


def test_emit_choghadiya_birth_native_lord():
    """Labh → lord=MER."""
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    lord_row = next(r for r in rows if r[10] == 'lord')
    assert lord_row[11] == 'MER'


def test_emit_choghadiya_birth_native_classification():
    """Labh → shubh."""
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    cls_row = next(r for r in rows if r[10] == 'classification')
    assert cls_row[11] == 'shubh'


def test_emit_choghadiya_birth_number_in_day_range():
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    num_row = next(r for r in rows if r[10] == 'choghadiya_number')
    assert 1 <= num_row[12] <= 8  # day choghadiya (1–8)


def test_emit_choghadiya_birth_iso_fields_present():
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    start_row = next(r for r in rows if r[10] == 'start_iso')
    end_row = next(r for r in rows if r[10] == 'end_iso')
    assert start_row[11].startswith('1984-02-05')
    assert end_row[11].startswith('1984-02-05')
    assert start_row[11] < end_row[11]


def test_emit_choghadiya_birth_ayanamsha_invariant():
    from pipeline.writers.panchanga_writer_a4 import emit_choghadiya_birth

    rows = emit_choghadiya_birth(
        CHART_ID, BUILD_ID, BIRTH_TIME, SUNRISE_TIME, SUNSET_TIME, WEEKDAY, BIRTH_DATE
    )
    for r in rows:
        assert r[2] == 'INVARIANT'
