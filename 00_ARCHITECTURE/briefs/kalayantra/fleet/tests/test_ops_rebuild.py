"""Bounded runtime registry rule and existing runner fail-stop bridge, DB-free."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_ops_backup import FLEET, NAMES, args, call, load, rig, scope

RUN = '0d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11'

def rargs(source, key='rebuild-one'):
    return ['--scope',str(source),'--idempotency-key',key,'--run-id',RUN]

def test_rebuild_dryrun_is_the_exact_bounded_order_and_never_calls_transport(rig):
    _, source, _, log, t = rig
    r = call('orchestrator_rebuild', ['--dry-run']+rargs(source), t)
    assert r['assets']==NAMES
    assert 'ka_avadhi' not in r['assets']
    assert r['submitted'] is False and r['result_verified'] is None
    assert r['planned_argv'][0][-2:]==['--run-id',RUN]
    assert t.calls==[] and not log.exists()

@pytest.mark.parametrize('damage', ['layer','avadhi_dep','missing','cycle','global','inactive','duplicate'])
def test_registry_rule_refuses_unsafe_or_unresolved_scope(rig, damage):
    _, source, _, log, t = rig
    s=scope()
    if damage=='layer': s['registry'][0]['layer_index']='L1'
    if damage=='avadhi_dep': s['registry'][0]['depends_on']=['ka_avadhi']
    if damage=='missing': s['registry'].pop()
    if damage=='cycle': s['registry'][0]['depends_on']=['ph_muhurta']
    if damage=='global': s['registry'][0]['scope']='global'
    if damage=='inactive': s['registry'][0]['is_active']=False
    if damage=='duplicate': s['registry'].append(copy.deepcopy(s['registry'][0]))
    source.write_text(json.dumps(s))
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild',rargs(source),t)
    assert t.calls==[] and not log.exists()

def test_extra_prefix_assets_are_not_silently_added_to_owner_scope(rig):
    _, source, _, _, t=rig
    s=scope()
    row=dict(s['registry'][0],asset_id='ka_unapproved',target_table='other')
    s['registry'].append(row)
    source.write_text(json.dumps(s))
    assert call('orchestrator_rebuild',rargs(source),t)['assets']==NAMES

@pytest.mark.parametrize('mutation', ['chart','plan','action','state','deps'])
def test_rebuild_refuses_wrong_chart_plan_action_or_attempted_run_before_writes(rig, mutation):
    _, source, _, _, t=rig
    old=t.run_record
    def damaged(run_id):
        r=old(run_id)
        if mutation=='chart': r['chart_id']='other-chart'
        if mutation=='plan': r['plan']=['ga_positions']+NAMES
        if mutation=='action': r['action']='build'
        if mutation=='state': r['state']='running'
        return r
    t.run_record=damaged
    if mutation=='deps': t.dependencies_ready=lambda _:False
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild',['--execute']+rargs(source),t)
    assert t.executed==[]

@pytest.mark.parametrize('state,asset_state,count,integrity', [('stopped','lit',1,True),('completed','incomplete',1,True),('completed','lit',0,True),('completed','lit',1,False)])
def test_readback_measures_terminal_success_rows_and_integrity_not_local_exit(rig,state,asset_state,count,integrity):
    _, source, _, _, t=rig
    t.run_state,t.asset_state,t.count,t.integrity=state,asset_state,count,integrity
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild_readback',['--execute']+rargs(source,key='readback'),t)

def test_rebuild_and_readback_success_need_actual_evidence(rig):
    _, source, _, _, t=rig
    r=call('orchestrator_rebuild',['--execute']+rargs(source),t)
    assert t.executed==[(RUN,NAMES)]
    assert r['result_verified'] is True
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild',['--execute']+rargs(source),t)
    r=call('orchestrator_rebuild_readback',['--execute']+rargs(source,key='readback'),t)
    assert r['result_verified'] is True
    assert len(r['readback']['assets'])==len(NAMES)

@pytest.mark.parametrize('outcome', ['error','incomplete','unknown'])
def test_serial_bridge_stops_first_failure_and_restores_runner(outcome):
    m=load()
    calls=[]
    class Runner:
        _SUCCESS_OUTCOMES={'lit','complete','service_ok'}
        @staticmethod
        def execute_dag(**kw):
            assert kw['worker_limit']==1
            failed=set()
            for a in kw['plan']:
                if kw['should_stop'](): break
                if kw['run_fn'](a) not in Runner._SUCCESS_OUTCOMES: failed.add(a)
            return failed,None
        @staticmethod
        def execute_run(run_id):
            return Runner.execute_dag(plan=NAMES,worker_limit=4,run_fn=lambda a: calls.append(a) or (outcome if a==NAMES[1] else 'lit'),should_stop=lambda:None)
    original=Runner.execute_dag
    failed,_=m.execute_serial(Runner,RUN,NAMES)
    assert calls==NAMES[:2] and failed=={NAMES[1]}
    assert Runner.execute_dag is original

def test_serial_bridge_refuses_changed_plan_and_seed_failure_without_dispatch():
    m=load()
    class Runner:
        _SUCCESS_OUTCOMES={'lit'}
        @staticmethod
        def execute_dag(**kw):
            pytest.fail('unsafe scheduler was invoked')
        @staticmethod
        def execute_run(run_id):
            return Runner.execute_dag(plan=['ga_positions'],worker_limit=4,run_fn=lambda _: 'lit')
    with pytest.raises(m.Refusal): m.execute_serial(Runner,RUN,NAMES)

@pytest.mark.parametrize('kind',['orchestrator_rebuild','orchestrator_rebuild_readback'])
def test_cli_dryrun_has_no_connection_dependency(rig,kind):
    _,source,_,log,_=rig
    env={k:v for k,v in os.environ.items() if k!='DATABASE_URL'}
    p=subprocess.run([sys.executable,'-B',str(FLEET/'ops'/(kind+'.py')),'--dry-run']+rargs(source),env=env,text=True,capture_output=True)
    assert p.returncode==0,p.stderr
    assert json.loads(p.stdout)['submitted'] is False and not log.exists()


def test_real_transport_binds_registry_count_placeholder_and_uses_readonly_queries():
    m=load()
    s=scope()
    for r in s['registry']:
        r['count_sql']='SELECT count(*) FROM public.fixture WHERE chart_id=$1'
    class Conn:
        def __init__(self): self.calls=[]
        def execute(self,sql,params=()):
            self.calls.append((sql,params))
            if sql.startswith('SELECT state FROM build_runs'): rows=[{'state':'completed'}]
            elif 'bra.state' in sql: rows=[{'asset_id':name,'run_state':'complete','throughput_state':'lit'} for name in NAMES]
            elif 'count(*)' in sql:
                assert '$1' not in sql and params==(m.A.CANONICAL_CHART,)
                rows=[{'count':1}]
            else: rows=[{'healthy':True}]
            return type('Cursor',(),{'fetchall':lambda _:rows})()
    t=m.Postgres.__new__(m.Postgres)
    t.conn=Conn()
    t.scope=s
    r=t.readback(RUN,NAMES)
    m.verify_readback(r,NAMES,{r['asset_id']:r for r in s['registry']})
    assert len(r['assets'])==len(NAMES)


def test_dryrun_prints_an_existing_wrapper_and_no_invented_runner_path(rig):
    _,source,_,_,t=rig
    r=call('orchestrator_rebuild',rargs(source),t)
    assert Path(r['planned_argv'][0][2]).is_file()


def test_registry_prohibits_lower_layer_downstream_state_mutation(rig):
    _,source,_,_,t=rig
    s=scope()
    s['registry'].append(dict(s['registry'][0],asset_id='ga_bad_edge',layer_index='L1',depends_on=['ka_yojaka']))
    source.write_text(json.dumps(s))
    with pytest.raises(load().Refusal): call('orchestrator_rebuild',rargs(source),t)


def test_readback_census_contains_content_digests(rig):
    _,source,_,_,t=rig
    r=call('orchestrator_rebuild_readback',['--execute']+rargs(source,key='content-census'),t)
    assert r['measurements'] and all(len(x['sha256'])==64 for x in r['measurements'].values())


def test_readback_refuses_a_hidden_extra_run_asset(rig):
    _,source,_,_,t=rig
    old=t.readback
    def extra(run_id,assets):
        r=old(run_id,assets)
        r['assets'].append(dict(r['assets'][0],asset_id='ga_positions'))
        return r
    t.readback=extra
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild_readback',['--execute']+rargs(source,key='extra-census'),t)


def test_existing_assets_argument_can_only_confirm_the_runtime_rule(rig):
    _,source,_,_,t=rig
    r=call('orchestrator_rebuild',rargs(source)+['--assets',','.join(NAMES)],t)
    assert r['assets']==NAMES
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild',rargs(source)+['--assets','ga_positions'],t)


@pytest.mark.parametrize('field,value',[('action','build'),('chart_id','another-chart'),('plan',['ga_positions'])])
def test_independent_readback_refuses_unrelated_run_identity(rig,field,value):
    _,source,_,_,t=rig
    original=t.run_record
    def damaged(run_id):
        r=original(run_id)
        r[field]=value
        return r
    t.run_record=damaged
    with pytest.raises(load().Refusal):
        call('orchestrator_rebuild_readback',['--execute']+rargs(source,key='wrong-readback'),t)
