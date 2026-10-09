import importlib
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
