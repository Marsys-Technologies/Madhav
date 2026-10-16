"""W4 production-deletion boundary over the suite's guarded loopback mirror.

Unlike the inherited SQL guard fixtures, this suite consumes the real teardown's
successful rollback proof before permitting its real commit. No cloud calls.
"""
import csv
import hashlib
import io
import json
import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import pytest

from .test_c38_teardown_real_db import tworld, template, _slice_run, _step, _counts  # noqa: F401
from pipeline.orchestrator.writers import ka_gochara_v5 as writer

SCRIPTS = Path(__file__).resolve().parents[5] / 'platform/scripts'
sys.path.insert(0, str(SCRIPTS)); sys.path.insert(0, str(SCRIPTS / '__tests__'))
import teardown_v5_small_test_job as td
import v5_small_test_shared as shared
import smalltest_safety_support as S


def candidate(w):
    rid = _slice_run(w, build=False)
    _step(w, rid, writer.MANIFEST_SUBSTEP)
    _step(w, rid, writer.SNAPSHOT_SUBSTEP)
    return str(rid)


def bind(w, root, monkeypatch, *, dry_run, rowset=None):
    with psycopg.connect(w.dsn, row_factory=dict_row, autocommit=True) as conn:
        run = conn.execute('SELECT id, plan_manifest FROM build_runs ORDER BY created_at DESC LIMIT 1').fetchone()
        manifest = conn.execute('SELECT manifest_id, input_generation_vector FROM kala_gochara_publication WHERE chart_id=%s AND generation=%s',
                                (shared.CHART_ID, shared.GENERATION)).fetchone()
    scope = S.scope_for(root, str(run['id']), run['plan_manifest'], manifest)
    req = S.request_for(root, scope, dry_run=dry_run, rowset_sha256=rowset)
    monkeypatch.setenv('KY_ROOT', str(root)); monkeypatch.setenv('DATABASE_URL', w.dsn)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    return req


def real_dryrun(w, root, monkeypatch, capsys):
    req = bind(w, root, monkeypatch, dry_run=True)
    before = _counts(w)
    td.teardown(dry_run=True)
    proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert proof['status'] == 'ROLLED_BACK' and proof['rollback_confirmed'] is True
    assert _counts(w) == before
    # Independent executor/verifier transport of the ACTUAL proof just emitted.
    receipt = dict(kind='smalltest_teardown_dryrun', operation_id=req['operation_id'], item_id='J-2b',
        request_sha256=shared.request_hash(req), reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00',
        status='COMPLETED', exit_code=0, teardown=proof)
    rr = S.put(root, 'receipts', 'real-rehearsal', receipt)
    ar = S.put(root, 'acceptance', 'real-rehearsal', dict(result='ACCEPTED', by='v1',
        operation_id=req['operation_id'], request_sha256=shared.request_hash(req), reviewed_commit=S.COMMIT))
    return rr, ar, proof


def apply_request(w, root, monkeypatch, rr, ar, proof):
    req = bind(w, root, monkeypatch, dry_run=False, rowset=proof['rowset_sha256'])
    req.update(dryrun_receipt=rr, dryrun_acceptance=ar)
    S.authorize(root, req)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    return req


