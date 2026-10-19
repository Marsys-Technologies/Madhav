"""W4-SAFETY-01..03: port of the rejected review's executable reproductions.

Boundaries use the real operation code and filesystem receipts. No remote calls.
"""
import json
import os
from pathlib import Path

import pytest
import test_teardown_v5_small_test as T
import dispatch_v5_small_test_job as dispatch


def test_refuse_unrelated_tagged_smalltest(tmp_path, monkeypatch):
    approved = '22222222-2222-4222-8222-222222222222'
    unrelated = '11111111-1111-4111-8111-111111111111'
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    p = tmp_path / 'run/ops/receipts'; p.mkdir(parents=True)
    (p / 'J-2a.dispatch.json').write_text(json.dumps({'kind': 'smalltest_dispatch', 'status': 'COMPLETED',
        'launch': {'run_id': approved, 'chart_id': T.CHART_ID, 'plan_manifest_digest': 'a' * 64}}))
    manifest = {T._W.TEST_SLICE_KEY: T.ONE_MARKER_FOR_TESTS}
    h = T._Harness(members=[T._test_run(unrelated)], receipts=[{'partition_key': 'p1', 'build_id': unrelated}],
        run_manifests=[{'id': unrelated, 'plan_manifest': manifest, 'plan_manifest_digest': T._W._manifest_digest(manifest)}],
        retention=[{'id': unrelated, 'created_at': '2026-09-01T00:00:00+00:00', 'secs': 60 * 86400}])
    with pytest.raises(T.teardown_mod.TeardownRefused):
        with T._patched(h, bind=False):
            T.teardown_mod.teardown(dry_run=False)
    assert h.commits == 0 and not h.deletes()


