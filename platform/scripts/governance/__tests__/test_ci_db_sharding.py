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
        plan = mod.partition_job(ROOT, job, count)
        assert all(plan)
        umbrella = jobs['required-'+job]
        assert umbrella['name'] == baseline[job]
        assert sum(j.get('name') == baseline[job] for j in jobs.values()) == 1
        assert umbrella['needs'] == [job]
        assert umbrella['if'] == '${{ always() }}'
        assert not umbrella.get('continue-on-error')
        script = umbrella['steps'][0]['run']
        assert not umbrella['steps'][0].get('continue-on-error')
        for result in ('success','failure','skipped','cancelled',''):
            code = script.replace('${{ needs.'+job+'.result }}', result)
            proc = subprocess.run(['bash', '-e', '-c', code], capture_output=True)
            assert (proc.returncode == 0) == (result == 'success'), (job,result)
    assert discovery.workflow_problems((ROOT / '.github/workflows/ci.yml').read_text()) == []


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
    jobs = yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
    script = next(s['run'] for s in jobs['db-integration-tests']['steps'] if 'mutation_check_1206.py' in s.get('run',''))
    script = '\n'.join(line for line in script.splitlines() if 'ci_discovery.py' not in line)
    script = script.replace('python3 scripts/gochara/mutation_check_1206.py', 'echo MUTATION_RUN')
    calls = 0
    for index in range(1,5):
        proc = subprocess.run(['bash','-e','-c',script.replace('${{ matrix.shard }}',str(index))],capture_output=True,text=True)
        assert proc.returncode == 0
        calls += proc.stdout.count('MUTATION_RUN')
    assert calls == 1


def test_committed_timings_have_recorded_sources_for_every_sharded_job():
    mod = sharding()
    timing = json.loads(mod.TIMINGS.read_text())
    assert timing['schema'] == 'ci.db_shard_timings/1'
    assert timing['sources'], 'balance must be backed by a recorded timing source'
    for job,count in mod.JOB_SHARDS.items():
        files = set(sum(mod.partition_job(ROOT,job,count),[]))
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
