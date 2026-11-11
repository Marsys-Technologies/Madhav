"""Regression oracle for mandatory lane selection, fixture and required-check wiring."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
SUITE = 'governance-tool-tests-lane'


def test_lane_profile_is_required_and_runs_on_its_guarded_endpoint():
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    job = jobs['governance-tool-tests-shard']
    steps = [s for s in job['steps'] if f'pytest {SUITE} --' in s.get('run', '')]
    assert len(steps) == 1, 'both lane modules need one mandatory discovery invocation'
    step = steps[0]
    assert step['if'] == 'matrix.shard == 1' and not step.get('continue-on-error', False)
    assert 1 in job['strategy']['matrix']['shard']
    assert not job.get('continue-on-error', False)
    assert 'governance-tool-tests-shard' in jobs['governance-tool-tests']['needs']
    assert 'SHARDS_RESULT' in jobs['governance-tool-tests']['steps'][0]['run']
    checkout = next(s for s in job['steps'] if s.get('uses', '').startswith('actions/checkout@'))
    depth = checkout['with']['fetch-depth']
    # Main gives shard 1 full history and keeps the others shallow: `matrix.shard != 1 && 1 || 0`. Evaluate it for the shard that
    # runs the lane step (`matrix.shard == 1`, asserted above); a literal 0 is also full history.
    if isinstance(depth, str):
        assert depth == '${{ matrix.shard != 1 && 1 || 0 }}', f'unrecognised fetch-depth expression {depth!r}'
        shard = 1
        depth = 1 if shard != 1 else 0
    assert depth == 0, 'real merged-base lookup needs origin/main history on the shard that runs the lane step'
    assert step['env']['KALA_REQUIRE_DB'] == '1'
    assert step['env']['GOCHARA_A53_REQUIRE_DB'] == '1'
    dsn = 'postgresql://postgres@127.0.0.1:55433/postgres'
    assert step['env']['KALA_ADMIN_DSN'] == dsn
    assert step['env']['GOCHARA_A53_ADMIN_DSN'] == dsn
    assert not job.get('services'), 'the strict observer requires a host loopback server, not a Docker proxy'
    assert '-p no:cacheprovider' in step['run']
    assert '--junitxml=' in step['run'] and 'skipped' in step['run'], 'required oracles cannot silently skip'
    spec = importlib.util.spec_from_file_location('approved_discovery', ROOT / 'platform/scripts/governance/ci_discovery.py')
    discovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(discovery)
    discovery.PROFILES = ROOT / 'platform/scripts/governance/ci_test_suites.json'
    profile = discovery.profiles()[SUITE]
    assert profile['cwd'] == '.' and profile['engine'] == 'pytest'
    selected = discovery.discover(ROOT, profile)
    assert '00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_lane_smalltest.py' in selected
    assert '00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_lane_smalltest_db.py' in selected


@pytest.mark.parametrize('body, expected', [
    ('<testcase />', 0),
    ('<testcase><skipped /></testcase>', 1),
    ('', 1),
])
def test_lane_ci_junit_gate_rejects_skipped_and_empty_runs(tmp_path, body, expected):
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    step = next(s for s in jobs['governance-tool-tests-shard']['steps']
                if f'pytest {SUITE} --' in s.get('run', ''))
    check = next(shlex.split(line) for line in step['run'].replace('\\\n', '').splitlines() if 'ET.parse(' in line)
    (tmp_path / 'lane-smalltest.xml').write_text('<testsuites><testsuite>' + body + '</testsuite></testsuites>')
    result = subprocess.run([sys.executable, *check[1:]], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == expected, result.stderr


NATIVE_PG_BIN = '/usr/lib/postgresql/16/bin'
LANE_PG_TOOLS = ('postgres', 'initdb', 'pg_ctl')
READBACK_PG_TOOLS = (*LANE_PG_TOOLS, 'psql')
READBACK_SUITE = 'governance-readback-tests-3-0'


@pytest.fixture
def pg_shell(tmp_path):
    """Run the checked-in shell with inert programs and a relocated native bindir."""
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    bin_dir = tmp_path / 'native-bin'
    bin_dir.mkdir()
    shim_dir = tmp_path / 'shims'
    shim_dir.mkdir()
    runner_temp = tmp_path / 'runner'
    runner_temp.mkdir()
    calls = tmp_path / 'calls.jsonl'
    fake = """#!PYTHON
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CI_PG_TEST_CALLS'], 'a') as log:
    log.write(json.dumps([name, args]) + '\\n')
