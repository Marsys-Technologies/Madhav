"""NB-KALA required-check wiring executes fail-closed, including skipped DBs."""
import itertools
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
    aggregate = jobs()['governance-gates']
    assert 'kala-db-tests' in aggregate['needs']
    assert aggregate['steps'][0]['env']['KALA_RESULT'] == '${{ needs.kala-db-tests.result }}'


@pytest.mark.parametrize('result,docs_only', list(itertools.product(
    ['success', 'failure', 'cancelled', 'skipped', ''], ['true', 'false', ''])))
def test_actual_aggregate_rejects_missing_failed_and_unexplained_skipped_db(result, docs_only):
    command = jobs()['governance-gates']['steps'][0]['run']
    run = subprocess.run(['bash', '-c', command], capture_output=True, text=True,
        env={'PATH': '/usr/bin:/bin', 'STATIC_RESULT': 'success', 'SHARDS_RESULT': 'success',
             'K3_RESULT': 'success', 'KALA_RESULT': result, 'DOCS_ONLY': docs_only})
    expected = result == 'success' or (result == 'skipped' and docs_only == 'true')
    assert (run.returncode == 0) == expected, (result, docs_only, run.stdout)


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