def test_refuse_teardown_without_candidate_bound_dryrun(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    h = T._Harness()
    with pytest.raises(T.teardown_mod.TeardownRefused):
        with T._patched(h, bind=False):
            T.teardown_mod.teardown(dry_run=False)
    assert h.commits == 0 and not h.deletes()


def test_refuse_measuring_build_through_smalltest_kind():
    with pytest.raises((RuntimeError, T.teardown_mod.TeardownRefused)):
        dispatch.build_slice_marker(run='all_classes_full', classes='all')

import copy
import hashlib
import importlib.util
from types import SimpleNamespace
import smalltest_safety_support as S


@pytest.fixture(autouse=True)
def _scoped_content_unchanged(monkeypatch):
    """These tests stage a dispatch against a fake database; the fresh scoped-content measurement is not their subject
    (it is proved in test_backup_v5_small_test_scoped.py and the kala_db suite)."""
    import backup_v5_small_test_job
    monkeypatch.setattr(backup_v5_small_test_job, 'measure_scope_now', S.fixture_measure)
import v5_small_test_shared as shared

ROOT = Path(__file__).resolve().parents[3]
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'


@pytest.fixture
def bound(tmp_path, monkeypatch):
    h = T._Harness()
    manifest = h.run_manifests[0]['plan_manifest']
    scope = S.scope_for(tmp_path, T.RUN_1, manifest, h.manifest)
    tables = {t for t, _ in T.teardown_mod.GENERATION_TABLES} | set(T.teardown_mod.CASCADE_PROOF_TABLES) | {
        'asset_registry', 'build_runs', 'build_run_assets', 'asset_throughput', 'asset_freshness', 'asset_provenance_receipts'}
    rowset = shared.evidence_digest({t: [] for t in tables})
    req = S.request_for(tmp_path, scope, rowset_sha256=rowset)
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    return SimpleNamespace(root=tmp_path, h=h, scope=scope, req=req, rowset=rowset, patch=monkeypatch)


def run_bound(b, *, dry_run=False):
    S.authorize(b.root, b.req)
    b.patch.setenv('KY_OPERATION_REQUEST', json.dumps(b.req))
    with T._patched(b.h, bind=False):
        T.teardown_mod.teardown(dry_run=dry_run)


def test_exact_staged_run_with_bound_rehearsal_commits_and_stays_pending_absence(bound, capsys):
    run_bound(bound)
    assert bound.h.commits == 1
    proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert proof['scope'] == bound.scope and proof['rowset_sha256'] == bound.rowset
    assert proof['status'] == 'COMMITTED_AWAITING_ABSENCE' and proof['rollback_confirmed'] is False


@pytest.mark.parametrize('field,value', [
    ('run_id', S.RUN), ('chart_id', S.RUN), ('generation', '5.1'), ('asset_id', 'another_asset'),
    ('plan_manifest_digest', '0' * 64), ('manifest_id', S.RUN), ('input_vector_sha256', '0' * 64),
])
def test_bound_scope_mismatches_refuse_before_delete(bound, field, value):
    bound.req['smalltest_scope'][field] = value
    with pytest.raises(shared.Refused):
        run_bound(bound)
    assert not bound.h.deletes() and bound.h.commits == 0


def test_additional_tagged_run_is_not_authorized_by_accepted_run(bound):
    bound.h.members.append(T._test_run(S.RUN))
    with pytest.raises(shared.Refused, match='identified staged run'):
        run_bound(bound)
    assert not bound.h.deletes() and not bound.h.commits


@pytest.mark.parametrize('target', ['dispatch_receipt', 'dispatch_acceptance'])
@pytest.mark.parametrize('mutation', ['missing', 'digest', 'escape', 'unaccepted'])
def test_scope_evidence_must_be_real_accepted_bytes(bound, target, mutation):
    ref = bound.scope[target]
    folder = 'receipts' if target.endswith('receipt') else 'acceptance'
    if mutation == 'missing':
        (bound.root / 'run/ops' / folder / ref['name']).unlink()
    elif mutation == 'digest':
        ref['sha256'] = '0' * 64
    elif mutation == 'escape':
        ref['name'] = '../other.json'
    else:
        path = bound.root / 'run/ops' / folder / ref['name']
        value = json.loads(path.read_text()); value.update(status='FAILED', result='REJECTED')
        bound.scope[target] = S.put(bound.root, folder, path.stem, value)
    with pytest.raises(shared.Refused):
        run_bound(bound)
    assert not bound.h.deletes() and not bound.h.commits


@pytest.mark.parametrize('mode', ['missing', 'failed', 'rollback', 'scope', 'rows', 'request', 'kind', 'digest'])
def test_own_dryrun_must_bind_success_scope_rows_and_rollback(bound, mode):
    if mode == 'missing':
        bound.req.pop('dryrun_receipt')
    elif mode == 'digest':
        bound.req['dryrun_receipt']['sha256'] = '0' * 64
    else:
        path = bound.root / 'run/ops/receipts/dryrun.json'; r = json.loads(path.read_text())
        if mode == 'failed': r['status'] = 'FAILED'
        elif mode == 'rollback': r['teardown']['rollback_confirmed'] = False
        elif mode == 'scope': r['teardown']['scope']['run_id'] = S.RUN
        elif mode == 'rows': r['teardown']['rowset_sha256'] = '0' * 64
        elif mode == 'request': r['teardown']['request_sha256'] = '0' * 64
        elif mode == 'kind': r['kind'] = 'smalltest_dispatch_dryrun'
        bound.req['dryrun_receipt'] = S.put(bound.root, 'receipts', 'dryrun', r)
    with pytest.raises(shared.Refused):
        run_bound(bound)
    assert not bound.h.deletes() and not bound.h.commits


def test_dryrun_evidence_is_emitted_only_after_confirmed_rollback(bound, capsys):
    bound.req = S.request_for(bound.root, bound.scope, dry_run=True)
    run_bound(bound, dry_run=True)
    proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert proof['status'] == 'ROLLED_BACK' and proof['rollback_confirmed'] is True
    assert not bound.h.commits


def test_rollback_failure_never_emits_success_evidence(bound, capsys):
    bound.req = S.request_for(bound.root, bound.scope, dry_run=True)
    bound.h.rollback_error = RuntimeError('fixture rollback failure')
    with pytest.raises(RuntimeError): run_bound(bound, dry_run=True)
    assert 'teardown_proof\t' not in capsys.readouterr().out


def test_rowset_digest_detects_equal_count_content_change():
    class Cur:
        def execute(self, sql, params): self.sql = sql
        def fetchall(self): return [{'row': self.value}]
    cur = Cur(); cur.value = '{"id":"a","value":1}'
    original = T.teardown_mod._rowset_digest(cur, [S.RUN])
    cur.value = '{"id":"a","value":2}'
    assert T.teardown_mod._rowset_digest(cur, [S.RUN]) != original


@pytest.fixture
def executor(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    spec = importlib.util.spec_from_file_location('w4_safety_executor', FLEET / 'executor.py')
    ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
    monkeypatch.setattr(ex, 'lease_live', lambda _: True)
    monkeypatch.setattr(ex, 'seen', lambda _: False)
    source = (ROOT / 'platform/scripts/v5_small_test_shared.py').read_text()
    monkeypatch.setattr(ex, 'git', lambda *a, **k: SimpleNamespace(returncode=0, stdout=source))
    for path in (ex.ACC, ex.REC, ex.KY_ROOT / 'logs'): path.mkdir(parents=True, exist_ok=True)
    return ex


def admitted_request(ex, kind='smalltest_dispatch', **fields):
    import datetime as dt
    req = dict(operation_id='fixture', idempotency_key='fixture', kind=kind, item_id='J-2a',
        requested_by='adhikarin', kyd='fixture', chart_id=shared.CHART_ID, lease_id='fixture',
        args={'run': 'all_classes_1y', 'classes': 'all', 'horizon-start': '2025-04-17T00:00:00+00:00',
              'horizon-end': '2026-04-17T00:00:00+00:00'}, reviewed_commit=S.COMMIT,
        expires_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).isoformat())
    req.update(fields)
    if kind == 'smalltest_dispatch':
        for key, value in S.scoped_backup_for(ex.KY_ROOT).items():
            req.setdefault(key, value)
    req['acceptance_receipt'] = str(ex.ACC / 'fixture.json')
    (ex.ACC / 'fixture.json').write_text(json.dumps(dict(result='ACCEPTED', by='v1', operation_id=req['operation_id'],
        request_sha256=ex.request_digest(req), reviewed_commit=S.COMMIT, ts=ex.now(),
        rows={k: True for k in ['2', '3', '7', '9', '11']},
        checks=dict(backup_taken=True, restore_verified=True, dry_run_passed=True))))
    return req


def validate(ex, req):
    return ex.validate(req, json.loads((FLEET / 'executor_ops.json').read_text())['ops'],
                       dict(owner=True, builder=True, gcloud=True, pgenv=True, none=True))


def test_refuse_next_dispatch_without_independent_absence(executor):
    req = admitted_request(executor)
    assert validate(executor, req) is not None


def test_refuse_teardown_admission_with_only_dryrun_boolean(executor):
    req = admitted_request(executor, 'smalltest_teardown')
    assert validate(executor, req) is not None


@pytest.mark.parametrize('args', [{'run': 'all_classes_full', 'classes': 'all'},
                                  {'run': 'one_class_full', 'classes': 'career'}])
def test_refuse_measuring_or_unstaged_class_at_admission(executor, args):
    rr, ar = S.absence_for(executor.KY_ROOT)
    req = admitted_request(executor, args=args, absence_receipt=rr, absence_acceptance=ar)
    assert validate(executor, req) is not None


def test_first_dispatch_accepts_measured_empty_baseline(executor):
    rr, ar = S.absence_for(executor.KY_ROOT)
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar)
    assert validate(executor, req) is None


