"""K4-1: independently calculated interval and conditional-null oracles."""
import math

import pytest

from services.kala_core.measure import (
    DEFAULT_NON_IDENTITY_SHIFTS, Experiment, Interval, Witness, Verdict,
    circular_shift, elementary_segments, evaluate_experiment, jury_agreement,
    prepare_draws, shift_schedule,
)


def witness(name, *bounds):
    return Witness(name, tuple(Interval(*pair) for pair in bounds))


def test_disconnected_support_never_becomes_a_joint_envelope():
    segments = elementary_segments(Interval(0, 30), (witness('A', (0, 1)), witness('B', (29, 30))))
    assert [(s.interval.start, s.interval.end, s.support) for s in segments] == [(0, 1, frozenset({'A'})), (1, 29, frozenset()), (29, 30, frozenset({'B'}))]
    assert not any({'A', 'B'} <= s.support for s in segments)


def test_adjacent_half_open_intervals_have_no_joint_segment():
    segments = elementary_segments(Interval(0, 2), (witness('A', (0, 1)), witness('B', (1, 2))))
    assert [s.support for s in segments] == [frozenset({'A'}), frozenset({'B'})]


def test_overlapping_intervals_within_a_witness_are_unioned_and_clipped():
    segments = elementary_segments(Interval(0, 5), (witness('A', (-2, 2), (1, 3), (3, 9)),))
    assert [(s.interval.start, s.interval.end, s.support) for s in segments] == [(0, 5, frozenset({'A'}))]


def test_circular_shift_splits_at_seam_and_preserves_exact_exposure():
    shifted = circular_shift((Interval(8, 10),), Interval(0, 10), 1)
    assert shifted == (Interval(0, 1), Interval(9, 10))
    assert sum(i.duration for i in shifted) == 2


def test_shift_schedule_contains_only_non_identity_draws_and_default_is_pinned():
    assert DEFAULT_NON_IDENTITY_SHIFTS == 1023
    assert shift_schedule(Interval(0, 8), 3) == (2, 4, 6)
    schedule = shift_schedule(Interval(0, 36525))
    assert len(schedule) == 1023
    assert all(0 < offset < 36525 for offset in schedule)


def test_universally_active_witness_contributes_zero_and_is_non_informative():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 2)), witness('always', (0, 8))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    result = jury_agreement(draws, alpha=0.05)
    assert result.effect == pytest.approx(0)
    assert result.reason == 'zero_null_variance'
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert result.p_value is None and result.standardized_effect is None


def test_conditional_overlap_and_denominator_are_hand_calculated():
    # Anchor [0,2), witness [0,2). Null shifts 2/4/6 give zero overlap.
    # Conditioning on anchor exposure gives observed=1 and 3 null zeros.
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 2)), witness('w', (0, 2))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    result = jury_agreement(draws, alpha=0.3)
    assert result.observed == 1
    assert result.null_statistics == (0, 0, 0)
    assert result.denominator == 4
    # No measured null variance: even a tail rank cannot be promoted to PASS.
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE


def test_informative_null_counts_ties_and_observation_once():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 3)), witness('w', (0, 3))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    result = jury_agreement(draws, alpha=0.3)
    assert result.observed == 1
    assert result.null_statistics == pytest.approx((1/3, 0, 1/3))
    assert result.p_value == 1/4
    assert result.denominator == 4
    assert result.effect == pytest.approx(7/9)
    assert result.verdict is Verdict.PASS


def test_all_experiments_keep_their_statistic_and_conditioning_on_shared_draws():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 3)), witness('w', (0, 3))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    jury = jury_agreement(draws, alpha=0.3)
    selection = evaluate_experiment(draws, Experiment('whole_pipeline_selection', 'rerun selection on each draw'), lambda draw: max((s.interval.duration for s in draw.segments if s.support == {'w'}), default=0), alpha=0.3)
    field = evaluate_experiment(draws, Experiment('class_field_maximum', 'class/risk set held fixed'), lambda draw: max((len(s.support) for s in draw.segments), default=0), alpha=0.3)
    assert (jury.observed, selection.observed, field.observed) == (1, 0, 2)
    assert len({r.experiment.estimand for r in (jury, selection, field)}) == 3
    assert selection.experiment.conditioning != field.experiment.conditioning
    assert all(r.preparation_digest == draws.digest for r in (jury, selection, field))


def test_unexchangeable_shifts_are_diagnostic_and_cannot_claim_inferential_pass():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 3)), witness('w', (0, 3))), anchor_id='anchor', non_identity_shifts=3, exchangeable=False)
    result = jury_agreement(draws, alpha=0.3)
    assert result.surrogate_diagnostic
    assert result.p_value == 1/4
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert result.reason == 'exchangeability_not_established'


