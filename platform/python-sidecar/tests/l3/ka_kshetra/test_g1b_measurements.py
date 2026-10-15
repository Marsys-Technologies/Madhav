"""Scientific verdicts measure declared endpoints; test success is not K1 PASS."""
from services.kala_core.measure import Verdict


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


def test_reliability_requires_real_prospective_exposure_protocol():
    from services.kala_core.measure.forecaster_oracles import measure_forecaster
    evidence={'K2':{'endpoint':'prospective frequency error minus declared tolerance',
        'minimum_n':2,'prospective_issued':True,'observation_mask_verified':True,
        'censoring_accounted':True,'tolerance':.1,'resolved_forecasts':[(.5,1),(.5,0)]}}
    assert measure_forecaster(evidence)['K2']['verdict']==Verdict.PASS
    evidence['K2']['resolved_forecasts']=[(.9,0),(.9,0)]
    assert measure_forecaster(evidence)['K2']['verdict']==Verdict.FAIL
    evidence['K2']['prospective_issued']=False
    assert measure_forecaster(evidence)['K2']['verdict']==Verdict.NOT_EVALUABLE


def test_interval_score_penalizes_misses_and_width_and_invalid_inputs_are_null():
    from services.kala_core.measure.forecaster_oracles import interval_score,measure_forecaster
    assert interval_score(0.,2.,1.,.1)==2.
    assert interval_score(0.,2.,3.,.1)==22.
    assert measure_forecaster({'K3':{'endpoint':'x','minimum_n':1,'alpha':0.,
        'intervals':[(0.,2.,1.,0.,3.)]}})['K3']['verdict']==Verdict.NOT_EVALUABLE
