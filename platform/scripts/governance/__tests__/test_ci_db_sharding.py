"""A4 D-31: file sharding preserves selections and required checks fail closed."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
GOV = ROOT / 'platform/scripts/governance'
sys.path.insert(0, str(GOV))
import ci_discovery as discovery
from _ci_gate_test_support import evaluate as discovery_eval


def sharding():
    spec = importlib.util.spec_from_file_location('ci_db_shard', GOV / 'ci_db_shard.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_shards_cover_every_discovered_file_once_and_new_files_join(tmp_path, monkeypatch):
    mod = sharding()
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {'demo-1': profile})
    for name in ('heavy', 'medium', 'light', 'new'):
        (tmp_path / f'test_{name}.py').write_text('def test_one(): pass\n')
    durations = {'test_heavy.py': 90, 'test_medium.py': 60, 'test_light.py': 30}
    plan = mod.partition_job(tmp_path, 'demo', 2, durations)
    assert Counter(f for shard in plan for f in shard) == Counter(f'test_{n}.py' for n in ('heavy','medium','light','new'))
    assert 'test_heavy.py' not in plan[1]
    assert 'test_medium.py' in plan[1] and 'test_light.py' in plan[1]
    assert mod.partition_job(tmp_path, 'demo', 2, durations) == plan
    (tmp_path / 'test_future.py').write_text('def test_future(): pass\n')
    assert 'test_future.py' in sum(mod.partition_job(tmp_path, 'demo', 2, durations), [])


def test_runtime_selection_runs_only_assigned_files_and_propagates_failure(tmp_path, monkeypatch):
    mod = sharding()
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {'demo-1': profile})
    (tmp_path / 'test_a.py').write_text('def test_a(): assert False\n')
    (tmp_path / 'test_b.py').write_text('def test_b(): pass\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB', 'demo')
    monkeypatch.setenv('CI_DB_SHARD', '1/2')
    assert discovery.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider'], suite='demo-1') == 1
    monkeypatch.setenv('CI_DB_SHARD', '2/2')
    assert discovery.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider'], suite='demo-1') == 0
    monkeypatch.setenv('CI_DB_SHARD', '3/2')
    with pytest.raises(ValueError):
        discovery.run(tmp_path, profile, [], suite='demo-1')


def test_empty_profile_share_never_invokes_unfiltered_test_runner(tmp_path, monkeypatch):
    sharding()
    first = {'cwd': '.', 'engine': 'pytest', 'include': ['test_a*.py']}
    second = {'cwd': '.', 'engine': 'pytest', 'include': ['test_b*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {'demo-1': first, 'demo-2': second})
    (tmp_path / 'test_a.py').write_text('def test_a(): assert False\n')
    (tmp_path / 'test_b.py').write_text('def test_b(): assert False\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB', 'demo')
    monkeypatch.setenv('CI_DB_SHARD', '2/2')
    assert discovery.run(tmp_path, first, [], suite='demo-1') == 0
    monkeypatch.setenv('CI_DB_SHARD_JOB', 'unknown')
    with pytest.raises(ValueError):
        discovery.run(tmp_path, first, [], suite='demo-1')


def test_real_partition_is_complete_and_required_names_remain_unique():
    mod = sharding()
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    baseline = json.loads((GOV / 'ci_discovery_baseline.json').read_text())['job_names']
    for job, count in mod.JOB_SHARDS.items():
        worker = jobs[job]
        assert worker['strategy']['matrix']['shard'] == list(range(1, count+1))
        assert worker['strategy']['fail-fast'] is False
        assert worker['env']['CI_DB_SHARD_JOB'] == job
        assert worker['env']['CI_DB_SHARD'] == '${{ matrix.shard }}/'+str(count)
        assert 'postgres' in worker['services']
        assert not worker.get('continue-on-error')
        assert 'docs_only' not in str(worker.get('if', ''))
        if job not in mod.NODE_SHARD_JOBS:
            plan = mod.partition_job(ROOT, job, count)
            assert all(plan)
        umbrella = jobs['required-'+job]
        assert umbrella['name'] == baseline[job]
        assert sum(j.get('name') == baseline[job] for j in jobs.values()) == 1
        expected_needs = ['changes', job, 'replace-chain-substrate'] if job in mod.NODE_SHARD_JOBS else ['changes', job]
        assert umbrella['needs'] == expected_needs
        assert not umbrella.get('continue-on-error')
        assert not umbrella['steps'][0].get('continue-on-error')
        # D-29 x D-31: job and umbrella share ONE selection rule (main's full-suite expects `required-<job>` iff <job> is selected).
        for event, selected, full, want in (('pull_request', [job], False, True), ('pull_request', [], False, False),
                                            ('pull_request', ['other'], False, False), ('merge_group', [], False, True),
                                            ('push', [], False, True), ('workflow_dispatch', [], True, True),
                                            ('workflow_dispatch', [], False, False)):
            assert discovery_eval(umbrella['if'], event=event, selected=selected, full=full) is want, (job, event, selected)
            assert discovery_eval(worker['if'], event=event, selected=selected, full=full) is want, (job, event, selected)
        script = umbrella['steps'][0]['run']
        # Once an umbrella runs, ANY non-success shard (failed, cancelled or skipped) or substrate result fails it.
        for result in ('success','failure','skipped','cancelled',''):
            preparation_results = ('success','failure','skipped','cancelled','') if job in mod.NODE_SHARD_JOBS else ('success',)
            for preparation in preparation_results:
                code = script.replace('${{ needs.'+job+'.result }}', result)
                code = code.replace('${{ needs.replace-chain-substrate.result }}', preparation)
                proc = subprocess.run(['bash', '-e', '-c', code], capture_output=True)
                assert (proc.returncode == 0) == (result == preparation == 'success'), (job,result,preparation)
    assert discovery.workflow_problems((ROOT / '.github/workflows/ci.yml').read_text()) == []


def test_every_db_worker_discovery_step_belongs_to_its_partition(monkeypatch):
    """The named small-test profile must join SAMĪKṢĀ's numeric profiles."""
    import re
    mod = sharding()
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    for job, count in mod.JOB_SHARDS.items():
        suites = {suite for step in jobs[job]['steps']
                  for suite in re.findall(r'ci_discovery.py" (?:pytest|vitest) ([\w-]+) --',
                                          step.get('run', ''))}
        assert suites == set(mod.job_profiles(job)), (job, suites ^ mod.job_profiles(job).keys())
    suite = 'db-integration-tests-smalltest'
    profile = discovery.profiles()[suite]
    files = discovery.discover(ROOT, profile)
    selected = []
    job = 'db-integration-tests'
    monkeypatch.setenv('CI_DB_SHARD_JOB', job)
    for index in range(mod.JOB_SHARDS[job]):
        monkeypatch.setenv('CI_DB_SHARD', f'{index+1}/{mod.JOB_SHARDS[job]}')
        selected.extend(mod.selected_files(ROOT, suite, profile, files))
    assert Counter(selected) == Counter(files)