def committed_fixture(root):
    scope = dict(run_id=S.RUN)
    proof = dict(schema='ky.smalltest_teardown/1', status='COMMITTED_AWAITING_ABSENCE', scope=scope,
                 scope_sha256=shared.evidence_digest(scope), rowset_sha256='c' * 64)
    return dict(operation_id='apply', kind='smalltest_teardown', status='AWAITING_ABSENCE', exit_code=0,
        request_sha256='d' * 64, reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00', teardown=proof)


@pytest.mark.parametrize('mutation', ['none', 'run', 'scope', 'rows', 'commit', 'output', 'counts', 'incomplete', 'ordering'])
def test_independent_absence_binds_measured_output_and_exact_commit(executor, mutation):
    committed = committed_fixture(executor.KY_ROOT)
    prior = S.put(executor.KY_ROOT, 'receipts', 'apply', committed)
    rr, ar = S.absence_for(executor.KY_ROOT, committed=committed)
    ap = executor.ACC / ar['name']; a = json.loads(ap.read_text())
    field = {'run': 'run_id', 'scope': 'scope_sha256', 'rows': 'rowset_sha256', 'commit': 'teardown_request_sha256'}.get(mutation)
    if field: a['absence'][field] = 'wrong'
    elif mutation == 'counts': a['absence']['counts']['build_runs'] = 1
    elif mutation == 'incomplete': a['absence']['counts'].pop('build_run_assets')
    elif mutation == 'output': (executor.REC / 'readback.output.txt').write_text('wrong bytes')
    elif mutation == 'ordering':
        r = json.loads((executor.REC / rr['name']).read_text()); r['ts'] = committed['ts']
        rr = S.put(executor.KY_ROOT, 'receipts', 'readback', r)
    if mutation in ('run', 'scope', 'rows', 'commit', 'counts', 'incomplete'):
        # Give the adversary a fully self-consistent measured output/acceptance.
        # The run/commit/census binding itself must refuse, not merely its hash.
        import csv
        import io
        measured = {k: v for k, v in a['absence'].items() if k != 'output_sha256'}
        body = io.StringIO(); writer = csv.writer(body, delimiter='\t', lineterminator='\n')
        writer.writerow(['absence_proof']); writer.writerow([json.dumps(measured)])
        output = executor.REC / 'readback.output.txt'; output.write_text(body.getvalue())
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        r = json.loads((executor.REC / rr['name']).read_text()); r['output_sha256'] = digest
        rr = S.put(executor.KY_ROOT, 'receipts', 'readback', r)
        a['absence']['output_sha256'] = digest
    ar = S.put(executor.KY_ROOT, 'acceptance', 'readback', a)
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar, prior_teardown_receipt=prior)
    assert (validate(executor, req) is None) == (mutation == 'none')


