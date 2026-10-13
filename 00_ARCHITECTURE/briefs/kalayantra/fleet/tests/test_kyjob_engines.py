"""KV3-B-KYJOB-ENGINES: fake programs/tools only; no Git mutation or live service.

The tool double models Git objects, remote refs, PRs and tracker events. Crashes
happen after the effect and before kyaction records it. Production observers must
prove those effects, rather than trusting the double's exit status.
"""
import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

FLEET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLEET))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kyd_jobs as J
import kyqualify as Q
import kyboot as B
import kyaction as ka
import test_kyjob as legacy
from dispatch.test_kyd_jobs import Ctx, World as JobsWorld, Crash

A, H, TREE = 'a' * 40, 'b' * 40, 'c' * 40


def baseline_launcher(folder):
    path=Path(folder)/'accepted-kyjob.sh'
    source='16565d549c390753d7e454aac56ccad2c8fe94b0:00_ARCHITECTURE/briefs/kalayantra/fleet/kyjob.sh'
    read=subprocess.run(['/usr/bin/git','-C',str(FLEET.parents[3]),'show',source],capture_output=True,
                        env={'PATH':'/usr/bin:/bin','GIT_OPTIONAL_LOCKS':'0'},timeout=30)
    assert read.returncode==0, 'accepted KYJOB baseline object must be readable'
    path.write_bytes(read.stdout)
    return path


def adapter():
    assert (FLEET / 'kyjob_engines.py').exists(), 'engine adapter is absent'
    return importlib.import_module('kyjob_engines')


def config(w, verifier=False):
    return dict(schema='ky.launch_config/1', engine='codex', role=w.state['role'],
                model='gpt-6.1-sol', effort='high', sandbox='workspace-write', network=False,
                deadline_seconds=7200, worktree=str(w.worktree), codex_bin=str(w.program),
                codex_min_version='0.162.0', prompt_path=w.state['prompt_path'],
                env_names=['HOME','USER','LANG','TERM','PATH','TMPDIR','JOB_SCRATCH'],
                child_path=w.child_path(), writable_dirs=[],
                **({'work_root':'job'} if verifier else {'commit_mode':'launcher'}))


def codex_world(tmp_path, mode='locked', verifier=False):
    w = legacy.World(tmp_path)
    w.build()
    for name in ['kyjob_engines.py','kyqualify.py','kyboot.py','kyprobe.py','kyloop.py','kyaction.py','kyschema.py','kyroute.py']:
        if (FLEET / name).exists(): shutil.copyfile(FLEET / name, w.fleet / name)
    shutil.copytree(FLEET / 'schemas', w.fleet / 'schemas')
    w.program.write_bytes((FLEET / 'tests/fixtures/b0c_engines/fake_codex_ok.sh').read_bytes())
    w.program.chmod(0o755)
    # Read-only Git worktree discovery, pointing at this job's existing linked repo.
    (w.worktree / '.git').write_bytes((FLEET.parents[3] / '.git').read_bytes())
    for key in ['claude_bin','permission_mode','max_turns','mcp_config']:
        w.state[key] = None
    w.state.update(extra_lean_flags=[],disallowed_tools=[],engine='codex',sandbox_mode=mode,
                   model='gpt-6.1-sol',stall_seconds=300)
    if verifier: w.state.update(kind='VERIFY',boundary='verifier')
    cfg = config(w, verifier)
    cfg_path = w.job_scratch / 'launch.json'
    legacy.write_json(cfg_path, cfg)
    w.state['launch_config_path'] = str(cfg_path)
    legacy.write_json(w.state_path, w.state)
    return w, cfg


@pytest.mark.parametrize('engine', [None,'unknown',42])
def test_unknown_engine_or_mixed_config(tmp_path,engine):
    w = legacy.World(tmp_path).build()
    w.state['engine'] = engine
    legacy.write_json(w.state_path,w.state)
    done = w.launch()
    assert done.code == 65 and w.record() is None


def test_mixed_codex_config(tmp_path):
    w,cfg=codex_world(tmp_path)
    cfg['claude_bin']=str(w.program)
    legacy.write_json(w.state['launch_config_path'],cfg)
    assert w.launch().code == 65


@pytest.mark.parametrize('explicit',[False,True])
def test_claude_bytes_changed(tmp_path,explicit):
    w=legacy.World(tmp_path).build()
    baseline=baseline_launcher(w.base)
    shutil.copyfile(baseline,w.fleet/'kyjob.sh')
    first=w.launch()
    old=w.record()
    old_logs=[Path(w.state[k]).read_bytes() for k in ['stdout_path','stderr_path']]
    old_launch=json.loads((w.job_scratch/'kyjob.launch.json').read_text())
    shutil.copyfile(FLEET/'kyjob.sh',w.fleet/'kyjob.sh')
    if explicit:
        w.state['engine']='claude'
        legacy.write_json(w.state_path,w.state)
    second=w.launch()
    new=w.record()
    # PID/PGID are necessarily allocated anew: measure the same-process predicate.
    assert old['pid']==first.pid and new['pid']==second.pid
    assert old['pgid']==new['pgid'] and old['sid']==new['sid']
    for r in (old,new): r.pop('pid')
    assert json.dumps(old,sort_keys=True).encode()==json.dumps(new,sort_keys=True).encode()
    assert old_logs==[Path(w.state[k]).read_bytes() for k in ['stdout_path','stderr_path']]
    new_launch=json.loads((w.job_scratch/'kyjob.launch.json').read_text())
    old_launch.pop('at'); new_launch.pop('at')
    assert old_launch==new_launch and first.code==second.code==0