@pytest.mark.parametrize('spec', ['', 'x/y', '0/2', '3/2', '1/0', '1/2/3'])
def test_invalid_shard_specs_fail_closed(tmp_path, monkeypatch, spec):
    mod = sharding()
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {'demo-1': profile})
    (tmp_path/'test_one.py').write_text('def test_one(): pass\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB', 'demo')
    monkeypatch.setenv('CI_DB_SHARD', spec)
    with pytest.raises(ValueError):
        mod.selected_files(tmp_path, 'demo-1', profile, ['test_one.py'])


def test_new_file_does_not_turn_an_empty_whole_job_shard_green(tmp_path, monkeypatch):
    mod = sharding()
    monkeypatch.setattr(discovery, 'profiles', lambda: {'demo-1': {'cwd':'.','engine':'pytest','include':['test_*.py']}})
    (tmp_path/'test_only.py').write_text('def test_only(): pass\n')
    with pytest.raises(ValueError, match='empty'):
        mod.partition_job(tmp_path, 'demo', 2, {})


def test_auxiliary_mutation_evidence_still_runs_once_across_the_matrix():
    """The 1206 mutation harness runs once, on shard 4, and only on a full event (D-29: never on a selected PR job)."""
    import re
    jobs = yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    script = next(s['run'] for s in jobs['db-integration-tests']['steps'] if 'mutation_check_1206.py' in s.get('run',''))
    script = '\n'.join(line for line in script.splitlines() if 'ci_discovery.py' not in line)
    script = script.replace('python3 scripts/gochara/mutation_check_1206.py', 'echo MUTATION_RUN')
    (full_expr,) = set(re.findall(r'\$\{\{ (\(github\.event_name.*?inputs\.full_gate\)\)) \}\}', script))
    for event, full, want in (('merge_group', False, 1), ('push', False, 1), ('workflow_dispatch', True, 1),
                              ('pull_request', False, 0), ('workflow_dispatch', False, 0)):
        calls = 0
        for index in range(1,5):
            shell = script.replace('${{ matrix.shard }}',str(index)).replace('${{ '+full_expr+' }}', str(discovery_eval('${{ '+full_expr+' }}', event=event, full=full)).lower())
            proc = subprocess.run(['bash','-e','-c',shell],capture_output=True,text=True)
            assert proc.returncode == 0
            calls += proc.stdout.count('MUTATION_RUN')
        assert calls == want, (event, full)


