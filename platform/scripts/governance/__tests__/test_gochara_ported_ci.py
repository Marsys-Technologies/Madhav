"""P05-B02: ported AM-7 and readback oracles must execute in mandatory CI.

Removing a suite, its DB environment, or the required aggregate dependency must fail.
The Python command includes real-cluster cases and rejects skipped JUnit results.
"""
from __future__ import annotations

from _ci_gate_test_support import evaluate, runs_in_full_gate

import copy
import re
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

NATIVE_SETUP = 'Install pytest and disposable PostgreSQL server binaries'
# Pin only the required setup recipe. test_lane_smalltest_ci executes this shell against inert binaries.
NATIVE_SETUP_RUN = r"""native_pg_bin=/usr/lib/postgresql/16/bin
native_pg_release=
for tool in postgres initdb pg_ctl psql; do
  binary="$native_pg_bin/$tool"
  if [[ ! -f "$binary" || ! -x "$binary" || "$(readlink -f -- "$binary")" != "$binary" ]]; then
    echo "::error::Missing or unexpected native PostgreSQL 16 executable: $binary"
    exit 1
  fi
  if ! banner="$(LC_ALL=C "$binary" --version)" ||
     [[ ! $banner =~ ^$tool\ \(PostgreSQL\)\ (16\.[0-9]+)([[:blank:]]|$) ]]; then
    echo "::error::Cannot verify native PostgreSQL 16 version: $binary"
    exit 1
  fi
  if [[ -n "$native_pg_release" && "$native_pg_release" != "${BASH_REMATCH[1]}" ]]; then
    echo "::error::Mismatched native PostgreSQL releases in $native_pg_bin"
    exit 1
  fi
  native_pg_release="${BASH_REMATCH[1]}"
done
python -m pip install pytest 'psycopg[binary]'
printf 'SUVARNA_PG_BIN=%s\n' "$native_pg_bin" >> "$GITHUB_ENV"
printf '%s\n' "$native_pg_bin" >> "$GITHUB_PATH"
"""


@pytest.fixture
def jobs():
    return _ci_load(CI.read_text())['jobs']


def _commands(step):
    return [shlex.split(line) for line in str(step.get('run', '')).replace('\\\n', ' ').splitlines()
            if ('vitest' in line or 'pytest' in line) and not line.lstrip().startswith('#')]


def _native_setup_problems(job):
    steps = job.get('steps', [])
    setups = [(index, step) for index, step in enumerate(steps) if step.get('name') == NATIVE_SETUP]
    readbacks = [(index, step) for index, step in enumerate(steps)
                 if any('pytest' in command and any(suite in command for suite in READBACK_SUITES)
                        for command in _commands(step))]
    if len(setups) != 1 or not readbacks or setups[0][0] >= readbacks[0][0]:
        return ['native PostgreSQL setup missing or after readback']

    _, setup = setups[0]
    inherited_shell = job.get('defaults', {}).get('run', {}).get('shell')
    if (job.get('runs-on') != 'ubuntu-24.04' or setup.get('if') is not None or setup.get('continue-on-error')
            or setup.get('shell', inherited_shell) not in (None, 'bash')):
        return ['native PostgreSQL setup is optional or lacks the expected runner and shell']
    if setup.get('run', '').strip() != NATIVE_SETUP_RUN.strip():
        return ['native PostgreSQL setup must verify and bind the preinstalled PG16 binaries']

    problems = []
    if job.get('env', {}).get('KALA_ADMIN_DSN'):
        problems.append('native readback fixture or client binding overridden')
    for _, step in readbacks:
        if re.search(r'\b(?:always|cancelled|failure|success)\s*\(', str(step.get('if', ''))):
            problems.append('native readback can bypass failed setup')
        if any(not evaluate(item.get('if'), event=event, selected=('governance-readback-tests',),
                            profiles=('governance-readback-tests-3-0',))
               for item in (job, step) for event in ('pull_request', 'merge_group')):
            problems.append('native readbacks omitted from a selected PR or merge group')
        if {'SUVARNA_PG_BIN', 'PATH', 'KALA_ADMIN_DSN'} & set(step.get('env', {})):
            problems.append('native readback fixture or client binding overridden')
    return problems


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
    problems.extend(_native_setup_problems(job))
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


@pytest.mark.parametrize(('old', 'new'), [
    ('native_pg_bin=/usr/lib/postgresql/16/bin', 'native_pg_bin=/usr/lib/postgresql/17/bin'),
    ('|| "$(readlink -f -- "$binary")" != "$binary"', ''),
    (r'(16\.[0-9]+)', r'(1[67]\.[0-9]+)'),
    ('"$native_pg_release" != "${BASH_REMATCH[1]}"', 'false'),
    ('exit 1', 'true'),
    ("printf 'SUVARNA_PG_BIN", "# printf 'SUVARNA_PG_BIN"),
    ('>> "$GITHUB_PATH"', '>> "$GITHUB_ENV"'),
])
def test_native_setup_requires_real_preflight_and_bindings(jobs, old, new):
    job = jobs['governance-readback-tests']
    setup = next(step for step in job['steps'] if step.get('name') == NATIVE_SETUP)
    assert old in setup['run']
    setup['run'] = setup['run'].replace(old, new, 1)
    assert 'native PostgreSQL setup must verify and bind the preinstalled PG16 binaries' in _readback_problems(jobs)


@pytest.mark.parametrize('mutation', ['omitted', 'late', 'condition', 'continue-on-error', 'wrong-shell'])
def test_native_setup_is_required_before_readback(jobs, mutation):
    steps = jobs['governance-readback-tests']['steps']
    setup = next(step for step in steps if step.get('name') == NATIVE_SETUP)
    if mutation == 'omitted':
        steps.remove(setup)
    elif mutation == 'late':
        steps.remove(setup)
        steps.append(setup)
    elif mutation == 'condition':
        setup['if'] = '${{ false }}'
    elif mutation == 'continue-on-error':
        setup['continue-on-error'] = True
    else:
        setup['shell'] = 'bash {0}'
    assert any(problem.startswith('native PostgreSQL setup') for problem in _readback_problems(jobs))


@pytest.mark.parametrize('mutation', ['predicate', 'failed-setup', 'fixture', 'client', 'admin-dsn', 'job-admin-dsn'])
def test_native_setup_reaches_the_actual_readback_step(jobs, mutation):
    job = jobs['governance-readback-tests']
    step = next(step for step in job['steps']
                if any(READBACK_SUITES[0] in command for command in _commands(step)))
    if mutation == 'predicate':
        step['if'] = step['if'].replace("github.event_name == 'merge_group'", "false")
        assert 'native readbacks omitted from a selected PR or merge group' in _readback_problems(jobs)
    elif mutation == 'failed-setup':
        step['if'] = step['if'].replace('{{', '{{ always() &&', 1)
        assert 'native readback can bypass failed setup' in _readback_problems(jobs)
    else:
        owner = job if mutation == 'job-admin-dsn' else step
        env_name = {'fixture': 'SUVARNA_PG_BIN', 'client': 'PATH'}.get(mutation, 'KALA_ADMIN_DSN')
        owner.setdefault('env', {})[env_name] = 'synthetic-override'
        assert 'native readback fixture or client binding overridden' in _readback_problems(jobs)


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
    command = next(shlex.split(line) for line in step['run'].replace('\\\n', '').splitlines() if 'ET.parse(' in line)
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
