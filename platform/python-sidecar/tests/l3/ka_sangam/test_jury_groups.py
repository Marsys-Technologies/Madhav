import importlib
from dataclasses import replace
from services.kala_core.measure import Interval


def api(): return importlib.import_module('services.ka_sangam.jury.groups')


def test_all_groups_declare_inputs_roles_coverage_admission():
    g=api(); groups=g.declarations(Interval(0,30))
    assert {x.group_id for x in groups}=={'G-P','G-J','G-T','G-K','G-A'}
    assert all(x.inputs and x.roles and x.requested_horizon==Interval(0,30) for x in groups)
    assert all(x.coverage==() for x in groups)
    assert all(x.status=='information_unavailable' for x in groups)


def test_unadmitted_schools_stay_unavailable():
    g=api(); groups=g.declarations(Interval(0,30))
    assert [x.reason for x in groups if x.group_id in ('G-T','G-K')]==['corpus_not_admitted','kp_not_ingested']


def test_yogini_kalachakra_testimony_has_moon_ancestry():
    g=api(); a=g.declarations(Interval(0,30))[-1]
    assert a.ancestry==frozenset({'moon_nakshatra'})
    assert a.roles==frozenset({'explains'})


def test_admission_requires_complete_coverage_and_source_references():
    g=api(); p=g.declarations(Interval(0,30))[0]
    assert g.admit(p,('judge:1',),(),('review:1',)).status=='information_unavailable'
    assert g.admit(p,('judge:1',),(Interval(0,30),),('review:1',)).status=='available'
    assert g.admit(p,(),(Interval(0,30),),('review:1',)).status=='information_unavailable'


def test_local_ingestion_does_not_admit_tajaka_corpus():
    g=api(); t=g.declarations(Interval(0,30))[2]
    assert g.admit(t,('local:1',),(Interval(0,30),),('review:1',)).status=='information_unavailable'


def test_jaimini_cannot_be_admitted_by_a_partial_group_rule():
    g=api(); j=g.declarations(Interval(0,30))[1]
    assert g.admit(j,('cara:1',),(Interval(0,30),),('review:1',)).reason=='complete_method_required'
