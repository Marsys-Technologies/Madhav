"""KA-1e coverage: every result names source interval, backend and
completeness; coverage cannot be removed and a gap cannot be promoted."""
from __future__ import annotations

from dataclasses import replace

import pytest

from services.gochara_kernel.arcs import build_arc_index
from services.kala_core.sky import (
    SkyCoverage, SkyResult, boundary_events, coverage_of, solve_contacts, unavailable,
)
from services.kala_core.vocab import NullReason

T0 = 2460000.0
CONVENTION = "c0"


def sweep_index(days: int = 200):
    jds = [T0 + k for k in range(days + 1)]
    return build_arc_index("Sun", jds, [(1.0 * k) % 360.0 for k in range(days + 1)],
                           tolerance_arcsec=1e-7)


def test_inside_the_source_is_complete_and_named() -> None:
    result = solve_contacts(sweep_index(), "Sun", "conjunction", 45.0, (T0, T0 + 100),
                            CONVENTION, refine=False)
    cov = result.coverage
    assert result.available and len(result.values) == 1
    assert cov.source_interval == (T0, T0 + 200)
    assert cov.backend == "arc_spline_unrefined" and cov.convention_id == CONVENTION
    assert cov.complete and cov.gaps == ()


def test_partial_request_names_its_gap() -> None:
    result = boundary_events(sweep_index(), "Sun", ["sign_ingress"], (T0 + 150, T0 + 260),
                             CONVENTION, refine=False)
    cov = result.coverage
    assert result.available and not cov.complete
    assert cov.covered == (T0 + 150, T0 + 200)
    assert cov.gaps == ((T0 + 200, T0 + 260),)
    assert all(T0 + 150 <= e.jd < T0 + 200 for e in result.values)


def test_uncovered_request_is_information_unavailable() -> None:
    result = solve_contacts(sweep_index(), "Sun", "conjunction", 45.0, (T0 + 300, T0 + 400),
                            CONVENTION, refine=False)
    assert result.values == ()
    assert result.null_reason is NullReason.INFORMATION_UNAVAILABLE
    assert result.coverage.covered is None and result.coverage.gaps == ((T0 + 300, T0 + 400),)


def test_removing_coverage_from_a_valid_result_fails() -> None:
    valid = solve_contacts(sweep_index(), "Sun", "conjunction", 45.0, (T0, T0 + 100),
                           CONVENTION, refine=False)
    with pytest.raises(TypeError, match="coverage"):
        replace(valid, coverage=None)
    with pytest.raises(TypeError, match="coverage"):
        SkyResult(valid.values, None)


def test_promoting_a_gap_to_complete_fails() -> None:
    partial = coverage_of((T0, T0 + 300), (T0, T0 + 200), backend="swieph",
                          convention_id=CONVENTION)
    assert not partial.complete
    with pytest.raises(ValueError, match="complete"):
        replace(partial, complete=True)
    with pytest.raises(ValueError, match="covered"):
        replace(partial, covered=(T0, T0 + 300))
    with pytest.raises(ValueError, match="complete"):
        SkyCoverage((T0, T0 + 300), None, None, True, "swieph", CONVENTION)


def test_values_without_coverage_or_with_a_null_fail() -> None:
    nothing = coverage_of((T0, T0 + 1), None, backend="swieph", convention_id=CONVENTION)
    with pytest.raises(ValueError, match="information_unavailable"):
        SkyResult(("a value",), nothing)
    covered = coverage_of((T0, T0 + 1), (T0, T0 + 2), backend="swieph", convention_id=CONVENTION)
    with pytest.raises(ValueError, match="no values"):
        SkyResult(("a value",), covered, NullReason.INFORMATION_UNAVAILABLE)
    with pytest.raises(ValueError, match="not a sky null"):
        SkyResult((), covered, NullReason.EVALUATED_SILENT)
    assert unavailable(nothing).null_reason is NullReason.INFORMATION_UNAVAILABLE


def test_coverage_names_backend_and_convention() -> None:
    with pytest.raises(ValueError, match="backend"):
        coverage_of((T0, T0 + 1), (T0, T0 + 2), backend="", convention_id=CONVENTION)
    with pytest.raises(ValueError, match="interval"):
        coverage_of((T0 + 1, T0), (T0, T0 + 2), backend="swieph", convention_id=CONVENTION)