def test_committed_timings_have_recorded_sources_for_every_sharded_job():
    mod = sharding()
    timing = json.loads(mod.TIMINGS.read_text())
    assert timing['schema'] == 'ci.db_shard_timings/1'
    assert timing['sources'], 'balance must be backed by a recorded timing source'
    for job,count in mod.JOB_SHARDS.items():
        files = {str(Path(p['cwd']) / f) for p in mod.job_profiles(job).values() for f in discovery.discover(ROOT, p)}
        assert files.intersection(timing['file_seconds']), f'{job}: no recorded file durations'


def test_vitest_shards_exclude_unassigned_files_even_when_filename_filters_overlap(tmp_path,monkeypatch):
    sharding()
    profile={'cwd':'.','engine':'vitest','include':['*.test.*']}
    monkeypatch.setattr(discovery,'profiles',lambda:{'demo-1':profile})
    (tmp_path/'prefix.test.ts').write_text('test("one",()=>{});\n')
    (tmp_path/'prefix.test.tsx').write_text('test("two",()=>{});\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB','demo')
    monkeypatch.setenv('CI_DB_SHARD','1/2')
    commands=[]
    monkeypatch.setattr(discovery.subprocess,'call',lambda cmd,**kw: commands.append(cmd) or 0)
    assert discovery.run(tmp_path,profile,[],suite='demo-1')==0
    command=commands[0]
    assert command[command.index('--exclude')+1]=='prefix.test.tsx'
    assert 'prefix.test.ts' in command[:command.index('--exclude')]


def test_committed_node_id_comparison_covers_the_final_job_set():
    import hashlib
    mod=sharding()
    report=json.loads((GOV/'ci_db_shard_coverage.json').read_text())
    assert report['schema']=='ci.db_shard_coverage/1'
    expected={**mod.JOB_SHARDS,'kala-db-tests':1,'gochara-a55-slice-transitions':1,'gochara-a55-teardown-round2':1}
    assert set(report['jobs'])==set(expected)
    for job,count in expected.items():
        row=report['jobs'][job]
        assert row['identical'] and not row['missing'] and not row['extra']
        digest=hashlib.sha256('\n'.join(sorted(row['node_ids'])).encode()).hexdigest()
        assert row['before_sha256']==row['after_sha256']==digest
        assert row['before_count']==row['after_count']==len(row['node_ids'])
        assert len(row['shards'])==count
        assert sum(shard['count'] for shard in row['shards'])==row['before_count']


