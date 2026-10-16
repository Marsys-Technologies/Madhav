import math
from dataclasses import replace

import numpy as np
import pytest

from services.ka_kshetra.compact.null import compute_null, compare_null
from services.ka_kshetra.dhara_null import dhara_compute_null
from services.ka_kshetra.stage5_null import DURATION_BUCKETS, _EXCEEDANCE_REL_TOL
from .fixtures import evaluator, primitive, curved_evaluator


def test_default_1023_shifts_plus_observation_matches_unchanged_operations_bitwise():
    ev = evaluator()
    reference = dhara_compute_null(ev)
    got = compute_null(ev)
    assert got == reference
    assert got.shift_count == 1023
    assert got.resolution == 1 / 1024
    assert all(len(x) == 1023 for x in got.max_stats.values())
    assert compare_null(reference, got, observations={7: (0.0, 1.0)})['passed']


def test_fractional_circular_shifts_keep_orientation_clocks_and_pooled_quantile():
    ev = evaluator([
        primitive('contact_moon_ref', ((1, 0), (3, .8), (11, 0))),
        primitive('contact_lagna_ref', ((6, 0), (13, .6), (21, 0))),
    ])
    reference = dhara_compute_null(ev, replicates=31)
    got = compute_null(ev, replicates=31)
    assert got.shift_grid_step == 32 / 31
    assert compare_null(reference, got, observations={7: (0.0, 1.0)})['passed']
    assert got.q_threshold == pytest.approx(reference.q_threshold, rel=1e-12, abs=1e-12)
    for bucket in DURATION_BUCKETS:
        np.testing.assert_allclose(got.max_stats[bucket], reference.max_stats[bucket], rtol=1e-12, atol=1e-12)


def test_bounded_field_does_not_automatically_reproduce_null_statistics():
    ev = curved_evaluator()
    reference = dhara_compute_null(ev)
    got = compute_null(ev)
    comparison = compare_null(reference, got, observations={7: (0.0, 1.0)})
    assert not comparison['passed']
    assert comparison['max_stat_abs_error'] > 1e-12
    assert comparison['q_abs_error'] > 1e-12


def test_tail_ties_must_reproduce_even_inside_float_tolerance():
    reference = dhara_compute_null(evaluator(), replicates=4)
    stats = {b: list(v) for b, v in reference.max_stats.items()}
    observed = stats[7][0]
    # null_p's actual threshold includes the established relative tie margin.
    # Cross THAT threshold, while remaining within the magnitude tolerance.
    stats[7][0] = math.nextafter(observed * (1 - _EXCEEDANCE_REL_TOL), -math.inf)
    got = replace(reference, max_stats=stats)
    result = compare_null(reference, got, observations={7: (observed,)})
    assert not result['passed']
    assert result['tail_probabilities_equal'] is False


@pytest.mark.parametrize('change', [
    {'shift_count': 4}, {'replicates': 5}, {'q_threshold': None},
    {'q_threshold': float('nan')}, {'shift_grid_step': 999},
    {'max_stats': {}}, {'horizon_days': 33}, {'alpha': .9},
])
def test_context_or_missing_evidence_never_passes(change):
    reference = dhara_compute_null(evaluator(), replicates=4)
    got = replace(reference, **change)
    assert not compare_null(reference, got, observations={7: (1.0,)})['passed']


def test_empty_tail_probe_is_not_a_green_detector():
    reference = dhara_compute_null(evaluator(), replicates=4)
    assert not compare_null(reference, reference, observations={})['passed']


@pytest.mark.parametrize('replicates,alpha', [(1, .05), (3.5, .05), (True, .05), (4, 0), (4, 1)])
def test_invalid_null_parameters_fail(replicates, alpha):
    with pytest.raises(ValueError):
        compute_null(evaluator(), replicates=replicates, alpha=alpha)


def test_noninteger_midpoint_grid_horizon_is_not_silently_rounded():
    with pytest.raises(ValueError, match='integer'):
        compute_null(evaluator(horizon=32.2))
