"""Named semantic mutations live with the item; no separate fleet stage.

Compile only the pure interpreter in a private namespace. No source file,
class, registry or production module is changed by a mutant.
"""
import inspect

import pytest
from services.ka_vighnakara import model
from tests.l3.ka_vighnakara.test_negative_space import finding, protection


@pytest.mark.parametrize('before,after,inputs,oracle', [
    ("defeat = 'cancelled'", "defeat = 'active'", {'protections':[protection()]}, 'obstruction_cancelled'),
    ("elif finding.coverage != 'complete':", "elif False:", {'coverage':'absent'}, 'information_unavailable'),
    ("edge.target_assertion_id == assertion_id", "True", {'protections':[protection(target_assertion_id='unrelated')]}, 'obstruction_in_force'),
    ("finding.judge_state in {None, 'unqualified'}", "False", {'judge_state':None,'rule_conclusion':'none'}, 'information_unavailable'),
    ("if finding.binding == 'unbound':", "if False:", {'binding':'unbound','null_reason':'source_mapping_unadmitted'}, 'information_unavailable'),
])
def test_oracle_rejects_semantic_mutation(before,after,inputs,oracle):
    target = model.targeted_edges if before.startswith('edge.target_assertion_id') else model.interpret
    code=inspect.getsource(target)
    if code.count(before)!=1:
        pytest.fail('mutation target must remain unique')
    namespace=dict(vars(model))
    if target is not model.interpret:
        exec(compile(inspect.getsource(model.interpret),'<K3 interpreter>','exec'),namespace)
    exec(compile(code.replace(before,after),'<K3 semantic mutation>','exec'),namespace)
    value=finding(**inputs)
    assert (model.interpret(value).effective_state == oracle
            and namespace['interpret'](value).effective_state != oracle)


def test_m_k3_split_full_protection(monkeypatch):
    value = finding(protections=[
        protection(interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'}),
        protection(interval={'t0':'2026-01-15T00:00:00Z','t1':'2026-02-01T00:00:00Z'})])
    assert model.interpret(value).effective_state == 'obstruction_cancelled'
    code = inspect.getsource(model.protection_spans)
    assert code.count('start <= merged[-1][1]') == 1
    namespace = dict(vars(model))
    exec(compile(code.replace('start <= merged[-1][1]', 'start < merged[-1][1]'),
                 '<M_K3_SPLIT_FULL_PROTECTION>', 'exec'), namespace)
    monkeypatch.setattr(model,'protection_spans',namespace['protection_spans'])
    assert model.interpret(value).effective_state != 'obstruction_cancelled'


@pytest.mark.parametrize('before,after,inputs,attribute,expected', [
    ("and defeat != 'unresolved'", "", {'defeat_state':'unresolved','protections':[protection()]},
     'effective_state','information_unavailable'),
    ('elif unsupported:', 'elif False:', {'defeat_state':'cancelled'},
     'effective_state','information_unavailable'),
    ('onset = protection_release(finding)', 'onset = None', {'protections':[protection(interval={
        't0':'2026-01-10T00:00:00Z','t1':'2026-02-01T00:00:00Z'})]},
     'release',model.Release(kind='instant',instant='2026-01-10T00:00:00Z')),
])
def test_k3_review_mutations(before,after,inputs,attribute,expected):
    code=inspect.getsource(model.interpret)
    assert code.count(before) == 1
    namespace=dict(vars(model))
    exec(compile(code.replace(before,after),'<K3 review mutation>','exec'),namespace)
    value=finding(**inputs)
    assert getattr(model.interpret(value),attribute) == expected
    assert getattr(namespace['interpret'](value),attribute) != expected
