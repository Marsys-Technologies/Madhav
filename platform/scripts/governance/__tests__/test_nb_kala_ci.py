"""NB-KALA required-check wiring executes fail-closed, including skipped DBs."""
import json
import os
from pathlib import Path
import subprocess
import sys

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


def _full_suite(result, event, selected, extra=None):
    """Run the real full-suite contract script with kala-db-tests set to `result`."""
    job = jobs()['full-suite']
    command = job['steps'][0]['run']
    needs = {name: {'result': 'success'} for name in job['needs']}
    needs['kala-db-tests'] = {'result': result}
    needs.update(extra or {})
    return subprocess.run(['bash', '-c', command], capture_output=True, text=True,
        env={'PATH': os.environ['PATH'], 'EVENT_NAME': event, 'REF': 'refs/heads/x', 'FULL_GATE': '',
             'DB_JOBS': json.dumps(selected), 'NEEDS_JSON': json.dumps(needs)})


@pytest.mark.parametrize('result', ['success', 'failure', 'cancelled', 'skipped', ''])
@pytest.mark.parametrize('event,selected,executes', [
    ('merge_group', [], True), ('pull_request', ['kala-db-tests'], True), ('pull_request', [], False)])
def test_actual_full_suite_rejects_failed_and_unexplained_skipped_kala_db(result, event, selected, executes):
    run = _full_suite(result, event, selected)
    expected = result == 'success' or (result == 'skipped' and not executes)
    assert (run.returncode == 0) == expected, (result, event, selected, run.stdout, run.stderr)


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
