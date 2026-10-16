"""Real guarded-suite staging/readback, with an injected launcher; never cloud."""
import importlib.util
import json
from pathlib import Path

import psycopg
import psycopg.rows
import pytest

from ._smalltest_executor_evidence import executor_bound_smalltest  # noqa: F401
from .test_a55_replace_chain import template  # noqa: F401
from .test_c37_dispatch_real_db import dtemplate, dw  # noqa: F401


def test_real_staged_run_is_launched_once_and_receipted(dw, tmp_path, monkeypatch, capsys):
    path = Path(__file__).resolve().parents[5] / "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py"
    spec = importlib.util.spec_from_file_location("w4_bridge", path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    import dispatch_v5_small_test_job as dispatch
    monkeypatch.setenv("DATABASE_URL", dw.dsn)
    calls = []
    result = bridge.run(["--run", "one_class_full", "--classes", "marriage"], dispatcher=dispatch,
                        connect=lambda: psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row), claim_dir=tmp_path,
                        launcher=lambda run_id, timeout_s: calls.append(run_id) or "brahma-build-pipeline-job-fixture01")
    stored = dw.conn.execute("SELECT id, state, plan_manifest_digest FROM build_runs").fetchall()
    assert len(stored) == 1 and str(stored[0][0]) == calls[0] == result["run_id"]
    assert stored[0][1:] == ("planned", result["plan_manifest_digest"])
    assert json.loads(capsys.readouterr().out)["execution_name"] == "brahma-build-pipeline-job-fixture01"
    assert json.loads((tmp_path / (result["run_id"] + ".json")).read_text()) == result


def test_measuring_staging_dry_run_is_refused_without_writes(dw, capsys, monkeypatch):
    import dispatch_v5_small_test_job as dispatch
    monkeypatch.setenv("DATABASE_URL", dw.dsn)
    fixed_args = ["--i-am-steward", "--after-settled-1", "--dry-run", "--run", "all_classes_full", "--classes", "all"]
    # PR #3507 / P01 deliberately disables measuring through the small-test path.
    with pytest.raises(SystemExit) as refused:
        dispatch.main(fixed_args)
    assert refused.value.code == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    assert "measuring phase is disabled" in streams.err
    assert dw.conn.execute("SELECT count(*) FROM build_runs").fetchone()[0] == 0
    assert dw.conn.execute("SELECT count(*) FROM build_run_assets").fetchone()[0] == 0


from ._measuring_binding_world import measuring_world  # noqa: F401


def test_dedicated_measuring_real_rollback_then_exact_staged_launch(measuring_world, tmp_path, monkeypatch, capsys):
    """Actual SQL and manifest, injected remote transport. No run completion claim."""
    dw = measuring_world
    import sys
    fleet = Path(__file__).resolve().parents[5] / '00_ARCHITECTURE/briefs/kalayantra/fleet'
    sys.path.insert(0, str(fleet))
    import measuring_launch
    import dispatch_v5_measuring_job as measuring
    import smalltest_safety_support as S
    import v5_small_test_shared as shared
    monkeypatch.setenv('DATABASE_URL', dw.dsn)
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    rr, ar = S.absence_for(tmp_path)
    req = S.authorize(tmp_path, dict(kind='measuring_dispatch_dryrun', item_id='J-3c', operation_id='rollback',
        args=dict(run='all_classes_full', classes='all'), absence_receipt=rr, absence_acceptance=ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    base = ['--i-am-steward', '--after-settled-1', '--run', 'all_classes_full', '--classes', 'all']
    measuring.main(base + ['--dry-run'])
    plan = json.loads(capsys.readouterr().out)
    assert plan['plan_manifest']['gochara_v5_test_slice']['run'] == 'all_classes_full'
    assert dw.conn.execute('SELECT count(*) FROM build_runs').fetchone()[0] == 0
    assert dw.conn.execute('SELECT count(*) FROM build_run_assets').fetchone()[0] == 0
    dry_rr, dry_ar = S.accepted(tmp_path, 'measuring_dispatch_dryrun', 'rollback', item_id='J-3c',
        request_sha256=shared.request_hash(req), staging=plan)
    req = S.authorize(tmp_path, dict(req, kind='measuring_dispatch', operation_id='launch',
        dryrun_receipt=dry_rr, dryrun_acceptance=dry_ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    # A self-consistent accepted rollback of a different manifest cannot launch.
    import copy
    bad_plan = copy.deepcopy(plan)
    bad_plan['plan_manifest']['assets'][0]['expected_code_digest'] = '0' * 64
    bad_plan['plan_manifest_digest'] = shared.evidence_digest(bad_plan['plan_manifest'])
    bad_plan['operation_id'] = 'wrong-manifest'
    bad_rr, bad_ar = S.accepted(tmp_path, 'measuring_dispatch_dryrun', 'wrong-manifest', item_id='J-3c',
        request_sha256=plan['request_sha256'], staging=bad_plan)
    bad_req = S.authorize(tmp_path, dict(req, dryrun_receipt=bad_rr, dryrun_acceptance=bad_ar))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(bad_req))
    with pytest.raises(shared.Refused, match='same source, args and manifest'):
        measuring.main(base + ['--execute'])
    assert dw.conn.execute('SELECT count(*) FROM build_runs').fetchone()[0] == 0
    req = S.authorize(tmp_path, req)
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(req))
    calls = []
    result = measuring_launch.run(['--run', 'all_classes_full', '--classes', 'all'], dispatcher=measuring,
        connect=lambda: psycopg.connect(dw.dsn, row_factory=psycopg.rows.dict_row), claim_dir=tmp_path / 'claims',
        launcher=lambda rid, timeout: calls.append(rid) or 'brahma-build-pipeline-job-measuringfixture')
    row = dw.conn.execute('SELECT id, state, plan_manifest, plan_manifest_digest FROM build_runs').fetchone()
    assert str(row[0]) == result['run_id'] == calls[0] and row[1] == 'planned'
    assert row[2] == plan['plan_manifest'] and row[3] == shared.evidence_digest(row[2])
    assert result['schema'] == 'ky.measuring_launch/1'
    assert dw.conn.execute("SELECT is_active FROM asset_registry WHERE asset_id='ka_gochara_v5'").fetchone()[0] is False