@pytest.mark.parametrize('mode',['locked','full'])
@pytest.mark.parametrize('verifier',[False,True])
def test_full_argv_or_record_changed(tmp_path,mode,verifier):
    w,cfg=codex_world(tmp_path,mode,verifier)
    done=w.launch()
    assert done.code==0,done.err
    actual=(w.job_scratch/'tmp/fake_argv.txt').read_text().splitlines()
    expected=Q.build_argv(cfg,str(w.job_scratch))[1:]
    if mode=='full':
        expected[expected.index('-s')+1]='danger-full-access'
        for flag in ['sandbox_workspace_write.network_access=false','sandbox_workspace_write.exclude_slash_tmp=true']:
            i=expected.index(flag); del expected[i-1:i+1]
    assert actual==expected
    assert '--max-turns' not in actual
    assert (w.job_scratch/'tmp/fake_stdin.txt').read_bytes()==w.prompt()
    assert int((w.job_scratch/'tmp/fake_pgid.txt').read_text())==os.getpgrp()
    record=json.loads((w.job_scratch/'kyjob.launch.json').read_text())
    assert record['engine']=='codex' and record['sandbox_mode']==mode
    assert record['sandbox']==('full (owner direction 2026-10-12)' if mode=='full' else 'locked')
    if verifier:
        assert [c.split()[0] for c in w.boundary_calls()]==['prepare','exec']
        assert actual[actual.index('-C')+1]==str(w.job_scratch)


def test_full_without_explicit_selection(tmp_path):
    w,cfg=codex_world(tmp_path)
    cfg['sandbox']='danger-full-access'
    legacy.write_json(w.state['launch_config_path'],cfg)
    assert w.launch().code==65


@pytest.mark.parametrize('field,value',[('engine','claude'),('model','wrong'),('effort','xhigh'),('network',True),('writable_dirs',['/tmp'])])
def test_config_identity_and_roots(tmp_path,field,value):
    w,cfg=codex_world(tmp_path)
    cfg[field]=value
    legacy.write_json(w.state['launch_config_path'],cfg)
    assert w.launch().code==65


def result(job,status='done'):
    return dict(schema='ky.job_result/1',job_id=job['job_id'],item=job['item'],status=status,
                tests=[],commit_message='engine change\n\nBody.',blocked_reason='blocked here' if status=='blocked' else None,notes='')


@pytest.mark.parametrize('change',[{}, {'branch':None},{'head_sha':None},{'pr_number':None},{'job_id':'other'}, {'item':'other'}, {'commit_message':None}])
def test_result_schema_or_identity(tmp_path,change):
    job=dict(job_id='J-test',item='KV3-T',kind='BUILD',engine='codex',job_scratch=str(tmp_path))
    legacy.write_json(tmp_path/'result.json',dict(result(job),**change))
    doc=J._result(job)
    assert (doc is not None)==(not change)
    if not change:
        (tmp_path/'result.json').rename(tmp_path/'other.json')
        (tmp_path/'result.json').symlink_to(tmp_path/'other.json')
        assert J._result(job) is None


class Landing:
    def __init__(self,tmp_path,monkeypatch):
        self.world=JobsWorld(tmp_path,monkeypatch)
        self.ctx=self.world.ctx
        self.job=J.open(self.ctx,self.world.intent({'item':'KV3-T'}),'k1',self.world.facts({}))
        self.job.update(engine='codex',sandbox_mode='full',stall_seconds=300,
                        phase='terminating',exit_code=0,result_event={'type':'turn.completed'},
                        pid=123456,pgid=123456,process_start='owned')
        self.wt=Path(self.job['worktree'])
        (self.wt/'.git').write_text('gitdir: /observed/git\n')
        self.packet=Path(self.job['packet_path'])
        self.packet.write_text('```json\n'+json.dumps({'id':self.job['item'],'kind':'bootstrap','d1_paths':['src/a.py','src/b.py']})+'\n```\n')
        self.head=A; self.parent=A; self.tree=TREE; self.message=''; self.remote=None
        self.status=' M src/a.py\0'; self.index=''; self.prs=[]; self.events=[dict(kind='claim',state='acquired',claim_id=self.job['claim_id'],actor='stream-K:k1')]
        self.calls=[]; self.crash=None; self.command_fail=None; self.guards={'git':{'common_dir':'/observed','config_files':{},'worktree_entries':[], 'own':{},'hooks':{}}}
        monkeypatch.setattr(B,'codex_guards',lambda launch,env: copy.deepcopy(self.guards))
        monkeypatch.setattr(J,'_process',lambda job:'gone')
        self.ctx.sh=self.sh
        self.original_ky=self.ctx.ky
        self.ctx.ky=self.ky
        self.ctx.events=lambda item: copy.deepcopy(self.events)
        legacy.write_json(Path(self.job['job_scratch'])/'result.json',result(self.job))
        self.E=adapter()
        self.E.prepare(self.ctx,self.job)
        J._save(self.ctx,self.job)

    def cleanup(self): self.world.cleanup()

    def sh(self,argv,env=None,cwd=None,timeout=120):
        args=list(map(str,argv)); self.calls.append(args)
        if self.command_fail and self.command_fail in args: return 1,'','conflict with origin/main'
        out=''
        if args[0] in ('git','/usr/bin/git'):
            a=args[3:]
            if a[:2]==['rev-parse','HEAD']: out=self.head+'\n'
            elif a[:2]==['rev-parse','HEAD^']: out=self.parent+'\n'
            elif a[:2]==['rev-parse','HEAD^{tree}']: out=self.tree+'\n'
            elif a[:2]==['rev-parse','--absolute-git-dir']: out='/observed/git\n'
            elif a[:2]==['rev-parse','--abbrev-ref']: out=self.job['branch']+'\n'
            elif a[:2]==['rev-parse','--verify']: out=A+'\n'
            elif a[0]=='status': out=self.status
            elif a[:2]==['diff','--cached']: out=self.index
            elif a[:2]==['diff','--exit-code']: out=''
            elif a[0]=='write-tree': out=self.tree+'\n'
            elif a[0]=='show': out=self.message if '%B' in ' '.join(a) else self.tree+'\n'+self.parent+'\n'
            elif a[0]=='ls-remote': out=(self.remote+'\trefs/heads/'+self.job['branch']+'\n') if self.remote else ''
            elif a[0]=='add': self.index=''.join(p+'\0' for p in a[a.index('--')+1:])
            elif a[0]=='commit':
                self.message=Path(a[a.index('-F')+1]).read_text(); self.head=H; self.status=''; self.index=''
            elif a[0]=='push': self.remote=self.head
            elif a[0]=='merge-tree': out=self.tree+'\n'
            else: raise AssertionError('unexpected Git command '+repr(a))
        elif args[0] in ('gh','/opt/homebrew/bin/gh'):
            if args[1:3]==['pr','list']: out=json.dumps(self.prs)
            elif args[1:3]==['pr','create']:
                self.prs=[dict(number=27,headRefName=self.job['branch'],headRefOid=self.head,baseRefName='main',mergeable='MERGEABLE')]; out='https://example.test/pull/27\n'
            else: raise AssertionError(args)
        else: raise AssertionError(args)
        if self.crash and self.crash in args:
            self.crash=None; raise Crash('after effect before action record')
        return 0,out,''

    def ky(self,*args,stream=None,lane=None):
        if args[0]=='show': return 0,json.dumps({'events':self.events,'item':{'id':self.job['item'],'state':'claimed'}}),''
        if args[0] in ('review','block'):
            self.events.append(dict(kind='item',state='review' if args[0]=='review' else 'blocked',
                                    actor='stream-%s:%s'%(stream,lane),detail=args[args.index('--detail')+1]))
            if self.crash==args[0]: self.crash=None; raise Crash('after tracker event')
            return 0,'',''
        return self.original_ky(*args,stream=stream,lane=lane)

    def finish(self): return self.E.finish(self.ctx,self.job,J._result(self.job))


