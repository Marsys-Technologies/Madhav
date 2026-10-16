"""D-OWNER-TESTS-20261016 / CI demand halving (madhav-6d, D-29).

The oracles are CI event/fixture contracts from the job brief (a)-(e), not
astrological claims; no chart output is captured as an expected result.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from _ci_gate_test_support import evaluate

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
CI = ROOT / '.github/workflows/ci.yml'
REQUIRED = {
    'TypeScript (src only)', 'Unit Tests', 'Secret Scan (unit 0b.2)',
    'Governance Gates (drift / schema / edge / native-literal / py-sidecar)',
    'Governance Tool Tests (pytest)',
    'DB Integration Tests (SAMĪKṢĀ, throwaway Postgres)',
    'Gochara A5.5f - a rebuild replaces the whole candidate chain (real writer, throwaway Postgres)',
    'Gochara C38 - the small-test teardown (real writer, throwaway Postgres)',
    'Gochara C38 - the small-test teardown, round 3 (real catalog foreign keys, lock race, interrupted replacement) (real writer, throwaway Postgres)',
    'Gochara A5.5f - test-slice round 2 and the real runner (real writer, throwaway Postgres)',
    'Gochara A5.5f - verifier fixes (P1 exclusion, member geometry, graze interim) (real writer, throwaway Postgres)',
}


def workflow():
    return yaml.safe_load(CI.read_text())


def db_jobs(jobs):
    return {name for name, job in jobs.items() if job.get('services')} | {'governance-readback-tests'}


def heavy_jobs(jobs):
    return db_jobs(jobs) | {'governance-gates-py-sidecar-shard', 'governance-gates-gochara'} | {n for n in jobs if n.startswith('required-')}


def test_pull_request_has_light_checks_and_skips_unrelated_heavy_jobs():
    """Brief (a,b): ordinary code PR pays only the light gate, all required names report."""
    jobs = workflow()['jobs']
    names = {j.get('name') for j in jobs.values()}
    assert REQUIRED <= names
    historical = json.loads((ROOT / 'platform/scripts/governance/ci_discovery_baseline.json').read_text())
    assert set(historical['job_names'].values()) <= names, 'every original context, including any protected name, must report'
    for name in heavy_jobs(jobs):
        assert not evaluate(jobs[name].get('if'), event='pull_request'), name
    for name in ('typecheck', 'typecheck-mcp', 'unit-tests', 'generated-artifacts', 'secret-scan',
                 'naming-lint', 'fact-category-pin-lint', 'earned-signal-lint', 'governance-tool-tests-shard'):
        assert evaluate(jobs[name].get('if'), event='pull_request'), name
    assert 'services' not in jobs['unit-tests'], 'the light Unit Tests check must not start Postgres'
    assert 'ci_discovery.py guard' in str(jobs['generated-artifacts']['steps'])
    # Other workflows' possibly protected names stay present for both queue and PR.
    for file, key, name in (
        ('tap-ci.yml', 'tap6-method-audit', 'TAP-6 — Method audit grep set'),
        ('ekv-lints.yml', 'ekv-d01c-no-local-ayanamsha-map', 'D-01c — No Local Ayanamsha Map (WARN)'),
    ):
        external = yaml.safe_load((CI.parent / file).read_text())
        assert external['jobs'][key]['name'] == name
        triggers = external.get('on', external.get(True))
        assert {'pull_request', 'merge_group'} <= set(triggers)
        assert all(evaluate(external['jobs'][key].get('if'), event=ev) for ev in ('pull_request', 'merge_group'))



@pytest.mark.parametrize('event,full,expected', [('merge_group', False, True), ('push', False, True),
                                               ('workflow_dispatch', True, True), ('workflow_dispatch', False, False)])
def test_full_events_execute_every_heavy_job_even_for_docs_changes(event, full, expected):
    """Brief (b,c,d): queue/main/full dispatch runs every heavy leg, including docs changes."""
    w = workflow()
    triggers = w.get('on', w.get(True))
    assert triggers['workflow_dispatch']['inputs']['full_gate']['type'] == 'boolean'
    assert triggers['workflow_dispatch']['inputs']['full_gate']['default'] is False
    assert triggers['push']['branches'] == ['main'] and triggers['merge_group']['branches'] == ['main']
    if event == 'workflow_dispatch':
        assert not evaluate(w['jobs']['census-battery']['if'], event=event, full=full)
    for name in heavy_jobs(w['jobs']):
        assert evaluate(w['jobs'][name].get('if'), event=event, full=full, docs='true') is expected, name
        if expected and name in db_jobs(w['jobs']):
            import ci_gate
            for step in w['jobs'][name]['steps']:
                if ci_gate.PROFILE_CALL.search(step.get('run', '')):
                    assert evaluate(step.get('if'), event=event, full=full, docs='true'), (name, step.get('name'))


def test_only_changed_discovered_db_profiles_run_on_a_pull_request(tmp_path, monkeypatch):
    """Brief (a): ownership comes from discovery, including a newly added test, not source prefixes."""
    import ci_gate
    import ci_discovery
    jobs = workflow()['jobs']
    profiles = ci_discovery.profiles()
    for owner in sorted(db_jobs(jobs)):
        mapping = ci_gate.db_profile_owners(jobs)
        owned = [p for p, owners in mapping.items() if owner in owners]
        if not owned:
            assert owner == 'replace-chain-substrate' and owner in jobs['gochara-a55-replace-chain']['needs']
            continue
        profile = owned[0]
        files = ci_discovery.discover(ROOT, profiles[profile])
        cwd = ROOT / profiles[profile]['cwd']
        expanded = [p for f in files for p in (list((cwd / f).rglob('*')) if (cwd / f).is_dir() else [cwd / f])]
        suffix = ('.py',) if profiles[profile]['engine'] == 'pytest' else ('.test.ts', '.test.tsx')
        path = next(p.relative_to(cwd).as_posix() for p in expanded if p.is_file() and p.name.endswith(suffix) and (profiles[profile]['engine'] != 'pytest' or p.name.startswith('test_') or p.name.endswith('_test.py')))
        changed = (Path(profiles[profile]['cwd']) / path).as_posix()
        selected, selected_profiles = ci_gate.select_db(ROOT, jobs, [changed])
        assert owner in selected and profile in selected_profiles, (owner, changed)
        for step in jobs[owner]['steps']:
            calls = ci_gate.PROFILE_CALL.findall(step.get('run', ''))
            if calls:
                assert evaluate(step.get('if'), event='pull_request', profiles=selected_profiles) is bool(set(calls) & set(selected_profiles))
        for name in db_jobs(jobs):
            assert evaluate(jobs[name].get('if'), event='pull_request', selected=selected) is (name in selected), name
    assert ci_gate.select_db(ROOT, jobs, ['platform/src/app/page.tsx']) == ([], [])
    assert ci_gate.select_db(ROOT, jobs, ['platform/python-sidecar/tests/l3/kala_db/_schema.py']) == ([], [])
    # Newly added filename family member is discovered without a workflow edit.
    local = tmp_path / 'platform/tests/integration'
    local.mkdir(parents=True)
    (local / 'fresh.db.test.ts').write_text('test')
    monkeypatch.setattr(ci_discovery, 'profiles', lambda: {'fresh': {'cwd': 'platform', 'engine': 'vitest', 'include': ['tests/integration/*.db.test.ts']}})
    synthetic = {'db': {'services': {'postgres': {}}, 'steps': [{'run': 'python ci_discovery.py vitest fresh --'}]}}
    assert ci_gate.select_db(tmp_path, synthetic, ['platform/tests/integration/fresh.db.test.ts']) == (['db'], ['fresh'])
    assert ci_gate.select_db(tmp_path, synthetic, ['platform/tests/integration/deleted.db.test.ts']) == (['db'], ['fresh'])


def test_discovery_does_not_launch_an_unselected_pr_profile(tmp_path, monkeypatch):
    """Brief (a): unrelated profiles skip; a selected failing suite makes its job fail."""
    import ci_discovery
    (tmp_path / 'test_db_contract.py').write_text('def test_contract(): assert False\n')
    monkeypatch.setattr(ci_discovery, 'ROOT', tmp_path)
    monkeypatch.setattr(ci_discovery, 'profiles', lambda: {'demo': {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}})
    monkeypatch.setattr(sys, 'argv', ['ci_discovery.py', 'pytest', 'demo', '--', '-q', '-p', 'no:cacheprovider'])
    monkeypatch.setenv('CI_PR_DB_PROFILES', '[]')
    assert ci_discovery.main() == 0
    monkeypatch.setenv('CI_PR_DB_PROFILES', '["demo"]')
    assert ci_discovery.main() == 1


def test_required_aggregate_propagates_every_heavy_failure_and_unexpected_skip():
    """Brief (c), §N.8: a real failure/skip must be able to turn the protected check red."""
    jobs = workflow()['jobs']
    agg = jobs['full-suite']
    assert heavy_jobs(jobs) <= set(agg['needs'])
    assert 'full-suite' in jobs['governance-gates']['needs']
    step = agg['steps'][0]
    for event, full in [('merge_group', False), ('push', False), ('workflow_dispatch', True), ('pull_request', False)]:
        expected = {n: {'result': 'success'} for n in agg['needs']}
        env = {**os.environ, 'EVENT_NAME': event, 'FULL_GATE': str(full).lower(), 'REF': 'refs/heads/main',
               'DB_JOBS': '[]', 'NEEDS_JSON': json.dumps(expected)}
        p = subprocess.run(['bash', '-e', '-c', step['run']], env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stdout + p.stderr
        for name in heavy_jobs(jobs):
            for result in ('failure', 'cancelled', 'skipped'):
                cases = {**expected, name: {'result': result}}
                p = subprocess.run(['bash', '-e', '-c', step['run']], env={**env, 'NEEDS_JSON': json.dumps(cases)}, capture_output=True, text=True)
                allowed = event == 'pull_request' and result == 'skipped'
                assert (p.returncode == 0) is allowed, (event, name, result, p.stdout, p.stderr)
        # On PRs a selected DB job must succeed; unselected skips alone are permitted.
        if event == 'pull_request':
            name = sorted(db_jobs(jobs))[0]
            env.update(DB_JOBS=json.dumps([name]), NEEDS_JSON=json.dumps({**expected, name: {'result': 'skipped'}}))
            assert subprocess.run(['bash', '-e', '-c', step['run']], env=env, capture_output=True).returncode != 0


def test_db_mutation_harness_runs_once_only_on_full_events():
    """Brief (b,d): selected PR suites do not also pay for auxiliary P06 mutations."""
    jobs = workflow()['jobs']
    worker = jobs['db-integration-tests']
    source = next(s['run'] for s in worker['steps'] if 'mutation_check_1206.py' in s.get('run', ''))
    source = '\n'.join(line for line in source.splitlines() if 'ci_discovery.py' not in line)
    source = source.replace('python3 scripts/gochara/mutation_check_1206.py', 'echo MUTATION_RUN')
    shards = worker.get('strategy', {}).get('matrix', {}).get('shard', [1])
    for event, full, expected in [('pull_request', False, 0), ('merge_group', False, 1),
                                  ('push', False, 1), ('workflow_dispatch', True, 1), ('workflow_dispatch', False, 0)]:
        calls = 0
        for shard in shards:
            script = source.replace('${{ matrix.shard }}', str(shard))
            script = re.sub(r'\$\{\{[^}]+}}', lambda m: str(evaluate(m[0], event=event, full=full)).lower(), script)
            p = subprocess.run(['bash', '-e', '-c', script], capture_output=True, text=True)
            assert p.returncode == 0, p.stderr
            calls += p.stdout.count('MUTATION_RUN')
        assert calls == expected, (event, full, calls)
