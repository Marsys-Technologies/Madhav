#!/usr/bin/env python3
"""Compare real DB-job node IDs with a pre-sharding workflow on unchanged test sources.

Run from this worktree with a Python that has requirements-ci.txt installed:
  python compare_ci_db_shards.py --baseline REV --scratch "$JOB_SCRATCH" --ephe-path /path/to/ephe

Uses only read-only Git, pytest collection and Vitest list (never DB fixture execution).
Raw collection evidence stays in --scratch; the reviewable comparison is written to --output.
"""
import argparse, collections, hashlib, importlib.util, json, os, re, shlex, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',required=True)
parser.add_argument('--job', action='append', help='Recheck only named jobs; preserve other rows in an existing same-baseline report')
parser.add_argument('--scratch',type=Path,required=True)
parser.add_argument('--ephe-path',type=Path,required=True)
parser.add_argument('--output',type=Path,default=ROOT/'platform/scripts/governance/ci_db_shard_coverage.json')
options=parser.parse_args()
SCRATCH=options.scratch.resolve()
SCRATCH.mkdir(parents=True,exist_ok=True)
(SCRATCH/'tmp').mkdir(exist_ok=True)
(SCRATCH/'collect_nodes.py').write_text('import json,os\nfrom pathlib import Path\ndef pytest_collection_finish(session):\n    Path(os.environ["NODE_OUTPUT"]).write_text(json.dumps([item.nodeid for item in session.items]))\n')
GOV=ROOT/'platform/scripts/governance'
sys.path.insert(0,str(GOV))
import ci_discovery as current
import ci_db_shard as shard
import yaml
base_source=subprocess.check_output(['git','show',options.baseline+':platform/scripts/governance/ci_discovery.py'],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},text=True)
base_path=SCRATCH/'base_ci_discovery.py';base_path.write_text(base_source)
spec=importlib.util.spec_from_file_location('base_discovery',base_path)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base_profiles=json.loads(subprocess.check_output(['git','show',options.baseline+':platform/scripts/governance/ci_test_suites.json'],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},text=True))['suites']
base.profiles=lambda: base_profiles
before=yaml.safe_load(subprocess.check_output(['git','show',options.baseline+':.github/workflows/ci.yml'],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},text=True))['jobs']
after=yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())['jobs']
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':os.pathsep.join([str(SCRATCH),str(GOV)]),'TMPDIR':str(SCRATCH/'tmp'),'NODE_ENV':'test','SE_EPHE_PATH':str(options.ephe_path.resolve()),'GOCHARA_SE1_REQUIRE':'1','KALA_REQUIRE_DB':'1','KALA_ADMIN_DSN':'postgresql://postgres@127.0.0.1:55433/postgres','GOCHARA_A53_REQUIRE_DB':'1','GOCHARA_A53_ADMIN_DSN':'postgresql://postgres@127.0.0.1:55433/postgres'}
# Collection never executes DB fixtures. Do not set GITHUB_ACTIONS: this is a local collection.

def commands(job, mod):
    for step in job['steps']:
        text=step.get('run','').replace('\\\n',' ')
        for line in text.splitlines():
            m=re.search(r'ci_discovery.py" (pytest|vitest) ([\w-]+) --(.*)',line)
            if m:
                mode,key,flags=m.groups();p={**mod.profiles()[key], '_collection_env': {**job.get('env',{}), **step.get('env',{})}}
                yield key,p,mod.discover(ROOT,p),shlex.split(flags)
            elif line.startswith('python -B -m pytest ') or line.startswith('python -m pytest '):
                tokens=shlex.split(line); args=tokens[tokens.index('pytest')+1:]
                index=next((i for i,arg in enumerate(args) if arg.startswith('-')),len(args))
                cwd='platform/python-sidecar'
                files=[str(path.relative_to(ROOT/cwd)) for arg in args[:index] for path in sorted((ROOT/cwd).glob(arg))]
                key='kala-db-tests-5-0' if 'tests/l3/kala_db' in files else 'native-'+str(len(files))
                p={'engine':'pytest','cwd':cwd,'_collection_env':{**job.get('env',{}),**step.get('env',{})}}
                yield key,p,files,args[index:]
            elif line.startswith('npx vitest run '):
                args=shlex.split(line)[3:];i=next((i for i,a in enumerate(args) if a.startswith('-')),len(args))
                yield 'db-integration-tests-7-0',{'engine':'vitest','cwd':'platform','_collection_env':{**job.get('env',{}),**step.get('env',{})}},args[:i],args[i:]

