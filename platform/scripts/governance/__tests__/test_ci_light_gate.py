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


# SR-BOLD-08(a): umbrellas that run on EVERY event and earn their verdict in a script (their own oracles below), so they are not
# "skipped when unselected" like the rest of the heavy family.
REPORTING_UMBRELLAS = {'required-db-integration-tests'}


def skippable_heavy_jobs(jobs):
    return heavy_jobs(jobs) - REPORTING_UMBRELLAS


def test_pull_request_has_light_checks_and_skips_unrelated_heavy_jobs():
    """Brief (a,b): ordinary code PR pays only the light gate, all required names report."""
    jobs = workflow()['jobs']
    names = {j.get('name') for j in jobs.values()}
    assert REQUIRED <= names
    historical = json.loads((ROOT / 'platform/scripts/governance/ci_discovery_baseline.json').read_text())
    assert set(historical['job_names'].values()) <= names, 'every original context, including any protected name, must report'
    for name in skippable_heavy_jobs(jobs):
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



@pytest.mark.parametrize('event,full,expected', [('push', False, True),
                                               ('workflow_dispatch', True, True), ('workflow_dispatch', False, False)])
def test_full_events_execute_every_heavy_job_even_for_docs_changes(event, full, expected):
    """Brief (b,c,d), OWNER-CI-SCOPED-QUEUE-20261017: main/full dispatch runs every heavy leg, including docs changes.
    The merge queue is deliberately NOT here any more: it is scoped like a PR (tests below)."""
    w = workflow()
    triggers = w.get('on', w.get(True))
    assert triggers['workflow_dispatch']['inputs']['full_gate']['type'] == 'boolean'
    assert triggers['workflow_dispatch']['inputs']['full_gate']['default'] is False
    assert triggers['push']['branches'] == ['main'] and triggers['merge_group']['branches'] == ['main']
    if event == 'workflow_dispatch':
        assert not evaluate(w['jobs']['census-battery']['if'], event=event, full=full)
    for name in skippable_heavy_jobs(w['jobs']):
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
        scoped = event in ('pull_request', 'merge_group')
        expected = {n: {'result': 'success'} for n in agg['needs']}
        env = {**os.environ, 'EVENT_NAME': event, 'FULL_GATE': str(full).lower(), 'REF': 'refs/heads/main',
               'DB_JOBS': '[]', 'NEEDS_JSON': json.dumps(expected)}
        p = subprocess.run(['bash', '-e', '-c', step['run']], env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stdout + p.stderr
        for name in heavy_jobs(jobs):
            for result in ('failure', 'cancelled', 'skipped'):
                cases = {**expected, name: {'result': result}}
                p = subprocess.run(['bash', '-e', '-c', step['run']], env={**env, 'NEEDS_JSON': json.dumps(cases)}, capture_output=True, text=True)
                allowed = scoped and result == 'skipped'
                assert (p.returncode == 0) is allowed, (event, name, result, p.stdout, p.stderr)
        # On PRs and the queue a selected DB job must succeed; unselected skips alone are permitted.
        if scoped:
            name = sorted(db_jobs(jobs))[0]
            env.update(DB_JOBS=json.dumps([name]), NEEDS_JSON=json.dumps({**expected, name: {'result': 'skipped'}}))
            assert subprocess.run(['bash', '-e', '-c', step['run']], env=env, capture_output=True).returncode != 0


def test_db_mutation_harness_runs_once_only_on_full_events():  # the queue is scoped, not full
    """Brief (b,d): selected PR suites do not also pay for auxiliary P06 mutations."""
    jobs = workflow()['jobs']
    worker = jobs['db-integration-tests']
    source = next(s['run'] for s in worker['steps'] if 'mutation_check_1206.py' in s.get('run', ''))
    source = '\n'.join(line for line in source.splitlines() if 'ci_discovery.py' not in line)
    source = source.replace('python3 scripts/gochara/mutation_check_1206.py', 'echo MUTATION_RUN')
    shards = worker.get('strategy', {}).get('matrix', {}).get('shard', [1])
    for event, full, expected in [('pull_request', False, 0), ('merge_group', False, 0),
                                  ('push', False, 1), ('workflow_dispatch', True, 1), ('workflow_dispatch', False, 0)]:
        calls = 0
        for shard in shards:
            script = source.replace('${{ matrix.shard }}', str(shard))
            script = re.sub(r'\$\{\{[^}]+}}', lambda m: str(evaluate(m[0], event=event, full=full)).lower(), script)
            p = subprocess.run(['bash', '-e', '-c', script], capture_output=True, text=True)
            assert p.returncode == 0, p.stderr
            calls += p.stdout.count('MUTATION_RUN')
        assert calls == expected, (event, full, calls)


def test_earned_signal_gate_runs_on_merge_group():
    """§N.8 gate must be reported (executed, not skipped) on every full event and on every PR kind.

    madhav-6d 2026-10-17: #3625 landed with a §N.8 violation because the gate was not
    enforced on the queue. Claim: the job (and its only dependency chain) has no condition
    that can skip it on merge_group, for docs-only and code changes alike, its required-check
    name is unchanged, and no step can swallow its failure.
    """
    w = workflow()
    jobs = w['jobs']
    triggers = w.get('on', w.get(True))
    assert 'merge_group' in triggers, 'merge_group trigger removed: required checks never report on the queue'
    gate = jobs['earned-signal-lint']
    assert gate['name'] == 'Earned-Signal Gate (§N.8)', 'required-check context name must not change'
    chain, todo = set(), ['earned-signal-lint']
    while todo:
        name = todo.pop()
        needs = jobs[name].get('needs') or []
        needs = [needs] if isinstance(needs, str) else needs
        chain.add(name)
        todo.extend(n for n in needs if n not in chain)
    assert 'changes' not in chain, 'the gate must not sit behind the light-PR classifier'
    for name in sorted(chain):
        for event in ('merge_group', 'push'):
            for docs in ('true', 'false'):
                assert evaluate(jobs[name].get('if'), event=event, docs=docs), (name, event, docs)
    assert 'continue-on-error' not in gate and all('continue-on-error' not in s for s in gate['steps'])
    assert all(s.get('if') is None for s in gate['steps'] if 'check_earned_signal.py' in s.get('run', ''))


def _scoped_state(jobs):
    """Selection fixtures: nothing selected, and every DB job + discovered profile selected."""
    import ci_gate
    owners = ci_gate.db_profile_owners(jobs)
    return [
        dict(selected=(), profiles=()),
        dict(selected=sorted({j for o in owners.values() for j in o} | db_jobs(jobs)), profiles=sorted(owners)),
    ]


def test_merge_queue_selects_exactly_what_a_pull_request_selects():
    """OWNER-CI-SCOPED-QUEUE-20261017 claim 1: every `if` (job and step) gives the same verdict on merge_group as on a PR.

    Oracle is the PR contract itself (D-29 scoped selection, test above); a job or step that still lists
    merge_group among the full events would run unselected heavy work on the queue and differ here.
    """
    jobs = workflow()['jobs']
    checked = 0
    for state in _scoped_state(jobs):
        for docs in ('false',):
            for name, job in jobs.items():
                for where, cond in [(name, job.get('if'))] + [(f"{name}/{st.get('name')}", st.get('if')) for st in job.get('steps', [])]:
                    if cond is None or 'github.event_name' not in str(cond):
                        continue
                    pr = evaluate(cond, event='pull_request', docs=docs, **state)
                    mg = evaluate(cond, event='merge_group', docs=docs, **state)
                    assert pr == mg, (where, state['selected'][:1])
                    checked += 1
    assert checked > 100
    heavy_unselected = [n for n in skippable_heavy_jobs(jobs) if evaluate(jobs[n].get('if'), event='merge_group')]
    assert heavy_unselected == [], f'merge_group runs heavy jobs nothing selected: {heavy_unselected}'


def test_merge_queue_hands_the_changed_profiles_to_discovery():
    """Claim 1b: CI_PR_DB_PROFILES is fed on merge_group, else a selected job would run its whole profile list."""
    jobs = workflow()['jobs']
    seen = 0
    for name, job in jobs.items():
        value = (job.get('env') or {}).get('CI_PR_DB_PROFILES')
        if value is None:
            continue
        seen += 1
        # evaluate() yields truthiness: the profile JSON is non-empty on the queue / PR and '' on full events.
        assert evaluate(value, event='merge_group', profiles=('some-profile',)), name
        assert evaluate(value, event='pull_request', profiles=('some-profile',)), name
        assert not evaluate(value, event='push', profiles=('some-profile',)), name
        assert not evaluate(value, event='workflow_dispatch', full=True, profiles=('some-profile',)), name
    assert seen >= 8


def test_ci_gate_selects_changed_profiles_on_merge_group_and_nothing_on_main(monkeypatch, capsys):
    """Claim 1c: `ci_gate.py --event merge_group` prints the same selection as a PR; push/dispatch print none."""
    import ci_changes
    import ci_gate
    changed = ['platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py']
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: changed)
    out = {}
    for event in ('pull_request', 'merge_group', 'push', 'workflow_dispatch'):
        assert ci_gate.main(['--event', event, '--base', 'B', '--head', 'H']) == 0
        out[event] = capsys.readouterr().out
    assert 'gochara-a55-replace-chain' in out['merge_group']
    parsed = {e: dict(l.split('=', 1) for l in out[e].splitlines()) for e in ('pull_request', 'merge_group')}
    # the queue = the PR selection plus the SR-CI-SCOPED-SAFEGUARD suites (own oracle below), nothing else
    for key in ('db_jobs', 'db_profiles'):
        assert set(json.loads(parsed['pull_request'][key])) <= set(json.loads(parsed['merge_group'][key]))
    assert {j for j in json.loads(parsed['merge_group']['db_jobs'])} - set(json.loads(parsed['pull_request']['db_jobs'])) \
        <= ci_gate.QUEUE_ALWAYS_JOBS | ci_gate.QUEUE_PATH_SCOPED_JOBS
    assert out['push'] == out['workflow_dispatch'] == 'db_jobs=[]\ndb_profiles=[]\nrun_combination_suites=true\n'
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: None)
    with pytest.raises(ValueError):
        ci_gate.main(['--event', 'merge_group'])


