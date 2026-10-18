"""J-1a lane admission, endpoint isolation and measured executor receipts."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[1]
ROOT = FLEET.parents[3]
sys.path.insert(0, str(FLEET))
KINDS = ('backup_snapshot', 'backup_restore_verify', 'smalltest_dispatch_dryrun',
         'smalltest_dispatch', 'smalltest_teardown_dryrun', 'smalltest_teardown')


def load(name):
    spec = importlib.util.spec_from_file_location(name, FLEET / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def request(kind):
    args = {'label': 'j1a_lane'} if kind.startswith('backup_') else (
        {'run': 'one_class_full', 'classes': 'marriage'} if 'dispatch' in kind else {})
    return dict(operation_id='lane-' + kind, request_id='request-' + kind, kind=kind,
                item_id='J-1a', idempotency_key='j1a-' + kind, requested_by='adhikarin', kyd='J-1a',
                chart_id='482012f1-710e-4a25-994a-93821f5871aa', reviewed_commit='a' * 40,
                expires_at='2099-01-01T00:00:00+00:00', dry_run=True,
                lane_target=dict(host='127.0.0.1', port=55433, database='ky_j1a'), args=args)


@pytest.fixture
def ex(tmp_path, monkeypatch):
    mod = load('executor')
    monkeypatch.setattr(mod, 'seen', lambda _: False)
    def git(*args, **kw):
        if args[0] == 'show' and args[1].endswith('executor_ops.json'):
            return SimpleNamespace(returncode=0, stdout=(FLEET / 'executor_ops.json').read_text())
        if args[0] == 'show' and args[1].endswith('v5_small_test_shared.py'):
            return SimpleNamespace(returncode=0, stdout=(ROOT / 'platform/scripts/v5_small_test_shared.py').read_text())
        return SimpleNamespace(returncode=0, stdout='')
    monkeypatch.setattr(mod, 'git', git)
    monkeypatch.setattr(mod, 'REC', tmp_path)
    monkeypatch.setattr(mod, 'log', lambda *a: None)
    return mod


@pytest.fixture
def table():
    return json.loads((FLEET / 'executor_ops.json').read_text())['ops']


@pytest.mark.parametrize('kind', KINDS)
def test_six_local_lane_requests_need_no_production_capability(ex, table, kind):
    assert ex.validate(request(kind), table, {'none': True}) is None


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('target', [dict(host='production.example', port=55433, database='ky_j1a'),
    dict(host='127.0.0.1', port=55433, database='amjis'),
    dict(host='127.0.0.1', port=5432, database='ky_j1a'),
    dict(host='127.0.0.1,production.example', port=55433, database='ky_j1a'),
    dict(host='127.0.0.1', port=55433, database='ky_x', service='prod'), None, {}, 'ky_j1a'])
def test_lane_endpoint_guard_refuses_before_execution(ex, table, kind, target):
    req = request(kind); req['lane_target'] = target
    problem = ex.validate(req, table, {'none': True})
    assert problem is not None and 'lane target' in problem


@pytest.mark.parametrize('kind', KINDS)
def test_dry_run_requires_lane_target(ex, table, kind, monkeypatch):
    # A fully admissible production control prevents another missing privilege
    # or approval from masking removal of the lane-selector guard.
    req = request(kind); req.pop('lane_target'); req.pop('dry_run')
    monkeypatch.setattr(ex, 'lease_live', lambda _: True)
    monkeypatch.setattr(ex, 'smalltest_policy_problem', lambda _: None)
    monkeypatch.setattr(ex, 'ACC', ex.REC / 'acceptance'); ex.ACC.mkdir()
    req.update(lease_id='fixture', acceptance_receipt=str(ex.ACC / 'approval.json'))
    def authorize():
        (ex.ACC / 'approval.json').write_text(json.dumps(dict(result='ACCEPTED', by='v1',
            operation_id=req['operation_id'], reviewed_commit=req['reviewed_commit'], ts=ex.now(),
            request_sha256=ex.request_digest(req), rows={key: True for key in ['2', '3', '7', '9', '11']},
            checks=dict(backup_taken=True, restore_verified=True, dry_run_passed=True))))
    caps = dict(owner=True, builder=True, gcloud=True, none=True)
    authorize(); assert ex.validate(req, table, caps) is None
    req['dry_run'] = True; authorize()
    assert ex.validate(req, table, caps) == 'dry_run requires an explicit lane target'


@pytest.mark.parametrize('kind', KINDS)
@pytest.mark.parametrize('mode', [False, None, 'true', 1])
def test_lane_target_requires_literal_dry_run(ex, table, kind, mode):
    req = request(kind); req['dry_run'] = mode
    assert ex.validate(req, table, {'none': True}) == 'lane target requires dry_run=true'


def test_lane_reviewed_source_must_be_merged_and_have_both_scripts(ex, table, monkeypatch):
    req = request('backup_snapshot')
    monkeypatch.setattr(ex, 'git', lambda *a, **k: SimpleNamespace(returncode=int(a[0] == 'merge-base'), stdout=''))
    assert 'not merged' in ex.validate(req, table, {'none': True})
    monkeypatch.setattr(ex, 'git', lambda *a, **k: SimpleNamespace(returncode=int(a[0] == 'cat-file'), stdout=''))
    assert 'does not exist' in ex.validate(req, table, {'none': True})


def test_lane_refuses_replay_disabled_kind_and_unlisted_args(ex, table):
    req = request('backup_snapshot'); req['args']['execute'] = 'true'
    assert 'disallowed args' in ex.validate(req, table, {'none': True})
    req = request('backup_snapshot'); table[req['kind']]['enabled'] = False
    assert 'not enabled' in ex.validate(req, table, {'none': True})
    table[req['kind']]['enabled'] = True
    ex.seen = lambda _: True
    assert 'already used' in ex.validate(request('backup_snapshot'), table, {'none': True})


def test_lane_dispatch_does_not_admit_measuring_phase(ex, table):
    req = request('smalltest_dispatch'); req['args'] = dict(run='all_classes_full', classes='all')
    assert 'measuring phase is disabled' in ex.validate(req, table, {'none': True})


def test_lane_readback_uses_existing_enabled_kind_without_arbitrary_sql(ex, table):
    req = request('readback_sql'); req.update(requested_by='v1', args={})
    assert ex.validate(req, table, {'none': True}) is None
    req['args'] = {'sql_file': 'anything.sql'}
    assert 'lane readback takes no SQL' in ex.validate(req, table, {'none': True})


def test_child_routing_never_inherits_credentials_or_connection_overrides(ex, table, monkeypatch, tmp_path):
    monkeypatch.setenv('KY_OWNER_DATABASE_URL', 'DO_NOT_FORWARD')
    monkeypatch.setenv('KY_BUILDER_DATABASE_URL', 'DO_NOT_FORWARD')
    monkeypatch.setenv('PGSERVICE', 'DO_NOT_FORWARD')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', 'DO_NOT_FORWARD')
    env = ex.lane_child_env(request('backup_snapshot'), tmp_path)
    assert 'DO_NOT_FORWARD' not in json.dumps(env)
    assert env['PGPASSFILE'] == '/dev/null'
    assert 'DATABASE_URL' not in env  # adapter creates its own fixed local conninfo
    assert env['TMPDIR'] == str(tmp_path)


@pytest.mark.parametrize('kind', KINDS)
def test_lane_receipt_requires_bound_independent_readback(ex, table, kind):
    req = request(kind)
    proof = dict(schema='ky.smalltest_lane/1', operation_id=req['operation_id'], request_id=req['request_id'],
        request_sha256=ex.request_digest(req), reviewed_commit=req['reviewed_commit'], kind=kind,
        lane_target=req['lane_target'], dry_run=True, status='DRY_RUN_VERIFIED',
        script=table[kind]['script'], script_sha256='b' * 64, child_output_sha256='c' * 64,
        before_sha256='d' * 64, after_sha256='d' * 64, unchanged=True, independent_readback=True)
    ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps(proof))
    value = json.loads((ex.REC / (req['operation_id'] + '.json')).read_text())
    assert value['status'] == 'COMPLETED' and value['request_id'] == req['request_id']
    assert value['lane'] == proof and len(value['evidence_sha256']) == 64
    assert 'launch' not in value and 'teardown' not in value
    for field, wrong in [('request_id', 'other'), ('independent_readback', False), ('unchanged', False),
                         ('after_sha256', 'e' * 64), ('lane_target', {}), ('script', 'other.py')]:
        ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps({**proof, field: wrong}))
        assert json.loads((ex.REC / (req['operation_id'] + '.json')).read_text())['status'] == 'FAILED'
    ex.receipt(req, 'COMPLETED', rc=0, out='no proof')
    assert json.loads((ex.REC / (req['operation_id'] + '.json')).read_text())['status'] == 'FAILED'


def test_local_empty_teardown_exception_never_grants_execute_authority(monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / 'platform/scripts'))
    import v5_small_test_shared as shared
    from psycopg.conninfo import make_conninfo
    ex = load('executor')
    req = request('smalltest_teardown_dryrun'); req['smalltest_scope'] = {'empty': True}
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    monkeypatch.setenv('DATABASE_URL', make_conninfo(**ex.lane_target_settings(req)))
    assert shared.lane_rehearsal_request() == req
    for change in [dict(kind='smalltest_teardown'), dict(dry_run=False), dict(smalltest_scope={'run_id': 'other'})]:
        monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps({**req, **change}))
        with pytest.raises(shared.Refused): shared.lane_rehearsal_request()
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    for dsn in ['host=production.example port=55433 dbname=ky_j1a',
                'host=127.0.0.1 port=55433 dbname=amjis',
                'host=127.0.0.1 port=55433 dbname=ky_j1a service=production']:
        monkeypatch.setenv('DATABASE_URL', dsn)
        with pytest.raises(shared.Refused): shared.lane_rehearsal_request()


@pytest.mark.parametrize('kind', KINDS)
def test_lane_child_cli_is_always_dry_run_and_never_execute(kind, table):
    adapter = load('lane_smalltest')
    argv = adapter.child_command(request(kind), table[kind])
    assert '--dry-run' in argv and '--execute' not in argv
    assert argv[1] == str(ROOT / table[kind]['script'])


def test_execute_revalidates_lane_before_export(ex, table, monkeypatch):
    req = request('backup_snapshot'); req['lane_target']['host'] = 'production.example'
    monkeypatch.setattr(ex.subprocess, 'run', lambda *a, **k: pytest.fail('must refuse before export or child'))
    rc, output = ex.execute(req, table[req['kind']])
    assert rc != 0 and 'lane target' in output


def test_adapter_refuses_changed_content_in_independent_readback(monkeypatch, tmp_path, table):
    import sys
    sys.path.insert(0, str(FLEET))
    adapter = load('lane_smalltest')
    req = request('backup_snapshot')
    monkeypatch.setenv('TMPDIR', str(tmp_path))
    calls = iter([{'rows': 'before'}, {'rows': 'after'}])
    monkeypatch.setattr(adapter, 'observe', lambda _: next(calls))
    monkeypatch.setattr(adapter.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='planned', stderr=''))
    with pytest.raises(ValueError, match='readback changed'):
        adapter.run(req)


def test_adapter_cli_requires_matching_lane_and_dry_run(monkeypatch, capsys):
    import sys
    sys.path.insert(0, str(FLEET))
    adapter = load('lane_smalltest')
    req = request('backup_snapshot')
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    monkeypatch.setattr(adapter, 'run', lambda _: pytest.fail('invalid selector must not execute'))
    assert adapter.cli(['--dry-run', '--lane-target', '{}']) == 1
    for argv in [[], ['--dry-run'], ['--lane-target', json.dumps(req['lane_target'])],
                 ['--dry-run', '--lane-target', json.dumps(req['lane_target']), '--execute']]:
        with pytest.raises(SystemExit): adapter.cli(argv)


def qualification(ex, target_request):
    refs = []
    for kind in KINDS:
        req = request(kind)
        output = 'measured-' + kind
        output_path = ex.REC / (req['operation_id'] + '.output.txt'); output_path.write_text(output)
        proof = dict(schema='ky.smalltest_lane/1', operation_id=req['operation_id'], request_id=req['request_id'],
            request_sha256=ex.request_digest(req), reviewed_commit=req['reviewed_commit'], kind=kind,
            lane_target=req['lane_target'], dry_run=True, status='DRY_RUN_VERIFIED',
            script_sha256='b' * 64, child_output_sha256='c' * 64,
            before_sha256='d' * 64, after_sha256='d' * 64, unchanged=True, independent_readback=True)
        record = dict(operation_id=req['operation_id'], request_id=req['request_id'], kind=kind,
            item_id='J-1a', status='COMPLETED', exit_code=0, reviewed_commit=req['reviewed_commit'],
            request_sha256=proof['request_sha256'], lane=proof,
            evidence_sha256=ex.digest_bytes(json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()),
            output_file=str(output_path), output_sha256=ex.digest_bytes(output.encode()))
        path = ex.REC / (req['operation_id'] + '.json'); body = json.dumps(record).encode(); path.write_bytes(body)
        refs.append(dict(name=path.name, sha256=ex.digest_bytes(body)))
    target_request['lane_receipts'] = refs
    return target_request


def test_final_independent_readback_binds_all_six_receipt_bytes(ex, table):
    req = qualification(ex, request('readback_sql')); req.update(requested_by='v1', args={})
    assert ex.validate(req, table, {'none': True}) is None
    observed = ex.lane_qualification(req)
    assert {r['kind'] for r in observed} == set(KINDS)
    for refs in [req['lane_receipts'][:-1], req['lane_receipts'] + req['lane_receipts'][:1],
                 req['lane_receipts'][:-1] + req['lane_receipts'][:1]]:
        bad = {**req, 'lane_receipts': refs}
        assert ex.validate(bad, table, {'none': True}) is None           # A8 §4: the ritual is no longer an admission precondition ...
        with pytest.raises(ValueError): ex.lane_qualification(bad)       # ... a request that still carries it is bound at execution and receipt
    output = ex.REC / 'lane-backup_snapshot.output.txt'; output.write_text('changed')
    assert ex.validate(req, table, {'none': True}) is None
    with pytest.raises(ValueError): ex.lane_qualification(req)


def test_qualification_refuses_cross_lane_or_changed_receipt_bytes(ex, table):
    req = qualification(ex, request('readback_sql')); req.update(requested_by='v1', args={})
    for mutation in ['hash', 'escape', 'target', 'source', 'failed', 'evidence']:
        bad = json.loads(json.dumps(req))
        ref = bad['lane_receipts'][0]
        if mutation == 'hash': ref['sha256'] = '0' * 64
        elif mutation == 'escape': ref['name'] = '../escape.json'
        else:
            path = ex.REC / ref['name']; original = path.read_bytes(); value = json.loads(original)
            if mutation == 'target': value['lane']['lane_target']['database'] = 'ky_other'
            elif mutation == 'source': value['reviewed_commit'] = '0' * 40
            elif mutation == 'failed': value['status'] = 'FAILED'
            elif mutation == 'evidence': value['evidence_sha256'] = '0' * 64
            body = json.dumps(value).encode(); path.write_bytes(body); ref['sha256'] = ex.digest_bytes(body)
        assert ex.validate(bad, table, {'none': True}) is None           # A8 §4: not an admission precondition ...
        with pytest.raises((ValueError, OSError, KeyError, TypeError)): ex.lane_qualification(bad)   # ... still refused where it is bound
        if mutation not in ('hash', 'escape'): path.write_bytes(original)


def test_executor_receipt_refuses_missing_six_entry_qualification(ex, table):
    req = qualification(ex, request('readback_sql')); req.update(requested_by='v1', args={})
    bundle = ex.lane_qualification(req)
    proof = dict(schema='ky.smalltest_lane/1', operation_id=req['operation_id'], request_id=req['request_id'],
        request_sha256=ex.request_digest(req), reviewed_commit=req['reviewed_commit'], kind=req['kind'],
        lane_target=req['lane_target'], dry_run=True, status='DRY_RUN_VERIFIED',
        script=table[req['kind']]['script'], script_sha256='b' * 64, child_output_sha256='c' * 64,
        before_sha256='d' * 64, after_sha256='d' * 64, unchanged=True, independent_readback=True,
        qualification=bundle, qualification_sha256=ex.digest_bytes(json.dumps(bundle, sort_keys=True, separators=(',', ':')).encode()))
    ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps(proof))
    path = ex.REC / (req['operation_id'] + '.json')
    assert json.loads(path.read_text())['status'] == 'COMPLETED'
    proof.pop('qualification')
    ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps(proof))
    assert json.loads(path.read_text())['status'] == 'FAILED'


@pytest.mark.parametrize('existing_fence', [False, True])
def test_interrupted_lane_never_takes_or_clears_production_fence(tmp_path, monkeypatch, existing_fence):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    ex = load('executor')
    ex.INFLIGHT.mkdir(parents=True)
    (ex.INFLIGHT / 'interrupted.json').write_text(json.dumps(request('backup_snapshot')))
    (ex.RUN / 'STOP_executor').touch()
    original = b'{"operation_id":"production-operation"}'
    if existing_fence: ex.FENCE.write_bytes(original)
    monkeypatch.setattr(ex, 'capabilities', lambda _: {'none': True})
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    assert ex.main() == 0
    assert ex.FENCE.exists() is existing_fence
    if existing_fence: assert ex.FENCE.read_bytes() == original
    result = json.loads((ex.REC / 'lane-backup_snapshot.json').read_text())
    assert result['status'] == 'INTERRUPTED' and result['production'] is False


def test_lane_queue_runs_with_retained_production_fence(tmp_path, monkeypatch, table):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    ex = load('executor')
    ex.REQ.mkdir(parents=True)
    req = request('backup_snapshot'); (ex.REQ / 'request.json').write_text(json.dumps(req))
    original = b'{"operation_id":"production-operation"}'
    ex.FENCE.write_bytes(original)
    submitted = []
    class Pool:
        def __init__(self, **kwargs): self.name = kwargs['thread_name_prefix']
        def submit(self, *args): submitted.append(self.name)
        def shutdown(self, **kwargs): pass
    monkeypatch.setattr(ex.cf, 'ThreadPoolExecutor', Pool)
    monkeypatch.setattr(ex, 'capabilities', lambda _: {'none': True})
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    monkeypatch.setattr(ex, 'sync', lambda: None)
    monkeypatch.setattr(ex, 'load_table', lambda: table)
    monkeypatch.setattr(ex, 'refresh_from_main_or_fail_closed', lambda: True)
    monkeypatch.setattr(ex, 'fence_quiescent', lambda: False)
    monkeypatch.setattr(ex, 'git', lambda *a, **kw: SimpleNamespace(returncode=0, stdout=''))
    monkeypatch.setattr(ex.time, 'sleep', lambda _: (ex.RUN / 'STOP_executor').touch())
    assert ex.main() == 0
    assert submitted == ['read'] and ex.FENCE.read_bytes() == original


@pytest.mark.parametrize('endpoint', [('amjis', '127.0.0.1', 55433), ('ky_j1a', '10.0.0.1', 55433),
                                     ('ky_j1a', '127.0.0.1', 5432)])
def test_observer_checks_actual_server_before_measurements(monkeypatch, endpoint):
    import psycopg
    adapter = load('lane_smalltest')
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, *args): return self
        def fetchone(self): return endpoint
    monkeypatch.setattr(psycopg, 'connect', lambda **kwargs: Connection())
    monkeypatch.setattr(adapter.backup, 'measurements', lambda _: pytest.fail('unverified endpoint must never be measured'))
    with pytest.raises(ValueError, match='server identity differs'):
        adapter.observe(request('backup_snapshot'))


@pytest.mark.parametrize('value', [[], None, 'bad receipt', {'lane': []}, {'lane': True}, {'lane': 'bad proof'}])
def test_qualification_malformed_json_shapes_refuse_without_crashing(ex, table, value):
    req = qualification(ex, request('readback_sql')); req.update(requested_by='v1', args={})
    ref = req['lane_receipts'][0]
    path = ex.REC / ref['name']
    if isinstance(value, dict): value = {**json.loads(path.read_text()), **value}
    body = json.dumps(value).encode(); path.write_bytes(body)
    ref['sha256'] = ex.digest_bytes(body)
    assert ex.validate(req, table, {'none': True}) is None               # A8 §4: not an admission precondition ...
    with pytest.raises((ValueError, OSError, KeyError, TypeError)): ex.lane_qualification(req)   # ... still refused, without crashing, where it is bound
