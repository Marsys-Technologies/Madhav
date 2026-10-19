"""Real persistence and SQL refusal detectors for KA-3a review survivors."""
from types import SimpleNamespace
from uuid import UUID

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
from tests.l3.kala_db.ka_vedha_gochara.conftest import BUILD, CHART, MIGRATION
from tests.l3.kala_db.ka_vedha_gochara.test_candidate_storage import active_bundle, snapshot, store


def test_typed_payload_writer_dispatch_persists_exact_rows_on_caller_transaction(conn, kala_db_dsn):
    conn.commit()  # Only fixture setup is committed, to expose the test schema.
    schema = conn.execute('SELECT current_schema()').fetchone()[0]
    payload = active_bundle()
    assert payload.intervals
    legacy = snapshot(conn, 'kala_vedha_gochara')
    ctx = SimpleNamespace(db_conn=conn, build_id=BUILD, dry_run=False,
                          config={'chart_id': CHART, 'vedha_candidate_payload': payload})
    result = KaVedhaGocharaWriter().run(ctx)
    assert result.rows_inserted == len(payload.intervals)
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_candidate').fetchone()[0] == 3
    with conn.cursor(row_factory=dict_row) as cursor:
        stored = cursor.execute('SELECT * FROM kala_vedha_gochara_interval').fetchall()
    normalized = [{k: str(v) if isinstance(v, UUID) else v for k, v in row.items()} for row in stored]
    order = lambda row: (row['vedha_kind'], row['graha'], row['t_in'])
    assert sorted(normalized, key=order) == sorted(payload.intervals, key=order)
    assert snapshot(conn, 'kala_vedha_gochara') == legacy
    # The provider must neither commit nor close the orchestrator connection.
    with psycopg.connect(kala_db_dsn) as observer:
        observer.execute(f'SET search_path TO "{schema}", public')
        assert observer.execute('SELECT count(*) FROM kala_vedha_gochara_interval').fetchone()[0] == 0
    conn.rollback()
    assert conn.execute('SELECT count(*) FROM kala_vedha_gochara_interval').fetchone()[0] == 0


@pytest.mark.parametrize('qualification', ['unsourced', 'algorithmic_approximation'])
def test_sql_rejects_non_verse_cited_intervals(conn, qualification):
    store(conn, active_bundle())
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute('UPDATE kala_vedha_gochara_interval SET source_qualification=%s', (qualification,))


@pytest.mark.parametrize('key,value', [('score', 99), ('segments', []), ('concurrent_latta_count', 2)])
def test_sql_rejects_forbidden_computation_fields(conn, key, value):
    # Packet §4: exact child intervals, no invented numerical severity or packed
    # segments; XXVI.47-48 is enrichment only, never a concurrent-latta score.
    store(conn, active_bundle())
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute('UPDATE kala_vedha_gochara_interval SET detail=detail || %s', (Jsonb({key: value}),))


@pytest.mark.parametrize('primary,excepted,allowed', [('Sun', 'Saturn', 'Mars'), ('Saturn', 'Sun', 'Mars')])
def test_sql_rejects_classically_excepted_obstructors(conn, primary, excepted, allowed):
    # Phaladipika XXVI.3-8 PG322-323, exception paragraph: Sun/Saturn do
    # not obstruct one another. The positive control rules out an unrelated
    # UPDATE/identity/state refusal as the cause of the negative control.
    store(conn, active_bundle())
    conn.execute("UPDATE kala_vedha_gochara_interval SET graha=%s,obstructors=ARRAY[%s] "
                 "WHERE graha='Sun' AND state='active'", (primary, allowed))
    assert conn.execute("SELECT count(*) FROM kala_vedha_gochara_interval WHERE graha=%s AND state='active'",
                        (primary,)).fetchone()[0] == 1
    with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
        conn.execute("UPDATE kala_vedha_gochara_interval SET obstructors=ARRAY[%s] WHERE graha=%s AND state='active'",
                     (excepted, primary))


def test_migration_adds_nullable_legacy_contract_columns_without_backfill(conn):
    expected = {'method_qualification': 'text', 'coverage': 'jsonb', 'upstream_fingerprint': 'jsonb'}
    for _ in range(2):
        columns = {name: (kind, nullable, default) for name, kind, nullable, default in conn.execute(
            "SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns "
            "WHERE table_schema=current_schema() AND table_name='kala_vedha_gochara'")}
        assert {name: columns.get(name) for name in expected} == {
            name: (kind, 'YES', None) for name, kind in expected.items()}
        assert conn.execute('SELECT method_qualification,coverage,upstream_fingerprint FROM kala_vedha_gochara').fetchall() == [
            (None, None, None)]
        schema = conn.execute('SELECT quote_ident(current_schema())').fetchone()[0]
        conn.execute(MIGRATION.read_text().replace('public.', schema + '.'))
