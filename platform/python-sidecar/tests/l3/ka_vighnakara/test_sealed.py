"""K3-2 synthetic contract exports. These fixtures are never live-seal evidence."""
from copy import deepcopy
import csv
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

CHART='00000000-0000-0000-0000-000000000392'
BUILD='00000000-0000-0000-0000-000000000393'
NATAL='00000000-0000-0000-0000-000000000394'
START='2026-01-01T00:00:00+00:00'
MID='2026-01-15T00:00:00+00:00'
END='2026-02-01T00:00:00+00:00'
GEN='candidate:k3-sealed'


def api():
    assert importlib.util.find_spec('services.ka_vighnakara.sealed'), 'sealed negative-space consumer missing'
    return importlib.import_module('services.ka_vighnakara.sealed')


def data():
    pins=dict(chart_id=CHART,judge_generation='5.0',judge_build_id='judge:build',f2_scenario_id=None,manifest_id='manifest:sealed',
        verifier_execution_id='verification:run',natal_build_id=NATAL,vedha_generation='candidate:vedha',
        f1_generation='candidate:f1',ayanamsha_id='lahiri_chitrapaksha',convention_id='convention:pinned',
        upstream_fingerprint={'sky':'sha256:sky','F1':'sha256:f1','F2':'sha256:f2'})
    span=dict(t0=START,t1=END)
    record=dict(record_id='record:1',chart_id=CHART,generation='5.0',contact_id='contact:1',
        event_class='career_change',frame_kind='moon',frame_arg=None,agent='saturn',relation='residence',
        path_id='P2',rule_version='sealed:version',temporal_support_state='computed',
        temporal_support_intervals=[span],coverage_partition_kind='event_class',coverage_partition_key='career_change',
        coverage_facts=dict(convention_id=pins['convention_id'],completed_horizon=span,relations_searched=['residence']),
        source_text='Phaladipika',source_page='XXVI',source_fact_ids=['fact:moon'],fixture=False,
        provenance='verse_cited',operator_role='testimony',admission_state='admitted',
        evidence_for_occurrence=None,evidence_against_occurrence=None,
        qualification={'vedha':'retained testimony'},period_anchor_lord=None,period_anchor_level=None)
    coverage=dict(chart_id=CHART,generation='5.0',partition_kind='event_class',partition_key='career_change',
        convention_id=pins['convention_id'],requested_horizon=span,completed_horizon=span,
        relations_searched=['residence'],targets_unresolved=0,unavailable_inputs={},unsearched_reason=None,
        build_id='judge:build',resolution=0.1,targets_requested=1,targets_resolved=1,target_resolution_state_counts={'resolved':1})
    header=dict(chart_id=CHART,generation=pins['vedha_generation'],ayanamsha_id=pins['ayanamsha_id'],
        vedha_kind='house_vedha',janma_reference_fact_id='fact:moon',natal_build_id=NATAL,
        formula_version='producer:version',method_qualification='qualified',null_reason=None,
        coverage=dict(search_state='searched',complete=True,requested=span,covered=span,gaps=[]),
        upstream_fingerprint=pins['upstream_fingerprint'],payload={'disclosures':['Moon excluded']})
    def segment(a,b,state):
        return dict(chart_id=CHART,generation=pins['vedha_generation'],ayanamsha_id=pins['ayanamsha_id'],
            vedha_kind='house_vedha',graha='Saturn',t_in=a,t_out=b,state=state,
            classical_citation='Phaladipika XXVI',source_qualification='verse_cited',reasons=[],
            obstructors=['Mars'] if state=='active' else [],unknown_obstructors=[],unqualified_reason=None,
            moon_scope='excluding_on_demand_moon_obstruction' if state=='inactive' else None,
            detail={'primary_house':3,'vedha_house':12})
    segments=[segment(START,MID,'active'),segment(MID,END,'inactive')]
    factor=['vedha','house_vedha']
    results=[dict(state=s['state'],value=0.0 if s['state']=='active' else 1.0,null_state='unqualified',
        reason=None,reasons=[],qualification='vedha_active' if s['state']=='active' else None,
        scope=s['moon_scope'],obstructors=s['obstructors'],unknown_obstructors=[],factor=factor,
        t_in=s['t_in'],t_out=s['t_out']) for s in segments]
    binding=dict(record_id='record:1',exposure='in_risk_set',mechanism='vedha',assertion_id='binding:1',event_class_id='career_change',
        frame_kind='moon',frame_arg=None,contact_id='contact:1',source_fact_ids=['fact:moon'],
        janma_reference_fact_id='fact:moon',graha='Saturn',factor=factor,primary_span=span,
        source={'text':'Phaladipika','locator':'XXVI'},callback=dict(factor=factor,applicable=True,
            results=results,boundaries=[START,MID,END],scopes=['excluding_on_demand_moon_obstruction']),
        upstream_fingerprint=pins['upstream_fingerprint'],f1_id='f1:1',f2_system='vimshottari')
    state=dict(conclusion_id='binding:1',formation_state='formed',fact_state='present',effective_state='in_force',
        defeats=[],excepts=[],qualification='sourced',fact_ids=['fact:moon'])
    f1=dict(id='f1:1',chart_id=CHART,generation=pins['f1_generation'],ayanamsha_id=pins['ayanamsha_id'],
        event_class_id='career_change',mechanism_id='vedha',mechanism_route='admitted',conclusion_state_jsonb=state,
        derivation_ledger_jsonb=dict(deepcopy(state),route='admitted',
            source=json.dumps({'l1':'fact:moon','l0':'rule:1','citations':['Phaladipika XXVI']})))
    fact=dict(fact_id='fact:moon',chart_id=CHART,build_id=NATAL,ayanamsha_id=pins['ayanamsha_id'],
        fact_category='graha_position',fact_subject='MOON',fact_key='longitude_sidereal')
    return dict(pins=pins,seal=[dict(chart_id=CHART,generation='5.0',manifest_id=pins['manifest_id'])],
        publication=[dict(chart_id=CHART,generation='5.0',manifest_id=pins['manifest_id'],status='published',
            convention_id=pins['convention_id'],input_generation_vector={'stored_scope':'full'},row_counts={'records':1,'coverage':1})],
        verifier=[dict(chart_id=CHART,generation='5.0',manifest_id=pins['manifest_id'],execution_id=pins['verifier_execution_id'],
            brief_digest='b'*64,state_digest='c'*64)],record=[record],coverage=[coverage],vedha_header=[header],
        vedha_interval=segments,correspondence=[binding],f1=[f1],fact=[fact])


