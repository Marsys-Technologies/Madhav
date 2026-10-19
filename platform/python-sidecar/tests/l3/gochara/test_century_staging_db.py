"""Century staging and launch over the guarded loopback mirror (SR-PREBUILD-ALL; item J-4e). Injected launcher; never cloud.

The century run is the measuring run without the test slice: the real staging SQL runs (and rolls back for the dry run); the launch wrapper
stages once and launches exactly that staged run through the small-test bridge's durable claim, with the century trigger and NO slice marker.
No run completion is claimed — only the writer's later execution could do that.
"""
import copy
import json
import sys
from pathlib import Path

import psycopg
import psycopg.rows
import pytest

from ._measuring_binding_world import measuring_world  # noqa: F401
from ._smalltest_executor_evidence import scoped_content_unchanged

FLEET = Path(__file__).resolve().parents[5] / '00_ARCHITECTURE/briefs/kalayantra/fleet'
SCRIPTS = Path(__file__).resolve().parents[5] / 'platform/scripts'
for path in (str(FLEET), str(SCRIPTS), str(SCRIPTS / '__tests__')):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def _scoped_content_unchanged(monkeypatch):
    scoped_content_unchanged(monkeypatch)


def runs(dw):
    return dw.conn.execute('SELECT count(*) FROM build_runs').fetchone()[0], dw.conn.execute('SELECT count(*) FROM build_run_assets').fetchone()[0]


def test_century_real_rollback_then_exact_unmarked_staged_launch(measuring_world, tmp_path, monkeypatch, capsys):
    dw = measuring_world
    import century_launch
    import dispatch_v5_century_job as century
    import smalltest_safety_support as S
    import v5_small_test_shared as shared
    monkeypatch.setenv('DATABASE_URL', dw.dsn)
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    rr, ar = S.absence_for(tmp_path)
    req = S.authorize(tmp_path, dict(kind='century_dispatch_dryrun', item_id='J-4e', operation_id='rollback', args=dict(classes='all'),
                                     absence_receipt=rr, absence_acceptance=ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    base = ['--i-am-steward', '--after-settled-1', '--classes', 'all']

    # 1. the dry run runs the REAL staging transaction and rolls it back: zero writes, an unmarked century manifest, the launch it would make
    century.main(base + ['--dry-run'])
    plan = json.loads(capsys.readouterr().out)
    assert plan['schema'] == 'ky.century_staging/1' and plan['status'] == 'ROLLED_BACK' and plan['rollback_confirmed'] is True
    assert 'gochara_v5_test_slice' not in plan['plan_manifest'] and plan['triggered_by'] == shared.CENTURY_TRIGGERED_BY
    assert plan['launch_plan'] == century.launch_plan(plan['run_id']) and plan['launch_plan']['async_launch'] is True
    assert runs(dw) == (0, 0)

    # 2. the real kind cites that rollback; an accepted rollback of a DIFFERENT manifest cannot launch
    dry_rr, dry_ar = S.accepted(tmp_path, 'century_dispatch_dryrun', 'rollback', item_id='J-4e',
                                request_sha256=shared.request_hash(req), staging=plan)
    req = S.authorize(tmp_path, dict(req, kind='century_dispatch', operation_id='launch', dryrun_receipt=dry_rr, dryrun_acceptance=dry_ar))
    bad_plan = copy.deepcopy(plan)
    bad_plan['plan_manifest']['assets'][0]['expected_code_digest'] = '0' * 64
    bad_plan['plan_manifest_digest'] = shared.evidence_digest(bad_plan['plan_manifest'])
    bad_plan['operation_id'] = 'wrong-manifest'
    bad_rr, bad_ar = S.accepted(tmp_path, 'century_dispatch_dryrun', 'wrong-manifest', item_id='J-4e',
                                request_sha256=plan['request_sha256'], staging=bad_plan)
    bad_req = S.authorize(tmp_path, dict(req, dryrun_receipt=bad_rr, dryrun_acceptance=bad_ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(bad_req))
    with pytest.raises(shared.Refused, match='same source, args and manifest'):
        century.main(base + ['--execute'])
    assert runs(dw) == (0, 0)

    # 3. the real launch: staged ONCE, launched exactly that run, with the century trigger and an unmarked manifest
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(S.authorize(tmp_path, req)))
    calls = []
    result = century_launch.run(['--classes', 'all'], dispatcher=century,
                                connect=lambda: psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row), claim_dir=tmp_path / 'claims',
                                launcher=lambda rid, timeout: calls.append(rid) or 'brahma-build-pipeline-job-centuryfixture')
    row = dw.conn.execute('SELECT id, state, triggered_by, plan_manifest, plan_manifest_digest FROM build_runs').fetchone()
    assert str(row[0]) == result['run_id'] == calls[0] and row[1] == 'planned' and row[2] == shared.CENTURY_TRIGGERED_BY
    assert row[3] == plan['plan_manifest'] and 'gochara_v5_test_slice' not in row[3] and row[4] == shared.evidence_digest(row[3])
    assert result['schema'] == 'ky.century_launch/1' and result['status'] == 'LAUNCHED' and result['plan_manifest_digest'] == row[4]
    assert json.loads((tmp_path / 'claims' / (result['run_id'] + '.json')).read_text()) == result
    assert dw.conn.execute("SELECT is_active FROM asset_registry WHERE asset_id='ka_gochara_v5'").fetchone()[0] is False

    # 4. never a second staging: the durable claim and the one-active-run rule both refuse a replay
    with pytest.raises(Exception):
        century_launch.run(['--classes', 'all'], dispatcher=century, connect=lambda: psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row),
                           claim_dir=tmp_path / 'claims', launcher=lambda rid, timeout: calls.append(rid) or 'brahma-build-pipeline-job-again')
    assert len(calls) == 1 and runs(dw) == (1, 1)