def test_combination_sensitive_suites_run_on_every_merge_group_even_for_an_unrelated_change(monkeypatch, capsys):
    """SR-CI-SCOPED-SAFEGUARD: SAMIKSHA DB Integration (all shards), the Gochara measuring build and the C38 teardown
    jobs (they failed green-alone/red-combined) run on a merge_group whose diff touches none of their tests; a PR with
    the same diff, and every other DB job, stay path-scoped; the required checks still pass through the umbrellas."""
    import ci_changes
    import ci_gate
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: ['platform/scripts/governance/__tests__/test_nb_kala_ci.py'])
    out = {}
    for event in ('pull_request', 'merge_group'):
        assert ci_gate.main(['--event', event, '--base', 'B', '--head', 'H']) == 0
        out[event] = dict(line.split('=', 1) for line in capsys.readouterr().out.splitlines())
    jobs = workflow()['jobs']
    names = {n: str(j.get('name')) for n, j in jobs.items()}
    queue_jobs, queue_profiles = json.loads(out['merge_group']['db_jobs']), json.loads(out['merge_group']['db_profiles'])
    assert out['pull_request'] == {'db_jobs': '[]', 'db_profiles': '[]', 'run_combination_suites': 'false'}
    must = {n for n, name in names.items() if jobs[n].get('services') and (
        'DB Integration Tests (SAMĪKṢĀ' in name or 'Gochara measuring build' in name or 'Gochara C38 - the small-test teardown' in name)}
    assert len(must) == 5, must
    assert must <= set(queue_jobs)
    import ci_discovery
    shards = {p for p in ci_discovery.profiles() if p.startswith(('db-integration-tests-', 'gochara-a55-measuring-build-', 'gochara-a55-teardown'))}
    assert shards and shards <= set(queue_profiles)
    assert set(queue_jobs) == must, 'every other DB job stays path-scoped'
    for n in sorted(must):
        assert evaluate(jobs[n].get('if'), event='merge_group', selected=queue_jobs, profiles=queue_profiles), n
    for n in ('required-db-integration-tests', 'required-gochara-a55-teardown', 'required-gochara-a55-teardown-round3'):
        assert evaluate(jobs[n].get('if'), event='merge_group', selected=queue_jobs, profiles=queue_profiles), n
    assert not evaluate(jobs['gochara-a55-replace-chain'].get('if'), event='merge_group', selected=queue_jobs, profiles=queue_profiles)


