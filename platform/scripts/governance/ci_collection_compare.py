#!/usr/bin/env python3
"""Reproduce the A5 D-33 selector-containment certificate from the proposed tree.

Run from any directory with JOB_SCRATCH set to an owned scratch folder. Requires the
usual CI dependencies and installed platform / platform-mcp packages. Uses the local
Swiss corpus, no database fixtures, no Git writes, and bounded Vitest workers.
The unchanged native Unit Tests command is certified by identity; counts cover C.
"""
import pathlib,os,json,sys,shlex,subprocess,re,time,hashlib

def main():
    root=pathlib.Path(__file__).resolve().parents[3]; scratch=pathlib.Path(os.environ['JOB_SCRATCH']);sys.path.insert(0,str(root/'platform/scripts/governance'))
    import ci_discovery as discovery
    import yaml
    old_jobs=yaml.safe_load(subprocess.check_output(['git','show',json.loads((root/'platform/scripts/governance/ci_discovery_baseline.json').read_text())['source_revision']+':.github/workflows/ci.yml'],cwd=root,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},text=True))['jobs']
    baseline=json.loads((root/'platform/scripts/governance/ci_discovery_baseline.json').read_text())
    profiles=discovery.profiles();before=set();after=set();rows=[]; cache={}
    cache_path=scratch/'collection-cache.json'
    persistent={}
    # Vitest 2 needs a bounded minimum; these env knobs also work with the Vitest 4 collector.
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','SE_EPHE_PATH':'/Users/Dev/kalayantra/ephe','SWE_EPHE_PATH':'/Users/Dev/kalayantra/ephe','TMPDIR':str(scratch/'tmp'),'NPM_CONFIG_CACHE':str(scratch/'npm-cache'),'CI':'true','TSX_DISABLE_CACHE':'1','GIT_OPTIONAL_LOCKS':'0','VITEST_MIN_THREADS':'1','VITEST_MIN_FORKS':'1'}
    # Collection never uses fixtures; strip connection-bearing variables so import-time code cannot contact anything remote.
    for key in list(env):
     if key.endswith(('_DSN','_DATABASE_URL')) or key in ('DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD'):env.pop(key)
    env['PYTHONPATH']=os.pathsep.join([str(root/'platform/scripts/governance/pytest_plugins'),str(scratch/'python-deps'),str(root/'platform/scripts/governance'),str(root/'platform/scripts/governance/pytest_plugins')])

    def options(c):
     args=shlex.split(c['line'].split(c['exe'],1)[1]); paths=c['paths'];args=args[len(paths):];out=[];i=0
     while i<len(args):
      a=args[i]
      if a in ('-m','--deselect','--ignore','--ignore-glob'):
       out.extend(args[i:i+2]);i+=2;continue
      if a.startswith(('--ignore=','--ignore-glob=','--deselect=')):out.append(a)
      i+=1
     return out

    def collect(c,paths,tag):
     opts=options(c)
     if tag.endswith(' after') and c['engine']=='vitest':
      opts += [arg for path in profiles[c['suite']].get('quarantine',{}) for arg in ('--exclude',path)]
     sources=[]
     for token in paths:
      target=root/c['cwd']/token.split('::')[0]
      if target.is_dir():
       sources.extend((str(p.relative_to(root)),p.stat().st_mtime_ns) for p in target.rglob('*') if p.is_file() and ('test' in p.name or '.spec.' in p.name) and 'node_modules' not in p.parts)
      elif target.is_file():sources.append((str(target.relative_to(root)),target.stat().st_mtime_ns))
     key=(c['suite'],c['cwd'],c['engine'],tuple(paths),tuple(opts))
     persistent_key=hashlib.sha256(json.dumps([key,sources]).encode()).hexdigest()
     if persistent_key in persistent:return set(persistent[persistent_key])
     if key in cache:return cache[key]
     index=len(cache);log=scratch/f'collection-{index}.log'
     if c['engine']=='pytest':
      target=scratch/f'collection-{index}.json';childenv={**env,'KY_COLLECTION_OUT':str(target)}
      cmd=[sys.executable,'-m','pytest',*paths,*opts,'--collect-only','-q','-p','no:cacheprovider','-p','ci_capture','--disable-warnings','--basetemp',str(scratch/f'collect-tmp-{index}')]
     else:
      childenv=env;cmd=['npx','--no-install','vitest','list',*paths,*opts,'--json','--no-cache','--maxWorkers=4']
     childenv=dict(childenv)
     if 'job' in c:
      job=old_jobs[c['job']];step=job['steps'][c['step']]
      for name,value in {**job.get('env',{}),**step.get('env',{})}.items():
       value=str(value)
       if '${{' in value:continue
       if name.endswith(('_DSN','_DATABASE_URL')) or name=='DATABASE_URL':value='postgresql://postgres@127.0.0.1:55433'+__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(value).path
       childenv[name]=value
     childenv['PYTHONPATH']=env['PYTHONPATH']+os.pathsep+childenv.get('PYTHONPATH','')
     worker=subprocess.Popen(cmd,cwd=root/c['cwd'],env=childenv,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
     try:
      stdout,stderr=worker.communicate(timeout=600)
     except subprocess.TimeoutExpired:
      import signal
      os.killpg(worker.pid,signal.SIGTERM)
      try:worker.communicate(timeout=5)
      except subprocess.TimeoutExpired:os.killpg(worker.pid,signal.SIGKILL);worker.communicate()
      raise RuntimeError(f'{tag}: collection timed out; process tree stopped')
     proc=subprocess.CompletedProcess(cmd,worker.returncode,stdout,stderr)
     log.write_text(proc.stdout+proc.stderr)
     if proc.returncode:
      raise RuntimeError(f'{tag}: collection exit {proc.returncode}; see {log}')
     if c['engine']=='pytest': ids=json.loads(target.read_text())
     else:
      text=proc.stdout;start=re.search(r'\[\s*(?:\{|\])',text).start()
      parsed=json.JSONDecoder().raw_decode(text[start:])[0];ids=[str(pathlib.Path(x['file']).relative_to(root/c['cwd']))+'::'+x['name'] for x in parsed]
     result={c['cwd'].rstrip('/')+'/'+node for node in ids};cache[key]=result
     persistent[persistent_key]=sorted(result);cache_path.write_text(json.dumps(persistent))
     return result

    for idx,c in enumerate(baseline['commands']):
     old=collect(c,c['paths'],c['suite']+' before');new=collect(c,discovery.discover(root,profiles[c['suite']]),c['suite']+' after')
     missing=sorted(old-new)
     if missing:raise RuntimeError(f"{c['suite']} dropped {missing[:5]}")
     before|=old;after|=new;rows.append({'suite':c['suite'],'before':len(old),'after':len(new),'missing':missing})
     print(f"{idx+1}/{len(baseline['commands'])} {c['suite']}: {len(old)} -> {len(new)}",flush=True)
    # Unchanged directory jobs and whole-suite unit tests. Preserve their marker/exclusion selections.
    unchanged=[
     {'suite':'samiksha','cwd':'platform','engine':'vitest','paths':['tests/pariprashna/samiksha','src/lib/pariprashna/samiksha'],'exe':'npx vitest run','line':'npx vitest run tests/pariprashna/samiksha src/lib/pariprashna/samiksha'},
     {'suite':'planner-regression','cwd':'platform','engine':'vitest','paths':['tests/planner'],'exe':'npx vitest run','line':'npx vitest run tests/planner'},
     {'suite':'governance-shards-full','cwd':'.','engine':'pytest','paths':['platform/scripts/governance/__tests__'],'exe':'pytest','line':'pytest platform/scripts/governance/__tests__'},
     {'suite':'muhurta','cwd':'platform/python-sidecar','engine':'pytest','paths':['tests/l3/ka_muhurta_seva'],'exe':'pytest','line':'pytest tests/l3/ka_muhurta_seva'},
     {'suite':'compact','cwd':'platform/python-sidecar','engine':'pytest','paths':['tests/l3/ka_kshetra/compact'],'exe':'pytest','line':'pytest tests/l3/ka_kshetra/compact'},
     {'suite':'gochara-fast','cwd':'platform/python-sidecar','engine':'pytest','paths':['services/gochara_v3/mechanisms/tests','services/ka_gochara_resonance/tests','scripts/kala_admission/tests','services/gochara_v3/tests'],'exe':'pytest','line':'pytest services/gochara_v3/mechanisms/tests services/ka_gochara_resonance/tests scripts/kala_admission/tests services/gochara_v3/tests -m "not integration and not slow_real_ephemeris and not benchmark"'},
     {'suite':'gochara-slow','cwd':'platform/python-sidecar','engine':'pytest','paths':[p for entry in old_jobs['governance-gates-gochara']['strategy']['matrix']['include'] for p in entry.get('shard_files','').split()],'exe':'pytest','line':'pytest '+' '.join(p for entry in old_jobs['governance-gates-gochara']['strategy']['matrix']['include'] for p in entry.get('shard_files','').split())+' -m slow_real_ephemeris'},
     {'suite':'gochara-benchmark','cwd':'platform/python-sidecar','engine':'pytest','paths':['services/gochara_v3/tests'],'exe':'pytest','line':'pytest services/gochara_v3/tests -m benchmark'},
    ]
    for c in unchanged:
     ids=collect(c,c['paths'],c['suite'])
     if c['suite']=='gochara-slow':
      slow_after=collect(c,discovery.slow_files(root),'gochara-slow after');assert ids <= slow_after;after|=slow_after
     before|=ids;after|=ids;rows.append({'suite':c['suite'],'before':len(ids),'after':len(ids),'missing':[]});print(c['suite'],len(ids),flush=True)
    new_jobs=yaml.safe_load((root/'.github/workflows/ci.yml').read_text())['jobs']
    native='npm test -- --reporter=verbose'
    assert any(step.get('run')==native for step in old_jobs['unit-tests']['steps'])
    assert any(step.get('run')==native for step in new_jobs['unit-tests']['steps'])
    assert old_jobs['unit-tests']['env']==new_jobs['unit-tests']['env']
    identity_files={}
    for path in ['platform/package.json','platform/vitest.config.ts']:
     old=subprocess.check_output(['git','show',baseline['source_revision']+':'+path],cwd=root,env=env)
     assert old==(root/path).read_bytes()
     identity_files[path]=hashlib.sha256(old).hexdigest()
    report={'schema':'ci.collection_comparison/1','source_revision':baseline['source_revision'],'method':'Real pytest --collect-only (after marker/deselect) and vitest list --json; fixture environments are independently pinned by governance tests. Unchanged directory selections collected once, included in both sets. No database fixtures execute. All 5 governance shards and 4 sidecar shards are compared as their complete unions.','collection_scope':'Materialized C: every changed explicit selector plus directory suites below. U: the unchanged native Unit Tests command is certified by identity, not included in these numeric counts. Both selectors are collected on the proposed source tree.', 'full_ci_superset_proof':{'formula':'C_before subset C_after => (C_before union U) subset (C_after union U)', 'C_subset_verified':before<=after,'U_identity':{'job':'unit-tests','cmd':native,'cwd':'platform','env':old_jobs['unit-tests']['env'],'unchanged_config_sha256':identity_files},'local_limitation':'Whole-platform Vitest list timed out at 180s and 600s; the native Unit Tests invocation and its configuration have no selection edit.'}, 'collected_before':len(before),'collected_after':len(after),'missing':sorted(before-after),'suites':rows,'before_nodeids':sorted(before),'after_nodeids':sorted(after)}
    import gzip
    path=root/'00_ARCHITECTURE/briefs/kalayantra/CI_DISCOVERY_COLLECTION_COMPARISON.json'
    for label,nodes in [('before',before),('after',after)]:
     payload=('\n'.join(sorted(nodes))+'\n').encode()
     target=path.with_name('CI_DISCOVERY_'+label.upper()+'.nodeids.txt.gz')
     target.write_bytes(gzip.compress(payload,mtime=0))
     report[label+'_nodeids']={'path':str(target.relative_to(root)), 'sha256':hashlib.sha256(payload).hexdigest()}
    report['nodeid_format']='collection working directory / native pytest nodeid or Vitest file::name'
    report['profile_sha256']=hashlib.sha256((root/'platform/scripts/governance/ci_test_suites.json').read_bytes()).hexdigest()
    report['required_checks_unchanged']=all(old_jobs[key].get('name',key)==__import__('yaml').safe_load((root/'.github/workflows/ci.yml').read_text())['jobs'][key].get('name',key) for key in old_jobs)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('COMPARISON',len(before),len(after),'missing',len(before-after),flush=True)

if __name__ == "__main__":
    main()