def test_baseline_cannot_be_replayed_after_a_teardown(executor):
    S.put(executor.KY_ROOT, 'receipts', 'apply', committed_fixture(executor.KY_ROOT))
    rr, ar = S.absence_for(executor.KY_ROOT)
    assert validate(executor, admitted_request(executor, absence_receipt=rr, absence_acceptance=ar)) is not None


def test_generic_quiescence_does_not_complete_a_teardown(executor):
    committed = committed_fixture(executor.KY_ROOT)
    S.put(executor.KY_ROOT, 'receipts', 'apply', committed)
    executor.FENCE.write_text(json.dumps(dict(operation_id='apply', request_sha256=committed['request_sha256'])))
    (executor.ACC / 'apply.quiescence.json').write_text(json.dumps(dict(operation_id='apply',
        request_sha256=committed['request_sha256'], result='ACCEPTED', by='v2', ts=executor.now())))
    assert executor.fence_quiescent() is False
    assert not (executor.REC / "apply.completion.json").exists()
    rr, ar = S.absence_for(executor.KY_ROOT, committed=committed)
    q = json.loads((executor.ACC / 'apply.quiescence.json').read_text())
    q.update(absence_receipt=rr, absence_acceptance=ar)
    (executor.ACC / 'apply.quiescence.json').write_text(json.dumps(q))
    assert executor.fence_quiescent() is True
    completion = json.loads((executor.REC / 'apply.completion.json').read_text())
    assert completion['status'] == 'COMPLETED' and completion['run_id'] == S.RUN
    assert completion['absence_receipt'] == rr and executor.FENCE.exists()
    assert json.loads((executor.REC / 'apply.json').read_text()) == committed


def test_output_from_a_different_run_refuses_even_with_identical_stamp(bound):
    bound.h.foreign_coverage = 1
    with pytest.raises(shared.Refused, match='not created by the identified staged run'):
        run_bound(bound)
    assert not bound.h.deletes() and not bound.h.commits


def test_generated_independent_readback_measures_counts_and_binds_commit():
    committed = committed_fixture(ROOT)
    sql = shared.absence_readback_sql(committed)
    assert sql.startswith('SELECT ') and sql.endswith('AS absence_proof')
    assert 'count(*) FROM build_runs WHERE id =' in sql
    assert 'count(*) FROM ka_gochara_contact WHERE chart_id =' in sql
    assert 'count(*) FROM ka_gochara_near_miss WHERE chart_id =' in sql and 'count(*) FROM ka_gochara_near_miss_search WHERE chart_id =' in sql
    assert "partition_kind = 'event_class'" in sql
    assert shared.evidence_digest(committed) in sql
    assert 'registry_inert' in sql and 'is_active IS FALSE' in sql
    assert not any(word in sql.upper() for word in ('DELETE ', 'UPDATE ', 'INSERT ', 'DROP '))


@pytest.mark.parametrize('horizon', [({}, 'missing'), ({'horizon-start': '2025-01-01', 'horizon-end': '2026-01-01'}, 'naive'),
    ({'horizon-start': '2025-01-01T00:00:00+00:00', 'horizon-end': '2027-01-01T00:00:00+00:00'}, 'measuring'),
    ({'horizon-start': '2026-01-01T00:00:00+00:00', 'horizon-end': '2025-01-01T00:00:00+00:00'}, 'reverse')])
