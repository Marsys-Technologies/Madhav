"""K9-23 disabled bindings and least-privilege child credential selection."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET=Path(__file__).resolve().parents[4]/'00_ARCHITECTURE/briefs/kalayantra/fleet'
REPO=FLEET.parents[3]


def test_all_k9_bindings_are_real_disabled_distinct_commands():
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    commands={'orchestrator_rebuild_dryrun':'rebuild-dryrun','orchestrator_rebuild':'rebuild',
              'layer_verify':'verify','layer_publish':'publish','layer_rollback':'rollback'}
    for kind,command in commands.items():
        entry=ops[kind]
        assert entry['enabled'] is False
        assert entry['script']=='platform/python-sidecar/services/kala_core/publication.py'
        assert (REPO/entry['script']).is_file()
        assert entry['fixed_args']==[command]
        assert entry['python_module']=='services.kala_core.publication'
        assert entry['cwd']=='platform/python-sidecar'
        assert entry['needs']==('layer_verifier' if kind=='layer_verify' else 'builder')
    assert ops['layer_verify']['allowed_args']==['run-id','generation','independently-derived-digest','semantic-source']
    assert ops['layer_publish']['allowed_args']==['run-id','generation','expected-head','semantic-source']
    assert ops['layer_rollback']['allowed_args']==['generation','expected-head']
    assert '00_ARCHITECTURE/briefs/kalayantra/fleet/k9_readback.py' in (FLEET/'BOOTSTRAP_COMPONENTS.txt').read_text().splitlines()


@pytest.mark.parametrize('kind,credential', [('layer_verify','verifier-fixture'),('layer_publish','builder-fixture')])
def test_executor_passes_only_operation_specific_connection(tmp_path,monkeypatch,kind,credential):
    monkeypatch.setenv('KY_ROOT',str(tmp_path))
    monkeypatch.setenv('KY_BUILDER_DATABASE_URL','builder-fixture')
    monkeypatch.setenv('KY_LAYER_VERIFIER_DATABASE_URL','verifier-fixture')
    monkeypatch.setenv('KY_OWNER_DATABASE_URL','owner-fixture')
    spec=importlib.util.spec_from_file_location('k923_executor',FLEET/'executor.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    calls=[]
    monkeypatch.setattr(executor,'git',lambda *a,**k:SimpleNamespace(returncode=0,stderr=''))
    def run_group(argv,cwd,env,timeout):
        calls.append(env)
        return SimpleNamespace(returncode=0,stdout='',stderr='')
    monkeypatch.setattr(executor,'run_group',run_group)
    op=json.loads((FLEET/'executor_ops.json').read_text())['ops'][kind]
    assert executor.execute({'operation_id':'fixture','reviewed_commit':'a'*40,'args':{}},op)[0]==0
    assert calls[0]['DATABASE_URL']==credential
    assert not {'KY_BUILDER_DATABASE_URL','KY_OWNER_DATABASE_URL','KY_LAYER_VERIFIER_DATABASE_URL'} & calls[0].keys()


@pytest.mark.parametrize('kind',['orchestrator_rebuild_dryrun','orchestrator_rebuild','layer_verify','layer_publish','layer_rollback'])
def test_real_admission_refuses_disabled_and_planted_placeholder_before_any_git(tmp_path,monkeypatch,kind):
    monkeypatch.setenv('KY_ROOT',str(tmp_path))
    spec=importlib.util.spec_from_file_location('k923_admission',FLEET/'executor.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    def no_git(*a,**k):
        pytest.fail('refusal must occur before consulting or changing git')
    monkeypatch.setattr(executor,'git',no_git)
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    request=dict(operation_id='fixture',kind=kind,item_id='K9-23',idempotency_key='fixture',requested_by='adhikarin',kyd='fixture')
    assert 'not enabled' in executor.validate(request,ops,{'builder':True,'layer_verifier':True})
    ops[kind]['enabled']=True
    ops[kind]['script']='TO_BE_SET_BY_FIXTURE'
    assert executor.validate(request,ops,{'builder':True,'layer_verifier':True})=='operation script not yet reviewed/landed'


def test_k94b_readback_admission_requires_sql_digest_before_git(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT',str(tmp_path))
    spec=importlib.util.spec_from_file_location('k94b_admission',FLEET/'executor.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    monkeypatch.setattr(executor,'git',lambda *a,**k: pytest.fail('missing SQL digest must refuse before git'))
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    req=dict(operation_id='fixture',kind='readback_sql',item_id='K9-4b',idempotency_key='fixture',
             requested_by='adhikarin',kyd='fixture',args={'sql_file':'run/ops/sql/fixture.sql'})
    assert executor.validate(req,ops,{'pgenv':True})=='K9-4b readback requires a prepared SQL digest'
    req['args']['sql-sha256']='malformed'
    assert executor.validate(req,ops,{'pgenv':True})=='K9-4b readback requires a prepared SQL digest'


def test_backups_retain_main_qualified_owner_bindings():
    import subprocess,sys
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    for kind,mode in [('backup_snapshot','snapshot'),('backup_restore_verify','restore-verify')]:
        entry=ops[kind]
        assert entry['needs']=='owner'
        assert entry['script']=='platform/scripts/backup_v5_small_test_job.py'
        assert entry['fixed_args']==['--operation',mode,'--execute']
        assert entry['enabled'] is True  # main's J-1a activation, not K923B enablement
        run=subprocess.run([sys.executable,'-B',str(REPO/entry['script']),'--operation',mode,
                            '--label','k923_fixture','--dry-run'],capture_output=True,text=True,timeout=5)
        assert run.returncode==0
        evidence=json.loads(run.stdout)
        assert evidence['status']=='planned'
        assert evidence['backup_taken'] is None and evidence['restore_verified'] is None


def test_verifier_capability_tracks_its_own_presence_without_builder_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv('KY_ROOT',str(tmp_path))
    spec=importlib.util.spec_from_file_location('k923_caps',FLEET/'executor.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    executor.OPS.mkdir(parents=True)
    # Capability discovery's unrelated cloud probe is an in-process double.
    monkeypatch.setattr(executor.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='',stderr='',returncode=0))
    monkeypatch.setenv('KY_BUILDER_DATABASE_URL','builder-fixture')
    monkeypatch.delenv('KY_LAYER_VERIFIER_DATABASE_URL',raising=False)
    assert executor.capabilities(True)['layer_verifier'] is False
    monkeypatch.setenv('KY_LAYER_VERIFIER_DATABASE_URL','verifier-fixture')
    assert executor.capabilities(True)['layer_verifier'] is True
