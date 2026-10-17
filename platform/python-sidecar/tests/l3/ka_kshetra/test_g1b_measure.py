"""Field-specific experiment, same numeric reductions, shared shift schedule."""
import math
import pytest

from services.ka_kshetra import stage5_null as S5


def test_field_preparation_and_unchanged_reductions_are_bitwise():
    from services.kala_core.measure.field import prepare_field, FieldAccumulator
    from services.kala_core.measure import Interval, shift_schedule
    preparation=prepare_field('career',10.,non_identity_shifts=3)
    assert preparation.offsets==shift_schedule(Interval(0,10),3)
    assert preparation.experiment.estimand=='class_specific_field_maximum:career'
    assert 'transit' in preparation.experiment.conditioning
    acc=FieldAccumulator(preparation,buckets=(1,3))
    old=S5.NullAccumulator(replicates=3,horizon_days=10,buckets=(1,3))
    values=[.1,.2,.3,1.7,.4,.2,.1,.8,.2,.1]
    for i in range(3):
        stats={1:float(i+.1),3:float(i+.3)}
        acc.add_replicate(i,stats,values)
        old.add_replicate(i,stats,values)
    actual=acc.finalize(); expected=old.finalize()
    assert actual.max_stats==expected.max_stats
    assert actual.q_threshold.hex()==expected.q_threshold.hex()
    assert actual.shift_grid_step==2.5
    assert actual.replicates==3 and actual.denominator==4
    # Both production window insert paths consume this public result property.
    assert actual.resolution==.25
    assert actual.surrogate_diagnostic is True
    assert actual.exchangeable is False


def test_field_accumulator_retries_do_not_reweight_quantile():
    from services.kala_core.measure.field import prepare_field,FieldAccumulator
    a=FieldAccumulator(prepare_field('career',2.,non_identity_shifts=2),buckets=(1,))
    a.add_replicate(0,{1:2.},[1.,2.])
    a.add_replicate(0,{1:2.},[1.,2.])
    assert a.completed==1
    with pytest.raises(ValueError,match='incomplete'): a.finalize()
    with pytest.raises(ValueError,match='changed'): a.add_replicate(0,{1:3.},[1.,2.])
    with pytest.raises(ValueError): a.add_replicate(1,{1:math.nan},[1.,2.])
    a.add_replicate(1,{1:3.},[3.,4.])
    assert a.finalize().max_stats=={1:[2.,3.]}


def test_candidate_null_uses_shared_schedule_and_full_reference(monkeypatch):
    from services.kala_core.measure.field import prepare_field,FieldAccumulator
    from services.ka_kshetra import writer as W,integrator
    from services.ka_kshetra.contracts import Segment
    from types import SimpleNamespace
    seen=[]
    # Boundary-sensitive full reference is reached for every non-identity draw.
    monkeypatch.setattr(S5,'replicate_evaluator',lambda ev,delta: seen.append(delta) or ev)
    monkeypatch.setattr(S5,'_null_build_segments',lambda ev:[Segment(0,0,10,0,0)])
    p=prepare_field('career',10.,non_identity_shifts=3)
    acc=FieldAccumulator(p,buckets=(1,3))
    S5.run_field_block(object(),acc,start=0,end=2)
    S5.run_field_block(object(),acc,start=2,end=3)
    assert seen==[2.5,5.,7.5]
    assert acc.finalize().max_stats=={1:[1.]*3,3:[3.]*3}
    assert W.candidate_null_shifts()==1023
    writer=W.KaKshetraWriter(); writer._generation='candidate:g1';writer._dry_run=False
    fresh=FieldAccumulator(p,buckets=(1,3))
    monkeypatch.setattr(writer,'_require_stage4_committed',lambda *a:None)
    monkeypatch.setattr(writer,'_class_context',lambda *a:SimpleNamespace(evaluator=object(),null_accumulator=fresh))
    monkeypatch.setattr(writer,'_record_substep',lambda *a:None)
    monkeypatch.setattr(W,'candidate_null_shifts',lambda:3)
    seen.clear()
    writer._run_stage5_block(object(),'career',1,SimpleNamespace(key='stage5:career:1'))
    assert seen==[2.5,5.,7.5] and fresh.completed==3


