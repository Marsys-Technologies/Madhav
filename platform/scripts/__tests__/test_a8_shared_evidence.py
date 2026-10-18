"""A8 (§3.8, §3.9) and A7 D-44: the small-test children's evidence rules, one oracle per claim.

  1. operation_request demands NO V acceptance for a `*_dryrun` kind (read-only with a credential) and exactly one — an ACCEPTED receipt
     by one V slot, bound to the request — for a writing kind;
  2. dryrun_evidence takes the dry run's executor receipt (COMPLETED, exit 0, its kind) as the whole evidence: no dry-run acceptance
     is read or required;
  3. accepted_receipt, still used for the writing kinds (a dispatch's receipt), needs that one V acceptance and nothing else.
Filesystem fixtures only; no database, no remote call.
"""
import json

import pytest

import smalltest_safety_support as S
import v5_small_test_shared as shared


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    return tmp_path


def _as_request(monkeypatch, req):
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))


def test_a_dry_run_request_needs_no_acceptance_and_a_writing_request_needs_exactly_one(root, monkeypatch):
    dry = dict(operation_id='rehearse', kind='smalltest_teardown_dryrun', reviewed_commit=S.COMMIT)      # no acceptance_receipt, lease or chart_id
    _as_request(monkeypatch, dry)
    assert shared.operation_request() == dry
    writing = dict(operation_id='apply', kind='smalltest_teardown')
    _as_request(monkeypatch, writing)
    with pytest.raises(shared.Refused):                       # a writing kind with no acceptance
        shared.operation_request()
    accepted = S.authorize(root, dict(writing))
    _as_request(monkeypatch, accepted)
    assert shared.operation_request() == accepted             # one V acceptance bound to the request
    path = root / 'run/ops/acceptance/apply.json'
    record = json.loads(path.read_text())
    path.write_text(json.dumps(dict(record, by='b1')))        # a builder slot is not a signer
    with pytest.raises(shared.Refused):
        shared.operation_request()


