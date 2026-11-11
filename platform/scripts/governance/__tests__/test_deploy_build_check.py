"""Deploy demand oracles: owner madhav-6d job; CLAUDE.md §N.8.

The policy comes from the job's runner-cap requirement and the actual Docker
COPY inputs, rather than captured build output. GitHub expressions are executed
with Node, as in test_ci_generated.py; no workflow/API/Docker is dispatched.
"""
import json
import os
import shutil
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
NODE = shutil.which('node') or 'node'
WORKFLOW = ROOT / '.github/workflows/deploy.yml'
PIPELINE_REPO = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"


def workflow():
    return yaml.safe_load(WORKFLOW.read_text())


def triggers(doc):
    # PyYAML's YAML 1.1 loader treats the Actions `on` key as True.
    return doc.get('on', doc.get(True))


def evaluate(condition, event, deployable='', cancelled=False, docs_only='false'):
    script = r'''
const [condition, event, deployable, cancelled, docs_only] = JSON.parse(process.argv[1]);
const github = {event_name: event, event: {workflow_run: {conclusion: ''}}};
const needs = {'pr-changes': {outputs: {deployable}}, changes: {outputs: {docs_only}}};
const expr = condition.replace(/^\$\{\{\s*|\s*\}\}$/g, '').replace(/needs\.pr-changes/g, 'needs["pr-changes"]');
const result = new Function('github', 'needs', 'cancelled', 'always', 'return (' + expr + ')')(
  github, needs, () => cancelled, () => true);
process.stdout.write(JSON.stringify(Boolean(result)));
'''
    result = subprocess.run(['node', '-e', script, json.dumps([condition, event, deployable, cancelled, docs_only])],
                            capture_output=True, text=True, check=True, timeout=10)
    return json.loads(result.stdout)


def classify(tmp_path, files, exit_code=0):
    """Execute the real workflow body with an offline, read-only diff fixture."""
    job = workflow()['jobs'].get('pr-changes')
    assert job is not None, 'PR builds need a cheap path detector'
    step = next(s for s in job['steps'] if s.get('id') == 'classify')
    git = tmp_path / 'git'
    git.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                   'assert sys.argv[1:] == ["diff", "--name-only", "--no-renames", "-z", "HEAD^1", "HEAD"]\n'
                   'sys.stdout.buffer.write(b"".join(p.encode()+b"\\0" for p in json.loads(os.environ["DIFF_FILES"])))\n'
                   'sys.exit(int(os.environ["DIFF_EXIT"]))\n')
    git.chmod(0o755)
    output = tmp_path / 'output'
    env = {**os.environ, 'PATH': str(tmp_path) + os.pathsep + os.environ['PATH'],
           'DIFF_FILES': json.dumps(files), 'DIFF_EXIT': str(exit_code), 'GITHUB_OUTPUT': str(output)}
    result = subprocess.run(['bash', '-eo', 'pipefail', '-c', step['run']], env=env,
                            capture_output=True, text=True, timeout=10, check=True)
    assert not result.stderr or 'warning' in result.stderr.lower()
    return dict(line.split('=', 1) for line in output.read_text().splitlines())['deployable']


def test_docs_and_plan_only_pr_reports_skipped_build_check(tmp_path):
    """Owner runner-cap claim: ordinary evidence never schedules Docker."""
    doc = workflow()
    assert 'paths' not in triggers(doc)['pull_request'], 'required-named checks must always report'
    assert 'paths-ignore' not in triggers(doc)['pull_request']
    decision = classify(tmp_path, ['00_ARCHITECTURE/briefs/kalayantra/NOTE.md',
                                 '00_ARCHITECTURE/control/kalayantra/plan_model.json',
                                 'docs/deploy-guide.md', 'README.md'])
    assert decision == 'false'
    job = doc['jobs']['build-check']
    assert job['name'] == 'Build Check (PR only)'
    assert job['needs'] == ['pr-changes']
    assert not evaluate(job['if'], 'pull_request', decision)


@pytest.mark.parametrize('path', [
    'platform/src/app/page.tsx', 'platform/next.config.ts', 'platform/public/icon.svg',
    'platform/package.json', 'platform/package-lock.json', 'platform/patches/fix.patch',
    'platform/scripts/temporal/compute_transits.py', 'platform/migrations/new.sql',
    'platform/python-sidecar/services/engine.py', 'platform/python-sidecar/requirements.txt',
    'platform/python-sidecar/Dockerfile.pipeline', 'platform-mcp/src/server.ts',
    'platform-mcp/resources/prompt.md', 'platform-mcp/package-lock.json',
    'Dockerfile', 'platform/.dockerignore', '.dockerignore', 'cloudbuild.yaml',
    'infra/cloudbuild.release.yml', 'package.json', 'pnpm-lock.yaml',
    '01_FACTS_LAYER/runtime.md', '025_HOLISTIC_SYNTHESIS/runtime.md',
    '035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json',
    '00_ARCHITECTURE/CAPABILITY_MANIFEST.json', '00_ARCHITECTURE/manifest_overrides.yaml',
    '00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md', '00_ARCHITECTURE/MACRO_PLAN_v2_0.md',
    '00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md', '00_ARCHITECTURE/CURRENT_STATE_v1_0.md',
    '.github/workflows/deploy.yml',
])
def test_image_and_build_inputs_run_pr_build_check(tmp_path, path):
    """COPY inputs: web COPY .; sidecar COPY python-sidecar + temporal;
    pipeline and MCP repo-root COPYs; deploy.yml's explicit corpus copies.
    """
    decision = classify(tmp_path, ['docs/guide.md', path])
    assert decision == 'true', path
    assert evaluate(workflow()['jobs']['build-check']['if'], 'pull_request', decision)