C37_C38_JOBS = {'gochara-a55-dispatch', 'gochara-a55-teardown', 'gochara-a55-teardown-round2', 'gochara-a55-teardown-round3'}
C37_PROFILE = 'gochara-a55-dispatch-1-9'


@pytest.mark.parametrize('changed', [
    '00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py',
    '00_ARCHITECTURE/briefs/kalayantra/fleet/J2A_SCOPED_BACKUP_v1_0.md',
    'platform/scripts/v5_small_test_shared.py',
    'platform/scripts/backup_v5_small_test_job.py',
    'platform/scripts/dispatch_v5_century_job.py',
    'platform/scripts/teardown_v5_small_test_job.py',
    'platform/python-sidecar/tests/l3/gochara/_smalltest_executor_evidence.py',
])
def test_sr_scope_c37_queue_runs_c37_and_c38_for_each_small_test_backup_dispatch_teardown_executor_path(monkeypatch, capsys, changed):
    """SR-SCOPE-C37 (incident #3715): a merge_group touching any listed path family runs C37 (dispatch) and the C38 teardown jobs
    and the C37 profile; the same diff on a pull_request stays path-scoped. Required check names are not touched."""
    import ci_changes
    import ci_gate
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: [changed])
    out = {}
    for event in ('pull_request', 'merge_group'):
        assert ci_gate.main(['--event', event, '--base', 'B', '--head', 'H']) == 0
        out[event] = dict(line.split('=', 1) for line in capsys.readouterr().out.splitlines())
    assert C37_C38_JOBS <= set(json.loads(out['merge_group']['db_jobs'])), changed
    assert C37_PROFILE in json.loads(out['merge_group']['db_profiles']), changed
    assert not C37_C38_JOBS & set(json.loads(out['pull_request']['db_jobs'])), 'a pull_request stays path-scoped'
    jobs = workflow()['jobs']
    for n in C37_C38_JOBS:
        assert evaluate(jobs[n].get('if'), event='merge_group', selected=json.loads(out['merge_group']['db_jobs']),
                        profiles=json.loads(out['merge_group']['db_profiles'])), n


