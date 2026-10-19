"""First L3 declarations are partial read-only measurements, never certificates."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT / 'platform/scripts/governance'))
import asset_census as ac


def declaration():
    return {
        'status':'declared', 'fingerprint_definition':'nikasha_stale_certs.table_fingerprint/1',
        'scope':'chart', 'coverage':'partial', 'groups':[],
        'tables':[{'name':'kala_jury_candidate','scope':'chart',
          'key':['chart_id','generation','event_class','assertion_id'],
          'key_evidence':'platform/migrations/1350_kala_jury_candidate.sql:4',
          'exclude':[], 'naive_utc_columns':[],
          'write_evidence':'platform/python-sidecar/services/ka_sangam/jury/candidate.py:322'}],
        'not_covered_tables':[{'name':'kala_convergence','reason':'Legacy dispatch and retained generations are outside this first candidate fingerprint',
          'evidence':'platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py:1'}],
    }


def module():
    path=ROOT / 'platform/scripts/governance/kala_fingerprint_declarations.py'
    assert path.exists(), 'K8 optional chart fingerprint adapter has not been built'
    return importlib.import_module('kala_fingerprint_declarations')


def entry(fp):
    return dict(kind='data', fingerprint=fp)


def test_census_accepts_optional_chart_declaration_without_grading_it():
    fp=declaration()
    ac.validate_declarations({'version':'test','kind_enum':list(ac.DECLARED_KINDS),'assets':{'ka_sangam':entry(fp)}})
    mod=module()
    assert mod.validate('ka_sangam',fp)['coverage']=='partial'
    assert mod.validate('ka_sangam',None) is None
    ac.validate_declarations({'version':'test','kind_enum':list(ac.DECLARED_KINDS),'assets':{'ka_sangam':entry(None)}})


@pytest.mark.parametrize('field,value',[
 ('coverage','full'),('scope','global'),('groups',['made_up']),('status','PASS'),
 ('fingerprint_definition','invented/1'),('not_covered_tables',[]),
])
def test_unearned_scope_full_coverage_and_pass_claims_refuse(field,value):
    fp=declaration(); fp[field]=value
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations({'version':'test','kind_enum':list(ac.DECLARED_KINDS),'assets':{'ka_sangam':entry(fp)}})


@pytest.mark.parametrize('mutation', ['key','table','writer','evidence','exclude','foreign','selector'])
def test_bad_table_key_evidence_exclusion_or_runtime_selector_refuses(mutation):
    fp=declaration(); tab=fp['tables'][0]; aid='ka_sangam'
    if mutation=='key':tab['key']=['chart_id','assertion_id']
    if mutation=='table':tab['name']='issued_forecast'
    if mutation=='writer':tab['write_evidence']='platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py:1'
    if mutation=='evidence':tab['key_evidence']='../../etc/passwd:1'
    if mutation=='exclude':tab['exclude']=[{'column':'generation','reason_code':'wall_clock_timestamp','reason':'pretend'}]
    if mutation=='foreign':aid='ga_positions'
    if mutation=='selector':tab['where']="generation='candidate:x'"
    with pytest.raises(ValueError):module().validate(aid,fp)


def test_committed_first_declaration_keeps_retained_legacy_explicitly_uncovered():
    doc=json.loads((ROOT / 'platform/scripts/governance/asset_declarations.json').read_text())
    fp=doc['assets']['ka_sangam'].get('fingerprint')
    assert fp is not None, 'first L3 fingerprint declaration is absent'
    module().validate('ka_sangam',fp)
    assert {t['name'] for t in fp['tables']}=={
      'kala_jury_candidate','kala_jury_candidate_segment','kala_jury_candidate_contest'}
    assert fp['coverage']=='partial' and fp['not_covered_tables']


def test_service_kind_cannot_claim_a_data_fingerprint():
    with pytest.raises(ac.DeclarationsError,match='data'):
        ac.validate_declarations({'version':'test','kind_enum':list(ac.DECLARED_KINDS),
          'assets':{'ka_sangam':dict(kind='service',fingerprint=declaration())}})