def test_auxiliary_work_reserves_budget_before_assigning_files(tmp_path,monkeypatch):
    mod=sharding()
    profile={'cwd':'.','engine':'pytest','include':['test_*.py']}
    monkeypatch.setattr(discovery,'profiles',lambda:{'demo-1':profile})
    durations={}
    for name in ('a','b','c','d'):
        path='test_'+name+'.py'
        (tmp_path/path).write_text('def test_one(): pass\n')
        durations[path]=10
    timing=tmp_path/'timings.json'
    timing.write_text(json.dumps({'file_seconds':durations,'shard_fixed_seconds':{'demo':{'2':20}}}))
    monkeypatch.setattr(mod,'TIMINGS',timing)
    # The second shard already has 20 seconds of non-file work; it needs one file,
    # while the first needs three, for 30 seconds of total work on both.
    assert [len(files) for files in mod.partition_job(tmp_path,'demo',2)]==[3,1]


def test_worker_check_names_cannot_alias_required_names_when_github_shortens_them():
    mod=sharding()
    jobs=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    before=json.loads((GOV/'ci_discovery_baseline.json').read_text())['job_names']
    for job,count in mod.JOB_SHARDS.items():
        names=[jobs[job]['name'].replace('${{ matrix.shard }}',str(i))[:100] for i in range(1,count+1)]
        assert before[job][:100] not in names,job
        assert len(set(names))==count,job


def test_replace_chain_splits_inside_heavy_file_without_losing_nodes(tmp_path, monkeypatch):
    """R1: reverting collection-level splitting strands the heavy file on one worker."""
    mod = sharding()
    job = 'gochara-a55-replace-chain'
    suite = job + '-1-9'
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {suite: profile})
    # Every case records its unchanged pytest node ID; one can be made to fail.
    source = '''import os, pytest
from pathlib import Path
@pytest.mark.parametrize("case", range(12))
def test_heavy(case, request):
    node = request.node.nodeid
    with Path(os.environ["SELECTION_OUTPUT"]).open("a") as out:
        out.write(node + "\\n")
    assert node != os.environ.get("FAIL_NODE")
'''
    (tmp_path / 'test_heavy.py').write_text(source)
    for i in range(4):
        (tmp_path / f'test_small_{i}.py').write_text('def test_small(): pass\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB', job)
    shards = []
    count = mod.JOB_SHARDS[job]
    for i in range(count):
        output = tmp_path / f'selected-{i}.txt'
        monkeypatch.setenv('SELECTION_OUTPUT', str(output))
        monkeypatch.setenv('CI_DB_SHARD', f'{i+1}/{count}')
        assert discovery.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider'], suite=suite) == 0
        shards.append(output.read_text().splitlines() if output.exists() else [])
    assert sum(bool(nodes) for nodes in shards) == count, 'heavy file is still indivisible'
    assert Counter(sum(shards, [])) == Counter(f'test_heavy.py::test_heavy[{i}]' for i in range(12))
    for i, nodes in enumerate(shards):
        monkeypatch.setenv('CI_DB_SHARD', f'{i+1}/{count}')
        monkeypatch.setenv('FAIL_NODE', nodes[0])
        assert discovery.run(tmp_path, profile, ['-q', '-p', 'no:cacheprovider'], suite=suite) == 1


def test_node_partition_is_complete_balanced_and_new_cases_join():
    mod = sharding()
    nodes = [f'test_heavy.py::test_case[{i}]' for i in range(12)]
    timing = {'node_seconds': {'demo': {n: 100 for n in nodes}},
              'node_shard_fixed_seconds': {'demo': 50}}
    plan = mod.partition_nodes(nodes, 'demo', 4, timing)
    assert Counter(sum(plan, [])) == Counter(nodes)
    assert [len(group) for group in plan] == [3, 3, 3, 3]
    assert mod.partition_nodes(list(reversed(nodes)), 'demo', 4, timing) == plan
    assert 'test_future.py::test_new' in sum(mod.partition_nodes(nodes + ['test_future.py::test_new'], 'demo', 4, timing), [])
    with pytest.raises(ValueError, match='empty'):
        mod.partition_nodes(nodes[:3], 'demo', 4, timing)
    with pytest.raises(ValueError, match='unique'):
        mod.partition_nodes(nodes + nodes[:1], 'demo', 4, timing)
    timing['node_seconds']['demo'][nodes[0]] = float('nan')
    with pytest.raises(ValueError, match='invalid DB node timing'):
        mod.partition_nodes(nodes, 'demo', 4, timing)


