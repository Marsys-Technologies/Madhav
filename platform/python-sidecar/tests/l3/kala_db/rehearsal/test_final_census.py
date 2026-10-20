"""K9-4 consumes K9-5's complete measurements and separately authored expectations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
import kala_rehearsal_census as census
import asset_census as ac
from services.kala_core import final_rebuild


@pytest.fixture
def inputs(tmp_path):
    report = census.build_report(ROOT)
    decl = (ROOT / census.DECLARATIONS).read_bytes()
    records = [dict(asset_id=row['asset'], layer='L3', asset_kind='data', measurements={
        name: {'v': 'NO_DETECTOR' if criterion['detector'] == 'NONE' else 'FAIL'}
        for name, criterion in report['criteria'].items()}) for row in report['assets']]
    source = dict(L3=dict(layer='L3', generated='2026-10-16T12:00:00Z', chart_scope=final_rebuild.CANONICAL_CHART,
        census_target={'declared': 'disposable'}, registry_revision=ac.REGISTRY_REVISION,
        registry_fingerprint=ac.registry_fingerprint(), declarations_sha256=hashlib.sha256(decl).hexdigest(),
        declarations_version=json.loads(decl)['version'], assets=records))
    # Independent planted oracle: every measured detector is deliberately FAIL.
    # Never copy observed rollups to make the expected side agree.
    expected = dict(schema='kala.final_expectations/1', author='independent-fixture-oracle',
        basis=['test_final_census.py: deliberately planted FAIL on every detector'],
        expectations={row['asset_id']: {gate: 'FAIL' for gate in ac.CELL_GATES} for row in records})
    a,b = tmp_path/'census.json', tmp_path/'expected.json'
    a.write_text(json.dumps(source)); b.write_text(json.dumps(expected))
    return a,b,source,expected


def test_complete_census_matches_independent_predictions_without_turning_failures_into_acceptance(inputs):
    a,b,_,_ = inputs
    assert hasattr(final_rebuild, 'inspect_census'), 'complete K9-5 population/expectation inspection is missing'
    result = final_rebuild.inspect_census(a,b)
    assert result['population_complete'] is True and result['expectations_match'] is True
    assert result['observed_assets'] == 25 and result['observed_gates'] == 225
    assert result['census_sha256'] == hashlib.sha256(a.read_bytes()).hexdigest()
    assert result['expectations_sha256'] == hashlib.sha256(b.read_bytes()).hexdigest()
    assert len(result['non_passing_gates']) == 225
    assert result['production_acceptance'] is None


@pytest.mark.parametrize('mutation', ['missing_asset','missing_measurement','missing_expectation_asset','missing_expectation_gate',
                                    'null_expectation','wrong_expectation','invented_pass','unmeasured','unknown_asset','no_author','no_basis'])
def test_partial_unmeasured_self_expected_and_disagreeing_census_refused(inputs, mutation):
    a,b,source,expected = inputs
    assert hasattr(final_rebuild, 'inspect_census'), 'complete K9-5 population/expectation inspection is missing'
    record=source['L3']['assets'][0]; aid=record['asset_id']
    if mutation == 'missing_asset': source['L3']['assets'].pop()
    elif mutation == 'missing_measurement': record['measurements'].pop('Null.schema_default')
    elif mutation == 'missing_expectation_asset': del expected['expectations'][aid]
    elif mutation == 'missing_expectation_gate': del expected['expectations'][aid]['Idem']
    elif mutation == 'null_expectation': expected['expectations'][aid]['Idem']=None
    elif mutation == 'wrong_expectation': expected['expectations'][aid]['Idem']='PASS'
    elif mutation == 'invented_pass': record['measurements']['Carr.D2']={'v':'PASS'}
    elif mutation == 'unmeasured': record['measurements']['Idem.pattern']={'v':'ERRORED'}
    elif mutation == 'unknown_asset': expected['expectations']['ka_invented']={gate:'FAIL' for gate in ac.CELL_GATES}
    elif mutation == 'no_author': expected['author']=''
    else: expected['basis']=[]
    a.write_text(json.dumps(source)); b.write_text(json.dumps(expected))
    with pytest.raises(ValueError): final_rebuild.inspect_census(a,b)
