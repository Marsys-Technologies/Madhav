"""Century teardown over the suite's guarded loopback mirror (SR-TEARDOWN-AUTHORITY-GATE item 3).

QUESTION SETTLED WITH EVIDENCE: does today's scoped teardown (teardown_v5_small_test_job.py, small-test and measuring kinds) cover the rows of a
CENTURY candidate — an ordinary, unstamped generation '5.0' candidate built by a 'gochara-v5-century' run? It does NOT, by construction: it selects
runs by the small-test trigger and proves ownership by a test-slice STAMP, which a century candidate does not carry
(`test_todays_scoped_teardown_refuses_a_century_candidate`, the real SQL, every table untouched). The extension is the `century_teardown` kinds: the
same guards, locks, deletes, rowset-digest rollback proof and absence proof, with the century run trigger and an ordinary-candidate proof bound to
the one century run named by a run_id scope (`test_century_*`). Real writer substeps and real deletion SQL; no cloud.
"""
import json
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep  # noqa: F401
from pipeline.orchestrator.writers import ka_gochara_v5 as writer

from .test_a55_replace_chain import CLASSES, PATHS, SHORT
from .test_c38_teardown_real_db import tworld, template, _run, _slice_run, _step, _counts, CHART_ID, MARKER  # noqa: F401

SCRIPTS = Path(__file__).resolve().parents[5] / 'platform/scripts'
for path in (str(SCRIPTS), str(SCRIPTS / '__tests__')):
    if path not in sys.path:
        sys.path.insert(0, path)
import teardown_v5_small_test_job as td
import v5_small_test_shared as shared
import smalltest_safety_support as S

CENTURY = shared.CENTURY_TRIGGERED_BY
MANIFEST = {'version': 'nirmana-run-manifest/v1', 'chart_id': CHART_ID, 'scope': 'asset_set', 'scope_target': shared.ASSET_ID,
            'action': 'rebuild', 'waves': [[shared.ASSET_ID]], 'assets': [{'asset_id': shared.ASSET_ID}]}


def century_candidate(w, *, build=True):
    """A century run staged as dispatch_v5_century_job stages it (trigger 'gochara-v5-century', a plan_manifest with NO slice marker, its digest),
    then built by the WRITER's own substeps under it: a real ordinary candidate whose snapshot, inventory and coverage carry the run's identity."""
    rid = _run(w, triggered_by=CENTURY, marker=None)
    w.conn.execute('UPDATE public.build_runs SET plan_manifest = %s::jsonb, plan_manifest_digest = %s WHERE id = %s',
                   (json.dumps(MANIFEST), writer._manifest_digest(MANIFEST), rid))
    if build:
        for key in (writer.MANIFEST_SUBSTEP, writer.SNAPSHOT_SUBSTEP):
            _step(w, rid, key, SHORT)
        for cls in CLASSES:
            _step(w, rid, f'inventory:{cls}', SHORT)
            _step(w, rid, f'coverage:{cls}', SHORT)
            for path in PATHS:
                _step(w, rid, f'record:{cls}:{path}', SHORT)
    return str(rid)


def century_scope(root, w, rid):
    with psycopg.connect(w.dsn, row_factory=dict_row, autocommit=True) as conn:
        run = conn.execute('SELECT plan_manifest FROM build_runs WHERE id = %s', (rid,)).fetchone()
        manifest = conn.execute('SELECT manifest_id, input_generation_vector FROM kala_gochara_publication WHERE chart_id=%s AND generation=%s',
                                (shared.CHART_ID, shared.GENERATION)).fetchone()
    digest = shared.evidence_digest(run['plan_manifest'])
    launch = dict(schema='ky.century_launch/1', status='LAUNCHED', run_id=rid, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID,
                  plan_manifest_digest=digest, execution_name='brahma-build-pipeline-job-centuryfixture')
    rr, ar = S.accepted(root, 'century_dispatch', 'dispatch', item_id='J-4e', launch=launch)
    return dict(run_id=rid, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID, generation=shared.GENERATION, plan_manifest_digest=digest,
                manifest_id=str(manifest['manifest_id']), input_vector_sha256=shared.evidence_digest(manifest['input_generation_vector']),
                dispatch_receipt=rr, dispatch_acceptance=ar)


def request(root, w, monkeypatch, scope, *, kind, rowset=None, dryrun=None):
    req = dict(operation_id='apply' if kind == 'century_teardown' else 'rehearse', kind=kind, item_id='J-4e', century_scope=scope)
    if dryrun:
        req['dryrun_receipt'], req['dryrun_acceptance'] = dryrun
    S.authorize(root, req)
    monkeypatch.setenv('KY_ROOT', str(root))
    monkeypatch.setenv('DATABASE_URL', w.dsn)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    return req


