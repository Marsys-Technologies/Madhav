"""Evidence fixtures for the century resume gate (SR-RESUME-NOW): the launch receipt of the run being resumed, the ledger it left, the accepted readback of both, and the
`century_resume` request that cites them. `root` is the executor's evidence directory itself (run/ops): receipts/, acceptance/, done/ below it.

The caller puts platform/scripts on sys.path (the gate is v5_small_test_shared.py). The builders use the REAL module's constants only; the module that JUDGES the evidence is
the caller's choice, so a test can judge it with a copy that carries one planted reversion."""
import csv
import hashlib
import io
import json
from pathlib import Path

import v5_small_test_shared as shared

COMMIT = 'a' * 40
RUN = '11111111-1111-4111-8111-111111111111'
NEW_RUN = '22222222-2222-4222-8222-222222222222'
EXECUTION = 'brahma-build-pipeline-job-abc12'
OTHER_EXECUTION = 'brahma-build-pipeline-job-zzz99'
LAUNCHED_AT = '2026-10-25T01:00:00+00:00'
READ_AT = '2026-10-25T03:00:00+00:00'
ARGS = {'classes': 'all', 'final_rules': 'true', 'defer_in_build_verify': 'true',
        'horizon': '1998-01-01T00:00:00+00:00,2084-02-05T00:00:00+00:00', 'result_policy': 'window_qualification/1'}
MANIFEST_ID = '88888888-8888-4888-8888-888888888888'
VECTOR_SHA = 'a1' * 32
# the program a migration-1410 ledger row binds its substep to (implementation / writer / plan digests, the horizon)
IDENTITY = {'implementation_digest': 'c' * 64, 'writer_digest': 'd' * 64, 'plan_digest': 'e' * 64, 'horizon': ARGS['horizon']}
# the committed substeps and the rows each owns (table -> count). `None` = a GLOBAL idempotent substep (scope NULL); the ordinals are the plan's 0..n-1.
SUBSTEPS = (('rules', None),
            ('manifest', {'kala_gochara_publication': 1}),
            ('snapshot', {'ka_gochara_search_input_snapshot': 1}),
            ('inventory:career', {'ka_gochara_search_inventory': 2, 'ka_gochara_search_interval': 5}),
            ('window:career:p1', {'ka_gochara_eval_window': 7, 'ka_gochara_eval_window_record': 3}))