def test_zero_anchor_exposure_is_not_evaluable_not_a_denial():
    draws = prepare_draws(Interval(0, 8), (witness('anchor'), witness('w', (0, 3))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    result = jury_agreement(draws, alpha=0.05)
    assert result.verdict is Verdict.NOT_EVALUABLE
    assert result.reason == 'no_anchor_exposure'


def test_non_finite_statistic_is_not_evaluable():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 1)),), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    result = evaluate_experiment(draws, Experiment('fixture', 'fixed input'), lambda _: math.nan, alpha=0.05)
    assert result.verdict is Verdict.NOT_EVALUABLE
    assert result.reason == 'non_finite_statistic'


@pytest.mark.parametrize('start,end', [(1, 1), (2, 1), (math.nan, 3), (0, math.inf)])
def test_invalid_intervals_refuse(start, end):
    with pytest.raises(ValueError): Interval(start, end)


def test_shift_preserves_shared_dependencies_within_declared_witness_group():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 3)), witness('a', (0, 2)), witness('b', (0, 2))), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    assert all(('a' in segment.support) == ('b' in segment.support) for draw in draws.null_draws for segment in draw.segments)


def test_preparation_is_deterministic_and_input_bound():
    kwargs = dict(anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    data = (witness('anchor', (0, 3)), witness('w', (0, 2)))
    first = prepare_draws(Interval(0, 8), data, **kwargs)
    assert first == prepare_draws(Interval(0, 8), data, **kwargs)
    assert first.digest != prepare_draws(Interval(0, 9), data, **kwargs).digest


def test_tail_probability_includes_ties_and_can_fail():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 1)),), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    values = {0: 2, 2: 2, 4: 0, 6: 1}
    result = evaluate_experiment(draws, Experiment('tie_fixture', 'explicit fixed statistic'), lambda draw: values[draw.offset], alpha=0.3)
    assert result.p_value == 2/4
    assert result.verdict is Verdict.FAIL


def test_adding_universal_witness_changes_no_incremental_agreement():
    kwargs = dict(anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    data = (witness('anchor', (0, 3)), witness('w', (0, 3)))
    base = jury_agreement(prepare_draws(Interval(0, 8), data, **kwargs), alpha=0.3)
    extra = jury_agreement(prepare_draws(Interval(0, 8), (*data, witness('always', (0, 8))), **kwargs), alpha=0.3)
    assert extra.effect == pytest.approx(base.effect)
    assert extra.standardized_effect == pytest.approx(base.standardized_effect)
    assert extra.p_value == base.p_value


def test_circular_shifts_preserve_support_exposure_over_all_seams():
    horizon = Interval(-5, 5)
    for start in range(-5, 5):
        for end in range(start + 1, 6):
            for offset in range(1, 10):
                shifted = circular_shift((Interval(start, end),), horizon, offset)
                assert sum(i.duration for i in shifted) == end - start
                assert all(horizon.start <= i.start < i.end <= horizon.end for i in shifted)


def test_interval_intersection_does_not_intersect_outer_envelopes():
    from services.kala_core.measure import intersect_intervals
    actual = intersect_intervals((Interval(0, 1), Interval(29, 30)), (Interval(10, 20),), Interval(0, 30))
    assert actual == ()


@pytest.mark.parametrize('count', [0, -1, 1.5, True])
def test_invalid_shift_counts_refuse(count):
    with pytest.raises(ValueError): shift_schedule(Interval(0, 8), count)


def test_duplicate_witness_identity_cannot_multiply_support():
    with pytest.raises(ValueError, match='unique'):
        elementary_segments(Interval(0, 8), (witness('same', (0, 2)), witness('same', (0, 3))))


def test_failed_statistic_propagates_instead_of_becoming_a_null_zero():
    draws = prepare_draws(Interval(0, 8), (witness('anchor', (0, 1)),), anchor_id='anchor', non_identity_shifts=3, exchangeable=True)
    def statistic(draw):
        if draw.offset: raise RuntimeError('draw failure')
        return 1
    with pytest.raises(RuntimeError, match='draw failure'):
        evaluate_experiment(draws, Experiment('fixture', 'explicit'), statistic, alpha=0.05)


def test_fractional_universal_support_does_not_create_variance_from_roundoff():
    draws = prepare_draws(Interval(0.1, 3.7), (witness('anchor', (0.2, 1.3)), witness('always', (0.1, 3.7))), anchor_id='anchor', non_identity_shifts=31, exchangeable=True)
    result = jury_agreement(draws, alpha=0.05)
    assert result.verdict is Verdict.INSUFFICIENT_EVIDENCE
    assert result.reason == 'zero_null_variance'
    assert result.effect == pytest.approx(0, abs=1e-14)
