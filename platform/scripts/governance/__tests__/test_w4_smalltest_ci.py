"""The production-deletion safety proofs remain in mandatory CI."""
import copy
from pathlib import Path
import pytest
import yaml

CI = Path(__file__).resolve().parents[4] / '.github/workflows/ci.yml'
SUITE = 'scripts/__tests__/test_w4_smalltest_safety.py'


def mandatory_safety_step(jobs, suite=SUITE):
    job = jobs['db-integration-tests']
    steps = [s for s in job['steps'] if suite in str(s.get('run', ''))]
    return (len(steps) == 1 and not job.get('continue-on-error')
            and not steps[0].get('if') and not steps[0].get('continue-on-error')
            and 'pytest' in steps[0]['run'] and '||' not in steps[0]['run']
            and not any(flag in steps[0]['run'] for flag in (' -k ', ' --deselect', ' --collect-only')))


def test_w4_safety_suite_runs_in_mandatory_database_integration_check():
    assert mandatory_safety_step(yaml.safe_load(CI.read_text())['jobs'])


@pytest.mark.parametrize('mutation', ['remove', 'optional', 'filter', 'swallow'])
def test_a_weakened_safety_ci_binding_is_detected(mutation):
    jobs = yaml.safe_load(CI.read_text())['jobs']
    step = next(s for s in jobs['db-integration-tests']['steps'] if SUITE in str(s.get('run', '')))
    if mutation == 'remove': step['run'] = step['run'].replace(SUITE, '')
    elif mutation == 'optional': step['continue-on-error'] = True
    elif mutation == 'filter': step['run'] += ' -k only_one'
    else: step['run'] += ' || true'
    assert not mandatory_safety_step(jobs)


def test_real_w4_rollback_and_independent_readback_run_in_required_db_job():
    jobs = yaml.safe_load(CI.read_text())['jobs']
    step = next(s for s in jobs['gochara-a55-teardown']['steps'] if
        'tests/l3/gochara/test_w4_smalltest_safety_db.py' in str(s.get('run', '')))
    assert not step.get('if') and not step.get('continue-on-error')
    assert str(step['env']['GOCHARA_A53_REQUIRE_DB']) == '1'
    assert '--tb=short' in step['run'] and '-p no:cacheprovider' in step['run']


@pytest.mark.parametrize('suite', [
    '../00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_w4_smalltest_enablement.py',
    '../00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_smalltest_launch.py',
])
def test_admission_and_launch_fixtures_run_in_mandatory_ci(suite):
    assert mandatory_safety_step(yaml.safe_load(CI.read_text())['jobs'], suite)
