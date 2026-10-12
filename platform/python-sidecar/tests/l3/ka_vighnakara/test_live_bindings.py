"""K3-1b preparation only: contract holes never become quiet findings.

The conductor owns the survivor roster and source mappings. These oracles
prove refusal before that admission; they do not assert a live producer exists.
"""
import json

import pytest

from services.kala_trigger import negative_space
from tests.l3.ka_vighnakara.test_negative_space import finding


@pytest.mark.parametrize('mechanism', ['fixture:unadmitted', 'papakartari', 'badhaka'])
@pytest.mark.parametrize('exposure', ['in_risk_set', 'outside_risk_set', 'method_inapplicable'])
def test_unadmitted_trigger_is_information_unavailable(mechanism, exposure):
    assert negative_space.unavailable_trigger(mechanism, finding(exposure=exposure)).effective_state == 'information_unavailable'


@pytest.mark.parametrize('mechanism', ['fixture:unadmitted', 'papakartari', 'badhaka'])
def test_unadmitted_trigger_names_roster_and_doctrine_hole(mechanism):
    assert negative_space.unavailable_trigger(mechanism, finding()).null_reason == 'trigger_survivor_roster_and_doctrine_unadmitted'


@pytest.mark.parametrize('binding,reason', [
    ('judge_vedha', 'judge_vedha_source_mapping_unadmitted'),
    ('F1', 'f1_protection_source_mapping_unadmitted'),
    ('F2', 'f2_applicability_source_mapping_unadmitted'),
    ('trigger_mechanisms', 'trigger_survivor_roster_and_doctrine_unadmitted'),
])
def test_unbound_source_names_its_contract_reason(binding, reason):
    assert negative_space.unavailable_binding(binding, finding()).null_reason == reason


@pytest.mark.parametrize('binding', ['judge_vedha', 'F1', 'F2', 'trigger_mechanisms'])
def test_unbound_source_cannot_be_operational(binding):
    assert negative_space.unavailable_binding(binding, finding()).effective_state == 'information_unavailable'


def contract_with(tmp_path, monkeypatch, binding, **changes):
    contract = json.loads(negative_space.CONTRACT_PATH.read_text())
    contract['live_bindings'][binding].update(changes)
    path = tmp_path / 'input_contract_v1.json'
    path.write_text(json.dumps(contract))
    monkeypatch.setattr(negative_space, 'CONTRACT_PATH', path)
    return path


def test_trigger_reads_reason_from_contract(tmp_path, monkeypatch):
    contract_with(tmp_path, monkeypatch, 'trigger_mechanisms', reason='fixture:conductor_mapping_pending')
    assert negative_space.unavailable_trigger('fixture:unadmitted', finding()).null_reason == 'fixture:conductor_mapping_pending'


def test_binding_reads_current_contract_without_cached_admission(tmp_path, monkeypatch):
    path = contract_with(tmp_path, monkeypatch, 'F1', reason='fixture:first_hole')
    negative_space.unavailable_binding('F1', finding())
    contract = json.loads(path.read_text())
    contract['live_bindings']['F1']['reason'] = 'fixture:second_hole'
    path.write_text(json.dumps(contract))
    assert negative_space.unavailable_binding('F1', finding()).null_reason == 'fixture:second_hole'


def test_unknown_binding_refused():
    with pytest.raises(ValueError, match='unknown live binding'):
        negative_space.unavailable_binding('unadmitted_source', finding())


@pytest.mark.parametrize('state', ['bound', 'admitted', 'fixture_only', None])
def test_scaffold_cannot_admit_a_producer(tmp_path, monkeypatch, state):
    contract_with(tmp_path, monkeypatch, 'F1', state=state)
    with pytest.raises(ValueError, match='unbound'):
        negative_space.unavailable_binding('F1', finding())


@pytest.mark.parametrize('reason', [None, '', '   '])
def test_missing_reason_refused(tmp_path, monkeypatch, reason):
    contract_with(tmp_path, monkeypatch, 'F2', reason=reason)
    with pytest.raises(ValueError, match='reason'):
        negative_space.unavailable_binding('F2', finding())


def test_unavailable_binding_clears_planted_adverse_conclusion():
    assert negative_space.unavailable_binding('judge_vedha', finding()).rule_conclusion == 'none'


def test_unavailable_binding_has_no_licensed_release():
    assert negative_space.unavailable_binding('judge_vedha', finding()).release.kind == 'unknown'


def test_unavailable_binding_preserves_source_identity():
    context = finding()
    assert negative_space.unavailable_binding('judge_vedha', context).source == context.source


def test_unavailable_trigger_preserves_requested_mechanism():
    assert negative_space.unavailable_trigger('fixture:unadmitted', finding()).mechanism == 'fixture:unadmitted'
