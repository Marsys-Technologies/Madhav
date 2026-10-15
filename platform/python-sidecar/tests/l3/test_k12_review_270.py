"""Independent review 270: real production paths, in-memory SQL transport only."""
from copy import deepcopy
from types import SimpleNamespace
import json
import pytest
from pipeline.orchestrator.writers import SubStep
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter
from tests.l3.ka_yojaka.test_k12_candidate_pins import Conn
from tests.l3.ka_yojaka.test_source_adapter import sources

class MemorySQL(Conn):
    def __init__(self):
        super().__init__()
        facts, firings = sources()
        self.facts = [dict(r, build_id='A', verification_pass_status='two_pass_verified') for r in facts]
        self.firings = [dict(r, build_id='A') for r in firings]
        self.signals = [dict(signal_id='signal:A', build_id='A', ayanamsha_id='a',
                             constituent_facts_array=['f:moon'], configuration_jsonb={})]
        self.cgm = [dict(edge_id='cgm:A', build_id='A', ayanamsha_id='a', edge_properties_jsonb={})]
        self.pratijna = [dict(pratijna_id='pratijna:A', build_id='A', ayanamsha_id='a',
                             event_class_id='major_gain', derivation={})]
        self.grains = {}
        self.reads = []
        self.dashas = [dict(dasha_row_id='d:A', build_id='A', ayanamsha_id='a',
                            lord_graha='Moon', verification_pass_status='two_pass_verified')]
    def execute(self, sql, params=()):
        self.reads.append((sql, params))
        compact = ' '.join(sql.split())
        if 'SELECT input_vector FROM kala_layer_candidate_grain' in compact:
            vector = self.grains.get(tuple(params))
            self.rows = [] if vector is None else [dict(input_vector=vector)]
        elif 'INSERT INTO kala_layer_candidate_grain' in compact:
            self.grains[tuple(params[:3])] = params[4]
            self.writes.append((sql, params)); self.rows = []
        else:
            table = next((t for t in ('chart_facts','ga_yoga_firings','bodha_msr_signals',
                                      'bodha_cgm_edges','bodha_pratijna','chart_dashas')
                          if f'FROM {t}' in compact), None)
            if table:
                rows = getattr(self, {'chart_facts':'facts', 'ga_yoga_firings':'firings',
                    'bodha_msr_signals':'signals','bodha_cgm_edges':'cgm','bodha_pratijna':'pratijna',
                    'chart_dashas':'dashas'}[table])
                selected = rows
                if 'build_id' in compact.split('WHERE')[-1]:
                    selected = [r for r in selected if r['build_id'] == params[1]]
                if 'ayanamsha_id' in compact.split('WHERE')[-1]:
                    i = 2 if 'build_id' in compact.split('WHERE')[-1] else 1
                    selected = [r for r in selected if r['ayanamsha_id'] == params[i]]
                self.rows = deepcopy(selected)
            elif 'FROM brahma_event_ontology' in compact:
                from services.ka_gochara_resonance.writer import TARGET_EVENT_CLASSES
                self.rows = [dict(event_class_id=c,signature_model={},citations=[]) for c in TARGET_EVENT_CLASSES]
            else:
                super().execute(sql, params)
        return self

def context(conn):
    return SimpleNamespace(dry_run=False,db_conn=conn,build_id='owner',
        config={'chart_id':'chart','candidate_generation':'candidate:G'})

def written(conn):
    return [json.loads(row[7]) for sql, rows in conn.writes
            if 'INSERT INTO kala_activation_predicates' in sql for row in rows]

@pytest.mark.parametrize('table,attr', [('chart_facts','facts'),('ga_yoga_firings','firings'),
    ('bodha_msr_signals','signals'),('bodha_cgm_edges','cgm'),('bodha_pratijna','pratijna')])
def test_pinned_source_drift_refuses_before_candidate_delete(table,attr):
    conn=MemorySQL(); writer=KaYojakaWriter(); step=SubStep('class:major_gain')
    writer.run_substep(context(conn),step)
    getattr(conn,attr).clear()
    old=len(conn.writes)
    with pytest.raises(ValueError,match='input vector changed'):
        writer.run_substep(context(conn),step)
    assert conn.writes[old:]==[]

