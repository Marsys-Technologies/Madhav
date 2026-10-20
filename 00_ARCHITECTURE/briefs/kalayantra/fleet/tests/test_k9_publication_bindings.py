"""K9-23 bindings and least-privilege child credential selection."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET=Path(__file__).resolve().parents[1]
REPO=FLEET.parents[3]


def test_all_k9_bindings_are_real_distinct_commands():
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    # main (#3746) enabled these kinds and routes the dry-run/rebuild subcommands through publication_admission.
    commands={'orchestrator_rebuild_dryrun':('publication_admission','rebuild-dryrun'),'orchestrator_rebuild':('publication_admission','rebuild'),
              'layer_verify':('publication','verify'),'layer_publish':('publication','publish'),'layer_rollback':('publication','rollback')}
    for kind,(module,command) in commands.items():
        entry=ops[kind]
        assert entry['enabled'] is True
        assert entry['script']==f'platform/python-sidecar/services/kala_core/{module}.py'
        assert (REPO/entry['script']).is_file()
        # SR-BOLD-04-WITHDRAWN / U-K9P-01 (option B): the real rebuild kind forces every writer to execute; no other kind carries a flag.
        assert entry['fixed_args']==([command,'--force-execute'] if kind=='orchestrator_rebuild' else [command])
        assert entry['python_module']==f'services.kala_core.{module}'
        assert entry['cwd']=='platform/python-sidecar'
        assert entry['needs']==('layer_verifier' if kind=='layer_verify' else 'builder')
    assert ops['layer_verify']['allowed_args']==['run-id','generation','independently-derived-digest']
    assert ops['layer_publish']['allowed_args']==['run-id','generation','expected-head']
    assert ops['layer_rollback']['allowed_args']==['generation','expected-head']


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
    # The writer-digest overlay (J-2a M12) has its own oracles in test_executor_overlay*.py; this test pins only the connection.
    monkeypatch.setattr(executor,'apply_generated_overlay',lambda root,commit,env,timeout=600:({'schema':'ky.generated_overlay/1','source_sha':commit,'files':{}},''))
    op=json.loads((FLEET/'executor_ops.json').read_text())['ops'][kind]
    assert executor.execute({'operation_id':'fixture','reviewed_commit':'a'*40,'args':{}},op)[0]==0
    assert calls[0]['DATABASE_URL']==credential
    assert not {'KY_BUILDER_DATABASE_URL','KY_OWNER_DATABASE_URL','KY_LAYER_VERIFIER_DATABASE_URL'} & calls[0].keys()


@pytest.mark.parametrize('kind',['orchestrator_rebuild_dryrun','orchestrator_rebuild','layer_verify','layer_publish','layer_rollback'])
def test_real_admission_refuses_a_planted_placeholder_script_before_any_git(tmp_path,monkeypatch,kind):
    monkeypatch.setenv('KY_ROOT',str(tmp_path))
    spec=importlib.util.spec_from_file_location('k923_admission',FLEET/'executor.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    def no_git(*a,**k):
        pytest.fail('refusal must occur before consulting or changing git')
    monkeypatch.setattr(executor,'git',no_git)
    ops=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    request=dict(operation_id='fixture',kind=kind,item_id='K9-23',idempotency_key='fixture',requested_by='adhikarin',kyd='fixture')
    ops[kind]['enabled']=True
    ops[kind]['script']='TO_BE_SET_BY_FIXTURE'
    assert executor.validate(request,ops,{'builder':True,'layer_verifier':True})=='operation script not yet reviewed/landed'