def test_node_shard_collection_retains_existing_deselection_policy(tmp_path, monkeypatch):
    mod = sharding()
    job = 'gochara-a55-replace-chain'
    suite = job + '-1-9'
    profile = {'cwd': '.', 'engine': 'pytest', 'include': ['test_*.py']}
    monkeypatch.setattr(discovery, 'profiles', lambda: {suite: profile})
    (tmp_path / 'test_cases.py').write_text('import pytest\n@pytest.mark.parametrize("case", range(12))\ndef test_keep(case): pass\ndef test_excluded(): pass\n')
    (tmp_path / 'conftest.py').write_text('import json, os\nfrom pathlib import Path\ndef pytest_collection_finish(session):\n    Path(os.environ["SELECTION_OUTPUT"]).write_text(json.dumps([item.nodeid for item in session.items]))\n')
    monkeypatch.setenv('CI_DB_SHARD_JOB', job)
    collected = []
    for i in range(mod.JOB_SHARDS[job]):
        output = tmp_path / f'collected-{i}.json'
        monkeypatch.setenv('SELECTION_OUTPUT', str(output))
        monkeypatch.setenv('CI_DB_SHARD', f'{i+1}/{mod.JOB_SHARDS[job]}')
        args = ['--collect-only', '-q', '-p', 'no:cacheprovider', '-k', 'not excluded',
                '--deselect=test_cases.py::test_keep[0]']
        assert discovery.run(tmp_path, profile, args, suite=suite) == 0
        collected.extend(json.loads(output.read_text()))
    assert Counter(collected) == Counter(f'test_cases.py::test_keep[{i}]' for i in range(1, 12))
    # A user filter must never turn an empty whole-job worker green.
    assert discovery.run(tmp_path, profile, ['--collect-only', '-q', '-p', 'no:cacheprovider', '-k', 'missing'], suite=suite) != 0


def test_parallel_real_substrate_is_required_before_node_workers():
    """R1: node partitioning must not repeat the full serial sky-template build."""
    jobs = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())['jobs']
    worker = jobs['gochara-a55-replace-chain']
    assert 'replace-chain-substrate' in worker['needs'], 'serial full-domain fixture is still on every test worker'
    producer = jobs['replace-chain-substrate']
    assert producer['strategy']['matrix']['body'] == ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    assert producer['strategy']['fail-fast'] is False
    assert not producer.get('continue-on-error')
    # D-29: main's selection (ci_gate) adds this producer whenever its only consumer is selected; the producer's own `if`
    # follows that selection, so it runs on full events and for a selected consumer, and is skipped otherwise.
    import ci_gate
    changed = 'platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py'
    selected, _ = ci_gate.select_db(ROOT, jobs, [changed])
    assert {'gochara-a55-replace-chain', 'replace-chain-substrate'} <= set(selected)
    for event, chosen, full, want in (('pull_request', selected, False, True), ('pull_request', [], False, False),
                                      ('merge_group', [], False, True), ('workflow_dispatch', [], False, False)):
        assert discovery_eval(producer['if'], event=event, selected=chosen, full=full) is want, (event, chosen)
    steps = worker['steps']
    download = next(s for s in steps if s.get('uses', '').startswith('actions/download-artifact@'))
    assert download['with']['pattern'] == 'replace-chain-substrate-*'
    test_step = next(s for s in steps if s.get('name', '').startswith('A5.5f - replace-chain suites'))
    assert test_step['env']['CI_REPLACE_CHAIN_SUBSTRATE'] == '${{ runner.temp }}/replace-chain-substrate'
    assert 'ci_replace_chain_fixture.py' in str(producer['steps'])
    umbrella = jobs['required-gochara-a55-replace-chain']
    assert 'replace-chain-substrate' in umbrella['needs']
    assert 'success' in umbrella['steps'][0]['run']