def test_candidate_writer_filters_all_sources_and_exposes_three_consultations():
    conn=MemorySQL()
    for attr,id_key in [('facts','fact_id'),('firings','id'),('signals','signal_id'),
                        ('cgm','edge_id'),('pratijna','pratijna_id')]:
        original=deepcopy(getattr(conn,attr)[0])
        for build,ayan in [('B','a'),('A','b')]:
            foreign=dict(original,build_id=build,ayanamsha_id=ayan)
            foreign[id_key]=str(original[id_key])+':foreign:'+build+ayan
            getattr(conn,attr).append(foreign)
    KaYojakaWriter().run_substep(context(conn),SubStep('class:major_gain'))
    gain=next(r for r in written(conn) if r['canonical_id']=='sunapha')
    assert gain['fact_ids']==['f:moon']
    assert gain['attachments']==['signal:A']
    assert gain['source_natal_pin']['build_id']=='A'
    assert gain['sources_consulted']==['msr','cgm','pratijna']
    assert gain['source_states']==dict(msr='present',cgm='missing_fact',pratijna='missing_fact')
    assert gain['constituent_fact_tiers']=={'f:moon':'two_pass_verified'}
    assert gain['yoga_tier'] is None
    for table in ['chart_facts','ga_yoga_firings','bodha_msr_signals','bodha_cgm_edges','bodha_pratijna']:
        selected=[(q,p) for q,p in conn.reads if f'FROM {table}' in q]
        assert selected, table
        assert all(tuple(p)==('chart','A','a') for q,p in selected), table

def test_cgm_pratijna_actual_writer_consults_rootless_rows_without_formations():
    conn=MemorySQL(); conn.facts=[]; conn.firings=[]; conn.signals=[]
    KaYojakaWriter().run_substep(context(conn),SubStep('class:unqualified'))
    audit=written(conn)
    assert {r['source'] for r in audit}=={'bodha_cgm_edges','bodha_pratijna'}
    assert {a['attachment_id'] for r in audit for a in r['l2_attachments']}=={'cgm:A','pratijna:A'}
    for r in audit:
        assert r['source_states']['cgm']==r['source_states']['pratijna']=='missing_fact'
        assert r['source_null_reasons']['cgm']=='no_fact_root_identity_in_l2_source'
        assert r['effective_state']=='unresolved' and r['scored'] is False

def test_named_missing_root_defeat_actual_writer_keeps_target_reason_and_ids():
    from tests.l3.test_k12_fresh_review import target_defeat
    conn=MemorySQL(); target_defeat(conn.firings,['f:moon','f:missing'])
    KaYojakaWriter().run_substep(context(conn),SubStep('class:major_gain'))
    rows=[row for sql,rows in conn.writes if 'INSERT INTO kala_activation_predicates' in sql for row in rows]
    ledger,state=json.loads(rows[0][7]),json.loads(rows[0][10])
    assert state['effective_state']=='unresolved' and not state['scored']
    assert state['null_reason']=='missing_defeat_facts'
    assert state['effective_reason']==ledger['effective_reason']
    assert state['effective_reason']['missing_fact_ids']==['f:missing']
    assert state['defeats'][0]['fact_ids']==['f:missing','f:moon']

def test_relationship_readset_drift_refuses_before_replacement(monkeypatch):
    # This SQL transport models the already-admitted projection readset;
    # settlement population checks are exercised with real SQL elsewhere.
    import importlib
    from tests.l3._dasha_projection import emulated_projection
    monkeypatch.setattr(importlib.import_module('services.ka_gochara_resonance.relationship_storage'),
                        'execute_governed_dasha_query', emulated_projection)
    from services.ka_gochara_resonance.relationship_storage import build_candidate_projection
    conn=MemorySQL(); conn.signals=[]
    build_candidate_projection(context(conn))
    source_reads=[(q,p) for q,p in conn.reads if 'FROM chart_dashas' in q or 'FROM chart_facts' in q or 'FROM ga_yoga_firings' in q]
    assert all(tuple(p)==('chart','A','a') for q,p in source_reads)
    conn.dashas[0]['lord_graha']='Venus'
    old=len(conn.writes)
    with pytest.raises(ValueError,match='input vector changed'):
        build_candidate_projection(context(conn))
    assert conn.writes[old:]==[]

