"""NB-KALA required-check wiring executes fail-closed, including skipped DBs."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
SUITE = 'src/tools/retrieval/register_gochara_windows_kcert_assessment.test.ts'


def jobs():
    sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
    from ci_discovery import expanded_workflow
    return expanded_workflow(yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs'])


def test_kala_database_proof_is_a_required_aggregate_dependency():
    all_jobs = jobs()
    assert 'full-suite' in all_jobs['governance-gates']['needs']
    assert 'kala-db-tests' in all_jobs['full-suite']['needs']


def _full_suite(result, event, selected, ref='refs/heads/x', full_gate='', extra=None):
    """Run the real full-suite contract script with kala-db-tests set to `result`."""
    job = jobs()['full-suite']
    command = job['steps'][0]['run']
    needs = {name: {'result': 'success'} for name in job['needs']}
    needs['kala-db-tests'] = {'result': result}
    needs.update(extra or {})
    return subprocess.run(['bash', '-c', command], capture_output=True, text=True,
        env={'PATH': os.environ['PATH'], 'EVENT_NAME': event, 'REF': ref, 'FULL_GATE': full_gate,
             'DB_JOBS': json.dumps(selected), 'NEEDS_JSON': json.dumps(needs)})


# Every event that merges or releases code must execute the Kala DB proof; a PR may
# skip it only when the change classifier did not select it (ci.yml header, D-29).
@pytest.mark.parametrize('result', ['success', 'failure', 'cancelled', 'skipped', ''])
@pytest.mark.parametrize('event,ref,full_gate,selected,executes', [
    ('merge_group', 'refs/heads/x', '', [], True),
    ('push', 'refs/heads/main', '', [], True),
    ('workflow_dispatch', 'refs/heads/x', 'true', [], True),
    ('pull_request', 'refs/heads/x', '', ['kala-db-tests'], True),
    ('pull_request', 'refs/heads/x', '', [], False)])
def test_actual_full_suite_rejects_failed_and_unexplained_skipped_kala_db(
        result, event, ref, full_gate, selected, executes):
    run = _full_suite(result, event, selected, ref=ref, full_gate=full_gate)
    expected = result == 'success' or (result == 'skipped' and not executes)
    assert (run.returncode == 0) == expected, (result, event, selected, run.stdout, run.stderr)


def _expression(text, event, ref='refs/heads/x', full_gate=False, db_jobs=(), db_profiles=()):
    """Evaluate a ci.yml `if:` expression over the closed set of names the workflow uses."""
    body = re.fullmatch(r'\s*\$\{\{(.*)\}\}\s*', str(text), re.S)
    assert body, text
    source = body[1].replace('&&', ' and ').replace('||', ' or ').replace('!cancelled()', 'True')
    scope = {
        '__builtins__': {},
        'github': SimpleNamespace(event_name=event, ref=ref),
        'inputs': SimpleNamespace(full_gate=full_gate),
        'needs': SimpleNamespace(changes=SimpleNamespace(outputs=SimpleNamespace(
            db_jobs=json.dumps(list(db_jobs)), db_profiles=json.dumps(list(db_profiles))))),
        'fromJSON': json.loads,
        'contains': lambda haystack, needle: needle in haystack,
    }
    return bool(eval(source, scope))  # noqa: S307 - repository-owned workflow text only


FULL_EVENTS = [('merge_group', 'refs/heads/x', False), ('push', 'refs/heads/main', False),
               ('workflow_dispatch', 'refs/heads/x', True)]


def _raw_job(name):
    return yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs'][name]


def _db_steps(job):
    """Steps that run a kala-db-tests* discovery profile (unexpanded, so profiles stay named)."""
    return [s for s in job['steps'] if re.search(r'ci_discovery\.py"? pytest kala-db-tests-', s.get('run', ''))]


@pytest.mark.parametrize('event,ref,full_gate', FULL_EVENTS)
def test_kala_db_job_and_every_test_step_execute_on_each_full_event(event, ref, full_gate):
    job = _raw_job('kala-db-tests')
    steps = _db_steps(job)
    assert len(steps) == 4, [s.get('name') for s in steps]
    assert _expression(job['if'], event, ref, full_gate)
    for step in steps:
        assert _expression(step['if'], event, ref, full_gate), step['name']


def test_kala_db_job_is_skipped_on_a_pull_request_that_did_not_select_it():
    job = _raw_job('kala-db-tests')
    assert not _expression(job['if'], 'pull_request')
    assert _expression(job['if'], 'pull_request', db_jobs=['kala-db-tests'])


def test_kala_db_steps_make_a_missing_database_or_a_skip_fatal():
    job = _raw_job('kala-db-tests')
    assert 'continue-on-error' not in job
    port = str(job['services']['postgres']['ports'][0]).split(':')[0]
    for step in _db_steps(job):
        assert 'continue-on-error' not in step, step['name']
        assert not re.search(r'\|\|\s*true|set \+e', step['run']), step['name']
    # 5-0 and parihara collect real database tests; the pure-Python 7-0/8-0 steps have none.
    for step in (s for s in _db_steps(job) if re.search(r'kala-db-tests-(?:5-0|parihara) --', s['run'])):
        env = step['env']
        assert str(env['KALA_REQUIRE_DB']) == '1', step['name']
        assert env['KALA_ADMIN_DSN'].endswith(f'@localhost:{port}/postgres'), step['name']


def test_density_census_executes_projection_aware_kcert_serving_regression(tmp_path):
    job = jobs()['density-census']
    steps = [step for step in job['steps'] if SUITE in step.get('run', '')]
    assert steps, 'K-CERT serving assertions must execute in mandatory Density Census'
    launcher = tmp_path / 'npx'
    launcher.write_text('#!/bin/sh\nprintf "%s\n" "$@" > "$NB_ARGS"\n')
    launcher.chmod(0o755)
    args = tmp_path / 'args'
    for step in steps:
        assert not step.get('if') and not step.get('continue-on-error')
        assert step['working-directory'] == 'platform-mcp'
        subprocess.run(['bash', '-e', '-c', step['run']], check=True,
            env={**os.environ, 'PATH': str(tmp_path) + ':/usr/bin:/bin', 'NB_ARGS': str(args)})
        assert args.read_text().splitlines()[:2] == ['vitest', 'run']
        assert SUITE in args.read_text().splitlines()
    assert (ROOT / 'platform-mcp' / SUITE).is_file()
