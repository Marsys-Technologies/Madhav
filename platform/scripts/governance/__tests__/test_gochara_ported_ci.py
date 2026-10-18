"""P05-B02: ported AM-7 and readback oracles must execute in mandatory CI.

Removing a suite, its DB environment, or the required aggregate dependency must fail.
The Python command includes real-cluster cases and rejects skipped JUnit results.
"""
from __future__ import annotations

from _ci_gate_test_support import runs_in_full_gate

import copy
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

CI = Path(__file__).resolve().parents[4] / '.github/workflows/ci.yml'
READBACK_SUITES = (
    'platform/scripts/__tests__/test_gochara_window_readbacks.py',
    'platform/scripts/__tests__/test_fn_1235_readbacks.py',
    'platform/scripts/__tests__/test_gochara_rehearsal.py',
)
AM7 = 'tests/integration/gochara_b6_v15_migrations.db.test.ts'


@pytest.fixture
def jobs():
    return _ci_load(CI.read_text())['jobs']


def _commands(step):
    return [shlex.split(line) for line in str(step.get('run', '')).replace('\\\n', ' ').splitlines()
            if ('vitest' in line or 'pytest' in line) and not line.lstrip().startswith('#')]


def _readback_problems(jobs):
    problems = []
    job = jobs.get('governance-readback-tests', {})
    if 'governance-readback-tests' not in jobs['governance-tool-tests']['needs']:
        problems.append('missing required aggregate dependency')
    aggregate = jobs['governance-tool-tests']
    if not any('${{ needs.governance-readback-tests.result }}' in str(s.get('env', {}))
               and 'READBACK_RESULT' in str(s.get('run', '')) for s in aggregate['steps']):
        problems.append('readback result not checked by aggregate')
    if job.get('continue-on-error') or 'changes' not in str(job.get('needs', '')):
        problems.append('optional readback job')
    if not runs_in_full_gate(job):
        problems.append('not fail closed for full events')
    if not any('apt-get install' in str(s.get('run', '')) and 'postgresql' in str(s.get('run', ''))
               for s in job.get('steps', [])):
        problems.append('no PostgreSQL server binaries installed')
    steps = [s for s in job.get('steps', []) if any('pytest' in c for c in _commands(s))]
    for suite in READBACK_SUITES:
        matches = [s for s in steps if any('pytest' in c and suite in c for c in _commands(s))]
        if not matches:
            problems.append('missing suite: ' + suite)
        for step in matches:
            commands = [c[c.index('pytest') + 1:] for c in _commands(step) if 'pytest' in c]
            if not runs_in_full_gate(step) or step.get('continue-on-error'):
                problems.append('optional pytest step')
            if any(any(t in ('-k', '-m', '--deselect', '--ignore', '--collect-only', '||', ';', '|')
                       or t.startswith(('--deselect=', '--ignore=')) for t in c) for c in commands):
                problems.append('filtered or swallowed pytest command')
            if not any(any(t.startswith('--junitxml=') for t in c) for c in commands):
                problems.append('no JUnit evidence')
            run = str(step.get('run', ''))
            if 'skipped' not in run or 'SystemExit' not in run:
                problems.append('skips not rejected')
    return problems


def test_am7_runs_in_the_db_enabled_gochara_command(jobs):
    job = jobs['db-integration-tests']
    steps = [s for s in job['steps'] if any(AM7 in c and 'vitest' in c for c in _commands(s))]
    assert len(steps) == 1, 'AM-7 omitted from the DB-enabled Gochara command'
    step = steps[0]
    assert step['env']['GOCHARA_A51_TEST_DATABASE_URL'].endswith('/gochara_a51_test')
    assert str(step['env']['GOCHARA_REQUIRE_DB']) == '1'
    assert runs_in_full_gate(step) and not step.get('continue-on-error')
    assert '--no-file-parallelism' in step['run']


def test_readbacks_are_mandatory_and_include_all_real_cluster_cases(jobs):
    assert _readback_problems(jobs) == []


@pytest.mark.parametrize('suite', READBACK_SUITES)
def test_removing_either_readback_suite_is_detected(jobs, suite):
    changed = copy.deepcopy(jobs)
    for step in changed.get('governance-readback-tests', {}).get('steps', []):
        step['run'] = str(step.get('run', '')).replace(suite, '')
    assert 'missing suite: ' + suite in _readback_problems(changed)


def test_removing_the_required_readback_dependency_is_detected(jobs):
    changed = copy.deepcopy(jobs)
    changed['governance-tool-tests']['needs'] = [x for x in changed['governance-tool-tests']['needs']
                                                if x != 'governance-readback-tests']
    assert 'missing required aggregate dependency' in _readback_problems(changed)


@pytest.mark.parametrize("skipped", [False, True])
def test_the_ci_junit_check_rejects_skipped_oracles(jobs, tmp_path, skipped):
    steps = jobs['governance-readback-tests']['steps']
    step = next(s for s in steps if '--junitxml=' in str(s.get('run', '')))
    command = next(shlex.split(line) for line in step['run'].splitlines() if 'ET.parse(' in line)
    report = '<testsuites><testsuite><testcase>' + ('<skipped />' if skipped else '') + '</testcase></testsuite></testsuites>'
    (tmp_path / 'gochara-readbacks.xml').write_text(report)
    proc = subprocess.run([sys.executable, *command[1:]], cwd=tmp_path, capture_output=True, text=True)
    assert (proc.returncode != 0) is skipped
    if skipped:
        assert 'required Gochara readback oracles skipped' in proc.stderr

from pathlib import Path as _CiPath
import sys as _ci_sys
_ci_sys.path.insert(0, str(_CiPath(__file__).resolve().parents[4] / 'platform/scripts/governance'))
from ci_discovery import expanded_workflow as _ci_expanded

def _ci_load(text):
    import yaml
    data = yaml.safe_load(text)
    data['jobs'] = _ci_expanded(data['jobs'])
    return data