def put(root, folder, name, value):
    path = Path(root) / folder / (name + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))
    return {'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def launch(root, operation_id, *, kind='century_dispatch', run_id=RUN, execution=EXECUTION, ts=LAUNCHED_AT, resumes=None, status='COMPLETED'):
    """The executor's COMPLETED launch receipt of a century_dispatch (or century_resume) and, for a resume, the archived request its receipt bound."""
    request = {'operation_id': operation_id, 'kind': kind, 'item_id': shared.CENTURY_ITEM, 'args': dict(ARGS)}
    if resumes is not None:
        request['resumes'] = resumes
    put(root, 'done', operation_id, request)
    return put(root, 'receipts', operation_id, {
        'operation_id': operation_id, 'kind': kind, 'item_id': shared.CENTURY_ITEM, 'status': status, 'exit_code': 0, 'ts': ts,
        'request_sha256': shared.request_hash(request), 'reviewed_commit': COMMIT,
        'launch': {'schema': 'ky.century_launch/1', 'status': 'LAUNCHED', 'run_id': run_id, 'chart_id': shared.CHART_ID, 'asset_id': shared.ASSET_ID,
                   'execution_name': execution, 'plan_manifest_digest': 'f' * 64}})


def scope_of(counts):
    """A migration-1410 `scope` (build_ledger.measure_scope's shape) and its digest (sha256 of the canonical JSON), or (None, None) for a global substep."""
    if counts is None:
        return None, None
    scope = {'schema': shared.RESUME_SCOPE_SCHEMA, 'tables': {t: {'rows': n, 'digest': hashlib.sha256(f'{t}:{n}'.encode()).hexdigest()} for t, n in counts.items()}}
    canonical = json.dumps(scope, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return scope, hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def ledger_rows(*, identity=None, execution=EXECUTION, run_id=RUN, substeps=SUBSTEPS):
    """The ledger as the readback reports it: one dict per row, keyed exactly by shared.RESUME_LEDGER_KEYS (the migration-1410 columns, the horizon as [lower, upper])."""
    identity = IDENTITY if identity is None else identity
    manifest_at = [k for k, _ in substeps].index('manifest') if any(k == 'manifest' for k, _ in substeps) else len(substeps)
    rows = []
    for i, (key, counts) in enumerate(substeps):
        scope, digest = scope_of(counts)
        bound = i >= manifest_at
        rows.append({'substep_key': key, 'ordinal': i, 'manifest_id': MANIFEST_ID if bound else None, 'vector_sha256': VECTOR_SHA if bound else None,
                     'implementation_digest': identity['implementation_digest'], 'writer_digest': identity['writer_digest'], 'plan_digest': identity['plan_digest'],
                     'build_run_id': run_id, 'execution_id': execution, 'rows_written': sum((counts or {}).values()), 'scope': scope, 'scope_digest': digest,
                     'horizon': identity['horizon'].split(',')})
    return rows


def census_of(rows):
    census = {t: 0 for t in shared.RESUME_CHAIN_TABLES + shared.RESUME_NEVER_PRESENT}
    for row in rows:
        for table, owned in ((row['scope'] or {}).get('tables') or {}).items():
            if table in census:
                census[table] += owned['rows']
    return census


def proof_of(rows, census=None, manifest=None):
    return {'schema': shared.RESUME_SCHEMA, 'chart_id': shared.CHART_ID, 'generation': shared.GENERATION, 'ledger': rows,
            'census': census_of(rows) if census is None else census, 'manifest': manifest or {'count': 1, 'status': 'candidate', 'manifest_id': MANIFEST_ID}}


def readback(root, proof, *, ts=READ_AT, accepted=None, name='readback'):
    """The accepted readback_sql: the executor's retained output (one TSV row, column resume_proof), its receipt and the verifier's acceptance repeating the proof.
    `accepted` is what the acceptance states (default: exactly the measured proof)."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    writer.writerow(['resume_proof'])
    writer.writerow([json.dumps(proof, sort_keys=True)])
    path = Path(root) / 'receipts' / (name + '.output.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = put(root, 'receipts', name, {'operation_id': name, 'kind': 'readback_sql', 'status': 'COMPLETED', 'exit_code': 0, 'item_id': shared.CENTURY_ITEM,
                                           'request_sha256': 'b' * 64, 'reviewed_commit': COMMIT, 'ts': ts, 'output_file': str(path), 'output_sha256': digest})
    acceptance = put(root, 'acceptance', name, {'operation_id': name, 'result': 'ACCEPTED', 'by': 'v1', 'request_sha256': 'b' * 64, 'reviewed_commit': COMMIT,
                                                'resume_readback': dict(proof if accepted is None else accepted, output_sha256=digest)})
    return receipt, acceptance


def scenario(root, *, rows=None, census=None, manifest=None, identity=None, request_identity=None, run_id=RUN, ts=READ_AT, accepted=None, operation_id='resume-1', **over):
    """A complete century_resume request that the gate admits, with the parts a test may break: the ledger `rows`, the measured `census` / `manifest`, the ledger's
    `identity`, the identity the request states (`request_identity`), the run it names, the readback time, and any request field (`over`)."""
    prior = launch(root, 'dispatch-1')
    rows = ledger_rows(identity=identity) if rows is None else rows
    receipt, acceptance = readback(root, proof_of(rows, census, manifest), ts=ts, accepted=accepted)
    req = {'operation_id': operation_id, 'kind': 'century_resume', 'item_id': shared.CENTURY_ITEM, 'args': dict(ARGS), 'resumes': prior, 'resume_run_id': run_id,
           'program_identity': dict(IDENTITY if request_identity is None else request_identity), 'resume_receipt': receipt, 'resume_acceptance': acceptance}
    req.update(over)
    return req


def absence(root, *, counts_over=None, name='absence', drop=()):
    """An accepted independent-absence readback (the shape absence_evidence reads), every count zero except `counts_over`; the first-dispatch baseline form."""
    counts = {t: 0 for t, _ in shared.ABSENCE_TABLES}
    counts.update({t: 0 for t in (shared.LEDGER_ABSENCE_TABLE, 'kala_gochara_publication', 'build_runs', 'build_run_assets', 'asset_provenance_receipts', 'asset_freshness', 'asset_throughput',
                                  'owned_test_runs', 'ka_gochara_eval_window_record', 'ka_gochara_record_prerequisite', 'ka_gochara_eval_window_verification',
                                  'ka_gochara_search_inventory_verification')})
    counts.update(counts_over or {})
    for table in drop:                    # a readback taken without that count (an older census)
        counts.pop(table)
    proof = dict(schema='ky.smalltest_independent_absence/1', chart_id=shared.CHART_ID, generation=shared.GENERATION, counts=counts, run_id=None, baseline=True,
                 registry_inert=True)
    out = io.StringIO()
    writer = csv.writer(out, delimiter='\t', lineterminator='\n')
    writer.writerow(['absence_proof'])
    writer.writerow([json.dumps(proof, sort_keys=True)])
    path = Path(root) / 'receipts' / (name + '.output.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = put(root, 'receipts', name, {'operation_id': name, 'kind': 'readback_sql', 'status': 'COMPLETED', 'exit_code': 0, 'request_sha256': 'b' * 64,
                                           'reviewed_commit': COMMIT, 'ts': READ_AT, 'output_file': str(path), 'output_sha256': digest})
    acceptance = put(root, 'acceptance', name, {'operation_id': name, 'result': 'ACCEPTED', 'by': 'v1', 'request_sha256': 'b' * 64, 'reviewed_commit': COMMIT,
                                                'absence': dict(proof, output_sha256=digest)})
    return {'absence_receipt': receipt, 'absence_acceptance': acceptance}