@pytest.fixture
def land(tmp_path,monkeypatch):
    l=Landing(tmp_path,monkeypatch)
    try: yield l
    finally: l.cleanup()


def writes(l): return [a for a in l.calls if any(v in a for v in ['add','commit','push','create'])]


def test_landing_and_registration(land):
    raw=(Path(land.job['job_scratch'])/'result.json').read_bytes()
    assert land.finish()['outcome']=='done'
    assert land.job['head']==H and land.job['pr']==27 and land.job['registered_head']==H
    assert land.events[-1]['detail']=='PR #27 @ '+H
    assert land.events[-1]['actor']=='stream-K:k1'
    assert (Path(land.job['job_scratch'])/'result.json').read_bytes()==raw
    before=copy.deepcopy(writes(land))
    assert land.finish()['outcome']=='done'
    assert writes(land)==before


@pytest.mark.parametrize('drift',['head','remote'])
def test_builder_commit_or_push(land,drift):
    setattr(land,drift,H)
    assert land.finish()['outcome']=='failed'
    assert not writes(land)


def test_git_pointer_redirect(land):
    (land.wt/'.git').write_text('gitdir: /different\n')
    land.calls.clear()
    assert land.finish()['outcome']=='failed'
    assert land.calls==[]


@pytest.mark.parametrize('case',['exit','turn','group','guards'])
def test_exit_turn_or_group_not_clean(land,monkeypatch,case):
    if case=='exit': land.job['exit_code']=1
    elif case=='turn': land.job['result_event']={'type':'turn.failed'}
    elif case=='group': monkeypatch.setattr(J,'_process',lambda j:'survivors')
    else: land.guards['git']['own']['pointer']='changed'
    assert land.finish()['outcome'] in ['failed','held']
    assert not writes(land)


@pytest.mark.parametrize('case',['scope','rename','queue','packet','index'])
def test_scope_or_queue_authorisation(land,case):
    if case=='scope': land.status='?? outside.py\0'
    elif case=='rename': land.status='R  src/a.py\0outside.py\0'
    elif case=='queue': land.job['queue_authorised']=True
    elif case=='packet': land.packet.write_text('changed')
    else: land.index='outside.py\0'
    assert land.finish()['outcome']=='failed'
    assert not writes(land)


def test_origin_main_conflict_no_merge(land):
    land.command_fail='merge-tree'
    r=land.finish()
    assert r['outcome']=='blocked' and 'origin/main' in r['detail']
    assert not writes(land)
    assert not any('merge' in a for a in land.calls)


@pytest.mark.parametrize('case',['claim','actor','head','pr'])
def test_claim_actor_head_pr_mismatch(land,case):
    if case=='claim':
        p=land.world.run/'claims/k1.json'; d=json.loads(p.read_text()); d['claim_id']='foreign'; legacy.write_json(p,d)
    else:
        land.prs=[dict(number=27,headRefName=land.job['branch'],headRefOid=H if case!='head' else A,baseRefName='other' if case=='pr' else 'main',mergeable='MERGEABLE')]
        if case=='actor':
            land.events.append(dict(kind='item',state='review',actor='stream-K:other',detail='PR #27 @ '+H))
    assert land.finish()['outcome'] in ['failed','held']


@pytest.mark.parametrize('step',['add','commit','push','create','review'])
def test_restart_each_finish_step(land,step):
    land.crash=step
    with pytest.raises(Crash): land.finish()
    land.ctx.controller_id='CTL-restarted'
    land.job=J._fresh(land.ctx,land.job)
    assert land.finish()['outcome']=='done'
    for verb in ['commit','push','create']:
        assert sum(verb in a for a in land.calls)==1, (verb,land.calls)
    assert sum(e.get('state')=='review' for e in land.events)==1


def test_blocked_result_registers_block(land):
    legacy.write_json(Path(land.job['job_scratch'])/'result.json',result(land.job,'blocked'))
    assert land.finish()['outcome']=='blocked'
    assert land.events[-1]['state']=='blocked' and not writes(land)


def test_activity_growth_and_restart(tmp_path):
    E=adapter()
    job=dict(engine='codex',sandbox_mode='locked',stall_seconds=10,checkpoint={},
             stdout_path=str(tmp_path/'out'),stderr_path=str(tmp_path/'err'))
    for k in ['stdout_path','stderr_path']: Path(job[k]).write_text('')
    assert not E.stalled(job,100)
    os.utime(job['stdout_path'],None)
    assert not E.stalled(job,109)
    restarted=json.loads(json.dumps(job))
    assert E.stalled(restarted,110)
    Path(job['stderr_path']).write_text('activity')
    assert not E.stalled(job,111)
    assert not E.stalled(job,120)
    assert E.stalled(job,121)


