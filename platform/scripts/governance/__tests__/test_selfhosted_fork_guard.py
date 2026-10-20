"""SR-SELFHOSTED-SPLIT item 3: no fork-reachable job may be able to land on a self-hosted runner, and no job that can run
self-hosted may mount a host path. Each test plants ONE reversion in a copy of a workflow (never in the repo) and expects the
check to FAIL it; the live-repo tests pin the shape ci.yml actually ships.

Authority for the rules: OWNER-SELFHOSTED-SPLIT-20261018 / SR-SELFHOSTED-SPLIT (items 2-4) -- fork PRs run the fork author's code;
only the exact fork fence keeps them on GitHub-hosted runners; `pull_request_target` never goes on a self-hosted label; no host-path mounts.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'platform/scripts/governance/check_selfhosted_fork_guard.py'
_spec = importlib.util.spec_from_file_location('check_selfhosted_fork_guard', SCRIPT)
guard = importlib.util.module_from_spec(_spec)
sys.modules['check_selfhosted_fork_guard'] = guard
_spec.loader.exec_module(guard)

FENCE = guard.FORK_FENCE
FENCED_RUNS_ON = "${{ (" + FENCE + ") && fromJSON(needs.probe.outputs.runs_on || '\"ubuntu-latest\"') || 'ubuntu-latest' }}"

# The DB-heavy jobs OWNER-SELFHOSTED-SPLIT-20261018 routes to madhav-db (SR-SELFHOSTED-SPLIT item 2): Kala DB Tests, the DB Integration
# shards and the Gochara A5.5f / C37 / C38 DB jobs. Nothing else in ci.yml may be able to run self-hosted.
DB_HEAVY_JOBS = {
    'kala-db-tests', 'db-integration-tests', 'gochara-a55-replace-chain', 'gochara-a55-slice-transitions',
    'gochara-a55-teardown', 'gochara-a55-teardown-round2', 'gochara-a55-teardown-round3', 'gochara-a55-dispatch',
    'gochara-a55-round2-runner', 'gochara-a55-verifier-fixes',
}
# Branch protection on main (00_ARCHITECTURE/ci_campaign_prompts/CI_RULESET_MIGRATION_PROMPT.md, "names must be byte-identical").
REQUIRED_CHECK_NAMES = {
    'TypeScript (src only)', 'Unit Tests', 'Secret Scan (unit 0b.2)',
    'Governance Gates (drift / schema / edge / native-literal / py-sidecar)',
}


def workflow(on: str, runs_on: str, extra_job: str = '', job_if: str | None = None) -> dict:
    """A one-job workflow document; `on` and `runs_on` are YAML fragments."""
    cond = f'\n    if: {job_if}' if job_if else ''
    text = f"name: planted\non:\n{textwrap.indent(on, '  ')}\njobs:\n  db:\n    runs-on: {runs_on}{cond}\n{extra_job}    steps:\n      - run: echo hi\n"
    return yaml.safe_load(text)


def codes(doc) -> set[str]:
    return {v['code'] for v in guard.check_document('planted.yml', doc)}


def test_the_repository_workflows_pass_the_guard():
    assert guard.check_directory(ROOT / '.github/workflows') == []


# -- claim: a self-hosted label on a fork-reachable job fails ---------------------------------------------------------------------
@pytest.mark.parametrize('runs_on', ['[self-hosted, madhav-db]', 'madhav-db', "${{ fromJSON(needs.probe.outputs.runs_on) }}",
                                     "${{ matrix.runner }}"])
def test_planted_self_hosted_or_dynamic_runner_on_a_pull_request_workflow_fails(runs_on):
    assert codes(workflow('pull_request:\n', runs_on)) == {'SELFHOSTED_UNFENCED'}


def test_a_runner_group_on_a_pull_request_workflow_fails():
    doc = yaml.safe_load("on: pull_request\njobs:\n  j:\n    runs-on:\n      group: lanes\n    steps: []\n")
    assert codes(doc) == {'SELFHOSTED_UNFENCED'}


def test_the_ci_yml_fence_shape_passes_and_the_job_if_fence_passes():
    assert codes(workflow('pull_request:\npush:\n', FENCED_RUNS_ON)) == set()
    cond = "${{ !cancelled() && (" + FENCE + ") && needs.changes.outputs.x == 'y' }}"
    assert codes(workflow('pull_request:\n', '[self-hosted, madhav-db]', job_if=f'"{cond}"')) == set()


# -- claim: the fence must be the exact fence, evaluated first, with no unfenced branch -------------------------------------------
@pytest.mark.parametrize('runs_on', [
    # fence compares with == instead of != (inverted: only fork PRs would get the label)
    "${{ (github.event_name == 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository) && "
    "fromJSON(needs.p.outputs.r) || 'ubuntu-latest' }}",
    # the fence does not guard the dynamic value: it is only one OR-branch
    "${{ fromJSON(needs.p.outputs.r) || (" + FENCE + ") && 'ubuntu-latest' }}",
    # an extra top-level `||` adds a branch the fence does not cover
    "${{ (" + FENCE + ") && 'ubuntu-latest' || fromJSON(needs.p.outputs.r) || 'ubuntu-latest' }}",
    # the fallback is not a GitHub-hosted literal
    "${{ (" + FENCE + ") && 'ubuntu-latest' || 'madhav-db' }}",
    # head repo compared with something other than github.repository
    "${{ (github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == 'x/y') && "
    "fromJSON(needs.p.outputs.r) || 'ubuntu-latest' }}",
])
def test_planted_weakened_fence_fails(runs_on):
    assert codes(workflow('pull_request:\n', runs_on)) == {'SELFHOSTED_UNFENCED'}


def test_a_job_if_that_offers_the_fence_only_as_one_or_branch_fails():
    cond = "${{ (" + FENCE + ") || github.event_name == 'workflow_dispatch' }}"
    assert codes(workflow('pull_request:\n', '[self-hosted]', job_if=f'"{cond}"')) == {'SELFHOSTED_UNFENCED'}


# -- claim: never pull_request_target (or any trigger the fence cannot protect) on a self-hosted label ------------------------------
@pytest.mark.parametrize('on', ['pull_request_target:\n', 'workflow_run:\n  workflows: [CI]\n', 'issue_comment:\n',
                                'pull_request:\nworkflow_call:\n'])
def test_planted_unfenceable_trigger_fails_even_with_the_fence(on):
    assert codes(workflow(on, FENCED_RUNS_ON)) == {'SELFHOSTED_UNFENCEABLE'}


def test_self_hosted_on_triggers_that_only_fire_for_this_repository_is_allowed():
    assert codes(workflow('push:\nmerge_group:\nschedule:\n  - cron: "0 1 * * *"\nworkflow_dispatch:\n', '[self-hosted, madhav-db]')) == set()


def test_github_hosted_runners_are_never_flagged_whatever_the_trigger():
    assert codes(workflow('pull_request_target:\n', 'ubuntu-latest')) == set()
    assert codes(workflow('pull_request:\n', '[ubuntu-24.04, ubuntu-latest]')) == set()


# -- claim: a job that can run self-hosted must not mount a host path --------------------------------------------------------------
@pytest.mark.parametrize('extra', [
    "    services:\n      pg:\n        image: postgres:16\n        volumes:\n          - /var/run/postgresql:/var/run/postgresql\n",
    "    container:\n      image: x\n      volumes:\n        - /Users/Dev:/work\n",
    "    container:\n      image: x\n      volumes:\n        - ./data:/data\n",
    "    services:\n      pg:\n        image: postgres:16\n        options: -v /var/run/docker.sock:/var/run/docker.sock\n",
    "    services:\n      pg:\n        image: postgres:16\n        options: --mount type=bind,source=/tmp,target=/t\n",
])
def test_planted_host_mount_on_a_self_hosted_job_fails(extra):
    assert codes(workflow('push:\n', '[self-hosted, madhav-db]', extra_job=extra)) == {'HOST_MOUNT'}


def test_planted_docker_run_with_host_volume_in_a_step_fails():
    doc = yaml.safe_load("on: push\njobs:\n  j:\n    runs-on: [self-hosted]\n    steps:\n"
                         "      - name: x\n        run: |\n          docker run --rm \\\n            -v $HOME/.ssh:/root/.ssh img\n")
    assert codes(doc) == {'HOST_MOUNT'}


def test_named_volumes_psql_dash_v_and_hosted_jobs_are_not_host_mounts():
    named = "    services:\n      pg:\n        image: postgres:16\n        volumes:\n          - pgdata:/var/lib/postgresql/data\n"
    assert codes(workflow('push:\n', '[self-hosted, madhav-db]', extra_job=named)) == set()
    doc = yaml.safe_load("on: push\njobs:\n  j:\n    runs-on: [self-hosted]\n    steps:\n"
                         "      - run: psql -h localhost -v ON_ERROR_STOP=1 -c 'select 1'\n      - run: pytest -v --tb=short\n")
    assert codes(doc) == set()
    hosted = "    services:\n      pg:\n        image: postgres:16\n        volumes:\n          - /var/run/postgresql:/var/run/postgresql\n"
    assert codes(workflow('pull_request:\n', 'ubuntu-latest', extra_job=hosted)) == set()


# -- the command line: exit status is what CI reads -------------------------------------------------------------------------------
def test_cli_exits_one_on_a_planted_fork_reachable_self_hosted_job_and_zero_on_the_repository(tmp_path):
    planted = tmp_path / 'wf'
    planted.mkdir()
    (planted / 'bad.yml').write_text('on: pull_request\njobs:\n  j:\n    runs-on: [self-hosted, madhav-db]\n    steps: []\n')
    bad = subprocess.run([sys.executable, '-I', str(SCRIPT), '--workflows', str(planted), '--json'], capture_output=True, text=True, timeout=60)
    assert bad.returncode == 1 and json.loads(bad.stdout)[0]['code'] == 'SELFHOSTED_UNFENCED'
    good = subprocess.run([sys.executable, '-I', str(SCRIPT)], capture_output=True, text=True, timeout=60)
    assert good.returncode == 0, good.stdout
    assert subprocess.run([sys.executable, '-I', str(SCRIPT), '--workflows', str(tmp_path / 'nope')], capture_output=True, timeout=60).returncode == 2


def test_an_unparseable_workflow_fails_closed(tmp_path):
    (tmp_path / 'broken.yml').write_text('on: [pull_request\njobs: {')
    assert {v['code'] for v in guard.check_directory(tmp_path)} == {'UNPARSEABLE'}


# -- claim: ci.yml routes exactly the named DB-heavy jobs and renames no required check --------------------------------------------
def _ci():
    return yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8'))


def test_only_the_named_db_heavy_jobs_can_run_self_hosted_and_each_keeps_a_probe_dependency_and_cancelled_guard():
    jobs = _ci()['jobs']
    movable = {k for k, j in jobs.items() if not guard.provably_hosted(j['runs-on'])}
    assert movable == DB_HEAVY_JOBS
    for key in movable:
        assert guard.runs_on_is_fenced(jobs[key]['runs-on']), key
        assert 'db-runner-probe' in jobs[key]['needs'], key
        # `!cancelled()` keeps the job running (on its ubuntu-latest fallback) even if the probe is skipped or errors.
        assert '!cancelled()' in jobs[key]['if'], key
        assert jobs[key]['services']['postgres']['image'].startswith('mirror.gcr.io/library/postgres:'), key


def test_required_checks_keep_their_names_and_stay_on_github_hosted_runners():
    jobs = _ci()['jobs']
    by_name = {j.get('name'): j for j in jobs.values()}
    for name in REQUIRED_CHECK_NAMES:
        assert name in by_name, f'required check {name!r} no longer has a job'
        assert guard.provably_hosted(by_name[name]['runs-on']), name
    # every "required-*" umbrella that stands in for a moved shard job stays hosted and keeps its (unsharded) name
    for key, job in jobs.items():
        if key.startswith('required-'):
            assert guard.provably_hosted(job['runs-on']), key
            assert '${{' not in job['name'], key


def test_the_probe_job_is_github_hosted_and_never_fails_the_pipeline():
    probe = _ci()['jobs']['db-runner-probe']
    assert guard.provably_hosted(probe['runs-on'])
    assert 'needs' not in probe and 'if' not in probe
    script = probe['steps'][0]['run']
    # the fallback answer is ubuntu-latest, and the only way out of the script is `exit 0` through choose()
    assert "fallback='\"ubuntu-latest\"'" in script and 'exit 1' not in script


def test_the_probe_uses_no_secret_and_no_runner_api_call():
    """SR-RUNNER-PROBE-NOSECRET: the heartbeat is a repository variable; no token, no `gh api` runners call."""
    text = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert 'MADHAV_RUNNER_PROBE_TOKEN' not in text
    probe = _ci()['jobs']['db-runner-probe']
    step = probe['steps'][0]
    assert 'secrets.' not in json.dumps(probe) and 'GH_TOKEN' not in step.get('env', {})
    assert 'gh api' not in step['run'] and 'actions/runners' not in step['run']
    assert step['env']['HEARTBEAT'] == '${{ vars.MADHAV_DB_ONLINE }}'
    assert step['env']['DB_ENABLED'] == '${{ vars.MADHAV_DB_ENABLED }}'


# -- claim: DB jobs route to madhav-db only on a fresh, parseable heartbeat (<= 180 s old, <= 60 s in the future) ---------------------
SELF_HOSTED = '["self-hosted","madhav-db"]'
UBUNTU = '"ubuntu-latest"'


def _iso(offset_seconds: float) -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + offset_seconds))


def _run_probe(tmp_path, heartbeat, db_enabled=None) -> str:
    """Run the ci.yml probe step's own script under bash with the step's env; return the published runs_on value."""
    script = _ci()['jobs']['db-runner-probe']['steps'][0]['run']
    out = tmp_path / 'github_output'
    out.write_text('')
    env = {'PATH': os.environ['PATH'], 'GITHUB_OUTPUT': str(out)}
    if heartbeat is not None:
        env['HEARTBEAT'] = heartbeat
    if db_enabled is not None:
        env['DB_ENABLED'] = db_enabled
    done = subprocess.run(['bash', '-c', script], env=env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    lines = [l for l in out.read_text().splitlines() if l.startswith('runs_on=')]
    assert len(lines) == 1, lines
    return lines[0].split('=', 1)[1]


@pytest.mark.parametrize('offset', [0, -10, -170, 30])
def test_a_fresh_heartbeat_routes_the_db_jobs_to_madhav_db(tmp_path, offset):
    assert _run_probe(tmp_path, _iso(offset)) == SELF_HOSTED


@pytest.mark.parametrize('offset', [-200, -400, -86400])
def test_planted_stale_heartbeat_routes_to_ubuntu_latest(tmp_path, offset):
    assert _run_probe(tmp_path, _iso(offset)) == UBUNTU


@pytest.mark.parametrize('offset', [120, 3600])
def test_planted_future_dated_heartbeat_beyond_skew_routes_to_ubuntu_latest(tmp_path, offset):
    assert _run_probe(tmp_path, _iso(offset)) == UBUNTU


@pytest.mark.parametrize('heartbeat', [
    None, '', 'yesterday', '1792425600', '2026-13-45T99:99:99Z', '2026-02-30T10:00:00Z',
    '2026-10-19 16:00:00', '2026-10-19T16:00:00+00:00', '2026-10-19T16:00:00',
])
def test_missing_or_unparsable_heartbeat_routes_to_ubuntu_latest(tmp_path, heartbeat):
    assert _run_probe(tmp_path, heartbeat) == UBUNTU


def test_the_kill_switch_beats_a_fresh_heartbeat_and_only_the_word_false_trips_it(tmp_path):
    assert _run_probe(tmp_path, _iso(0), db_enabled='false') == UBUNTU
    assert _run_probe(tmp_path, _iso(0), db_enabled='true') == SELF_HOSTED
    assert _run_probe(tmp_path, _iso(0), db_enabled='') == SELF_HOSTED


def test_the_guard_is_selected_by_its_ci_profile_and_by_governance_shard_discovery():
    for name in ('ci_discovery', 'ci_shard'):
        spec = importlib.util.spec_from_file_location(name, ROOT / f'platform/scripts/governance/{name}.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if name == 'ci_discovery':
            assert str(Path(__file__).relative_to(ROOT)) in mod.discover(ROOT, mod.profiles()['selfhosted-fork-guard-tests'])
        else:
            assert Path(__file__) in mod.test_files()