@pytest.mark.parametrize('files,exit_code', [([], 0), ([], 128), (['docs/a.md'], 128)])
def test_unreadable_or_empty_diff_keeps_build_validation(tmp_path, files, exit_code):
    """§N.8: a missing measurement cannot earn a skipped build."""
    assert classify(tmp_path, files, exit_code) == 'true'
    condition = workflow()['jobs']['build-check']['if']
    assert evaluate(condition, 'pull_request', '')  # detector job failure/missing output
    assert not evaluate(condition, 'pull_request', 'true', cancelled=True)


def test_main_deployment_and_merge_queue_triggers_stay_unchanged():
    """Main deploys are CI-success workflow_run events, not push events.
    PR-only detection cannot become a dependency of production/protected jobs.
    """
    doc = workflow()
    events = triggers(doc)
    assert set(events) == {'workflow_run', 'pull_request', 'workflow_dispatch'}
    assert events['workflow_run'] == {'workflows': ['CI — Ganga Quality Gate'],
                                      'types': ['completed'], 'branches': ['main']}
    assert events['pull_request']['branches'] == ['main']
    for event in ('push', 'workflow_run', 'workflow_dispatch', 'merge_group'):
        assert not evaluate(doc['jobs']['build-check']['if'], event, 'true')
        assert not evaluate(doc['jobs']['pr-changes']['if'], event)
    for key, job in doc['jobs'].items():
        if key not in ('pr-changes', 'build-check'):
            assert 'pr-changes' not in str(job.get('needs', [])), key
    assert doc['jobs']['changes']['if'] == "github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'"
    outcome = doc['jobs']['deployment-outcome']
    assert outcome['name'] == 'Require earned deployment outcome'
    assert outcome['if'] == ("${{ always() && github.event_name != 'pull_request' "
                             "&& needs.changes.result != 'skipped' }}")
    assert set(outcome['needs']) == {'changes', 'migrate', 'deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job'}
    assert doc['concurrency']['cancel-in-progress'] == "${{ github.event_name == 'pull_request' }}"


def outcome_job_runs(event, changes_result):
    """Evaluate the real deployment-outcome `if` with Node, as evaluate() does."""
    script = r'''
const [condition, event, changes] = JSON.parse(process.argv[1]);
const github = {event_name: event};
const needs = {changes: {result: changes}};
const expr = condition.replace(/^\$\{\{\s*|\s*\}\}$/g, '');
process.stdout.write(JSON.stringify(Boolean(new Function('github', 'needs', 'always', 'return (' + expr + ')')(
  github, needs, () => true))));
'''
    condition = workflow()['jobs']['deployment-outcome']['if']
    result = subprocess.run([NODE, '-e', script, json.dumps([condition, event, changes_result])],
                            capture_output=True, text=True, check=True, timeout=10)
    return json.loads(result.stdout)


def run_outcome_gate(changes_result, web_changed, migrate, web, *, event_name='workflow_run', extra_env=None):
    """Run the real gate script (the job's only step that can fail) offline."""
    env = {**os.environ, 'OUTCOME_EVENT_NAME': event_name, 'OUTCOME_SHA': 'a' * 40,
           'OUTCOME_CHANGES_RESULT': changes_result, 'OUTCOME_FORCE_ALL': 'false',
           'OUTCOME_WEB_CHANGED': web_changed, 'OUTCOME_SIDECAR_CHANGED': 'false',
           'OUTCOME_MCP_CHANGED': 'false', 'OUTCOME_PIPELINE_CHANGED': 'false',
           'OUTCOME_SIDECAR_RESULT': 'skipped', 'OUTCOME_MCP_RESULT': 'skipped',
           'OUTCOME_PIPELINE_RESULT': 'skipped'}
    env.pop('NODE_ENV', None)
    env.pop('OUTCOME_WEB_SHADOW', None)
    for name, result in (('OUTCOME_MIGRATE_RESULT', migrate), ('OUTCOME_WEB_RESULT', web)):
        if result is None:
            env.pop(name, None)
        else:
            env[name] = result
    env.update(extra_env or {})
    return subprocess.run([NODE, '--experimental-strip-types', '--no-warnings',
                           str(ROOT / 'platform/scripts/ci/deployment_outcome_gate.ts')],
                          env=env, capture_output=True, text=True, timeout=30)


def test_cancelled_or_superseded_upstream_reports_skipped_not_failure():
    """§N.8: with no green upstream no deployment was attempted, so the outcome
    job must not run (GitHub reports SKIPPED); a FAILURE there is a false alarm.
    `changes` is skipped exactly when workflow_run.conclusion != 'success'.
    """
    doc = workflow()
    assert doc['jobs']['changes']['if'] == "github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'"
    assert doc['jobs']['deployment-outcome']['name'] == 'Require earned deployment outcome'
    assert not outcome_job_runs('workflow_run', 'skipped')


def test_green_upstream_with_skipped_or_failed_deploy_still_fails():
    """§N.8: the real-failure path is preserved. Upstream green means the
    detector ran; a deployable change whose migrate/deploy was skipped or failed
    must still fail, as must a failed or cancelled detector.
    """
    for changes_result in ('success', 'failure', 'cancelled'):
        assert outcome_job_runs('workflow_run', changes_result), changes_result
    probe = subprocess.run([NODE, '--experimental-strip-types', '--no-warnings', '-e', '0'],
                           capture_output=True, text=True)
    if probe.returncode:
        pytest.skip('node lacks --experimental-strip-types; gate verdicts are covered by vitest')
    for migrate, web in (('skipped', 'skipped'), ('success', 'failure')):
        result = run_outcome_gate('success', 'true', migrate, web)
        assert result.returncode == 1, (migrate, web, result.stdout, result.stderr)
        assert 'Deployment outcome not earned' in result.stderr
    assert run_outcome_gate('success', 'true', 'success', 'success').returncode == 0
    assert run_outcome_gate('failure', 'false', 'skipped', 'skipped').returncode == 1


