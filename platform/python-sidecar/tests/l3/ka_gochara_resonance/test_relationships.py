"""K2-2 behavior oracles; frame-mixing/first-root/weight mutants defeat these."""
import importlib
from dataclasses import asdict

import pytest


def api():
    name = 'services.kala_core.promise.relationships'
    assert importlib.util.find_spec(name) is not None, 'F1 relationship resolver is missing'
    return importlib.import_module(name)


def fact(fid, subject, category, key, value, text=None, unit='degrees'):
    return dict(fact_id=fid, fact_subject=subject, fact_category=category,
                fact_key=key, fact_value_num=value, fact_value_text=text, unit=unit)


def facts():
    return [fact('lagna', 'LAGNA', 'graha_sign_attributes', 'sign_num', 5),
            fact('moon-sign', 'MOON', 'graha_sign_attributes', 'sign_num', 2),
            fact('venus', 'VEN', 'graha_position', 'longitude_sidereal', 182),
            fact('sun', 'SUN', 'graha_position', 'longitude_sidereal', 15)]


def build(**kw):
    return api().resolve_relationships('marriage', facts=facts(), sign_lords={11: 'Venus'},
                                     **kw)


def test_frame_before_rule_selects_moon_house_six_and_lagna_house_three():
    result = build(signature={'houses': ['3'], 'karakas': ['Venus']}, transit_rules=[
        dict(id=1, graha='Venus', primary_house=6, rule_type='favourable', classical_citation='PD26'),
        dict(id=2, graha='Venus', primary_house=3, rule_type='favourable', classical_citation='PD26')])
    assert {(e.frame, e.target_ref, e.rule_id) for e in result.edges if e.role in {'bhava', 'mechanism_node'}} == {
        ('lagna', '3', 'ontology:marriage'), ('moon', '6', 'bg_transit_rules:1')}


def test_one_physical_graha_two_roles():
    result = build(signature={'lords': ['7L afflicted'], 'karakas': ['Venus']})
    assert (len(result.objects), [e.role for e in result.edges]) == (1, ['karaka', 'lord'])


def test_numeric_weight_is_rejected_at_boundary():
    with pytest.raises(ValueError, match='weight'):
        build(signature={'karakas': ['Venus']}, transit_rules=[dict(weight=.5)])


def test_output_contains_no_weight_field():
    assert 'weight' not in str(asdict(build(signature={'karakas': ['Venus']})))


@pytest.mark.parametrize('key,value', [('mrityu_bhaga', 'not_fired'), ('gandanta', 'not_gandanta'),
                                        ('kartari', 'none'), ('pushkara', 'not_pushkara')])
def test_r1_negative_sensitive_checks_have_no_targets(key, value):
    result = build(signature={'karakas': ['Venus']}, sensitive=[fact('neg', 'VEN',
                   'sensitive_degree_check', key, None, value)])
    assert not [e for e in result.edges if e.role == 'sensitive_degree']


def test_r2_arudha_is_sign_interval_not_cusp_longitude():
    result = build(signature={'houses': ['7']}, arudhas=[fact('a7', 'ARUDHA_A7',
                   'arudha_pada', 'sign', 0, 'Libra')])
    edge = next(e for e in result.edges if e.role == 'arudha')
    obj = next(o for o in result.objects if o.object_id == edge.object_id)
    assert (obj.object_type, obj.sign_num, obj.longitude_deg) == ('sign_interval', 7, None)


def test_r3_unfired_yoga_has_no_dangling_target():
    assert not build(signature={}, yogas=[dict(yoga_canonical_id='gone', fired=False,
                     constituent_fact_ids=['venus'], constituent_planets=['Venus'])]).edges


def test_r3_constituents_revalidated_against_current_fact_ids():
    result = build(signature={}, yogas=[dict(yoga_canonical_id='live', fired=True,
                  constituent_fact_ids=['stale'], constituent_planets=['Venus'])])
    assert [(e.resolution_state, e.object_id) for e in result.edges] == [('unavailable', None)]


