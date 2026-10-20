"""Independent ephemeris root for the J-4d TOLERANCE proof (SR-EDGES-PROOF b).

A minted span edge (`t_in` / `t_out` of a point contact) is the instant the body is `orb` degrees from a ray level. This module finds that instant
FROM THE EPHEMERIS ALONE: pyswisseph with the kernel's flags (SWIEPH + sidereal Lahiri, mean node, Ketu = Rahu + 180), a scan for the sign change of the
separation, and a bisection. It imports nothing from `services.gochara_kernel` (no arc index, no `contacts._refine_root`, no `swiss_bisect`): a root found
here shares no solver code with the edge it judges (CLAUDE.md N.8 — the detector must be able to read false).

The only shared inputs are CONSTANTS the caller passes in: the orb (degrees) and the candidate ray levels. Nothing is read from a database here.
"""
from __future__ import annotations

import swisseph as swe

from panchang_engine.swiss_state import swiss_state_scope     # the process-wide Swiss-state lock (DP-SD-010), not solver code

FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL            # the kernel's EPHE_FLAGS (knots.py): SWIEPH backend, sidereal; Lahiri is set in `Sky`
BISECT_STEPS = 60                                    # to ~1e-9 day on a 4-day bracket, the precision of the kernel's own refinement
EDGE_WINDOWS_DAYS = (0.05, 0.5, 2.0)                 # the scan widens only when the narrower one finds no sign change
STATION_WINDOW_DAYS = 1.0
SCAN_POINTS = 50                                     # half-window steps
MAX_BRACKET_SEPARATION_DEG = 60.0                    # a sign change of the wrapped separation across +-180 is a seam, not a band edge
_SWE_BODY = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
             "saturn": swe.SATURN, "rahu": swe.MEAN_NODE, "ketu": swe.MEAN_NODE}


class EphemerisUnavailable(RuntimeError):
    """The Swiss backend did not serve the call from the pinned files (retflag), or the body is not one of the nine grahas."""


class Sky:
    """One body's longitude and speed straight from pyswisseph; the SWIEPH backend is asserted on every call (no Moshier stand-in)."""

    def __init__(self, ephe_path: str):
        self.ephe_path = ephe_path

    def state(self, body: str, jd: float) -> tuple[float, float]:
        if body not in _SWE_BODY:
            raise EphemerisUnavailable(f"unknown body {body!r}")
        with swiss_state_scope():                                        # path + mode + calc are one span: Swiss state is process-global
            swe.set_ephe_path(self.ephe_path)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            xx, retflag = swe.calc_ut(jd, _SWE_BODY[body], FLAGS | swe.FLG_SPEED)
        if retflag & 4 or not retflag & 2:
            raise EphemerisUnavailable(f"{body} @ {jd}: ephemeris backend {retflag}")
        lon = xx[0]
        if body == "ketu":
            lon = (lon + 180.0) % 360.0
        return lon, xx[3]

    def lon(self, body: str, jd: float) -> float:
        return self.state(body, jd)[0]


def signed_sep(sky: Sky, body: str, jd: float, level: float) -> float:
    return ((sky.lon(body, jd) - level + 180.0) % 360.0) - 180.0


def band_edge_error_deg(sky: Sky, body: str, jd: float, level: float, orb: float) -> float:
    """How far (degrees of longitude) the instant `jd` is from the band edge: ||separation| - orb|."""
    return abs(abs(signed_sep(sky, body, jd, level)) - orb)


def pick_level(sky: Sky, body: str, jd: float, levels, orb: float) -> float:
    """Of the candidate ray levels, the one whose band edge the body is nearest at `jd` (the edge belongs to exactly one level's band)."""
    return min(levels, key=lambda level: band_edge_error_deg(sky, body, jd, level, orb))


def _bisect(g, lo: float, hi: float) -> float:
    g_lo = g(lo)
    for _ in range(BISECT_STEPS):
        mid = 0.5 * (lo + hi)
        g_mid = g(mid)
        if g_lo * g_mid <= 0:
            hi = mid
        else:
            lo, g_lo = mid, g_mid
    return 0.5 * (lo + hi)


def _nearest_sign_change(g, centre: float, half_window: float, valid=lambda jd: True) -> tuple[float, float] | None:
    """The sampled interval nearest `centre` across which `g` changes sign (both ends `valid`), or None."""
    step = half_window / SCAN_POINTS
    points = [centre + k * step for k in range(-SCAN_POINTS, SCAN_POINTS + 1)]
    values = [g(p) for p in points]
    found = [(abs(0.5 * (points[i] + points[i + 1]) - centre), points[i], points[i + 1])
             for i in range(len(points) - 1)
             if values[i] * values[i + 1] <= 0 and valid(points[i]) and valid(points[i + 1])]
    if not found:
        return None
    _, a, b = min(found)
    return a, b


def band_edge_root(sky: Sky, body: str, jd: float, level: float, orb: float) -> float | None:
    """The instant, nearest `jd`, the body is exactly `orb` degrees from `level` on the side `jd` is on (None when no sign change is bracketed)."""
    sep0 = signed_sep(sky, body, jd, level)
    side = 1.0 if sep0 > 0 else -1.0

    def g(t):
        return signed_sep(sky, body, t, level) - side * orb

    def near_level(t):
        return abs(signed_sep(sky, body, t, level)) < MAX_BRACKET_SEPARATION_DEG
    for half_window in EDGE_WINDOWS_DAYS:
        bracket = _nearest_sign_change(g, jd, half_window, near_level)
        if bracket is not None:
            return _bisect(g, *bracket)
    return None


def station_root(sky: Sky, body: str, jd: float) -> float | None:
    """The instant, nearest `jd`, the ephemeris speed changes sign (a station), or None."""
    def speed(t):
        return sky.state(body, t)[1]
    bracket = _nearest_sign_change(speed, jd, STATION_WINDOW_DAYS)
    return None if bracket is None else _bisect(speed, *bracket)


def check_edge(sky: Sky, body: str, jd: float, levels, orb: float, delta_lambda_deg: float) -> dict:
    """Judge one minted edge instant against the ephemeris.

    `orb_edge`       the edge lies within `delta_lambda_deg` of longitude of the band edge (and the independent root is reported);
    `station_closed` the edge closes the span at a station (E8-2): it lies within `delta_lambda_deg` of the longitude of the independent station root;
    `unverified`     neither: the edge is off the ephemeris by more than the contact states.
    """
    level = pick_level(sky, body, jd, levels, orb)
    err = band_edge_error_deg(sky, body, jd, level, orb)
    root = band_edge_root(sky, body, jd, level, orb)
    out = {"class": "unverified", "level_deg": level, "error_deg": err, "root_jd": root,
           "seconds_from_root": None if root is None else abs(jd - root) * 86400.0}
    if root is not None and err <= delta_lambda_deg:
        out["class"] = "orb_edge"
        return out
    station = station_root(sky, body, jd)
    if station is not None:
        gap = abs(((sky.lon(body, jd) - sky.lon(body, station) + 180.0) % 360.0) - 180.0)
        if gap <= delta_lambda_deg:
            return {"class": "station_closed", "level_deg": level, "error_deg": gap, "root_jd": station,
                    "seconds_from_root": abs(jd - station) * 86400.0}
    return out