@pytest.mark.parametrize('event_name', ['workflow_run', 'workflow_dispatch'])
def test_admitted_workflow_requires_routine_migration_and_web_without_selected_paths(event_name):
    assert outcome_job_runs(event_name, 'success')
    probe = subprocess.run([NODE, '--experimental-strip-types', '--no-warnings', '-e', '0'],
                           capture_output=True, text=True)
    if probe.returncode:
        pytest.skip('node lacks --experimental-strip-types; gate verdicts are covered by vitest')

    for status in ('skipped', 'failure', 'cancelled', None):
        for job, migrate, web in (('migrate', status, 'success'), ('deploy-web', 'success', status)):
            result = run_outcome_gate('success', 'false', migrate, web, event_name=event_name)
            assert result.returncode == 1, (event_name, job, status, result.stdout, result.stderr)
            assert f'{job}={status or "(missing)"}' in result.stderr

    result = run_outcome_gate('success', 'false', 'success', 'success', event_name=event_name)
    assert result.returncode == 0
    assert 'earned-deployment' in result.stdout


def test_web_shadow_is_terminal_observation_only():
    doc = workflow()
    shadow_steps = [
        (job_id, step)
        for job_id, job in doc['jobs'].items()
        for step in job.get('steps', [])
        if 'OUTCOME_WEB_SHADOW' in step.get('env', {})
    ]
    assert len(shadow_steps) == 1
    job_id, step = shadow_steps[0]
    assert job_id == 'deployment-outcome'
    assert step['env']['OUTCOME_WEB_SHADOW'] == 'true'
    assert step['run'] == 'cd platform && npx --yes tsx scripts/ci/deployment_outcome_gate.ts'
    assert 'outputs' not in doc['jobs'][job_id]
    assert doc['jobs'][job_id]['permissions'] == {'contents': 'read'}
    assert WORKFLOW.read_text().splitlines()[2542].strip().split()[0] == '--task-timeout=86400'

    probe = subprocess.run([NODE, '--experimental-strip-types', '--no-warnings', '-e', '0'],
                           capture_output=True, text=True, timeout=10)
    if probe.returncode:
        pytest.skip('node lacks --experimental-strip-types; shadow is covered by vitest')
    prefix = '[web-reconciliation-shadow] '
    cases = [
        (('success', 'false', 'success', 'success'), {}, 'unknown', 'comparison-unavailable', 'success', 0),
        (('success', 'false', 'skipped', 'success'), {}, 'unknown', 'comparison-unavailable', 'success', 1),
        (('success', 'false', 'success', 'skipped'), {}, 'unknown', 'comparison-unavailable', 'skipped', 1),
        (('success', 'true', 'success', 'failure'), {}, 'rebuild', 'web-selected', 'failure', 1),
        (('failure', 'true', 'skipped', 'skipped'), {}, 'unknown', 'change-detection-unavailable', 'skipped', 1),
        (('success', 'TRUE', 'success', 'missing'), {}, 'unknown', 'invalid-change-signal', 'unknown', 1),
        (('success', 'false', 'success', 'success'), {'OUTCOME_EVENT_NAME': 'workflow_dispatch'},
         'rebuild', 'manual-dispatch', 'success', 0),
        (('success', 'false', 'success', 'success'), {'OUTCOME_FORCE_ALL': 'true'},
         'rebuild', 'force-all', 'success', 1),
        (('success', 'false', 'success', 'skipped'), {'OUTCOME_MCP_CHANGED': 'true', 'OUTCOME_MCP_RESULT': 'success'},
         'rebuild', 'mcp-needs-matching-web', 'skipped', 1),
        (('success', 'false', 'success', 'success'), {'OUTCOME_WEB_CONFIG_MATCH': 'true', 'OUTCOME_WEB_IMAGE_MATCH': 'true'},
         'unknown', 'comparison-unavailable', 'success', 0),
    ]
    for args, env, requested, reason, actual, expected_returncode in cases:
        baseline = run_outcome_gate(*args, extra_env=env)
        observed = run_outcome_gate(*args, extra_env={**env, 'OUTCOME_WEB_SHADOW': step['env']['OUTCOME_WEB_SHADOW']})
        lines = observed.stdout.splitlines(keepends=True)
        reports = [json.loads(line.removeprefix(prefix)) for line in lines if line.startswith(prefix)]
        assert reports == [{
            'comparison': 'unknown', 'requested': requested, 'reason': reason, 'actualWebJobResult': actual,
        }]
        assert observed.returncode == baseline.returncode == expected_returncode
        assert observed.stderr == baseline.stderr
        assert ''.join(line for line in lines if not line.startswith(prefix)) == baseline.stdout


def test_required_contexts_remain_present_and_independent():
    """Branch protection evidence: ci.yml merge-queue comment and the newer
    governance-tool-tests ruleset 20141220 comment (2026-10-05).
    """
    ci = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
    assert {'push', 'pull_request', 'merge_group'} <= set(triggers(ci))
    for event in ('push', 'pull_request', 'merge_group'):
        assert not {'paths', 'paths-ignore'} & set(triggers(ci)[event])
    required = {
        'typecheck': 'TypeScript (src only)', 'unit-tests': 'Unit Tests',
        'secret-scan': 'Secret Scan (unit 0b.2)',
        'governance-gates': 'Governance Gates (drift / schema / edge / native-literal / py-sidecar)',
        'governance-tool-tests': 'Governance Tool Tests (pytest)',
    }
    for key, name in required.items():
        job = ci['jobs'][key]
        assert job['name'] == name
        assert 'pr-changes' not in str(job.get('needs', []))
        # All contexts are scheduled by their workflow. TypeScript/unit jobs
        # report SKIPPED for docs; always-on checks/aggregates report normally.
        condition = job.get('if', 'true')
        assert evaluate(condition, 'pull_request', docs_only='true') is (key not in ('typecheck', 'unit-tests'))
        for event in ('push', 'merge_group'):
            assert evaluate(condition, event)
    assert workflow()['jobs']['build-check']['name'] == 'Build Check (PR only)'


