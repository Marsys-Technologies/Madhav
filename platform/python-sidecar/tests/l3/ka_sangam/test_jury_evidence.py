"""Evidence algebra oracles; missing implementations fail on the base."""
import importlib
import pytest
from services.kala_core.measure import Interval


def api():
    return importlib.import_module('services.ka_sangam.jury.evidence')


def test_same_contact_two_roles_increments_once():
    e=api()
    n=[e.Node('a',frozenset({'contact:1'}))]
    u=[e.Use('a','G-P',Interval(0,10),r) for r in ('corroborates','explains')]
    assert e.corroboration(n,u)==(e.Support('G-P',Interval(0,10),frozenset({'contact:1'}),frozenset()),)


@pytest.mark.parametrize('role',['selects','conditions'])
def test_selection_or_condition_root_never_corroborates(role):
    e=api(); n=[e.Node('a',frozenset({'contact:1'}))]
    u=[e.Use('a','G-P',Interval(0,10),role),e.Use('a','G-J',Interval(0,10),'corroborates')]
    assert e.corroboration(n,u)==()


def test_alias_and_stage_relocation_leave_evidence_unchanged():
    e=api(); n=[e.Node('a',frozenset({'contact:1'}))]
    u=[e.Use('a','G-P',Interval(0,10),'corroborates')]
    expected=e.corroboration(n,u)
    n.append(e.Node('moved',frozenset(),('a',)))
    assert e.corroboration(n,u+[e.Use('moved','G-P',Interval(0,10),'corroborates')])==expected


def test_selection_ancestry_inherited_and_testimony_weightless():
    e=api(); n=[e.Node('a',frozenset({'cara:1'}),selection_roots=frozenset({'cara:1'})),e.Node('b',frozenset(),('a',))]
    assert e.corroboration(n,[e.Use('b','G-J',Interval(0,10),'corroborates')])==()


def test_shared_contact_across_groups_increments_once():
    e=api(); n=[e.Node('a',frozenset({'contact:1'}))]
    u=[e.Use('a',g,Interval(0,10),'corroborates') for g in ('G-P','G-J')]
    assert len(e.corroboration(n,u))==1


def test_cyclic_or_missing_provenance_refused():
    e=api()
    with pytest.raises(ValueError):
        e.corroboration([e.Node('a',frozenset(),('a',))],[e.Use('a','G-P',Interval(0,1),'corroborates')])
    with pytest.raises(ValueError):
        e.corroboration([],[e.Use('missing','G-P',Interval(0,1),'corroborates')])


def test_shared_root_cannot_leave_a_partial_jaimini_witness():
    e=api()
    n=[e.Node('p',frozenset({'rasi:1'})),e.Node('j',frozenset({'cara:1','rasi:1'}))]
    u=[e.Use('p','G-P',Interval(0,10),'corroborates'),e.Use('j','G-J',Interval(0,10),'corroborates')]
    assert {s.group_id for s in e.corroboration(n,u)}=={'G-P'}


def test_one_selected_method_input_excludes_the_complete_assertion():
    e=api()
    n=[e.Node('j',frozenset({'cara:1','rasi:1'})),e.Node('selector',frozenset({'rasi:1'}))]
    u=[e.Use('j','G-J',Interval(0,10),'corroborates'),e.Use('selector','G-P',Interval(0,10),'selects')]
    assert e.corroboration(n,u)==()
