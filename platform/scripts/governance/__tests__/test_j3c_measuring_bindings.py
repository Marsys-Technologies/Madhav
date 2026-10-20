"""Offline measuring authority proofs; auto-discovered by governance CI shards.

No cloud, Git writes, DB connections or canonical chart computations. Evidence
is explicitly synthetic transport data, never operational acceptance.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
SCRIPTS = ROOT / 'platform/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / '__tests__'))
sys.path.insert(0, str(FLEET))
import v5_small_test_shared as shared
import smalltest_safety_support as S


def load(name):
    path = FLEET / (name + '.py')
    assert path.is_file(), f'missing measuring implementation: {path}'
    spec = importlib.util.spec_from_file_location('j3c_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize('kind,script,needs', [
    ('measuring_dispatch', 'measuring_launch.py', 'builder'),
    ('measuring_dispatch_dryrun', 'dispatch_v5_measuring_job.py', 'builder'),
    ('measuring_teardown', 'teardown_v5_small_test_job.py', 'owner'),
    ('measuring_teardown_dryrun', 'teardown_v5_small_test_job.py', 'owner'),
])
def test_measuring_bindings_are_real_and_enabled_by_j3a(kind, script, needs):
    ops = json.loads((FLEET / 'executor_ops.json').read_text())['ops']
    assert kind in ops, f'missing dedicated measuring kind {kind}'
    op = ops[kind]
    assert op['enabled'] is True                                                         # J-3a enabled the four measuring kinds
    assert op['production'] is (not kind.endswith('_dryrun')) and op['needs'] == needs   # A8 §3.8: a dry run is read-only with a credential
    assert op['script'].endswith('/' + script) and (ROOT / op['script']).is_file()
    assert 'required_rows' not in op                                                     # A8 §5: retired
    assert op['allowed_args'] == (['run', 'classes'] if 'dispatch' in kind else [])
    if kind == 'measuring_dispatch':
        assert op['also_needs'] == ['gcloud'] and op['remote_async'] is True             # A8 §3.11: the remote launch takes the fence
    executor = load('executor')
    req = dict(operation_id='fixture', kind=kind, item_id='J-3c', idempotency_key='fixture', requested_by='adhikarin', kyd='fixture')
    caps = {'builder': True, 'owner': True, 'gcloud': True}
    assert 'not enabled' not in executor.validate(req, ops, caps)                        # enabled: the refusal is for the missing evidence, not the table
    assert executor.validate(req, {**ops, kind: {**op, 'enabled': False}}, caps).startswith(f'kind {kind} is not enabled')


def test_measuring_receipt_requires_launch_record_and_cannot_replay_smalltest(tmp_path, monkeypatch):
    executor = load('executor')
    monkeypatch.setattr(executor, 'REC', tmp_path)
    monkeypatch.setattr(executor, 'log', lambda *a: None)
    req = dict(operation_id='launch', kind='measuring_dispatch', item_id='J-3c')
    body = dict(schema='ky.measuring_launch/1', status='LAUNCHED', run_id=S.RUN, chart_id=shared.CHART_ID,
        asset_id=shared.ASSET_ID, plan_manifest_digest='a' * 64, execution_name='brahma-build-pipeline-job-fixture')
    for output in (S.RUN, json.dumps({**body, 'schema': 'ky.smalltest_launch/1'}), json.dumps(body) + '\n' + json.dumps(body)):
        executor.receipt(req, 'COMPLETED', rc=0, out=output)
        assert json.loads((tmp_path / 'launch.json').read_text())['status'] == 'FAILED'
    executor.receipt(req, 'COMPLETED', rc=0, out=json.dumps(body))
    assert json.loads((tmp_path / 'launch.json').read_text())['launch'] == body


def measuring_scope(root):
    rr, ar = S.accepted(root, 'measuring_dispatch', 'launch', item_id='J-3c', launch=dict(
        schema='ky.measuring_launch/1', status='LAUNCHED', run_id=S.RUN, chart_id=shared.CHART_ID,
        asset_id=shared.ASSET_ID, plan_manifest_digest='a' * 64, execution_name='brahma-build-pipeline-job-fixture'))
    return dict(run_id=S.RUN, chart_id=shared.CHART_ID, generation='5.0', asset_id=shared.ASSET_ID,
        manifest_id='22222222-2222-4222-8222-222222222222', input_vector_sha256='c' * 64,
        plan_manifest_digest='a' * 64, dispatch_receipt=rr, dispatch_acceptance=ar)


def test_measuring_scope_accepts_j3c_and_requires_candidate_vector(tmp_path):
    scope = measuring_scope(tmp_path)
    req = dict(kind='measuring_teardown_dryrun', item_id='J-3d', measuring_scope=scope)
    assert shared.staged_scope(req, tmp_path / 'run/ops') == scope
    for field in ('manifest_id', 'input_vector_sha256'):
        bad = copy.deepcopy(req); bad['measuring_scope'][field] = None
        with pytest.raises(shared.Refused):
            shared.staged_scope(bad, tmp_path / 'run/ops')
    with pytest.raises(shared.Refused):
        shared.staged_scope(dict(kind='smalltest_teardown', smalltest_scope=scope), tmp_path / 'run/ops')


@pytest.mark.parametrize('change', ['item', 'kind', 'schema', 'run', 'digest', 'execution'])
def test_measuring_scope_rejects_cross_identity_launch(tmp_path, change):
    scope = measuring_scope(tmp_path)
    p = tmp_path / 'run/ops/receipts/launch.json'
    r = json.loads(p.read_text())
    if change == 'item': r['item_id'] = 'J-2a'
    elif change == 'kind': r['kind'] = 'smalltest_dispatch'
    elif change == 'schema': r['launch']['schema'] = 'ky.smalltest_launch/1'
    elif change == 'run': r['launch']['run_id'] = '22222222-2222-4222-8222-222222222222'
    elif change == 'digest': r['launch']['plan_manifest_digest'] = 'b' * 64
    else: r['launch']['execution_name'] = 'other-job-fixture'
    scope['dispatch_receipt'] = S.put(tmp_path, 'receipts', 'launch', r)
    with pytest.raises(shared.Refused):
        shared.staged_scope(dict(kind='measuring_teardown', item_id='J-3d', measuring_scope=scope), tmp_path / 'run/ops')


def teardown_request(root):
    scope = measuring_scope(root)
    req = dict(operation_id='apply', kind='measuring_teardown', item_id='J-3d', measuring_scope=scope)
    req['dryrun_receipt'], req['dryrun_acceptance'] = S.accepted(root, 'measuring_teardown_dryrun', 'rollback', item_id='J-3d',
        teardown=dict(schema='ky.measuring_teardown/1', status='ROLLED_BACK', rollback_confirmed=True,
        operation_id='rollback', request_sha256='b' * 64, scope=scope, scope_sha256=shared.evidence_digest(scope), rowset_sha256='d' * 64))
    return S.authorize(root, req)


def test_measuring_teardown_binds_real_rollback_scope_rowset_and_executor_receipt(tmp_path, monkeypatch):
    req = teardown_request(tmp_path)
    root = tmp_path / 'run/ops'
    proof = shared.dryrun_evidence(req, root, req['measuring_scope'], 'd' * 64)
    assert proof['rollback_confirmed']
    with pytest.raises(shared.Refused):
        shared.dryrun_evidence(req, root, req['measuring_scope'], 'e' * 64)
    executor = load('executor'); monkeypatch.setattr(executor, 'REC', root / 'receipts'); monkeypatch.setattr(executor, 'log', lambda *a: None)
    monkeypatch.setattr(executor, 'now', lambda: '2026-10-15T00:00:00+00:00')
    committed = dict(proof, status='COMMITTED_AWAITING_ABSENCE', rollback_confirmed=False,
        operation_id='apply', request_sha256=shared.request_hash(req))
    executor.receipt(req, 'COMPLETED', rc=0, out='teardown_proof\t' + json.dumps(committed))
    r = json.loads((root / 'receipts/apply.json').read_text())
    assert r['status'] == 'AWAITING_ABSENCE' and r['teardown'] == committed
    rr, ar = S.absence_for(tmp_path, committed=r)
    observed = shared.absence_evidence(dict(absence_receipt=rr, absence_acceptance=ar), root, teardown_receipt=r)
    assert observed['run_id'] == S.RUN
    monkeypatch.setattr(executor, 'OPS', root)
    monkeypatch.setattr(executor, 'ACC', root / 'acceptance')
    monkeypatch.setattr(executor, 'FENCE', root / 'production.fence.json')
    monkeypatch.setattr(executor, 'smalltest_policy', lambda req: vars(shared))
    executor.FENCE.write_text(json.dumps(dict(operation_id='apply', request_sha256=r['request_sha256'])))
    q = dict(operation_id='apply', request_sha256=r['request_sha256'], result='ACCEPTED', by='v2', ts=executor.now())
    qp = executor.ACC / 'apply.quiescence.json'; qp.write_text(json.dumps(q))
    assert executor.fence_quiescent() is False
    original_commit = (root / 'receipts/apply.json').read_bytes()
    qp.write_text(json.dumps(dict(q, absence_receipt=rr, absence_acceptance=ar)))
    assert executor.fence_quiescent() is True
    completion = json.loads((root / 'receipts/apply.completion.json').read_text())
    assert completion['schema'] == 'ky.measuring_completion/1' and completion['run_id'] == S.RUN
    assert (root / 'receipts/apply.json').read_bytes() == original_commit
    changed = copy.deepcopy(r); changed['teardown']['rowset_sha256'] = 'e' * 64
    with pytest.raises(shared.Refused):
        shared.absence_evidence(dict(absence_receipt=rr, absence_acceptance=ar), root, teardown_receipt=changed)


def staging_for(root, req, manifest=None):
    manifest = manifest or dict(chart_id=shared.CHART_ID, scope_target=shared.ASSET_ID,
        gochara_v5_test_slice=dict(run='all_classes_full'))
    proof = dict(schema='ky.measuring_staging/1', status='ROLLED_BACK', rollback_confirmed=True,
        operation_id='staging-rollback', request_sha256='b' * 64, args=req['args'],
        plan_manifest=manifest, plan_manifest_digest=shared.evidence_digest(manifest))
    rr, ar = S.accepted(root, 'measuring_dispatch_dryrun', 'staging-rollback', item_id='J-3c', staging=proof)
    req.update(dryrun_receipt=rr, dryrun_acceptance=ar)
    return S.authorize(root, req)


def test_measuring_policy_is_routed_from_reviewed_source(tmp_path, monkeypatch):
    executor = load('executor')
    monkeypatch.setattr(executor, 'OPS', tmp_path / 'run/ops')
    namespace = {}; exec((SCRIPTS / 'v5_small_test_shared.py').read_text(), namespace)
    monkeypatch.setattr(executor, 'smalltest_policy', lambda req: namespace)
    req = dict(kind='measuring_dispatch', item_id='J-3c', operation_id='launch', args={'run': 'all_classes_full', 'classes': 'all'})
    assert executor.smalltest_policy_problem(req), 'absence evidence is mandatory'
    req['absence_receipt'], req['absence_acceptance'] = S.absence_for(tmp_path)
    req = staging_for(tmp_path, req)
    assert executor.smalltest_policy_problem(req) is None
    for args in ({'run': 'one_class_full', 'classes': 'all'}, {'run': 'all_classes_full', 'classes': 'marriage'},
                 {'run': 'all_classes_full', 'classes': 'all', 'horizon-start': '2025-01-01'}):
        assert executor.smalltest_policy_problem({**req, 'args': args})
    assert executor.smalltest_policy_problem({**req, 'item_id': 'J-2a'})


@pytest.fixture
def snapshot(tmp_path):
    import hashlib
    mod_path = SCRIPTS / 'gochara/canonical_l1_snapshot.py'
    assert mod_path.is_file(), 'offline canonical fixture validator is missing'
    spec = importlib.util.spec_from_file_location('snapshot_spec', mod_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    # Synthetic transport fixture only: never exported/used as real canonical data.
    files = {}
    for name in mod.REQUIRED_FILES:
        if name.endswith('.json'):
            identity = {'charts.json': 'id', 'chart_facts.json': 'fact_id', 'chart_dashas.json': 'dasha_row_id', 'life_events.json': 'event_id'}[name]
            body = json.dumps([{identity: shared.CHART_ID if name == 'charts.json' else 'synthetic-transport-only',
                                'chart_id': shared.CHART_ID}]).encode()
        else:
            body = b'-- synthetic transport fixture\n'
        (tmp_path / name).write_bytes(body)
        files[name] = dict(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    manifest = dict(schema='ky.canonical_l1_snapshot/1', chart_id=shared.CHART_ID, source='governed_offline_export',
        source_commit='a' * 40, captured_at='2026-10-16T00:00:00+00:00', files=files,
        builder_role='data_plane_builder', canonical=True)
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    approval = dict(schema='ky.canonical_l1_snapshot_approval/1', result='ACCEPTED', by='v1',
        manifest_sha256=hashlib.sha256((tmp_path / 'manifest.json').read_bytes()).hexdigest(),
        canonical_source_verified=True, schema_grants_verified=True)
    (tmp_path / 'approval.json').write_text(json.dumps(approval))
    return mod


def test_offline_snapshot_refuses_missing_approval_and_changed_bytes(snapshot, tmp_path):
    approval = (tmp_path / 'approval.json').read_bytes()
    assert snapshot.validate(tmp_path)['production_acceptance'] is False
    (tmp_path / 'approval.json').unlink()
    with pytest.raises(ValueError): snapshot.validate(tmp_path)
    (tmp_path / 'approval.json').write_bytes(approval)
    facts = tmp_path / 'chart_facts.json'
    facts.write_bytes(facts.read_bytes().replace(b'synthetic-transport-only', b'synthetic-transporx-only'))
    with pytest.raises(ValueError): snapshot.validate(tmp_path)


def test_measuring_staging_receipt_requires_confirmed_rollback(tmp_path, monkeypatch):
    executor = load('executor'); monkeypatch.setattr(executor, 'REC', tmp_path); monkeypatch.setattr(executor, 'log', lambda *a: None)
    req = dict(operation_id='rollback', kind='measuring_dispatch_dryrun', item_id='J-3c', args=dict(run='all_classes_full', classes='all'))
    manifest = dict(chart_id=shared.CHART_ID, scope_target=shared.ASSET_ID,
        gochara_v5_test_slice=dict(run='all_classes_full'))
    proof = dict(schema='ky.measuring_staging/1', status='ROLLED_BACK', rollback_confirmed=True,
        operation_id='rollback', request_sha256=shared.request_hash(req), args=req['args'],
        plan_manifest=manifest, plan_manifest_digest=shared.evidence_digest(manifest))
    for output in ('{}', json.dumps({**proof, 'rollback_confirmed': False}),
                   json.dumps({**proof, 'request_sha256': '0' * 64})):
        executor.receipt(req, 'COMPLETED', rc=0, out=output)
        assert json.loads((tmp_path / 'rollback.json').read_text())['status'] == 'FAILED'
    executor.receipt(req, 'COMPLETED', rc=0, out=json.dumps(proof))
    assert json.loads((tmp_path / 'rollback.json').read_text())['staging'] == proof


def test_measuring_launch_requires_same_manifest_rollback_not_boolean(tmp_path):
    req = dict(kind='measuring_dispatch', item_id='J-3c', operation_id='launch', args=dict(run='all_classes_full', classes='all'))
    req['absence_receipt'], req['absence_acceptance'] = S.absence_for(tmp_path)
    S.authorize(tmp_path, req)
    assert shared.measuring_request_problem(req, tmp_path / 'run/ops')
    staging_for(tmp_path, req)
    proof = shared.measuring_dryrun_evidence(req, tmp_path / 'run/ops')
    assert shared.measuring_dryrun_evidence(req, tmp_path / 'run/ops', proof['plan_manifest_digest']) == proof
    with pytest.raises(shared.Refused):
        shared.measuring_dryrun_evidence(req, tmp_path / 'run/ops', '0' * 64)


def test_a_mechanically_accepted_measuring_launch_passes_the_same_reviewed_policy_as_a_signed_one(tmp_path):
    """OWNER-MINIMAL-PROTECTION-NOW: the J-3c launch carries `pack_fill` and no acceptance_receipt; the executor's own pre-acceptance record is what the
    reviewed measuring policy reads (the staging rollback must precede it), and a record that is not complete refuses."""
    req = dict(kind='measuring_dispatch', item_id='J-3c', operation_id='launch', args=dict(run='all_classes_full', classes='all'))
    req['absence_receipt'], req['absence_acceptance'] = S.absence_for(tmp_path)
    req = staging_for(tmp_path, req)
    root = tmp_path / 'run/ops'
    assert shared.measuring_request_problem(req, root) is None, 'control: the signed request is admitted'
    req.pop('acceptance_receipt'); req.pop('dryrun_acceptance')
    req['pack_fill'] = dict(pack_manifest_sha256='a' * 64, template={}, fill_sha256='b' * 64)
    record = dict(schema='ky.mechanical_acceptance/1', phase='pre', by='executor-mechanical', result='ACCEPTED', operation_id='launch',
                  request_sha256=shared.request_hash(req), reviewed_commit=S.COMMIT, ts='2026-10-18T00:00:00+00:00',
                  checks={'request_equals_verified_pack_fill': True, 'dry_run_completed_ok_for_same_identity': True, 'lease_live': True})
    S.put(tmp_path, 'acceptance', 'launch', record)
    assert shared.measuring_request_problem(req, root) is None
    S.put(tmp_path, 'acceptance', 'launch', dict(record, checks={'lease_live': False}))
    assert shared.measuring_request_problem(req, root), 'a record with a false check must refuse'
    S.put(tmp_path, 'acceptance', 'launch', dict(record, ts='2026-10-14T00:00:00+00:00'))
    assert shared.measuring_request_problem(req, root), 'the staging rollback must precede the acceptance'


def resign_snapshot(root, *, changed_file=None):
    import hashlib
    m = json.loads((root / 'manifest.json').read_text())
    if changed_file:
        body = (root / changed_file).read_bytes()
        m['files'][changed_file] = dict(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        (root / 'manifest.json').write_text(json.dumps(m))
    a = json.loads((root / 'approval.json').read_text())
    a['manifest_sha256'] = hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()
    (root / 'approval.json').write_text(json.dumps(a))


@pytest.mark.parametrize('field,value', [('canonical', False), ('source', 'synthetic'), ('chart_id', S.RUN),
    ('source_commit', 'unknown'), ('builder_role', 'postgres'), ('captured_at', '2026-10-16')])
def test_offline_snapshot_requires_governed_source_metadata(snapshot, tmp_path, field, value):
    m = json.loads((tmp_path / 'manifest.json').read_text()); m[field] = value
    (tmp_path / 'manifest.json').write_text(json.dumps(m)); resign_snapshot(tmp_path)
    with pytest.raises(ValueError): snapshot.validate(tmp_path)


@pytest.mark.parametrize('field,value', [('result', 'PENDING'), ('by', 'builder'), ('manifest_sha256', '0' * 64),
    ('canonical_source_verified', False), ('schema_grants_verified', False)])
def test_offline_snapshot_requires_independent_byte_bound_approval(snapshot, tmp_path, field, value):
    a = json.loads((tmp_path / 'approval.json').read_text()); a[field] = value
    (tmp_path / 'approval.json').write_text(json.dumps(a))
    with pytest.raises(ValueError): snapshot.validate(tmp_path)


@pytest.mark.parametrize('change', ['empty', 'duplicate', 'foreign-chart', 'missing-id', 'not-array', 'duplicate-json-field',
    'symlink', 'missing-file', 'empty-schema', 'missing-inventory', 'wrong-bytes'])
def test_offline_snapshot_inventory_and_row_envelope_refusals(snapshot, tmp_path, change):
    name = 'chart_facts.json'; p = tmp_path / name
    if change == 'empty': p.write_text('[]')
    elif change == 'duplicate': p.write_text(json.dumps(json.loads(p.read_text()) * 2))
    elif change == 'foreign-chart': p.write_text(json.dumps([dict(fact_id='fixture', chart_id=S.RUN)]))
    elif change == 'missing-id': p.write_text(json.dumps([dict(chart_id=shared.CHART_ID)]))
    elif change == 'not-array': p.write_text('{}')
    elif change == 'duplicate-json-field': p.write_text('[{"fact_id":"fixture","fact_id":"other"}]')
    elif change == 'symlink':
        other = tmp_path / 'other.json'; other.write_bytes(p.read_bytes()); p.unlink(); p.symlink_to(other)
    elif change == 'missing-file': p.unlink()
    elif change == 'empty-schema': name = 'schema.sql'; (tmp_path / name).write_text('  ')
    elif change == 'missing-inventory':
        m = json.loads((tmp_path / 'manifest.json').read_text()); del m['files'][name]
        (tmp_path / 'manifest.json').write_text(json.dumps(m))
    elif change == 'wrong-bytes':
        m = json.loads((tmp_path / 'manifest.json').read_text()); m['files'][name]['bytes'] += 1
        (tmp_path / 'manifest.json').write_text(json.dumps(m))
    resign_snapshot(tmp_path, changed_file=name if change not in ('missing-file', 'missing-inventory', 'wrong-bytes') else None)
    with pytest.raises(ValueError): snapshot.validate(tmp_path)


def test_measuring_commit_unknown_never_retries_or_launches(tmp_path):
    from types import SimpleNamespace
    module = load('measuring_launch')
    calls = []
    def stage(argv):
        calls.append(argv)
        raise TimeoutError('synthetic commit-unknown transport')
    dispatcher = SimpleNamespace(build_slice_marker=lambda **kw: {}, main=stage)
    with pytest.raises(TimeoutError):
        module.run(['--run', 'all_classes_full', '--classes', 'all'], dispatcher=dispatcher, claim_dir=tmp_path,
            connect=lambda: pytest.fail('commit unknown must not read back as launched'),
            launcher=lambda *a: pytest.fail('commit unknown must never launch'))
    assert len(calls) == 1


def test_measuring_preview_points_to_dedicated_binding_but_never_attests_rollback():
    preview = load('operation_dryrun').prepare('measuring_dispatch', dict(run='all_classes_full', classes='all'))
    assert preview['source'] == 'platform/scripts/dispatch_v5_measuring_job.py'
    assert preview['status'] == 'PREPARATION_ONLY' and preview['dry_run_passed'] is False
    assert preview['enabled'] is False and preview['blockers']