def test_admission_refuses_widened_or_missing_annual_horizon(executor, horizon):
    rr, ar = S.absence_for(executor.KY_ROOT)
    args = dict(run='all_classes_1y', classes='all', **horizon[0])
    assert validate(executor, admitted_request(executor, args=args, absence_receipt=rr, absence_acceptance=ar)) is not None


def test_dryrun_from_another_reviewed_source_is_refused(bound):
    path = bound.root / 'run/ops/receipts/dryrun.json'; r = json.loads(path.read_text())
    r['reviewed_commit'] = 'f' * 40
    bound.req['dryrun_receipt'] = S.put(bound.root, 'receipts', 'dryrun', r)
    ap = bound.root / 'run/ops/acceptance/dryrun.json'; a = json.loads(ap.read_text()); a['reviewed_commit'] = r['reviewed_commit']
    bound.req['dryrun_acceptance'] = S.put(bound.root, 'acceptance', 'dryrun', a)
    with pytest.raises(shared.Refused): run_bound(bound)
    assert not bound.h.deletes() and not bound.h.commits


def test_initial_empty_rehearsal_is_allowed_but_never_commits(bound, capsys):
    bound.h = T._Harness(members=[], receipts=[], rows={}, manifest=None)
    bound.req = S.request_for(bound.root, {'empty': True}, dry_run=True)
    run_bound(bound, dry_run=True)
    proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert proof['scope'] == {'empty': True} and proof['rollback_confirmed'] is True
    assert not bound.h.commits


def test_empty_rehearsal_cannot_select_an_existing_candidate(bound):
    bound.req = S.request_for(bound.root, {'empty': True}, dry_run=True)
    with pytest.raises(shared.Refused, match='empty rehearsal'):
        run_bound(bound, dry_run=True)
    assert not bound.h.deletes() and not bound.h.commits


def test_conditional_marriage_profile_is_admitted_with_independent_absence(executor):
    rr, ar = S.absence_for(executor.KY_ROOT)
    req = admitted_request(executor, args=dict(run='one_class_full', classes='marriage'),
                           absence_receipt=rr, absence_acceptance=ar)
    assert validate(executor, req) is None


def test_real_bridge_refuses_measuring_before_staging_or_launching(tmp_path):
    spec = importlib.util.spec_from_file_location('w4_real_bridge', FLEET / 'smalltest_launch.py')
    bridge = importlib.util.module_from_spec(spec); spec.loader.exec_module(bridge)
    calls = []
    with pytest.raises(RuntimeError, match='measuring phase is disabled'):
        bridge.run(['--run', 'all_classes_full', '--classes', 'all'], dispatcher=dispatch,
                   connect=lambda: calls.append('connect'), launcher=lambda *a: calls.append('launch'), claim_dir=tmp_path)
    assert not calls and not list(tmp_path.iterdir())


@pytest.mark.parametrize('mutation', ['none', 'missing', 'request', 'scope', 'rollback', 'rowset', 'duplicate', 'type'])
def test_executor_records_only_bound_rollback_proofs(executor, mutation):
    req = admitted_request(executor, 'smalltest_teardown_dryrun', smalltest_scope={'empty': True})
    proof = dict(schema='ky.smalltest_teardown/1', status='ROLLED_BACK', rollback_confirmed=True,
        operation_id=req['operation_id'], request_sha256=executor.request_digest(req), scope=req['smalltest_scope'],
        scope_sha256=shared.evidence_digest(req['smalltest_scope']), rowset_sha256='a' * 64)
    if mutation == 'request': proof['request_sha256'] = '0' * 64
    elif mutation == 'scope': proof['scope_sha256'] = '0' * 64
    elif mutation == 'rollback': proof['rollback_confirmed'] = False
    elif mutation == 'rowset': proof['rowset_sha256'] = 'bad'
    elif mutation == 'type': proof = []
    output = 'teardown_proof\t' + json.dumps(proof) + '\n'
    if mutation == 'missing': output = ''
    elif mutation == 'duplicate': output *= 2
    executor.receipt(req, 'COMPLETED', rc=0, out=output)
    record = json.loads((executor.REC / 'fixture.json').read_text())
    assert record['status'] == ('COMPLETED' if mutation == 'none' else 'FAILED')