def test_sr_scope_c37_queue_does_not_run_c37_for_an_unrelated_docs_only_change(monkeypatch, capsys):
    """SR-SCOPE-C37: a docs-only diff adds no C37 job or profile on the queue (C38 stays only via SR-CI-SCOPED-SAFEGUARD)."""
    import ci_changes
    import ci_gate
    monkeypatch.setattr(ci_changes, 'changed_files', lambda base, head: ['docs/README.md', '00_ARCHITECTURE/briefs/kalayantra/NOTES.md'])
    assert ci_gate.main(['--event', 'merge_group', '--base', 'B', '--head', 'H']) == 0
    out = dict(line.split('=', 1) for line in capsys.readouterr().out.splitlines())
    assert 'gochara-a55-dispatch' not in json.loads(out['db_jobs'])
    assert C37_PROFILE not in json.loads(out['db_profiles'])
    assert not ci_gate.queue_always_jobs('pull_request', ['platform/scripts/backup_v5_small_test_job.py'])
    assert ci_gate.queue_always_jobs('merge_group', ['docs/README.md']) == ci_gate.QUEUE_ALWAYS_JOBS


def test_merge_queue_diffs_against_the_group_base_and_every_required_check_reports():
    """Claim 3: required contexts still report on the queue; the queue diff uses merge_group.base_sha (fail-closed)."""
    w = workflow()
    jobs = w['jobs']
    assert 'merge_group' in w.get('on', w.get(True))
    step = next(s for s in jobs['changes']['steps'] if s.get('id') == 'select-db')
    assert step['env']['MERGE_GROUP_BASE_SHA'] == '${{ github.event.merge_group.base_sha }}'
    assert 'fetch --no-tags --depth=1 origin "$MERGE_GROUP_BASE_SHA"' in step['run'] and '--base "$base"' in step['run']
    historical = json.loads((ROOT / 'platform/scripts/governance/ci_discovery_baseline.json').read_text())['job_names']
    by_name = {j.get('name'): n for n, j in jobs.items()}
    # Light/aggregate required contexts run on the queue exactly as on a PR, with nothing selected.
    for context in sorted(REQUIRED | set(historical.values())):
        key = by_name[context] if context in by_name else None
        assert key, f'required context {context!r} has no job: it would never report on the queue'
        if '${{' in context:
            assert 'matrix' in jobs[key]['strategy'], context
    for key in ('typecheck', 'unit-tests', 'secret-scan', 'earned-signal-lint', 'governance-tool-tests', 'governance-gates-static',
                'full-suite', 'governance-gates'):
        assert evaluate(jobs[key].get('if'), event='merge_group'), key
    # A skipped heavy job rolls up to a passing aggregate on the queue, as on a PR (aggregate test above).
    assert not any(evaluate(jobs[n].get('if'), event='merge_group') for n in skippable_heavy_jobs(jobs))