@pytest.mark.parametrize('engine',[None,'wrong'])
def test_controller_refuses_unknown_engine(tmp_path,monkeypatch,engine):
    w=JobsWorld(tmp_path,monkeypatch)
    try:
        facts=w.facts({})
        facts['launch']['engine']=engine
        assert J.open(w.ctx,w.intent({'item':'KV3-T'}),'k1',facts) is None
        assert not w.log.ky
    finally: w.cleanup()


def test_controller_preserves_header_precedence(tmp_path,monkeypatch):
    w=JobsWorld(tmp_path,monkeypatch)
    try:
        intent=w.intent({'item':'KV3-T','header':dict(engine='codex',sandbox_mode='full',stall_seconds=12,
                         launch_config_path=str(tmp_path/'config.json'),claude_bin=None,permission_mode=None,
                         max_turns=None,mcp_config=None,extra_lean_flags=[],disallowed_tools=[])})
        facts=w.facts({}); facts['launch']['engine']='claude'
        plan,why=J._plan(w.ctx,intent,'k1',facts)
        assert why is None
        assert plan['state']['engine']=='codex' and plan['state']['sandbox_mode']=='full'
        assert plan['state']['stall_seconds']==12
    finally: w.cleanup()


def test_stall_term_ignoring_child(tmp_path,monkeypatch):
    w=JobsWorld(tmp_path,monkeypatch)
    try:
        job=J.open(w.ctx,w.intent({'item':'KV3-T'}),'k1',w.facts({}))
        s=Path(job['job_scratch'])
        (w.fleet/'kyjob.sh').write_text('#!/bin/bash\ntrap "" TERM\n/bin/sleep 600 &\necho $! > "$KY_SCRATCH/jobs/$1/tool.pid"\nwait\n')
        monkeypatch.setattr(adapter(),'prepare',lambda ctx,j:None)
        job.update(engine='codex',sandbox_mode='full',stall_seconds=0.15)
        J._save(w.ctx,job)
        job=J.launch(w.ctx,job)
        proc=J._CHILDREN[job['job_id']]
        w.procs[job['job_id']]=proc; w.lstart[proc.pid]=job['process_start']
        end=time.time()+5
        while not (s/'tool.pid').exists() and time.time()<end: time.sleep(.02)
        assert (s/'tool.pid').exists()
        time.sleep(.2)
        stopped=J.supervise(w.ctx)
        assert stopped and stopped[0]['failure_fp']=='codex_stalled'
        assert stopped[0]['outcome']=='failed' and J._process(stopped[0])=='gone'
        ended=J.close(w.ctx,stopped[0])
        assert ended['phase']=='ended' and ended['outcome']=='failed'
        assert ended['checkpoint']['codex_activity']['reason']=='codex_stalled'
        assert json.loads((w.run/'claims/k1.json').read_text())['state']=='released'
        assert not (w.run/'locks/item.KV3-T').exists()
    finally: w.cleanup()


def test_locked_socket_job_failure(land):
    land.job.update(sandbox_mode='locked',exit_code=1,result_event={'type':'turn.failed','error':'socket denied'})
    r=land.finish()
    assert r['outcome']=='failed' and r['sandbox_mode']=='locked'
    assert not writes(land)


def test_unknown_guard_refuses(land):
    before = copy.deepcopy(land.guards)
    land.guards['git'] = None
    assert land.finish()['outcome'] == 'held'
    assert not writes(land)
    assert json.loads((land.world.run / 'claims/k1.json').read_text())['state'] == 'acquired'
    assert (land.world.run / 'locks/item.KV3-T').exists()
    land.guards = before
    assert land.finish()['outcome'] == 'done'


@pytest.mark.parametrize('case',['queue_file','live_queue','claim_actor','lock','unknown_remote'])
def test_fresh_landing_fences(land,case):
    if case=='queue_file':
        p=land.world.run/'merge_requests/queued/KV3-T.json'; p.parent.mkdir(parents=True); p.write_text('{}')
    elif case=='live_queue':
        land.prs=[dict(number=27,headRefName=land.job['branch'],headRefOid=A,baseRefName='main',mergeable='MERGEABLE',autoMergeRequest={'enabledAt':'now'})]
    elif case=='claim_actor': land.events[0]['actor']='stream-K:foreign'
    elif case=='lock':
        p=land.world.run/'locks/item.KV3-T/owner.json'; d=json.loads(p.read_text()); d['session_or_run_id']='foreign'; legacy.write_json(p,d)
    else:
        old=land.ctx.sh
        land.ctx.sh=lambda a,**kw: (None,'','unobservable') if 'ls-remote' in a else old(a,**kw)
    r=land.finish()
    assert r['outcome'] in ('failed','held')
    assert not writes(land)


def test_resulting_commit_conflicts_with_main(land):
    old=land.ctx.sh
    def conflicting(argv,**kw):
        if 'merge-tree' in argv and land.head==H: return 1,'','new patch conflicts'
        return old(argv,**kw)
    land.ctx.sh=conflicting
    assert land.finish()['outcome']=='blocked'
    assert not any('push' in a for a in land.calls)
    assert land.head==H


def test_unrecorded_commit_cannot_be_reused_if_message_differs(land):
    land.crash='commit'
    with pytest.raises(Crash): land.finish()
    land.message='foreign message\n'
    land.ctx.controller_id='CTL-restarted'
    land.job=J._fresh(land.ctx,land.job)
    assert land.finish()['outcome']=='held'
    assert sum('commit' in a for a in land.calls)==1
    assert not any('push' in a for a in land.calls)