def test_executor_commit_receipt_remains_pending_until_independent_absence(executor):
    req = admitted_request(executor, 'smalltest_teardown', smalltest_scope={'run_id': S.RUN})
    proof = dict(schema='ky.smalltest_teardown/1', status='COMMITTED_AWAITING_ABSENCE', rollback_confirmed=False,
        operation_id=req['operation_id'], request_sha256=executor.request_digest(req), scope=req['smalltest_scope'],
        scope_sha256=shared.evidence_digest(req['smalltest_scope']), rowset_sha256='a' * 64)
    executor.receipt(req, 'COMPLETED', rc=0, out='teardown_proof\t' + json.dumps(proof))
    assert json.loads((executor.REC / 'fixture.json').read_text())['status'] == 'AWAITING_ABSENCE'
    assert not (executor.REC / 'fixture.completion.json').exists()


@pytest.mark.parametrize('field,value', [
    ('result', 'REJECTED'), ('by', 'adhikarin'), ('operation_id', 'another'),
    ('request_sha256', '0' * 64), ('reviewed_commit', '0' * 40),
])
def test_request_acceptance_itself_rejects_unbound_or_nonverifier_evidence(bound, field, value):
    root = bound.root / 'run/ops'
    assert shared.acceptance(bound.req, root)['result'] == 'ACCEPTED'
    path = Path(bound.req['acceptance_receipt'])
    acceptance = json.loads(path.read_text())
    acceptance[field] = value
    path.write_text(json.dumps(acceptance))
    with pytest.raises(shared.Refused, match='bound to independent verifier acceptance'):
        shared.acceptance(bound.req, root)


@pytest.mark.parametrize('field,value', [
    ('run_id', S.RUN), ('plan_manifest_digest', '0' * 64),
    ('chart_id', S.RUN), ('asset_id', 'another'), ('generation', '5.1'),
])
def test_staged_scope_itself_is_bound_to_the_accepted_launch(bound, field, value):
    root = bound.root / 'run/ops'
    assert shared.staged_scope(bound.req, root) == bound.scope
    bound.scope[field] = value
    with pytest.raises(shared.Refused, match='scope differs from the accepted staged launch'):
        shared.staged_scope(bound.req, root)


@pytest.mark.parametrize('field,value', [('id', S.RUN), ('plan_manifest_digest', '0' * 64),
                                       ('plan_manifest', {})])
def test_teardown_checks_surviving_run_identity_independently_of_stamp_proof(bound, field, value):
    # Exercise this boundary directly: the earlier generation-ownership check
    # must not mask a missing UUID/manifest binding in _bound_scope itself.
    cur = bound.h.conn.cursor()
    with T._patched(bound.h, bind=False):
        assert T.teardown_mod._bound_scope(cur, [T.RUN_1], bound.req) == bound.scope
        bound.h.run_manifests[0][field] = value
        with pytest.raises(shared.Refused, match='staged launch UUID/manifest'):
            T.teardown_mod._bound_scope(cur, [T.RUN_1], bound.req)
    assert not bound.h.deletes() and not bound.h.commits


@pytest.mark.parametrize('field,value', [('manifest_id', S.RUN), ('status', 'published'),
                                       ('input_generation_vector', {})])
def test_teardown_checks_candidate_identity_against_accepted_scope(bound, field, value):
    cur = bound.h.conn.cursor()
    with T._patched(bound.h, bind=False):
        assert T.teardown_mod._bound_scope(cur, [T.RUN_1], bound.req) == bound.scope
        bound.h.manifest[field] = value
        with pytest.raises(shared.Refused, match='candidate manifest/vector differs'):
            T.teardown_mod._bound_scope(cur, [T.RUN_1], bound.req)
    assert not bound.h.deletes() and not bound.h.commits


def test_teardown_requires_the_original_surviving_marker_even_with_bound_identities(bound):
    # Keep UUID, manifest digest and accepted candidate vector all coherent.
    # Only the original marker's relation to that vector is wrong.
    manifest = copy.deepcopy(bound.h.run_manifests[0]['plan_manifest'])
    original_class = manifest[T._W.TEST_SLICE_KEY]['classes'][0]
    manifest[T._W.TEST_SLICE_KEY]['classes'] = [next(c for c in T._W.SCORED_CLASSES if c != original_class)]
    T._W._validate_test_slice(manifest[T._W.TEST_SLICE_KEY])
    bound.h.run_manifests[0].update(plan_manifest=manifest, plan_manifest_digest=shared.evidence_digest(manifest))
    bound.req['smalltest_scope'] = S.scope_for(bound.root, T.RUN_1, manifest, bound.h.manifest)
    with T._patched(bound.h, bind=False):
        with pytest.raises(shared.Refused, match="original marker"):
            T.teardown_mod._bound_scope(bound.h.conn.cursor(), [T.RUN_1], bound.req)
    assert not bound.h.deletes() and not bound.h.commits


