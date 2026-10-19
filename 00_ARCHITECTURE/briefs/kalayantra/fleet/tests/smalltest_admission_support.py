"""P01-compatible admission fixtures; only external observations are doubled."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

FLEET = Path(__file__).resolve().parents[1]
ROOT = FLEET.parents[3]
sys.path.insert(0, str(ROOT / 'platform/scripts'))
sys.path.insert(0, str(ROOT / 'platform/scripts/__tests__'))
import smalltest_safety_support as evidence
from test_teardown_v5_small_test import _Harness, RUN_1

ARG_VALUES = {'label': 'fixture', 'scope': 'small_test', 'sql_file': 'fixture.sql', 'sql_sha256': '0' * 64, 'migration': '1304',
              'run': 'all_classes_1y', 'classes': 'all',
              'horizon-start': '2025-04-17T00:00:00+00:00',
              'horizon-end': '2026-04-17T00:00:00+00:00'}


def load_executor(root, monkeypatch):
    monkeypatch.setenv('KY_ROOT', str(root))
    spec = importlib.util.spec_from_file_location('w4_executor', FLEET / 'executor.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    policy = (ROOT / 'platform/scripts/v5_small_test_shared.py').read_text()

    def git(*args, **kwargs):
        if args == ('merge-base', '--is-ancestor', evidence.COMMIT, 'origin/main'):
            return SimpleNamespace(returncode=0, stdout='')
        if args == ('show', evidence.COMMIT + ':platform/scripts/v5_small_test_shared.py'):
            return SimpleNamespace(returncode=0, stdout=policy)
        raise AssertionError('unexpected Git observation: ' + repr(args))

    monkeypatch.setattr(mod, 'lease_live', lambda _: True)
    monkeypatch.setattr(mod, 'git', git)
    monkeypatch.setattr(mod, 'seen', lambda _: False)
    mod.ACC.mkdir(parents=True, exist_ok=True)
    return mod


def approve(executor, req):
    acceptance = executor.ACC / (req['operation_id'] + '.json')
    req['acceptance_receipt'] = str(acceptance)
    acceptance.write_text(json.dumps(dict(result='ACCEPTED', by='v1', operation_id=req['operation_id'],
        reviewed_commit=req['reviewed_commit'], ts=executor.now(), request_sha256=executor.request_digest(req),
        rows={k: True for k in ['2', '3', '7', '9', '11']},
        checks=dict(backup_taken=True, restore_verified=True, dry_run_passed=True))))
    return req


def request(executor, kind, args=None):
    if args is None and kind in ('smalltest_dispatch', 'smalltest_dispatch_dryrun'):
        args = {key: ARG_VALUES[key] for key in
                ('run', 'classes', 'horizon-start', 'horizon-end')}
    req = dict(operation_id='w4-proof', idempotency_key='w4-proof', item_id='J-2a', kind=kind,
               requested_by='adhikarin', kyd='PRE-D-TEARDOWN', chart_id=executor.CANONICAL_CHART,
               lease_id='fixture', reviewed_commit=evidence.COMMIT, args=args or {},
               expires_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).isoformat())
    if kind in ('smalltest_teardown', 'smalltest_teardown_dryrun'):
        harness = _Harness()
        scope = evidence.scope_for(executor.KY_ROOT, RUN_1, harness.run_manifests[0]['plan_manifest'], harness.manifest)
        bound = evidence.request_for(executor.KY_ROOT, scope, dry_run=kind.endswith('_dryrun'), rowset_sha256='c' * 64)
        for field in ('smalltest_scope', 'dryrun_receipt', 'dryrun_acceptance'):
            if field in bound:
                req[field] = bound[field]
    if kind == 'smalltest_dispatch':
        req['absence_receipt'], req['absence_acceptance'] = evidence.absence_for(executor.KY_ROOT)
        req.update(evidence.scoped_backup_for(executor.KY_ROOT))
    return approve(executor, req)


def caps():
    return {k: True for k in ['owner', 'builder', 'gcloud', 'pgenv', 'none']}
