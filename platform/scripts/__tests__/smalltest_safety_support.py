"""Filesystem evidence fixtures shared by the unit and guarded local DB suites."""
import datetime as dt
import hashlib
import json
from pathlib import Path

import v5_small_test_shared as shared

RUN = '11111111-1111-4111-8111-111111111111'
COMMIT = 'a' * 40


def put(root, folder, name, value):
    path = Path(root) / 'run/ops' / folder / (name + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return {'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def accepted(root, kind, name, **fields):
    receipt = dict(kind=kind, operation_id=name, status='COMPLETED', exit_code=0,
                   item_id='J-2a', request_sha256='b' * 64, reviewed_commit=COMMIT,
                   ts='2026-10-15T00:00:00+00:00')
    receipt.update(fields)
    rref = put(root, 'receipts', name, receipt)
    aref = put(root, 'acceptance', name, dict(operation_id=name, result='ACCEPTED', by='v1',
               request_sha256=receipt['request_sha256'], reviewed_commit=COMMIT))
    return rref, aref


FIXTURE_MEASURED = dict(tables={'public.a': dict(rows=1, sha256='a' * 64)}, sequences={})


def fixture_measure(tables, sequences, dsn=None, presence_only=None):
    """Stands in for backup_v5_small_test_job.measure_scope_now in suites that stage a dispatch against a fake database:
    the scoped content is unchanged since scoped_backup_for's capture. The measurement itself is proved in
    test_backup_v5_small_test_scoped.py and tests/l3/kala_db/test_p01_smalltest_backup_scoped.py."""
    return FIXTURE_MEASURED


def scoped_backup_for(root, label='p02_fixture', scope='small_test'):
    """A fresh, verified scoped backup + restore proof (what a dispatch must name; SR-J2A-BACKUP-SCOPE condition 4).
    One per root: a second call returns the fields of the first, so earlier approvals keep matching their bytes. `scope` names the reviewed scope the proof covers."""
    folder = Path(root) / 'run/ops/backups' / label
    if not (folder / 'restore.json').exists():
        started = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)
        window = dict(not_before=started.isoformat(), basis='scoped_content_digest_unchanged')
        measured = FIXTURE_MEASURED
        folder.mkdir(parents=True)
        (folder / 'capture.json').write_text(json.dumps(dict(schema='ky.smalltest_backup/2', label=label, archive_sha256='b' * 64,
            scope=dict(sha256=shared.SCOPED_BACKUP_SCOPE_SHA256S[scope]), validity=window, measurements=measured,
            measurement_method=shared.SCOPED_MEASUREMENT_METHOD, scoped_content_digest=shared.scoped_content_digest(measured)), sort_keys=True))
        (folder / 'restore.json').write_text(json.dumps(dict(schema='ky.smalltest_restore/2', label=label, status='verified',
            scoped=True, restore_verified=True, backup_taken=True, target_removed=True, archive_sha256='b' * 64,
            scope_sha256=shared.SCOPED_BACKUP_SCOPE_SHA256S[scope], validity=window, measurements=measured, ts=(started + dt.timedelta(minutes=10)).isoformat(),
            capture_sha256=hashlib.sha256((folder / 'capture.json').read_bytes()).hexdigest()), sort_keys=True))
    return dict(backup_label=label, backup_restore_sha256=hashlib.sha256((folder / 'restore.json').read_bytes()).hexdigest())


def authorize(root, req):
    if req.get('kind') in ('smalltest_dispatch', 'century_dispatch'):      # a century dispatch names its scoped backup too (SR-PREBUILD-ALL: scoped backup by content hash)
        for key, value in scoped_backup_for(root, scope='century' if req.get('kind') == 'century_dispatch' else 'small_test').items():
            req.setdefault(key, value)
    req['chart_id'] = shared.CHART_ID
    req['reviewed_commit'] = COMMIT
    req['acceptance_receipt'] = str(Path(root) / 'run/ops/acceptance' / (req['operation_id'] + '.json'))
    put(root, 'acceptance', req['operation_id'], dict(result='ACCEPTED', by='v2',
        operation_id=req['operation_id'], request_sha256=shared.request_hash(req), reviewed_commit=COMMIT,
        ts=dt.datetime.now(dt.timezone.utc).isoformat()))
    return req


def scope_for(root, run_id, manifest, candidate):
    digest = shared.evidence_digest(manifest)
    rr, ar = accepted(root, 'smalltest_dispatch', 'dispatch', launch=dict(schema='ky.smalltest_launch/1',
        status='LAUNCHED', run_id=run_id, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID,
        plan_manifest_digest=digest, execution_name='brahma-build-pipeline-job-fixture'))
    return dict(run_id=run_id, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID, generation=shared.GENERATION,
                plan_manifest_digest=digest, manifest_id=str(candidate['manifest_id']) if candidate else None,
                input_vector_sha256=shared.evidence_digest(candidate['input_generation_vector']) if candidate else None,
                dispatch_receipt=rr, dispatch_acceptance=ar)


def request_for(root, scope, *, dry_run=False, rowset_sha256=None):
    req = dict(operation_id='apply' if not dry_run else 'rehearse',
               kind='smalltest_teardown_dryrun' if dry_run else 'smalltest_teardown', smalltest_scope=scope)
    if not dry_run:
        req['dryrun_receipt'], req['dryrun_acceptance'] = accepted(root, 'smalltest_teardown_dryrun', 'dryrun',
            teardown=dict(schema='ky.smalltest_teardown/1', status='ROLLED_BACK', rollback_confirmed=True,
                          operation_id='dryrun', request_sha256='b' * 64, scope=scope,
                          scope_sha256=shared.evidence_digest(scope), rowset_sha256=rowset_sha256))
    return authorize(root, req)


def absence_for(root, *, committed=None, century=False):
    """`century=True`: the census of a century_dispatch(_dryrun) also counts the committed-substep ledger (SR-RESUME-NOW, migration 1410; absence_evidence requires it)."""
    import csv
    import io
    counts = {t: 0 for t, _ in shared.ABSENCE_TABLES}
    if century:
        counts[shared.LEDGER_ABSENCE_TABLE] = 0
    counts.update({t: 0 for t in ('kala_gochara_publication', 'build_runs', 'build_run_assets',
        'asset_provenance_receipts', 'asset_freshness', 'asset_throughput', 'owned_test_runs',
        'ka_gochara_eval_window_record', 'ka_gochara_record_prerequisite',
        'ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification')})
    proof = dict(schema='ky.smalltest_independent_absence/1', chart_id=shared.CHART_ID,
                 generation=shared.GENERATION, counts=counts, run_id=None, baseline=True, registry_inert=True)
    if committed:
        t = committed['teardown']
        proof.update(run_id=t['scope']['run_id'], baseline=False, scope_sha256=t['scope_sha256'],
                     rowset_sha256=t['rowset_sha256'], teardown_request_sha256=committed['request_sha256'],
                     teardown_operation_id=committed['operation_id'], teardown_receipt_sha256=shared.evidence_digest(committed))
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')
    writer.writerow(['absence_proof']); writer.writerow([json.dumps(proof, sort_keys=True)])
    path = Path(root) / 'run/ops/receipts/readback.output.txt'
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(output.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rr, ar = accepted(root, 'readback_sql', 'readback', output_file=str(path), output_sha256=digest)
    rp = path.parent / rr['name']; r = json.loads(rp.read_text()); r['ts'] = '2026-10-15T00:00:01+00:00'
    rr = put(root, 'receipts', 'readback', r)
    ap = path.parent.parent / 'acceptance' / ar['name']; a = json.loads(ap.read_text())
    a['absence'] = dict(proof, output_sha256=digest)
    ar = put(root, 'acceptance', 'readback', a)
    return rr, ar


import contextlib
import os
import tempfile


@contextlib.contextmanager
def database_request(dsn, *, dry_run=False):
    """A verifier-evidence fixture around the existing guarded SQL tests.

    This creates no database. The caller's suite owns the loopback fixture;
    the fixture models independently accepted prior evidence. Dedicated W4 DB
    tests separately exercise a real rollback and its exact resulting proof.
    """
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.conninfo import conninfo_to_dict
    import teardown_v5_small_test_job as td
    params = conninfo_to_dict(dsn)
    if params.get('host') not in ('127.0.0.1', 'localhost') or params.get('port') not in ('55433', '5432'):
        raise AssertionError('evidence fixture requires the suite loopback database')
    with tempfile.TemporaryDirectory(prefix='w4-db-evidence-', dir=os.environ.get('TMPDIR')) as root:
        with psycopg.connect(dsn, row_factory=dict_row, autocommit=True, connect_timeout=3) as conn:
            addr = conn.execute('SELECT inet_server_addr()::text AS addr').fetchone()['addr']
            if addr not in ('127.0.0.1/32', '::1/128'):
                # CI's guarded disposable fixture has already checked the server.
                if os.environ.get('GITHUB_ACTIONS') != 'true':
                    raise AssertionError('evidence fixture server is not loopback')
            rows = conn.execute('SELECT id, plan_manifest FROM build_runs WHERE chart_id = %s AND triggered_by = %s ORDER BY created_at DESC',
                                (shared.CHART_ID, shared.TRIGGERED_BY)).fetchall()
            candidate = conn.execute('SELECT manifest_id, input_generation_vector FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s',
                                     (shared.CHART_ID, shared.GENERATION)).fetchone()
            run = rows[0] if rows else {'id': RUN, 'plan_manifest': {}}
            scope = scope_for(root, str(run['id']), run['plan_manifest'] or {}, candidate)
            digest = td._rowset_digest(conn.cursor(), [str(run['id'])])
        req = request_for(root, scope, dry_run=dry_run, rowset_sha256=digest)
        old = {k: os.environ.get(k) for k in ('KY_ROOT', 'KY_OPERATION_REQUEST')}
        os.environ.update(KY_ROOT=root, KY_OPERATION_REQUEST=json.dumps(req))
        try:
            yield req
        finally:
            for k, value in old.items():
                if value is None: os.environ.pop(k, None)
                else: os.environ[k] = value