def proof_of(capsys):
    return json.loads(capsys.readouterr().out.split('teardown_proof\t')[1].splitlines()[0])


def all_rows(w):
    return {'generation': _counts(w), 'runs': w.conn.execute('SELECT count(*) FROM public.build_runs').fetchone()[0],
            'receipts': w.conn.execute('SELECT count(*) FROM public.asset_provenance_receipts').fetchone()[0]}


def test_todays_scoped_teardown_refuses_a_century_candidate(tworld, tmp_path, monkeypatch):
    """EVIDENCE for item 3: the small-test and the measuring teardown kinds do not select a century candidate's rows — they refuse by name, deleting nothing."""
    w = tworld
    rid = century_candidate(w)
    before = all_rows(w)
    assert before['generation']['kala_gochara_publication'] == 1 and before['runs'] == 1
    scope = century_scope(tmp_path, w, rid)
    smalltest = dict(scope)
    smalltest['dispatch_receipt'], smalltest['dispatch_acceptance'] = S.accepted(tmp_path, 'smalltest_dispatch', 'dispatch-s', item_id='J-2a', launch=dict(
        schema='ky.smalltest_launch/1', status='LAUNCHED', run_id=rid, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID,
        plan_manifest_digest=scope['plan_manifest_digest'], execution_name='brahma-build-pipeline-job-fixture'))
    measuring = dict(scope)
    measuring['dispatch_receipt'], measuring['dispatch_acceptance'] = S.accepted(tmp_path, 'measuring_dispatch', 'dispatch-m', item_id='J-3c', launch=dict(
        schema='ky.measuring_launch/1', status='LAUNCHED', run_id=rid, chart_id=shared.CHART_ID, asset_id=shared.ASSET_ID,
        plan_manifest_digest=scope['plan_manifest_digest'], execution_name='brahma-build-pipeline-job-fixture'))
    for kind, key, item, body in (('smalltest_teardown_dryrun', 'smalltest_scope', 'J-2a', smalltest), ('measuring_teardown_dryrun', 'measuring_scope', 'J-3d', measuring)):
        req = S.authorize(tmp_path, {'operation_id': 'old-' + kind, 'kind': kind, 'item_id': item, key: body})
        monkeypatch.setenv('KY_ROOT', str(tmp_path)); monkeypatch.setenv('DATABASE_URL', w.dsn)
        monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
        with pytest.raises(shared.Refused, match=r"NON-test build run\(s\) include ka_gochara_v5"):
            td.teardown(dry_run=True)
        assert all_rows(w) == before, kind