def clock(a=START,b=END,applicability='applicable'):
    return dict(interval=dict(t0=a,t1=b),applicability=applicability,period_ids={'MD':'period:1'},lords={'MD':'Saturn'},
        lineage={'period:1':None},build_id=NATAL,ayanamsha_id='lahiri_chitrapaksha',tier='two_pass_verified',
        scenario_id=None,system='vimshottari',sources=['BPHS 46.12-16'])


def prepare(value=None,clocks=None):
    return api().prepare(data() if value is None else value,candidate_generation=GEN,clock_spans=clocks or [clock()])


def export(tmp_path,value=None):
    value=data() if value is None else value
    rows=[(kind,api().row_key(kind,v),v) for kind,values in value.items() if kind!='pins' for v in values]
    path=tmp_path/'full.tsv'
    with path.open('w',newline='') as stream:
        writer=csv.writer(stream,delimiter='\t',lineterminator='\n');writer.writerow(['kind','key','payload'])
        writer.writerow(['pins','pins',json.dumps(value['pins'])])
        for kind,key,payload in rows: writer.writerow([kind,key,json.dumps(payload)])
    body=path.read_bytes()
    receipt=dict(status='COMPLETED',exit_code=0,output_file=str(path),output_bytes=len(body),output_sha256=hashlib.sha256(body).hexdigest())
    expected=dict(pins=deepcopy(value['pins']),row_count=len(rows)+1,
        keys={kind:sorted(api().row_key(kind,v) for v in values) for kind,values in value.items() if kind!='pins'})
    return receipt,expected


