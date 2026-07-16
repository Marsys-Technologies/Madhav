"""
Regression test — D-2 cycle-1 rebuild incident 4 (build_run c0dd6db4).

ga_tajaka's `_solar_return` bisection crashed the whole asset (and its
~26-asset downstream L3/L4/L5 closure) when the underlying swisseph position
engine raised on a specific bisection instant it could not compute (a
Moshier-range error, only observed on the deployed container — not locally
reproducible, likely an ephemeris-file-availability difference). Fixed by
wrapping every engine call inside `_solar_return` with `_safe_f`, which
catches any exception and treats that instant as "no information" (None) —
the SAME honesty-preserving non-fabrication pattern the function already
used for its "no sign change" fallback: a row is still emitted, honestly
marked `converged: False`, never silently dropped or allowed to crash the
build.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import ga_writers.ga_tajaka_writer as sut


_BP = {
    "datetime_iso": "1984-02-04T10:43:00",
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "tz_offset_hours": 5.5,
}


def test_solar_return_survives_engine_failure_at_every_probed_instant():
    """If the position engine raises unconditionally, _solar_return must
    return a graceful converged=False result — never propagate the
    exception (the exact class of crash this regression guards against)."""
    with patch.object(sut, "_sun_longitude", side_effect=RuntimeError("Moshier range error")):
        instant, audit = sut._solar_return(43, 291.0, "lahiri", birth_params=_BP)
    assert isinstance(instant, datetime)
    assert audit["converged"] is False
    assert audit["diff_deg"] is None
    assert audit["unconverged_reason"] == "position_engine_error"


def test_solar_return_converges_normally_when_engine_is_healthy():
    """Sanity check: a healthy (non-raising) engine still converges exactly
    as before — the defensive wrapper must not change normal-path behavior.
    Uses a synthetic _sun_longitude that's linear-in-time so bisection has a
    real, deterministic root within the ±2-day bracket."""
    anniversary = datetime(2026, 2, 4, 10, 43, 0)

    def fake_sun_longitude(dt, aya_adapter, birth_params=None):
        # Sun moves ~1 deg/day; root exactly at the anniversary instant.
        days_offset = (dt - anniversary).total_seconds() / 86400.0
        return (291.0 + days_offset * 1.0) % 360.0

    with patch.object(sut, "_sun_longitude", side_effect=fake_sun_longitude):
        instant, audit = sut._solar_return(43, 291.0, "lahiri", birth_params=_BP)
    assert audit["converged"] is True
    assert audit["diff_deg"] is not None
    assert abs(audit["diff_deg"]) < 0.01
    assert abs((instant - anniversary).total_seconds()) < 120  # within ~2 minutes


def test_solar_return_survives_engine_failure_only_at_midpoint():
    """The engine fails only on instants strictly inside the bracket (not at
    lo/hi) — bisection must stop gracefully at that midpoint (still bracketed,
    just not narrowed further) rather than crash."""
    anniversary = datetime(2026, 2, 4, 10, 43, 0)
    call_count = {"n": 0}

    def flaky_sun_longitude(dt, aya_adapter, birth_params=None):
        call_count["n"] += 1
        days_offset = (dt - anniversary).total_seconds() / 86400.0
        if call_count["n"] > 2:  # first two calls are lo/hi bracket probes
            raise RuntimeError("Moshier range error at this specific instant")
        return (291.0 + days_offset * 1.0) % 360.0

    with patch.object(sut, "_sun_longitude", side_effect=flaky_sun_longitude):
        instant, audit = sut._solar_return(43, 291.0, "lahiri", birth_params=_BP)
    assert isinstance(instant, datetime)
    # Either converged with reduced iterations, or honestly marked unconverged
    # at the final instant — either way, no exception propagated.
    assert "converged" in audit
