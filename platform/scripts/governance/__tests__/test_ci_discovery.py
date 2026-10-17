"""A5 D-33: discovery is executable, fail closed, and fixture contexts survive."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
TOOL = ROOT / 'platform/scripts/governance/ci_discovery.py'


def module():
    spec = importlib.util.spec_from_file_location('ci_discovery', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ci_has_no_literal_test_file_selections():
    assert module().workflow_problems((ROOT / '.github/workflows/ci.yml').read_text()) == []


def test_governance_guard_rejects_a_future_literal_in_a_discovered_directory():
    mod = module()
    for command in ('pytest tests/l3/gochara/test_new.py -q', 'npx vitest run src/__tests__/new.test.ts', 'npx vitest run src/__tests__/new.spec.tsx'):
        assert mod.workflow_problems('jobs:\n  x:\n    steps:\n      - run: '+command+'\n')
    assert mod.workflow_problems('jobs:\n  x:\n    steps:\n      - run: pytest tests/l3/gochara -q\n') == []


def test_new_family_files_are_discovered_and_empty_profiles_fail(tmp_path):
    mod = module()
    (tmp_path / 'test_family_one.py').write_text('def test_one(): pass\n')
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_family*.py']}
    assert mod.discover(tmp_path, profile) == ['test_family_one.py']
    (tmp_path / 'test_family_new.py').write_text('def test_new(): pass\n')
    assert mod.discover(tmp_path, profile) == ['test_family_new.py', 'test_family_one.py']
    with pytest.raises(ValueError, match='empty'):
        mod.discover(tmp_path, {**profile, 'include': ['missing*.py']})


def test_baseline_files_remain_selected_in_the_same_fixture_context():
    mod = module()
    profiles = json.loads((TOOL.parent / 'ci_test_suites.json').read_text())['suites']
    baseline = json.loads((TOOL.parent / 'ci_discovery_baseline.json').read_text())['commands']
    for command in baseline:
        profile = profiles[command['suite']]
        assert profile['cwd'] == command['cwd'] and profile['engine'] == command['engine']
        selected = mod.discover(ROOT, profile)
        for path in command['paths']:
            if (ROOT / command['cwd'] / path).is_dir():
                assert path.rstrip('/') in {entry.rstrip('/') for entry in selected}, (command['suite'], path)
                continue
            assert path in selected or path.split("::")[0] in selected or any((ROOT / command['cwd'] / sel).is_dir() and Path(path).is_relative_to(Path(sel)) for sel in selected), (command['suite'], path)


def test_a_new_profile_does_not_reintroduce_a_file_allowlist():
    for profile in json.loads((TOOL.parent / 'ci_test_suites.json').read_text())['suites'].values():
        assert all('*' in pattern for pattern in profile['include'])


def test_builder_role_profile_keeps_main_narrowing_and_accepts_new_family_cases(tmp_path):
    """The shard merge must not restore the superseded broad L1 selector."""
    mod = module()
    profile = mod.profiles()['db-integration-tests-37-2']
    directory = tmp_path / profile['cwd'] / 'ga_writers/__tests__'
    directory.mkdir(parents=True)
    for name in ('test_l1_min_fixes_builder_role_pg.py',
                 'test_l1_min_fixes_future.py', 'test_l1_data_plane_contracts.py'):
        (directory / name).write_text('def test_case(): pass\n')
    assert mod.discover(tmp_path, profile) == [
        'ga_writers/__tests__/test_l1_min_fixes_builder_role_pg.py',
        'ga_writers/__tests__/test_l1_min_fixes_future.py',
    ]


def test_runner_propagates_collection_failure_and_executes_new_test(tmp_path):
    mod = module()
    (tmp_path / 'test_new.py').write_text('def test_new(): assert False\n')
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    assert mod.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider']) == 1
    (tmp_path / 'test_new.py').write_text('def test_new(): pass\n')
    assert mod.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider']) == 0


def test_slow_shards_are_complete_disjoint_and_keep_measured_balance():
    mod = module()
    shards = [mod.slow_files(ROOT, n) for n in range(1, 4)]
    full = mod.slow_files(ROOT)
    assert sorted(sum(shards, [])) == full
    assert len(sum(shards, [])) == len(set(sum(shards, [])))
    loads = [mod.SLOW_GROUP_ESTIMATES[i] + sum(mod.NEW_SLOW_ESTIMATE for f in shard if Path(f).name not in mod.SLOW_LEGS) for i, shard in enumerate(shards)]
    assert max(loads) - min(loads) <= max(mod.SLOW_GROUP_ESTIMATES) - min(mod.SLOW_GROUP_ESTIMATES), loads
    before = json.loads((TOOL.parent / 'ci_discovery_baseline.json').read_text())['matrices']['governance-gates-gochara']['include']
    for entry in before:
        if 'shard_files' in entry:
            leg = int(entry['leg'].removeprefix('slow-'))
            assert set(entry['shard_files'].split()) <= set(shards[leg - 1])


def test_new_template_backed_db_suite_joins_required_a53_context(tmp_path):
    mod = module()
    directory = tmp_path / 'platform/python-sidecar/tests/l3/gochara'
    directory.mkdir(parents=True)
    (directory / 'test_new_campaign.py').write_text('from . import template\ndef test_new(): pass\n')
    (directory / 'test_other.py').write_text('def test_unit(): pass\n')
    profile = {'cwd': 'platform/python-sidecar', 'engine': 'pytest', 'include': ['tests/l3/gochara/test_other*.py'], 'discover_db': True}
    assert 'tests/l3/gochara/test_new_campaign.py' in mod.discover(tmp_path, profile)
    (directory / 'nested').mkdir()
    (directory / 'nested/test_new_nested.py').write_text('from .. import template\ndef test_nested(): pass\n')
    assert 'tests/l3/gochara/nested/test_new_nested.py' in mod.discover(tmp_path, profile)


def test_all_original_job_names_and_shard_counts_remain_exact():
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    before = json.loads((TOOL.parent / 'ci_discovery_baseline.json').read_text())
    for key, name in before['job_names'].items():
        context = jobs.get('required-'+key, jobs[key])
        assert context.get('name', key) == name
    for key, matrix in before['matrices'].items():
        actual = jobs[key]['strategy']['matrix']
        # Runtime slow discovery removes only the old shard_files payload.
        def legs(value):
            if 'include' in value:
                return [entry['leg'] for entry in value['include']]
            return value
        assert legs(matrix) == legs(actual)


def test_mcp_quarantine_cannot_remove_a_previously_run_file():
    before = json.loads((TOOL.parent / 'ci_discovery_baseline.json').read_text())['commands']
    selected = {path for command in before if command['cwd'] == 'platform-mcp' for path in command['paths']}
    for profile in module().profiles().values():
        assert not selected.intersection(profile.get('quarantine', {}))
        assert all(not any(char in path for char in '*?[') for path in profile.get('quarantine', {}))


@pytest.mark.parametrize('missing', ['dependency', 'restore', 'order', 'conditional'])
def test_guard_discovers_future_checkout_consumers_automatically(missing):
    jobs = {
        'generated-artifacts': {'steps': [{'uses': 'actions/checkout@v4'}]},
        'changes': {'steps': [{'uses': 'actions/checkout@v4'}]},
        'future-merged-job': {
            'needs': ['changes', 'generated-artifacts'],
            'steps': [{'uses': 'actions/checkout@v4'},
                      {'uses': './.github/actions/restore-generated'},
                      {'run': 'python -m pytest tests/new_family'}],
        },
    }
    mod = module()
    assert mod.workflow_problems(yaml.safe_dump({'jobs': jobs})) == []
    job = jobs['future-merged-job']
    if missing == 'dependency':
        job['needs'] = ['changes']
    elif missing == 'restore':
        job['steps'].pop(1)
    elif missing == 'order':
        job['steps'].reverse()
    else:
        job['steps'][1]['if'] = 'false'
    assert any('future-merged-job' in error for error in mod.workflow_problems(yaml.safe_dump({'jobs': jobs})))


def test_merged_g1_candidate_suites_keep_the_required_kala_db_context():
    """PR #3588: main's G1 selectors must survive discovery without literal paths."""
    mod = module()
    profile = mod.profiles()['kala-db-tests-5-0']
    assert profile['cwd'] == 'platform/python-sidecar'
    selected = mod.discover(ROOT, profile)
    for path in ('tests/l3/ka_kshetra/test_g1a_contract.py',
                 'tests/l3/ka_kshetra/test_g1a_candidate_sql.py'):
        assert path in selected
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    assert any('ci_discovery.py" pytest kala-db-tests-5-0 --' in step.get('run', '')
               for step in jobs['kala-db-tests']['steps'])