def test_oracles_are_selected_by_profile_and_ci_shard_discovery():
    import importlib.util
    for filename in ('ci_discovery', 'ci_shard'):
        spec = importlib.util.spec_from_file_location(filename, ROOT / f'platform/scripts/governance/{filename}.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if filename == 'ci_discovery':
            assert str(Path(__file__).relative_to(ROOT)) in mod.discover(ROOT, mod.profiles()['deploy-build-check-tests'])
        else:
            assert Path(__file__) in mod.test_files()


def deploy_diff_repo(path, operation, changed_path, destination=None):
    path.mkdir()
    subprocess.run(['git', 'init', '-q', str(path)], check=True, timeout=10)

    def git(*args):
        return subprocess.run(
            ['git', '-c', 'user.name=CI fixture', '-c', 'user.email=fixture@example.invalid',
             '-c', 'commit.gpgsign=false', *args],
            cwd=path, capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()

    def write(name):
        file = path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('fixture\n')

    write('fixture-root')
    if operation in ('delete', 'rename'):
        write(changed_path)
    git('add', '.')
    git('commit', '-qm', 'installed source')
    base = git('rev-parse', 'HEAD')

    if operation == 'add':
        write(changed_path)
    elif operation == 'delete':
        (path / changed_path).unlink()
    elif operation == 'rename':
        assert destination is not None
        (path / destination).parent.mkdir(parents=True, exist_ok=True)
        git('mv', changed_path, destination)
    git('add', '-A')
    git('commit', '-qm', 'candidate source')
    return base


def run_deploy_diff(tmp_path, repo, base, *, fail_diff=False, traffic=None, fail_revision=False, pipeline_image=None):
    """Execute the production selection step; Cloud Run and failure are local fixtures."""
    step = next(s for s in workflow()['jobs']['changes']['steps'] if s.get('id') == 'diff')
    output = tmp_path / 'deploy-output'
    if traffic is None:
        traffic = [{'revisionName': 'fixture-active', 'percent': 100}]
    service = tmp_path / 'fixture-service'
    service.write_text(json.dumps({
        'status': {'latestReadyRevisionName': 'fixture-candidate', 'traffic': traffic},
    }))
    if fail_revision:
        (tmp_path / 'fixture-failed-revision').touch()
    harness = '''
gcloud() {
    case "$1 $2 $3" in
        "run services describe")
            case "$*" in
                *--format=json*) cat ../fixture-service ;;
                *) printf '%s\\n' fixture-candidate ;;
            esac
            ;;
        "run revisions describe")
            case "$4" in
                fixture-active)
                    if [ -f ../fixture-failed-revision ]; then
                        command git rev-parse HEAD
                        return 98
                    fi
                    printf '%s\\n' "$FIXTURE_DEPLOYED_SHA"
                    ;;
                fixture-candidate) command git rev-parse HEAD ;;
                *) return 97 ;;
            esac
            ;;
        "run jobs describe") printf '%s\\n' "$FIXTURE_PIPELINE_IMAGE" ;;
        *) return 97 ;;
    esac
}
git() {
    if [ "$1" = diff ] && [ "$FIXTURE_FAIL_DIFF" = 1 ]; then
        return 128
    fi
    command git "$@"
}
'''
    return subprocess.run(
        ['bash', '-eo', 'pipefail', '-c', harness + step['run']],
        cwd=repo,
        env={**os.environ, 'GITHUB_OUTPUT': str(output),
             'FIXTURE_DEPLOYED_SHA': base, 'FIXTURE_FAIL_DIFF': '1' if fail_diff else '0',
             'FIXTURE_PIPELINE_IMAGE': pipeline_image or f'{PIPELINE_REPO}:{base}'},
        capture_output=True, text=True, timeout=10,
    ), output


@pytest.mark.parametrize('operation,path,destination,selected,not_selected', [
    ('add', '00_ARCHITECTURE/MACRO_PLAN_v2_0.md', None, 'mcp', 'pipeline'),
    ('add', '00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md', None, 'mcp', 'sidecar'),
    ('delete', '00_ARCHITECTURE/CURRENT_STATE_v1_0.md', None, 'mcp', 'pipeline'),
    ('add', '01_FACTS_LAYER/runtime.md', None, 'mcp', 'pipeline'),
    ('add', '025_HOLISTIC_SYNTHESIS/runtime.md', None, 'mcp', 'sidecar'),
    ('add', '025_HOLISTIC_SYNTHESIS/runtime\nnotes.md', None, 'mcp', 'sidecar'),
    ('add', 'platform/scripts/temporal/compute_transits.py', None, 'sidecar', 'mcp'),
    ('delete', 'platform/scripts/temporal/__init__.py', None, 'sidecar', 'mcp'),
    ('rename', 'platform-mcp/resources/runtime.md', 'docs/runtime.md', 'mcp', 'sidecar'),
    ('rename', 'docs/runtime.md', 'platform-mcp/resources/runtime.md', 'mcp', 'sidecar'),
    ('add', '.dockerignore', None, 'mcp', 'sidecar'),
    ('add', '.dockerignore', None, 'pipeline', 'sidecar'),
    ('add', 'platform/.dockerignore', None, 'sidecar', 'mcp'),
    ('add', 'platform/scripts/temporal/notes.md', None, 'web', 'sidecar'),
    ('add', '00_ARCHITECTURE/briefs/madhav_consolidation/KICKOFF.md', None, None, None),
])
def test_production_deploy_diff_selects_actual_copy_inputs(
    tmp_path, operation, path, destination, selected, not_selected,
):
    repo = tmp_path / 'repo'
    base = deploy_diff_repo(repo, operation, path, destination)
    result, output = run_deploy_diff(tmp_path, repo, base)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split('=', 1) for line in output.read_text().splitlines())
    if selected is None:
        assert decisions == dict.fromkeys(('web', 'sidecar', 'mcp', 'pipeline'), 'false')
    else:
        assert decisions[selected] == 'true'
        assert decisions[not_selected] == 'false'


@pytest.mark.parametrize('base', ['', '1234567890abcdef1234567890abcdef12345678'])
def test_production_deploy_diff_preserves_missing_installed_source(tmp_path, base):
    repo = tmp_path / 'repo'
    deploy_diff_repo(repo, 'add', 'docs/guide.md')
    result, output = run_deploy_diff(tmp_path, repo, base)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert decisions == dict.fromkeys(('web', 'sidecar', 'mcp', 'pipeline'), 'true')


def test_production_deploy_diff_fails_when_existing_commit_cannot_be_diffed(tmp_path):
    repo = tmp_path / 'repo'
    base = deploy_diff_repo(repo, 'add', 'platform-mcp/src/index.ts')
    result, output = run_deploy_diff(tmp_path, repo, base, fail_diff=True)
    assert result.returncode != 0
    assert 'cannot diff deployed commit' in result.stderr
    assert not output.exists()


def test_production_deploy_diff_uses_active_traffic_over_newest_ready_revision(tmp_path):
    repo = tmp_path / 'repo'
    base = deploy_diff_repo(repo, 'add', 'platform-mcp/src/index.ts')
    traffic = [
        {'revisionName': 'fixture-active', 'percent': 100},
        {'revisionName': 'fixture-candidate', 'tag': 'smoke'},
    ]
    result, output = run_deploy_diff(tmp_path, repo, base, traffic=traffic)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert decisions == {'web': 'false', 'sidecar': 'false', 'mcp': 'true', 'pipeline': 'false'}


@pytest.mark.parametrize('traffic', [
    [],
    [{'percent': 100}],
    [
        {'revisionName': 'fixture-active', 'percent': 90},
        {'revisionName': 'fixture-candidate', 'percent': 10},
    ],
])
def test_production_deploy_diff_does_not_skip_with_ambiguous_active_traffic(tmp_path, traffic):
    repo = tmp_path / 'repo'
    base = deploy_diff_repo(repo, 'add', 'docs/guide.md')
    result, output = run_deploy_diff(tmp_path, repo, base, traffic=traffic)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert decisions == {'web': 'true', 'sidecar': 'true', 'mcp': 'true', 'pipeline': 'false'}


def test_production_deploy_diff_disregards_partial_revision_lookup_output(tmp_path):
    repo = tmp_path / 'repo'
    base = deploy_diff_repo(repo, 'add', 'docs/guide.md')
    result, output = run_deploy_diff(tmp_path, repo, base, fail_revision=True)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert decisions == {'web': 'true', 'sidecar': 'true', 'mcp': 'true', 'pipeline': 'false'}


CGM_ACTION = "./.github/actions/build-verified-cgm-image"
CGM_PROBE = ROOT / CGM_ACTION / "probe_registration.py"


@pytest.fixture
def cgm_probe():
    import importlib.util

    spec = importlib.util.spec_from_file_location("probe_registration", CGM_PROBE)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    return probe


def pipeline_region_expression(repoint):
    region_arg, = (line.strip() for line in repoint.splitlines() if line.lstrip().startswith("--region="))
    expression = region_arg.removeprefix("--region=").removesuffix(" \\")
    assert expression.startswith("${{ env.") and expression.endswith(" }}")
    return expression


def test_cgm_workflow_build_and_production_handoffs():
    jobs = workflow()["jobs"]
    assert jobs["build-check"]["timeout-minutes"] == 30
    ordinary = jobs["build-check"]["steps"]
    sidecar = jobs["deploy-sidecar"]["steps"]
    pipeline = jobs["deploy-pipeline-job"]["steps"]
    action = yaml.safe_load((CGM_PROBE.parent / "action.yml").read_text())
    build, probe = action["runs"]["steps"]
    assert build["id"] == "build"
    assert probe["env"]["CGM_BUILD_IMAGE_ID"] == "${{ steps.build.outputs.imageid }}"
    assert probe["env"]["CGM_BUILD_DIGEST"] == "${{ steps.build.outputs.digest }}"
    assert probe["env"]["CGM_BUILD_METADATA"] == "${{ steps.build.outputs.metadata }}"

    for steps, names, context, dockerfile, push in (
        (ordinary, ("Build regular sidecar image (load, no push)", "Verify Nirmana route and release smoke are packaged"),
         "./platform", "./platform/python-sidecar/Dockerfile", False),
        (ordinary, ("Build pipeline job image (load, no push)", "Verify ga_writers is importable in the pipeline image"),
         ".", "./platform/python-sidecar/Dockerfile.pipeline", False),
        (sidecar, ("Build and push sidecar image", "Deploy sidecar candidate to Cloud Run (zero traffic)"),
         "./platform", "./platform/python-sidecar/Dockerfile", True),
        (pipeline, ("Build and push pipeline job image", "Re-point Cloud Run Job at the new image"),
         ".", "./platform/python-sidecar/Dockerfile.pipeline", True),
    ):
        build_index, next_index = [next(i for i, step in enumerate(steps) if step.get("name") == name) for name in names]
        selected = steps[build_index]
        assert build_index < next_index
        if steps is pipeline:
            assert next_index == build_index + 1
        assert selected["uses"] == CGM_ACTION and "if" not in selected and "continue-on-error" not in selected
        assert selected["with"]["context"] == context
        assert selected["with"]["file"] == dockerfile
        assert selected["with"]["push"] is push
        assert selected["with"].get("load", False) is not push

    candidate = next(s for s in sidecar if s.get("id") == "deploy-sidecar")
    assert candidate["with"]["image"] == "${{ env.CGM_VERIFIED_IMAGE }}"
    smoke = next(s for s in sidecar if s.get("name") == "Configure authenticated candidate smoke job")
    assert '--image="$CGM_VERIFIED_IMAGE"' in smoke["run"]
    repoint = next(s["run"] for s in pipeline if s.get("name") == "Re-point Cloud Run Job at the new image")
    lines = repoint.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("gcloud run jobs update "))
    assert lines[start - 1] == f"python3 {CGM_PROBE.relative_to(ROOT)} verify-repoint"
    assert lines[start + 2].strip() == '--image="${CGM_VERIFIED_PIPELINE_REF:?missing verified Pipeline image}" \\'
    assert lines[start + 9].strip() == "--quiet"
    region = pipeline_region_expression(repoint)
    assert lines[start + 10] == (
        f'GOOGLE_CLOUD_REGION="{region}" python3 {CGM_PROBE.relative_to(ROOT)} post-repoint'
    )
    assert WORKFLOW.read_text().splitlines()[2542].strip().split()[0] == "--task-timeout=86400"


