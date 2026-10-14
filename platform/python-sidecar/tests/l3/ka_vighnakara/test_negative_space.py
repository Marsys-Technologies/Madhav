"""ALGO3.4 consumer oracles; planted data proves no live doctrine admission."""
import importlib.util
import ast
import json
import re
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
    paths=list((ROOT/'services/ka_vighnakara').rglob('*.py'))+[
        ROOT/'services/kala_trigger/negative_space.py',
        ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py']
    prohibited=re.compile(r'\b(?:kala_field\w*|ka_kshetra\w*|kala_convergence|compose_with_ka_sangam)\b')
    weights={'severity_score','override_score','weight','multiplier'}
    for path in paths:
        tree=ast.parse(path.read_text())
        if path == ROOT/'pipeline/orchestrator/writers/ka_vighnakara.py':
            # The registered dispatch is in scope; the explicitly retained
            # legacy implementation keeps its old contract until cutover.
            tree=next(node for node in tree.body if isinstance(node,ast.ClassDef)
                      and node.name == 'KaVighnakaraWriter')
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                assert not prohibited.search(node.value), (path,node.lineno)
                assert node.value not in weights, (path,node.lineno)
            if isinstance(node,(ast.Name,ast.Attribute,ast.alias)):
                name=(node.id if isinstance(node,ast.Name) else
                      node.attr if isinstance(node,ast.Attribute) else node.name)
                assert not prohibited.search(name) and name not in weights, (path,node.lineno)
            if isinstance(node,ast.keyword) and node.arg in weights:
                # Only the exact, inert legacy INSERT slots are exempt.
                assert (path == ROOT/'services/ka_vighnakara/storage.py'
                        and node.arg in {'severity_score','override_score'}
                        and isinstance(node.value,ast.Constant) and node.value.value == 0), (path,node.lineno)


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


# K3 packet-exit counterexamples (M_K3_*); planted inputs only.
def test_split_full_protection_remains_cancelled():
    edges = [protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'}),
             protection(interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})]
    assert evaluate(protections=edges).effective_state == 'obstruction_cancelled'
    assert evaluate(protections=list(reversed(edges))).effective_state == 'obstruction_cancelled'


@pytest.mark.parametrize('incoming,expected', [('cancelled','obstruction_cancelled'),
    ('excepted','obstruction_cancelled'), ('unresolved','information_unavailable'),
    ('contested','obstruction_contested')])
def test_partial_protection_preserves_f1_state(incoming,expected):
    row = evaluate(defeat_state=incoming, protections=[protection(interval={
        't0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.defeat_state == incoming
    assert row.effective_state == expected


@pytest.mark.parametrize('incoming', ['cancelled','excepted','partly_cancelled'])
@pytest.mark.parametrize('edges', [[], [protection(target_assertion_id='unrelated')],
    [protection(interval={'t0':'2027-01-01T00:00:00Z','t1':'2027-02-01T00:00:00Z'})],
    [protection(kind='contests')]])
def test_cancellation_requires_retained_defeating_evidence(incoming,edges):
    row = evaluate(defeat_state=incoming,protections=edges)
    assert row.effective_state == 'information_unavailable'
    assert row.null_reason == 'defeating_evidence_unavailable'


def test_partial_edge_cannot_substantiate_full_cancellation():
    row = evaluate(defeat_state='cancelled',protections=[protection(kind='partly_defeats')])
    assert row.effective_state == 'information_unavailable'


@pytest.mark.parametrize('release', [{'kind':'instant','instant':'2026-02-01T00:00:00Z'},
    {'kind':'instant','instant':'2026-01-10T00:00:00Z'}, {'kind':'unknown'}])
def test_protection_onset_releases_remaining_obstruction(release):
    row = evaluate(protections=[protection(interval={
        't0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})],release=release)
    assert row.release.instant == datetime(2026,1,10,tzinfo=timezone.utc)
    assert row.release_reason is None


def test_split_terminal_protection_uses_earliest_continuous_onset():
    row = evaluate(protections=[
        protection(interval={'t0':'2026-01-10T00:00:00Z','t1':'2026-01-15T00:00:00Z'}),
        protection(interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.release.instant == datetime(2026,1,10,tzinfo=timezone.utc)


def test_protection_gap_is_partial_and_release_uses_terminal_suffix():
    row = evaluate(protections=[
        protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-14T00:00:00Z'}),
        protection(kind='excepts',interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert row.effective_state == 'obstruction_partly_cancelled'
    assert row.release.instant == datetime(2026,1,15,tzinfo=timezone.utc)


def test_conditional_protection_release_is_not_assumed_satisfied():
    row = evaluate(protections=[protection()],release={'kind':'conditional','predicate_ref':'fixture:condition'})
    assert row.release.kind == 'conditional'
    assert row.release.predicate_ref == 'fixture:condition'


@pytest.mark.parametrize('changes', [{'defeat_state':'unresolved'}, {'coverage':'absent'},
    {'knowledge':'unsearched'}, {'defeat_state':'contested'}])
def test_unavailable_or_contested_input_cannot_license_early_release(changes):
    row = evaluate(**changes,protections=[protection()])
    assert row.release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


@pytest.mark.parametrize('edge', [protection(kind='partly_defeats'),
    protection(kind='contests'), protection(target_assertion_id='unrelated'),
    protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'})])
def test_nonterminal_or_unqualified_protection_does_not_advance_release(edge):
    assert evaluate(protections=[edge]).release.instant == datetime(2026,2,1,tzinfo=timezone.utc)


def test_arbitrary_early_vedha_release_is_refused():
    with pytest.raises(ValueError,match='release'):
        finding(release={'kind':'instant','instant':'2026-01-10T00:00:00Z'})


@pytest.mark.parametrize('relative', ['services/ka_vighnakara/storage.py',
    'pipeline/orchestrator/writers/ka_vighnakara.py'])
def test_forecaster_read_mutant_is_detected(monkeypatch,relative):
    target = ROOT/relative
    original = Path.read_text
    def mutated(path,*args,**kwargs):
        source = original(path,*args,**kwargs)
        if path == target:
            if path.name == 'storage.py':
                source = source.replace("    if ctx.dry_run:",
                    "    ctx.db_conn.execute('SELECT * FROM kala_field')\n    if ctx.dry_run:")
            else:
                source = source.replace("        if 'negative_space_fixture_inputs' in ctx.config:",
                    "        if 'negative_space_fixture_inputs' in ctx.config:\n            ctx.db_conn.execute('SELECT * FROM kala_field')")
        return source
    monkeypatch.setattr(Path,'read_text',mutated)
    with pytest.raises(AssertionError):
        test_no_downstream_reads_or_multiplier_in_new_path()
