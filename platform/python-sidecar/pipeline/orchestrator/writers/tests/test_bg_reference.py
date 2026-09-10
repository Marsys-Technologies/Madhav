"""Opt-in mutation tests for bg_reference against an explicit local test DB."""
import os
import uuid
import pytest
import psycopg
from pipeline.orchestrator.writers.bg_reference import ReferenceWriter
from pipeline.orchestrator.writers import ContextSpec


@pytest.fixture(scope='module')
def db_conn():
    url = os.environ.get('NIRMANA_BG_REFERENCE_MUTATION_TEST_DATABASE_URL')
    if not url:
        pytest.skip('NIRMANA_BG_REFERENCE_MUTATION_TEST_DATABASE_URL not set')
    parsed = psycopg.conninfo.conninfo_to_dict(url)
    if parsed.get('host') not in {'localhost', '127.0.0.1'} \
       or parsed.get('dbname') != 'nirmana_bg_reference_writer_test':
        raise RuntimeError(
            'NIRMANA_BG_REFERENCE_MUTATION_TEST_DATABASE_URL must point to the exact '
            'local nirmana_bg_reference_writer_test database'
        )
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_reference_writer_runs(db_conn):
    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    assert result.asset_id == 'bg_reference'
    assert result.rows_inserted >= 0  # may be 0 on idempotent re-run


def test_bg_reference_row_counts(db_conn):
    """After a run, all 11 writer-owned tables match the achieved contract."""
    cur = db_conn.cursor()
    expected_counts = {
        'reference_planets': 11, 'reference_signs': 12,
        'reference_aspects': 19, 'reference_vargas': 19,
        'reference_houses': 12, 'reference_strength_systems': 33,
        'reference_karakas': 77, 'reference_upagrahas': 11,
        'reference_constants': 203, 'reference_topic_tags': 481,
        'reference_glossary': 364,
    }
    for table, expected in expected_counts.items():
        cur.execute(f"SELECT count(*) AS n FROM {table}")
        assert cur.fetchone()['n'] == expected, f'{table} does not equal {expected}'


def test_bg_reference_no_null_citations(db_conn):
    """Every row must have a non-NULL source_citation."""
    cur = db_conn.cursor()
    citation_columns = {
        'reference_planets': 'source_citation', 'reference_signs': 'source_citation',
        'reference_aspects': 'source_citation', 'reference_vargas': 'source_citation',
        'reference_houses': 'source_citation', 'reference_strength_systems': 'source_citation',
        'reference_karakas': 'source_citation', 'reference_upagrahas': 'source_citation',
        'reference_constants': 'source_citation', 'reference_glossary': 'classical_citation',
    }
    for tbl, citation_column in citation_columns.items():
        cur.execute(
            f"SELECT count(*) AS n FROM {tbl} "
            f"WHERE {citation_column} IS NULL OR btrim({citation_column}) = ''"
        )
        n = cur.fetchone()['n']
        assert n == 0, f'{tbl} has {n} missing citations'


def test_bg_reference_writer_idempotent(db_conn):
    """Running the writer twice leaves reference table counts identical."""
    cur = db_conn.cursor()
    cur.execute("""
        SELECT
          (SELECT count(*) FROM reference_planets) +
          (SELECT count(*) FROM reference_signs) +
          (SELECT count(*) FROM reference_aspects) +
          (SELECT count(*) FROM reference_vargas) +
          (SELECT count(*) FROM reference_houses) +
          (SELECT count(*) FROM reference_strength_systems) +
          (SELECT count(*) FROM reference_karakas) +
          (SELECT count(*) FROM reference_upagrahas) +
          (SELECT count(*) FROM reference_constants) +
          (SELECT count(*) FROM reference_topic_tags) +
          (SELECT count(*) FROM reference_glossary) AS total
    """)
    count_before = cur.fetchone()['total']

    writer = ReferenceWriter()
    ctx = ContextSpec(asset_id='bg_reference', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)

    cur.execute("""
        SELECT
          (SELECT count(*) FROM reference_planets) +
          (SELECT count(*) FROM reference_signs) +
          (SELECT count(*) FROM reference_aspects) +
          (SELECT count(*) FROM reference_vargas) +
          (SELECT count(*) FROM reference_houses) +
          (SELECT count(*) FROM reference_strength_systems) +
          (SELECT count(*) FROM reference_karakas) +
          (SELECT count(*) FROM reference_upagrahas) +
          (SELECT count(*) FROM reference_constants) +
          (SELECT count(*) FROM reference_topic_tags) +
          (SELECT count(*) FROM reference_glossary) AS total
    """)
    count_after = cur.fetchone()['total']

    assert count_before == count_after, \
        f'Idempotency broken: {count_before} → {count_after} (rows_inserted={result.rows_inserted})'
    assert result.rows_inserted == 0, \
        f'Expected 0 rows_inserted on re-run, got {result.rows_inserted}'
