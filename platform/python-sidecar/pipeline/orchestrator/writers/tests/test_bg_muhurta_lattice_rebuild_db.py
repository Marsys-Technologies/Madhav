"""Real-Postgres regression for repairing legacy full-day aṅga atoms."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import psycopg
import pytest

from pipeline.orchestrator.writers.bg_muhurta_lattice import BgMuhurtaLatticeWriter


TEST_DB_URL = os.environ.get("NIRMANA_MUHURTA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DB_URL, reason="NIRMANA_MUHURTA_TEST_DATABASE_URL not set")


@pytest.fixture()
def db_conn():
    parsed = urlparse(TEST_DB_URL or "")
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.path != "/nirmana_muhurta_test":
        raise RuntimeError(
            "NIRMANA_MUHURTA_TEST_DATABASE_URL must point to the exact local "
            "nirmana_muhurta_test database"
        )
    conn = psycopg.connect(TEST_DB_URL, row_factory=psycopg.rows.dict_row)
    conn.execute("""
        DROP TABLE IF EXISTS bg_muhurta_lattice CASCADE;
        CREATE TABLE bg_muhurta_lattice (
          factor_family text NOT NULL,
          factor_key text NOT NULL,
          start_utc timestamptz NOT NULL,
          end_utc timestamptz NOT NULL,
          detail jsonb NOT NULL,
          reference_lat double precision NOT NULL,
          reference_lon double precision NOT NULL,
          reference_tz_offset_minutes integer NOT NULL,
          reference_location_key text NOT NULL,
          ayanamsha_key text NOT NULL,
          sampling_method text NOT NULL,
          source_citation text NOT NULL,
          corpus_status text NOT NULL,
          build_id uuid NOT NULL,
          computed_at timestamptz NOT NULL,
          UNIQUE (factor_family, factor_key, start_utc)
        );
    """)
    conn.commit()
    yield conn
    conn.execute("DROP TABLE IF EXISTS bg_muhurta_lattice CASCADE")
    conn.commit()
    conn.close()


def _batch_row(key: str, start: datetime, end: datetime, detail: dict, build_id: str):
    return {
        "factor_family": "tithi",
        "factor_key": key,
        "start_utc": start,
        "end_utc": end,
        "detail": json.dumps(detail),
        "reference_lat": 20.27,
        "reference_lon": 85.84,
        "reference_tz_offset_minutes": 330,
        "reference_location_key": "bhubaneswar",
        "ayanamsha_key": "lahiri",
        "sampling_method": "muhurta_lattice_test_v2",
        "source_citation": "test citation",
        "corpus_status": "computed_cited",
        "build_id": build_id,
    }


def test_rebuild_shortens_legacy_full_day_atom_without_overlap(db_conn):
    sunrise = datetime(2026, 8, 14, 23, 56, 14, tzinfo=timezone.utc)
    boundary = datetime(2026, 8, 15, 11, 59, 24, tzinfo=timezone.utc)
    next_sunrise = datetime(2026, 8, 15, 23, 56, 32, tzinfo=timezone.utc)
    build_id = str(uuid.uuid4())

    legacy = _batch_row(
        "shukla_tritiya", sunrise, next_sunrise,
        {"factor_id": 3, "span_convention": "hindu_day_sunrise_to_next_sunrise_anga_at_sunrise"},
        str(uuid.uuid4()),
    )
    with db_conn.cursor() as cur:
        cur.execute(
            """INSERT INTO bg_muhurta_lattice
              (factor_family, factor_key, start_utc, end_utc, detail,
               reference_lat, reference_lon, reference_tz_offset_minutes,
               reference_location_key, ayanamsha_key, sampling_method,
               source_citation, corpus_status, build_id, computed_at)
              VALUES
              (%(factor_family)s, %(factor_key)s, %(start_utc)s, %(end_utc)s,
               %(detail)s::jsonb, %(reference_lat)s, %(reference_lon)s,
               %(reference_tz_offset_minutes)s, %(reference_location_key)s,
               %(ayanamsha_key)s, %(sampling_method)s, %(source_citation)s,
               %(corpus_status)s, %(build_id)s, now())""",
            legacy,
        )
    db_conn.commit()

    corrected = _batch_row(
        "shukla_tritiya", sunrise, boundary,
        {"factor_id": 3, "span_convention": "true_anga_interval_clipped_to_hindu_day"},
        build_id,
    )
    successor = _batch_row(
        "shukla_chaturthi", boundary, next_sunrise,
        {"factor_id": 4, "span_convention": "true_anga_interval_clipped_to_hindu_day"},
        build_id,
    )

    with db_conn.cursor() as cur:
        changed = BgMuhurtaLatticeWriter._flush_batch(cur, [corrected, successor])
    db_conn.commit()
    assert changed == 2

    rows = db_conn.execute(
        """SELECT factor_key, start_utc, end_utc, detail
             FROM bg_muhurta_lattice ORDER BY start_utc"""
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["end_utc"] == rows[1]["start_utc"] == boundary
    assert rows[0]["detail"]["span_convention"] == "true_anga_interval_clipped_to_hindu_day"
    overlap_count = db_conn.execute(
        """SELECT count(*) AS n
             FROM bg_muhurta_lattice left_atom
             JOIN bg_muhurta_lattice right_atom
               ON left_atom.factor_family = right_atom.factor_family
              AND left_atom.start_utc < right_atom.start_utc
              AND tstzrange(left_atom.start_utc, left_atom.end_utc, '[)')
                  && tstzrange(right_atom.start_utc, right_atom.end_utc, '[)')"""
    ).fetchone()["n"]
    assert overlap_count == 0

    with db_conn.cursor() as cur:
        unchanged = BgMuhurtaLatticeWriter._flush_batch(cur, [corrected, successor])
    db_conn.commit()
    assert unchanged == 0
