"""publish_head (J-6m) and rollback_head (J-6r) on guarded disposable Postgres, against the real 1236/1379/1382 schema.

Sources of the claims: migration 1379 (a governed head requires a published, non-test-slice manifest AND its immutable
seal; DELETE of a governed head is refused: "rollback requires the explicit retained previous head"), migration 1382
(no TRUNCATE), PLAN section 4.4.6 (compare-and-swap back to a retained head), SURROGATE G6 (previous-head retention),
SR-MINIMAL-PROTECTION (a dry run writes nothing). Seals are synthetic admission metadata (see test_j6r_rehearsal_db),
not attestations of computation. No production database is reachable from this module.
"""
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from psycopg.conninfo import make_conninfo

from scripts.kala_gochara_cutover import head_ops, publish_head, rollback_head
from .test_a53_inventory import CHART_ID
from .test_a53_record_store import ADMIN_DSN
from .test_j6r_rehearsal_db import rehearsal_database  # noqa: F401  (module fixture: 1236+1379+1382 schema, 3.0 head)

SCRIPTS = Path(__file__).resolve().parents[3] / 'scripts' / 'kala_gochara_cutover'
OP_ENV = {'KY_OPERATION_REQUEST': json.dumps({'operation_id': 'op-test-1'})}
INITIAL = ('3.0', '2025-01-01 UTC', 'fixture', 'retained-head')


@pytest.fixture(autouse=True)
def _canonical_chart_head(rehearsal_database):
    # The operations are pinned to the canonical chart; the fixture's chart must be it, or every test is vacuous.
    assert CHART_ID == head_ops.CANONICAL_CHART
    conn, _ = rehearsal_database
    conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=%s::timestamptz,'
                 ' flipped_by=%s, evidence_ref=%s WHERE chart_id=%s', (*INITIAL, CHART_ID))
    yield
    conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=%s::timestamptz,'
                 ' flipped_by=%s, evidence_ref=%s WHERE chart_id=%s', (*INITIAL, CHART_ID))


@pytest.fixture(autouse=True, scope='module')
def _synthetic_search_inventory(rehearsal_database):
    """Synthetic search-inventory header for the sealed 5.0 manifest (the AM-5 snapshot chain is not rebuilt here, so the
    snapshot FK is bypassed by replica mode on THIS statement only). It is admission metadata that lets the REAL reader
    answer an all-class read; it attests nothing about search completeness (the reader reports `stale_binding`).
    A sealed generation's inventory is immutable (AM-5), so it is added once and kept."""
    conn, _ = rehearsal_database
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role = replica")
        conn.execute("INSERT INTO public.ka_gochara_search_inventory (chart_id,generation,event_class,horizon,input_digest)"
                     " VALUES (%s,'5.0','marriage',tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),%s)",
                     (CHART_ID, '0' * 64))