def test_segments_scopes_and_all_source_fields_survive():
    rows=prepare()
    assert [(r['interval'],r['effective_state']) for r in rows]==[(dict(t0=START,t1=MID),'obstruction_in_force'),(dict(t0=MID,t1=END),'evaluated_silent')]
    assert rows[0]['release']==dict(kind='instant',instant=MID)
    assert rows[1]['provenance']['callback']['results'][1]['scope']=='excluding_on_demand_moon_obstruction'
    assert all(r['acceptance_scope']=='sealed_producers' and r['measurement']=='not_estimated_here' for r in rows)
    assert rows[0]['provenance']['record']==data()['record'][0]
    assert rows[0]['provenance']['coverage']==data()['coverage'][0]


@pytest.mark.parametrize('field',list(data()['pins']))
def test_export_pins_independent_and_exact(tmp_path,field):
    receipt,expected=export(tmp_path);expected['pins'][field]='wrong'
    with pytest.raises(ValueError,match='pins'): api().read_export(receipt,expected)


def test_multiline_tsv_readback_lossless(tmp_path):
    value=data();value['record'][0]['source_page']='XXVI\nquoted "locator"\tretained'
    receipt,expected=export(tmp_path,value)
    assert api().read_export(receipt,expected)==value


@pytest.mark.parametrize('mutation',['tail','hash','bytes','count','key','duplicate','zero_header'])
def test_incomplete_or_substituted_export_refused(tmp_path,mutation):
    receipt,expected=export(tmp_path)
    if mutation=='tail': Path(receipt['output_file']).write_text('record\tkey\tpayload\n')
    elif mutation=='hash': receipt['output_sha256']='0'*64
    elif mutation=='bytes': receipt['output_bytes']-=1
    elif mutation=='count': expected['row_count']-=1
    elif mutation=='key': expected['keys']['record']=['other']
    elif mutation=='zero_header': expected['keys']['vedha_header']=[]
    else:
        p=Path(receipt['output_file']);body=p.read_bytes();p.write_bytes(body+body.splitlines(keepends=True)[2])
        receipt.update(output_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),output_bytes=p.stat().st_size)
    with pytest.raises(ValueError): api().read_export(receipt,expected)


@pytest.mark.parametrize('kind,field,value',[('record','chart_id','wrong'),('record','generation','5.1'),
    ('record','fixture',True),('seal','manifest_id','wrong'),('publication','status','candidate'),
    ('verifier','execution_id','wrong'),('vedha_header','natal_build_id','wrong'),('vedha_header','upstream_fingerprint',{}),
    ('correspondence','frame_kind','lagna_sign'),('correspondence','contact_id','wrong'),
    ('correspondence','janma_reference_fact_id','wrong'),('fact','chart_id','wrong'),('fact','build_id','wrong'),('f1','generation','wrong')])
def test_stale_forged_source_halts(kind,field,value):
    fixture=data();fixture[kind][0][field]=value
    with pytest.raises(ValueError): prepare(fixture)


@pytest.mark.parametrize('field,value',[('targets_unresolved',1),('unavailable_inputs',{'x':'missing'}),
    ('unsearched_reason','unsearched'),('relations_searched',[]),('completed_horizon',dict(t0=START,t1=MID))])
def test_coverage_gaps_outrank_active_and_silent(field,value):
    fixture=data();fixture['coverage'][0][field]=value;rows=prepare(fixture)
    assert {r['effective_state'] for r in rows}=={'information_unavailable'}
    assert {r['null_reason'] for r in rows}=={'judge_coverage_unavailable'}


def test_zero_children_and_missing_header_retain_unavailable():
    fixture=data();fixture['vedha_interval']=[]
    rows=prepare(fixture)
    assert len(rows)==1 and rows[0]['null_reason']=='judge_vedha_rows_absent'
    fixture['vedha_header']=[]
    assert prepare(fixture)[0]['null_reason']=='judge_vedha_rows_absent'