def test_r4_missing_rulership_is_unqualified():
    result = api().resolve_relationships('marriage', facts=facts(), sign_lords={},
                                        signature={'lords': ['7L']})
    assert [(e.resolution_state, e.object_id) for e in result.edges] == [('unqualified', None)]


@pytest.mark.parametrize('event_class', ['bereavement', 'illness_acute'])
@pytest.mark.parametrize('target_ref,sign_lords', [
    ('mandi_sign_distance_from_8L', {}),
    ('mandi_sign_distance_from_8L', {5: 'Sun'}),
    ('lagna_lord_minus_yamakantaka', {}),
    ('lagna_lord_minus_yamakantaka', {12: 'Mars'}),
])
def test_r4_derived_target_missing_rulership_is_unqualified(event_class, target_ref, sign_lords):
    source = facts() + [
        fact('sun-sign', 'SUN', 'graha_sign_attributes', 'sign_num', 1),
        fact('mars-sign', 'MAR', 'graha_sign_attributes', 'sign_num', 2),
        fact('mandi-sign', 'MANDI', 'sensitive_point_gulika_mandi', 'sign', None, 'Cancer'),
        fact('yamaka-sign', 'YAMAKANTAKA', 'sensitive_point_gulika_mandi', 'sign', None, 'Gemini'),
    ]
    result = api().resolve_relationships(event_class, facts=source, sign_lords=sign_lords, signature={})
    edge = next(e for e in result.edges if e.target_ref == target_ref)
    assert (edge.resolution_state, edge.object_id) == ('unqualified', None)


@pytest.mark.parametrize('target_ref,missing_fact', [
    ('mandi_sign_distance_from_8L', 'lagna'),
    ('mandi_sign_distance_from_8L', 'mars-sign'),
    ('mandi_sign_distance_from_8L', 'mandi-sign'),
    ('lagna_lord_minus_yamakantaka', 'lagna'),
    ('lagna_lord_minus_yamakantaka', 'sun-sign'),
    ('lagna_lord_minus_yamakantaka', 'yamaka-sign'),
])
def test_r4_derived_target_missing_l1_operand_stays_unavailable(target_ref, missing_fact):
    source = facts() + [
        fact('sun-sign', 'SUN', 'graha_sign_attributes', 'sign_num', 1),
        fact('mars-sign', 'MAR', 'graha_sign_attributes', 'sign_num', 2),
        fact('mandi-sign', 'MANDI', 'sensitive_point_gulika_mandi', 'sign', None, 'Cancer'),
        fact('yamaka-sign', 'YAMAKANTAKA', 'sensitive_point_gulika_mandi', 'sign', None, 'Gemini'),
    ]
    result = api().resolve_relationships('bereavement',
        facts=[f for f in source if f['fact_id'] != missing_fact],
        sign_lords={5: 'Sun', 12: 'Mars'}, signature={})
    edge = next(e for e in result.edges if e.target_ref == target_ref)
    assert (edge.resolution_state, edge.object_id) == ('unavailable', None)


def test_r5_qualifier_and_multiple_rule_roots_survive():
    result = build(signature={'lords': ['7L afflicted', '7L']}, transit_rules=[
        dict(id=i, graha='Venus', primary_house=6, rule_type='favourable', classical_citation='PD26')
        for i in (1, 2)])
    assert [(e.role, e.qualifier, e.rule_id) for e in result.edges] == [
        ('lord', None, 'ontology:marriage'), ('lord', 'afflicted', 'ontology:marriage')]


def test_multiple_roots_are_distinct_edges_for_one_object():
    result = build(signature={'houses': ['3'], 'karakas': ['Venus']}, transit_rules=[
        dict(id=i, graha='Venus', primary_house=6, rule_type='favourable', classical_citation=f'PD26:{i}')
        for i in (1, 2)])
    assert len({e.edge_id for e in result.edges if e.role == 'mechanism_node'}) == 2


