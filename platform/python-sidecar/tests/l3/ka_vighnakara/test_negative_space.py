"""ALGO3.4 consumer oracles; planted data proves no live doctrine admission."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]


def api():
    assert importlib.util.find_spec('services.ka_vighnakara.model') is not None, 'K3 typed model missing'
    from services.ka_vighnakara import model
    return model


def finding(**changes):
    data = dict(contract_version='k3-negative-space/1.0.0', assertion_id='fixture:vedha',
                chart_id='00000000-0000-0000-0000-000000000392', generation='candidate:fixture',
                event_class_id='career', mechanism='vedha', exposure='in_risk_set', knowledge='complete',
                rule_conclusion='obstructed', defeat_state='active', measurement='not_estimated_here',
                judge_state='active', coverage='complete', binding='fixture_only',
                interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-02-01T00:00:00Z'},
                roots={'record_ids':['fixture:judge'],'fact_ids':[],'contact_ids':[]},
                source={'text':'Phaladipika','locator':'XXVI; planted fixture'},
                what='vedha obstruction', by_what='fixture:obstructor', protections=[],
                release={'kind':'instant','instant':'2026-02-01T00:00:00Z'}, null_reason=None)
    data.update(changes)
    return api().Finding.model_validate(data)


def evaluate(**changes):
    return api().interpret(finding(**changes))


def protection(**changes):
    value = dict(target_assertion_id='fixture:vedha', kind='defeats', fact_ids=['fixture:Jupiter-kendra'],
                 source={'text':'Patel','locator':'PG2299; planted fixture'},
                 interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-02-01T00:00:00Z'})
    value.update(changes)
    return value


def test_active_vedha_is_in_force():
    assert evaluate().effective_state == 'obstruction_in_force'


def test_active_vedha_release_equals_interval_end():
    assert evaluate().release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


@pytest.mark.parametrize('axis,value', [('exposure','in_risk_set'),('knowledge','complete'),
    ('rule_conclusion','obstructed'),('defeat_state','active'),('measurement','not_estimated_here')])
def test_five_axes_survive_independently(axis,value):
    assert getattr(evaluate(),axis) == value


def test_protection_is_cancelled_never_active():
    assert evaluate(protections=[protection()]).effective_state == 'obstruction_cancelled'


def test_protection_retains_fact_ids():
    assert evaluate(protections=[protection()]).roots.fact_ids == ('fixture:Jupiter-kendra',)


def test_cancelled_candidate_conclusion_retained():
    assert evaluate(protections=[protection()]).rule_conclusion == 'obstructed'


def test_unrelated_protection_cannot_cancel():
    assert evaluate(protections=[protection(target_assertion_id='another-conclusion')]).effective_state == 'obstruction_in_force'


def test_nonoverlapping_protection_cannot_cancel():
    assert evaluate(protections=[protection(interval={'t0':'2027-01-01T00:00:00Z','t1':'2027-02-01T00:00:00Z'})]).effective_state == 'obstruction_in_force'


def test_partial_interval_protection_is_partial():
    assert evaluate(protections=[protection(interval={'t0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})]).effective_state == 'obstruction_partly_cancelled'


@pytest.mark.parametrize('kind,state', [('excepts','obstruction_cancelled'),
    ('partly_defeats','obstruction_partly_cancelled'),('contests','obstruction_contested')])
def test_targeted_edge_states(kind,state):
    assert evaluate(protections=[protection(kind=kind)]).effective_state == state


@pytest.mark.parametrize('coverage', ['absent','incomplete'])
def test_missing_coverage_never_quiet(coverage):
    assert evaluate(coverage=coverage).effective_state == 'information_unavailable'


@pytest.mark.parametrize('knowledge', ['unsearched','inputs_missing','computation_failed'])
def test_unavailable_knowledge_never_silent(knowledge):
    assert evaluate(knowledge=knowledge).effective_state == 'information_unavailable'


def test_inactive_vedha_with_complete_coverage_is_silent():
    assert evaluate(judge_state='inactive',rule_conclusion='none').effective_state == 'evaluated_silent'


def test_unqualified_vedha_retains_reason():
    assert evaluate(judge_state='unqualified',null_reason='node_obstruction_undecided').null_reason == 'node_obstruction_undecided'


def test_unbound_input_is_unavailable_even_when_planted_active():
    assert evaluate(binding='unbound',null_reason='judge_vedha_source_mapping_unadmitted').effective_state == 'information_unavailable'


def test_unknown_release_is_valid():
    assert evaluate(release={'kind':'unknown'}).release.kind == 'unknown'


def test_unknown_release_has_named_reason():
    assert evaluate(release={'kind':'unknown'}).release_reason == 'release_unknown'


def test_conditional_release_preserves_predicate():
    assert evaluate(release={'kind':'conditional','predicate_ref':'fixture:exit'}).release.predicate_ref == 'fixture:exit'


def test_rikta_produces_no_natal_row():
    assert api().interpret(finding(mechanism='rikta_tithi')) is None


@pytest.mark.parametrize('mechanism', ['daily_gandanta','kulika','transit_combustion'])
def test_non_natal_doctrines_not_admitted(mechanism):
    assert api().interpret(finding(mechanism=mechanism)) is None


def test_outside_risk_set():
    assert evaluate(exposure='outside_risk_set').effective_state == 'outside_risk_set'


def test_method_inapplicable():
    assert evaluate(exposure='method_inapplicable').effective_state == 'method_inapplicable'


def test_unresolved_defeat_not_operational():
    assert evaluate(defeat_state='unresolved').effective_state == 'information_unavailable'


@pytest.mark.parametrize('field,value', [('severity_score',0.5),('weight',0.5),('multiplier',0.45),('override_score',0.5)])
def test_numeric_weights_refused(field,value):
    with pytest.raises(ValueError): finding(**{field:value})


def test_no_obstruction_active_with_cancellation_subfield():
    assert 'obstruction_active' not in json.dumps(evaluate(protections=[protection()]).model_dump(mode='json'))


def test_invalid_release_instant_refused():
    with pytest.raises(ValueError): finding(release={'kind':'instant','instant':'2025-01-01T00:00:00Z'})


def test_unknown_binding_requires_named_reason():
    with pytest.raises(ValueError): finding(binding='unbound')


def test_missing_judge_vedha_state_never_silent():
    assert evaluate(judge_state=None,rule_conclusion='none').effective_state == 'information_unavailable'


def test_trigger_absent_doctrine_is_unqualified():
    assert importlib.util.find_spec('services.kala_trigger.negative_space') is not None, 'K3 trigger boundary missing'
    from services.kala_trigger.negative_space import unavailable_trigger
    assert unavailable_trigger('fixture:unadmitted', finding()).effective_state == 'information_unavailable'


def test_contract_survivors_are_not_invented():
    artifact=json.loads((ROOT/'services/ka_vighnakara/input_contract_v1.json').read_text())
    assert artifact['live_bindings']['trigger_mechanisms']['survivors'] is None


def test_no_downstream_reads_or_multiplier_in_new_path():
    api()
    paths=list((ROOT/'services/ka_vighnakara').glob('*.py'))+[ROOT/'services/kala_trigger/negative_space.py']
    prohibited=('kala_field','ka_kshetra','kala_convergence','compose_with_ka_sangam','severity_score','override_score')
    assert not any(word in p.read_text() for p in paths if p.name != 'storage.py' for word in prohibited)


@pytest.mark.parametrize('exposure',['outside_risk_set','method_inapplicable'])
def test_unbound_trigger_always_names_mapping_hole(exposure):
    from services.kala_trigger.negative_space import unavailable_trigger
    assert unavailable_trigger('fixture:unknown',finding(exposure=exposure)).null_reason == 'trigger_survivor_roster_and_doctrine_unadmitted'


@pytest.mark.parametrize('mechanism',['rikta_tithi','daily_gandanta','kulika','transit_combustion'])
def test_non_natal_trigger_request_is_explicitly_refused(mechanism):
    from services.kala_trigger.negative_space import unavailable_trigger
    with pytest.raises(ValueError,match='natal'): unavailable_trigger(mechanism,finding())


@pytest.mark.parametrize('conclusion',['none','supportive'])
def test_active_vedha_cannot_be_relabelled_as_quiet(conclusion):
    with pytest.raises(ValueError,match='active vedha'): finding(rule_conclusion=conclusion)


def test_unqualified_vedha_preserves_node_reason_as_unavailable():
    assert evaluate(judge_state='unqualified',null_reason='node_obstruction_undecided').effective_state == 'information_unavailable'


def test_protection_requires_cited_evidence():
    with pytest.raises(ValueError): finding(protections=[protection(fact_ids=[])])