def fake_digest(value):
    return "sha256:" + value * 64


@pytest.mark.parametrize(("pushed", "component", "failure"), [
    (pushed, component, failure)
    for pushed in (False, True)
    for component in ("amjis-sidecar", "brahma-pipeline")
    for failure in (None, "probe", "identity")
] + [(True, "brahma-pipeline", "pipeline-tag")])
def test_cgm_exact_build_gate(tmp_path, monkeypatch, cgm_probe, pushed, component, failure):
    commit = "a" * 40
    top, child, config = map(fake_digest, "bcd")
    repo = f"{cgm_probe.REGISTRY}/{component}"
    tags = f"{repo}:{commit}\n{repo}:latest" if pushed else f"{component}:pr-check"
    carrier = tmp_path / "job-env"
    file, context = next((f, c) for f, (name, c) in cgm_probe.BUILD_SHAPES.items() if name == component)
    for name, value in {
        "CGM_BUILD_FILE": file, "CGM_BUILD_CONTEXT": context,
        "CGM_BUILD_PUSH": str(pushed).lower(), "CGM_BUILD_LOAD": str(not pushed).lower(),
        "CGM_BUILD_TAGS": tags, "CGM_BUILD_DIGEST": top, "CGM_BUILD_IMAGE_ID": config,
        "GITHUB_ENV": str(carrier), "DEPLOY_SHA": commit,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("CGM_BUILD_METADATA", raising=False)

    calls = []

    def stub(*argv, data=None, timeout=30):
        calls.append(argv)
        if argv[:3] == ("git", "rev-parse", "HEAD"):
            return commit.encode()
        if argv[:2] == ("git", "show"):
            return argv[-1].encode()
        if argv[:4] == ("docker", "buildx", "imagetools", "inspect"):
            if "--raw" in argv:
                assert argv[-1] == f"{repo}@{child}"
                return json.dumps({
                    "mediaType": "application/vnd.oci.image.manifest.v1+json", "config": {"digest": config},
                }).encode()
            assert argv[-1] in (f"{repo}@{top}", f"{repo}:{commit}")
            actual = fake_digest("e") if failure == "pipeline-tag" and argv[-1].endswith(commit) else top
            return json.dumps({
                "digest": actual, "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [{
                    "digest": child, "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "platform": {"os": "linux", "architecture": "amd64"},
                }],
            }).encode()
        if argv[:3] == ("docker", "image", "inspect"):
            assert argv[-1] == (f"{repo}@{child}" if pushed else tags)
            return json.dumps({
                "Id": fake_digest("e") if failure == "identity" else config,
                "Os": "linux", "Architecture": "amd64", "Config": {},
            }).encode()
        if argv[:2] == ("docker", "pull"):
            assert pushed and argv[-1] == f"{repo}@{child}"
            return b""
        assert argv[:2] == ("docker", "run")
        assert argv[2:10] == (
            "--pull=never", "--rm", "-i", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--entrypoint=/usr/bin/env",
        )
        assert argv[10:13] == (config, "-i", "PATH=/usr/local/bin:/usr/bin:/bin")
        assert argv[13:20] == ("python", "-BI", "-X", "pycache_prefix=/dev/null", "-", "inside", component)
        assert len(argv[20:]) == 3 and data == CGM_PROBE.read_bytes()
        return b"CGM registration verified\n" if failure != "probe" else b"generic image smoke passed\n"

    monkeypatch.setattr(cgm_probe, "command", stub)
    if failure:
        with pytest.raises(cgm_probe.ProbeFailure):
            cgm_probe.verify_build()
        assert not carrier.exists()
        return

    cgm_probe.verify_build()
    if not pushed:
        assert not carrier.exists()
        assert not any(command[:3] == ("docker", "buildx", "imagetools") for command in calls)
        return
    expected = f"CGM_VERIFIED_IMAGE={repo}@{child}\n"
    if component == cgm_probe.PIPELINE:
        assert calls[-1][-1] == f"{repo}:{commit}"
        expected += f"CGM_VERIFIED_PIPELINE_REF={repo}:{commit}@{child}\n"
    assert carrier.read_text() == expected


