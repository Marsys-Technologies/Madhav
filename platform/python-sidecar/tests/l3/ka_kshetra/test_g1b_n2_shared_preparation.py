"""K5-G1b-N2: once-per-candidate preparation shared with the jury.

Authority: KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1 §6.2(2) no per-class
re-preparation, §6.2(5) schedule, segment preparation and draw machinery run
once per candidate with separate estimands, §6.2(7) resume bound to content.
"""
from copy import copy
from types import SimpleNamespace

import pytest

from services.ka_kshetra import stage4_field as S4
from services.ka_kshetra import stage5_null as S5
from services.ka_kshetra import writer as W
from services.kala_core import measure
from services.kala_core.measure import Interval, Witness, prepare_draws
from services.kala_core.measure.field import FieldAccumulator, SharedGeometry, prepare_field
from tests.l3.ka_kshetra import fixtures as F
from tests.l3.ka_kshetra.fake_db import FakeConn
from tests.l3.ka_kshetra.test_planning_safety import _plan
from tests.l3.ka_kshetra.test_stage5_null import _evaluator


def _two_classes():
    """Two classes of one chart: they share the chart's envelope index."""
    first = _evaluator(horizon=40, hump_at=20)
    second = copy(first)
    second.event_class = 'other_class'
    second.lifetime_count = 4.
    assert second.envelopes is first.envelopes
    return first, second


def test_geometry_is_shifted_once_per_offset_for_all_classes_and_estimands_stay_separate(monkeypatch):
    """§6.2(2,5): no class or draw rebuilds the shared shifted geometry; §5.5/ALGO 3.20:
    each class keeps its own full-reference statistics."""
    shifts = []
    real = S4.EnvelopeIndex.circular_shift
    monkeypatch.setattr(S4.EnvelopeIndex, 'circular_shift', lambda self, d: shifts.append(d) or real(self, d))
    first, second = _two_classes()
    schedule = measure.prepare_schedule(Interval(0, 40), 3)
    geometry = S5.shared_geometry(first.envelopes, schedule, capacity=3)
    results = []
    for ev in (first, second):
        acc = FieldAccumulator(prepare_field(ev.event_class, 40, schedule=schedule), buckets=(1, 3))
        S5.run_field_block(ev, acc, start=0, end=3, geometry=geometry)
        results.append(acc.finalize())
    assert shifts == [10., 20., 30.] and geometry.builds == 3      # not 6
    for ev, actual in zip((first, second), results):
        reference = S5.run_null(ev, 40, replicates=4, buckets=(1, 3))
        assert actual.max_stats == reference.max_stats
        assert actual.q_threshold.hex() == reference.q_threshold.hex()
    assert results[0].max_stats[1] != results[1].max_stats[1]
    assert results[0].preparation_digest != results[1].preparation_digest


def test_jury_draws_cannot_stand_in_for_field_transit_and_obstruction_geometry():
    """The separate field estimand: witness-segment draws are not envelope geometry."""
    first, _ = _two_classes()
    schedule = measure.prepare_schedule(Interval(0, 40), 3)
    jury = prepare_draws(Interval(0, 40), (Witness('anchor', (Interval(10, 20),)),
        Witness('other', (Interval(10, 20),))), anchor_id='anchor', exchangeable=False, schedule=schedule)
    substituted = SharedGeometry(schedule, first.envelopes, S5.envelope_digest(first.envelopes),
        lambda offset: next(d for d in jury.null_draws if d.offset == offset), S4.EnvelopeIndex, 3)
    with pytest.raises(ValueError, match='not field envelope geometry'):
        S5.replicate_evaluator(first, schedule.offsets[0], substituted)
    # Geometry built for another envelope set, or for an off-schedule offset, is refused too.
    foreign = S5.shared_geometry(S4.EnvelopeIndex([], 40), schedule, capacity=3)
    with pytest.raises(ValueError, match='different envelope set'):
        S5.replicate_evaluator(first, schedule.offsets[0], foreign)
    own = S5.shared_geometry(first.envelopes, schedule, capacity=3)
    with pytest.raises(ValueError, match='schedule'):
        S5.replicate_evaluator(first, 11., own)