@pytest.mark.parametrize('mismatch', ['kind', 'arguments'])
def test_dispatch_binds_kind_and_cli_arguments_before_connecting(tmp_path, monkeypatch, mismatch):
    import psycopg
    args = {'run': 'all_classes_1y', 'classes': 'all',
            'horizon-start': '2025-01-01T00:00:00+00:00', 'horizon-end': '2026-01-01T00:00:00+00:00'}
    rr, ar = S.absence_for(tmp_path)
    req = S.authorize(tmp_path, dict(operation_id='dispatch', kind='smalltest_dispatch', args=args,
                                   absence_receipt=rr, absence_acceptance=ar))
    argv = ['--i-am-steward', '--after-settled-1', '--execute']
    for key, value in args.items():
        argv.extend(['--' + key, value])
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    monkeypatch.setenv('DATABASE_URL', 'postgresql://postgres@127.0.0.1:55433/not_connected')
    class ConnectionBoundary(Exception):
        pass
    calls = []
    def connect(*a, **kw):
        calls.append(True)
        raise ConnectionBoundary()
    monkeypatch.setattr(psycopg, 'connect', connect)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    with pytest.raises(ConnectionBoundary):
        dispatch.main(argv)
    calls.clear()
    if mismatch == 'kind':
        req['kind'] = 'backup_snapshot'
        reason = 'operation kind does not authorize'
    else:
        req['args']['horizon-end'] = '2025-12-31T00:00:00+00:00'
        reason = 'staging arguments differ'
    S.authorize(tmp_path, req)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    with pytest.raises(shared.Refused, match=reason):
        dispatch.main(argv)
    assert not calls


def test_absence_output_hash_is_checked_even_when_altered_bytes_measure_the_same_json(executor):
    rr, ar = S.absence_for(executor.KY_ROOT)
    # Additional trailing whitespace leaves the parsed JSON/TSV unchanged.
    # Only a byte hash comparison detects this change.
    output = executor.REC / 'readback.output.txt'
    output.write_bytes(output.read_bytes() + b'\n')
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar)
    problem = validate(executor, req)
    assert problem and 'output digest mismatch' in problem


def test_absence_acceptance_cannot_change_a_measured_zero_into_another_zero(executor):
    rr, ar = S.absence_for(executor.KY_ROOT)
    a = json.loads((executor.ACC / ar['name']).read_text())
    # Both zero censuses meet the coverage requirement. Equality to the actual
    # measured output, independently of that coverage check, must still hold.
    a['absence']['counts']['unmeasured_extra_table'] = 0
    ar = S.put(executor.KY_ROOT, 'acceptance', 'readback', a)
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar)
    problem = validate(executor, req)
    assert problem and 'differs from the measured readback output' in problem


def test_old_absence_cannot_bypass_a_later_completed_launch(executor):
    committed = committed_fixture(executor.KY_ROOT)
    prior = S.put(executor.KY_ROOT, 'receipts', 'apply', committed)
    rr, ar = S.absence_for(executor.KY_ROOT, committed=committed)
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar, prior_teardown_receipt=prior)
    assert validate(executor, req) is None
    S.accepted(executor.KY_ROOT, 'smalltest_dispatch', 'later-launch',
               ts='2026-10-15T00:00:02+00:00', launch={'run_id': T.RUN_1})
    problem = validate(executor, req)
    assert problem and 'later staged launch requires its own teardown' in problem


def test_first_annual_smalltest_cannot_reduce_the_scored_class_set(executor):
    rr, ar = S.absence_for(executor.KY_ROOT)
    req = admitted_request(executor, absence_receipt=rr, absence_acceptance=ar)
    assert validate(executor, req) is None
    args = dict(req['args'], classes='marriage')
    req = admitted_request(executor, args=args, absence_receipt=rr, absence_acceptance=ar)
    problem = validate(executor, req)
    assert problem and 'requires all scored classes' in problem