@pytest.mark.parametrize("failure", [
    None, "wrong-repository", "wrong-source", "malformed-digest", "missing-image", "rebound-carrier",
    "tag-only", "digest-only", "configured-repository", "configured-source", "configured-platform", "normalized",
])
def test_cgm_pipeline_post_repoint(monkeypatch, cgm_probe, failure):
    repo = PIPELINE_REPO
    commit = "a" * 40
    child, wrong = map(fake_digest, "bc")
    image = f"{repo}@{child}"
    reference = f"{repo}:{commit}@{child}"
    monkeypatch.setenv("DEPLOY_SHA", commit if failure != "wrong-source" else "not-a-commit")
    monkeypatch.setenv("GOOGLE_CLOUD_REGION", "example-region")
    monkeypatch.setenv("CGM_VERIFIED_IMAGE", {
        "wrong-repository": f"{repo}-other@{child}",
        "malformed-digest": f"{repo}@sha256:ab",
    }.get(failure, image))
    monkeypatch.setenv("CGM_VERIFIED_PIPELINE_REF", (
        f"{repo}:{commit}@{wrong}" if failure == "rebound-carrier" else reference
    ))
    if failure == "missing-image":
        monkeypatch.delenv("CGM_VERIFIED_IMAGE")
    configured = {
        "tag-only": f"{repo}:{commit}",
        "digest-only": image,
        "configured-repository": f"{repo}-other:{commit}@{child}",
        "configured-source": f"{repo}:{'f' * 40}@{child}",
        "configured-platform": f"{repo}:{commit}@{wrong}",
        "normalized": f"{reference} ",
    }
    calls = []

    def stub(*argv):
        calls.append(argv)
        assert argv[:7] == (
            "gcloud", "run", "jobs", "describe", "brahma-build-pipeline-job", "--region", "example-region",
        )
        return (configured.get(failure, reference) + "\n").encode()

    monkeypatch.setattr(cgm_probe, "command", stub)
    if failure:
        with pytest.raises(cgm_probe.ProbeFailure):
            cgm_probe.post_repoint()
    else:
        cgm_probe.post_repoint()
    assert len(calls) == int(failure is None or failure in configured)


