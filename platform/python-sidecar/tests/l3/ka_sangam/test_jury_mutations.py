"""Named code mutants must defeat the actual semantic oracle, never skip it."""
import ast
import importlib
from pathlib import Path
import pytest


def mutate(monkeypatch,module_name,function,old,new,*,method_class=None):
    module=importlib.import_module('services.ka_sangam.jury.'+module_name)
    source=Path(module.__file__).read_text()
    assert source.count(old)==1, 'mutation target drifted'
    tree=ast.parse(source.replace(old,new))
    scope=tree.body if method_class is None else next(n.body for n in tree.body if isinstance(n,ast.ClassDef) and n.name==method_class)
    node=next(n for n in scope if isinstance(n,ast.FunctionDef) and n.name==function)
    namespace=dict(module.__dict__)
    exec(compile(ast.Module(body=[node],type_ignores=[]),module.__file__,'exec'),namespace)
    monkeypatch.setattr(module if method_class is None else getattr(module,method_class),function,namespace[function])


@pytest.mark.parametrize('module,function,old,new,oracle',[
    ('evidence','corroboration',"r.selected or r.role in ('selects','conditions')","r.selected",'test_selection_or_condition_root_never_corroborates'),
    ('evidence','corroboration','any(root in owner and owner[root]!=s.group_id for root in s.roots)','False','test_shared_root_cannot_leave_a_partial_jaimini_witness'),
    ('evidence','evidence_graph','roots.update(r)','roots.update(())','test_alias_and_stage_relocation_leave_evidence_unchanged'),
])
def test_evidence_mutants_fail_named_oracles(monkeypatch,module,function,old,new,oracle):
    mutate(monkeypatch,module,function,old,new)
    tests=importlib.import_module('tests.l3.ka_sangam.test_jury_evidence')
    with pytest.raises((AssertionError,ValueError)):
        getattr(tests,oracle)(*(['selects'] if oracle.startswith('test_selection') else []))


def test_symmetric_rasi_mutant_fails_directed_fixture(monkeypatch):
    mutate(monkeypatch,'jaimini','directed_contacts','c.caster==caster and c.target==target',
           '(c.caster==caster and c.target==target) or (c.caster==target and c.target==caster)',method_class='JaiminiResult')
    tests=importlib.import_module('tests.l3.ka_sangam.test_jury_jaimini')
    with pytest.raises(AssertionError):
        tests.test_directed_contact_never_gains_symmetric_reverse()


def test_wrong_clock_mutant_fails_clock_fixture(monkeypatch):
    mutate(monkeypatch,'jaimini','consume',"output.clock != dasha_method('chara')","False")
    tests=importlib.import_module('tests.l3.ka_sangam.test_jury_jaimini')
    with pytest.raises(AssertionError):
        tests.test_wrong_clock_never_admitted_as_jaimini()


def test_half_open_mutant_fails_contest_boundary_oracle(monkeypatch):
    # Count mere boundary contact as a sequence; the joint-duration oracle
    # rejects the invented zero-length segment before it becomes an output.
    mutate(monkeypatch,'contests','sequences','a.interval.start<b.interval.start<min(a.interval.end,b.interval.end)',
           'a.interval.start<b.interval.start<=min(a.interval.end,b.interval.end)')
    c=importlib.import_module('services.ka_sangam.jury.contests')
    a=c.Opinion('a',c.Interval(0,10),'supportive',frozenset({'G-P'}),frozenset({'a'}))
    b=c.Opinion('b',c.Interval(10,20),'adverse',frozenset({'G-J'}),frozenset({'b'}))
    with pytest.raises(ValueError):
        c.sequences([a,b])


@pytest.mark.parametrize('old,new,oracle',[
    ('output.contract_version != CONTRACT_VERSION','False','test_complete_output_requires_pinned_contract_version'),
    ('any(a.conclusion not in CONCLUSIONS for a in output.assertions)','False','test_complete_assertion_requires_typed_conclusion'),
])
def test_incomplete_contract_mutants_fail_admission_oracles(monkeypatch,old,new,oracle):
    mutate(monkeypatch,'jaimini','consume',old,new)
    tests=importlib.import_module('tests.l3.ka_sangam.test_jury_jaimini')
    with pytest.raises(AssertionError):
        getattr(tests,oracle)()


@pytest.mark.parametrize('function,old,new,oracle',[
    ('_segments','opinions=_canonical(opinions)','opinions=tuple(sorted(set(opinions),key=_key))','test_redundant_same_root_subinterval_preserves_contests'),
    ('sequences','sorted(_canonical(opinions),key=lambda o:(o.interval.start,_key(o)))','sorted(set(opinions),key=lambda o:(o.interval.start,_key(o)))','test_redundant_same_root_subinterval_cannot_create_self_sequence'),
])
def test_interval_alias_mutants_fail_invariance_oracles(monkeypatch,function,old,new,oracle):
    mutate(monkeypatch,'contests',function,old,new)
    tests=importlib.import_module('tests.l3.ka_sangam.test_jury_contests')
    with pytest.raises(AssertionError):
        getattr(tests,oracle)()
