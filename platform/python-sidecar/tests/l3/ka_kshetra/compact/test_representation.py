import math
import pytest

from services.ka_kshetra.contracts import Segment
from services.ka_kshetra import integrator
from services.ka_kshetra.compact.representation import CompactField


def rows():
    return [Segment(0, 0.0, 2.0, -0.0, 0.125),
            Segment(1, 2.0, 5.0, 2.0, -0.25, 3, True, 0.04)]


def test_lossless_structure_coefficients_and_metadata():
    source = rows()
    packed = CompactField.from_segments(source)
    assert packed.segments() == tuple(source)
    assert packed.segments()[0].alpha.hex() == source[0].alpha.hex()
    source.clear()
    assert len(packed.segments()) == 2


def test_one_sided_values_at_discontinuities_and_horizon():
    field = CompactField.from_segments(rows())
    assert field.ln_lambda(2.0, side='left') == 0.25
    assert field.ln_lambda(2.0, side='right') == 2.0
    assert field.ln_lambda(0.0) == 0.0
    assert field.ln_lambda(5.0, side='left') == 1.25
    for t, side in ((-1, 'right'), (0, 'left'), (5, 'right'), (6, 'left')):
        with pytest.raises(ValueError, match='outside'):
            field.ln_lambda(t, side=side)
    with pytest.raises(ValueError, match='side'):
        field.ln_lambda(1, side='neither')


@pytest.mark.parametrize('a,b', [(0, 5), (0.1, 4.9), (2, 5), (-1, 8), (3, 3), (4, 1)])
def test_integral_reuses_identical_segment_arithmetic(a, b):
    field = CompactField.from_segments(rows())
    assert field.integral(a, b).hex() == integrator.integrate(rows(), a, b).hex()


def test_tiny_slope_integral_keeps_expm1_accuracy():
    seg = Segment(0, 0.0, 1.0, 0.0, 1e-10)
    assert CompactField.from_segments([seg]).integral(0, 1) == math.expm1(1e-10) / 1e-10


@pytest.mark.parametrize('bad', [[], [Segment(0, 0, 0, 0, 0)],
    [Segment(0, 0, 1, float('nan'), 0)], [Segment(0, 0, 1, 0, float('inf'))],
    [Segment(2, 0, 1, 0, 0)], [Segment(0, 0, 1, 0, 0), Segment(1, 2, 3, 0, 0)],
    [Segment(0, 0, 2, 0, 0), Segment(1, 1, 3, 0, 0)]])
def test_invalid_structure_is_rejected(bad):
    with pytest.raises(ValueError):
        CompactField.from_segments(bad)


def test_exact_integral_does_not_flatten_small_gamma_over_long_horizon():
    seg = Segment(0, 0.0, 36525.0, 0.0, 1e-13)
    field = CompactField.from_segments([seg])
    # The legacy integrator deliberately treats this slope as flat. The trial
    # must expose that difference rather than claim unchanged arithmetic.
    assert field.integral(0, 36525) == integrator.integrate([seg], 0, 36525)