def test_collection_runs_landing_before_release(land):
    out=Path(land.job['stdout_path'])
    out.write_text('{"type":"thread.started","thread_id":"thread-observed"}\n{"type":"turn.completed","usage":{}}\n')
    # A process handle owned by this controller is the producer of observed exit 0.
    class Exited:
        def poll(self): return 0
    J._CHILDREN[land.job['job_id']]=Exited()
    J._collect(land.ctx,land.job)
    assert land.job['provider_session_id']=='thread-observed'
    assert land.job['outcome']=='done'
    assert land.events[-1]['state']=='review'
    ended=J.close(land.ctx,land.job)
    assert ended['phase']=='ended' and ended['outcome']=='done'
    assert not (land.world.run/'locks/item.KV3-T').exists()
    assert json.loads((land.world.run/'claims/k1.json').read_text())['state']=='released'


def test_unknown_finish_retains_claim_locks_and_resumes(land):
    class Exited:
        def poll(self): return 0
    Path(land.job['stdout_path']).write_text('{"type":"turn.completed"}\n')
    old=land.ctx.sh
    land.ctx.sh=lambda a,**kw: (None,'','unknown') if 'ls-remote' in a else old(a,**kw)
    J._CHILDREN[land.job['job_id']]=Exited()
    J._collect(land.ctx,land.job)
    held=J.close(land.ctx,land.job,{'outcome':'interrupted'})
    assert held['phase']=='terminating'
    assert (land.world.run/'locks/item.KV3-T').exists()
    assert json.loads((land.world.run/'claims/k1.json').read_text())['state']=='acquired'
    land.ctx.sh=old
    ended=J.close(land.ctx,held)
    assert ended['phase']=='ended' and ended['outcome']=='done'


@pytest.mark.parametrize('mode',['locked','full'])
def test_process_and_loopback_mode(tmp_path,mode):
    w,cfg=codex_world(tmp_path,mode)
    w.program.write_text('#!'+legacy._own_program()+r''' -IB
import json, os, socket, subprocess, sys
if sys.argv[1:]==['--version']:
 print('codex-cli 0.162.0-alpha.17.2'); sys.exit(0)
argv=sys.argv[1:]; sys.stdin.read()
print('{"type":"thread.started","thread_id":"socket-fake"}')
mode=argv[argv.index('-s')+1]
if mode!='danger-full-access':
 print('{"type":"turn.failed","error":{"message":"socket denied by fake locked engine"}}')
 sys.exit(1)
with socket.socket() as listener:
 listener.bind(('127.0.0.1',0)); listener.listen(1)
 with socket.create_connection(listener.getsockname()) as client:
  with listener.accept()[0] as server:
   client.sendall(b'database-stand-in'); data=server.recv(32)
 subprocess.run(['/usr/bin/true'],check=True)
 open(os.path.join(os.environ['JOB_SCRATCH'],'socket-observed.txt'),'wb').write(data)
print('{"type":"turn.completed","usage":{}}')
''')
    w.program.chmod(0o755)
    done=w.launch()
    assert done.code==(0 if mode=='full' else 1)
    assert not (w.job_scratch/'kyjob.refusal.json').exists()
    assert (w.job_scratch/'kyjob.launch.json').exists()
    if mode=='full': assert (w.job_scratch/'socket-observed.txt').read_bytes()==b'database-stand-in'
    assert json.loads((w.job_scratch/'kyjob.launch.json').read_text())['sandbox_mode']==mode


def test_bad_base_sandbox_argv_refuses(tmp_path,monkeypatch):
    E=adapter()
    monkeypatch.setattr(Q,'build_argv',lambda cfg,s:['codex','exec','-s','read-only','-'])
    with pytest.raises(E.Refusal): E.argv({},dict(job_scratch=str(tmp_path),sandbox_mode='full'))


@pytest.mark.parametrize('name',['OPENAI_API_KEY','CODEX_API_KEY'])
def test_claude_refusals_and_codex_credentials_preserve_legacy(tmp_path,name):
    w=legacy.World(tmp_path/'claude').build()
    w.own_env[name]='dummy-not-a-credential'
    shutil.copyfile(baseline_launcher(w.base),w.fleet/'kyjob.sh')
    baseline=w.launch()
    shutil.copyfile(FLEET/'kyjob.sh',w.fleet/'kyjob.sh')
    current=w.launch()
    assert current.code==baseline.code==0
    c,cfg=codex_world(tmp_path/'codex')
    c.own_env[name]='dummy-not-a-credential'
    assert c.launch().code==78
    assert not (c.job_scratch/'tmp/fake_argv.txt').exists()


def test_every_controller_action_observation_names_engine_and_mode(land):
    assert land.finish()['outcome']=='done'
    for path in (land.world.run/'actions').glob('ACT-codex-*.json'):
        record=json.loads(path.read_text())
        for section in ('inputs','target','result'):
            assert record[section]['engine']=='codex'
            assert record[section]['sandbox']=='full (owner direction 2026-10-12)'


@pytest.mark.parametrize('mode',['locked','full'])
def test_codex_exec_pid_group_env_and_stdin(tmp_path,mode):
    w,cfg=codex_world(tmp_path,mode)
    w.program.write_text(legacy.FAKE_PROGRAM.format(here=str(w.program_dir),python=legacy._own_program()))
    (w.program_dir/'version.txt').write_text('codex-cli 0.162.0-alpha.17.2\n')
    proc=w.start(new_session=True)
    out,err=proc.communicate(timeout=120)
    assert proc.returncode==0,err
    record=w.record()
    assert record['pid']==proc.pid and record['pgid']==proc.pid and record['sid']==proc.pid
    assert record['stdin'].encode()==w.prompt()
    actual=dict(v.split('=',1) for v in record['env'])
    expected={n:w.expected_env()[n] for n in cfg['env_names']}
    assert actual==expected
    assert [cfg['codex_bin']]+record['argv']==adapter().argv(cfg,w.state)


def test_unknown_push_uses_real_dispatcher_action_reconciliation(land):
    """Engine.act catches Exceptions; unknown effects must return unknown, not throw."""
    import types
    import kydispatch
    land.ctx.dry=False
    land.ctx._pr_cache={}
    land.ctx.act=types.MethodType(kydispatch.Engine.act,land.ctx)
    old=land.ctx.sh
    def lost_response(argv,**kw):
        reply=old(argv,**kw)
        return (None,'','push response lost') if 'push' in argv else reply
    land.ctx.sh=lost_response
    assert land.finish()['outcome']=='held'
    path=land.world.run/'actions'/('ACT-codex-'+land.job['job_id']+'-push.json')
    assert json.loads(path.read_text())['state']=='INTENDED'
    land.ctx.sh=old
    assert land.finish()['outcome']=='done'
    assert sum('push' in a for a in land.calls)==1