def test_unmatched_correspondence_is_not_guessed():
    fixture=data();fixture['correspondence']=[]
    assert prepare(fixture)[0]['null_reason']=='producer_record_correspondence_unavailable'


def test_ambiguous_correspondence_halts():
    fixture=data();fixture['correspondence']*=2
    with pytest.raises(ValueError,match='duplicate|ambiguous'): prepare(fixture)


def test_node_reason_survives():
    fixture=data();fixture['vedha_interval'][0].update(state='unqualified',reasons=['node_obstruction_undecided'],
        unqualified_reason='node_obstruction_undecided',obstructors=[])
    fixture['correspondence'][0]['callback']['results'][0].update(state='unqualified',value=None,
        reason='node_obstruction_undecided',reasons=['node_obstruction_undecided'],qualification=None,obstructors=[])
    row=prepare(fixture)[0]
    assert (row['knowledge'],row['rule_conclusion'],row['null_reason'])==('inputs_missing','none','node_obstruction_undecided')


@pytest.mark.parametrize('mutation',['boundaries','factor','aggregate'])
def test_structured_callback_cannot_hide_island_or_factor(mutation):
    fixture=data();callback=fixture['correspondence'][0]['callback']
    if mutation=='boundaries': callback['boundaries']=[START,END]
    elif mutation=='factor': callback['results'][0]['factor']=['wrong','factor']
    else: fixture['correspondence'][0]['callback']=0.0
    with pytest.raises(ValueError): prepare(fixture)


def test_coverage_without_records_is_not_silence():
    fixture=data();fixture['record']=[];fixture['correspondence']=[];fixture['publication'][0]['row_counts']['records']=0
    row=prepare(fixture)[0]
    assert row['null_reason']=='mechanism_evaluation_absent' and row['roots']['record_ids']==[]


def test_f2_boundaries_unknown_and_provenance():
    rows=prepare(clocks=[clock(START,MID),clock(MID,END,'unknown')])
    assert [r['effective_state'] for r in rows]==['obstruction_in_force','information_unavailable']
    assert rows[1]['null_reason']=='f2_applicability_unknown' and rows[0]['provenance']['F2']['period_ids']=={'MD':'period:1'}


@pytest.mark.parametrize('field,value',[('tier','single'),('build_id','wrong'),('ayanamsha_id','wrong')])
def test_f2_wrong_pin_refused(field,value):
    span=clock();span[field]=value
    with pytest.raises(ValueError): prepare(clocks=[span])


def protection(kind='defeats',target='binding:1',a=START,b=MID):
    return dict(target_assertion_id=target,kind=kind,fact_ids=['fact:jupiter'],source=dict(text='Patel',locator='PG2299'),interval=dict(t0=a,t1=b))


def with_protection(kind='defeats',target='binding:1',a=START,b=MID):
    fixture=data();fixture['fact'].append(dict(fixture['fact'][0],fact_id='fact:jupiter'))
    state=fixture['f1'][0]['conclusion_state_jsonb'];state['defeats']=[protection(kind,target,a,b)]
    state['effective_state']={'contests':'contested','partly_defeats':'partly_defeated'}.get(kind,'defeated')
    fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state));return fixture


@pytest.mark.parametrize('kind,effective',[('defeats','obstruction_cancelled'),('partly_defeats','obstruction_partly_cancelled'),('contests','obstruction_contested')])
def test_f1_targeted_states_keep_conclusion_and_facts(kind,effective):
    row=prepare(with_protection(kind))[0]
    assert row['effective_state']==effective and row['rule_conclusion']=='obstructed'
    assert set(row['roots']['fact_ids'])=={'fact:moon','fact:jupiter'}


def test_contest_outranks_defeat():
    fixture=with_protection();state=fixture['f1'][0]['conclusion_state_jsonb'];state['defeats'].append(protection('contests'))
    state['effective_state']='contested';fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state))
    assert prepare(fixture)[0]['effective_state']=='obstruction_contested'


