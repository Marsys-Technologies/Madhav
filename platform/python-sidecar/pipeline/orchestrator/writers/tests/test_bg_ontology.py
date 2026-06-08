"""Tests for the bg_ontology writer (runs against live DB via DATABASE_URL)."""
import os
import uuid
import pytest
import psycopg
from pipeline.orchestrator.writers.bg_ontology import OntologyWriter
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


def test_bg_ontology_writer_runs(db_conn):
    writer = OntologyWriter()
    ctx = ContextSpec(asset_id='bg_ontology', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == 'bg_ontology'
    assert result.rows_inserted >= 0


def test_bg_ontology_volume_floor(db_conn):
    """brahma_ontology must have >= 100 entities."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM brahma_ontology")
    n = cur.fetchone()['n']
    assert n >= 100, f'brahma_ontology below floor of 100 (got {n})'


def test_bg_ontology_no_null_citations(db_conn):
    """Every entity must have a non-NULL source_citation."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM brahma_ontology WHERE source_citation IS NULL")
    n = cur.fetchone()['n']
    assert n == 0, f'brahma_ontology has {n} rows with NULL source_citation'


def test_bg_ontology_required_entity_classes(db_conn):
    """Core entity classes must be present: planet, nakshatra, sign, house."""
    cur = db_conn.cursor()
    cur.execute("SELECT entity_class, count(*) AS n FROM brahma_ontology GROUP BY entity_class")
    rows = cur.fetchall()
    by_class = {r['entity_class']: r['n'] for r in rows}
    assert by_class.get('planet', 0) >= 9, f'Expected >= 9 planets, got {by_class}'
    assert by_class.get('nakshatra', 0) >= 27, f'Expected 27 nakshatras, got {by_class}'
    assert by_class.get('sign', 0) >= 12, f'Expected 12 signs, got {by_class}'
    assert by_class.get('house', 0) >= 12, f'Expected 12 houses, got {by_class}'


def test_bg_ontology_writer_idempotent(db_conn):
    """Running the writer twice leaves brahma_ontology count identical."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM brahma_ontology")
    count_before = cur.fetchone()['n']

    writer = OntologyWriter()
    ctx = ContextSpec(asset_id='bg_ontology', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()

    cur.execute("SELECT count(*) AS n FROM brahma_ontology")
    count_after = cur.fetchone()['n']

    assert count_before == count_after, \
        f'Idempotency broken: {count_before} → {count_after}'
    assert result.rows_inserted == 0, \
        f'Expected 0 rows_inserted on re-run, got {result.rows_inserted}'
