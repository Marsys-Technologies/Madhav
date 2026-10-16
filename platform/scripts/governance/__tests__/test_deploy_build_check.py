"""Deploy demand oracles: owner madhav-6d job; CLAUDE.md §N.8.

The policy comes from the job's runner-cap requirement and the actual Docker
COPY inputs, rather than captured build output. GitHub expressions are executed
with Node, as in test_ci_generated.py; no workflow/API/Docker is dispatched.
"""
import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / '.github/workflows/deploy.yml'


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
    assert outcome['if'] == "${{ always() && github.event_name != 'pull_request' }}"
    assert set(outcome['needs']) == {'changes', 'migrate', 'deploy-web', 'deploy-sidecar', 'deploy-mcp', 'deploy-pipeline-job'}
    assert doc['concurrency']['cancel-in-progress'] == "${{ github.event_name == 'pull_request' }}"


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