def test_protection_split_at_licensed_endpoint():
    rows=prepare(with_protection(b='2026-01-10T00:00:00+00:00'))
    assert [r['effective_state'] for r in rows]==['obstruction_cancelled','obstruction_in_force','evaluated_silent']
    assert rows[1]['interval']['t0']=='2026-01-10T00:00:00+00:00'


@pytest.mark.parametrize('mutation',['wrong_target','no_interval','missing_fact','ledger_conflict','unsourced'])
def test_unlicensed_protection_cannot_cancel_or_reactivate(mutation):
    fixture=with_protection();state=fixture['f1'][0]['conclusion_state_jsonb'];edge=state['defeats'][0]
    if mutation=='wrong_target': edge['target_assertion_id']='other'
    elif mutation=='no_interval': edge.pop('interval')
    elif mutation=='missing_fact': fixture['fact']=fixture['fact'][:1]
    elif mutation=='unsourced': edge['source']['locator']=''
    elif mutation=='ledger_conflict': fixture['f1'][0]['derivation_ledger_jsonb']['effective_state']='in_force'
    if mutation!='ledger_conflict': fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state))
    assert prepare(fixture)[0]['effective_state']=='information_unavailable'


def test_deferred_never_active():
    fixture=data();fixture['correspondence'][0]['rule_conclusion']='conditionally_deferred'
    assert prepare(fixture)[0]['null_reason']=='rule_conclusion_conditionally_deferred'


def test_unserved_badhaka_and_removed_daily_rules():
    fixture=data();fixture['correspondence'][0]['mechanism']='badhaka_movable_lagna'
    assert prepare(fixture)[0]['null_reason']=='source_not_served'
    fixture['correspondence'][0]['mechanism']='rikta_tithi';assert prepare(fixture)==[]


def test_missing_f1_is_not_assumed_unprotected():
    fixture=data();fixture['f1']=[];assert prepare(fixture)[0]['null_reason']=='f1_inputs_unqualified'


def test_factor_inapplicability_is_not_exposure_or_silence():
    fixture=data();binding=fixture['correspondence'][0]
    binding['callback']=dict(factor=binding['factor'],applicable=False,boundaries=[],scopes=[],results=[dict(
        factor=binding['factor'],state='not_applicable',not_applicable=True,value=None,
        reason='no_cited_vedha_pair_for_this_house',reasons=[],qualification=None,scope=None,obstructors=[],unknown_obstructors=[])])
    fixture['vedha_interval']=[];row=prepare(fixture)[0]
    assert row['exposure']=='in_risk_set' and row['effective_state']=='information_unavailable'
    assert row['null_reason']=='vedha_factor_not_applicable'


def test_real_f1_projection_reads_fact_ids_from_ledger():
    fixture=data();fixture['f1'][0]['conclusion_state_jsonb'].pop('fact_ids')
    assert prepare(fixture)[0]['effective_state']=='obstruction_in_force'


def test_unknown_clock_preserves_actual_reader_reason():
    value=clock(applicability='unknown');value.update(period_ids={},sources=[],null_reason='build_not_pinned')
    assert prepare(clocks=[value])[0]['null_reason']=='build_not_pinned'


def test_partial_producer_span_preserves_uncovered_record_edges():
    fixture=data();binding=fixture['correspondence'][0]
    binding['primary_span']=dict(t0=START,t1=MID)
    binding['callback']['results']=binding['callback']['results'][:1]
    binding['callback']['boundaries']=[START,MID];binding['callback']['scopes']=[]
    fixture['vedha_interval']=fixture['vedha_interval'][:1]
    assert [r['effective_state'] for r in prepare(fixture)]==['obstruction_in_force','information_unavailable']


def test_full_producer_coverage_with_interior_gap_is_unavailable_not_silent():
    fixture=data();fixture['vedha_header'][0]['coverage']['gaps']=[dict(t0=START,t1=MID)]
    assert {r['effective_state'] for r in prepare(fixture)}=={'information_unavailable'}


def test_source_locator_and_fact_reference_gaps_are_named():
    fixture=data();fixture['record'][0]['source_page']=None
    assert prepare(fixture)[0]['null_reason']=='source_locator_missing'


