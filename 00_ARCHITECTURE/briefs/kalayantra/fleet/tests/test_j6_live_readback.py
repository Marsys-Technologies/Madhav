"""J6l capture/soak tooling records bytes; never grants live or soak acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import uuid

import pytest

FLEET = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(FLEET))
import j6_live_readback as live

BINDING = dict(operation_id='J-6-attempt-1',request_sha256='1'*64,receipt_sha256='2'*64,
               readback_receipt_sha256='3'*64, chart_id='482012f1-710e-4a25-994a-93821f5871aa',
               generation='5.0',manifest_id=str(uuid.UUID(int=50)))
URL = 'https://fixture.invalid/actual-consumer'


def inputs():
    deploy = dict(schema='ky.j6_deployment_observation/1',url=URL,image_digest='sha256:'+'4'*64,
                  commit='a'*40,migrations=[dict(filename='1382_gochara_authority_no_truncate.sql',sha256='5'*64)],
                  observed_at='2026-10-16T01:01:00+00:00')
    routing = dict(schema='ky.j6_consumer_path/1',url=URL,mode='authority',by='v1',result='ACCEPTED',
                   binding=BINDING,deployment_sha256=live.sha(deploy),evidence_sha256='6'*64)
    response = dict(url=URL,status=200,observed_at='2026-10-16T01:02:00+00:00',
                    body=json.dumps(dict(schema='gochara_v5_windows/1',manifest_status='published',stored_scope='stored_non_moon',
                                         seal={'manifest_id':BINDING['manifest_id']},chart_id=BINDING['chart_id'],generation='5.0',
                                         manifest_id=BINDING['manifest_id'],refusal=None,
                                         classes=[dict(event_class='marriage',completeness='complete_within_scope')])).encode())
    return deploy,routing,response


def capture(deploy=None,routing=None,response=None):
    d,r,s=inputs()
    return live.capture(BINDING, deploy or d, routing or r, lambda url:s if response is None else response)


def test_live_capture_hashes_exact_response_and_identifies_image_migration_set():
    deploy,routing,response = inputs()
    got=capture()
    assert got['schema']=='ky.j6_live_capture/1' and got['binding']==BINDING
    assert got['response']['sha256']==hashlib.sha256(response['body']).hexdigest()
    assert got['response']['bytes']==len(response['body'])
    assert got['response']['served_manifest_id']==BINDING['manifest_id']
    assert got['deployment']==deploy and got['deployment_sha256']==live.sha(deploy)
    assert got['consumer_path_sha256']==live.sha(routing)
    assert got['acceptance'] is None and got['production_activated'] is False


@pytest.mark.parametrize('mutation',['generation','manifest','refusal','status','url','slice','stale','empty_classes'])
def test_response_failure_or_explicit_generation_cannot_masquerade_as_authority_cutover(mutation):
    deploy,routing,response=inputs()
    body=json.loads(response['body'])
    if mutation=='generation': body['generation']='3.0'
    if mutation=='manifest': body['manifest_id']=str(uuid.UUID(int=51))
    if mutation=='refusal': body['refusal']={'code':'not_sealed'}
    if mutation=='status': response['status']=503
    if mutation=='url': response['url']=URL+'?generation=5.0'
    if mutation=='slice': body['test_slice']={'run':'test'}
    if mutation=='stale': body['classes'][0]['completeness']='stale_binding'
    if mutation=='empty_classes': body['classes']=[]
    response['body']=json.dumps(body).encode()
    with pytest.raises(live.Refused): capture(deploy,routing,response)


@pytest.mark.parametrize('mutation',['image','migrations','migration_hash','duplicate_migration','path_mode','path_by','path_binding','path_deploy','path_missing','explicit_url'])
def test_deployment_and_independent_consumer_path_are_required_inputs(mutation):
    d,r,s=inputs()
    if mutation=='image': d['image_digest']='latest'
    if mutation=='migrations': d['migrations']=[]
    if mutation=='migration_hash': d['migrations'][0]['sha256']='bad'
    if mutation=='duplicate_migration': d['migrations']*=2
    if mutation=='path_mode': r['mode']='explicit_generation'
    if mutation=='path_by': r['by']='adhikarin'
    if mutation=='path_binding': r['binding']={**BINDING,'request_sha256':'0'*64}
    if mutation=='path_deploy': r['deployment_sha256']='0'*64
    if mutation=='path_missing': r={}
    if mutation=='explicit_url': d['url']=URL+'?generation=5.0';r['url']=d['url'];s['url']=d['url']
    with pytest.raises(live.Refused): live.capture(BINDING,d,r,lambda url:s)


def test_soak_without_owner_rule_records_measurements_without_assumed_exit():
    observations=[capture()]
    got=live.record_soak(BINDING,observations)
    assert got['schema']=='ky.j6_soak_record/1' and got['binding']==BINDING
    assert got['observations_sha256']==live.sha(observations) and got['sample_count']==1
    assert got['owner_rule_sha256'] is None and got['acceptance'] is None
    assert got['missing']==['owner_soak_rule_and_live_readback_acceptance']
    assert got['elapsed_seconds']==0
    assert 'passed' not in got and '24' not in str(got.get('duration_threshold',''))


def test_soak_binds_opaque_owner_rule_and_each_actual_sample_without_deciding_it():
    first=capture(); second=copy.deepcopy(first)
    second['response']['observed_at']='2026-10-16T01:12:00+00:00'
    rule=b'{"owner_decision_ref":"fixture-only","measured_exit_rule":"owner defines this later"}'
    got=live.record_soak(BINDING,[first,second],owner_rule_raw=rule)
    assert got['owner_rule_sha256']==hashlib.sha256(rule).hexdigest()
    assert got['elapsed_seconds']==600 and got['sample_count']==2
    assert got['acceptance'] is None and got['missing']==['independent_soak_acceptance']
    bad=copy.deepcopy(second);bad['binding']['operation_id']='other'
    with pytest.raises(live.Refused): live.record_soak(BINDING,[first,bad],owner_rule_raw=rule)
    with pytest.raises(live.Refused): live.record_soak(BINDING,[second,first],owner_rule_raw=rule)
    bad=copy.deepcopy(second);bad['deployment_sha256']='0'*64
    with pytest.raises(live.Refused): live.record_soak(BINDING,[first,bad],owner_rule_raw=rule)


def test_tooling_is_on_mandatory_ci_path_and_no_new_kind_is_enabled():
    root=FLEET.parents[3]
    ci=(root/'.github/workflows/ci.yml').read_text()
    for name in ('test_j6_head_bindings.py','test_j6_live_readback.py','test_j6_bindings_db.py'):
        assert name in ci
    table=json.loads((FLEET/'executor_ops.json').read_text())['ops']
    assert not any(table[k]['enabled'] for k in ('publish_head','rollback_head','publish_head_dryrun','rollback_head_dryrun'))


def test_capture_and_soak_cli_import_exact_bytes_without_network_or_acceptance(tmp_path,capsys):
    deploy,routing,response=inputs()
    docs={'binding':BINDING,'deployment':deploy,'consumer-path':routing,
          'http-observation':{k:v for k,v in response.items() if k!='body'}}
    args=['capture']
    for key,value in docs.items():
        path=tmp_path/(key+'.json');path.write_text(json.dumps(value));args += ['--'+key,str(path)]
    body=tmp_path/'body.json';body.write_bytes(response['body']);args += ['--body',str(body)]
    before=set(tmp_path.iterdir())
    assert live.main(args)==0
    sample=json.loads(capsys.readouterr().out)
    observations=tmp_path/'observations.json';observations.write_text(json.dumps([sample]))
    assert live.main(['soak','--binding',str(tmp_path/'binding.json'),'--observations',str(observations)])==0
    got=json.loads(capsys.readouterr().out)
    assert got['acceptance'] is None and got['owner_rule_sha256'] is None
    assert set(tmp_path.iterdir())==before|{observations}