def test_the_launch_bridge_keeps_slice_runs_and_century_runs_apart(measuring_world, tmp_path):
    """Claim: a staged run is launchable only as the family it was staged as — a century launch refuses a run carrying a slice marker, and the
    small-test / measuring launch still refuses an unmarked run (the default behaviour is unchanged)."""
    dw = measuring_world
    import smalltest_launch as bridge
    import dispatch_v5_century_job as century
    import dispatch_v5_small_test_job as staging
    import v5_small_test_shared as shared
    candidate = century._load_inactive_candidate(dw.conn.cursor(row_factory=psycopg.rows.dict_row))
    plain, plain_digest = century.build_century_manifest(candidate=candidate)
    marker = staging.build_slice_marker(run='all_classes_1y', classes='all', horizon_start='2025-04-01T00:00:00+00:00', horizon_end='2026-04-01T00:00:00+00:00')
    marked, marked_digest = staging.build_small_test_manifest(candidate=candidate, slice_marker=marker)

    def stage(manifest, digest, trigger):
        rid = str(__import__('uuid').uuid4())
        dw.conn.execute("INSERT INTO build_runs (id, chart_id, scope, scope_target, action, state, plan, plan_manifest, plan_manifest_digest, triggered_by)"
                        " VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb, %s::jsonb, %s, %s)",
                        (rid, shared.CHART_ID, shared.ASSET_ID, json.dumps([shared.ASSET_ID]), json.dumps(manifest), digest, trigger))
        dw.conn.execute("INSERT INTO build_run_assets (run_id, asset_id, position, state) VALUES (%s, %s, 0, 'queued')", (rid, shared.ASSET_ID))
        return rid

    def launch(rid, manifest, **kw):
        conn = psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row)
        try:
            return bridge.launch_staged(run_id=rid, expected_manifest=manifest, connection=conn, claim_dir=tmp_path / rid,
                                        launcher=lambda r, t: 'brahma-build-pipeline-job-fixture', **kw)
        finally:
            conn.rollback(); conn.close()

    marked_century = stage(marked, marked_digest, shared.CENTURY_TRIGGERED_BY)
    with pytest.raises(bridge.Refused, match='staged manifest differs'):
        launch(marked_century, marked, triggered_by=shared.CENTURY_TRIGGERED_BY, test_slice=False)
    dw.conn.execute('DELETE FROM build_run_assets'); dw.conn.execute('DELETE FROM build_runs')
    plain_small = stage(plain, plain_digest, shared.TRIGGERED_BY)
    with pytest.raises(bridge.Refused, match='staged manifest differs'):
        launch(plain_small, plain)                                    # default: a slice marker is required
    dw.conn.execute('DELETE FROM build_run_assets'); dw.conn.execute('DELETE FROM build_runs')
    wrong_trigger = stage(plain, plain_digest, shared.TRIGGERED_BY)
    with pytest.raises(bridge.Refused, match='identity/state mismatch'):
        launch(wrong_trigger, plain, triggered_by=shared.CENTURY_TRIGGERED_BY, test_slice=False)
    dw.conn.execute('DELETE FROM build_run_assets'); dw.conn.execute('DELETE FROM build_runs')
    good = stage(plain, plain_digest, shared.CENTURY_TRIGGERED_BY)
    assert launch(good, plain, triggered_by=shared.CENTURY_TRIGGERED_BY, test_slice=False, launch_schema='ky.century_launch/1')['status'] == 'LAUNCHED'