def test_no_source_record_means_honest_unknown_release():
    fixture=data();fixture['correspondence']=[]
    assert prepare(fixture)[0]['release']=={'kind':'unknown'}


def test_conditional_release_predicate_is_not_assumed_satisfied():
    fixture=data();fixture['correspondence'][0]['release_predicate_ref']='predicate:licensed'
    assert prepare(fixture)[0]['release']==dict(kind='conditional',predicate_ref='predicate:licensed')


def test_f2_method_inapplicability_keeps_own_axis():
    rows=prepare(clocks=[clock(applicability='method_inapplicable')])
    assert {r['exposure'] for r in rows}=={'method_inapplicable'}
    assert {r['effective_state'] for r in rows}=={'method_inapplicable'}


def test_record_support_uncomputed_cannot_claim_obstruction():
    fixture=data();fixture['record'][0]['temporal_support_state']='uncomputed'
    fixture['record'][0]['temporal_support_intervals']=[]
    rows=prepare(fixture)
    assert {r['effective_state'] for r in rows}=={'information_unavailable'}


def test_f2_lineage_and_source_missing_are_unavailable():
    for field in ('lineage','lords','sources'):
        value=clock();value[field]={} if field!='sources' else []
        assert prepare(clocks=[value])[0]['effective_state']=='information_unavailable'


def test_producer_source_qualification_and_moon_identity_required():
    fixture=data();fixture['vedha_interval'][0]['source_qualification']='uncited_extension'
    assert prepare(fixture)[0]['effective_state']=='information_unavailable'
    fixture=data();fixture['vedha_header'][0]['janma_reference_fact_id']='missing'
    fixture['correspondence'][0]['janma_reference_fact_id']='missing'
    with pytest.raises(ValueError): prepare(fixture)


def test_actual_postgres_range_and_coverage_snapshot_shapes():
    fixture=data();pg=f'["{START}","{END}")'
    fixture['record'][0]['temporal_support_intervals']=[pg]
    fixture['coverage'][0].update(requested_horizon=pg,completed_horizon=pg)
    fixture['record'][0]['coverage_facts']=dict(convention_id=fixture['pins']['convention_id'],
        horizon=dict(lower=START,upper=END,lower_inc=True,upper_inc=False),relations_searched=['residence'])
    assert prepare(fixture)[0]['effective_state']=='obstruction_in_force'


def test_actual_judge_lowercase_agent_matches_released_graha_identity():
    fixture=data();fixture['record'][0]['agent']='saturn'
    assert prepare(fixture)[0]['effective_state']=='obstruction_in_force'


def test_producer_jd_skycoverage_preserves_backend_convention_and_holes():
    from services.gochara_kernel.record_store import _utc_to_jd
    from datetime import datetime
    fixture=data();jd=[_utc_to_jd(datetime.fromisoformat(x)) for x in (START,END)]
    fixture['vedha_header'][0]['coverage']=dict(requested=jd,source_interval=jd,covered=jd,
        backend='swiss_file',convention_id=fixture['pins']['convention_id'],complete=True,gaps=[],search_state='searched')
    assert prepare(fixture)[0]['effective_state']=='obstruction_in_force'


@pytest.mark.parametrize('bad',['empty','["2026-01-01","2026-02-01"]','[,)', '["-infinity","infinity")'])
def test_nonfinite_unbounded_or_closed_source_range_refused(bad):
    fixture=data();fixture['coverage'][0]['requested_horizon']=bad
    with pytest.raises(ValueError): prepare(fixture)


def test_uncovered_coverage_partition_suffix_retains_gap_row():
    fixture=data();binding=fixture['correspondence'][0]
    fixture['record'][0]['temporal_support_intervals']=[dict(t0=START,t1=MID)]
    binding['primary_span']=dict(t0=START,t1=MID);binding['callback']['results']=binding['callback']['results'][:1]
    binding['callback']['boundaries']=[START,MID];binding['callback']['scopes']=[]
    fixture['vedha_interval']=fixture['vedha_interval'][:1]
    rows=prepare(fixture)
    assert [(r['interval'],r['effective_state']) for r in rows]==[
        (dict(t0=START,t1=MID),'obstruction_in_force'),(dict(t0=MID,t1=END),'information_unavailable')]
    assert rows[1]['null_reason']=='mechanism_evaluation_absent'