def _head(conn):
    return conn.execute('SELECT xmin::text, authoritative_generation, flipped_at, flipped_by, evidence_ref'
                        ' FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()


def _publish(conn, capsys, *argv, environ=OP_ENV):
    code = publish_head.run(list(argv), environ=environ, conn=conn)
    return code, json.loads(capsys.readouterr().out)


def _rollback(conn, capsys, *argv, environ=OP_ENV):
    code = rollback_head.run(list(argv), environ=environ, conn=conn)
    return code, json.loads(capsys.readouterr().out)


def _pub(mid, mode='--execute', gen='5.0', expected='3.0'):
    return [mode, '--generation', gen, '--manifest-id', mid, '--expected-head', expected]


def test_publish_then_rollback_round_trips_the_head_and_retains_everything(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    counts = head_ops.retained_counts(conn, CHART_ID)
    code, published = _publish(conn, capsys, *_pub(mids['5.0']))
    assert code == 0 and published['status'] == 'HEAD_PUBLISHED' and published['writes'] == 1, published
    assert published['previous_head']['generation'] == '3.0'
    assert published['previous_head']['evidence_ref'] == 'retained-head'          # the whole previous row is in the receipt
    assert published['served'] == {'generation': '5.0', 'manifest_id': mids['5.0'], 'refusal': None}
    assert published['retained_rows_equal'] is True
    row = _head(conn)
    assert row[1] == '5.0' and row[3] == 'publish_head:op-test-1'
    assert row[4] == f"manifest:{mids['5.0']};previous:3.0"                          # previous head retained on the row
    code, restored = _rollback(conn, capsys, '--execute', '--generation', '3.0', '--expected-head', '5.0')
    assert code == 0 and restored['status'] == 'HEAD_RESTORED' and restored['writes'] == 1
    assert restored['served'] is None and 'legacy' in restored['served_reason']        # an honest null, not a fake check
    row = _head(conn)
    assert row[1] == '3.0' and row[3] == 'rollback_head:op-test-1'                     # the retained head, not a DELETE-to-v1
    assert row[4].startswith('rollback-from:5.0;manifest:') and ';previous:' not in row[4]
    assert head_ops.retained_counts(conn, CHART_ID) == counts                            # no generation content moved
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 1


@pytest.mark.parametrize('gen', ['5.1', '5.2', '5.3', '9.9'])
@pytest.mark.parametrize('mode', ['--execute', '--dry-run'])
def test_candidate_unsealed_test_slice_and_missing_generations_are_refused(rehearsal_database, capsys, gen, mode):
    conn, mids = rehearsal_database
    before = _head(conn)
    code, out = _publish(conn, capsys, *_pub(mids.get(gen, str(uuid.uuid4())), mode=mode, gen=gen))
    assert code == head_ops.EXIT_REFUSED and out['status'] == 'REFUSED' and out['refusal'] == 'target_not_admissible'
    assert _head(conn) == before                                                       # xmin included: not even a no-op UPDATE


def test_a_sealed_generation_with_another_manifest_id_is_refused(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    before = _head(conn)
    code, out = _publish(conn, capsys, *_pub(mids['5.1']))                              # 5.0 asked, a candidate's manifest named
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'target_not_admissible'
    assert _head(conn) == before


@pytest.mark.parametrize('call', ['publish', 'rollback'])
def test_a_dry_run_writes_nothing_and_the_database_itself_is_read_only(rehearsal_database, capsys, call):
    conn, mids = rehearsal_database
    if call == 'rollback':
        assert _publish(conn, capsys, *_pub(mids['5.0']))[0] == 0
    before, counts = _head(conn), head_ops.retained_counts(conn, CHART_ID)
    if call == 'publish':
        code, out = _publish(conn, capsys, *_pub(mids['5.0'], mode='--dry-run'))
        assert out['served_preview'] == {'generation': '5.0', 'manifest_id': mids['5.0'], 'refusal': None}
        assert out['would_write']['evidence_ref'] == f"manifest:{mids['5.0']};previous:3.0"
    else:
        code, out = _rollback(conn, capsys, '--dry-run', '--generation', '3.0', '--expected-head', '5.0')
        assert out['would_write']['authoritative_generation'] == '3.0'
    assert code == 0 and out['status'] == 'DRY_RUN_NO_WRITE' and out['writes'] == 0 and out['read_only_confirmed'] is True
    assert _head(conn) == before and head_ops.retained_counts(conn, CHART_ID) == counts
    assert not conn.read_only                                                    # the caller's connection is left as found


def test_publish_is_compare_and_swap_on_the_expected_head(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    before = _head(conn)
    code, out = _publish(conn, capsys, *_pub(mids['5.0'], expected='4.1'))
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'head_compare_and_swap_conflict' and _head(conn) == before
    assert _publish(conn, capsys, *_pub(mids['5.0']))[0] == 0
    code, out = _publish(conn, capsys, *_pub(mids['5.0']))                              # a replay is stale, never a silent no-op
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'head_compare_and_swap_conflict'
    code, out = _publish(conn, capsys, *_pub(mids['5.0'], expected='5.0'))
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'target_is_current_head'


def test_rollback_refuses_unrecorded_stale_or_unretained_targets(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    args = lambda gen, cur: ['--execute', '--generation', gen, '--expected-head', cur]   # noqa: E731
    code, out = _rollback(conn, capsys, *args('3.0', '3.0'))
    assert out['refusal'] == 'target_is_current_head'
    code, out = _rollback(conn, capsys, *args('v1', '3.0'))                              # head not set by publish_head: no record
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'target_is_not_the_recorded_previous_head'
    assert _publish(conn, capsys, *_pub(mids['5.0']))[0] == 0
    published = _head(conn)
    code, out = _rollback(conn, capsys, *args('v1', '5.0'))                              # not the recorded previous head
    assert out['refusal'] == 'target_is_not_the_recorded_previous_head'
    code, out = _rollback(conn, capsys, *args('3.0', '9.9'))                             # stale expected head
    assert out['refusal'] == 'head_compare_and_swap_conflict' and _head(conn) == published
    conn.execute("UPDATE public.kala_gochara_authority SET evidence_ref=%s WHERE chart_id=%s",
                 (f"manifest:{mids['5.0']};previous:3.5", CHART_ID))                      # recorded, but 3.5 holds no rows
    code, out = _rollback(conn, capsys, *args('3.5', '5.0'))
    assert out['refusal'] == 'retained_head_has_no_rows'
    assert _rollback(conn, capsys, *args('3.5', '5.0'))[0] == head_ops.EXIT_REFUSED
    assert _head(conn)[1] == '5.0'


def test_a_second_rollback_is_refused_because_the_record_is_consumed(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    assert _publish(conn, capsys, *_pub(mids['5.0']))[0] == 0
    assert _rollback(conn, capsys, '--execute', '--generation', '3.0', '--expected-head', '5.0')[0] == 0
    code, out = _rollback(conn, capsys, '--execute', '--generation', '3.0', '--expected-head', '3.0')
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'target_is_current_head'


def test_a_missing_head_row_is_refused_not_defaulted(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    conn.execute('ALTER TABLE public.kala_gochara_authority DISABLE TRIGGER USER')
    try:
        conn.execute("DELETE FROM public.kala_gochara_authority WHERE chart_id=%s", (CHART_ID,))
        code, out = _publish(conn, capsys, *_pub(mids['5.0']))
        assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'head_missing'
        assert conn.execute('SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 0
    finally:
        conn.execute("INSERT INTO public.kala_gochara_authority (chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref)"
                     " VALUES (%s,%s,%s::timestamptz,%s,%s) ON CONFLICT DO NOTHING", (CHART_ID, *INITIAL))
        conn.execute('ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_0_statement_lock')
        conn.execute('ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_1_sealed_guard')


def test_the_operation_must_name_its_operation(rehearsal_database, capsys):
    conn, mids = rehearsal_database
    before = _head(conn)
    code, out = _publish(conn, capsys, *_pub(mids['5.0']), environ={})
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'operation_id_missing' and _head(conn) == before


def test_a_reader_that_refuses_the_new_head_aborts_the_publish(rehearsal_database, capsys, monkeypatch):
    from services.gochara_kernel import serving_reader
    conn, mids = rehearsal_database
    before = _head(conn)
    real = serving_reader.read_authoritative
    monkeypatch.setattr(serving_reader, 'read_authoritative',
                        lambda *a, **k: {**real(*a, **k), 'refusal': {'code': 'not_sealed'}})
    code, out = _publish(conn, capsys, *_pub(mids['5.0']))
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'served_identity_or_admission_failed'
    assert _head(conn) == before                                                       # the UPDATE was rolled back with the transaction


def test_content_rows_changing_during_the_operation_abort_it(rehearsal_database, capsys, monkeypatch):
    conn, mids = rehearsal_database
    before = _head(conn)
    original = head_ops.served_identity
    def deleting(c, chart, generation, manifest_id):
        c.execute('DELETE FROM public.kala_gochara_windows WHERE chart_id=%s', (chart,))
        return original(c, chart, generation, manifest_id)
    monkeypatch.setattr(head_ops, 'served_identity', deleting)
    code, out = _publish(conn, capsys, *_pub(mids['5.0']))
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'retained_rows_changed'
    assert _head(conn) == before
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 1


def test_scripts_run_as_the_executor_runs_them_and_round_trip_over_a_real_connection(rehearsal_database):
    conn, mids = rehearsal_database
    dsn = make_conninfo(ADMIN_DSN, dbname=conn.info.dbname)
    env = {'DATABASE_URL': dsn, 'KY_OPERATION_REQUEST': json.dumps({'operation_id': 'op-cli-1'}), 'PATH': '/usr/bin:/bin'}
    def cli(script, *argv):
        done = subprocess.run([sys.executable, str(SCRIPTS / script), *argv], env=env, capture_output=True, text=True, timeout=120)
        return done.returncode, json.loads(done.stdout)
    before = _head(conn)
    code, out = cli('publish_head.py', '--dry-run', '--generation', '5.0', '--manifest-id', mids['5.0'], '--expected-head', '3.0')
    assert code == 0 and out['status'] == 'DRY_RUN_NO_WRITE' and _head(conn) == before
    code, out = cli('publish_head.py', '--execute', '--generation', '5.0', '--manifest-id', mids['5.0'], '--expected-head', '3.0')
    assert code == 0 and out['status'] == 'HEAD_PUBLISHED' and _head(conn)[1] == '5.0'
    code, out = cli('rollback_head.py', '--dry-run', '--generation', '3.0', '--expected-head', '5.0')
    assert code == 0 and _head(conn)[1] == '5.0'
    code, out = cli('rollback_head.py', '--execute', '--generation', '3.0', '--expected-head', '5.0')
    assert code == 0 and out['status'] == 'HEAD_RESTORED' and _head(conn)[1] == '3.0'
    done = subprocess.run([sys.executable, str(SCRIPTS / 'publish_head.py'), '--generation', '5.0', '--manifest-id', mids['5.0'],
                           '--expected-head', '3.0'], env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 2 and _head(conn)[1] == '3.0'                            # neither --dry-run nor --execute: nothing happens


def test_a_generation_the_real_reader_cannot_serve_is_not_published(rehearsal_database, capsys):
    conn, _ = rehearsal_database                          # sealed and admissible, but the REAL reader refuses it (no bound result policy)
    mid = str(uuid.uuid4())
    with conn.transaction():
        conn.execute('ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER')
        conn.execute("INSERT INTO public.kala_gochara_publication (manifest_id,chart_id,generation,writer_asset_id,convention_id,"
                     " input_generation_vector,ephemeris_backend,horizon,row_counts,content_digest,status) VALUES"
                     " (%s,%s,'5.4','ka_gochara_v5','j6r-metadata-only','{\"stored_scope\":\"stored_non_moon\"}','{}',"
                     " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','metadata-only','published')", (mid, CHART_ID))
        conn.execute('INSERT INTO public.ka_gochara_generation_seal(chart_id,generation,manifest_id) VALUES (%s,%s,%s)',
                     (CHART_ID, '5.4', mid))
        conn.execute('ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER')
    mids = {'5.0': mid, '5.4': mid}
    before = _head(conn)
    code, out = _publish(conn, capsys, *_pub(mids['5.4'], gen='5.4'))
    assert code == head_ops.EXIT_REFUSED and out['refusal'] == 'served_identity_or_admission_failed'
    assert 'result_policy_unbound' in out['detail'] and _head(conn) == before


def test_the_executors_session_marker_reaches_the_scripts_connection(rehearsal_database, monkeypatch):
    """A7 D-44: quiescence finds an operation's sessions by PGAPPNAME. The scripts open their connection with head_ops.connect and
    set no application_name, so libpq applies the executor's marker; measured on a live session, not assumed."""
    conn, _ = rehearsal_database
    marker = 'ky-op-' + 'ab' * 8
    monkeypatch.setenv('PGAPPNAME', marker)
    own = head_ops.connect({'DATABASE_URL': make_conninfo(ADMIN_DSN, dbname=conn.info.dbname)}, read_only=True)
    try:
        assert own.execute('SHOW application_name').fetchone()[0] == marker
        assert conn.execute('SELECT count(*) FROM pg_stat_activity WHERE application_name=%s', (marker,)).fetchone()[0] == 1
    finally:
        own.close()
