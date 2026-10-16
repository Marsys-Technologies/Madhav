"""J-6r code preparation on guarded disposable Postgres, without a sky stand-in.

Seals below are synthetic admission metadata, installed before 1379. They do
not attest to computation or independent verification. The actual reader must
honestly report stale_binding (no search snapshot). This is deliberately
not the production/lane acceptance artifact required by J-6r and G6.
"""
import hashlib
import json
import uuid

import psycopg
from psycopg.types.json import Jsonb
import pytest

from scripts.kala_gochara_cutover import j6r_rehearsal as rehearsal
from ._disposable_db_guard import guarded_admin_connect
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_record_store import ADMIN_DSN
from .test_j6m_authority_admission_db import ROOT, MIGRATIONS

OTHER_CHART = str(uuid.UUID(int=900))


@pytest.fixture(scope='module')
def rehearsal_database():
    admin, name, dsn = create_am5_database('j6r')
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid)')
        conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
        conn.execute((MIGRATIONS / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
        conn.execute("INSERT INTO public.kala_gochara_convention"
                     " (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,epoch_convention,"
                     " time_scale,house_system,ephemeris_mode,method_version)"
                     " VALUES ('j6r-metadata-only','fixture','fixture','fixture','fixture','fixture','fixture',"
                     " 'fixture','fixture','fixture','fixture')")
        manifests = {}
        with conn.transaction():
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER')
            for gen, status, vector, sealed in [
                ('3.0', 'published', {}, False),
                ('5.0', 'published', {'stored_scope': 'stored_non_moon', 'result_policy': 'all_null_candidate/1'}, True),
                ('5.1', 'candidate', {}, False),
                ('5.2', 'published', {}, False),
                ('5.3', 'published', {'stored_scope': 'test_slice'}, True),
            ]:
                mid = str(uuid.uuid4())
                manifests[gen] = mid
                conn.execute("INSERT INTO public.kala_gochara_publication"
                             " (manifest_id,chart_id,generation,writer_asset_id,convention_id,input_generation_vector,"
                             " ephemeris_backend,horizon,row_counts,content_digest,status)"
                             " VALUES (%s,%s,%s,'ka_gochara_v5','j6r-metadata-only',%s,'{}',"
                             " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','metadata-only',%s)",
                             (mid, CHART_ID, gen, Jsonb(vector), status))
                if sealed:
                    conn.execute('INSERT INTO public.ka_gochara_generation_seal(chart_id,generation,manifest_id)'
                                 ' VALUES (%s,%s,%s)', (CHART_ID, gen, mid))
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER')
        conn.execute("INSERT INTO public.kala_gochara_authority"
                     " (chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref)"
                     " VALUES (%s,'3.0','2025-01-01 UTC','fixture','retained-head')", (CHART_ID,))
        conn.execute("INSERT INTO public.kala_gochara_windows(chart_id,generation) VALUES (%s,'3.0'),(%s,'v1')",
                     (CHART_ID, OTHER_CHART))
        with conn.transaction():
            conn.execute((MIGRATIONS / '1379_gochara_sealed_authority.sql').read_text())
            conn.execute((MIGRATIONS / '1382_gochara_authority_no_truncate.sql').read_text())
        yield conn, manifests
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture
def db(rehearsal_database):
    conn, manifests = rehearsal_database
    with conn.transaction(force_rollback=True):
        yield conn, manifests


def _legacy(conn, chart_id, generation, **request):
    # A deterministic transport fixture over stored rows, not fabricated chart
    # values, a production legacy adapter, or an ephemeris replacement.
    rows = conn.execute('SELECT generation FROM public.kala_gochara_windows'
                        ' WHERE chart_id=%s AND generation=%s ORDER BY generation', (chart_id, generation)).fetchall()
    return json.dumps({'generation': generation, 'stored_rows': rows}, separators=(',', ':')).encode()


def _run(db, **kw):
    conn, mids = db
    args = dict(chart_id=CHART_ID, expected_previous='3.0', generation='5.0',
                manifest_id=mids['5.0'], legacy_reader=_legacy, request={'event_classes': ['marriage']})
    args.update(kw)
    return rehearsal.rehearse(conn, **args)


def _heads(conn):
    return conn.execute('SELECT * FROM public.kala_gochara_authority ORDER BY chart_id').fetchall()


def test_flip_serves_exact_manifest_rollback_restores_bytes_and_retains_both_heads(db):
    conn, mids = db
    before_heads = _heads(conn)
    before = _legacy(conn, CHART_ID, '3.0')
    evidence = _run(db)
    assert evidence['schema'] == 'ky.j6r_prebuild_rehearsal/1'
    assert evidence['acceptance'] is None and evidence['production_activated'] is False
    assert evidence['target'] == {'generation': '5.0', 'manifest_id': mids['5.0']}
    assert evidence['before']['generation'] == evidence['after']['generation'] == '3.0'
    assert evidence['before']['sha256'] == evidence['after']['sha256'] == hashlib.sha256(before).hexdigest()
    assert evidence['flipped']['generation'] == '5.0'
    assert evidence['flipped']['manifest_id'] == mids['5.0']
    assert evidence['flipped']['class_completeness'] == {'marriage': 'stale_binding'}
    assert evidence['rollback_bytes_equal'] is True
    assert evidence['retained_rows_equal'] is True
    assert evidence['outside_horizon_refusal'] == 'outside_served_horizon'
    assert evidence['retained_before'] == evidence['retained_after_flip'] == evidence['retained_after_rollback']
    assert evidence['retained_before']['kala_gochara_publication']['rows'] == 5
    assert evidence['retained_before']['kala_gochara_windows']['rows'] == 1
    assert _heads(conn) == before_heads  # includes all audit columns
    assert conn.execute('SELECT generation FROM public.kala_gochara_windows WHERE chart_id=%s',
                        (OTHER_CHART,)).fetchall() == [('v1',)]
    json.dumps(evidence, allow_nan=False)


@pytest.mark.parametrize('gen', ['5.1', '5.2', '5.3', '9.9'])
def test_candidate_unsealed_slice_and_missing_target_refused_without_mutation(db, gen):
    conn, mids = db
    before = _heads(conn)
    with pytest.raises(rehearsal.RehearsalRefused, match='target_not_admissible'):
        _run(db, generation=gen, manifest_id=mids.get(gen, str(uuid.uuid4())))
    assert _heads(conn) == before


def test_exact_manifest_and_expected_previous_are_mandatory(db):
    conn, _ = db
    before = _heads(conn)
    with pytest.raises(rehearsal.RehearsalRefused, match='target_not_admissible'):
        _run(db, manifest_id=str(uuid.uuid4()))
    with pytest.raises(rehearsal.RehearsalRefused, match='previous_head_changed'):
        _run(db, expected_previous='v1')
    assert _heads(conn) == before


def test_missing_explicit_previous_head_is_not_invented(db):
    conn, _ = db
    conn.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    with pytest.raises(rehearsal.RehearsalRefused, match='previous_head_missing'):
        _run(db)
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 0


def test_compare_and_swap_refuses_stale_audit_metadata_as_well_as_generation(db):
    conn, _ = db
    previous = rehearsal.read_head(conn, CHART_ID)
    conn.execute("UPDATE public.kala_gochara_authority SET evidence_ref='different' WHERE chart_id=%s", (CHART_ID,))
    with pytest.raises(rehearsal.RehearsalRefused, match='head_compare_and_swap_conflict'):
        rehearsal.compare_and_swap(conn, CHART_ID, previous, previous)
    assert rehearsal.read_head(conn, CHART_ID).evidence_ref == 'different'


def test_byte_difference_is_detected_even_for_semantically_equal_json_and_scope_rolls_back(db):
    conn, _ = db
    before = _heads(conn)
    calls = []
    def unstable(*args, **kwargs):
        calls.append(1)
        raw = _legacy(*args, **kwargs)
        return raw if len(calls) == 1 else raw + b'\n'
    with pytest.raises(rehearsal.RehearsalRefused, match='rollback_response_bytes_changed'):
        _run(db, legacy_reader=unstable)
    assert len(calls) == 2 and _heads(conn) == before


def test_failure_during_reader_probe_rolls_back_and_preserves_callers_work(db, monkeypatch):
    conn, _ = db
    conn.execute("UPDATE public.kala_gochara_authority SET evidence_ref='caller-work' WHERE chart_id=%s", (CHART_ID,))
    before = _heads(conn)
    original = rehearsal.serving_reader.read_authoritative
    calls = []
    def broken(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            assert rehearsal.read_head(conn, CHART_ID).generation == '5.0'
            raise RuntimeError('reader failed after flip')
        return original(*args, **kwargs)
    monkeypatch.setattr(rehearsal.serving_reader, 'read_authoritative', broken)
    with pytest.raises(RuntimeError, match='reader failed'):
        _run(db)
    assert len(calls) == 2
    assert _heads(conn) == before


def test_retention_detector_rejects_mutated_rows_and_rolls_them_back(db):
    conn, _ = db
    before = _heads(conn)
    calls = []
    def destructive(c, chart_id, generation, **request):
        calls.append(1)
        if len(calls) == 1:
            c.execute('DELETE FROM public.kala_gochara_windows WHERE chart_id=%s', (chart_id,))
        return _legacy(c, chart_id, generation, **request)
    with pytest.raises(rehearsal.RehearsalRefused, match='retained_rows_changed'):
        _run(db, legacy_reader=destructive)
    assert _heads(conn) == before
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 1


def test_rehearsal_never_commits_an_autocommit_connection(rehearsal_database):
    conn, mids = rehearsal_database
    assert conn.autocommit
    before = _heads(conn)
    _run((conn, mids))
    assert _heads(conn) == before


def test_even_successful_probe_side_effects_are_discarded(rehearsal_database):
    conn, mids = rehearsal_database
    assert conn.autocommit
    def side_effect(*args, **kwargs):
        conn.execute('CREATE TABLE IF NOT EXISTS public.j6r_probe_side_effect (n integer)')
        conn.execute('INSERT INTO public.j6r_probe_side_effect VALUES (1)')
        return _legacy(*args, **kwargs)
    _run((conn, mids), legacy_reader=side_effect)
    assert conn.execute("SELECT to_regclass('public.j6r_probe_side_effect')").fetchone()[0] is None


@pytest.mark.parametrize('corruption', ['manifest', 'generation', 'refusal', 'horizon'])
def test_served_identity_admission_and_horizon_are_measured_not_assumed(db, monkeypatch, corruption):
    conn, _ = db
    before = _heads(conn)
    original = rehearsal.serving_reader.read_authoritative
    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        if isinstance(result, dict):
            if corruption == 'manifest':
                result['manifest_id'] = str(uuid.uuid4())
            elif corruption == 'generation':
                result['generation'] = '9.9'
            elif corruption == 'refusal':
                result['refusal'] = {'code': 'not_sealed'}
            elif 'at_instant' in kwargs:
                result['refusal'] = None
        return result
    monkeypatch.setattr(rehearsal.serving_reader, 'read_authoritative', corrupt)
    reason = 'outside_horizon_probe_failed' if corruption == 'horizon' else 'flipped_reader_identity_or_admission_failed'
    with pytest.raises(rehearsal.RehearsalRefused, match=reason):
        _run(db)
    assert _heads(conn) == before


def test_maintenance_database_is_refused_before_authority_access(rehearsal_database):
    # conn.info.dsn omits the password required by CI's disposable Postgres.
    with guarded_admin_connect(ADMIN_DSN) as maintenance:
        with pytest.raises(rehearsal.RehearsalRefused, match='not_a_lane_database'):
            _run((maintenance, rehearsal_database[1]))


# These exercise the executor's actual adapter against PostgreSQL. Reverting its
# CAS, dry-run rollback, retained-row check or source binding breaks the oracle.
@pytest.fixture(autouse=True)
def operation_root(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))


def _operation_module():
    from scripts.kala_gochara_cutover import authority_operation
    return authority_operation


def _op_request(kind, args, operation='flip-fixture'):
    return {'operation_id': operation, 'request_id': 'request-' + operation,
            'kind': kind, 'chart_id': CHART_ID, 'args': args, 'reviewed_commit': 'a'*40}


def _publish_args(conn, mids):
    op = _operation_module()
    return {'generation': '5.0', 'manifest-id': mids['5.0'],
            'expected-head': op.head_digest(op.head_dict(rehearsal.read_head(conn, CHART_ID)))}


def test_executor_publish_dryrun_and_execute_then_bound_rollback_restore_full_head(rehearsal_database, tmp_path):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = _publish_args(conn, mids)
    dry = op.apply(conn, _op_request('publish_head_dryrun', args), dry_run=True)
    assert dry['status'] == 'ROLLED_BACK'
    assert rehearsal.read_head(conn, CHART_ID) == previous
    proof = None
    try:
        proof = op.apply(conn, _op_request('publish_head', args), dry_run=False)
        assert proof['status'] == 'COMMITTED'
        assert proof['before'] == op.head_dict(previous)
        assert proof['after']['generation'] == '5.0'
        assert proof['retained_before'] == proof['retained_after']
        root = tmp_path / 'run/ops/receipts'
        root.mkdir(parents=True)
        raw = json.dumps(proof).encode()
        (root / 'flip-fixture.output.txt').write_bytes(raw)
        (root / 'flip-fixture.json').write_text(json.dumps({
            'operation_id': 'flip-fixture', 'kind': 'publish_head', 'status': 'COMPLETED', 'exit_code': 0,
            'request_sha256': proof['request_sha256'], 'output_sha256': hashlib.sha256(raw).hexdigest()}))
        rb_args = {'generation': '3.0', 'expected-head': op.head_digest(proof['after']),
                   'source-operation': 'flip-fixture', 'source-sha256': hashlib.sha256(raw).hexdigest()}
        rb_req = _op_request('rollback_head_dryrun', rb_args, 'rollback-fixture')
        dry_rb = op.apply(conn, rb_req, dry_run=True, evidence_root=root)
        assert dry_rb['status'] == 'ROLLED_BACK'
        assert rehearsal.read_head(conn, CHART_ID).generation == '5.0'
        rb_req['kind'] = 'rollback_head'
        rolled = op.apply(conn, rb_req, dry_run=False, evidence_root=root)
        assert rolled['after'] == proof['before']
        assert rehearsal.read_head(conn, CHART_ID) == previous
        assert _legacy(conn, CHART_ID, '3.0') == b'{"generation":"3.0","stored_rows":[["3.0"]]}'
    finally:
        # Fixture cleanup uses the complete retained row, even on test failure.
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=%s,'
                     ' flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


@pytest.mark.parametrize('damage', ['head', 'manifest', 'unsealed', 'slice', 'extra_arg', 'request_kind', 'dryrun_kind'])
def test_executor_publish_refuses_stale_or_unqualified_requests_before_change(rehearsal_database, damage):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = _publish_args(conn, mids)
    req = _op_request('publish_head', args)
    if damage == 'head': args['expected-head'] = '0' * 64
    elif damage == 'manifest': args['manifest-id'] = str(uuid.uuid4())
    elif damage in ('unsealed', 'slice'):
        args.update(generation='5.2' if damage == 'unsealed' else '5.3',
                    **{'manifest-id': mids['5.2' if damage == 'unsealed' else '5.3']})
    elif damage == 'extra_arg': args['sql'] = 'DELETE'
    elif damage == 'request_kind': req['kind'] = 'layer_publish'
    elif damage == 'dryrun_kind': req['kind'] = 'publish_head_dryrun'
    with pytest.raises(op.OperationRefused):
        op.apply(conn, req, dry_run=False)
    assert rehearsal.read_head(conn, CHART_ID) == previous


def test_executor_rollback_refuses_unbound_source_without_mutation(rehearsal_database, tmp_path):
    op = _operation_module()
    conn, _ = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = {'generation': 'v1', 'expected-head': op.head_digest(op.head_dict(previous)),
            'source-operation': '../escape', 'source-sha256': '0' * 64}
    with pytest.raises(op.OperationRefused):
        op.apply(conn, _op_request('rollback_head', args), dry_run=False, evidence_root=tmp_path)
    assert rehearsal.read_head(conn, CHART_ID) == previous


@pytest.mark.parametrize('damage', ['source_hash', 'receipt_hash', 'request_hash', 'operation',
                                    'dryrun_source', 'head', 'generation'])
def test_executor_rollback_rejects_each_changed_source_binding(rehearsal_database, tmp_path, damage):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    try:
        proof = op.apply(conn, _op_request('publish_head', _publish_args(conn, mids)), dry_run=False)
        root = tmp_path
        args = {'generation': '3.0', 'expected-head': op.head_digest(proof['after']),
                'source-operation': 'flip-fixture', 'source-sha256': ''}
        if damage == 'operation': proof['operation_id'] = 'other'
        elif damage == 'dryrun_source': proof['status'] = 'ROLLED_BACK'
        elif damage == 'head': args['expected-head'] = '0'*64
        elif damage == 'generation': args['generation'] = 'v1'
        raw = json.dumps(proof).encode(); sha = hashlib.sha256(raw).hexdigest()
        args['source-sha256'] = '0'*64 if damage == 'source_hash' else sha
        (root/'flip-fixture.output.txt').write_bytes(raw)
        (root/'flip-fixture.json').write_text(json.dumps({
            'operation_id': 'flip-fixture', 'kind': 'publish_head', 'status': 'COMPLETED', 'exit_code': 0,
            'request_sha256': '0'*64 if damage == 'request_hash' else proof['request_sha256'],
            'output_sha256': '0'*64 if damage == 'receipt_hash' else sha}))
        current = rehearsal.read_head(conn, CHART_ID)
        with pytest.raises(op.OperationRefused):
            op.apply(conn, _op_request('rollback_head', args, 'rollback-fixture'), dry_run=False, evidence_root=root)
        assert rehearsal.read_head(conn, CHART_ID) == current
    finally:
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
                     'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


def test_executor_detects_retained_row_mutation_and_discards_the_whole_flip(rehearsal_database):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    conn.execute("CREATE FUNCTION pg_temp.j6mr_destructive() RETURNS trigger LANGUAGE plpgsql AS $$"
                 " BEGIN DELETE FROM public.kala_gochara_windows; RETURN NEW; END $$")
    conn.execute('CREATE TRIGGER j6mr_destructive AFTER UPDATE ON public.kala_gochara_authority'
                 ' FOR EACH ROW EXECUTE FUNCTION pg_temp.j6mr_destructive()')
    try:
        with pytest.raises(op.OperationRefused, match='retained_rows_readback_failed'):
            op.apply(conn, _op_request('publish_head', _publish_args(conn, mids)), dry_run=False)
        assert rehearsal.read_head(conn, CHART_ID) == previous
        assert conn.execute('SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id=%s',
                            (CHART_ID,)).fetchone()[0] == 1
    finally:
        conn.execute('DROP TRIGGER j6mr_destructive ON public.kala_gochara_authority')


def test_executor_cli_checks_transport_before_connect_and_redacts_faults(rehearsal_database, monkeypatch, capsys):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = _publish_args(conn, mids)
    req = _op_request('publish_head_dryrun', args)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    # This DSN is ONLY the fixture's guarded loopback database.
    monkeypatch.setenv('DATABASE_URL', conn.info.dsn)
    argv = ['--kind', 'publish_head', '--dry-run']
    for key, value in args.items(): argv.extend(['--' + key, value])
    assert op.main(argv) == 0
    proof = json.loads(capsys.readouterr().out)
    assert proof['status'] == 'ROLLED_BACK' and proof['operation_id'] == req['operation_id']
    assert rehearsal.read_head(conn, CHART_ID) == previous
    argv[argv.index('--expected-head') + 1] = '0'*64
    # The accepted request remains valid; only CLI transport differs.
    assert op.main(argv) == 2
    captured = capsys.readouterr()
    assert 'executor_transport_mismatch' not in captured.err  # only error class, no sensitive exception detail
    assert 'OperationRefused' in captured.err and captured.out == ''
    assert rehearsal.read_head(conn, CHART_ID) == previous


def test_executor_persists_previous_full_head_before_commit_and_never_overwrites_intent(rehearsal_database, tmp_path):
    import os
    from pathlib import Path
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = _publish_args(conn, mids)
    req = _op_request('publish_head', args)
    journal = Path(os.environ['KY_ROOT'])/'run/ops/authority-intents/flip-fixture.json'
    journal.parent.mkdir(parents=True)
    journal.write_bytes(b'preexisting ambiguous operation')
    with pytest.raises(op.OperationRefused, match='intent_already_exists'):
        op.apply(conn, req, dry_run=False)
    assert journal.read_bytes() == b'preexisting ambiguous operation'
    assert rehearsal.read_head(conn, CHART_ID) == previous
    journal.unlink()
    try:
        proof = op.apply(conn, req, dry_run=False)
        intent = json.loads(journal.read_bytes())
        assert intent['status'] == 'PREPARED'
        assert intent['before'] == proof['before'] == op.head_dict(previous)
        assert intent['after'] == proof['after']
        assert intent['request_sha256'] == proof['request_sha256']
        assert intent['operation_id'] == req['operation_id']
    finally:
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
                     'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


@pytest.mark.parametrize('column,value', [('flipped_by', 'another-operator'), ('evidence_ref', 'another-proof'),
                                         ('flipped_at', '2026-01-01 UTC')])
def test_executor_cas_refuses_change_to_any_audit_column(rehearsal_database, column, value):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    args = _publish_args(conn, mids)
    try:
        # Identifiers come exclusively from the fixed parametrization above.
        conn.execute(f'UPDATE public.kala_gochara_authority SET {column}=%s WHERE chart_id=%s', (value, CHART_ID))
        changed = rehearsal.read_head(conn, CHART_ID)
        with pytest.raises(op.OperationRefused, match='head_compare_and_swap_conflict'):
            op.apply(conn, _op_request('publish_head', args), dry_run=False)
        assert rehearsal.read_head(conn, CHART_ID) == changed
    finally:
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
                     'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


def test_executor_cli_execute_requires_actual_accepted_same_head_dryrun(rehearsal_database, monkeypatch, capsys):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    req = _op_request('publish_head', _publish_args(conn, mids))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    monkeypatch.setenv('DATABASE_URL', conn.info.dsn)
    argv = ['--kind', 'publish_head', '--execute']
    for key, value in req['args'].items(): argv.extend(['--'+key, value])
    try:
        assert op.main(argv) == 2
        assert 'OperationRefused' in capsys.readouterr().err
        assert rehearsal.read_head(conn, CHART_ID) == previous
    finally:
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
                     'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


def _store_operation_output(root, req, raw, *, accepted=False):
    import pathlib
    root = pathlib.Path(root)/'run/ops'
    rec = root/'receipts'; rec.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(raw).hexdigest()
    proof = json.loads(raw)
    (rec/(req['operation_id']+'.output.txt')).write_bytes(raw)
    (rec/(req['operation_id']+'.json')).write_text(json.dumps({
        'operation_id': req['operation_id'], 'kind': req['kind'], 'status': 'COMPLETED', 'exit_code': 0,
        'reviewed_commit': req['reviewed_commit'], 'request_sha256': proof['request_sha256'], 'output_sha256': sha}))
    if accepted:
        acc = root/'acceptance'; acc.mkdir(parents=True, exist_ok=True)
        (acc/(req['operation_id']+'.json')).write_text(json.dumps({
            'operation_id': req['operation_id'], 'result': 'ACCEPTED', 'by': 'v2',
            'reviewed_commit': req['reviewed_commit'], 'request_sha256': proof['request_sha256'], 'output_sha256': sha}))
    return sha


def test_executor_real_cli_dryrun_flip_and_retained_head_rollback_chain(rehearsal_database, tmp_path, monkeypatch, capsys):
    op = _operation_module()
    conn, mids = rehearsal_database
    previous = rehearsal.read_head(conn, CHART_ID)
    before_bytes = _legacy(conn, CHART_ID, previous.generation)
    monkeypatch.setenv('DATABASE_URL', conn.info.dsn)
    def invoke(req):
        monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
        dry = req['kind'].endswith('_dryrun')
        argv = ['--kind', req['kind'].removesuffix('_dryrun'), '--dry-run' if dry else '--execute']
        for key,value in req['args'].items(): argv.extend(['--'+key,value])
        assert op.main(argv) == 0
        return capsys.readouterr().out.encode()
    try:
        args = _publish_args(conn, mids)
        dry_req = _op_request('publish_head_dryrun', args, 'publish-dry')
        dry_raw = invoke(dry_req)
        dry_sha = _store_operation_output(tmp_path, dry_req, dry_raw, accepted=True)
        publish_req = _op_request('publish_head', args, 'publish-real')
        publish_req.update(dryrun_operation='publish-dry', dryrun_output_sha256=dry_sha)
        raw = invoke(publish_req)
        flip_sha = _store_operation_output(tmp_path, publish_req, raw)
        flipped = json.loads(raw)
        assert rehearsal.read_head(conn, CHART_ID).generation == '5.0'
        served = rehearsal.serving_reader.read_authoritative(conn, CHART_ID, legacy_reader=_legacy,
                                                              event_classes=['marriage'])
        assert served['generation'] == '5.0' and served['manifest_id'] == mids['5.0']
        # This metadata fixture is still stale_binding, not G6 acceptance.
        assert served['classes'][0]['completeness'] == 'stale_binding'
        rb_args = {'generation': previous.generation, 'expected-head': op.head_digest(flipped['after']),
                   'source-operation': 'publish-real', 'source-sha256': flip_sha}
        dry_req = _op_request('rollback_head_dryrun', rb_args, 'rollback-dry')
        dry_raw = invoke(dry_req)
        dry_sha = _store_operation_output(tmp_path, dry_req, dry_raw, accepted=True)
        rb_req = _op_request('rollback_head', rb_args, 'rollback-real')
        rb_req.update(dryrun_operation='rollback-dry', dryrun_output_sha256=dry_sha)
        restored_raw = invoke(rb_req)
        _store_operation_output(tmp_path, rb_req, restored_raw)
        restored = json.loads(restored_raw)
        assert restored['after'] == flipped['before']
        assert rehearsal.read_head(conn, CHART_ID) == previous
        after = rehearsal.serving_reader.read_authoritative(conn, CHART_ID, legacy_reader=_legacy)
        assert after == before_bytes
        import base64
        (tmp_path/'component-evidence.json').write_text(json.dumps({
            'schema': 'ky.j6mr_component_rehearsal/1', 'fixture_only': True, 'acceptance': None,
            'production_activated': False, 'synthetic_admission_metadata': True,
            'transport': 'in_process_authority_reader', 'legacy_transport': 'stored_row_test_fixture',
            'before_response_base64': base64.b64encode(before_bytes).decode(),
            'after_response_base64': base64.b64encode(after).decode(),
            'flipped_response': served, 'rollback_bytes_equal': after == before_bytes,
            'previous_head_restored': rehearsal.read_head(conn, CHART_ID) == previous,
            'retained_rows_equal': flipped['retained_before'] == flipped['retained_after']
                                   == restored['retained_before'] == restored['retained_after'],
            'operation_ids': ['publish-dry', 'publish-real', 'rollback-dry', 'rollback-real'],
        }, sort_keys=True, indent=2) + '\n')
    finally:
        conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
                     'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                     (previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref, CHART_ID))


@pytest.mark.parametrize('damage', ['args', 'output_sha256', 'kind', 'reviewed_commit', 'status', 'approval'])
def test_executor_cli_rejects_changed_dryrun_binding(rehearsal_database, tmp_path, damage):
    op = _operation_module()
    conn, mids = rehearsal_database
    args = _publish_args(conn, mids)
    dry_req = _op_request('publish_head_dryrun', args, 'publish-dry')
    proof = op.apply(conn, dry_req, dry_run=True)
    raw = json.dumps(proof).encode()
    sha = _store_operation_output(tmp_path, dry_req, raw, accepted=True)
    req = _op_request('publish_head', dict(args), 'publish-real')
    req.update(dryrun_operation='publish-dry', dryrun_output_sha256=sha)
    if damage == 'args': req['args']['expected-head'] = '0'*64
    elif damage == 'output_sha256': req['dryrun_output_sha256'] = '0'*64
    elif damage == 'reviewed_commit': req['reviewed_commit'] = 'b'*40
    elif damage == 'kind': req['kind'] = 'rollback_head'
    else:
        path = tmp_path/'run/ops'/('receipts' if damage == 'status' else 'acceptance')/'publish-dry.json'
        value = json.loads(path.read_text()); value['status' if damage == 'status' else 'result'] = 'FAILED'
        path.write_text(json.dumps(value))
    with pytest.raises(op.OperationRefused):
        op.check_execution_bindings(req, tmp_path/'run/ops')