@pytest.mark.parametrize("mode", ["exact", "rebound", "tag-only"])
def test_cgm_pipeline_repoint_shell_fails_closed(tmp_path, mode):
    commit = "a" * 40
    child = fake_digest("b")
    reference = f"{PIPELINE_REPO}:{commit}@{child}"
    trace = tmp_path / "trace"
    gcloud = tmp_path / "gcloud"
    gcloud.write_text(
        '#!/usr/bin/env python3\n'
        'import json, os, sys\n'
        'with open(os.environ["CGM_TEST_TRACE"], "a") as f:\n'
        '    f.write(json.dumps(sys.argv[1:]) + "\\n")\n'
        'if sys.argv[3] == "describe":\n'
        '    print(os.environ["CGM_TEST_CONFIGURED"])\n'
    )
    gcloud.chmod(0o755)
    repoint = next(
        step["run"] for step in workflow()["jobs"]["deploy-pipeline-job"]["steps"]
        if step.get("name") == "Re-point Cloud Run Job at the new image"
    )
    env = {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
           "DEPLOY_SHA": commit, "CGM_VERIFIED_IMAGE": f"{PIPELINE_REPO}@{child}",
           "CGM_VERIFIED_PIPELINE_REF": reference if mode != "rebound" else f"{PIPELINE_REPO}:{commit}@{fake_digest('c')}",
           "CGM_TEST_TRACE": str(trace),
           "CGM_TEST_CONFIGURED": reference if mode != "tag-only" else f"{PIPELINE_REPO}:{commit}"}
    env.pop("GOOGLE_CLOUD_REGION", None)
    rendered = repoint.replace(pipeline_region_expression(repoint), "example-region")
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", rendered], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == (0 if mode == "exact" else 1)
    if mode == "rebound":
        assert not trace.exists()
        return
    update, describe = [json.loads(line) for line in trace.read_text().splitlines()]
    assert update[:4] == ["run", "jobs", "update", "brahma-build-pipeline-job"]
    assert update[4:6] == ["--region=example-region", f"--image={reference}"]
    assert "--task-timeout=86400" in update
    assert describe[:6] == ["run", "jobs", "describe", "brahma-build-pipeline-job", "--region", "example-region"]


