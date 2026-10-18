"""Regression oracle for mandatory lane selection, fixture and required-check wiring."""
import importlib.util
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
    check = next(shlex.split(line) for line in step['run'].splitlines() if 'ET.parse(' in line)
    (tmp_path / 'lane-smalltest.xml').write_text('<testsuites><testsuite>' + body + '</testsuite></testsuites>')
    result = subprocess.run([sys.executable, *check[1:]], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == expected, result.stderr


@pytest.mark.parametrize('child_exit', [0, 7])
def test_lane_ci_cluster_lifecycle_owns_loopback_and_cleans_up(tmp_path, child_exit):
    """Execute the actual CI shell with fake programs; never start a local cluster."""
    import json
    import os
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    step = next(s for s in jobs['governance-tool-tests-shard']['steps']
                if f'pytest {SUITE} --' in s.get('run', ''))
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    runner_temp = tmp_path / 'runner'
    runner_temp.mkdir()
    calls = tmp_path / 'calls.jsonl'
    fake = '''#!PYTHON
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['LANE_TEST_CALLS'], 'a') as log:
    log.write(json.dumps([name, args]) + '\\n')
if name == 'ls':
    print(pathlib.Path(sys.argv[0]).parent)
elif name == 'initdb':
    pathlib.Path(args[args.index('-D') + 1]).mkdir()
elif name == 'pg_ctl':
    pid = pathlib.Path(args[args.index('-D') + 1]) / 'postmaster.pid'
    if args[-1] == 'start': pid.write_text('fixture stub, never a real process')
    else: pid.unlink()
elif name == 'python' and 'pytest' in args:
    pathlib.Path('lane-smalltest.xml').write_text('<testsuites><testsuite><testcase /></testsuite></testsuites>')
    sys.exit(int(os.environ['LANE_TEST_CHILD_EXIT']))
'''.replace('PYTHON', sys.executable, 1)
    for name in ('sudo', 'ls', 'initdb', 'pg_ctl', 'python'):
        path = fake_bin / name
        path.write_text(fake)
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ['PATH'],
               RUNNER_TEMP=str(runner_temp), GITHUB_WORKSPACE=str(ROOT),
               LANE_TEST_CALLS=str(calls), LANE_TEST_CHILD_EXIT=str(child_exit))
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', step['run']],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == child_exit, result.stdout + result.stderr
    recorded = [json.loads(line) for line in calls.read_text().splitlines()]
    init = next(args for name, args in recorded if name == 'initdb')
    assert init[init.index('-A') + 1] == 'trust' and init[init.index('-U') + 1] == 'postgres'
    controls = [args for name, args in recorded if name == 'pg_ctl']
    assert len(controls) == 2 and controls[0][-1] == 'start' and controls[1][-1] == 'stop'
    assert controls[0][controls[0].index('-o') + 1].startswith('-h 127.0.0.1 -p 55433 -k ')
    data = Path(init[init.index('-D') + 1])
    assert data.parent.parent == runner_temp
    assert all(args[args.index('-D') + 1] == str(data) for args in controls)
    assert not list(runner_temp.iterdir()), 'the EXIT trap must clean up on pass and failure'
