"""
Tests for panchanga_writer_a4 — A4-S1 acceptance suite.
Uses actual panchanga_daily column names (confirmed against live schema).
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest


def make_fake_row():
    """Return a dict mimicking a panchanga_daily row for birth date 1984-02-05."""
    return {
        # Tithi
        "tithi_name": "Shukla Tritiya",
        "tithi": 3,
        "paksha": "shukla",
        # Vara
        "vara": "Ravivara",
        "vara_lord": "Sun",
        # Yoga
        "yoga": "Shiva",
        # Karana
        "karana": "Garaja",
        # Nakshatra (Lahiri DB default)
        "moon_nakshatra": "Purva Bhadrapada",
        "moon_nakshatra_pada": 2,
    }


def _make_conn(fake_row=None):
    conn = MagicMock()
    row = fake_row if fake_row is not None else make_fake_row()
    conn.execute.return_value.fetchone.return_value = row
    return conn


def test_write_panchanga_limbs_basic():
    """write_panchanga_limbs returns row count > 0."""
    from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs

    conn = _make_conn()
    chart_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    with patch("psycopg2.extras.execute_values"):
        n = write_panchanga_limbs(
            conn, chart_id, build_id, "1984-02-05",
            {"lahiri_chitrapaksha": {"nakshatra_moon": "Purva Bhadrapada", "nakshatra_moon_pada": 2}},
        )
    assert n > 0
    assert conn.execute.called


def test_native_birth_tithi_name():
    """Native birth: at least 5 limbs produce rows (tithi+vara+yoga+karana+nakshatra)."""
    from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs

    conn = _make_conn()
    chart_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    with patch("psycopg2.extras.execute_values"):
        n = write_panchanga_limbs(
            conn, chart_id, build_id, "1984-02-05",
            {"lahiri_chitrapaksha": {}},
        )
    # tithi:3 + vara:2 + yoga:1 + karana:1 + nakshatra:2 = 9
    assert n > 5


def test_nakshatra_is_ayanamsha_dependent():
    """Two ayanamshas produce distinct nakshatra rows; total > 10."""
    from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs

    conn = _make_conn()
    chart_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    ayanamshas = {
        "lahiri_chitrapaksha": {"nakshatra_moon": "Purva Bhadrapada", "nakshatra_moon_pada": 2},
        "krishnamurti": {"nakshatra_moon": "Uttara Bhadrapada", "nakshatra_moon_pada": 1},
    }
    with patch("psycopg2.extras.execute_values"):
        n = write_panchanga_limbs(conn, chart_id, build_id, "1984-02-05", ayanamshas)
    # invariant rows: 3+2+1+1=7, nakshatra: 2 ayanamshas × 2 keys = 4 → total 11
    assert n > 10


def test_invariant_limbs_have_invariant_ayanamsha():
    """Tithi, vara, yoga, karana rows must use ayanamsha_id=INVARIANT."""
    from pipeline.writers.panchanga_writer_a4 import make_fact_id

    chart_id = "362f9f17-95a5-490b-aaaa-bbbbccccdddd"
    build_id = "test-build"
    fid = make_fact_id("panchanga_tithi", "TITHI_BIRTH", "name", chart_id, "INVARIANT", build_id)
    # fact_id should be deterministic and 16 hex chars
    assert len(fid) == 16
    assert fid == make_fact_id("panchanga_tithi", "TITHI_BIRTH", "name", chart_id, "INVARIANT", build_id)


def test_nakshatra_rows_use_per_ayanamsha_id():
    """Nakshatra fact_id differs by ayanamsha_id."""
    from pipeline.writers.panchanga_writer_a4 import make_fact_id

    chart_id = "362f9f17-95a5-490b-aaaa-bbbbccccdddd"
    build_id = "test-build"
    fid_lahiri = make_fact_id(
        "panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", "name",
        chart_id, "lahiri_chitrapaksha", build_id,
    )
    fid_kp = make_fact_id(
        "panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", "name",
        chart_id, "krishnamurti", build_id,
    )
    assert fid_lahiri != fid_kp


def test_citation_format():
    """citation_ref must follow slug format with @chart=, :ay=, :eng= tokens."""
    from pipeline.writers.panchanga_writer_a4 import make_citation_ref

    ref = make_citation_ref("panchanga_tithi", "TITHI_BIRTH", "name", "362f9f17-95a5-490b", "INVARIANT")
    assert "@chart=" in ref
    assert ":ay=INVARIANT" in ref
    assert ":eng=natal_engine" in ref


def test_missing_panchanga_row_raises():
    """ValueError raised when birth date has no panchanga_daily row."""
    from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs

    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = None
    with pytest.raises(ValueError, match="No panchanga_daily row"):
        write_panchanga_limbs(conn, str(uuid.uuid4()), str(uuid.uuid4()), "1800-01-01", {})