def test_prepared_substrate_rejects_missing_stale_corrupt_and_duplicate_bodies(tmp_path):
    import hashlib
    from ci_replace_chain_fixture import SCHEMA, TABLES, manifest_files
    ephe = {'unit-test-integrity-probe': 'not-used-for-computation'}
    kwargs = {'source': 'source-v1', 'bodies': ['Sun', 'Mars'], 'ephe': ephe}
    with pytest.raises(ValueError, match='every body'):
        manifest_files(tmp_path, **kwargs)
    for body in kwargs['bodies']:
        parent = tmp_path / body
        parent.mkdir()
        tables = {}
        for table in TABLES:
            data = parent / (table + '.copy')
            data.write_bytes(b'integrity probe only\n')
            tables[table] = {'sha256': hashlib.sha256(data.read_bytes()).hexdigest(), 'rows': 1}
        (parent / 'manifest.json').write_text(json.dumps({'schema': SCHEMA, 'source_digest': 'source-v1',
                                                        'ephe_sha256': ephe, 'body': body, 'tables': tables}))
    assert len(manifest_files(tmp_path, **kwargs)) == 2
    with pytest.raises(ValueError, match='stale or unbound'):
        manifest_files(tmp_path, **{**kwargs, 'source': 'changed'})
    with pytest.raises(ValueError, match='stale or unbound'):
        manifest_files(tmp_path, **{**kwargs, 'ephe': {}})
    with pytest.raises(ValueError, match='every body'):
        manifest_files(tmp_path, **{**kwargs, 'bodies': ['Sun', 'Sun']})
    (tmp_path / 'Sun' / (TABLES[0] + '.copy')).write_bytes(b'corrupt\n')
    with pytest.raises(ValueError, match='bytes mismatch'):
        manifest_files(tmp_path, **kwargs)


def test_replace_chain_recorded_work_fits_approximately_ten_minute_worker_budget():
    """R1: strict 600s estimates/preparation; 5% tolerance for local instrumented wall time."""
    import math
    mod = sharding()
    timing = json.loads(mod.TIMINGS.read_text())
    job = 'gochara-a55-replace-chain'
    report = json.loads((GOV / 'ci_db_shard_coverage.json').read_text())['jobs'][job]
    nodes = [n.removeprefix('platform/python-sidecar/') for n in report['node_ids']]
    weights = timing['node_seconds'][job]
    assert set(weights) == set(nodes), 'every original node needs an explicit initial scheduling estimate'
    plan = mod.partition_nodes(nodes, job, mod.JOB_SHARDS[job])
    fixed = timing['node_shard_fixed_seconds'][job]
    estimates = [fixed + sum(weights[n] for n in group) for group in plan]
    observed = timing['replace_chain_observed_seconds']
    assert set(observed['preparation']) == {'Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'}
    assert set(observed['workers']) == {str(i+1) for i in range(mod.JOB_SHARDS[job])}
    values = estimates + list(observed['preparation'].values())
    assert all(math.isfinite(v) and 0 < v <= 600 for v in values), values
    # (I) INTERPRETATION: 'approximately ten minutes' permits 5% on shared-host
    # instrumented wall time. Report actual values, including strict-limit misses.
    assert timing['local_worker_tolerance_seconds'] == 30
    assert all(math.isfinite(v) and 0 < v <= 630 for v in observed['workers'].values())


def test_node_worker_reuses_real_index_results_without_sharing_mutable_callers():
    try:
        import ci_db_node_shard as plugin
    except ModuleNotFoundError:
        plugin = None  # the pre-fix runner has no node-worker cache
    calls = []
    def factory(body, path):
        calls.append((body, path))
        return {'body': body, 'values': [path]}
    # A protocol probe, not an ephemeris stand-in: the DB workers use the real factory.
    cached = getattr(plugin, 'index_cache', lambda f: f)(factory)
    first = cached('Sun', 'pinned-corpus')
    first['values'].append('caller mutation')
    second = cached('Sun', 'pinned-corpus')
    assert calls == [('Sun', 'pinned-corpus')], 'the full real index is still recomputed for every record phase'
    assert second['values'] == ['pinned-corpus']
    cached('Mars', 'pinned-corpus')
    cached('Sun', 'another-corpus')
    assert len(calls) == 3
