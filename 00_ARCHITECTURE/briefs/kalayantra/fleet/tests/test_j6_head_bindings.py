"""J6 bindings: no cloud, Git writes, credentials, production, or child processes."""
import copy
import csv
import io
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import uuid

import pytest

FLEET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLEET))
import head_operation as head

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
MID = str(uuid.UUID(int=50))
BEFORE = dict(generation='3.0', flipped_at='2025-01-01T00:00:00+00:00', flipped_by='prior', evidence_ref='retained')


def decision(outcome='approved', **over):
    event = dict(kind='decision', decision='D-FLIP', state='delegated', actor='steward',
                 ts='2026-10-16T00:00:00+00:00', outcome=outcome, detail='fixture controller decision')
    event.update(over)
    return event


def request(kind='publish_head_dryrun'):
    scope = dict(expected_head=copy.deepcopy(BEFORE), target=dict(generation='5.0', manifest_id=MID),
                 change_at='2026-10-16T01:00:00+00:00')
    return dict(operation_id='J-6-attempt-1', item_id='J-6', kind=kind, requested_by='adhikarin',
                idempotency_key='j6-test', kyd='fixture-only', chart_id=CHART, reviewed_commit='a'*40,
                args={'generation': '5.0', 'manifest-id': MID, 'expected-head-sha256': head.sha(BEFORE)},
                head_change=scope, decision_event_sha256=head.sha(decision()))


def stage(req):
    return dict(schema='ky.head_change/1', status='ROLLED_BACK', rollback_confirmed=True,
                operation_id=req['operation_id'], request_sha256=head.request_digest(req),
                chart_id=CHART, reviewed_commit=req['reviewed_commit'], head_change=req['head_change'],
                before=req['head_change']['expected_head'], after=head.replacement(req), retained_rows_equal=True,
                retained_before={t:{'rows':0,'sha256':hashlib.sha256(b'').hexdigest()} for t in head.RETAINED_TABLES},
                retained_after={t:{'rows':0,'sha256':hashlib.sha256(b'').hexdigest()} for t in head.RETAINED_TABLES})


def receipt(req, proof):
    return dict(status='COMPLETED', operation_id=req['operation_id'], kind=req['kind'], item_id=req['item_id'],
                reviewed_commit=req['reviewed_commit'], request_sha256=head.request_digest(req),
                head_change=proof, ts='2026-10-16T01:00:00+00:00')


def setup_ops(tmp_path):
    ops = tmp_path / 'run' / 'ops'
    (ops / 'receipts').mkdir(parents=True)
    (ops.parent / 'EVENTS.jsonl').write_text(json.dumps(decision())+'\n')
    return ops


def store(ops, name, doc):
    path = ops / 'receipts' / name
    raw = json.dumps(doc).encode()
    path.write_bytes(raw)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def test_actual_bindings_and_dryruns_exist_but_stay_disabled():
    ops = json.loads((FLEET/'executor_ops.json').read_text())['ops']
    for kind in ('publish_head', 'rollback_head', 'publish_head_dryrun', 'rollback_head_dryrun'):
        entry = ops[kind]
        assert next(iter(entry)) == 'enabled' and entry['enabled'] is False
        assert entry['script'] == '00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py'
        assert entry['needs'] == 'builder' and entry['production'] is (not kind.endswith('_dryrun'))   # A8 §3.8: a dry run is production:false
        assert entry['allowed_args'] == ['generation', 'manifest-id', 'expected-head-sha256']
        assert entry['fixed_args'] == ['--kind', kind.removesuffix('_dryrun'),
                                       '--dry-run' if kind.endswith('_dryrun') else '--execute']
        assert 'required_rows' not in entry     # A8 §5: retired from the table; the head policy itself still demands head.G6_ROWS / ROLLBACK_ROWS


