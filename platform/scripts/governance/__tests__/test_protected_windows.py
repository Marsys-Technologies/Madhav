"""SR-A6-GCW: behavior at the SQL/GitHub and merge-admission boundaries.

Removing catalog mapping, head/lease checks, durable reservation or readback
verification must fail dispatch tests; removing admission must fail guard tests.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
sys.path.insert(0, str(FLEET))
HEAD = 'a' * 40
LEASE = 'SR-A6-GCW-WINDOW'
COORD = '00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md'
SCHEDULE = '00_ARCHITECTURE/briefs/kalayantra/fleet/protected_window_schedule.json'


def modules():
    # Import within the test so an absent fix is an explicit failed test.
    return importlib.import_module('protected_windows'), importlib.import_module('protected_window_dispatch')


class Snapshot:
    def __init__(self):
        self.current = HEAD
        self.overrides = {}
        self.base_overrides = {}
        self.additions = []
        self.coord = f'## 1. Active leases\n| {LEASE} | campaign | owner | start | 2099-01-01 00:00 | ACTIVE |\n## 2. Other\n'

    def head(self):
        return self.current

    def text(self, path, ref):
        if path == COORD:
            return self.coord
        if ref == 'base' and path == SCHEDULE:
            return self.base_overrides.get(path, '{"schema":"ky.protected_window_schedule/1","windows":[]}')
        overrides = self.base_overrides if ref == 'base' else self.overrides
        if path in overrides:
            return overrides[path]
        return (ROOT / path).read_text()

    def files(self, ref):
        return [str(p.relative_to(ROOT)) for d in ('platform/migrations', 'platform/supabase/migrations')
                for p in (ROOT / d).glob('*.sql')]

    def added(self, base):
        return self.additions


@pytest.fixture
def rig(tmp_path, monkeypatch):
    windows, dispatch = modules()
    snap = Snapshot()
    names = [Path(p).name for p in snap.files(HEAD)]
    fixture = tmp_path / 'fixture.json'
    fixture.write_text(json.dumps({'applied': names, 'status': 'completed', 'conclusion': 'success',
                                   'ci': 'success', 'head': HEAD, 'runs': [], 'calls': [], 'readbacks': 0}))
    # Subprocess fakes mirror gh's complete consumed fields; unknown operations fail.
    fake = tmp_path / 'fake.py'
    fake.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p=Path(os.environ['WINDOW_FIXTURE']); f=json.loads(p.read_text()); a=sys.argv[1:]
f['calls'].append(a)
if '--command' in a:
    sql=a[a.index('--command')+1]
    assert 'FROM public._migrations_applied' in sql and 'SELECT' in sql
    f['readbacks']+=1
    result=f['applied']
elif a[:2]==['run','list']:
    if a[a.index('--workflow')+1]=='CI — Ganga Quality Gate':
        result=[dict(databaseId=8,headSha=f['head'],headBranch='main',event='push',status='completed',conclusion=f['ci'])]
    else: result=f['runs']
elif a[:2]==['workflow','run']:
    assert a[2]=='deploy.yml' and a[a.index('--ref')+1]=='main'
    f['dispatches']=f.get('dispatches',0)+1
    run=dict(databaseId=42,headSha=f['head'],event='workflow_dispatch',status=f['status'],conclusion=f['conclusion'])
    f['runs'].append(run)
    if f.get('apply',True): f['applied']+=f.get('pending',[])
    result=None
elif a[:2]==['run','view']:
    assert a[2]=='42'; result=f['runs'][-1]
elif a[:1]==['api']:
    assert a[-1].endswith('/git/ref/heads/main'); result={'object':{'sha':f['head']}}
else: raise SystemExit('unexpected fake invocation: '+repr(a))
p.write_text(json.dumps(f))
if result is not None: print(json.dumps(result))
''')
    fake.chmod(0o755)
    monkeypatch.setenv('WINDOW_FIXTURE', str(fixture))

    class Rig:
        source = snap
        state = tmp_path / 'state.json'

        def data(self, **updates):
            data = json.loads(fixture.read_text()); data.update(updates)
            fixture.write_text(json.dumps(data)); return data

        def pending(self, *files):
            data = self.data()
            self.data(applied=[f for f in data['applied'] if f not in files], pending=list(files))

        def run(self, dry_run=False):
            return dispatch.tick(snap, self.state, LEASE, gh=str(fake), readback=str(fake), dry_run=dry_run)

    return Rig()


@pytest.mark.parametrize(('migration', 'input_name'), [
    ('1071_kala_gochara_windows_generation_guard.sql', 'gochara_schema_migration'),
    ('1120_jataka_conversation_archive_context.sql', 'jataka_schema_migration'),
    ('1158_ai_console_configuration_types.sql', 'ai_console_schema_migration'),
    ('1202_ai_metering_ledger.sql', 'ai_metering_schema_migration'),
    ('1235_ka_gochara_staged_candidate_evidence_function.sql', 'gochara_contracts_schema_migration'),
    ('1330_kala_layer_manifest_candidates.sql', 'kala_schema_migration'),
])
def test_dispatches_actual_set_per_pending_migration_and_verifies_sql(rig, migration, input_name):
    rig.pending(migration)
    result = rig.run()
    assert result['status'] == 'verified'
    assert result['inputs'] == [input_name]
    calls = rig.data()['calls']
    dispatched = [c for c in calls if c[:2] == ['workflow', 'run']]
    assert len(dispatched) == 1 and f'{input_name}=true' in dispatched[0]
    assert rig.data()['readbacks'] == 2
    receipt = json.loads(rig.state.read_text())['heads'][HEAD]
    assert receipt['run_id'] == 42 and receipt['after'] and receipt['lease'] == LEASE


def test_all_applied_uses_readback_and_never_dispatches(rig):
    assert rig.run()['status'] == 'all_applied'
    assert rig.data()['readbacks'] == 1
    assert rig.data().get('dispatches', 0) == 0


def test_red_head_never_dispatches(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(ci='failure')
    assert rig.run()['status'] == 'waiting_ci'
    assert rig.data().get('dispatches', 0) == 0


def test_lowest_pending_set_first_with_one_batch_per_head(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql', '1235_ka_gochara_staged_candidate_evidence_function.sql')
    result = rig.run()
    assert result['inputs'] == ['gochara_contracts_schema_migration', 'kala_schema_migration']
    call = next(c for c in rig.data()['calls'] if c[:2] == ['workflow', 'run'])
    assert call.index('gochara_contracts_schema_migration=true') < call.index('kala_schema_migration=true')
    rig.pending('1330_kala_layer_manifest_candidates.sql')  # DB truth changes, durable head still reserved.
    assert rig.run()['status'] == 'already_dispatched'
    assert rig.data()['dispatches'] == 1


def test_dry_run_is_read_only_and_does_not_consume_head(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    assert rig.run(dry_run=True)['status'] == 'dry_run'
    assert not rig.state.exists()
    assert rig.data().get('dispatches', 0) == 0
    assert rig.run()['status'] == 'verified'


def test_workflow_success_does_not_substitute_for_readback(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(apply=False)
    with pytest.raises(ValueError, match='readback'):
        rig.run()
    assert rig.data()['readbacks'] == 2
    with pytest.raises(ValueError, match='readback'):
        rig.run()
    assert rig.data()['dispatches'] == 1


def test_active_run_resumes_after_restart_without_duplicate(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(status='in_progress', conclusion=None)
    assert rig.run()['status'] == 'in_progress'
    data = rig.data(); data['runs'][0].update(status='completed', conclusion='success'); rig.data(runs=data['runs'])
    assert rig.run()['status'] == 'verified'
    assert rig.data()['dispatches'] == 1


@pytest.mark.parametrize('coord', ['', '## 1.\n| OTHER | c | o | s | 2099-01-01 00:00 | ACTIVE |\n## 2.',
                                   f'## 1.\n| {LEASE} | c | o | s | 2000-01-01 00:00 | ACTIVE |\n## 2.'])
def test_missing_foreign_or_expired_lease_refuses_dispatch(rig, coord):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.source.coord = coord
    with pytest.raises(ValueError, match='lease'):
        rig.run()
    assert rig.data().get('dispatches', 0) == 0


def test_remote_head_race_refuses_dispatch(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(head='b' * 40)
    # CI also binds to the wrong SHA, and cannot authorize this local origin/main.
    assert rig.run()['status'] == 'waiting_ci'
    assert rig.data().get('dispatches', 0) == 0


def test_routine_predecessor_waits_without_weakening_migrator(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql', '1234_gochara_eval_window_builder_grants.sql')
    result = rig.run()
    assert result['status'] == 'waiting_predecessors'
    assert '1234_gochara_eval_window_builder_grants.sql' in result['missing']
    assert rig.data().get('dispatches', 0) == 0


def schedule(snap, rows):
    snap.overrides[SCHEDULE] = json.dumps({'schema': 'ky.protected_window_schedule/1', 'windows': rows})


def test_guard_rejects_added_protected_migration_without_new_schedule():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql']
    assert any('1235_' in e and 'schedule' in e for e in windows.guard(snap, 'base'))


def test_guard_accepts_exact_migration_window_and_lease_record():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql']
    schedule(snap, [{'migration': Path(snap.additions[0]).name,
                     'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}])
    assert windows.guard(snap, 'base') == []


@pytest.mark.parametrize('change', [{'window_input': 'kala_schema_migration'}, {'lease': ''}, {'lease': 'TODO'}])
def test_guard_rejects_wrong_window_or_placeholder_lease(change):
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql']
    row = {'migration': Path(snap.additions[0]).name, 'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}
    row.update(change); schedule(snap, [row])
    assert windows.guard(snap, 'base')


def test_old_schedule_cannot_be_reused_as_same_pr_schedule():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql']
    schedule(snap, [{'migration': Path(snap.additions[0]).name,
                     'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}])
    snap.base_overrides[SCHEDULE] = snap.overrides[SCHEDULE]
    assert windows.guard(snap, 'base')


def test_existing_history_and_new_routine_migration_are_not_retroactively_blocked():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1234_gochara_eval_window_builder_grants.sql']
    assert windows.guard(snap, 'base') == []


def test_undeclared_new_window_selection_fails_closed():
    windows, _ = modules(); snap = Snapshot()
    snap.overrides['.github/workflows/deploy.yml'] = snap.text('.github/workflows/deploy.yml', HEAD).replace(
        '      kala_schema_migration:\n', '      new_schema_migration:\n        type: boolean\n      kala_schema_migration:\n')
    with pytest.raises(ValueError, match='selection|window'):
        windows.catalog(snap, HEAD)


def test_newly_protected_existing_migration_also_needs_schedule():
    windows, _ = modules(); snap = Snapshot()
    # Same existing SQL, newly classified into a protected set in this PR.
    original = snap.text('platform/scripts/kala_protected_migrations.txt', HEAD)
    snap.overrides['platform/scripts/kala_protected_migrations.txt'] = original + '\n1234_gochara_eval_window_builder_grants.sql\n'
    assert any('1234_' in error for error in windows.guard(snap, 'base'))


def test_second_live_lease_refuses_dispatch(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    rig.source.coord = rig.source.coord.replace('## 2.', '| OTHER | c | o | s | 2099-01-01 00:00 | ACTIVE |\n## 2.')
    with pytest.raises(ValueError, match='lease'):
        rig.run()
    assert rig.data().get('dispatches', 0) == 0


def test_scheduled_lease_must_match_dispatch_lease(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    schedule(rig.source, [{'migration': '1330_kala_layer_manifest_candidates.sql',
                           'window_input': 'kala_schema_migration', 'lease': 'OTHER'}])
    with pytest.raises(ValueError, match='lease'):
        rig.run()
    assert rig.data().get('dispatches', 0) == 0


def test_failed_sql_command_never_dispatches(rig, monkeypatch):
    # The real SQL boundary, not an inferred workflow-history ledger.
    monkeypatch.setenv('WINDOW_FIXTURE', '/does/not/exist')
    with pytest.raises(ValueError, match='failed'):
        rig.run()


def test_duplicate_or_unknown_schedule_does_not_admit_a_protected_migration():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql']
    row = {'migration': Path(snap.additions[0]).name, 'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}
    schedule(snap, [row, row])
    assert windows.guard(snap, 'base')


def test_retained_intent_does_not_repeat_dispatch_after_api_error(rig, monkeypatch):
    _, dispatch = modules()
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    real_run = dispatch.subprocess.run

    def error_after_dispatch(args, **kwargs):
        result = real_run(args, **kwargs)
        if args[1:3] == ['workflow', 'run']:
            result.returncode = 1  # Server accepted request, client lost response.
        return result

    monkeypatch.setattr(dispatch.subprocess, 'run', error_after_dispatch)
    with pytest.raises(ValueError, match='uncertain'):
        rig.run()
    assert rig.run()['status'] == 'verified'
    assert rig.data()['dispatches'] == 1


def test_remote_head_change_after_green_ci_refuses_dispatch(rig, monkeypatch):
    _, dispatch = modules(); rig.pending('1330_kala_layer_manifest_candidates.sql')
    real_command = dispatch.command

    def race(executable, *args):
        if args[0] == 'api':
            return {'object': {'sha': 'b' * 40}}
        return real_command(executable, *args)

    monkeypatch.setattr(dispatch, 'command', race)
    assert rig.run()['status'] == 'head_changed'
    assert rig.data().get('dispatches', 0) == 0


def test_exact_predecessor_number_ceiling_includes_other_file_at_same_number(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    original_files = rig.source.files
    rig.source.files = lambda ref: original_files(ref) + ['platform/migrations/1389_zzz_other.sql']
    result = rig.run()
    assert result['status'] == 'waiting_predecessors' and result['missing'] == ['1389_zzz_other.sql']


@pytest.mark.parametrize('event_name', ['pull_request', 'merge_group'])
def test_required_ci_command_rejects_unscheduled_then_accepts_scheduled(tmp_path, monkeypatch, event_name):
    """Execute the real required job step: losing the CI wiring must fail too."""
    import shutil
    import subprocess
    import yaml
    workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    job = workflow['jobs']['governance-gates-static']
    steps = [step for step in job['steps'] if step.get('name', '').startswith('SR-A6-GCW')]
    assert len(steps) == 1, 'required Governance Gates must execute protected-window admission'
    script = steps[0]['run']
    repo = tmp_path / 'repo'
    for rel in ['.github/workflows/deploy.yml', 'platform/scripts/kala_protected_migrations.txt', 'platform/scripts/migrate.ts',
                str(Path(SCHEDULE).parent / 'protected_windows.py'), SCHEDULE]:
        target = repo / rel; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    for folder in ('platform/migrations', 'platform/supabase/migrations'):
        for path in (ROOT / folder).glob('*.sql'):
            target = repo / folder / path.name
            target.parent.mkdir(parents=True, exist_ok=True); target.write_text('-- fixture\n')
    base = 'b' * 40
    event = tmp_path / 'event.json'
    event.write_text(json.dumps({'pull_request': {'base': {'sha': base}}, 'merge_group': {'base_sha': base}}))
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    fake_git = bin_dir / 'git'
    fake_git.write_text('''#!/usr/bin/env python3
import sys
from pathlib import Path
args=sys.argv[1:]; root=Path.cwd()
base='b'*40
if args[0]=='diff':
    assert args[3:5]==[base,'HEAD'], args
    print('platform/migrations/1235_ka_gochara_staged_candidate_evidence_function.sql')
elif args[0]=='show':
    ref,path=args[1].split(':',1)
    assert ref==base, args
    if path.endswith('protected_window_schedule.json'): print('{"schema":"ky.protected_window_schedule/1","windows":[]}')
    else: print((root/path).read_text())
elif args[0]=='ls-tree':
    for folder in ('platform/migrations','platform/supabase/migrations'):
        for path in (root/folder).glob('*.sql'): print(path.relative_to(root))
else: raise SystemExit('unexpected read-only git operation: '+repr(args))
'''); fake_git.chmod(0o755)
    monkeypatch.setenv('PATH', str(bin_dir) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('GITHUB_EVENT_NAME', event_name); monkeypatch.setenv('GITHUB_EVENT_PATH', str(event))
    failed = subprocess.run(['bash', '-e', '-c', script], cwd=repo, capture_output=True, text=True)
    assert failed.returncode == 1 and '1235_' in failed.stderr, failed.stdout + failed.stderr
    (repo / SCHEDULE).write_text(json.dumps({'schema': 'ky.protected_window_schedule/1', 'windows': [{
        'migration': '1235_ka_gochara_staged_candidate_evidence_function.sql',
        'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}]}))
    passed = subprocess.run(['bash', '-e', '-c', script], cwd=repo, capture_output=True, text=True)
    assert passed.returncode == 0, passed.stdout + passed.stderr


def test_malformed_active_status_is_not_a_lease(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql')
    rig.source.coord = rig.source.coord.replace('ACTIVE |', 'ACTIVE_BROKEN |')
    with pytest.raises(ValueError, match='lease'):
        rig.run()
    assert rig.data().get('dispatches', 0) == 0


def test_unknown_dynamic_selection_is_not_silently_omitted():
    windows, _ = modules(); snap = Snapshot()
    snap.overrides['.github/workflows/deploy.yml'] = snap.text('.github/workflows/deploy.yml', HEAD).replace(
        'migrations+=(1071_kala_gochara_windows_generation_guard.sql)',
        'migrations+=(1071_kala_gochara_windows_generation_guard.sql)\n            migrations+=("$UNKNOWN_FILE")')
    with pytest.raises(ValueError, match='selection'):
        windows.catalog(snap, HEAD)


@pytest.fixture
def future_window(rig):
    import yaml
    workflow = yaml.safe_load(rig.source.text('.github/workflows/deploy.yml', HEAD))
    workflow[True]['workflow_dispatch']['inputs']['future_schema_migration'] = {'type': 'boolean', 'default': False}
    job = workflow['jobs']['jataka-protected-migrations']
    job['if'] = job['if'].replace('inputs.kala_schema_migration == true',
                                  'inputs.kala_schema_migration == true || inputs.future_schema_migration == true')
    step = next(step for step in job['steps']
                if step.get('name') == 'Apply exact protected public-schema migrations')
    step['env']['APPLY_FUTURE'] = '${{ inputs.future_schema_migration }}'
    selection = 'if [ "$APPLY_FUTURE" = "true" ]; then\n  migrations+=(1234_gochara_eval_window_builder_grants.sql)\nfi\n'
    empty_check = 'if [ "${#migrations[@]}" -eq 0 ]; then'
    assert step['run'].count(empty_check) == 1
    step['run'] = step['run'].replace(empty_check, selection + empty_check)
    rig.source.overrides['.github/workflows/deploy.yml'] = yaml.safe_dump(workflow)
    return workflow


def test_future_static_schema_window_is_automatically_selected(rig, future_window):
    windows, _ = modules()
    schedule(rig.source, [{'migration': '1234_gochara_eval_window_builder_grants.sql',
                          'window_input': 'future_schema_migration', 'lease': LEASE}])
    assert windows.guard(rig.source, 'base') == []
    rig.pending('1234_gochara_eval_window_builder_grants.sql')
    result = rig.run()
    assert result['status'] == 'verified' and result['inputs'] == ['future_schema_migration']


def test_future_window_job_admits_only_requested_input(future_window):
    """Evaluate the entire real job condition, with successful prerequisite jobs."""
    import re
    job = future_window['jobs']['jataka-protected-migrations']
    context = {
        'github.event_name': 'workflow_dispatch',
        'needs.changes.result': 'success',
        'needs.migration-state.result': 'success',
        'needs.migration-state.outputs.data_plane': 'marked',
        'needs.migration-state.outputs.data_plane_isolation': 'strict',
        'needs.migration-state.outputs.nirmana': 'marked',
        'needs.migration-state.outputs.purna': 'marked',
        'needs.privileged-bootstrap.result': 'skipped',
    }
    inputs = future_window[True]['workflow_dispatch']['inputs']

    def admitted(selected):
        values = {**context, **{f'inputs.{name}': name == selected for name in inputs}}
        # This local workflow's condition uses only literals, contexts, always(),
        # comparisons and boolean operators. Unknown contexts fail the test.
        expression = re.sub(r'\b(?:github|needs|inputs)\.[a-zA-Z0-9_.-]+',
                            lambda match: repr(values[match[0]]), job['if'])
        expression = expression.replace('always()', 'True').replace('&&', ' and ').replace('||', ' or ')
        expression = re.sub(r'\btrue\b', 'True', expression)
        expression = re.sub(r'\bfalse\b', 'False', expression)
        return eval(expression, {'__builtins__': {}}, {})

    assert not admitted(None), 'an unrequested window must not admit the job'
    assert admitted('future_schema_migration'), 'the future input must admit the protected job'
    context['github.event_name'] = 'push'
    assert not admitted('future_schema_migration'), 'the window must remain manual-only'


def test_future_window_selects_before_migration_execution(future_window, tmp_path):
    """Run deploy's actual selection shell; stub only the external runner."""
    import re
    import subprocess
    step = next(step for step in future_window['jobs']['jataka-protected-migrations']['steps']
                if step.get('name') == 'Apply exact protected public-schema migrations')
    (tmp_path / 'platform').mkdir()
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    calls = tmp_path / 'runner-calls.json'
    npx = bin_dir / 'npx'
    npx.write_text('#!/usr/bin/env python3\nimport json, os, sys\nfrom pathlib import Path\n'
                   "Path(os.environ['RUNNER_CALLS']).write_text(json.dumps(sys.argv[1:]))\n")
    npx.chmod(0o755)
    env = {'PATH': str(bin_dir) + os.pathsep + os.defpath + os.pathsep + str(Path(sys.executable).parent),
           'RUNNER_CALLS': str(calls)}
    for variable, binding in step['env'].items():
        match = re.fullmatch(r'\$\{\{\s*inputs\.([a-z0-9_]+)\s*\}\}', binding)
        if match:
            env[variable] = 'true' if match[1] == 'future_schema_migration' else 'false'
    run = subprocess.run(['bash', '-e', '-c', step['run']], cwd=tmp_path,
                         env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(calls.read_text()) == [
        'tsx', 'scripts/migrate.ts', '--only', '1234_gochara_eval_window_builder_grants.sql']
    calls.unlink()
    env.update({variable: 'false' for variable in env if variable.startswith('APPLY_')})
    unrequested = subprocess.run(['bash', '-e', '-c', step['run']], cwd=tmp_path,
                                 env=env, capture_output=True, text=True)
    assert unrequested.returncode != 0 and not calls.exists()


def test_protected_runner_declaration_without_deploy_window_cannot_escape_schedule_guard():
    windows, _ = modules(); snap = Snapshot()
    snap.additions = ['platform/migrations/1234_gochara_eval_window_builder_grants.sql']
    original = snap.text('platform/scripts/migrate.ts', HEAD)
    snap.overrides['platform/scripts/migrate.ts'] = original.replace(
        'export const PROTECTED_PUBLIC_SCHEMA_MIGRATIONS = new Set([',
        "export const PROTECTED_PUBLIC_SCHEMA_MIGRATIONS = new Set([\n  '1234_gochara_eval_window_builder_grants.sql',")
    assert any('1234_' in error and 'window' in error for error in windows.guard(snap, 'base'))


def test_schedule_commitment_cannot_be_removed_in_later_pr():
    windows, _ = modules(); snap = Snapshot()
    snap.base_overrides[SCHEDULE] = json.dumps({'schema': 'ky.protected_window_schedule/1', 'windows': [{
        'migration': '1235_ka_gochara_staged_candidate_evidence_function.sql',
        'window_input': 'gochara_contracts_schema_migration', 'lease': LEASE}]})
    assert any('removed' in error for error in windows.guard(snap, 'base'))


def test_dispatch_cli_runs_tools_in_requested_repo_and_preserves_state_path(tmp_path, monkeypatch):
    _, dispatch = modules()
    repo = tmp_path / 'repository'; repo.mkdir()
    monkeypatch.chdir(tmp_path)
    seen = {}

    def tick(source, state, lease, **kwargs):
        seen.update(cwd=Path.cwd(), repo=source.repo, state=state)
        return {'status': 'dry_run'}

    monkeypatch.setattr(dispatch, 'tick', tick)
    assert dispatch.main(['--repo', str(repo), '--state', 'receipt.json', '--lease-id', LEASE, '--dry-run']) == 0
    assert seen == {'cwd': repo, 'repo': repo, 'state': tmp_path / 'receipt.json'}


def test_failed_workflow_with_complete_sql_readback_does_not_stall_future_heads(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(conclusion='failure')
    result = rig.run()
    assert result['status'] == 'verified' and result['workflow_conclusion'] == 'failure'
    receipt = json.loads(rig.state.read_text())['heads'][HEAD]
    assert receipt['status'] == 'verified' and receipt['conclusion'] == 'failure'
    rig.source.current = 'b' * 40; rig.data(head='b' * 40)
    rig.pending('1235_ka_gochara_staged_candidate_evidence_function.sql')
    assert rig.run()['status'] == 'verified'
    assert rig.data()['dispatches'] == 2


def test_failed_readback_can_retry_at_a_new_green_head_without_repeating_old_head(rig):
    rig.pending('1330_kala_layer_manifest_candidates.sql'); rig.data(apply=False)
    with pytest.raises(ValueError, match='readback'):
        rig.run()
    rig.source.current = 'b' * 40; rig.data(head='b' * 40, apply=True)
    assert rig.run()['status'] == 'verified'
    assert rig.data()['dispatches'] == 2
    assert json.loads(rig.state.read_text())['heads'][HEAD]['status'] == 'readback_failed'
