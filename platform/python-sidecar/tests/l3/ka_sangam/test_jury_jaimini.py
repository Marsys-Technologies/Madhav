import importlib
from dataclasses import replace
from services.kala_core.measure import Interval
from services.kala_core.clocks.methods import dasha_method


def api(): return importlib.import_module('services.ka_sangam.jury.jaimini')


def output():
    j=api()
    return j.MethodOutput('class:career',Interval(0,30),dasha_method('chara'),
        ('cara:build:1',),('rasi:directed:1',),('method:review:1',),
        (Interval(0,30),),(j.DirectedContact('rasi:directed:1','aries','leo',Interval(5,10)),),
        (j.MethodAssertion('rule:complete:1',Interval(5,10),frozenset({'cara:build:1','rasi:directed:1'})),),True)


def test_complete_method_output_retains_provenance_and_coverage():
    j=api(); o=output(); result=j.consume(o)
    assert result.group.status=='available'
    assert result.output is o
    assert result.group.source_refs==('cara:build:1','rasi:directed:1')
    assert result.support[0].interval==Interval(5,10)


def test_missing_cara_or_rasi_is_information_unavailable():
    j=api(); o=output()
    for field in ('cara_refs','rasi_refs'):
        assert j.consume(replace(o,**{field:()})).group.status=='information_unavailable'


def test_wrong_clock_never_admitted_as_jaimini():
    j=api()
    assert j.consume(replace(output(),clock=dasha_method('vimshottari'))).group.reason=='wrong_clock'


def test_partial_method_and_missing_review_are_not_witnesses():
    j=api(); o=output()
    assert j.consume(replace(o,complete=False)).support==()
    assert j.consume(replace(o,review_refs=())).support==()


def test_directed_contact_never_gains_symmetric_reverse():
    j=api(); r=j.consume(output())
    assert r.directed_contacts('aries','leo')==(Interval(5,10),)
    assert r.directed_contacts('leo','aries')==()


def test_partial_root_rule_or_uncovered_assertion_rejected():
    j=api(); o=output()
    assert j.consume(replace(o,assertions=(j.MethodAssertion('partial',Interval(5,10),frozenset({'cara:build:1'})),))).support==()
    assert j.consume(replace(o,coverage=(Interval(0,5),))).support==()


def test_complete_output_connects_to_the_same_root_graph():
    j=api(); result=j.consume(output()); nodes,uses=result.evidence()
    assert nodes[0].roots==frozenset({'cara:build:1','rasi:directed:1'})
    assert uses[0].ancestry==frozenset({'jaimini_cara','rasi_drishti'})


def test_duplicate_and_repeated_rules_share_one_root_node():
    j=api(); o=output(); a=o.assertions[0]
    result=j.consume(replace(o,assertions=(a,a)))
    nodes,uses=result.evidence()
    assert len(nodes)==1 and len(uses)==1
    assert result.support==j.consume(o).support