failure = os.environ.get('CI_PG_TEST_FAILURE')
if name in ('sudo', 'apt-get'):
    sys.exit(91)
if args == ['--version']:
    release = '16.15'
    if name == os.environ['CI_PG_TEST_TARGET']:
        release = {'major': '17.8', 'mismatch': '16.14'}.get(failure, release)
    print(f'{name} (PostgreSQL) {release} (Ubuntu test fixture)')
    sys.exit(8 if name == os.environ['CI_PG_TEST_TARGET'] and failure == 'probe' else 0)
if name == 'initdb':
    if failure == 'initdb':
        sys.exit(9)
    pathlib.Path(args[args.index('-D') + 1]).mkdir()
elif name == 'pg_ctl':
    pid = pathlib.Path(args[args.index('-D') + 1]) / 'postmaster.pid'
    if args[-1] == 'start':
        if failure == 'start':
            sys.exit(10)
        pid.write_text('fixture stub, never a real process')
    else:
        pid.unlink()
elif name == 'python':
    if '-m' in args and failure == 'pip':
        sys.exit(11)
    if args and args[0] == '-c':
        os.execv(sys.executable, [sys.executable, *args])
    if 'pytest' in args and '-m' not in args:
        xml = next(arg.split('=', 1)[1] for arg in args if arg.startswith('--junitxml='))
        pathlib.Path(xml).write_text('<testsuites><testsuite><testcase /></testsuite></testsuites>')
        sys.exit(int(os.environ['CI_PG_TEST_CHILD_EXIT']))
elif name == 'pg_config':
    print(pathlib.Path(sys.argv[0]).parent)