EVIDENCE_CASES = [
    (None, 'defeat_evidence_missing', []),
    ([], 'defeat_evidence_missing', []),
    ([{'rule_id':'other-rule','fact_ids':['f:other']}], 'defeat_evidence_missing', []),
    ([{'rule_id':'NB-1','fact_ids':['f:moon']},
      {'rule_id':'NB-1','fact_ids':['f:missing']}],
     'defeat_evidence_ambiguous', ['f:missing', 'f:moon']),
    ([{'rule_id':'NB-1','fact_ids':['f:moon']},
      {'rule_id':'NB-1','fact_ids':['f:moon']}],
     'defeat_evidence_ambiguous', ['f:moon']),
]


def assert_unassessable_target(gain, kind, records, reason, refs):
    assert gain['effective_state']=='unresolved' and gain['scored'] is False, gain
    assert gain['null_reason'] == reason
    assert reason in gain['judgment_flags']
    assert gain['effective_reason'] == {
        'null_reason': reason,
        'conclusion_ids': ['a:sunapha:major_gain:conclusion'],
        'defeat_ids': [f'ga_yoga_firings:2:a:sunapha:major_gain:conclusion:{kind}:NB-1'],
        'evidence_fact_ids': refs,
    }
    evidence = gain[kind][0]
    assert evidence['evidence_reason'] == reason
    assert evidence['rule_id'] == 'NB-1'
    assert evidence['rule_version'] == 'fixture-v1'
    assert evidence['source_locator'] == 'fixture:source:1'
    assert evidence['fact_ids'] == refs
    assert evidence['evidence_records'] == [r for r in records or [] if r['rule_id'] == 'NB-1']


@pytest.mark.parametrize('records,reason,refs', EVIDENCE_CASES)
@pytest.mark.parametrize('kind', ['defeats', 'excepts'])
def test_fired_named_target_with_absent_or_ambiguous_evidence_record_never_licenses_target(records, reason, refs, kind):
    """A named fired rule is known; unavailable evidence cannot certify absence."""
    from services.ka_yojaka.promise_adapter import build_bundle
    from tests.l3.test_k12_fresh_review import target_defeat
    facts,firings=sources(); target_defeat(firings,['f:missing'])
    firings[1]['bhanga_rules_jsonb'][0]['kind'] = kind
    firings[1]['grounds_jsonb']={} if records is None else {'cancellation_evidence':records}
    bundle=build_bundle(facts,firings,[])
    gain=next(r for r in bundle if r['event_class_id']=='major_gain')
    assert_unassessable_target(gain, kind, records, reason, refs)
    from services.ka_yojaka.promise_adapter import mechanism_density_key
    assert mechanism_density_key(gain)[0] == 2
    unrelated=next(r for r in bundle if r['event_class_id']=='achievement_recognition')
    assert unrelated['effective_state']=='in_force'

@pytest.mark.parametrize('records,reason,refs', EVIDENCE_CASES)
@pytest.mark.parametrize('kind', ['defeats', 'excepts'])
def test_absent_named_evidence_record_is_not_persisted_as_active_by_real_writer(records, reason, refs, kind):
    from tests.l3.test_k12_fresh_review import target_defeat
    conn=MemorySQL(); target_defeat(conn.firings,['f:missing'])
    conn.firings[1]['bhanga_rules_jsonb'][0]['kind'] = kind
    conn.firings[1]['grounds_jsonb']={} if records is None else {'cancellation_evidence':records}
    KaYojakaWriter().run_substep(context(conn),SubStep('class:major_gain'))
    rows=[row for sql,rows in conn.writes if 'INSERT INTO kala_activation_predicates' in sql for row in rows]
    ledger,state=json.loads(rows[0][7]),json.loads(rows[0][10])
    assert_unassessable_target(ledger, kind, records, reason, refs)
    assert state['effective_state']=='unresolved' and state['scored'] is False, state
    assert state['null_reason'] == reason
    assert state['effective_reason'] == ledger['effective_reason']
    assert state[kind] == ledger[kind]

@pytest.mark.parametrize('refs,expected',[([], 'unresolved'),(['f:missing'],'unresolved'),(['f:moon'],'defeated')])
@pytest.mark.parametrize('kind', ['defeats', 'excepts'])
def test_same_named_firing_with_one_evidence_record_control(refs,expected,kind):
    from services.ka_yojaka.promise_adapter import build_bundle
    from tests.l3.test_k12_fresh_review import target_defeat
    facts,firings=sources(); target_defeat(firings,refs)
    firings[1]['bhanga_rules_jsonb'][0]['kind'] = kind
    gain=next(r for r in build_bundle(facts,firings,[]) if r['event_class_id']=='major_gain')
    assert gain['effective_state']==expected and gain['scored'] is False