def test_writer_runs_classes_block_major_and_builds_each_offset_once(monkeypatch):
    """The Kshetra writer's own substeps: block b of every class before block b+1."""
    monkeypatch.setattr(W, 'candidate_null_shifts', lambda: 3)
    monkeypatch.setattr(W, '_candidate_engine', lambda: 'sampled')
    monkeypatch.setattr(S5, 'DEFAULT_BLOCK_SIZE', 2)
    monkeypatch.setattr(W.KaKshetraWriter, '_discover_event_classes', lambda *a: ['aaa_class', 'zzz_class'])
    writer, _, steps = _plan(FakeConn(F.build_tables()))
    stage5 = [s.key for s in steps if s.key.startswith('stage5')]
    assert stage5 == ['stage5:aaa_class:1', 'stage5:zzz_class:1', 'stage5:aaa_class:2',
                      'stage5:zzz_class:2', 'stage5finalize:aaa_class', 'stage5finalize:zzz_class']
    shifts = []
    real = S4.EnvelopeIndex.circular_shift
    monkeypatch.setattr(S4.EnvelopeIndex, 'circular_shift', lambda self, d: shifts.append(d) or real(self, d))
    monkeypatch.setattr(W, 'HORIZON_DAYS', 40.)
    first, second = _two_classes()
    contexts = {c: SimpleNamespace(evaluator=ev, null_accumulator=writer._new_null_accumulator(c))
                for c, ev in (('aaa_class', first), ('zzz_class', second))}
    monkeypatch.setattr(writer, '_class_context', lambda conn, c: contexts[c])
    monkeypatch.setattr(writer, '_require_stage4_committed', lambda *a: None)
    monkeypatch.setattr(writer, '_bind_preparation', lambda *a: None)
    monkeypatch.setattr(writer, '_record_substep', lambda *a: None)
    writer._dry_run = False
    for key in [k for k in stage5 if not k.startswith('stage5finalize')]:
        _, c, b = key.split(':')
        writer._run_stage5_block(object(), c, int(b), SimpleNamespace(key=key))
    assert len(shifts) == 3 and all(c.null_accumulator.completed == 3 for c in contexts.values())


def test_changed_schedule_refuses_resume(monkeypatch):
    """§6.2(7): resume is content-bound — another shift schedule is another build."""
    monkeypatch.setattr(W, '_candidate_engine', lambda: 'sampled')
    tables = F.build_tables()
    writer, ctx, steps = _plan(FakeConn(tables))
    writer.run_substep(ctx, steps[0])               # prepare:replace records the ledger
    assert {r['substep_key'] for r in tables['build_substep_progress']} == {'prepare:replace'}
    fingerprint, snapshot = writer._fingerprint(), writer._snapshot_id
    monkeypatch.setattr(W, 'candidate_null_shifts', lambda: 5)
    other = W.KaKshetraWriter()
    with pytest.raises(ValueError, match='open a new candidate'):
        other.plan_substeps(ctx)
    # The schedule is a direct resume-fingerprint input, not only moved
    # transitively through the snapshot pin: hold the snapshot constant.
    writer._snapshot_id = snapshot
    assert writer._fingerprint() != fingerprint


@pytest.mark.parametrize('changed', [False, True])
def test_changed_witness_set_refuses_resume_at_the_null_stage(monkeypatch, changed):
    """The preparation digest covers the envelope (witness) set; a ledger recorded
    for another set refuses, the same set resumes without re-recording."""
    first, _ = _two_classes()
    schedule = measure.candidate_schedule(W.HORIZON_DAYS, 3)
    monkeypatch.setattr(W, 'candidate_null_shifts', lambda: 3)
    recorded = measure.prepare_candidate(schedule, S5.envelope_digest(first.envelopes))
    conn = FakeConn({'build_substep_progress': [dict(chart_id='c', asset_id=W.ASSET_ID,
        substep_key='stage5prep:' + recorded.digest, build_fingerprint='f', rows_written=0)]})
    writer = W.KaKshetraWriter(); writer._chart_id = 'c'; writer._dry_run = False
    envelopes = S4.EnvelopeIndex([S4.Primitive('contact_moon_ref', 'Sa', None, 'supportive', None,
        ((0., 0.), (5., 1.)))], 40) if changed else first.envelopes
    monkeypatch.setattr(writer, '_record_substep', lambda *a: pytest.fail('must not re-record'))
    if changed:
        with pytest.raises(ValueError, match='preparation content changed'):
            writer._bind_preparation(conn, envelopes)
    else:
        writer._bind_preparation(conn, envelopes)
        assert writer._bound_preparation.digest == recorded.digest


def test_preparation_digest_binds_schedule_and_geometry():
    a = measure.prepare_schedule(Interval(0, 40), 3)
    b = measure.prepare_schedule(Interval(0, 40), 4)
    one = measure.prepare_candidate(a, 'g1')
    assert measure.prepare_candidate(b, 'g1').digest != one.digest
    assert measure.prepare_candidate(a, 'g2').digest != one.digest
    measure.bind_preparation([], one)
    measure.bind_preparation([one.digest], one)
    with pytest.raises(ValueError, match='preparation content changed'):
        measure.bind_preparation([measure.prepare_candidate(b, 'g1').digest], one)