def test_j5s_mandatory_job_discovers_and_runs_future_full_class_suites(tmp_path):
    """J5S-N1: a new family member must run in the existing required DB context."""
    mod = module()
    profile = mod.profiles()['gochara-j5s-full-class-seal']
    assert profile['cwd'] == 'platform/python-sidecar'
    assert profile['engine'] == 'pytest'
    assert 'tests/l3/gochara/test_j5s_full_class_seal_db.py' in mod.discover(ROOT, profile)

    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    job = jobs['gochara-j5s-full-class-seal']
    command = next(step['run'] for step in job['steps']
                   if 'ci_discovery.py' in step.get('run', ''))
    assert 'pytest gochara-j5s-full-class-seal --' in command
    expanded = mod.expanded_workflow({'j5s': job})['j5s']
    assert any('python -m pytest tests/l3/gochara/test_j5s_full_class_seal_db.py' in step.get('run', '')
               for step in expanded['steps'])

    future = tmp_path / profile['cwd'] / 'tests/l3/gochara/test_j5s_future_db.py'
    future.parent.mkdir(parents=True)
    future.write_text('def test_future(): assert False\n')
    assert mod.discover(tmp_path, profile) == ['tests/l3/gochara/test_j5s_future_db.py']
    assert mod.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider']) == 1
    future.write_text('def test_future(): assert True\n')
    assert mod.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider']) == 0