def test_unreadable_nested_git_guard_is_not_equality(land):
    land.job['checkpoint']['codex_launch']['guards']['git']['config_files']['config']=None
    land.guards['git']['config_files']['config']=None
    J._save(land.ctx,land.job)
    assert land.finish()['outcome']=='held'
    assert not writes(land)


def test_scratch_cannot_cover_common_git_directory(tmp_path,monkeypatch):
    w,cfg=codex_world(tmp_path)
    monkeypatch.setattr(Q,'git_common_dir',lambda wt:(str(w.job_scratch/'git-data'),None))
    with pytest.raises(adapter().Refusal): adapter().launch_config(w.state,w.expected_env())


def test_claude_rejects_codex_configuration_without_engine_inference(tmp_path):
    w=legacy.World(tmp_path).build()
    w.state['launch_config_path']=str(w.job_scratch/'codex-config.json')
    legacy.write_json(w.state_path,w.state)
    assert w.launch().code==65
    assert w.record() is None


def test_crash_after_stage_binds_actual_diff_bytes(land):
    src=land.wt/'src/a.py'; src.parent.mkdir(); src.write_text('original builder bytes\n')
    land.crash='add'
    with pytest.raises(Crash): land.finish()
    src.write_text('different bytes under the same status path\n')
    land.ctx.controller_id='CTL-restarted'
    land.job=J._fresh(land.ctx,land.job)
    assert land.finish()['outcome'] in ('failed','held')
    assert not any('commit' in a for a in land.calls)


def test_verifier_without_builder_scope_retains_publication_and_boundary(land):
    land.job.update(kind='VERIFY',stream='V',head=A,verdict_phase='pre_merge',boundary='verifier')
    land.job['checkpoint'].pop('codex_launch')
    land.packet.write_text('```json\n{"id":"KV3-T","kind":"feature"}\n```\n')
    land.guards['worktree']=dict(head=A,status_sha256='unchanged')
    old=land.ctx.sh
    def tools(argv,**kw):
        if 'ls-remote' in argv: raise AssertionError('a verifier needs no remote landing query')
        if argv[0] in ('bash','python3'):
            land.calls.append(list(argv)); return 0,'',''
        return old(argv,**kw)
    land.ctx.sh=tools
    land.E.prepare(land.ctx,land.job)
    J._save(land.ctx,land.job)
    doc=dict(schema='ky.job_result/1',job_id=land.job['job_id'],item=land.job['item'],status='done',
             branch=None,head_sha=None,pr_number=None,tests=[],blocked_reason=None,notes='',
             proposed_verdict={'result':'ACCEPTED'})
    legacy.write_json(Path(land.job['job_scratch'])/'result.json',doc)
    assert land.finish() is None  # no builder landing; the unchanged publisher owns the verdict
    land.events.append(dict(kind='item',state='review',actor='stream-K:k1',detail='PR #27 @ '+A))
    class Exited:
        def poll(self): return 0
    Path(land.job['stdout_path']).write_text('{"type":"turn.completed"}\n')
    J._CHILDREN[land.job['job_id']]=Exited()
    J._collect(land.ctx,land.job)
    import kyd_kinds_build
    finished=kyd_kinds_build.finish(land.ctx,land.job)
    assert finished['outcome']=='done'
    assert ['bash',str(land.world.fleet/'kyboundary.sh'),'check',land.job['job_id']] in land.calls
    assert any('publish' in a for a in land.calls)
    ended=J.close(land.ctx,land.job,finished)
    assert ended['phase']=='ended'
    assert ['bash',str(land.world.fleet/'kyboundary.sh'),'release',land.job['job_id']] in land.calls
    assert ended['outcome']=='done'
    assert not writes(land)


def test_kind_done_cannot_bypass_uncollected_codex_finish(land):
    """A caller-supplied kind result is insufficient when no exit/turn was collected."""
    J._save(land.ctx,land.job)
    ended=J.close(land.ctx,land.job,{'outcome':'done','failure_fp':None,'detail':'caller says done'})
    assert ended['phase']=='ended' and ended['outcome']=='failed'
    assert not writes(land)


# Real brief fixtures: plan_model.json:3449 (K5-G1a), :3620 (VC-1),
# :7370 (K0a-3). The tool double's KV3-T id aliases one of these briefs.
MODEL = FLEET.parents[2] / 'control/kalayantra/plan_model.json'
KS = 'platform/python-sidecar/services/ka_kshetra/'
FROZEN = 'platform/python-sidecar/pipeline/orchestrator/runner.py'
CONTROL = '00_ARCHITECTURE/briefs/kalayantra/fleet/'


def campaign(land, item='K5-G1a', owns=(), shared=(), kind='feature'):
    source=json.loads(MODEL.read_text())
    items=[copy.deepcopy(i) for i in source['items'] if i['id'] in ('K5-G1a','K0a-3','VC-1')]
    chosen=copy.deepcopy(next(i for i in items if i['id']==item))
    chosen['id']=land.job['item']
    chosen['brief']['owns']=(chosen['brief'].get('owns') or [])+list(owns)
    chosen['brief']['shared']=(chosen['brief'].get('shared') or [])+list(shared)
    items.append(chosen)
    land.ctx.model=Path(land.job['job_scratch'])/'model.json'
    legacy.write_json(land.ctx.model,dict(items=items))
    land.packet.write_text('```json\n'+json.dumps(dict(id=land.job['item'],kind=kind))+'\n```\n')
    land.job['checkpoint'].pop('codex_launch')
    return chosen