def test_century_rollback_proof_then_commit_then_independent_absence(tworld, tmp_path, monkeypatch, capsys):
    """The century teardown, end to end on real rows: a rollback-confirmed proof of the exact scope and rowset, the same-count content mutation
    refused, the commit removing the whole century candidate and nothing else, and the independent absence readback bound to the commit."""
    w = tworld
    rid = century_candidate(w)
    scope = century_scope(tmp_path, w, rid)
    before = all_rows(w)
    survivors = w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id) VALUES ('other_asset', %s) RETURNING 1", (CHART_ID,)).fetchone()
    req = request(tmp_path, w, monkeypatch, scope, kind='century_teardown_dryrun')
    td.teardown(dry_run=True)
    proof = proof_of(capsys)
    assert proof['schema'] == 'ky.century_teardown/1' and proof['status'] == 'ROLLED_BACK' and proof['rollback_confirmed'] is True
    assert proof['scope'] == scope and proof['scope_sha256'] == shared.evidence_digest(scope)
    assert all_rows(w)['generation'] == before['generation'] and all_rows(w)['runs'] == 1

    rr, ar = S.accepted(tmp_path, 'century_teardown_dryrun', 'rehearse', item_id='J-4e', request_sha256=shared.request_hash(req), teardown=proof)
    req = request(tmp_path, w, monkeypatch, scope, kind='century_teardown', dryrun=(rr, ar))
    original = w.conn.execute('SELECT freshness_state FROM asset_freshness WHERE asset_id=%s', (shared.ASSET_ID,)).fetchone()[0]
    w.conn.execute("UPDATE asset_freshness SET freshness_state='stale' WHERE asset_id=%s", (shared.ASSET_ID,))
    with pytest.raises(shared.Refused, match='same scope and row set'):               # same count, different content: the rollback no longer matches
        td.teardown(dry_run=False)
    assert all_rows(w)['generation'] == before['generation']
    w.conn.execute('UPDATE asset_freshness SET freshness_state=%s WHERE asset_id=%s', (original, shared.ASSET_ID))
    td.teardown(dry_run=False)
    committed_proof = proof_of(capsys)
    assert committed_proof['status'] == 'COMMITTED_AWAITING_ABSENCE' and committed_proof['rowset_sha256'] == proof['rowset_sha256']
    assert all(n == 0 for n in _counts(w).values())
    assert w.conn.execute('SELECT count(*) FROM public.build_runs').fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id='other_asset'").fetchone()[0] == 1     # survivors kept
    committed = dict(operation_id='apply', kind='century_teardown', status='AWAITING_ABSENCE', exit_code=0, request_sha256=shared.request_hash(req),
                     reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00', teardown=committed_proof)
    with psycopg.connect(w.dsn, autocommit=True) as conn:                             # a SEPARATE connection executes the generated SELECT after COMMIT
        measured = json.loads(conn.execute(shared.absence_readback_sql(committed)).fetchone()[0])
    assert measured['run_id'] == rid and measured['registry_inert'] is True and all(n == 0 for n in measured['counts'].values())
    assert 'owned_test_runs' in measured['counts']


def test_century_teardown_refuses_a_stamped_test_slice_candidate(tworld, tmp_path, monkeypatch):
    """Claim: the century kinds never widen into the test-slice teardown — a candidate stamped test_slice is refused by name even under a century trigger."""
    w = tworld
    rid = str(_run(w, triggered_by=CENTURY, marker=MARKER))
    for key in (writer.MANIFEST_SUBSTEP, writer.SNAPSHOT_SUBSTEP):
        _step(w, rid, key)
    before = all_rows(w)
    # the run row's own digest is the marker manifest's; the century scope still names it
    scope = century_scope(tmp_path, w, rid)
    request(tmp_path, w, monkeypatch, scope, kind='century_teardown_dryrun')
    with pytest.raises(shared.Refused, match='not an ordinary century candidate'):
        td.teardown(dry_run=True)
    assert all_rows(w) == before


def test_century_teardown_refuses_a_small_test_candidate_under_a_century_request(tworld, tmp_path, monkeypatch):
    """Claim: a small-test run is a NON-owned run for the century kinds, exactly as a century run is for the small-test kinds."""
    w = tworld
    rid = str(_slice_run(w))
    before = all_rows(w)
    scope = century_scope(tmp_path, w, rid)
    request(tmp_path, w, monkeypatch, scope, kind='century_teardown_dryrun')
    with pytest.raises(shared.Refused, match=r"NON-test build run\(s\)"):
        td.teardown(dry_run=True)
    assert all_rows(w) == before


def test_century_teardown_refuses_coverage_not_written_by_the_identified_run(tworld, tmp_path, monkeypatch):
    """Claim: ownership of the generation's output is tied to the identified century run — a coverage partition written by another build refuses."""
    w = tworld
    rid = century_candidate(w)
    w.conn.execute("UPDATE public.kala_gochara_coverage SET build_id = %s WHERE ctid = (SELECT ctid FROM public.kala_gochara_coverage"
                   " WHERE partition_kind = 'event_class' AND generation = %s LIMIT 1)", (str(uuid.uuid4()), shared.GENERATION))
    before = all_rows(w)
    scope = century_scope(tmp_path, w, rid)
    request(tmp_path, w, monkeypatch, scope, kind='century_teardown_dryrun')
    with pytest.raises(shared.Refused, match='not written by the identified century run'):
        td.teardown(dry_run=True)
    assert all_rows(w) == before


def test_century_teardown_refuses_a_different_run_than_the_scope_names(tworld, tmp_path, monkeypatch):
    """Claim: the run_id scope is exact — a second century run, or a scope naming another run, never widens the deletion."""
    w = tworld
    rid = century_candidate(w)
    other = _run(w, triggered_by=CENTURY, marker=None, receipt=False)
    w.conn.execute('UPDATE public.build_runs SET plan_manifest = %s::jsonb, plan_manifest_digest = %s WHERE id = %s',
                   (json.dumps(MANIFEST), writer._manifest_digest(MANIFEST), other))
    before = all_rows(w)
    scope = century_scope(tmp_path, w, rid)
    request(tmp_path, w, monkeypatch, scope, kind='century_teardown_dryrun')
    with pytest.raises(shared.Refused, match='only the identified staged run may be deleted'):
        td.teardown(dry_run=True)
    assert all_rows(w) == before