def test_real_field_result_reaches_nonempty_window_insert():
    from datetime import date
    from services.kala_core.measure.field import prepare_field,FieldAccumulator
    from services.ka_kshetra import stage4_field as S4,writer as W,integrator
    from services.ka_kshetra.contracts import PromisePrior
    from tests.l3.ka_kshetra.fake_db import FakeConn
    ev=S4.FieldEvaluator(event_class='career',lifetime_count=1,promise=PromisePrior(.8),
        clocks=[],ladder={},envelopes=S4.EnvelopeIndex([],10),weights={},horizon_days=10)
    segments=ev.build_segments()
    acc=FieldAccumulator(prepare_field('career',10,non_identity_shifts=3))
    for i in range(3): acc.add_replicate(i,{b:0. for b in acc.buckets},[1e-10]*10)
    result=acc.finalize()
    windows=integrator.find_windows(segments,result.q_threshold)
    assert windows
    writer=W.KaKshetraWriter();writer._dry_run=False;writer._chart_id='chart'
    writer._weights_version='v0';writer._snapshot_id='snapshot'
    writer._birth_date=date(1984,2,5);writer._birth_time=None
    conn=FakeConn({})
    assert writer._write_windows_batch(conn,ev,'career',segments,windows,result,
        None,set(),None,[], 'shape_only',baseline_is_synthetic=True)>0
    row=conn.tables['kala_field_windows'][0]
    assert row['null_R']==3 and row['null_resolution']==.25


def test_shared_schedule_cannot_substitute_jury_conditioning_for_field_geometry():
    """K5-G1b-N1 negative control: equal offsets do not identify experiments."""
    from services.kala_core.measure import Interval, Witness, prepare_draws, jury_agreement
    from services.kala_core.measure.field import prepare_field
    from tests.l3.ka_kshetra.test_stage5_null import _evaluator

    jury = prepare_draws(Interval(0, 40), (
        Witness('anchor', (Interval(10, 20),)),
        Witness('other', (Interval(10, 20),)),
    ), anchor_id='anchor', non_identity_shifts=3, exchangeable=False)
    field = prepare_field('e', 40, non_identity_shifts=3)
    assert field.offsets == tuple(d.offset for d in jury.null_draws) == (10., 20., 30.)
    # The jury keeps its selected anchor fixed in every draw.
    assert [(s.interval.start, s.interval.end) for s in jury.null_draws[0].segments
            if 'anchor' in s.support] == [(10., 20.)]
    ev = _evaluator(horizon=40, hump_at=20)
    shifted = S5.replicate_evaluator(ev, field.offsets[0])
    # The field shifts its transit hump and keeps natal/clock terms fixed.
    assert shifted.envelopes.covariates_at(10)['contact_moon_ref'] == 1.
    assert ev.envelopes.covariates_at(10).get('contact_moon_ref', 0.) == 0.
    assert shifted.promise is ev.promise and shifted.clocks == ev.clocks
    result = jury_agreement(jury, alpha=.05)
    assert result.experiment.estimand == 'jury_incremental_agreement'
    assert field.experiment.estimand == 'class_specific_field_maximum:e'
    assert result.preparation_digest != field.digest
    assert result.surrogate_diagnostic is True


def test_full_reference_field_blocks_preserve_class_specific_null_statistics():
    """Sharing a schedule must not pool differently conditioned class fields."""
    from copy import copy
    from services.kala_core.measure.field import prepare_field, FieldAccumulator
    from tests.l3.ka_kshetra.test_stage5_null import _evaluator

    first = _evaluator(horizon=40, hump_at=20)
    second = copy(first)
    second.event_class = 'other_class'
    second.lifetime_count = 4.
    results = []
    for ev in (first, second):
        acc = FieldAccumulator(prepare_field(ev.event_class, 40, non_identity_shifts=3), buckets=(1, 3))
        S5.run_field_block(ev, acc, start=0, end=1)
        S5.run_field_block(ev, acc, start=1, end=3)
        actual = acc.finalize()
        reference = S5.run_null(ev, 40, replicates=4, buckets=(1, 3))
        assert actual.max_stats == reference.max_stats
        assert actual.q_threshold.hex() == reference.q_threshold.hex()
        assert actual.denominator == 4
        results.append(actual)
    assert results[0].preparation_digest != results[1].preparation_digest
    assert results[0].max_stats[1] != results[1].max_stats[1]
