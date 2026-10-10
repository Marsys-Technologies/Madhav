"""Fail-closed K6 fixture input oracles; live source admission is separate."""
from copy import deepcopy

import pytest

from pipeline.orchestrator.writers.k6_candidate import validate_bundle


def bundle():
    ref = {'build_id': 'CODEX-build', 'scenario_id': 'CODEX-scenario',
           'ayanamsha_id': 'lahiri_chitrapaksha', 'qualification': 'fixture_only',
           'source': {'text': 'CODEX', 'locator': 'CODEX/1'}}
    return {'contract_version': 'k6-123:read-models:v1',
            'as_of': '2000-01-01T00:00:00+00:00',
            'primary_ayanamsha': 'lahiri_chitrapaksha',
            'upstream_refs': {key: deepcopy(ref) for key in
                              ('judge', 'F1', 'F2', 'jury', 'negative_space', 'LEL')},
            **{key: [] for key in ('mechanisms', 'windows', 'contacts', 'periods',
                                  'negative_space', 'jury', 'contexts', 'lel')}}


def test_explicit_time_required():
    value = bundle(); del value['as_of']
    with pytest.raises(ValueError, match='as_of'): validate_bundle(value, 'chart', 'gen')


def test_naive_time_refused():
    value = bundle(); value['as_of'] = '2000-01-01'
    with pytest.raises(ValueError, match='aware'): validate_bundle(value, 'chart', 'gen')


def test_lahiri_is_explicit_primary_without_rewriting_scenarios():
    value = bundle(); value['primary_ayanamsha'] = 'true_chitra'
    with pytest.raises(ValueError, match='primary'): validate_bundle(value, 'chart', 'gen')


@pytest.mark.parametrize('pin', ['judge', 'F1', 'F2', 'jury', 'negative_space', 'LEL'])
def test_each_upstream_mapping_is_explicit(pin):
    value = bundle(); del value['upstream_refs'][pin]
    with pytest.raises(ValueError, match=pin): validate_bundle(value, 'chart', 'gen')


@pytest.mark.parametrize('field', ['build_id', 'scenario_id', 'ayanamsha_id', 'source'])
def test_source_pin_cannot_be_inferred(field):
    value = bundle(); del value['upstream_refs']['judge'][field]
    with pytest.raises(ValueError): validate_bundle(value, 'chart', 'gen')


def test_live_qualification_cannot_enter_fixture_path():
    value = bundle(); value['upstream_refs']['judge']['qualification'] = 'admitted'
    with pytest.raises(ValueError, match='fixture'): validate_bundle(value, 'chart', 'gen')


def test_mixed_scenario_cannot_silently_drop_a_join():
    value=bundle(); value['upstream_refs']['F1']['scenario_id']='CODEX-other'
    with pytest.raises(ValueError,match='scenario'): validate_bundle(value,'chart','gen')


def test_nonprimary_scenario_remains_stored_without_aliasing():
    value=bundle()
    for pin in value['upstream_refs'].values(): pin['ayanamsha_id']='true_chitra'
    assert validate_bundle(value,'chart','gen').upstream_refs['F2'].ayanamsha_id=='true_chitra'