@pytest.mark.parametrize('needs', ['none', 'builder', 'owner'])
def test_execute_hands_the_complete_accepted_request_to_the_operation(executor, monkeypatch, needs):
    req = admitted_request(executor)
    executor.TMP.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('KY_BUILDER_DATABASE_URL', 'synthetic-builder')
    monkeypatch.setenv('KY_OWNER_DATABASE_URL', 'synthetic-owner')
    calls = []
    def run_group(argv, cwd, env, timeout):
        calls.append((argv, env))
        return SimpleNamespace(returncode=0, stdout='fixture', stderr='')
    monkeypatch.setattr(executor, 'run_group', run_group)
    op = dict(script='fixture.py', fixed_args=[], needs=needs, production=False)
    assert executor.execute(req, op)[0] == 0
    assert len(calls) == 1
    env = calls[0][1]
    assert json.loads(env['KY_OPERATION_REQUEST']) == req
    assert env.get('DATABASE_URL') == {'none': None, 'builder': 'synthetic-builder', 'owner': 'synthetic-owner'}[needs]
    assert 'KY_OWNER_DATABASE_URL' not in env and 'KY_BUILDER_DATABASE_URL' not in env


def test_executor_loop_reconciles_independent_teardown_completion_without_new_requests(executor, monkeypatch):
    committed = committed_fixture(executor.KY_ROOT)
    S.put(executor.KY_ROOT, 'receipts', 'apply', committed)
    executor.FENCE.write_text(json.dumps(dict(operation_id='apply', request_sha256=committed['request_sha256'])))
    rr, ar = S.absence_for(executor.KY_ROOT, committed=committed)
    S.put(executor.KY_ROOT, 'acceptance', 'apply.quiescence', dict(operation_id='apply',
        request_sha256=committed['request_sha256'], result='ACCEPTED', by='v2', ts=executor.now(),
        absence_receipt=rr, absence_acceptance=ar))
    class NoWorkers:
        def __init__(self, **kwargs): pass
        def submit(self, *args): pytest.fail('idle loop submitted an operation')
        def shutdown(self, **kwargs): pass
    monkeypatch.setattr(executor.cf, 'ThreadPoolExecutor', NoWorkers)
    monkeypatch.setattr(executor, 'sync', lambda: None)
    monkeypatch.setattr(executor, 'refresh_from_main_or_fail_closed', lambda: True)
    monkeypatch.setattr(executor, 'load_table', lambda: {})
    monkeypatch.setattr(executor, 'capabilities', lambda *a: {})
    monkeypatch.setattr(executor.time, 'time', lambda: 1000)
    monkeypatch.setattr(executor.time, 'sleep', lambda _: (executor.RUN / 'STOP_executor').touch())
    assert executor.main() == 0
    completion = json.loads((executor.REC / 'apply.completion.json').read_text())
    assert completion['status'] == 'COMPLETED' and completion['run_id'] == S.RUN
    assert completion['absence_receipt'] == rr
    assert executor.FENCE.exists()


@pytest.mark.parametrize('profile', ['one_class_full', 'all_classes_1y'])
@pytest.mark.parametrize('active_run', [False, True])
def test_launch_bridge_dryrun_uses_real_staging_admission_and_rollback_only(
        tmp_path, capsys, profile, active_run):
    from test_dispatch_v5_small_test import _Harness, _run_main
    spec = importlib.util.spec_from_file_location('j1a_dryrun_bridge', FLEET / 'smalltest_launch.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    h = _Harness(active_runs=[{'id': S.RUN, 'state': 'running'}] if active_run else [])
    reports = []
    def rehearse(argv):
        assert '--dry-run' in argv and '--execute' not in argv
        reports.append(_run_main(h, argv, capsys))
    def forbidden(*a, **kw):
        pytest.fail('dry run entered the launch/claim boundary')
    bridge._write_claim = forbidden
    dispatcher = SimpleNamespace(build_slice_marker=dispatch.build_slice_marker, main=rehearse)
    argv = ['--run', profile, '--classes', 'marriage' if profile == 'one_class_full' else 'all', '--dry-run']
    if profile == 'all_classes_1y':
        argv += ['--horizon-start', '2025-01-01T00:00:00+00:00', '--horizon-end', '2026-01-01T00:00:00+00:00']
    def run():
        return bridge.run(argv, dispatcher=dispatcher, connect=forbidden, launcher=forbidden, claim_dir=tmp_path)
    if active_run:
        with pytest.raises(shared.Refused, match='already active'):
            run()
        assert not any('INSERT INTO' in sql for sql in h.statements)
    else:
        assert run() is None
        assert len(reports) == 1
        report = json.loads(reports[0].out)
        assert report['plan_manifest']['gochara_v5_test_slice']['run'] == profile
        assert 'ROLLED BACK' in reports[0].err
    assert not h.commits and len(h.rollbacks) == 1
    assert not list(tmp_path.iterdir())
