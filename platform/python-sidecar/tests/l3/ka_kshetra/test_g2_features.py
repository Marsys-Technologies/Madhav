"""Typed F1 feature extraction uses facts and effective conclusions, never conductance."""
from dataclasses import replace

from services.kala_core.promise import (
    Conclusion, Defeat, EdgePolarity, EventRelation, FactState, Mechanism,
    MechanismRoute, PromiseGraph, PromiseNode,
)
from services.kala_core.promise.relationships import Frame, Relationship, Role
from services.ka_kshetra.g2_features import FeatureSpec, extract_features
from services.ka_kshetra.g2_model import InputValue


def graph():
    g = PromiseGraph()
    g.add_node(PromiseNode('graha:JUPITER', 'graha', ('f1',)))
    for mid, route, fact in [('m1', MechanismRoute.ADMITTED, 'f1'),
                             ('m2', MechanismRoute.TESTIMONY, 'f2')]:
        g.add_mechanism(Mechanism(mid, route, 'marriage', ('graha:JUPITER',), (fact,), 'verse_cited'))
        g.add_conclusion(Conclusion('c'+mid, mid, FactState.PRESENT, (fact,),
                                  'target:7', EdgePolarity.SUPPORTS, EventRelation.SUPPORTS))
    return g


def edge(mid='m1', state='resolved'):
    return Relationship('e:'+mid, 'marriage', 'graha:JUPITER', Role.LORD, Frame.LAGNA,
                        mid, 'rule:1', 'citation:1', '7L', None, state)


def specs():
    return (FeatureSpec('lord_count', 'admitted_count', ('m1',), role='lord'),
            FeatureSpec('cancelled', 'effective_cancellation', ('m1',)),
            FeatureSpec('dominance', 'rule_local_dominance', ('m1',), rule_id='rule:1'))


def test_counts_by_role_deduplicate_and_exclude_testimony_other_routes():
    g = graph()
    f = extract_features(g, (edge(), edge(), edge('m2')), specs(), ('f1', 'f2'), complete=True)
    assert f['lord_count'].value == 1
    assert f['lord_count'].fact_ids == ('f1',)
    assert f['cancelled'].value == 0
    assert f['dominance'].state == 'information_unavailable'
    assert f['dominance'].value is None


def test_no_graph_coverage_never_means_evaluated_zero():
    f = extract_features(PromiseGraph(), (), specs(), (), complete=False)
    assert all(x.state == 'information_unavailable' and x.value is None for x in f.values())
    f = extract_features(graph(), (), specs(), ('f1',), complete=True)
    assert f['lord_count'].value == 0


def test_unresolved_or_missing_fact_cannot_be_a_zero_or_effective_state():
    g = graph()
    f = extract_features(g, (edge(state='unavailable'),), specs(), ('f1',), complete=True)
    assert f['lord_count'].value is None
    f = extract_features(g, (edge(),), specs(), (), complete=True)
    assert f['lord_count'].value is None
    assert f['cancelled'].value is None


def test_grounded_cancellation_and_evidence_survive():
    g = graph()
    g.add_defeat(Defeat('cm1', ('f1',), 'rule:cancel', defeat_id='d1'))
    f = extract_features(g, (edge(),), specs(), ('f1',), complete=True)
    assert f['cancelled'].value == 1
    assert f['cancelled'].fact_ids == ('f1',)
    assert 'cm1' in f['cancelled'].source and 'd1' in f['cancelled'].source
    # Formation count and effective cancellation are separate features.
    assert f['lord_count'].value == 1


def test_rule_local_dominance_requires_grounded_upstream_value():
    d = InputValue(2., 'evaluated', 'rule:1:local-comparison', ('f1',))
    f = extract_features(graph(), (edge(),), specs(), ('f1',), complete=True,
                         dominance={'rule:1': d})
    assert f['dominance'] == d
    f = extract_features(graph(), (edge(),), specs(), (), complete=True,
                         dominance={'rule:1': d})
    assert f['dominance'].value is None


def test_other_class_cannot_lend_features_and_unresolved_defeat_is_not_false():
    g = graph()
    g.add_defeat(Defeat('cm1', ('missing',), 'rule:cancel'))
    f = extract_features(g, (replace(edge(), event_class_id='career_change'),), specs(), ('f1',), complete=True)
    assert f['lord_count'].value is None
    assert f['cancelled'].value is None


def test_feature_assembly_pins_route_ownership_and_never_accepts_shadow_counts():
    import pytest
    from services.ka_kshetra.g2_features import assemble_cells
    from tests.l3.ka_kshetra.test_g2_model import model, cells, value
    g = graph()
    spec = (FeatureSpec('count', 'admitted_count', ('m1',), role='lord'),)
    raw = {'r1': tuple(replace(c, terms={}) for c in cells()['r1'])}
    got = assemble_cells(model(), raw, {'r1': spec}, g, (edge(),), ('f1',), complete=True)
    assert got['r1'][0].terms['count'].value == 1
    with pytest.raises(ValueError, match='shadow'):
        assemble_cells(model(), cells(), {'r1': spec}, g, (edge(),), ('f1',), complete=True)
    with pytest.raises(ValueError, match='route'):
        assemble_cells(model(), raw, {'r1': (replace(spec[0], mechanism_ids=('m2',)),)},
                       g, (edge(),), ('f1',), complete=True)


def test_coverage_assertion_cannot_be_replaced_with_row_presence():
    f = extract_features(graph(), (edge(),), specs(), ('f1',), complete=False)
    assert all(v.state == 'information_unavailable' for v in f.values())
    g = graph()
    assert extract_features(g, (edge('m2'),),
        (FeatureSpec('count', 'admitted_count', ('m2',), role='lord'),), ('f2',),
        complete=True)['count'].value is None


def test_graph_class_must_match_the_declared_event_model():
    import pytest
    from services.ka_kshetra.g2_features import assemble_cells
    from tests.l3.ka_kshetra.test_g2_model import model, cells
    g = graph()
    g.mechanisms['m1'] = replace(g.mechanisms['m1'], event_class_id='career_change')
    raw = {'r1': tuple(replace(c, terms={}) for c in cells()['r1'])}
    with pytest.raises(ValueError, match='class'):
        assemble_cells(model(), raw,
            {'r1': (FeatureSpec('count', 'admitted_count', ('m1',), role='lord'),)},
            g, (replace(edge(), event_class_id='career_change'),), ('f1',), complete=True)
