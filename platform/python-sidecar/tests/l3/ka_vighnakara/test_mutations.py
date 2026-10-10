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
    ("edge.target_assertion_id == finding.assertion_id", "True", {'protections':[protection(target_assertion_id='unrelated')]}, 'obstruction_in_force'),
    ("finding.judge_state in {None, 'unqualified'}", "False", {'judge_state':None,'rule_conclusion':'none'}, 'information_unavailable'),
    ("if finding.binding == 'unbound':", "if False:", {'binding':'unbound','null_reason':'source_mapping_unadmitted'}, 'information_unavailable'),
])
def test_oracle_rejects_semantic_mutation(before,after,inputs,oracle):
    code=inspect.getsource(model.interpret)
    if code.count(before)!=1:
        pytest.fail('mutation target must remain unique')
    namespace=dict(vars(model))
    exec(compile(code.replace(before,after),'<K3 semantic mutation>','exec'),namespace)
    value=finding(**inputs)
    assert (model.interpret(value).effective_state == oracle
            and namespace['interpret'](value).effective_state != oracle)
