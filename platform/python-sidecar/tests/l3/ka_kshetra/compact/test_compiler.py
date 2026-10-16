import math
import random

import pytest

from services.ka_kshetra.compact.compiler import compile_field, operator_breakpoints
from .fixtures import evaluator, primitive, curved_evaluator


def test_max_switching_roots_and_interior_peak_are_not_missed():
    ev = evaluator([
        primitive('contact_moon_ref', ((0, .75), (32, 0))),
        primitive('contact_moon_ref', ((0, 0), (32, .25))),
        primitive('contact_lagna_ref', ((0, 0), (7, 1), (32, 0))),
    ], extra=(3, 9, 23))
    knots = operator_breakpoints(ev)
    assert {0, 3, 7, 9, 16, 23, 24, 32} <= set(knots)
    trial = compile_field(ev)
    assert trial.proven
    rng = random.Random(5102)
    for t in [7, 24] + [rng.uniform(0, 32) for _ in range(100)]:
        assert trial.field.ln_lambda(t) == pytest.approx(ev.ln_lambda(t), abs=1e-12)


def test_min_moon_lagna_crossing_is_a_knot_and_a_peak():
    ev = evaluator([
        primitive('contact_moon_ref', ((0, 0), (32, 1))),
        primitive('contact_lagna_ref', ((0, 1), (32, 0))),
    ], weights={'beta:x3': 1.0}, clock=False)
    assert 16.0 in operator_breakpoints(ev)
    result = compile_field(ev)
    assert result.field.ln_lambda(16) > result.field.ln_lambda(8)
    assert result.field.ln_lambda(16) == pytest.approx(ev.ln_lambda(16), abs=1e-12)


def test_clock_is_nonzero_relevant_lord_changes_irrelevant_does_not():
    ev = evaluator()
    result = compile_field(ev)
    assert result.field.ln_lambda(16, side='left') > result.field.ln_lambda(16)
    assert result.field.ln_lambda(16, side='left') == pytest.approx(ev.ln_lambda(15), abs=1e-12)
    assert result.field.ln_lambda(16) == pytest.approx(ev.ln_lambda(17), abs=1e-12)


def test_coincident_knots_and_nonzero_support_edges_use_one_sided_limits():
    ev = evaluator([primitive('contact_moon_ref', ((2, .2), (8, .2), (8, .9), (14, .9)))])
    result = compile_field(ev)
    for t in (2, 8, 14, 16):
        for side, toward in (('left', -math.inf), ('right', math.inf)):
            assert result.field.ln_lambda(t, side=side) == pytest.approx(
                ev.ln_lambda(math.nextafter(t, toward)), abs=1e-12)


def test_curvature_certificates_bound_every_segment_not_only_midpoints():
    ev = curved_evaluator()
    result = compile_field(ev)
    assert result.proven and len(result.bounds) > 2
    for segment, bound in zip(result.field.segments(), result.bounds):
        assert bound <= 0.02
        for k in range(1, 40):
            t = segment.t_start + (segment.t_end - segment.t_start) * k / 40
            assert abs(result.field.ln_lambda(t) - ev.ln_lambda(t)) <= bound + 1e-12


def test_depth_exhaustion_is_failed_bound_not_green():
    result = compile_field(curved_evaluator(), tau=1e-12, max_depth=0)
    assert not result.proven
    assert any(s.refinement_exhausted for s in result.field.segments())
    assert max(result.bounds) > result.tau


def test_exhausted_segment_records_actual_midpoint_residual_separately_from_bound():
    ev = curved_evaluator()
    result = compile_field(ev, tau=1e-12, max_depth=0)
    for segment in result.field.segments():
        mid = (segment.t_start + segment.t_end) / 2
        residual = abs(result.field.ln_lambda(mid) - ev.ln_lambda(mid))
        assert segment.refinement_residual == pytest.approx(residual, abs=1e-15)


def test_seeded_multi_envelope_differentials_respect_local_bounds():
    rng = random.Random(510203)
    primitives = []
    for i in range(9):
        kind = ('contact_moon_ref', 'contact_lagna_ref', 'vedha')[i % 3]
        primitives.append(primitive(kind, ((0, rng.random()), (11, rng.random()), (32, rng.random())),
                                    polarity='obstructive' if kind == 'vedha' else 'supportive',
                                    subject=str(i % 2)))
    ev = evaluator(primitives)
    result = compile_field(ev)
    assert result.proven
    for _ in range(500):
        t = rng.uniform(0, 32)
        i = result.field.segment_index(t)
        assert abs(result.field.ln_lambda(t) - ev.ln_lambda(t)) <= result.bounds[i] + 1e-12


def test_obstruction_max_switches_are_included_in_curvature_bound():
    ev = evaluator([
        primitive('vedha', ((0, 0), (32, 1)), polarity='obstructive'),
        primitive('vedha', ((0, 1), (32, 0)), polarity='obstructive'),
    ])
    assert 16 in operator_breakpoints(ev)
    result = compile_field(ev)
    assert result.proven
    for t in (0.1, 7, 15.9, 16.1, 29):
        i = result.field.segment_index(t)
        assert abs(result.field.ln_lambda(t) - ev.ln_lambda(t)) <= result.bounds[i] + 1e-12


def test_interval_integrals_stay_within_declared_model_error():
    ev = curved_evaluator()
    result = compile_field(ev)
    # Independent composite midpoint quadrature on each side of clock jump.
    for a, b in ((0, 16), (16, 32), (3.25, 11.75)):
        n = 8000
        width = (b - a) / n
        reference = sum(math.exp(ev.ln_lambda(a + (i + .5) * width)) for i in range(n)) * width
        got = result.field.integral(a, b)
        assert abs(got - reference) <= reference * math.expm1(max(result.bounds)) + 1e-10


@pytest.mark.parametrize('tau,depth', [(0, 6), (-1, 6), (float('nan'), 6), (.02, -1), (.02, 7)])
def test_bad_refinement_parameters_fail(tau, depth):
    with pytest.raises(ValueError):
        compile_field(evaluator(), tau=tau, max_depth=depth)


def test_unknown_or_malformed_primitive_does_not_get_a_certificate():
    ev = evaluator([primitive('contact_moon_ref', ((1, 0), (0, 1)))])
    with pytest.raises(ValueError, match='knots'):
        compile_field(ev)
