"""C13 — both campaign copies of the nakṣatra index delegate to the ONE exact helper
(services.gochara_rules.kernel_factor.extent_index, integer arcseconds): a boundary
longitude belongs to the FOLLOWING nakṣatra (half-open extents), exact at every one of
the 27 boundaries, the 360° seam and every adjacent representable value.

Covers the two copies the steward assigned (M20261002T120320-19ad):
  1. services/gochara_kernel/legacy_semantics.py::longitude_to_nakshatra_index
     (the `/` form mis-indexed 7 of 27 boundaries — the non-integer-degree ones);
  2. scripts/kala_gochara_cutover/step06b_windows_projection.py::nakshatra_index_1based
     (the `//` form mis-indexed 15 of 27 — those 7 plus all 8 integer-degree ones).
The two production Kāla copies (gochara_intensity/enrichment.py:136,
gochara_v3/mechanisms/w23_tara_bala.py:158) are NOT touched — recorded finding only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel.legacy_semantics import (  # noqa: E402
    longitude_to_nakshatra_index,
)
from scripts.kala_gochara_cutover.step06b_windows_projection import (  # noqa: E402
    nakshatra_index_1based,
)
from services.gochara_rules.kernel_factor import (  # noqa: E402
    NAKSHATRA_ARCSEC,
    extent_index,
)

COPIES = [
    pytest.param(longitude_to_nakshatra_index, id="legacy_semantics"),
    pytest.param(nakshatra_index_1based, id="step06b"),
]

# All 27 nakṣatra boundaries as the floats the ephemeris actually produces:
# k * (360/27) for k = 0..26. Boundary k STARTS nakṣatra k+1.
BOUNDARIES = [(k, k * (360.0 / 27.0)) for k in range(27)]

# The 7 non-integer-degree boundary floats the C12 report listed for the `/` form.
# None is exactly representable, so each float is an ADJACENT representable value of its
# true boundary (880/3 etc. are not doubles); exact integer-arcsecond membership places
# each float by its true side (Fraction arithmetic, the helper's own): six just below
# (→ the preceding nakṣatra), 253.33333333333334 just above (→ the following one).
SLASH_FORM_C12_FLOATS = [
    (93.33333333333333, 7),
    (146.66666666666666, 11),
    (186.66666666666666, 14),
    (226.66666666666666, 17),
    (253.33333333333334, 20),
    (293.3333333333333, 22),
    (333.3333333333333, 25),
]

# The 8 integer-degree boundaries the C12 report listed for the `//` form — these ARE
# exactly representable and exactly on a boundary, so each belongs to the FOLLOWING
# nakṣatra. 15 = 7 + 8 in total.
FLOOR_FORM_C12_FLOATS = [
    (40.0, 4), (80.0, 7), (120.0, 10), (160.0, 13),
    (200.0, 16), (240.0, 19), (280.0, 22), (320.0, 25),
]


@pytest.mark.parametrize("fn", COPIES)
@pytest.mark.parametrize("k,lon", BOUNDARIES, ids=[f"b{k:02d}" for k in range(27)])
def test_every_boundary_starts_the_following_nakshatra(fn, k, lon):
    assert fn(lon) == k + 1


@pytest.mark.parametrize("fn", COPIES)
@pytest.mark.parametrize("k,lon", BOUNDARIES, ids=[f"b{k:02d}" for k in range(27)])
def test_adjacent_representable_values(fn, k, lon):
    """The float just below a boundary is the PREVIOUS nakṣatra (or 27 below 0°),
    the float just above is the boundary's own nakṣatra."""
    expected = k + 1
    below_expected = 27 if k == 0 else k
    assert fn(math.nextafter(lon, -math.inf)) == below_expected
    assert fn(math.nextafter(lon, math.inf)) == expected


@pytest.mark.parametrize("fn", COPIES)
def test_seam(fn):
    assert fn(360.0) == 1          # the seam: 360° IS 0° — Aśvinī, not clamped to 27
    assert fn(720.0) == 1
    assert fn(math.nextafter(360.0, math.inf)) == 1
    assert fn(math.nextafter(360.0, -math.inf)) == 27


@pytest.mark.parametrize("fn", COPIES)
def test_agrees_with_kernel_factor_on_a_dense_grid(fn):
    """Both copies must BE the helper: 0..360 in 0.01° steps plus every boundary's
    neighbours, all equal to kernel_factor.extent_index (NAKSHATRA_ARCSEC)."""
    steps = (i / 100.0 for i in range(0, 36001))
    extras = [lon for _, lon in BOUNDARIES] + [
        math.nextafter(lon, d)
        for _, lon in BOUNDARIES
        for d in (-math.inf, math.inf)
    ]
    for lon in list(steps) + extras:
        assert fn(lon) == extent_index(lon, None, NAKSHATRA_ARCSEC), lon


@pytest.mark.parametrize("fn", COPIES)
@pytest.mark.parametrize("lon,expected", SLASH_FORM_C12_FLOATS)
def test_c12_slash_form_floats_exact_membership(fn, lon, expected):
    """The 7 floats the C12 script listed for the `/` form, each asserted at its exact
    integer-arcsecond membership (the true side of the un-representable boundary)."""
    assert fn(lon) == expected


@pytest.mark.parametrize("fn", COPIES)
@pytest.mark.parametrize("lon,expected", FLOOR_FORM_C12_FLOATS)
def test_c12_floor_form_boundaries_now_following_nakshatra(fn, lon, expected):
    """The 8 exact integer-degree boundaries the C12 script listed for the `//` form
    must each land in the FOLLOWING nakṣatra on both fixed copies."""
    assert fn(lon) == expected
