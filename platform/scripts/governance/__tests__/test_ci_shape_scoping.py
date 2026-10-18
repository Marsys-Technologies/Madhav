"""SR-BOLD-08(a) CI shape: path-scoped PR runs; combination-sensitive suites are merge_group-only; required names still report.

Oracles are the owner rulings SR-BOLD-08 / SR-CI-SCOPED-SAFEGUARD (DECISIONS_SURROGATE.jsonl, 2026-10-17/18) and the
CI event contract in ci.yml, not astrological claims (D-OWNER-TESTS-20261016). One test per distinct production claim:

  1. a PR defers DB Integration Tests (even when its diff touches their tests) while every other DB profile stays path-scoped;
  2. a PR that changes the scoping itself, and every non-PR event, runs the whole family (the scoper cannot vouch for itself);
  3. the Governance Tool Tests shards run on queue/main/dispatch, are skipped on a deferring PR, and fail closed;
  4. the Governance Tool Tests required check reports "not applicable" only with the scoping proof (N.8: a skip that can read false);
  5. the DB Integration Tests required check reports on every event and passes a skip only with the same proof;
  6. no required context disappears and `Full suite event contract` still runs on every event.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from _ci_gate_test_support import evaluate

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
CI = ROOT / '.github/workflows/ci.yml'
# Contexts that must keep reporting on every PR: the 11 pinned in test_ci_light_gate.REQUIRED plus the ones this item touches.
TOUCHED = ('DB Integration Tests (SAMĪKṢĀ, throwaway Postgres)', 'Governance Tool Tests (pytest)', 'Full suite event contract',
           'Governance Gates (drift / schema / edge / native-literal / py-sidecar)')


def jobs():
    return yaml.safe_load(CI.read_text())['jobs']


def _gate(monkeypatch, capsys, event, changed):
    import ci_changes
    import ci_gate
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: changed)
    assert ci_gate.main(['--event', event, '--base', 'B', '--head', 'H']) == 0
    return dict(line.split('=', 1) for line in capsys.readouterr().out.splitlines())


def _samiksha_test_path():
    """A real test file that only the SAMIKSHA DB Integration job owns, found by discovery (no committed list)."""
    import ci_discovery
    import ci_gate
    specs = ci_discovery.profiles()
    for profile, owners in sorted(ci_gate.db_profile_owners(jobs()).items()):
        if owners != ['db-integration-tests']:
            continue
        spec = specs[profile]
        for rel in ci_discovery.discover(ROOT, spec):
            path = (Path(spec['cwd']) / rel).as_posix()
            if (ROOT / path).is_file() and ci_gate._test_file(path, spec['engine']):
                return path
    raise AssertionError('no SAMIKSHA-only test file discovered')


def test_pull_request_defers_db_integration_but_other_db_profiles_stay_path_scoped(monkeypatch, capsys):
    """Claim 1 (SR-BOLD-08a + SR-CI-SCOPED-SAFEGUARD: DB Integration shards are merge_group-only; everything else path-scoped)."""
    samiksha = _samiksha_test_path()
    replace_chain = 'platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py'
    pr = _gate(monkeypatch, capsys, 'pull_request', [samiksha, replace_chain])
    mg = _gate(monkeypatch, capsys, 'merge_group', [samiksha, replace_chain])
    assert 'db-integration-tests' not in json.loads(pr['db_jobs']), 'a PR must not run DB Integration Tests'
    assert not [p for p in json.loads(pr['db_profiles']) if p.startswith('db-integration-tests')]
    assert 'gochara-a55-replace-chain' in json.loads(pr['db_jobs']), 'every other DB job stays path-scoped on a PR'
    assert 'db-integration-tests' in json.loads(mg['db_jobs']), 'the queue runs DB Integration Tests'
    assert pr['run_combination_suites'] == 'false' and mg['run_combination_suites'] == 'true'


@pytest.mark.parametrize('scoper', ['.github/workflows/ci.yml', 'platform/scripts/governance/ci_gate.py',
                                    'platform/scripts/governance/ci_test_suites.json'])
def test_a_pr_that_changes_the_scoping_runs_the_whole_family_and_other_events_always_do(monkeypatch, capsys, scoper):
    """Claim 2: the scoper cannot vouch for a change to itself; push/dispatch/queue never defer."""
    samiksha = _samiksha_test_path()
    pr = _gate(monkeypatch, capsys, 'pull_request', [scoper, samiksha])
    assert pr['run_combination_suites'] == 'true'
    assert 'db-integration-tests' in json.loads(pr['db_jobs']), 'changed-profile selection is restored for a scoper-touching PR'
    plain = _gate(monkeypatch, capsys, 'pull_request', ['platform/src/app/page.tsx'])
    assert plain['run_combination_suites'] == 'false'
    for event in ('merge_group', 'push', 'workflow_dispatch'):
        assert _gate(monkeypatch, capsys, event, ['platform/src/app/page.tsx'])['run_combination_suites'] == 'true', event


def test_governance_tool_test_shards_are_merge_group_only_and_fail_closed():
    """Claim 3: shards run on queue/main/dispatch, skip on a deferring PR, run when the deferral is unproven or the PR is scoper-touching."""
    shard = jobs()['governance-tool-tests-shard']['if']
    for event, full in (('merge_group', False), ('push', False), ('workflow_dispatch', True)):
        assert evaluate(shard, event=event, full=full, combination='true'), event
    assert not evaluate(shard, event='pull_request', combination='false')
    assert evaluate(shard, event='pull_request', combination='true'), 'scoper-touching PR runs the shards'
    assert evaluate(shard, event='pull_request', combination=''), 'a failed `changes` (empty output) must not defer'
    assert not evaluate(shard, event='pull_request', combination='true', docs='true'), 'docs-only skip is unchanged'
    changes = jobs()['changes']
    assert changes['outputs']['run_combination_suites'] == '${{ steps.select-db.outputs.run_combination_suites }}'


def _run(step, **env):
    base = {k: v for k, v in os.environ.items() if k not in ('GITHUB_STEP_SUMMARY',)}
    p = subprocess.run(['bash', '-e', '-c', step['run']], env={**base, 'GITHUB_STEP_SUMMARY': os.devnull, **env},
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


GOV = dict(EVENT_NAME='pull_request', READBACK_EXPECTED='false', SHARDS_RESULT='skipped', READBACK_RESULT='skipped',
           DOCS_ONLY='false', RUN_COMBINATION='false', CHANGES_RESULT='success')


@pytest.mark.parametrize('override,passes', [
    ({}, True),                                                                  # PR, deferral proven
    ({'DOCS_ONLY': 'true', 'RUN_COMBINATION': 'true'}, True),                    # docs-only PR (pre-existing proof)
    ({'RUN_COMBINATION': 'true'}, False),                                        # shards should have run and did not
    ({'RUN_COMBINATION': ''}, False),                                            # `changes` produced no proof
    ({'CHANGES_RESULT': 'failure'}, False),                                      # classifier failed
    ({'EVENT_NAME': 'merge_group'}, False),                                      # the queue may never skip the shards
    ({'EVENT_NAME': 'push'}, False),
    ({'SHARDS_RESULT': 'failure'}, False),
    ({'SHARDS_RESULT': 'cancelled'}, False),
    ({'SHARDS_RESULT': 'success'}, True),
])
def test_governance_tool_tests_check_reports_not_applicable_only_with_the_scoping_proof(override, passes):
    """Claim 4 (N.8): the skip is accepted only by a detector that can read false."""
    step = jobs()['governance-tool-tests']['steps'][0]
    code, out = _run(step, **{**GOV, **override})
    assert (code == 0) is passes, out


DB = dict(EVENT_NAME='pull_request', REF='refs/pull/1/merge', FULL_GATE='', DB_JOBS='[]', RUN_COMBINATION='false',
          CHANGES_RESULT='success', SHARDS_RESULT='skipped')


@pytest.mark.parametrize('override,passes', [
    ({}, True),                                                                  # PR: deferred, proven
    ({'RUN_COMBINATION': 'true'}, True),                                         # scoper PR, no SAMIKSHA test changed: path-scoped skip
    ({'CHANGES_RESULT': 'failure'}, False),                                      # no scoping proof
    ({'CHANGES_RESULT': 'cancelled'}, False),
    ({'EVENT_NAME': 'merge_group', 'DB_JOBS': '["db-integration-tests"]', 'SHARDS_RESULT': 'skipped'}, False),
    ({'EVENT_NAME': 'merge_group', 'DB_JOBS': '["db-integration-tests"]', 'SHARDS_RESULT': 'success', 'RUN_COMBINATION': 'true'}, True),
    ({'EVENT_NAME': 'merge_group', 'DB_JOBS': '["db-integration-tests"]', 'SHARDS_RESULT': 'failure', 'RUN_COMBINATION': 'true'}, False),
    ({'EVENT_NAME': 'merge_group', 'DB_JOBS': '[]', 'SHARDS_RESULT': 'skipped', 'RUN_COMBINATION': 'true'}, False),  # queue never skips
    ({'EVENT_NAME': 'push', 'REF': 'refs/heads/main', 'SHARDS_RESULT': 'skipped', 'RUN_COMBINATION': 'true'}, False),
    ({'EVENT_NAME': 'push', 'REF': 'refs/heads/main', 'SHARDS_RESULT': 'success', 'RUN_COMBINATION': 'true'}, True),
    ({'EVENT_NAME': 'workflow_dispatch', 'FULL_GATE': 'true', 'SHARDS_RESULT': 'failure', 'RUN_COMBINATION': 'true'}, False),
    ({'EVENT_NAME': 'pull_request', 'DB_JOBS': '["db-integration-tests"]', 'SHARDS_RESULT': 'failure', 'RUN_COMBINATION': 'true'}, False),
    ({'EVENT_NAME': 'pull_request', 'SHARDS_RESULT': 'failure'}, False),         # a shard that ran and failed is never "not applicable"
])
def test_db_integration_check_reports_on_every_event_and_passes_a_skip_only_with_proof(override, passes):
    """Claim 5: the required context is no longer skipped away on a PR; it reports a verdict it earned."""
    umbrella = jobs()['required-db-integration-tests']
    assert evaluate(umbrella['if'], event=override.get('EVENT_NAME', 'pull_request')), 'must report on every event'
    code, out = _run(umbrella['steps'][0], **{**DB, **override})
    assert (code == 0) is passes, out


def test_every_required_context_still_reports_and_the_event_contract_runs_on_every_event():
    """Claim 6: before/after job-name set loses nothing; the PR-skip detector (`Full suite event contract`) runs on PR and queue."""
    now = {j.get('name') for j in jobs().values()}
    for context in TOUCHED:
        assert context in now, f'{context!r} disappeared'
    pinned = json.loads((ROOT / 'platform/scripts/governance/ci_discovery_baseline.json').read_text())['job_names']
    assert set(pinned.values()) <= now
    for event in ('pull_request', 'merge_group', 'push'):
        assert evaluate(jobs()['full-suite']['if'], event=event), event
        assert evaluate(jobs()['governance-tool-tests']['if'], event=event), event
        assert evaluate(jobs()['required-db-integration-tests']['if'], event=event), event
    needs = set(jobs()['full-suite']['needs'])
    assert {'db-integration-tests', 'required-db-integration-tests', 'governance-readback-tests'} <= needs
