"""Snapshot content plus complete dependency vector, never a publication."""
import copy
import json
from pathlib import Path
import pytest


def test_complete_dependency_digest_is_recomputed_for_each_mutation():
    from services.ka_kshetra.g1_manifest import snapshot_vector
    deps={'model_digest':'code','rule_registry_version':'rules','conventions':{'axis':'birth'},
          'upstream_grains':[('judge','j'),('jury','y')],'pins':{'weights':'w','corpus':'c'}}
    vector=snapshot_vector('snapshot','content',deps)
    assert vector==snapshot_vector('snapshot','content',copy.deepcopy(deps))
    for key in deps:
        changed=copy.deepcopy(deps); changed[key]=[changed[key],'mutation']
        assert snapshot_vector('snapshot','content',changed)['digest']!=vector['digest']
    assert snapshot_vector('snapshot','changed',deps)['digest']!=vector['digest']
    assert vector['snapshot_id']=='snapshot' and vector['content_digest']=='content'


def test_baseline_freeze_requires_merged_head_and_pins_exact_code(tmp_path):
    from services.ka_kshetra.g1_manifest import freeze_baseline
    target=tmp_path/'G1_BASELINE.json'
    with pytest.raises(ValueError): freeze_baseline(target,merged_head='not-a-sha',code_digest='c'*64)
    with pytest.raises(ValueError): freeze_baseline(target,merged_head='a'*40,code_digest='not-a-digest')
    freeze_baseline(target,merged_head='a'*40,code_digest='c'*64)
    assert json.loads(target.read_text())=={'schema':'ky.g1_baseline/1','merged_head':'a'*40,'code_digest':'c'*64}
    freeze_baseline(target,merged_head='a'*40,code_digest='c'*64)
    with pytest.raises(ValueError,match='frozen'): freeze_baseline(target,merged_head='b'*40,code_digest='c'*64)
    with pytest.raises(ValueError,match='frozen'): freeze_baseline(target,merged_head='a'*40,code_digest='d'*64)


def test_writer_attaches_snapshot_to_manifest(monkeypatch):
    from services.ka_kshetra import writer as W,stage4_field as S4,g1_manifest
    from types import SimpleNamespace
    writer=W.KaKshetraWriter()
    writer._dry_run=False; writer._chart_id='chart';writer._generation='candidate:g1'
    writer._build_id='build';writer._snapshot_id='snapshot';writer._weights_version='v0'
    writer._pins=S4.FieldPins('chart','corpus','v0','x',{})
    writer._event_classes=[];writer._skipped=[]
    monkeypatch.setattr(writer,'_compute_content_hash',lambda c:'content')
    monkeypatch.setattr(writer,'_record_substep',lambda *a:None)
    seen=[]
    monkeypatch.setattr(g1_manifest,'attest_snapshot',lambda *args,**kw:seen.append((args,kw)))
    class Conn:
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def execute(self,*a): pass
    writer._run_snapshot(Conn(),SimpleNamespace(key='snapshot'))
    assert len(seen)==1
    assert seen[0][1]['content_digest']=='content'
    assert seen[0][1]['generation']=='candidate:g1'
