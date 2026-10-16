"""P01-B2: table argv reaches real parsers; absence is measured, not N-137.

Mutations caught: disabled/placeholder bindings, missing --execute/steward flags,
unsupported run-id, permissive abbreviated flags, skipped absence detector,
equal-count/content-different restore, missing/tampered archive evidence.
All database and subprocess boundaries are replaced; no operation runs here.
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'platform/scripts'))
import dispatch_v5_small_test_job as dispatch
import teardown_v5_small_test_job as teardown

TABLE = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json'
KINDS = ('backup_snapshot', 'backup_restore_verify', 'smalltest_dispatch_dryrun',
         'smalltest_dispatch', 'smalltest_teardown_dryrun', 'smalltest_teardown')


def argv_for(op):
    values = {'label': 'p01_fixture', 'run': 'one_class_full', 'classes': 'marriage',
              'horizon-start': '1998-01-01T00:00:00+00:00',
              'horizon-end': '2026-04-17T00:00:00+00:00'}
    return op['fixed_args'] + [a for key in op['allowed_args'] for a in (f'--{key}', values[key])]


@pytest.mark.parametrize('kind', KINDS)
def test_enabled_table_argv_agrees_with_script(kind):
    op = json.loads(TABLE.read_text())['ops'][kind]
    assert op['enabled'] is True
    assert (ROOT / op['script']).is_file(), op['script']
    assert op['production'] is True
    assert op['enabled_by'] == 'J-1a'
    assert op['allowed_args'] == (['label'] if kind.startswith('backup_') else
                                 ['run', 'classes', 'horizon-start', 'horizon-end'] if 'dispatch' in kind else [])
    if kind == 'smalltest_dispatch':
        # Final main owns remote launching; the bridge injects the reviewed staging argv.
        assert op['script'] == '00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py'
        assert op['fixed_args'] == [] and op['also_needs'] == ['gcloud']
        spec = importlib.util.spec_from_file_location('p01_launch_bridge', ROOT / op['script'])
        bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge)
        from types import SimpleNamespace
        staging = []
        def stop_after_parse(argv):
            staging.extend(argv)
            raise RuntimeError('p01 staging boundary')
        dispatcher = SimpleNamespace(build_slice_marker=lambda **kw: {}, main=stop_after_parse)
        with pytest.raises(RuntimeError, match='p01 staging boundary'):
            bridge.run(argv_for(op), dispatcher=dispatcher, connect=lambda: pytest.fail('unexpected DB'))
        assert staging[:3] == ['--i-am-steward', '--after-settled-1', '--execute']
        assert staging[3:7] == ['--run', 'one_class_full', '--classes', 'marriage']
        return
    module = (importlib.import_module('backup_v5_small_test_job') if kind.startswith('backup_') else
              dispatch if 'dispatch' in kind else teardown)
    args = module._parse_args(argv_for(op))
    assert args.execute == (not kind.endswith('_dryrun'))
    if 'dispatch' in kind:
        assert args.i_am_steward and args.after_settled_1
    if kind == 'smalltest_teardown':
        assert args.i_am_steward
    if kind.startswith('backup_'):
        assert args.operation == ('snapshot' if kind == 'backup_snapshot' else 'restore-verify')
        assert op['needs'] == 'owner'  # executor already hands over only its owner URL


@pytest.mark.parametrize('script', ['dispatch', 'teardown', 'backup'])
@pytest.mark.parametrize('flag', ['--run-id', '--exec', '--database-url', '--unsupported'])
def test_unsupported_arguments_refused_at_parser(script, flag):
    module = {'dispatch': dispatch, 'teardown': teardown}.get(script)
    if module is None:
        module = importlib.import_module('backup_v5_small_test_job')
    base = ['--run', 'one_class_full'] if script == 'dispatch' else (
        ['--operation', 'snapshot', '--label', 'p01_fixture'] if script == 'backup' else [])
    with pytest.raises(SystemExit) as error:
        module._parse_args(base + [flag, 'synthetic'])
    assert error.value.code == 2


@pytest.mark.parametrize('script', ['dispatch', 'teardown', 'backup'])
@pytest.mark.parametrize('flag', ['--exec', '--dry-r'])
def test_bare_mode_abbreviations_refused_at_parser(script, flag):
    """No extra positional token may mask acceptance of an abbreviated mode."""
    module = {'dispatch': dispatch, 'teardown': teardown}.get(script)
    if module is None:
        module = importlib.import_module('backup_v5_small_test_job')
    base = (['--run', 'one_class_full', '--i-am-steward', '--after-settled-1']
            if script == 'dispatch' else ['--i-am-steward'] if script == 'teardown' else
            ['--operation', 'snapshot', '--label', 'p01_fixture'])
    # The full spelling must parse with the SAME prerequisites; in particular,
    # teardown's steward requirement must not accidentally reject --exec for us.
    full_flag = '--execute' if flag == '--exec' else '--dry-run'
    args = module._parse_args(base + [full_flag])
    assert args.execute is (full_flag == '--execute')
    assert args.dry_run is (full_flag == '--dry-run')
    with pytest.raises(SystemExit) as error:
        module._parse_args(base + [flag])
    assert error.value.code == 2


@pytest.mark.parametrize('kind', ['smalltest_dispatch_dryrun', 'smalltest_teardown_dryrun'])
def test_table_dryrun_uses_rollback_path(kind, monkeypatch, capsys):
    op = json.loads(TABLE.read_text())['ops'][kind]
    if 'dispatch' in kind:
        from test_dispatch_v5_small_test import _Harness, _run_main
        harness = _Harness()
        _run_main(harness, argv_for(op), capsys)
        assert not harness.commits and len(harness.rollbacks) == 1
    else:
        from test_teardown_v5_small_test import _Harness, _patched
        harness = _Harness()
        with _patched(harness):
            assert teardown.main(argv_for(op)) == 0
        assert harness.commits == 0 and harness.rollbacks > 0


class Counts:
    def __init__(self, leftovers=None):
        self.leftovers = leftovers or {}
        self.queries = []
    def execute(self, sql, params):
        self.queries.append((sql, params))
        self.table = sql.split(' FROM ')[1].split()[0]
    def fetchone(self):
        return {'n': self.leftovers.get(self.table, 0)}


def test_absence_proof_measures_every_deleted_scope_and_run_ids():
    cur = Counts()
    counts = teardown._absence_counts(cur, ['11111111-1111-4111-8111-111111111111'])
    assert set(counts) >= {'build_runs', 'build_run_assets', 'asset_freshness', 'asset_provenance_receipts',
                           'asset_throughput', *(table for table, _ in teardown.GENERATION_TABLES)}
    assert all(value == 0 for value in counts.values())
    assert any('build_runs WHERE id = ANY' in sql for sql, _ in cur.queries)


@pytest.mark.parametrize('table', ['build_runs', 'build_run_assets', 'asset_provenance_receipts',
                                 'ka_gochara_contact', 'ka_gochara_search_input_snapshot', 'kala_gochara_publication'])
def test_absence_refuses_surviving_rows(table):
    cur = Counts({table: 1})
    with pytest.raises(teardown.TeardownRefused, match=table):
        teardown._prove_absence(cur, [])


def test_failed_absence_detector_rolls_back_before_commit(monkeypatch):
    from test_teardown_v5_small_test import _Harness, _patched
    harness = _Harness()
    def refuse(cur, owned):
        raise teardown.TeardownRefused('absence proof: synthetic surviving row')
    with _patched(harness), monkeypatch.context() as patch:
        patch.setattr(teardown, '_prove_absence', refuse)
        with pytest.raises(teardown.TeardownRefused, match='absence proof'):
            teardown.teardown(dry_run=False)
    assert harness.commits == 0 and harness.rollbacks > 0


def test_dryrun_prints_rehearsal_absence_counts(capsys):
    from test_teardown_v5_small_test import _Harness, _patched
    harness = _Harness()
    with _patched(harness):
        teardown.teardown(dry_run=True)
    out = capsys.readouterr().out
    proof = json.loads(out.split('absence_proof\t')[1].splitlines()[0])
    assert proof['status'] == 'rehearsed_then_rolled_back'
    assert proof['chart_id'] == teardown.CHART_ID
    assert proof['generation'] == '5.0'
    assert proof['owned_run_ids']
    assert all(n == 0 for n in proof['counts'].values())


@pytest.mark.parametrize('kind', KINDS)
def test_enabling_a_kind_does_not_bypass_executor_request_gates(kind, tmp_path):
    # Compile the real validator without importing the daemon's top-level
    # directory creation or its Git-writing fixture. The reviewed-script and
    # lease queries are transport doubles; request validation remains real.
    import ast
    import datetime as dt
    import types
    source = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py'
    function = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'validate')
    accepted_dir = tmp_path / 'acceptance'; accepted_dir.mkdir()
    globals_ = {'pathlib': importlib.import_module('pathlib'), 'SAFE_ID': importlib.import_module('re').compile(r'^[a-z0-9_-]+$'),
                'SAFE_ARG': importlib.import_module('re').compile(r'^[A-Za-z0-9_.:+,/-]+$'),
                'SHA': importlib.import_module('re').compile(r'^[0-9a-f]{40}$'),
                'CANONICAL_CHART': '482012f1-710e-4a25-994a-93821f5871aa', 'ACC': accepted_dir,
                'lease_live': lambda lease: True, 'git': lambda *args: types.SimpleNamespace(returncode=0),
                'dt': dt, 'json': json, 'APPROVAL_MAX_AGE_S': 10800, 'seen': lambda key: False,
                'utc_time': lambda value: dt.datetime.fromisoformat(value),
                'smalltest_policy_problem': lambda req: None, 'request_digest': lambda req: 'synthetic_bound_digest'}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), globals_)
    validate = globals_['validate']
    table = json.loads(TABLE.read_text())['ops']
    request = {'operation_id': 'p01_fixture', 'kind': kind, 'item_id': 'J-1a', 'idempotency_key': 'p01_fixture',
               'requested_by': 'adhikarin', 'kyd': 'synthetic', 'chart_id': globals_['CANONICAL_CHART'], 'lease_id': 'synthetic'}
    caps = {'owner': True, 'builder': True, 'gcloud': True}
    assert 'pre-acceptance receipt missing' in validate(request, table, caps)
    assert 'disallowed args' in validate(dict(request, args={'run-id': 'synthetic'}), table, caps)
    assert 'may not request' in validate(dict(request, requested_by='v1'), table, caps)
    request.update(reviewed_commit='a'*40, expires_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat())
    receipt = {'result': 'ACCEPTED', 'operation_id': request['operation_id'], 'by': 'v1',
               'reviewed_commit': request['reviewed_commit'], 'request_sha256': 'synthetic_bound_digest',
               'ts': dt.datetime.now(dt.timezone.utc).isoformat(), 'checks': {}, 'rows': {}}
    path = accepted_dir / 'receipt.json'
    request['acceptance_receipt'] = str(path)
    path.write_text(json.dumps(receipt))
    if kind != 'backup_snapshot':
        assert 'attestation missing' in validate(request, table, caps) or 'rows are not all true' in validate(request, table, caps)
    receipt.update(checks={'backup_taken': True, 'restore_verified': True, 'dry_run_passed': True},
                   rows={key: True for key in table[kind]['required_rows']})
    path.write_text(json.dumps(receipt))
    assert validate(request, table, caps) is None