@pytest.mark.parametrize('outcome,effective', [('approved', True), ('refused', True), ('deferred', False), ('insufficient_evidence', False)])
def test_n_flip_consumes_only_latest_controller_decision(outcome, effective):
    result = head.flip_decision([decision(), decision(outcome)])
    assert result['effective'] is effective and result['outcome'] == outcome
    assert result['event_sha256'] == head.sha(decision(outcome))
    assert result['flip_authorized'] is (outcome == 'approved')


@pytest.mark.parametrize('event', [None, decision(state='requested'), decision(actor='builder'), decision(detail='')])
def test_default_proposal_missing_or_unauthorized_decision_cannot_authorize(event):
    result = head.flip_decision([] if event is None else [decision(), event])
    assert result['effective'] is False and result['flip_authorized'] is False


def test_publish_requires_latest_approved_event_and_exact_scope(tmp_path):
    ops = setup_ops(tmp_path)
    req = request()
    assert head.request_problem(req, ops) is None
    for outcome in ('refused', 'deferred', 'insufficient_evidence'):
        (ops.parent/'EVENTS.jsonl').write_text(json.dumps(decision(outcome))+'\n')
        assert 'D-FLIP' in head.request_problem(req, ops)
    (ops.parent/'EVENTS.jsonl').write_text(json.dumps(decision())+'\n')
    for mutate in (
        lambda r: r['args'].update(generation='5.1'),
        lambda r: r['args'].update({'expected-head-sha256': '0'*64}),
        lambda r: r.update(chart_id=str(uuid.UUID(int=3))),
        lambda r: r['head_change']['target'].update(manifest_id='not-uuid'),
        lambda r: r['head_change']['expected_head'].pop('evidence_ref'),
        lambda r: r['head_change'].update(sql='UPDATE anything'),
        lambda r: r.update(item_id='other'),
    ):
        bad = copy.deepcopy(req); mutate(bad)
        assert head.request_problem(bad, ops) is not None


def test_execute_needs_hash_bound_real_dryrun_of_identical_scope(tmp_path):
    ops = setup_ops(tmp_path)
    dry = request()
    req = request('publish_head')
    assert 'dry-run' in head.request_problem(req, ops)
    req['dry_run_receipt'] = store(ops, 'dry.json', receipt(dry, stage(dry)))
    assert head.request_problem(req, ops) is None
    for mutate in (lambda p: p.update(rollback_confirmed=False),
                   lambda p: p.update(status='PREPARATION_ONLY'),
                   lambda p: p['head_change']['target'].update(manifest_id=str(uuid.UUID(int=51))),
                   lambda p: p.update(retained_rows_equal=False),
                   lambda p: p.update(reviewed_commit='b'*40)):
        proof = stage(dry); mutate(proof)
        req['dry_run_receipt'] = store(ops, 'dry.json', receipt(dry, proof))
        assert head.request_problem(req, ops) is not None
    req['dry_run_receipt']['sha256'] = '0'*64
    assert head.request_problem(req, ops) is not None


def test_publish_refuses_a_decision_digest_that_is_not_the_latest_approved_event(tmp_path):
    # Latest controller D-FLIP event wins (tracker.state.decision_status); the request must bind that event's digest.
    ops = setup_ops(tmp_path)
    (ops.parent/'EVENTS.jsonl').write_text(json.dumps(decision(detail='earlier'))+'\n'+json.dumps(decision())+'\n')
    stale = request(); stale['decision_event_sha256'] = head.sha(decision(detail='earlier'))
    assert head.request_problem(stale, ops) == 'D-FLIP_latest_effective_approved_event_required'
    assert head.request_problem(request(), ops) is None


def test_j6_publishes_only_generation_5_0(tmp_path):
    # Plan item J-6 is the 5.0 flip; another well-formed governed target (args bound to it) must still be refused.
    ops = setup_ops(tmp_path)
    other = request()
    other['head_change']['target']['generation'] = '6.0'
    other['args']['generation'] = '6.0'
    assert head.shape(other)['target']['generation'] == '6.0'      # well-formed: only the J-6 policy can refuse it
    assert head.request_problem(other, ops) == 'J-6_requires_5.0'