def test_real_rollback_is_required_same_count_mutation_refuses_and_exact_rows_commit(tworld, tmp_path, monkeypatch, capsys):
    w = tworld
    candidate(w)
    rr, ar, proof = real_dryrun(w, tmp_path, monkeypatch, capsys)
    req = apply_request(w, tmp_path, monkeypatch, rr, ar, proof)
    before = _counts(w)
    original = w.conn.execute('SELECT freshness_state FROM asset_freshness WHERE asset_id=%s', (shared.ASSET_ID,)).fetchone()[0]
    w.conn.execute("UPDATE asset_freshness SET freshness_state='stale' WHERE asset_id=%s", (shared.ASSET_ID,))
    with pytest.raises(shared.Refused, match='same scope and row set'):
        td.teardown(dry_run=False)
    assert _counts(w) == before
    w.conn.execute('UPDATE asset_freshness SET freshness_state=%s WHERE asset_id=%s', (original, shared.ASSET_ID))
    td.teardown(dry_run=False)
    assert all(n == 0 for n in _counts(w).values())
    actual = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert actual['status'] == 'COMMITTED_AWAITING_ABSENCE'
    assert actual['rowset_sha256'] == proof['rowset_sha256']
    committed = dict(operation_id=req['operation_id'], kind='smalltest_teardown', status='AWAITING_ABSENCE', exit_code=0,
        request_sha256=shared.request_hash(req), reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00', teardown=actual)
    # A SEPARATE read-only connection executes the generated SELECT after COMMIT.
    with psycopg.connect(w.dsn, row_factory=dict_row) as observer:
        observer.read_only = True
        measured = json.loads(observer.execute(shared.absence_readback_sql(committed)).fetchone()['absence_proof'])
    assert measured['registry_inert'] is True and all(v == 0 for v in measured['counts'].values())
    output = io.StringIO(); out = csv.writer(output, delimiter='\t', lineterminator='\n')
    out.writerow(['absence_proof']); out.writerow([json.dumps(measured)])
    path = tmp_path / 'run/ops/receipts/independent.output.txt'; path.write_text(output.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(kind='readback_sql', operation_id='independent', status='COMPLETED', exit_code=0,
        request_sha256='e'*64, reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:01+00:00',
        output_file=str(path), output_sha256=digest)
    rref = S.put(tmp_path, 'receipts', 'independent', record)
    aref = S.put(tmp_path, 'acceptance', 'independent', dict(result='ACCEPTED', by='v3', operation_id='independent',
        request_sha256='e'*64, reviewed_commit=S.COMMIT, absence=dict(measured, output_sha256=digest)))
    assert shared.absence_evidence(dict(absence_receipt=rref, absence_acceptance=aref), shared.evidence_root(),
                                   teardown_receipt=committed)['run_id'] == actual['scope']['run_id']


def test_real_missing_rehearsal_refuses_before_deleting_rows(tworld, tmp_path, monkeypatch):
    w = tworld; candidate(w)
    req = bind(w, tmp_path, monkeypatch, dry_run=False)
    req.pop('dryrun_receipt'); S.authorize(tmp_path, req)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    before = _counts(w)
    with pytest.raises(shared.Refused, match='evidence reference'):
        td.teardown(dry_run=False)
    assert _counts(w) == before and before['kala_gochara_publication'] == 1


from ._measuring_binding_world import measuring_teardown_world  # noqa: F401


@pytest.mark.parametrize('shape', ['all_classes_full', 'one_class_full'])
def test_measuring_full_marker_rollback_then_commit_and_independent_absence(measuring_teardown_world, tmp_path, monkeypatch, capsys, shape):
    """Full measuring marker/manifest/vector through real guarded deletion SQL.

    Only manifest/snapshot substeps execute, not the full-horizon measurement.
    Prior launch/acceptance is synthetic transport; rollback and absence are real.
    """
    from .test_c38_teardown_real_db import _run
    import dispatch_v5_measuring_job as measuring
    w = measuring_teardown_world
    import dispatch_v5_small_test_job as smalltest
    marker = (measuring.build_slice_marker(run=shape, classes='all') if shape == 'all_classes_full' else
              smalltest.build_slice_marker(run=shape, classes='marriage'))
    rid = str(_run(w, marker=marker))
    _step(w, rid, writer.MANIFEST_SUBSTEP)
    _step(w, rid, writer.SNAPSHOT_SUBSTEP)
    with psycopg.connect(w.dsn, row_factory=dict_row, autocommit=True) as conn:
        run = conn.execute('SELECT plan_manifest FROM build_runs WHERE id=%s', (rid,)).fetchone()
        candidate = conn.execute('SELECT manifest_id, input_generation_vector FROM kala_gochara_publication').fetchone()
    scope = S.scope_for(tmp_path, rid, run['plan_manifest'], candidate)
    launch = dict(schema='ky.measuring_launch/1', status='LAUNCHED', run_id=rid, chart_id=shared.CHART_ID,
        asset_id=shared.ASSET_ID, plan_manifest_digest=scope['plan_manifest_digest'],
        execution_name='brahma-build-pipeline-job-measuringfixture')
    scope['dispatch_receipt'], scope['dispatch_acceptance'] = S.accepted(tmp_path, 'measuring_dispatch', 'dispatch', item_id='J-3c', launch=launch)
    req = S.authorize(tmp_path, dict(operation_id='rehearse', kind='measuring_teardown_dryrun', item_id='J-3d', measuring_scope=scope))
    monkeypatch.setenv('KY_ROOT', str(tmp_path)); monkeypatch.setenv('DATABASE_URL', w.dsn)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    before = _counts(w)
    if shape != 'all_classes_full':
        with pytest.raises(shared.Refused, match='original full measuring marker'):
            td.teardown(dry_run=True)
        assert _counts(w) == before
        return
    td.teardown(dry_run=True)
    proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert proof['schema'] == 'ky.measuring_teardown/1' and proof['rollback_confirmed'] is True
    assert _counts(w) == before
    rr, ar = S.accepted(tmp_path, 'measuring_teardown_dryrun', 'rehearse', item_id='J-3d',
        request_sha256=shared.request_hash(req), teardown=proof)
    req = S.authorize(tmp_path, dict(operation_id='apply', kind='measuring_teardown', item_id='J-3d',
        measuring_scope=scope, dryrun_receipt=rr, dryrun_acceptance=ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    # Same row count is insufficient: content mutation invalidates the rollback.
    original = w.conn.execute('SELECT freshness_state FROM asset_freshness WHERE asset_id=%s', (shared.ASSET_ID,)).fetchone()[0]
    w.conn.execute("UPDATE asset_freshness SET freshness_state='stale' WHERE asset_id=%s", (shared.ASSET_ID,))
    with pytest.raises(shared.Refused, match='same scope and row set'):
        td.teardown(dry_run=False)
    assert _counts(w) == before
    w.conn.execute('UPDATE asset_freshness SET freshness_state=%s WHERE asset_id=%s', (original, shared.ASSET_ID))
    td.teardown(dry_run=False)
    committed_proof = json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])
    assert committed_proof['status'] == 'COMMITTED_AWAITING_ABSENCE'
    committed = dict(operation_id='apply', kind='measuring_teardown', status='AWAITING_ABSENCE', exit_code=0,
        request_sha256=shared.request_hash(req), reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00', teardown=committed_proof)
    # Run the actual independent readback SQL on a separate transaction/connection.
    with psycopg.connect(w.dsn, autocommit=True) as conn:
        measured = json.loads(conn.execute(shared.absence_readback_sql(committed)).fetchone()[0])
    assert measured['run_id'] == rid and all(n == 0 for n in measured['counts'].values())
    assert measured['registry_inert'] is True
    output = io.StringIO(); out = csv.writer(output, delimiter='\t', lineterminator='\n')
    out.writerow(['absence_proof']); out.writerow([json.dumps(measured)])
    path = tmp_path / 'run/ops/receipts/independent.output.txt'; path.write_text(output.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rr, ar = S.accepted(tmp_path, 'readback_sql', 'independent', output_file=str(path), output_sha256=digest,
        ts='2026-10-15T00:00:01+00:00')
    ar = S.put(tmp_path, 'acceptance', 'independent', dict(result='ACCEPTED', by='v3', operation_id='independent',
        request_sha256='b' * 64, reviewed_commit=S.COMMIT, absence=dict(measured, output_sha256=digest)))
    assert shared.absence_evidence(dict(absence_receipt=rr, absence_acceptance=ar), shared.evidence_root(),
                                   teardown_receipt=committed)['run_id'] == rid
