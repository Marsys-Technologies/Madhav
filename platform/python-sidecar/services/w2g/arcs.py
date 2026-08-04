"""W2G — monotone-arc decomposition of a body's longitude history.

THE ONE IDEA THIS FILE ENCODES
──────────────────────────────
Planetary motion in ecliptic longitude is smooth and piecewise-monotonic. Cut
a body's history at (a) its real stations — the instants where longitude
velocity changes sign — and (b) every 360° wrap boundary, and what is left is
a sequence of arcs on which longitude is a STRICTLY MONOTONE function of time
that never repeats a degree.

That single property is what turns the v1 question

    "day-step through the window calling the ephemeris, watch for a sign
     change in the arc-difference, then bisect"                  (a SCAN)

into the 2.0 question

    "which arcs contain this degree at all — a range predicate — and what is
     the unique instant inside each"                     (an INDEXED LOOKUP
                                                          plus a bracketed
                                                          bisection)

and it is why the substrate is CHART-INDEPENDENT: when Saturn reaches 123.45°
has nothing to do with anybody's birth data. The century of arcs is computed
once, globally (`bg_gochara_arcs`), and every chart that ever onboards joins
against the same rows.

WHY THIS MATTERS NUMERICALLY (the measured design input this lane exists for)
────────────────────────────────────────────────────────────────────────────
v1's dominant cost was measured at ~110–120ms per contact-primitive call,
"regardless of whether it touches the DB at all" — the finding
`services/gochara_intensity/configuration_activity.py` documents in its own
source and which a clean A/B measurement re-confirmed on 2026-08-04
(SHAD_DARSHANA_STATE.md, lane (a) PARKED-HONEST: the ephemeris/kinematics
layer was FALSIFIED as the bottleneck; per-call overhead is the real cost).
Because a contact here is a pure-CPU bisection over an arc already in memory,
the solver's database-read count does not scale with targets, bodies, or
primitives at all. That is asserted by a test, not by this paragraph:
`tests/test_w2g_arc_substrate.py::test_solver_query_count_is_constant_in_target_count`.

SPLINE PROVENANCE
─────────────────
The interpolant is `w2g_validations.v3_spline_accuracy.fit_longitude_spline` —
deliberately the SAME callable whose accuracy V3 measured against direct Swiss
Ephemeris calls (worst case 0.314″ vs a 60″ target; recommended root-find
tolerance 1.0″). Re-implementing a second spline here would mean the engine in
production is not the artifact the validation blessed, and would be a
duplicate copy in a codebase whose rails require a duplicate-copy audit. The
import direction (engine → validation module) is unusual and intentional.

KNOT ABSCISSA: NOON UT. `brahmagyan.l0_ephemeris` computes every
`ephemeris_daily` row at `swe.julday(y, m, d, 12.0)`. A midnight-knot spline
is wrong by half a day (~6.6° for the Moon). V3 found and documented this; the
builder here inherits it rather than re-deriving it (§N.7 item 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from services.w2g_validations.v3_spline_accuracy import (  # noqa: F401  (re-export)
    angular_delta_deg,
    fit_longitude_spline,
)

# Root-find tolerance, in arcseconds. V3's live run recommended 1.0″ (measured
# worst-case spline error 0.314″, doubled, floored at 1.0). Stated as the
# measured recommendation, never as a round guess.
DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC = 1.0
ARCSEC_PER_DEG = 3600.0

# A station is a root of the velocity. Two roots closer together than this are
# the same physical station seen twice through spline noise, not two stations.
STATION_MERGE_DAYS = 0.25

# Bisection iteration cap. 80 halvings of a <400-day bracket reaches ~1e-22
# days; the tolerance check exits far sooner. The cap exists so a pathological
# input terminates rather than spins.
MAX_BISECTION_ITERATIONS = 80


def unwrap_degrees(values: Sequence[float]) -> list[float]:
    """Turn a wrapped [0,360) angle sequence into a continuous one.

    Same branch-nearest rule V3 uses; kept here (not imported) because V3's
    copy is module-private and this is the public seam the arc builder needs.
    """
    if not values:
        return []
    out = [float(values[0])]
    for v in values[1:]:
        prev = out[-1]
        candidate = float(v)
        while candidate - prev > 180.0:
            candidate -= 360.0
        while prev - candidate > 180.0:
            candidate += 360.0
        out.append(candidate)
    return out


@dataclass(frozen=True)
class MonotoneArc:
    """One maximal interval on which longitude is monotone AND stays inside a
    single 360° band.

    `evaluator` maps Julian day -> UNWRAPPED longitude (the continuous branch
    the spline was fitted on). It is excluded from equality/repr so two arcs
    describing the same span compare equal whether or not either carries an
    interpolant — the DB round-trip drops it, and `with_evaluator` puts one
    back.
    """

    body: str
    arc_index: int
    start_jd: float
    end_jd: float
    start_lon_unwrapped: float
    end_lon_unwrapped: float
    direction: int          # +1 direct, -1 retrograde
    wrap_index: int         # which 360° band this arc lives in
    evaluator: Callable[[float], float] | None = field(
        default=None, compare=False, repr=False, hash=False
    )

    # ── wrapped bounds: the columns the range-join predicate reads ────────────

    @property
    def lon_start_deg(self) -> float:
        return self.start_lon_unwrapped - 360.0 * self.wrap_index

    @property
    def lon_end_deg(self) -> float:
        return self.end_lon_unwrapped - 360.0 * self.wrap_index

    @property
    def lon_lo_deg(self) -> float:
        return min(self.lon_start_deg, self.lon_end_deg)

    @property
    def lon_hi_deg(self) -> float:
        return max(self.lon_start_deg, self.lon_end_deg)

    @property
    def span_deg(self) -> float:
        return abs(self.end_lon_unwrapped - self.start_lon_unwrapped)

    @property
    def duration_days(self) -> float:
        return self.end_jd - self.start_jd

    def with_evaluator(self, evaluator: Callable[[float], float]) -> "MonotoneArc":
        """Attach an interpolant to an arc loaded from the database."""
        return MonotoneArc(
            body=self.body,
            arc_index=self.arc_index,
            start_jd=self.start_jd,
            end_jd=self.end_jd,
            start_lon_unwrapped=self.start_lon_unwrapped,
            end_lon_unwrapped=self.end_lon_unwrapped,
            direction=self.direction,
            wrap_index=self.wrap_index,
            evaluator=evaluator,
        )

    def unwrapped_longitude_at(self, jd: float) -> float:
        if self.evaluator is None:
            raise ValueError(
                f"arc {self.body}#{self.arc_index} has no interpolant attached — "
                "call with_evaluator() with a spline built over the body's "
                "ephemeris rows before root-finding on it"
            )
        return float(self.evaluator(jd))

    def longitude_at(self, jd: float) -> float:
        """Wrapped longitude, expressed in THIS arc's own band, so an arc that
        ends exactly on a boundary reports 360.0 rather than folding to 0.0."""
        return self.unwrapped_longitude_at(jd) - 360.0 * self.wrap_index

    def covers_degree(self, target_deg: float) -> bool:
        return self.lon_lo_deg - 1e-9 <= float(target_deg) <= self.lon_hi_deg + 1e-9

    def as_row(self) -> dict[str, Any]:
        """The `bg_gochara_arcs` row shape (no chart_id — global asset)."""
        return {
            "body": self.body,
            "arc_index": self.arc_index,
            "start_jd": self.start_jd,
            "end_jd": self.end_jd,
            "start_lon_unwrapped_deg": self.start_lon_unwrapped,
            "end_lon_unwrapped_deg": self.end_lon_unwrapped,
            "lon_lo_deg": self.lon_lo_deg,
            "lon_hi_deg": self.lon_hi_deg,
            "direction": self.direction,
            "wrap_index": self.wrap_index,
        }


def _refine_boundary(
    evaluate: Callable[[float], float],
    lo_jd: float,
    hi_jd: float,
    level: float,
    tol_deg: float,
) -> float:
    """Bisect [lo_jd, hi_jd] for evaluate(jd) == level on a monotone stretch."""
    f_lo = evaluate(lo_jd) - level
    f_hi = evaluate(hi_jd) - level
    if f_lo == 0.0:
        return lo_jd
    if f_hi == 0.0:
        return hi_jd
    if f_lo * f_hi > 0.0:
        # Not bracketed — return the nearer endpoint rather than inventing a
        # crossing that the data does not contain.
        return lo_jd if abs(f_lo) <= abs(f_hi) else hi_jd
    for _ in range(MAX_BISECTION_ITERATIONS):
        mid = 0.5 * (lo_jd + hi_jd)
        f_mid = evaluate(mid) - level
        if abs(f_mid) <= tol_deg or (hi_jd - lo_jd) < 1e-9:
            return mid
        if f_lo * f_mid <= 0.0:
            hi_jd, f_hi = mid, f_mid
        else:
            lo_jd, f_lo = mid, f_mid
    return 0.5 * (lo_jd + hi_jd)


def _station_times(spline, jds: Sequence[float]) -> list[float]:
    """Real stations = roots of the spline's derivative inside the epoch.

    Roots are merged within STATION_MERGE_DAYS and then CONFIRMED by an actual
    sign change of the velocity across the candidate. A root that does not
    change the sign of the velocity is a tangency, not a station, and splitting
    there would manufacture two adjacent arcs with the same direction.
    """
    derivative = spline.derivative()
    try:
        raw = [float(r) for r in derivative.roots(extrapolate=False)]
    except Exception:  # noqa: BLE001 — scipy version differences only
        raw = []

    lo, hi = float(jds[0]), float(jds[-1])
    candidates = sorted(r for r in raw if lo < r < hi)

    merged: list[float] = []
    for r in candidates:
        if merged and (r - merged[-1]) <= STATION_MERGE_DAYS:
            continue
        merged.append(r)

    confirmed: list[float] = []
    eps = min(0.05, STATION_MERGE_DAYS / 2.0)
    for r in merged:
        before = float(derivative(max(lo, r - eps)))
        after = float(derivative(min(hi, r + eps)))
        if before == 0.0 or after == 0.0:
            continue
        if (before > 0.0) != (after > 0.0):
            confirmed.append(r)
    return confirmed


def build_arcs(
    body: str,
    knot_jds: Sequence[float],
    wrapped_longitudes_deg: Sequence[float],
    tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
) -> list[MonotoneArc]:
    """Decompose one body's longitude history into monotone, sub-revolution arcs.

    `knot_jds` are NOON-UT Julian days (the abscissa `ephemeris_daily` rows
    were computed at); `wrapped_longitudes_deg` are the stored tropical
    longitudes in [0, 360).

    Raises ValueError on fewer than 4 knots — a cubic spline is not definable
    there, and returning an empty arc list would silently drop the body.
    """
    if len(knot_jds) != len(wrapped_longitudes_deg):
        raise ValueError("knot and longitude sequences must be the same length")
    if len(knot_jds) < 4:
        raise ValueError(
            f"{body}: a cubic spline needs at least 4 knots, got {len(knot_jds)}"
        )

    unwrapped = unwrap_degrees(wrapped_longitudes_deg)
    evaluate = _make_unwrapped_evaluator(knot_jds, unwrapped)
    spline = evaluate.spline  # type: ignore[attr-defined]

    tol_deg = float(tolerance_arcsec) / ARCSEC_PER_DEG
    boundaries: list[float] = [float(knot_jds[0])]
    boundaries.extend(_station_times(spline, knot_jds))
    boundaries.append(float(knot_jds[-1]))
    boundaries = sorted(set(boundaries))

    # Stage 1 gave monotone stretches. Stage 2 splits each at its 360° bands.
    arcs: list[MonotoneArc] = []
    index = 0
    for seg_start, seg_end in zip(boundaries, boundaries[1:]):
        if seg_end - seg_start <= 0.0:
            continue
        lon_a = evaluate(seg_start)
        lon_b = evaluate(seg_end)
        rising = lon_b >= lon_a
        direction = 1 if rising else -1

        # Cut points carry their EXACT longitude where one is known. A wrap
        # boundary is at exactly 360k by definition, so the stored endpoint is
        # that exact value, not the interpolant's ~0.6″-off re-evaluation at
        # the refined instant. Without this, an arc can be recorded as
        # spanning 360.0002° and the "at most one revolution" invariant — which
        # the range-join predicate's exactness rests on — is violated by
        # rounding.
        cuts: list[tuple[float, float | None]] = [(seg_start, None)]
        lo_lon, hi_lon = (lon_a, lon_b) if rising else (lon_b, lon_a)
        k = int(lo_lon // 360.0) + 1
        while 360.0 * k < hi_lon:
            level = 360.0 * k
            if level > lo_lon:  # strictly inside the segment
                cuts.append(
                    (_refine_boundary(evaluate, seg_start, seg_end, level, tol_deg), level)
                )
            k += 1
        cuts.append((seg_end, None))
        cuts.sort(key=lambda c: c[0])

        for (a_jd, a_lon), (b_jd, b_lon) in zip(cuts, cuts[1:]):
            if b_jd - a_jd <= 0.0:
                continue
            start_lon = a_lon if a_lon is not None else evaluate(a_jd)
            end_lon = b_lon if b_lon is not None else evaluate(b_jd)
            mid_lon = 0.5 * (start_lon + end_lon)
            wrap_index = int(mid_lon // 360.0)
            arcs.append(
                MonotoneArc(
                    body=body,
                    arc_index=index,
                    start_jd=float(a_jd),
                    end_jd=float(b_jd),
                    start_lon_unwrapped=float(start_lon),
                    end_lon_unwrapped=float(end_lon),
                    direction=direction,
                    wrap_index=wrap_index,
                    evaluator=evaluate,
                )
            )
            index += 1

    return arcs


def _make_unwrapped_evaluator(knot_jds: Sequence[float], unwrapped: Sequence[float]):
    """A jd -> UNWRAPPED-longitude callable carrying its own spline object.

    `fit_longitude_spline` (the V3-validated fitter) wraps its result to
    [0,360), which is exactly wrong for arc arithmetic across a band boundary,
    so the arc layer builds the same CubicSpline over the same unwrapped
    values and keeps the continuous branch. The wrapping is the only
    difference; the interpolant itself is identical, which is what V3's
    accuracy measurement blessed.
    """
    from scipy.interpolate import CubicSpline

    spline = CubicSpline(list(knot_jds), list(unwrapped))

    def _evaluate(jd: float) -> float:
        return float(spline(jd))

    _evaluate.spline = spline  # type: ignore[attr-defined]
    return _evaluate


def arcs_covering_degree(
    arcs: Sequence[MonotoneArc], target_deg: float
) -> list[MonotoneArc]:
    """The in-memory twin of the `lon_lo_deg <= L <= lon_hi_deg` SQL predicate.

    Exact because every arc spans at most one revolution — so an arc contains
    a given degree at most once, and containment is a plain interval test.
    """
    t = float(target_deg) % 360.0
    return [arc for arc in arcs if arc.covers_degree(t)]


__all__ = [
    "ARCSEC_PER_DEG",
    "DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC",
    "MonotoneArc",
    "angular_delta_deg",
    "arcs_covering_degree",
    "build_arcs",
    "fit_longitude_spline",
    "unwrap_degrees",
]