def test_source_conclusion_identity_is_preserved_without_retargeting_edges():
    row=prepare(with_protection())[0]
    assert row['source_assertion_id']=='binding:1'
    assert row['protections'][0]['target_assertion_id']=='binding:1'
    assert row['assertion_id']!='binding:1'


def test_unrelated_fact_cannot_satisfy_moon_reference():
    fixture=data();fixture['fact'][0]['fact_subject']='SUN'
    with pytest.raises(ValueError): prepare(fixture)


def test_vedha_cannot_bind_to_a_lagna_frame():
    fixture=data();fixture['record'][0]['frame_kind']='lagna';fixture['correspondence'][0]['frame_kind']='lagna'
    with pytest.raises(ValueError): prepare(fixture)


def test_every_consumed_f1_fact_is_retained_in_roots():
    fixture=data();fixture['fact'].append(dict(fixture['fact'][0],fact_id='fact:f1'))
    fixture['f1'][0]['derivation_ledger_jsonb']['fact_ids'].append('fact:f1')
    assert 'fact:f1' in prepare(fixture)[0]['roots']['fact_ids']


def test_f1_unassessed_protection_is_not_turned_into_active():
    fixture=data();fixture['f1'][0]['derivation_ledger_jsonb']['cancellation_unqualified']=['conditions_unassessed']
    assert prepare(fixture)[0]['null_reason']=='f1_inputs_unqualified'


def test_f1_contested_label_without_contesting_evidence_is_unavailable():
    fixture=with_protection();state=fixture['f1'][0]['conclusion_state_jsonb'];state['effective_state']='contested'
    fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state))
    assert prepare(fixture)[0]['effective_state']=='information_unavailable'


def test_multiple_scoped_producer_bindings_for_one_record_are_not_ambiguous():
    fixture=data();original=deepcopy(fixture['correspondence'][0])
    first=deepcopy(original);second=deepcopy(original)
    first['primary_span']=dict(t0=START,t1=MID);first['callback'].update(results=original['callback']['results'][:1],boundaries=[START,MID],scopes=[])
    second['primary_span']=dict(t0=MID,t1=END);second['callback'].update(results=original['callback']['results'][1:],boundaries=[MID,END])
    fixture['correspondence']=[first,second]
    assert [r['effective_state'] for r in prepare(fixture)]==['obstruction_in_force','evaluated_silent']


def test_overlapping_scoped_correspondences_are_refused():
    fixture=data();other=deepcopy(fixture['correspondence'][0]);other['primary_span']=dict(t0=START,t1=MID)
    fixture['correspondence'].append(other)
    with pytest.raises(ValueError,match='ambiguous|overlap'): prepare(fixture)


def test_output_identity_comes_from_immutable_record_not_conclusion_label():
    fixture=data();before=[r['assertion_id'] for r in prepare(fixture)]
    fixture['correspondence'][0]['assertion_id']='alias:conclusion'
    fixture['f1'][0]['conclusion_state_jsonb']['conclusion_id']='alias:conclusion'
    fixture['f1'][0]['derivation_ledger_jsonb']['conclusion_id']='alias:conclusion'
    assert [r['assertion_id'] for r in prepare(fixture)]==before


def test_two_records_sharing_f1_target_cannot_share_output_identity():
    fixture=data();record=deepcopy(fixture['record'][0]);record['record_id']='record:2';record['contact_id']='contact:2'
    binding=deepcopy(fixture['correspondence'][0]);binding.update(record_id='record:2',contact_id='contact:2')
    fixture['record'].append(record);fixture['correspondence'].append(binding)
    fixture['publication'][0]['row_counts']['records']=2
    rows=prepare(fixture)
    assert len(rows)==4 and len({r['assertion_id'] for r in rows})==4