def campaign_prepare(land, **kw):
    campaign(land, **kw)
    land.E.prepare(land.ctx,land.job)
    J._save(land.ctx,land.job)
    # Exercise the JSON checkpoint, not in-memory tuples/frozensets.
    land.job=J._fresh(land.ctx,land.job)


@pytest.mark.parametrize('kind',['feature','artifact','operation','schema-prerequisite'])
def test_campaign_scope_sources_and_pins(land,kind):
    campaign_prepare(land,shared=['shared/{a,b}.py'],kind=kind)
    launch=land.job['checkpoint']['codex_launch']
    assert launch['model_sha256']==ka.sha_bytes(land.ctx.model.read_bytes())
    assert launch['patterns']
    ignored=[e['entry'] for e in launch['scope_ignored']]
    assert 'K0a-2\'s files are merged before this starts' in ignored
    assert any('regenerated by' in e for e in ignored)
    assert launch['packet_sha256']==ka.sha_bytes(land.packet.read_bytes())


@pytest.mark.parametrize('path',[
    KS+'new.py', KS+'nested/new.py', KS+'nested/deeper/new.py',
    'shared/a.py','shared/b.py','shared/dir/nested/new.py',
    'shared/existing/nested/new.py',
])
def test_campaign_globs_directory_and_shared(land,path):
    # Existing bare directories must stay directories after checkpoint reload.
    (land.wt/'shared/existing').mkdir(parents=True)
    campaign_prepare(land,shared=['shared/{a,b}.py','shared/dir/','shared/existing'])
    land.status='?? '+path+'\0'
    assert land.finish()['outcome']=='done'
    assert land.job['head']==H


@pytest.mark.parametrize('path',[
    'elsewhere/tests/check.py','elsewhere/__tests__/check.ts','elsewhere/test/check.py',
    'elsewhere/test_case.py','elsewhere/case_test.py','elsewhere/case.test.ts',
    'elsewhere/case.test.tsx','elsewhere/case.spec.ts',
])
def test_campaign_tests_outside_owns(land,path):
    campaign_prepare(land)
    land.status='?? '+path+'\0'
    assert land.finish()['outcome']=='done'


@pytest.mark.parametrize('status,path',[
    ('?? outside.py\0','outside.py'),
    ('R  '+KS+'new.py\0outside.py\0','outside.py'),
    ('R  outside.py\0'+KS+'old.py\0','outside.py'),
    ('?? shared/c.py\0','shared/c.py'),
    ('?? elsewhere/contest/check.py\0','elsewhere/contest/check.py'),
    ('?? elsewhere/case.spec.tsx\0','elsewhere/case.spec.tsx'),
    (' M platform/src/generated/capability_estate_census.json\0',
     'platform/src/generated/capability_estate_census.json'),
])
def test_campaign_outside_or_annotated_scope_blocks(land,status,path):
    campaign_prepare(land,shared=['shared/{a,b}.py'])
    land.status=status
    finished=land.finish()
    assert finished['outcome']=='blocked'
    assert 'outside_owns' in land.events[-1]['detail'] and path in land.events[-1]['detail']
    assert not writes(land) and land.head==A
    assert not land.job['checkpoint'].get('codex_finish',{}).get('paths')


@pytest.mark.parametrize('path',[
    CONTROL+'kyjob_engines.py',CONTROL+'tests/test_campaign.py',
    'platform/scripts/governance/check.py','.github/workflows/check.yml','infra/test_case.py',
])
def test_campaign_control_plane_even_owned_or_tests_blocks(land,path):
    campaign_prepare(land,owns=[CONTROL+'**','platform/scripts/governance/**',
                                 '.github/workflows/**','infra/**'])
    land.status='?? '+path+'\0'
    assert land.finish()['outcome']=='blocked'
    assert 'control_plane' in land.events[-1]['detail'] and path in land.events[-1]['detail']
    assert not writes(land) and land.head==A


@pytest.mark.parametrize('status',[
    ' M '+FROZEN+'\0',
    'R  '+KS+'new.py\0'+FROZEN+'\0',
    ' M outside.py\0 M '+FROZEN+'\0',
])
def test_campaign_frozen_blocks_before_any_landing(land,status):
    campaign_prepare(land,owns=['platform/python-sidecar/pipeline/orchestrator/**'])
    land.status=status
    assert land.finish()['outcome']=='blocked'
    assert land.events[-1]['detail']=='freeze: '+FROZEN
    assert land.events[-1]['actor']=='stream-K:k1'
    assert not writes(land) and land.head==A


@pytest.mark.parametrize('missing',[False,True])
def test_campaign_empty_or_missing_scope_refuses_before_process(land,monkeypatch,missing):
    campaign(land,item='VC-1')  # Its only real owns entry is annotated prose.
    if missing:
        legacy.write_json(land.ctx.model,dict(items=[]))
    land.job['phase']='prepared'
    land.job['pid']=None
    def no_process(*args,**kw):
        pytest.fail('empty campaign scope started a process')
    monkeypatch.setattr(J.subprocess,'Popen',no_process)
    with pytest.raises(land.E.Refusal,match='owns/shared enumerate no machine-readable path'):
        land.E.prepare(land.ctx,land.job)
    assert 'codex_launch' not in land.job['checkpoint']
    assert not writes(land)


def test_campaign_unreadable_entry_is_ignored(land):
    campaign_prepare(land,owns=['shared/unclosed[.py','shared/unclosed{.py'])
    ignored=land.job['checkpoint']['codex_launch']['scope_ignored']
    assert {'source':'brief.owns','entry':'shared/unclosed[.py'} in ignored
    assert {'source':'brief.owns','entry':'shared/unclosed{.py'} in ignored
    land.status='?? shared/unclosed[.py\0'
    assert land.finish()['outcome']=='blocked'
    assert not writes(land)


