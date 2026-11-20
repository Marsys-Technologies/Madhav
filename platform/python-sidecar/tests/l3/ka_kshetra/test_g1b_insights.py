"""G1(f): reachable predicates, explicit observation horizons and typed silence."""
from types import SimpleNamespace
import pytest

from services.ka_kshetra import stage65_insights as S
from services.ka_kshetra import writer as W
from services.ka_kshetra.contracts import PromisePrior


def window(**kw):
    values = dict(window_id='w', event_class='career', t_start=1., t_end=2.,
                  t_peak=1.5, lambda_peak=2., salience=.7, confidence_tier=None)
    return S.InsightWindow(**(values | kw))


def test_normalized_promise_absence_is_typed_model_silence():
    candidate = S.detect_absence_of_expected('career', .8, [], 0., 100.)
    assert candidate is not None
    assert candidate.statement_params['state'] == 'evaluated_silent'
    assert candidate.statement_params['probability_target'] is None
    assert S.detect_absence_of_expected('career', .59, [], 0., 100.) is None
    assert S.detect_absence_of_expected('career', .8, [window()], 0., 100.) is None


@pytest.mark.parametrize('prior', [-.1, 1.01, 6., float('inf'), float('-inf'), float('nan')])
def test_absence_never_converts_invalid_normalized_prior_into_a_finding(prior):
    # ALGO §3.20: P is normalized, not the former six-point promise grade.
    assert S.detect_absence_of_expected('career', prior, [], 0., 100.) is None


@pytest.mark.parametrize('completed', [False, True])
def test_absence_requires_an_evaluated_field_not_merely_an_empty_window_set(monkeypatch, completed):
    from tests.l3.ka_kshetra.fake_db import FakeConn
    writer = W.KaKshetraWriter()
    writer._dry_run = False
    writer._chart_id = 'chart'; writer._snapshot_id = 'snapshot'
    writer._weights_version = 'v0'; writer._event_classes = ['career']; writer._skipped = []
    monkeypatch.setattr(writer, '_load_committed_windows', lambda c: [])
    monkeypatch.setattr(writer, '_load_salience', lambda c: {})
    monkeypatch.setattr(writer, '_load_window_fact_ids', lambda c: {})
    monkeypatch.setattr(writer, '_reversal_inputs', lambda *a: [])
    monkeypatch.setattr(writer, '_record_substep', lambda *a: None)
    monkeypatch.setattr(W.S4, 'load_promise_prior', lambda *a: PromisePrior(.8, fact_ids=('fact',)))
    conn = FakeConn({'kala_field': [{'event_class': 'career'}] if completed else []})
    result = writer._run_stage65(conn, SimpleNamespace(key='stage65'))
    assert result.rows_inserted == int(completed)
    rows = conn.tables.get('kala_insights', [])
    assert [r['insight_type'] for r in rows] == (['absence_of_expected'] if completed else [])


def test_zero_windows_still_runs_absence_for_completed_class(monkeypatch):
    writer = W.KaKshetraWriter()
    writer._dry_run=False; writer._chart_id='chart'; writer._snapshot_id='snapshot'
    writer._weights_version='v0'; writer._event_classes=['career','skipped']
    writer._skipped=[{'event_class':'skipped'}]
    monkeypatch.setattr(writer, '_load_committed_windows', lambda c: [])
    monkeypatch.setattr(writer, '_load_salience', lambda c: {})
    monkeypatch.setattr(writer, '_load_window_fact_ids', lambda c: {})
    monkeypatch.setattr(writer, '_reversal_inputs', lambda *a: [])
    monkeypatch.setattr(writer, '_record_substep', lambda *a: None)
    monkeypatch.setattr(writer, '_require_stage4_committed', lambda *a: None)
    monkeypatch.setattr(W.S4, 'load_promise_prior', lambda *a: PromisePrior(.8, fact_ids=('fact',)))
    class Conn:
        def __init__(self): self.rows=[]
        def cursor(self): return self
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def execute(self, sql, params): self.rows.append((sql,params))
    conn=Conn()
    result=writer._run_stage65(conn,SimpleNamespace(key='stage65'))
    assert result.rows_inserted==1
    assert conn.rows[0][1][2]=='absence_of_expected'
    assert conn.rows[0][1][3]=='career'
    assert 'fact' in conn.rows[0][1][9]


def test_obstruction_engages_and_releases_without_impossible_positive_values():
    samples=[S.ReversalSample(t, obstruction, 2., 1.) for t,obstruction in
             [(0.,0.),(1.,-.2),(2.,-.4),(3.,0.)]]
    rows=S.detect_reversal('career',window(),samples)
    assert [r.statement_params['t_cross'] for r in rows]==[1.,3.]
    assert all(r.statement_params['obstruction_crossed'] for r in rows)
    assert all(not r.statement_params['lambda_crossed'] for r in rows)


def test_scarcity_requires_enough_searched_exposure_and_same_class():
    w=window()
    assert S.detect_scarcity(w,[],horizon_end=100.) is None
    found=S.detect_scarcity(w,[],horizon_end=2000.)
    assert found.statement_params['gap_days']==1998.
    assert found.statement_params['right_censored'] is True
    other=window(window_id='other',event_class='marriage',t_start=3.,t_end=4.)
    assert S.detect_scarcity(w,[other],horizon_end=2000.) is not None
    adjacent=window(window_id='adjacent',t_start=2.,t_end=3.)
    assert S.detect_scarcity(w,[adjacent],horizon_end=2000.) is None


def test_unwired_contrast_is_explicitly_removed_from_candidate_catalog():
    assert 'contrast' not in S.NON_LEL_INSIGHT_TYPES
    assert S.DISABLED_INSIGHT_TYPES['contrast']=='baseline_input_not_bound'