def test_execute_refuses_a_self_consistent_dryrun_receipt_for_another_scope(tmp_path):
    # A real dry run of a different manifest, with its own consistent request digest, is not the dry run of this scope.
    ops = setup_ops(tmp_path)
    other_dry = request(); other_manifest = str(uuid.UUID(int=51))
    other_dry['head_change']['target']['manifest_id'] = other_manifest
    other_dry['args']['manifest-id'] = other_manifest
    head.shape(other_dry)
    req = request('publish_head')
    req['dry_run_receipt'] = store(ops, 'other-dry.json', receipt(other_dry, stage(other_dry)))
    assert head.request_problem(req, ops) == 'dry-run_exact_scope_rollback_receipt_required'


def rollback_request(ops):
    pub = request('publish_head')
    proof = stage(pub)
    proof.update(status='COMMITTED_AWAITING_READBACK', rollback_confirmed=False)
    committed = receipt(pub, proof); committed['status'] = 'AWAITING_READBACK'
    req = request('rollback_head_dryrun')
    req['item_id'] = 'J-6r'
    req['head_change'] = dict(expected_head=proof['after'], target=dict(generation='3.0', manifest_id=None),
                              restore_head=BEFORE, change_at='2026-10-16T02:00:00+00:00')
    req['args'] = {'generation':'3.0', 'manifest-id':'none', 'expected-head-sha256': head.sha(proof['after'])}
    req['rollback_of'] = store(ops, 'publish.json', committed)
    return req


def test_rollback_restores_only_the_original_full_retained_row(tmp_path):
    ops = setup_ops(tmp_path)
    req = rollback_request(ops)
    assert head.request_problem(req, ops) is None
    assert head.replacement(req) == BEFORE
    req['head_change']['restore_head']['evidence_ref'] = 'invented'
    assert 'retained' in head.request_problem(req, ops)
    req = rollback_request(ops)
    req['rollback_of']['path'] = str(tmp_path/'outside.json')
    assert head.request_problem(req, ops) is not None


