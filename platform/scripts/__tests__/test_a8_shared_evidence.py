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