@pytest.mark.parametrize("mutation", [None, "wrong-class", "missing-key", "alias", "hash", "origin", "wrong-base"])
def test_cgm_named_registration_and_historical_aliases(tmp_path, monkeypatch, cgm_probe, mutation):
    import hashlib
    import sys
    from types import SimpleNamespace

    class WriterBase:
        def __init__(self):
            pytest.fail("must not construct a writer")

    class BoBimbaWriter(WriterBase):
        pass

    class BoKaranajalaWriter(WriterBase):
        pass

    identity = SimpleNamespace(
        SUBJECT_TO_GRAHA={"sun": "Sun"}, YOGA_NODE_CLASSES=("yoga",),
        _yoga_config_name=lambda: None, yoga_node_subject=lambda: None,
    )
    bimba = SimpleNamespace(
        BoBimbaWriter=BoBimbaWriter, _SUBJECT_TO_GRAHA=identity.SUBJECT_TO_GRAHA,
        _YOGA_NODE_CLASSES=identity.YOGA_NODE_CLASSES, _yoga_config_name=identity._yoga_config_name,
        yoga_node_subject=identity.yoga_node_subject,
    )
    karanajala = SimpleNamespace(
        BoKaranajalaWriter=BoKaranajalaWriter, _GRAHA_SUBJECT_MAP=identity.SUBJECT_TO_GRAHA,
        _YOGA_NODE_CLASSES=identity.YOGA_NODE_CLASSES, _yoga_node_subject=identity.yoga_node_subject,
    )
    expected = []
    for name, module in zip(cgm_probe.MODULES, (identity, bimba, karanajala)):
        source = tmp_path / (name.replace(".", "/") + ".py")
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"# {name}\n")
        module.__file__ = str(source)
        expected.append(hashlib.sha256(source.read_bytes()).hexdigest())
    entries = {"bo_bimba": BoBimbaWriter, "bo_karanajala": BoKaranajalaWriter}
    registry = SimpleNamespace(WRITER_REGISTRY=entries, WriterBase=WriterBase)
    if mutation == "wrong-class":
        entries["bo_bimba"] = type("BoBimbaWriter", (WriterBase,), {})
    elif mutation == "missing-key":
        entries.pop("bo_karanajala")
    elif mutation == "alias":
        karanajala._GRAHA_SUBJECT_MAP = dict(identity.SUBJECT_TO_GRAHA)
    elif mutation == "hash":
        expected[0] = "0" * 64
    elif mutation == "origin":
        bimba.__file__ = identity.__file__
    elif mutation == "wrong-base":
        registry.WriterBase = type("WrongBase", (), {})

    modules = dict(zip(cgm_probe.MODULES, (identity, bimba, karanajala)))
    modules["pipeline.orchestrator.writers"] = registry
    monkeypatch.setattr(cgm_probe.importlib, "import_module", modules.__getitem__)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    if mutation:
        with pytest.raises(cgm_probe.ProbeFailure):
            cgm_probe.verify_registration(tmp_path, expected)
    else:
        cgm_probe.verify_registration(tmp_path, expected)


@pytest.mark.parametrize("mode", ["metadata", "agree", "conflict", "missing"])
def test_cgm_loaded_image_identity_carrier(monkeypatch, cgm_probe, mode):
    config = fake_digest("d")
    monkeypatch.setenv("CGM_BUILD_METADATA", json.dumps(
        {"containerimage.config.digest": config} if mode != "missing" else {},
    ))
    monkeypatch.setenv(
        "CGM_BUILD_IMAGE_ID", config if mode == "agree" else fake_digest("e") if mode == "conflict" else "",
    )
    if mode in ("conflict", "missing"):
        with pytest.raises(cgm_probe.ProbeFailure):
            cgm_probe.loaded_build_id()
    else:
        assert cgm_probe.loaded_build_id() == config


@pytest.mark.parametrize("mode", ["single", "duplicate", "no-amd64"])
def test_cgm_manifest_identity(monkeypatch, cgm_probe, mode):
    manifest = {"digest": fake_digest("b"), "mediaType": "application/vnd.oci.image.manifest.v1+json"}
    if mode != "single":
        platform = {"os": "linux", "architecture": "amd64" if mode == "duplicate" else "arm64"}
        manifest = {
            "digest": fake_digest("b"), "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [{**manifest, "platform": platform}] * 2,
        }
    monkeypatch.setattr(cgm_probe, "command", lambda *argv: json.dumps(manifest).encode())
    if mode == "single":
        assert cgm_probe.manifest_identity("fixture/image") == (fake_digest("b"), fake_digest("b"))
    else:
        with pytest.raises(cgm_probe.ProbeFailure):
            cgm_probe.manifest_identity("fixture/image")


@pytest.mark.parametrize(("image", "unresolved"), [
    ("{repo}:{base}", False),
    ("{repo}:{base}@{digest}", False),
    ("{repo}@{digest}", True),
    ("{repo}-other:{base}@{digest}", True),
    ("{repo}:latest", True),
    ("{repo}:{base}@sha256:abc", True),
    ("{repo}:{base}@{digest}!", True),
    ("{repo}:{base}@{digest}@{digest}", True),
    ("{repo}:{base}@SHA256:abc", True),
])
def test_cgm_preserves_pipeline_commit_tag_selection(tmp_path, image, unresolved):
    repo = tmp_path / "repo"
    base = deploy_diff_repo(repo, "add", "docs/notes.md")
    pipeline_image = image.format(repo=PIPELINE_REPO, base=base, digest=fake_digest("d"))
    result, output = run_deploy_diff(tmp_path, repo, base, pipeline_image=pipeline_image)
    assert result.returncode == 0, result.stderr
    decisions = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert decisions["pipeline"] == str(unresolved).lower()
    assert all(decisions[name] == "false" for name in ("web", "sidecar", "mcp"))


@pytest.mark.parametrize(("selector", "result_key", "job"), [
    ("OUTCOME_SIDECAR_CHANGED", "OUTCOME_SIDECAR_RESULT", "deploy-sidecar"),
    ("OUTCOME_PIPELINE_CHANGED", "OUTCOME_PIPELINE_RESULT", "deploy-pipeline-job"),
])
def test_cgm_required_job_failure_remains_terminal(selector, result_key, job):
    if subprocess.run([NODE, "--experimental-strip-types", "--no-warnings", "-e", "0"],
                      capture_output=True, text=True).returncode:
        pytest.skip("node lacks --experimental-strip-types; gate verdicts are covered by vitest")
    result = run_outcome_gate("success", "false", "success", "success",
                              extra_env={selector: "true", result_key: "failure"})
    assert result.returncode == 1
    assert f"{job}=failure" in result.stderr