@pytest.mark.parametrize('path,outcome',[(KS+'nested/new.py','done'),('outside.py','blocked')])
def test_campaign_model_edit_after_launch_has_no_effect(land,path,outcome):
    campaign_prepare(land)
    before=copy.deepcopy(land.job['checkpoint']['codex_launch'])
    # Replacing every entry must neither revoke pinned owns nor add a new path.
    legacy.write_json(land.ctx.model,dict(items=[dict(id=land.job['item'],brief=dict(owns=['outside.py']))]))
    land.E.prepare(land.ctx,land.job)
    assert land.job['checkpoint']['codex_launch']==before
    land.status='?? '+path+'\0'
    assert land.finish()['outcome']==outcome
    if outcome=='blocked': assert not writes(land)


def test_campaign_other_real_brief_glob(land):
    campaign_prepare(land,item='K0a-3')
    land.status='?? platform/python-sidecar/services/kala_core/manifest/nested/new.py\0'
    assert land.finish()['outcome']=='done'


def test_campaign_launch_record_pins_scope_beside_packet(tmp_path,land):
    campaign_prepare(land)
    w,cfg=codex_world(tmp_path/'shell')
    before=copy.deepcopy(land.job['checkpoint']['codex_launch'])
    before.update(config_sha256=land.E.digest(w.state['launch_config_path']),pointer=land.E.pointer(w.state))
    w.state['checkpoint']=dict(codex_launch=before)
    legacy.write_json(w.state_path,w.state)
    assert w.launch().code==0
    record=json.loads((w.job_scratch/'kyjob.launch.json').read_text())
    for key in ('packet_sha256','model_sha256','patterns','scope_ignored'):
        assert record[key]==before[key]


def test_campaign_model_change_during_scope_read_refuses(land,monkeypatch):
    import kyroute
    campaign(land)
    original=kyroute.model_brief
    def changed_after_read(path,item):
        brief=original(path,item)
        Path(path).write_text('{"items": []}\n')
        return brief
    monkeypatch.setattr(kyroute,'model_brief',changed_after_read)
    with pytest.raises(land.E.Refusal,match='model changed while preparing'):
        land.E.prepare(land.ctx,land.job)
    assert 'codex_launch' not in land.job['checkpoint']
    assert not writes(land)


def test_campaign_test_basename_with_newline(land):
    campaign_prepare(land)
    land.status='?? elsewhere/test_line\nbreak.py\0'
    assert land.finish()['outcome']=='done'


@pytest.mark.parametrize('case', ['missing_time', 'null_time', 'nan_time', 'future_time',
                                 'short_counts', 'bad_counts', 'missing_log', 'truncated_log'])
def test_persisted_activity_unknown_is_held(tmp_path, case):
    E = adapter()
    job = dict(engine='codex', sandbox_mode='locked', stall_seconds=10, checkpoint={},
               stdout_path=str(tmp_path / 'out'), stderr_path=str(tmp_path / 'err'))
    for key in ('stdout_path', 'stderr_path'):
        Path(job[key]).write_text('output')
    assert not E.stalled(job, 100)
    activity = job['checkpoint']['codex_activity']
    if case == 'missing_time': activity.pop('last_growth_at')
    elif case == 'null_time': activity['last_growth_at'] = None
    elif case == 'nan_time': activity['launched_at'] = float('nan')
    elif case == 'future_time': activity['last_growth_at'] = 200
    elif case == 'short_counts': activity['bytes'] = []
    elif case == 'bad_counts': activity['bytes'] = [None, 6]
    elif case == 'missing_log': Path(job['stdout_path']).unlink()
    else: Path(job['stderr_path']).write_text('')
    restarted = json.loads(json.dumps(job))
    with pytest.raises(E.Hold): E.stalled(restarted, 120)


@pytest.mark.parametrize('step', ['add', 'commit', 'push', 'create', 'review'])
def test_recover_collected_landing_resumes_persisted_progress(land, step):
    """Actual recovery, with no child handles, resumes only observed durable landing effects."""
    class Exited:
        def poll(self): return 0
    Path(land.job['stdout_path']).write_text('{"type":"turn.completed"}\n')
    J._CHILDREN[land.job['job_id']] = Exited()
    land.crash = step
    with pytest.raises(Crash): J._collect(land.ctx, land.job)
    J._CHILDREN.clear()
    land.ctx.controller_id = 'CTL-recovered-landing'
    recovered = J.recover(land.ctx)
    assert len(recovered) == 1 and recovered[0]['phase'] == 'ended'
    assert recovered[0]['outcome'] == 'done'
    for verb in ('commit', 'push', 'create'):
        assert sum(verb in call for call in land.calls) == 1
    assert sum(event.get('state') == 'review' for event in land.events) == 1
    assert json.loads((land.world.run / 'claims/k1.json').read_text())['state'] == 'released'
    assert not (land.world.run / 'locks/item.KV3-T').exists()


@pytest.mark.parametrize('case', ['snapshot', 'guards', 'pointer'])
def test_missing_persisted_launch_evidence_holds_resources(land, case):
    if case == 'snapshot': land.job['checkpoint'].pop('codex_launch')
    else: land.job['checkpoint']['codex_launch'].pop(case)
    assert land.finish()['outcome'] == 'held'
    assert not writes(land)
    assert json.loads((land.world.run / 'claims/k1.json').read_text())['state'] == 'acquired'
    assert (land.world.run / 'locks/item.KV3-T').exists()


@pytest.mark.parametrize('case', ['missing', 'malformed'])
def test_lost_persisted_landing_progress_is_not_reconstructed(land, case):
    land.crash = 'commit'
    with pytest.raises(Crash): land.finish()
    land.job = J._fresh(land.ctx, land.job)
    if case == 'missing': land.job['checkpoint'].pop('codex_finish')
    else: land.job['checkpoint']['codex_finish'].pop('diff_sha256')
    legacy.write_json(land.world.run / 'jobs' / land.job['job_id'] / 'state.json', land.job)
    land.ctx.controller_id = 'CTL-restarted-with-lost-progress'
    assert land.finish()['outcome'] == 'held'
    assert sum('commit' in call for call in land.calls) == 1
    assert not any('push' in call or 'create' in call for call in land.calls)
    assert json.loads((land.world.run / 'claims/k1.json').read_text())['state'] == 'acquired'
    assert (land.world.run / 'locks/item.KV3-T').exists()
