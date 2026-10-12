"""Integrated selection, alias, method and boundary qualification."""
from dataclasses import replace
import pytest
from services.ka_sangam.jury import Node, Use, Opinion
from services.kala_core.measure import Interval
from tests.l3.ka_sangam.test_jury_writer import api, fixture_input, T, H


def computed(value):
    return api().compute(api().ClassInput.model_validate(value))


def test_stage_alias_and_predicate_duplication_leave_candidate_unchanged():
    value = fixture_input()
    before = computed(value)
    value['nodes'] += (Node('alias', frozenset(), ('p',)),)
    value['uses'] += (replace(value['uses'][0], node_id='alias'),) * 20
    value['opinions'] *= 20
    assert computed(value) == before


def test_selected_or_conditioned_root_never_corroborates():
    value = fixture_input()
    value['nodes'] = (Node('p', frozenset({'selected:contact'})),)
    value['opinions'] = (replace(value['opinions'][0], roots=frozenset({'selected:contact'})),)
    assert computed(value).agreement.witness_signature == ()
    value = fixture_input()
    value['uses'] += (replace(value['uses'][0], role='conditions'),)
    assert computed(value).agreement.witness_signature == ()


def test_half_open_disjoint_intervals_create_no_contest_or_sequence():
    value = fixture_input()
    value['opinions'] = (
        Opinion('career', Interval(T, T + 1), 'supportive', frozenset({'G-P'}), frozenset({'judge:other'})),
        Opinion('career', Interval(T + 29, T + 30), 'adverse', frozenset({'G-P'}), frozenset({'judge:other'})))
    result = computed(value)
    assert result.contests == ()
    assert result.sequences == ()


def test_missing_complete_method_cannot_be_claimed_by_a_group_alias():
    value = fixture_input()
    value['groups'] = tuple(replace(g, status='available', reason=None, coverage=(H,),
        source_refs=('fixture:spoof',), review_refs=('fixture:review',)) if g.group_id == 'G-J' else g
        for g in value['groups'])
    assert 'G-J' not in computed(value).agreement.witness_signature
    value['uses'] += (Use('p', 'G-J', H, 'corroborates'),)
    with pytest.raises(ValueError):
        computed(value)


def test_zero_variance_is_noninformative_and_null_estimands_stay_distinct():
    result = computed(fixture_input())
    assert result.agreement.conditional.reason == 'zero_null_variance'
    assert result.agreement.conditional.denominator == 32
    assert result.agreement.pipeline is None


@pytest.mark.parametrize('group_id', ['G-T', 'G-K'])
def test_corpus_and_ingestion_gates_cannot_be_bypassed_by_a_group_declaration(group_id):
    value = fixture_input()
    value['groups'] = tuple(replace(g, status='available', reason=None, coverage=(H,),
        source_refs=('fixture:source',), review_refs=('fixture:review',)) if g.group_id == group_id else g
        for g in value['groups'])
    value['nodes'] += (Node('school', frozenset({'school:independent'})),)
    value['uses'] += (Use('school', group_id, H, 'corroborates'),)
    assert group_id not in computed(value).agreement.witness_signature


def complete_method(value):
    from tests.l3.ka_sangam.test_jury_jaimini import output
    method = output()
    return replace(method, event_class=value['anchor'].subject.event_class, horizon=H, coverage=(H,),
        contacts=tuple(replace(c, interval=Interval(T + c.interval.start, T + c.interval.end)) for c in method.contacts),
        assertions=tuple(replace(a, interval=Interval(T + a.interval.start, T + a.interval.end)) for a in method.assertions))


def test_complete_directed_method_enters_once_and_p8_selection_gives_no_extra_credit():
    value = fixture_input()
    value['jaimini'] = complete_method(value)
    before = computed(value)
    assert 'G-J' in before.agreement.witness_signature
    value['jaimini'] = replace(value['jaimini'], assertions=value['jaimini'].assertions * 20)
    assert computed(value) == before
    value['nodes'] += (Node('p8', frozenset({'rasi:directed:1'})),)
    value['uses'] += (Use('p8', 'G-P', H, 'selects', frozenset({'jaimini_cara'})),)
    assert 'G-J' not in computed(value).agreement.witness_signature


def test_integrated_reused_root_mutant_fails_selection_oracle(monkeypatch):
    import ast
    import importlib
    from pathlib import Path
    module = importlib.import_module('services.ka_sangam.jury.evidence')
    source = Path(module.__file__).read_text()
    target = "blocked={r.root_id for r in graph if r.selected or r.role in ('selects','conditions')}"
    assert source.count(target) == 1
    tree = ast.parse(source.replace(target, 'blocked=set()'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'corroboration')
    scope = dict(module.__dict__)
    exec(compile(ast.Module(body=[function], type_ignores=[]), module.__file__, 'exec'), scope)
    monkeypatch.setattr(api(), 'corroboration', scope['corroboration'])
    agreement = importlib.import_module('services.ka_sangam.jury.agreement')
    monkeypatch.setattr(agreement, 'corroboration', scope['corroboration'])
    with pytest.raises(AssertionError):
        test_selected_or_conditioned_root_never_corroborates()
