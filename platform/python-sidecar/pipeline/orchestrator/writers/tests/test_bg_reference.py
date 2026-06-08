"""Tests for the bg_reference writer (runs against live DB via DATABASE_URL)."""
import os
import uuid
import pytest
import psycopg
from pipeline.orchestrator.writers.bg_reference import ReferenceWriter
from pipeline.orchestrator.writers import ContextSpec


@pytest.fixture(scope='module')
def db_conn():
    url = os.environ.get('DATABASE_URL') or os.environ.get('PROD_DB_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_reference_writer_runs(db_conn):
    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == 'bg_reference'
    assert result.rows_inserted >= 0  # may be 0 on idempotent re-run


def test_bg_reference_row_counts(db_conn):
    """After a run, reference tables must meet their volume floors."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM reference_planets")
    assert cur.fetchone()['n'] >= 11, 'reference_planets below floor of 11'
    cur.execute("SELECT count(*) AS n FROM reference_nakshatras")
    assert cur.fetchone()['n'] >= 27, 'reference_nakshatras below floor of 27'
    cur.execute("SELECT count(*) AS n FROM reference_signs")
    assert cur.fetchone()['n'] >= 12, 'reference_signs below floor of 12'


def test_bg_reference_no_null_citations(db_conn):
    """Every row must have a non-NULL source_citation."""
    cur = db_conn.cursor()
    for tbl in ['reference_planets', 'reference_nakshatras', 'reference_signs',
                'reference_aspects', 'reference_vargas']:
        cur.execute(f"SELECT count(*) AS n FROM {tbl} WHERE source_citation IS NULL")
        n = cur.fetchone()['n']
        assert n == 0, f'{tbl} has {n} rows with NULL source_citation'


def test_bg_reference_writer_idempotent(db_conn):
    """Running the writer twice leaves reference table counts identical."""
    cur = db_conn.cursor()
    cur.execute("""
        SELECT
          (SELECT count(*) FROM reference_planets) +
          (SELECT count(*) FROM reference_nakshatras) +
          (SELECT count(*) FROM reference_signs) +
          (SELECT count(*) FROM reference_aspects) +
          (SELECT count(*) FROM reference_vargas) AS total
    """)
    count_before = cur.fetchone()['total']

    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()

    cur.execute("""
        SELECT
          (SELECT count(*) FROM reference_planets) +
          (SELECT count(*) FROM reference_nakshatras) +
          (SELECT count(*) FROM reference_signs) +
          (SELECT count(*) FROM reference_aspects) +
          (SELECT count(*) FROM reference_vargas) AS total
    """)
    count_after = cur.fetchone()['total']

    assert count_before == count_after, \
        f'Idempotency broken: {count_before} → {count_after} (rows_inserted={result.rows_inserted})'
    assert result.rows_inserted == 0, \
        f'Expected 0 rows_inserted on re-run, got {result.rows_inserted}'