""".replace('PYTHON', sys.executable, 1)
    for parent, tools in ((bin_dir, READBACK_PG_TOOLS), (shim_dir, (*READBACK_PG_TOOLS, 'python', 'pg_config', 'sudo', 'apt-get'))):
        for name in tools:
            path = parent / name
            path.write_text(fake)
            path.chmod(0o755)

    env = dict(PATH=str(shim_dir) + os.pathsep + os.environ['PATH'],
               RUNNER_TEMP=str(runner_temp), GITHUB_WORKSPACE=str(ROOT),
               GITHUB_ENV=str(tmp_path / 'github-env'), GITHUB_PATH=str(tmp_path / 'github-path'),
               CI_PG_TEST_CALLS=str(calls), CI_PG_TEST_CHILD_EXIT='0')

    def run(scope, failure='', child_exit=0):
        if scope == 'lane':
            steps = jobs['governance-tool-tests-shard']['steps']
            script = next(step['run'] for step in steps if f'pytest {SUITE} --' in step.get('run', ''))
        elif scope == 'readback-setup':
            steps = jobs['governance-readback-tests']['steps']
            script = next(step['run'] for step in steps if step.get('name') == 'Install pytest and disposable PostgreSQL server binaries')
        else:
            steps = jobs['governance-readback-tests']['steps']
            script = next(step['run'] for step in steps if f'pytest {READBACK_SUITE} --' in step.get('run', ''))
        if scope != 'readback-test':
            assert script.count(NATIVE_PG_BIN) == 1
            script = script.replace(NATIVE_PG_BIN, str(bin_dir))
        target = 'pg_ctl' if scope == 'lane' else 'psql'
        if failure in ('missing', 'path'):
            (bin_dir / target).unlink()
        if failure == 'path':
            (bin_dir / target).symlink_to(shim_dir / target)
        child_env = dict(env, CI_PG_TEST_FAILURE=failure, CI_PG_TEST_TARGET=target, CI_PG_TEST_CHILD_EXIT=str(child_exit))
        return subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                              cwd=tmp_path, env=child_env, capture_output=True, text=True)

    def recorded():
        return [json.loads(line) for line in calls.read_text().splitlines()]

    return run, recorded, env, bin_dir, runner_temp


@pytest.mark.parametrize('child_exit', [0, 7])
def test_lane_ci_cluster_lifecycle_owns_loopback_and_cleans_up(pg_shell, child_exit):
    run, recorded, _, _, runner_temp = pg_shell
    result = run('lane', child_exit=child_exit)
    assert result.returncode == child_exit, result.stdout + result.stderr
    calls = recorded()
    assert [name for name, args in calls if args == ['--version']] == list(LANE_PG_TOOLS)
    init = next(args for name, args in calls if name == 'initdb' and '-D' in args)
    assert init[init.index('-A') + 1] == 'trust' and init[init.index('-U') + 1] == 'postgres'
    # --no-locale alone leaves SQL_ASCII; retain UTF8 for migration SQL (CI run 39383161799).
    assert '--encoding=UTF8' in init
    controls = [args for name, args in calls if name == 'pg_ctl' and '-D' in args]
    assert len(controls) == 2 and controls[0][-1] == 'start' and controls[1][-1] == 'stop'
    assert controls[0][controls[0].index('-o') + 1].startswith('-h 127.0.0.1 -p 55433 -k ')
    data = Path(init[init.index('-D') + 1])
    assert data.parent.parent == runner_temp
    assert all(args[args.index('-D') + 1] == str(data) for args in controls)
    assert any(name == 'python' and SUITE in args for name, args in calls)
    assert not list(runner_temp.iterdir()), 'the EXIT trap must clean up on pass and failure'


@pytest.mark.parametrize('scope', ['lane', 'readback-setup'])
@pytest.mark.parametrize(('failure', 'diagnostic'), [
    ('missing', 'Missing or unexpected native PostgreSQL 16 executable'),
    ('path', 'Missing or unexpected native PostgreSQL 16 executable'),
    ('major', 'Cannot verify native PostgreSQL 16 version'),
    ('mismatch', 'Mismatched native PostgreSQL releases'),
    ('probe', 'Cannot verify native PostgreSQL 16 version'),
    ('pip', ''),
])
def test_ci_pg_bootstrap_refuses_bad_setup(pg_shell, scope, failure, diagnostic):
    run, recorded, env, _, runner_temp = pg_shell
    result = run(scope, failure=failure)
    assert result.returncode == (11 if failure == 'pip' else 1), result.stdout + result.stderr
    assert diagnostic in result.stdout
    assert all(args == ['--version'] or (failure == 'pip' and args[:3] == ['-m', 'pip', 'install'])
               for _, args in recorded())
    assert not Path(env['GITHUB_ENV']).exists() and not Path(env['GITHUB_PATH']).exists()
    assert not list(runner_temp.iterdir())


@pytest.mark.parametrize(('failure', 'status'), [('initdb', 9), ('start', 10)])
def test_lane_ci_pg_start_failure_stops_before_pytest(pg_shell, failure, status):
    run, recorded, _, _, runner_temp = pg_shell
    result = run('lane', failure=failure)
    assert result.returncode == status, result.stdout + result.stderr
    assert not any('pytest' in args for _, args in recorded())
    assert not list(runner_temp.iterdir())


def test_readback_ci_binds_native_fixture_and_cli_before_unchanged_tests(pg_shell, monkeypatch):
    run, recorded, env, bin_dir, _ = pg_shell
    result = run('readback-setup')
    assert result.returncode == 0, result.stdout + result.stderr
    assert [name for name, args in recorded() if args == ['--version']] == list(READBACK_PG_TOOLS)
    assert Path(env['GITHUB_ENV']).read_text() == f'SUVARNA_PG_BIN={bin_dir}\n'
    assert Path(env['GITHUB_PATH']).read_text() == f'{bin_dir}\n'

    # Apply exactly the runner's setup outputs and exercise the helper's real resolution.
    name, value = Path(env['GITHUB_ENV']).read_text().strip().split('=', 1)
    env[name] = value
    env['PATH'] = Path(env['GITHUB_PATH']).read_text().strip() + os.pathsep + env['PATH']
    for name in ('SUVARNA_PG_BIN', 'PATH', 'CI_PG_TEST_CALLS'):
        monkeypatch.setenv(name, env[name])
    spec = importlib.util.spec_from_file_location('ci_disposable_pg', Path(__file__).with_name('_disposable_pg.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.find_bin_dir() == bin_dir
    assert subprocess.run(['bash', '-c', 'command -v psql'], env=env, check=True, capture_output=True,
                          text=True).stdout.strip() == str(bin_dir / 'psql')

    result = run('readback-test')
    assert result.returncode == 0, result.stdout + result.stderr
    assert any(name == 'python' and READBACK_SUITE in args for name, args in recorded())
