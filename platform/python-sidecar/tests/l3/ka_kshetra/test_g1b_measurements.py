"""Scientific verdicts measure declared endpoints; test success is not K1 PASS."""
import pytest

from services.kala_core.measure import Verdict


@pytest.mark.parametrize('missing_gate', ['held_out', 'matched_controls'])
@pytest.mark.parametrize('value', [False, None, 1, 'true'])
def test_k1_requires_real_heldout_and_matched_control_protocol(missing_gate, value):
    from services.kala_core.measure.forecaster_oracles import measure_forecaster
    row = {'endpoint': 'paired hit-control alignment tail', 'minimum_n': 2,
           'pairs': [(.01, .5), (.02, .6)], 'held_out': True, 'matched_controls': True}
    row[missing_gate] = value
    result = measure_forecaster({'K1': row})['K1']
    assert result['verdict'] == Verdict.NOT_EVALUABLE
    assert result['value'] is None
    assert result['reason'] == 'held_out_matched_controls_required'


def test_four_way_evidence_and_prospective_reliability_gate():
    from services.kala_core.measure.forecaster_oracles import measure_forecaster
    empty=measure_forecaster({})
    assert set(empty)=={'K1','K2','K3','K6'}
    assert all(r['verdict']==Verdict.NOT_EVALUABLE for r in empty.values())
    evidence={
        'K1':{'endpoint':'mean paired hit-control alignment tail', 'minimum_n':2,
              'pairs':[(.01,.5),(.02,.6)],'matched_controls':True,'held_out':True},
        'K2':{'prospective_issued':False,'probabilities':[.8]*10,'outcomes':[1]*10},
        'K3':{'endpoint':'mean interval score improvement','minimum_n':2,'alpha':.1,
              'intervals':[(0.,2.,1.,0.,10.),(0.,2.,1.,0.,10.)]},
        'K6':{'endpoint':'quiet event rate below class baseline','minimum_n':2,
              'events':0,'exposure':10.,'baseline_rate':.2,'observation_mask_verified':True,'held_out':True},
    }
    rows=measure_forecaster(evidence)
    assert rows['K1']['verdict']==Verdict.PASS and rows['K1']['value']<0
    assert rows['K2']['verdict']==Verdict.NOT_EVALUABLE
    assert rows['K3']['verdict']==Verdict.PASS and rows['K3']['value']<0
    assert rows['K6']['verdict']==Verdict.PASS
    evidence['K1']['pairs']=[(.8,.1)]*2
    evidence['K3']['intervals']=[(0.,100.,1.,0.,2.)]*2
    evidence['K6']['events']=5
    rows=measure_forecaster(evidence)
    assert all(rows[k]['verdict']==Verdict.FAIL for k in ('K1','K3','K6'))
    evidence['K1']['minimum_n']=3
    assert measure_forecaster(evidence)['K1']['verdict']==Verdict.INSUFFICIENT_EVIDENCE
    evidence['K6']['observation_mask_verified']=False
    assert measure_forecaster(evidence)['K6']['verdict']==Verdict.NOT_EVALUABLE


@pytest.mark.parametrize('forecasts', [
    # Each group misses by .9, although their signed errors cancel exactly.
    [(.9, 0)] * 100 + [(.1, 1)] * 100,
    # Calibrated groups also need the missing detector and scorekeeper binding.
    [(.9, 1)] * 90 + [(.9, 0)] * 10 + [(.1, 1)] * 10 + [(.1, 0)] * 90,
    # An unambiguously bad single group cannot earn a measured verdict either.
    [(.9, 0)] * 200,
], ids=['opposing-errors', 'calibrated-groups', 'single-bad-group'])
def test_k2_requires_conditional_reliability_detector_and_samiksha_binding(forecasts):
    from services.kala_core.measure.forecaster_oracles import measure_forecaster
    evidence = {'K2': {
        'endpoint': 'stated probabilities match prospective frequencies',
        'minimum_n': 200, 'prospective_issued': True,
        'observation_mask_verified': True, 'censoring_accounted': True,
        'tolerance': .1, 'resolved_forecasts': forecasts,
    }}
    result = measure_forecaster(evidence)['K2']
    assert result['verdict'] == Verdict.NOT_EVALUABLE
    assert result['value'] is None
    assert result['reason'] == 'conditional_reliability_and_samiksha_scoring_required'
    assert result['endpoint'] == evidence['K2']['endpoint']
    assert result['n'] == 200


@pytest.mark.parametrize('missing_gate', [
    'prospective_issued', 'observation_mask_verified', 'censoring_accounted',
])
def test_reliability_requires_real_prospective_exposure_protocol(missing_gate):
    from services.kala_core.measure.forecaster_oracles import measure_forecaster
    protocol = {
        'endpoint': 'prospective probability-conditional reliability',
        'minimum_n': 2, 'prospective_issued': True,
        'observation_mask_verified': True, 'censoring_accounted': True,
        'tolerance': .1, 'resolved_forecasts': [(.5, 1), (.5, 0)],
    }
    protocol[missing_gate] = False
    result = measure_forecaster({'K2': protocol})['K2']
    assert result['verdict'] == Verdict.NOT_EVALUABLE
    assert result['value'] is None
    assert result['reason'] == 'prospective_issued_exposure_non_events_and_censoring_required'


def test_interval_score_penalizes_misses_and_width_and_invalid_inputs_are_null():
    from services.kala_core.measure.forecaster_oracles import interval_score,measure_forecaster
    assert interval_score(0.,2.,1.,.1)==2.
    assert interval_score(0.,2.,3.,.1)==22.
    assert measure_forecaster({'K3':{'endpoint':'x','minimum_n':1,'alpha':0.,
        'intervals':[(0.,2.,1.,0.,3.)]}})['K3']['verdict']==Verdict.NOT_EVALUABLE