def test_dry_run_evidence_is_the_executor_receipt_alone(root):
    scope = {'run_id': S.RUN}
    teardown = dict(schema='ky.smalltest_teardown/1', status='ROLLED_BACK', rollback_confirmed=True, operation_id='dryrun',
                    request_sha256='b' * 64, scope=scope, scope_sha256=shared.evidence_digest(scope), rowset_sha256='c' * 64)
    receipt = dict(kind='smalltest_teardown_dryrun', operation_id='dryrun', status='COMPLETED', exit_code=0, item_id='J-2a',
                   request_sha256='b' * 64, reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00', teardown=teardown)
    ref = S.put(root, 'receipts', 'dryrun', receipt)
    req = S.authorize(root, dict(operation_id='apply', kind='smalltest_teardown', dryrun_receipt=ref))
    assert not (root / 'run/ops/acceptance/dryrun.json').exists()       # nobody accepted the dry run
    assert shared.dryrun_evidence(req, shared.evidence_root(), scope, 'c' * 64) == teardown
    for change in (dict(status='FAILED'), dict(exit_code=1), dict(kind='smalltest_dispatch_dryrun')):    # the receipt can still read false
        req['dryrun_receipt'] = S.put(root, 'receipts', 'dryrun', dict(receipt, **change))
        with pytest.raises(shared.Refused):
            shared.dryrun_evidence(req, shared.evidence_root(), scope, 'c' * 64)


def test_a_writing_kinds_receipt_needs_its_one_v_acceptance(root):
    rref, aref = S.accepted(root, 'smalltest_dispatch', 'dispatch')
    receipt, acceptance = shared.accepted_receipt(shared.evidence_root(), rref, aref, 'smalltest_dispatch')
    assert receipt['kind'] == 'smalltest_dispatch' and acceptance['by'] == 'v1'
    with pytest.raises(shared.Refused):                       # no acceptance named
        shared.accepted_receipt(shared.evidence_root(), rref, None, 'smalltest_dispatch')
    forged = json.loads((root / 'run/ops/acceptance/dispatch.json').read_text())
    with pytest.raises(shared.Refused):                       # a signer outside the V slots
        shared.accepted_receipt(shared.evidence_root(), rref, S.put(root, 'acceptance', 'dispatch', dict(forged, by='b1')), 'smalltest_dispatch')


# ── OWNER-MINIMAL-PROTECTION-NOW: the executor's own mechanical PRE-acceptance (executor.mechanical_pre_acceptance) is an independent acceptance too ──

def _mechanical_record(req, **over):
    record = dict(schema='ky.mechanical_acceptance/1', phase='pre', by='executor-mechanical', result='ACCEPTED', operation_id=req['operation_id'],
                  request_sha256=shared.request_hash(req), reviewed_commit=req['reviewed_commit'], ts='2026-10-18T00:00:00+00:00',
                  checks={'request_equals_verified_pack_fill': True, 'dry_run_completed_ok_for_same_identity': True, 'lease_live': True})
    record.update(over)
    return record


def _pack_fill_request(root, **over):
    req = dict(operation_id='mech', kind='smalltest_dispatch', chart_id=shared.CHART_ID, reviewed_commit=S.COMMIT,
               pack_fill=dict(pack_manifest_sha256='a' * 64, template={}, fill_sha256='b' * 64))     # no acceptance_receipt: the executor accepted it itself
    req.update(over)
    return req


def test_a_mechanically_accepted_request_needs_no_signer_but_only_its_own_complete_record(root, monkeypatch):
    req = _pack_fill_request(root)
    S.put(root, 'acceptance', 'mech', _mechanical_record(req))
    _as_request(monkeypatch, req)
    assert shared.operation_request() == req                                       # the child accepts the executor's record: schema, phase pre, every check true, bound to the request
    for label, change in (('a check that is not true', dict(checks={'lease_live': True, 'request_equals_verified_pack_fill': False})),
                          ('no checks at all', dict(checks={})),
                          ('a post-acceptance (a readback judged nothing about a write)', dict(phase='post')),
                          ('another schema', dict(schema='ky.mechanical_quiescence/1')),
                          ('another request', dict(request_sha256='0' * 64))):
        S.put(root, 'acceptance', 'mech', _mechanical_record(req, **change))
        with pytest.raises(shared.Refused):
            shared.operation_request()
    S.put(root, 'acceptance', 'mech', _mechanical_record(req))
    bare = dict(req); bare.pop('pack_fill')                                         # without a pack fill there is no mechanical route: the missing signer is refused as before
    S.put(root, 'acceptance', 'mech', _mechanical_record(bare))
    _as_request(monkeypatch, bare)
    with pytest.raises(shared.Refused):
        shared.operation_request()


def test_a_mechanical_dispatch_acceptance_can_be_cited_by_its_signed_teardown_scope_but_a_readbacks_post_acceptance_cannot(root):
    rref, _ = S.accepted(root, 'smalltest_dispatch', 'dispatch')
    receipt = json.loads((root / 'run/ops/receipts/dispatch.json').read_text())
    pre = dict(schema='ky.mechanical_acceptance/1', phase='pre', by='executor-mechanical', result='ACCEPTED', operation_id='dispatch',
               request_sha256=receipt['request_sha256'], reviewed_commit=receipt['reviewed_commit'], checks={'request_equals_verified_pack_fill': True})
    assert shared.accepted_receipt(shared.evidence_root(), rref, S.put(root, 'acceptance', 'dispatch', pre), 'smalltest_dispatch')[1]['by'] == 'executor-mechanical'
    post = dict(pre, phase='post')
    with pytest.raises(shared.Refused):
        shared.accepted_receipt(shared.evidence_root(), rref, S.put(root, 'acceptance', 'dispatch', post), 'smalltest_dispatch')