def executor(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('j6_executor', FLEET/'executor.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    ops = setup_ops(tmp_path)
    monkeypatch.setattr(mod, 'OPS', ops); monkeypatch.setattr(mod, 'REC', ops/'receipts')
    monkeypatch.setattr(mod, 'log', lambda *a: None)
    def git(*args, **kw):
        assert args[0] == 'show', args  # no fetch, writes or remote access
        source = (FLEET/'head_operation.py').read_text()
        import subprocess
        return subprocess.CompletedProcess(args, 0, source, '')
    monkeypatch.setattr(mod, 'git', git)
    return mod


def test_real_executor_rejects_exit_zero_without_bound_head_proof(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    req = request('publish_head')
    ex.receipt(req, 'COMPLETED', rc=0, out='{}')
    got = json.loads((ex.REC/(req['operation_id']+'.json')).read_text())
    assert got['status'] == 'FAILED'


def test_real_executor_stages_commit_as_awaiting_independent_readback(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    req = request('publish_head')
    proof = stage(req); proof.update(status='COMMITTED_AWAITING_READBACK', rollback_confirmed=False)
    ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps(proof))
    got = json.loads((ex.REC/(req['operation_id']+'.json')).read_text())
    assert got['status'] == 'AWAITING_READBACK' and got['head_change'] == proof
    bad = copy.deepcopy(proof); bad['request_sha256'] = '0'*64
    ex.receipt(req, 'COMPLETED', rc=0, out=json.dumps(bad))
    assert json.loads((ex.REC/(req['operation_id']+'.json')).read_text())['status'] == 'FAILED'


def test_real_executor_loads_policy_from_reviewed_commit_and_applies_it(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    req = request('publish_head')
    assert 'dry-run' in ex.head_policy_problem(req)
    req['kind'] = 'readback_sql'
    assert ex.head_policy_problem(req) is None


def test_post_readback_requires_exact_sql_output_request_and_independent_acceptance(tmp_path):
    req = request('publish_head')
    proof = stage(req); proof.update(status='COMMITTED_AWAITING_READBACK', rollback_confirmed=False)
    commit = receipt(req, proof); commit['status'] = 'AWAITING_READBACK'
    commit_raw = json.dumps(commit).encode()
    query = head.readback_sql(req)
    assert 'ka_gochara_generation_is_sealed' in query and MID in query and CHART in query
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
    writer.writerow(['head_readback']); writer.writerow([json.dumps(head.expected_readback(req))])
    output = stream.getvalue().encode()
    rb_req = dict(operation_id='J6-observe', item_id='J-6', kind='readback_sql', requested_by='v1',
                  args={'sql_file':'run/ops/sql/j6.sql','sql_sha256':head.raw_sha(query.encode())})
    rb = dict(operation_id='J6-observe', item_id='J-6', kind='readback_sql', status='COMPLETED',
              requested_by='v1', request_sha256=head.request_digest(rb_req),
              output_sha256=hashlib.sha256(output).hexdigest())
    rb_raw = json.dumps(rb).encode()
    accepted = dict(result='ACCEPTED', by='v2', operation_id=req['operation_id'],
                    request_sha256=head.request_digest(req), receipt_sha256=hashlib.sha256(commit_raw).hexdigest(),
                    readback_receipt_sha256=hashlib.sha256(rb_raw).hexdigest())
    result = head.complete(req, commit_raw, rb_req, rb_raw, output, accepted)
    assert result['status'] == 'COMPLETED' and result['operation_id'] == req['operation_id']
    for mutation in ('output', 'reader', 'receipt', 'acceptance'):
        rbr = copy.deepcopy(rb_req); acc = copy.deepcopy(accepted); raw = output
        if mutation == 'output': raw = b'{}'
        if mutation == 'reader': rbr['requested_by'] = 'adhikarin'
        if mutation == 'receipt': acc['receipt_sha256'] = '0'*64
        if mutation == 'acceptance': acc['by'] = 'adhikarin'
        with pytest.raises(head.Refused):
            head.complete(req, commit_raw, rbr, rb_raw, raw, acc)


def test_completion_rejects_unbound_readback_query_even_if_output_was_plausible(tmp_path):
    req=request('publish_head');proof=stage(req)
    proof.update(status='COMMITTED_AWAITING_READBACK',rollback_confirmed=False)
    commit=receipt(req,proof);commit['status']='AWAITING_READBACK';commit_raw=json.dumps(commit).encode()
    stream=io.StringIO();writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
    writer.writerow(['head_readback']);writer.writerow([json.dumps(head.expected_readback(req))]);output=stream.getvalue().encode()
    rb_req=dict(operation_id='observe',item_id='J-6',kind='readback_sql',requested_by='v1',
                args={'sql_file':'run/ops/sql/j6.sql','sql_sha256':'0'*64})
    rb=dict(operation_id='observe',item_id='J-6',kind='readback_sql',status='COMPLETED',requested_by='v1',
            request_sha256=head.request_digest(rb_req),output_sha256=head.raw_sha(output))
    rb_raw=json.dumps(rb).encode()
    acceptance=dict(result='ACCEPTED',by='v2',operation_id=req['operation_id'],request_sha256=head.request_digest(req),
                    receipt_sha256=head.raw_sha(commit_raw),readback_receipt_sha256=head.raw_sha(rb_raw))
    with pytest.raises(head.Refused,match='readback'):
        head.complete(req,commit_raw,rb_req,rb_raw,output,acceptance)


def test_readback_driver_checks_requested_query_digest_before_connecting(tmp_path,monkeypatch):
    # Execute the real embedded Python, with only the DB connect boundary faked.
    # No pgenv/secret is sourced, no socket or database is opened.
    # The governance shard installs only pyyaml and pytest, so the driver module is always a stand-in here: the script
    # only needs a `psycopg.connect` it can call, and the test only needs to see that it is never called.
    import types
    psycopg=types.ModuleType('psycopg')
    monkeypatch.setitem(sys.modules,'psycopg',psycopg)
    root=tmp_path/'ky';sql=root/'run/ops/sql/j6.sql';sql.parent.mkdir(parents=True)
    sql.write_text('SELECT 1 AS observed;')
    source=(FLEET/'readback_sql.sh').read_text().split("<<'KYPY'\n",1)[1].split('\nKYPY',1)[0]
    connected=[]
    def forbidden(*a,**kw):
        connected.append(1);raise AssertionError('connection attempted before digest refusal')
    psycopg.connect=forbidden
    monkeypatch.setattr(sys,'argv',['readback',str(root),'run/ops/sql/j6.sql','','0'*64])
    with pytest.raises(SystemExit,match='digest'):
        exec(compile(source,'readback_sql.sh embedded Python','exec'),{'__name__':'__main__'})
    assert not connected


def test_executor_g8_checks_remain_required_before_head_policy(tmp_path,monkeypatch):
    ex=executor(tmp_path,monkeypatch)
    acc=ex.OPS/'acceptance';acc.mkdir();monkeypatch.setattr(ex,'ACC',acc)
    monkeypatch.setattr(ex,'SEEN',ex.OPS/'idempotency.jsonl')
    monkeypatch.setattr(ex,'lease_live',lambda lease:lease=='fixture-live')
    real_git=ex.git
    def git(*args,**kw):
        if args[0]=='merge-base':
            import subprocess
            return subprocess.CompletedProcess(args,0,'','')
        return real_git(*args,**kw)
    monkeypatch.setattr(ex,'git',git)
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    fixture=copy.deepcopy(ops);fixture['publish_head']['enabled']=True
    req=request('publish_head')
    dry=request();req['dry_run_receipt']=store(ex.OPS,'dry.json',receipt(dry,stage(dry)))
    req.update(lease_id='fixture-live',expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat())
    accepted=dict(result='ACCEPTED',operation_id=req['operation_id'],by='v1',reviewed_commit=req['reviewed_commit'],
        ts=dt.datetime.now(dt.timezone.utc).isoformat(),rows={k:True for k in head.G6_ROWS},
        checks=dict(backup_taken=True,restore_verified=True,dry_run_passed=True),request_sha256=head.request_digest(req))
    path=acc/'pre.json';path.write_text(json.dumps(accepted));req['acceptance_receipt']=str(path)
    assert ex.validate(req,fixture,{'builder':True}) is None
    no_dry=copy.deepcopy(req);no_dry.pop('dry_run_receipt')
    bound=copy.deepcopy(accepted);bound['request_sha256']=head.request_digest(no_dry);path.write_text(json.dumps(bound))
    assert 'dry-run' in ex.validate(no_dry,fixture,{'builder':True})
    path.write_text(json.dumps(accepted))
    assert 'not enabled' in ex.validate(req,ops,{'builder':True})
    for key in ('dry_run_passed',):  # A8 §5 retired backup_taken / restore_verified as preconditions of a non-teardown kind
        bad=copy.deepcopy(accepted);bad['checks'][key]=False;path.write_text(json.dumps(bad))
        if key == 'dry_run_passed':
            assert 'attestation' in ex.validate(req,fixture,{'builder':True})
        else:                                                    # A8 §5: restore_verified retired; backup_taken only for a *_teardown
            assert ex.validate(req,fixture,{'builder':True}) is None
    for key in head.G6_ROWS:                                     # A8 §5: the executor no longer gates on checklist rows (the verifier's acceptance owns them)
        bad=copy.deepcopy(accepted);bad['rows'].pop(key);path.write_text(json.dumps(bad))
        assert ex.validate(req,fixture,{'builder':True}) is None
    path.write_text(json.dumps(accepted))
    assert 'lease' in ex.validate({**req,'lease_id':'expired'},fixture,{'builder':True})
    assert 'complete request' in ex.validate({**req,'kyd':'different'},fixture,{'builder':True})
    ex.receipt(req,'RUNNING')
    assert ex.validate(req,fixture,{'builder':True},reserved=True) is None
    assert 'already has a receipt' in ex.validate(req,fixture,{'builder':True})


def test_head_proof_requires_measured_equal_relation_fingerprints(tmp_path,monkeypatch):
    ex=executor(tmp_path,monkeypatch);req=request('publish_head')
    valid=stage(req);valid.update(status='COMMITTED_AWAITING_READBACK',rollback_confirmed=False)
    for mutate in (lambda p:p.pop('retained_before'),lambda p:p['retained_after'].update(kala_gochara_publication={'rows':1,'sha256':'0'*64})):
        bad=copy.deepcopy(valid);mutate(bad)
        ex.receipt(req,'COMPLETED',rc=0,out=json.dumps(bad))
        assert json.loads((ex.REC/(req['operation_id']+'.json')).read_text())['status']=='FAILED'


def test_readback_parses_real_executor_trailing_newline_and_refuses_extra_rows():
    req=request('publish_head');stream=io.StringIO();writer=csv.writer(stream,delimiter='\t',lineterminator='\n')
    writer.writerow(['head_readback']);writer.writerow([json.dumps(head.expected_readback(req))])
    raw=stream.getvalue().encode()
    assert head.decode_readback(raw+b'\n')==head.expected_readback(req)
    with pytest.raises(head.Refused): head.decode_readback(raw+b'{}\n')
    with pytest.raises(head.Refused): head.load_json('{"status":"ACCEPTED","status":"FAILED"}')


def test_offline_decision_and_readback_cli_never_write_operational_state(tmp_path,capsys):
    events=tmp_path/'events.jsonl';events.write_text(json.dumps(decision('deferred'))+'\n')
    before=set(tmp_path.iterdir())
    assert head.evidence_main(['decision','--events',str(events)])==0
    got=json.loads(capsys.readouterr().out)
    assert got['effective'] is False and got['outcome']=='deferred'
    req=request('publish_head');path=tmp_path/'request.json';path.write_text(json.dumps(req))
    assert head.evidence_main(['readback-sql','--request',str(path)])==0
    assert capsys.readouterr().out==head.readback_sql(req)
    assert set(tmp_path.iterdir())==before|{path}


def test_head_operation_id_cannot_overwrite_a_prior_receipt(tmp_path,monkeypatch):
    ex=executor(tmp_path,monkeypatch)
    # The early guard runs before a lease or credential is consulted.
    req=request('publish_head')
    (ex.REC/(req['operation_id']+'.json')).write_text('{"status":"FAILED"}')
    table=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    fixture=copy.deepcopy(table);fixture['publish_head']['enabled']=True
    assert 'already has a receipt' in ex.validate(req,fixture,{'builder':True})


def test_rollback_execute_requires_its_own_exact_dryrun_and_can_consume_prior_flip_when_decision_reopens(tmp_path):
    ops=setup_ops(tmp_path);dry=rollback_request(ops)
    req=copy.deepcopy(dry);req['kind']='rollback_head';req['operation_id']='rollback-execute'
    assert 'dry-run' in head.request_problem(req,ops)
    req['dry_run_receipt']=store(ops,'rollback-dry.json',receipt(dry,stage(dry)))
    # A later deferred flip decision cannot prevent explicit retained-head rollback.
    (ops.parent/'EVENTS.jsonl').write_text(json.dumps(decision('deferred'))+'\n')
    assert head.request_problem(req,ops) is None
    req['head_change']['restore_head']['flipped_by']='invented'
    assert 'retained' in head.request_problem(req,ops)


@pytest.mark.parametrize('kind', ['publish_head', 'rollback_head', 'publish_head_dryrun', 'rollback_head_dryrun'])
@pytest.mark.parametrize('enabled', [True, False])
@pytest.mark.parametrize('prior_status', ['AWAITING_READBACK', 'RUNNING', 'FAILED', 'unreadable'])
def test_main_duplicate_refusal_preserves_receipt_and_retained_head_bytes(tmp_path, monkeypatch, kind, enabled, prior_status):
    ex = executor(tmp_path, monkeypatch)
    root = tmp_path
    for attr, path in {
        'KY_ROOT': root, 'RUN': root/'run', 'OPS': root/'run/ops',
        'REQ': root/'run/ops/requests', 'REC': root/'run/ops/receipts',
        'DONE': root/'run/ops/done', 'ACC': root/'run/ops/acceptance',
        'INFLIGHT': root/'run/ops/inflight', 'TMP': root/'run/ops/tmp',
        'EXEC': root/'exec', 'FENCE': root/'run/ops/PRODUCTION_PENDING.json',
        'SEEN': root/'run/ops/idempotency.jsonl',
    }.items():
        monkeypatch.setattr(ex, attr, path)
    ex.REQ.mkdir()
    req = request(kind)
    prior_req = request('publish_head')
    original = receipt(prior_req, stage(prior_req))
    original['status'] = prior_status
    original_raw = json.dumps(original, indent=2).encode() if prior_status != 'unreadable' else b'{retained-unreadable'
    original_path = ex.REC/(req['operation_id']+'.json')
    original_path.write_bytes(original_raw)
    output_path = ex.REC/(req['operation_id']+'.output.txt')
    output_path.write_bytes(b'original adapter output evidence\n')
    table = json.loads((FLEET/'executor_ops.json').read_text())['ops']
    table[kind]['enabled'] = enabled  # fixture only; authority stays disabled in source
    monkeypatch.setattr(ex, 'sync', lambda: None)
    monkeypatch.setattr(ex, 'load_table', lambda: table)
    monkeypatch.setattr(ex, 'refresh_from_main_or_fail_closed', lambda: True)
    monkeypatch.setattr(ex, 'capabilities', lambda _: {'builder': True})
    def forbidden(*args, **kwargs):
        pytest.fail('duplicate refusal must not consult a lease or dispatch an operation')
    monkeypatch.setattr(ex, 'lease_live', forbidden)
    monkeypatch.setattr(ex, 'execute', forbidden)
    monkeypatch.setattr(ex.time, 'sleep', lambda _: (ex.RUN/'STOP_executor').touch())
    for attempt in range(2):
        (ex.RUN/'STOP_executor').unlink(missing_ok=True)
        queued = ex.REQ/'duplicate-request.json'
        queued.write_text(json.dumps(req))
        assert ex.main() == 0
        assert original_path.read_bytes() == original_raw
        assert output_path.read_bytes() == b'original adapter output evidence\n'
        refusals = sorted((ex.REC/'refusals').glob('*.json'))
        assert len(refusals) == attempt + 1
        for path in refusals:
            refused = json.loads(path.read_text())
            assert refused['status'] == 'REFUSED'
            assert refused['operation_id'] == req['operation_id']
            assert refused['request_sha256'] == head.request_digest(req)
            assert refused['preserved_receipt'] == {
                'path': str(original_path), 'sha256': hashlib.sha256(original_raw).hexdigest(),
            }
        assert not queued.exists() and (ex.DONE/queued.name).exists()
        assert not ex.SEEN.exists() and not ex.FENCE.exists()
        assert not list(ex.INFLIGHT.iterdir())


def test_reserved_operation_refusal_still_finishes_its_own_running_receipt(tmp_path, monkeypatch):
    ex = executor(tmp_path, monkeypatch)
    req = request('publish_head')
    ex.receipt(req, 'RUNNING')
    ex.receipt(req, 'REFUSED', 'operation definition changed before execution')
    got = json.loads((ex.REC/(req['operation_id']+'.json')).read_text())
    assert got['status'] == 'REFUSED'
    assert got['reason'] == 'operation definition changed before execution'
    assert not (ex.REC/'refusals').exists()