def test_r6_mechanism_with_missing_moon_is_unavailable():
    result = api().resolve_relationships('marriage', facts=[f for f in facts() if f['fact_id'] != 'moon-sign'],
        sign_lords={}, signature={'houses': ['3'], 'karakas': ['Venus']}, transit_rules=[
        dict(id=1, graha='Venus', primary_house=6, rule_type='favourable', classical_citation='PD26')])
    assert [(e.resolution_state, e.object_id) for e in result.edges if e.role == 'mechanism_node'] == [('unavailable', None)]


def test_missing_longitude_cannot_be_resolved():
    result = api().resolve_relationships('marriage', facts=[f for f in facts() if f['fact_id'] != 'venus'],
                                       sign_lords={}, signature={'karakas': ['Venus']})
    assert [(e.resolution_state, e.object_id) for e in result.edges] == [('unavailable', None)]


def test_portfolio_and_karaka_share_object_without_duplicate_role():
    result = build(signature={'karakas': ['Venus']}, dasha_lords=['Venus', 'Venus'])
    assert (len(result.objects), {e.role for e in result.edges}) == (1, {'karaka', 'dasha_lord_portfolio'})


def test_promise_route_projects_every_referenced_physical_fact():
    result = build(signature={}, promises=[dict(mechanism_id='m1', fact_ids=['venus', 'sun'],
        binding={'frame': 'moon', 'rule_id': 'r1'}, source='L1:formation')])
    assert ({o.object_id for o in result.objects}, {e.mechanism_id for e in result.edges}) == ({'graha:VEN', 'graha:SUN'}, {'m1'})


def test_repeat_input_and_reordered_sources_are_identical():
    source = [dict(mechanism_id='m1', fact_ids=['venus', 'sun'], binding={'frame': 'moon', 'rule_id': 'r1'}, source='L1')]
    assert build(signature={}, promises=source) == build(signature={}, promises=source)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, 360])
def test_invalid_degree_is_not_a_physical_target(value):
    result = api().resolve_relationships('marriage', facts=[fact('x', 'VEN', 'graha_position',
        'longitude_sidereal', value)], sign_lords={}, signature={'karakas': ['Venus']})
    assert result.objects == ()


def test_requested_bhava_arudha_missing_fact_has_explicit_unavailable_edge():
    result = build(signature={'houses': ['7']})
    assert [(e.resolution_state, e.object_id) for e in result.edges if e.role == 'bhava_arudha'] == [('unavailable', None)]


def test_yoga_must_reference_the_same_constituent_planet():
    result = build(signature={}, yogas=[dict(yoga_canonical_id='live', fired=True,
        constituent_fact_ids=['sun'], constituent_planets=['Venus'])])
    assert [(e.resolution_state, e.object_id) for e in result.edges] == [('unavailable', None)]


def test_mandi_distance_and_yamakantaka_keep_verse_locators():
    source = facts() + [fact('mars-sign', 'MAR', 'graha_sign_attributes', 'sign_num', 2),
        fact('mandi-sign', 'MANDI', 'sensitive_point_gulika_mandi', 'sign', None, 'Cancer'),
        fact('yamaka-sign', 'YAMAKANTAKA', 'sensitive_point_gulika_mandi', 'sign', None, 'Gemini')]
    result = api().resolve_relationships('bereavement', facts=source, sign_lords={12: 'Mars'}, signature={})
    mandi = next(e for e in result.edges if e.role == 'gulika_mandi_distance')
    assert (mandi.object_id, mandi.rule_id, mandi.provenance) == ('sign:6', 'PG220:C1 śl.26', 'PG220:C1 śl.26')


def test_promise_subject_sign_fact_resolves_to_real_graha():
    result = build(signature={}, promises=[dict(mechanism_id='m1', fact_ids=['moon-sign'],
        binding={'frame': 'moon', 'rule_id': 'r1'}, source='L1')])
    # A sign fact without its longitude stays unavailable, not a zero-degree object.
    assert [(e.resolution_state, e.object_id) for e in result.edges] == [('unavailable', None)]
