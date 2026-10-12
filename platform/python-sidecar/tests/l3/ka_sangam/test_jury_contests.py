import importlib
import pytest
from services.kala_core.measure import Interval


def api(): return importlib.import_module('services.ka_sangam.jury.contests')


def opinions():
    c=api()
    return [c.Opinion('career',Interval(0,10),'supportive',frozenset({'G-P'}),frozenset({'judge:1'})),c.Opinion('career',Interval(5,15),'adverse',frozenset({'G-J'}),frozenset({'cara:1'}))]


def test_opposing_witnesses_keep_separate_support_vectors():
    c=api(); r=c.contests(opinions())
    assert r[0].interval==Interval(5,10)
    assert {x.conclusion for x in r[0].sides}=={'supportive','adverse'}
    assert {x.groups for x in r[0].sides}=={frozenset({'G-P'}),frozenset({'G-J'})}


def test_duplicate_predicate_or_witness_does_not_multiply_rows():
    c=api(); o=opinions()
    assert c.contests(o+o)==c.contests(o)


def test_disjoint_and_equal_boundary_have_no_contest():
    c=api(); o=opinions()
    assert c.contests([o[0],c.Opinion('career',Interval(10,20),'adverse',o[1].groups,o[1].roots)])==()


def test_turning_point_requires_joint_multi_class_support():
    c=api(); o=opinions()
    assert c.turning_points(o,min_classes=2)==()
    extra=c.Opinion('family',Interval(5,10),'supportive',frozenset({'G-J'}),frozenset({'family:1'}))
    assert c.turning_points(o+[extra],min_classes=2)[0].interval==Interval(5,10)


def test_disjoint_cannot_create_sequence_and_duplicates_do_not_multiply():
    c=api(); o=opinions(); dis=c.Opinion('family',Interval(20,30),'supportive',frozenset({'G-J'}),frozenset({'family:1'}))
    assert c.sequences([o[0],dis])==()
    assert c.sequences(o+o)==c.sequences(o)


def test_sequence_order_is_temporal_with_joint_interval():
    c=api(); first=c.Opinion('z',Interval(0,10),'supportive',frozenset({'G-P'}),frozenset({'z:1'}))
    second=c.Opinion('a',Interval(5,15),'adverse',frozenset({'G-J'}),frozenset({'a:1'}))
    seq=c.sequences([second,first])[0]
    assert seq.earlier is first and seq.later is second
    assert seq.joint_interval==Interval(5,10)


def test_redundant_same_root_subinterval_preserves_contests():
    from dataclasses import replace
    c=api(); o=opinions(); duplicate=replace(o[0],interval=Interval(6,7))
    assert c.contests(o+[duplicate])==c.contests(o)


def test_redundant_same_root_subinterval_cannot_create_self_sequence():
    from dataclasses import replace
    c=api(); first=opinions()[0]; duplicate=replace(first,interval=Interval(6,7))
    assert c.sequences([first,duplicate])==()


def test_redundant_subinterval_preserves_sequences_and_turning_points():
    from dataclasses import replace
    c=api(); o=opinions(); duplicate=replace(o[0],interval=Interval(6,7))
    family=replace(o[1],event_class='family')
    assert c.sequences(o+[duplicate])==c.sequences(o)
    assert c.turning_points(o+[family,duplicate],min_classes=2)==c.turning_points(o+[family],min_classes=2)


def test_same_roots_with_distinct_conclusions_still_contest():
    from dataclasses import replace
    c=api(); first=opinions()[0]; adverse=replace(first,conclusion='adverse',interval=Interval(5,10))
    assert len(c.contests([first,adverse]))==1


@pytest.mark.parametrize('conclusion',['defeated','none'])
@pytest.mark.parametrize('operation',['contests','turning_points','sequences'])
def test_inactive_testimony_does_not_change_active_outputs(conclusion,operation):
    from dataclasses import replace
    c=api(); active=opinions()
    active.append(replace(active[1],event_class='family'))
    inactive=replace(active[0],interval=Interval(6,7),conclusion=conclusion)
    compute=getattr(c,operation)
    kwargs={'min_classes':2} if operation=='turning_points' else {}
    assert compute(active+[inactive],**kwargs)==compute(active,**kwargs)