def collect(key,profile,files,flags,tag):
    output=SCRATCH/'collection'/f'{key}-{tag}.json';output.parent.mkdir(exist_ok=True)
    log=output.with_suffix('.log')
    if not files:return []
    fixture_env={}
    for name,value in profile.get('_collection_env',{}).items():
        if name.startswith('CI_DB_'): continue
        value=str(value)
        if 'postgresql://' in value:
            from urllib.parse import urlsplit
            value='postgresql://postgres@127.0.0.1:55433'+urlsplit(value).path
        fixture_env[name]=value
    execution_env={**env, **fixture_env}
    if 'ci_db_node_shard' in flags:
        execution_env.update({name: os.environ[name] for name in ('CI_DB_SHARD_JOB', 'CI_DB_SHARD')})
    if profile['engine']=='pytest':
        cmd=[sys.executable,'-B','-m','pytest',*files,*flags,'--collect-only','-p','no:cacheprovider','-p','collect_nodes','--basetemp='+str(SCRATCH/'collection-tmp'/f'{key}-{tag}')]
        e={**execution_env,'NODE_OUTPUT':str(output)}
    else:
        cmd=['node',str(ROOT/'platform/node_modules/vitest/vitest.mjs'),'list',*files,*flags,'--json='+str(output),'--no-cache','--maxWorkers=1']
        e=execution_env
    with log.open('w') as out:
        proc=subprocess.run(cmd,cwd=ROOT/profile['cwd'],env=e,stdout=out,stderr=subprocess.STDOUT,timeout=180)
    if proc.returncode!=0:
        print(log.read_text()[-5000:],flush=True)
        raise RuntimeError(f'collection failed {key} {tag} ({proc.returncode}), see {log}')
    data=json.loads(output.read_text())
    if profile['engine']=='pytest':return [profile['cwd']+'/'+n for n in data]
    return [str(Path(n['file']).relative_to(ROOT))+'::'+n['projectName']+'::'+n['name'] for n in data]

def digest(nodes):return hashlib.sha256('\n'.join(sorted(nodes)).encode()).hexdigest()

report={'schema':'ci.db_shard_coverage/1','baseline_sha':subprocess.check_output(['git','rev-parse',options.baseline],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},text=True).strip(),'method':'CI step environments with DSNs mapped to the guarded localhost:55433 cluster; pytest --collect-only with the original flags and Vitest list --json --no-cache; same unchanged test sources, original selectors versus actual runtime shard selections (files, or collected node IDs for replace-chain); node IDs include project and full test name for Vitest','jobs':{}}
all_jobs={**shard.JOB_SHARDS,'kala-db-tests':1,'gochara-a55-slice-transitions':1,'gochara-a55-teardown-round2':1}
if options.job:
    if set(options.job) - all_jobs.keys():
        raise ValueError('unknown requested DB job')
    if options.output.exists():
        previous = json.loads(options.output.read_text())
        assert previous['baseline_sha'] == report['baseline_sha'], 'cannot mix coverage baselines'
        report['jobs'] = previous['jobs']
    all_jobs = {job: count for job, count in all_jobs.items() if job in options.job}
report['rechecked_jobs'] = list(all_jobs)
report['retained_jobs'] = sorted(set(report['jobs']) - set(all_jobs))
for job,count in all_jobs.items():
    print(f'Collecting {job} before and {count} shards',flush=True)
    old_nodes=[];new_nodes=[[] for _ in range(count)]
    old_specs={k:(p,f,a) for k,p,f,a in commands(before[job],base)}
    new_specs={k:(p,f,a) for k,p,f,a in commands(after[job],current)}
    assert old_specs.keys()==new_specs.keys(),(job,old_specs.keys()^new_specs.keys())
    plan=shard.partition_job(ROOT,job,count) if job in shard.JOB_SHARDS and job not in shard.NODE_SHARD_JOBS else [[str(Path(p['cwd'])/f) for p,files,a in new_specs.values() for f in files]]
    for key,(p,files,flags) in old_specs.items():
        old_nodes.extend(collect(key,p,files,flags,'before'))
        np,nf,na=new_specs[key]
        assert p['cwd']==np['cwd'] and p['engine']==np['engine'] and flags==na,(key,p,np,flags,na)
        for i in range(count):
            # Call the same production selector as ci_discovery.run, including its fail-closed validation.
            os.environ['CI_DB_SHARD_JOB']=job;os.environ['CI_DB_SHARD']=f'{i+1}/{count}'
            chosen=shard.selected_files(ROOT,key,np,nf) if job in shard.JOB_SHARDS else nf
            shard_flags = list(na)
            if job in shard.NODE_SHARD_JOBS:
                shard_flags += ['-p', 'ci_db_node_shard']
            if np['engine']=='vitest' and job in shard.JOB_SHARDS:
                shard_flags += [arg for path in nf if path not in chosen for arg in ('--exclude',path)]
            new_nodes[i].extend(collect(key,np,chosen,shard_flags,f'shard-{i+1}'))
    flat=sum(new_nodes,[])
    missing=list((collections.Counter(old_nodes)-collections.Counter(flat)).elements())
    extra=list((collections.Counter(flat)-collections.Counter(old_nodes)).elements())
    entry={'before_count':len(old_nodes),'after_count':len(flat),'before_sha256':digest(old_nodes),'after_sha256':digest(flat),'identical':not missing and not extra,'missing':missing,'extra':extra,'shards':[{'index':i+1,'count':len(n),'sha256':digest(n),'files':sorted({n.split('::',1)[0] for n in new_nodes[i]}) if job in shard.NODE_SHARD_JOBS else plan[i]} for i,n in enumerate(new_nodes)],'node_ids':sorted(old_nodes)}
    report['jobs'][job]=entry
    options.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert entry['identical'],(job,missing,extra)
    print(f'{job}: {len(old_nodes)} == {len(flat)}, exact multiset equality',flush=True)
print('All job node-ID multisets identical',flush=True)
