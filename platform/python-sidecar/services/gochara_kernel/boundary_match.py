"""When does a STORED contact boundary equal a RECONSTRUCTED one? (Codex round 9, R9-9 — Stream B's all-guards rehearsal.)

A fixed tolerance in seconds is wrong on the real sky: the contact solver is accurate to ONE ARCSECOND of longitude, and
one arcsecond is ≈ 24 s for the Sun, ≈ 12 min for Saturn — and unbounded at a station, where the body's speed passes
through zero. Fixtures with a constant stand-in ephemeris hid it; on the real ephemeris the writer's own window phase
rejected its own correct contacts.

So every comparison of a reconstructed boundary with a stored one uses a tolerance DERIVED from the stored contact's
stated angular accuracy (`delta_lambda`; the solver's one arcsecond when it states none) and the body's speed at that
instant — `time_tolerance_seconds`, a named function, not a constant — and where the speed is too small for a time
tolerance to mean anything (a station) the comparison is made in ANGLE, not in time:

    time tolerance  = accuracy / |speed|  +  BISECT_SECONDS          (accuracy and speed in degrees, degrees/second)
    station         = |speed| below `STATION_FLOOR_DPS` ⇒ no time tolerance (None): compare |Δλ| ≤ accuracy + the
                      reconstruction's own location error.

This module is the VERIFIER's own; it imports nothing from the builder's geometry."""
from __future__ import annotations

from datetime import datetime, timedelta

from .contact_reconstruct import BISECT_SECONDS, VMAX_DPS

#: the contact solver's stated angular accuracy (1 arcsecond of longitude); a stored contact's own `delta_lambda` wins
SOLVER_ACCURACY_ARCSEC = 1.0
DEFAULT_ACCURACY_DEG = SOLVER_ACCURACY_ARCSEC / 3600.0
#: below this |speed| (degrees/day) a boundary's time uncertainty (accuracy/speed) exceeds ~3.6 days and is treated as
#: unbounded — the station case
STATION_FLOOR_DPS = 1.0e-3
_SPEED_HALF_WINDOW_SECONDS = 60.0


def _angdiff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def speed_deg_per_second(position_at, body: str, t: datetime) -> float:
    """|d(longitude)/dt| at `t` by a central difference over ±60 s (degrees/second; wrap-safe)."""
    h = timedelta(seconds=_SPEED_HALF_WINDOW_SECONDS)
    a, b = float(position_at(body, t - h)), float(position_at(body, t + h))
    return _angdiff(b, a) / (2.0 * _SPEED_HALF_WINDOW_SECONDS)


def accuracy_degrees(delta_lambda) -> float:
    """The accuracy a stored contact states (degrees); the solver's stated one arcsecond when it states none."""
    return float(delta_lambda) if delta_lambda is not None and float(delta_lambda) > 0 else DEFAULT_ACCURACY_DEG


def time_tolerance_seconds(position_at, body: str, t: datetime, accuracy_deg: float) -> float | None:
    """The time tolerance for a boundary at `t`: accuracy ÷ speed (+ the reconstruction's own location error), or None
    where the body is at a station and a time tolerance is unbounded (compare in angle there)."""
    v = speed_deg_per_second(position_at, body, t)
    if v * 86400.0 < STATION_FLOOR_DPS:
        return None
    return accuracy_deg / v + BISECT_SECONDS


def boundaries_agree(position_at, body: str, t_stored: datetime, t_expected: datetime, accuracy_deg: float) -> bool:
    """True iff the stored boundary and the reconstructed one are the same crossing to the stated accuracy.

    Away from a station: |Δt| ≤ the derived time tolerance (`time_tolerance_seconds`). AT a station (no usable time
    tolerance) the comparison is made in ANGLE — |Δλ| ≤ accuracy + the reconstruction's location error — AND the body must
    have stayed within that band of the boundary longitude for the WHOLE interval between the two instants (sampled): a
    body hovering on the edge through a station really can cross it at any instant of the hover, whereas two instants at
    the same angle with the body elsewhere in between are different crossings of the same edge, not the same one."""
    tol = time_tolerance_seconds(position_at, body, t_expected, accuracy_deg)
    if tol is not None:
        return abs((t_stored - t_expected).total_seconds()) <= tol
    location_error = VMAX_DPS[body.lower()] / 86400.0 * BISECT_SECONDS
    band = accuracy_deg + location_error
    ref = float(position_at(body, t_expected))
    a, b = sorted((t_stored, t_expected))
    n = max(2, min(240, int((b - a).total_seconds() // 600) + 2))
    return all(_angdiff(float(position_at(body, a + (b - a) * k / (n - 1))), ref) <= band for k in range(n))


def intervals_agree(position_at, body: str, stored: tuple, expected: tuple, accuracy_deg: float,
                    lo: datetime, hi: datetime) -> bool:
    """Both ends of a stored contact interval equal the reconstructed interval's: an end at the horizon's own edge must be
    the edge (the interval is clipped there — compared in time, to the reconstruction's location error); every other end is
    a crossing compared with `boundaries_agree`."""
    for s, e, edge in ((stored[0], expected[0], lo), (stored[1], expected[1], hi)):
        if e == edge:
            if abs((s - edge).total_seconds()) > BISECT_SECONDS:
                return False
        elif not boundaries_agree(position_at, body, s, e, accuracy_deg):
            return False
    return True


def edge_distance_degrees(position_at, body: str, relation: str, target: str, t: datetime) -> float:
    """How far (degrees of longitude) the body is at `t` from the NEAREST EDGE of the geometry the contact is about — a
    sign / nakṣatra cusp, or the orb edge of a point band. A stored boundary is genuine when this is within the stored
    accuracy, whatever the speed (the angle test that survives a station)."""
    from .window_verifier import _ASPECT_ANGLES, _POINT_ORB_DEG
    lon = float(position_at(body, t)) % 360.0
    kind, _, arg = target.partition(":")
    if kind == "point":
        lam = float(arg) % 360.0
        angles = (0.0,) if relation == "conjunction" else _ASPECT_ANGLES[body]
        orb = _POINT_ORB_DEG[relation]
        return min(abs(_angdiff(lon, (lam - a) % 360.0) - orb) for a in angles)
    width = 360.0 / 27.0 if kind == "star" else 30.0
    m = lon % width
    return min(m, width - m)


__all__ = ["DEFAULT_ACCURACY_DEG", "SOLVER_ACCURACY_ARCSEC", "STATION_FLOOR_DPS", "accuracy_degrees",
           "boundaries_agree", "edge_distance_degrees", "intervals_agree", "speed_deg_per_second",
           "time_tolerance_seconds"]