def test_actual_f1_rule_edge_fields_are_retained_with_licensed_interval():
    fixture=with_protection();state=fixture['f1'][0]['conclusion_state_jsonb'];edge=state['defeats'][0]
    edge.update(conclusion_id=edge.pop('target_assertion_id'),rule_id='rule:jupiter-kendra',
        rule_version='rule:v1',source_locator=edge.pop('source')['locator'],defeat_id='edge:1',
        evidence_reason=None,evidence_records=[{'fact_ids':edge['fact_ids']}])
    fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state))
    row=prepare(fixture)[0]
    assert row['effective_state']=='obstruction_cancelled'
    assert row['provenance']['F1']['conclusion_state_jsonb']['defeats'][0]==edge


@pytest.mark.parametrize('value',[None,0.0,1.0])
def test_scalar_adverse_testimony_never_drives_state(value):
    fixture=data();fixture['record'][0]['evidence_against_occurrence']=value
    assert [r['effective_state'] for r in prepare(fixture)]==['obstruction_in_force','evaluated_silent']


@pytest.mark.parametrize('mutation',['null_state','boolean_value','missing_obstructor','lost_reason'])
def test_callback_qualifier_fields_cannot_be_forged(mutation):
    fixture=data();result=fixture['correspondence'][0]['callback']['results'][0]
    if mutation=='null_state': result.pop('null_state')
    elif mutation=='boolean_value': result['value']=False
    elif mutation=='missing_obstructor':
        result['obstructors']=[];fixture['vedha_interval'][0]['obstructors']=[]
    else:
        result.update(state='unqualified',value=None,reason='node_obstruction_undecided',reasons=[],qualification=None)
        fixture['vedha_interval'][0].update(state='unqualified',unqualified_reason='node_obstruction_undecided',reasons=[])
    with pytest.raises(ValueError): prepare(fixture)


def test_explicit_exposure_axis_is_retained_separately():
    fixture=data();fixture['correspondence'][0]['exposure']='outside_risk_set'
    rows=prepare(fixture)
    assert {r['exposure'] for r in rows}=={'outside_risk_set'}
    assert {r['effective_state'] for r in rows}=={'outside_risk_set'}
    assert rows[0]['rule_conclusion']=='obstructed'


def test_f2_cut_is_not_invented_as_protection_onset():
    cut='2026-01-10T00:00:00+00:00'
    rows=prepare(with_protection(),clocks=[clock(START,cut),clock(cut,END)])
    assert rows[0]['release']==dict(kind='instant',instant=START)
    assert rows[1]['release']==dict(kind='unknown')


def test_active_callback_cannot_be_relabelled_silent():
    fixture=data();fixture['correspondence'][0]['rule_conclusion']='none'
    with pytest.raises(ValueError): prepare(fixture)


def test_judge_coverage_build_is_independently_pinned():
    fixture=data();fixture['coverage'][0]['build_id']='wrong:judge-build'
    with pytest.raises(ValueError): prepare(fixture)


def test_f2_scenario_is_not_silently_substituted():
    value=clock();value['scenario_id']='other:scenario'
    with pytest.raises(ValueError): prepare(clocks=[value])


def test_contestation_is_scoped_to_its_own_edge_not_an_adjacent_defeat():
    cut='2026-01-10T00:00:00+00:00'
    fixture=with_protection(a=cut,b=MID);state=fixture['f1'][0]['conclusion_state_jsonb']
    state['defeats'].append(protection('contests',a=START,b=cut));state['effective_state']='contested'
    fixture['f1'][0]['derivation_ledger_jsonb'].update(deepcopy(state))
    assert [r['effective_state'] for r in prepare(fixture)]==[
        'obstruction_contested','obstruction_cancelled','evaluated_silent']


def test_correspondence_cannot_substitute_the_judge_source_locator():
    fixture=data();fixture['correspondence'][0]['source']['locator']='wrong:locator'
    with pytest.raises(ValueError): prepare(fixture)
