"""Fresh independent K12 composition probes on pinned main."""
import pytest
from services.ka_yojaka.promise_adapter import build_bundle
from tests.l3.ka_yojaka.test_source_adapter import sources
from services.kala_core.promise import Defeat, EffectiveState
from tests.l3.kala_core.promise.test_promise import graph, FACT_ID


def target_defeat(firings, refs):
    firings[1]['bhanga_rules_jsonb'] = [dict(rule_id='NB-1', kind='defeats',
        target_yoga_canonical_id='sunapha', target_event_class_id='major_gain',
        rule_version='fixture-v1', source_locator='fixture:source:1')]
    firings[1]['grounds_jsonb'] = {'cancellation_evidence': [{'rule_id':'NB-1','fact_ids':refs}]}


@pytest.mark.parametrize('roots', [[], ['f:missing'], ['f:moon','f:missing']])
@pytest.mark.parametrize('kind', ['defeats', 'excepts'])
def test_named_cancellation_with_missing_evidence_never_licenses_target(roots, kind):
    facts, firings = sources()
    target_defeat(firings, roots)
    firings[1]['bhanga_rules_jsonb'][0]['kind'] = kind
    gain=next(r for r in build_bundle(facts,firings,[]) if r['event_class_id']=='major_gain')
    assert gain['effective_state']=='unresolved', gain
    assert gain['scored'] is False
    assert gain['defeats'] or gain['excepts'] or gain['cancellation_unqualified'], 'target evidence must remain auditable'
    evidence = gain[kind][0]
    assert evidence['fact_ids'] == sorted(roots)
    assert evidence['rule_id'] == 'NB-1'
    assert evidence['source_locator'] == 'fixture:source:1'
    assert gain['null_reason'] == 'missing_defeat_facts'
    assert gain['effective_reason'] == {
        'null_reason': 'missing_defeat_facts',
        'conclusion_ids': ['a:sunapha:major_gain:conclusion'],
        'defeat_ids': [f'ga_yoga_firings:2:a:sunapha:major_gain:conclusion:{kind}:NB-1'],
        'missing_fact_ids': sorted(set(roots) - {'f:moon'}),
    }
    other = next(r for r in build_bundle(facts, firings, [])
                 if r['event_class_id'] == 'achievement_recognition')
    assert other['effective_state'] == 'in_force'


@pytest.mark.parametrize('roots', [(), ('f:missing',), (FACT_ID, 'f:missing')])
def test_graph_unknown_defeat_control(roots):
    subject=graph(); subject.add_defeat(Defeat('c:career', roots, 'fixture:rule'))
    assert subject.effective_state('c:career',{FACT_ID}) is EffectiveState.UNRESOLVED
    result = subject.effective_result('c:career', {FACT_ID})
    assert result.null_reason == 'missing_defeat_facts'
    assert result.conclusion_ids == ('c:career',)
    assert result.defeat_ids == ('fixture:rule',)
    assert result.missing_fact_ids == tuple(sorted(set(roots) - {FACT_ID}))


def test_grounded_target_defeat_control():
    facts, firings=sources(); target_defeat(firings,['f:moon'])
    gain=next(r for r in build_bundle(facts,firings,[]) if r['event_class_id']=='major_gain')
    assert gain['effective_state']=='defeated'


def test_conditions_event_binding_is_accepted_by_f1_adapter():
    from services.ka_yojaka.promise_adapter import EventBinding
    facts,firings=sources()
    binding=EventBinding('sunapha','major_gain','fixture:condition','v1','fixture:source',relation='conditions')
    bundle=build_bundle(facts,firings,[],bindings=(binding,))
    gain=next(r for r in bundle if r['event_class_id']=='major_gain')
    assert gain['binding']['relation']=='conditions'
    assert gain['effective_state'] == 'unresolved'
    assert gain['scored'] is False
    assert gain['null_reason'] == 'conditions_unassessed'
    assert gain['effective_reason']['conclusion_ids'] == ['a:sunapha:major_gain:conclusion']


def test_conditions_binding_does_not_contest_an_opposing_conclusion():
    from services.ka_yojaka.promise_adapter import EventBinding
    facts, firings = sources()
    firings[1]['bhanga_active'] = False
    bindings = (
        EventBinding('sunapha', 'major_gain', 'fixture:condition', 'v1',
                     'fixture:source', relation='conditions'),
        EventBinding('neecha_bhanga_raja_yoga', 'major_gain', 'fixture:adverse',
                     'v1', 'fixture:source', relation='opposes'),
    )
    bundle = build_bundle(facts, firings, [], bindings=bindings)
    conditional = next(r for r in bundle if r['canonical_id'] == 'sunapha')
    adverse = next(r for r in bundle if r['canonical_id'] == 'neecha_bhanga_raja_yoga')
    assert conditional['null_reason'] == 'conditions_unassessed'
    assert adverse['effective_state'] == 'in_force'
