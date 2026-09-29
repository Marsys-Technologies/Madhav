"""Monotone-arc index over a cubic spline on noon-UT sidereal knots (plan §4.2).

ADOPTED from services/w2g/arcs.py (proven arc decomposition; plan §2.2
"Adopted, not imported"), with the E8 defect fixes and structure the kernel
needs:

  * Sidereal-before-arc-building (F-07 fix, plan §4.2): callers pass knots that
    are ALREADY sidereal (knots.sample_knots, D-1). This module never converts
    frames.
  * NO station coalescing (E8-1): services/w2g merges derivative roots within
    STATION_MERGE_DAYS = 0.25 d, which deleted genuine small retrograde loops
    (measured: stations at 1.4/1.6 d coalesced to one, 3 expected roots
    reduced to 1). Here EVERY sign-confirmed derivative root is a station
    boundary. The sign-change confirmation alone still rejects spline-noise
    tangencies (a root of the velocity that does not change its sign is a
    tangency, not a station — splitting there would manufacture two adjacent
    arcs with the same direction).
  * Explicit station structure: `ArcIndex.stations` carries every station
    instant, and `ArcIndex.segments` the station-bounded monotone pieces the
    episode layer solves orb intervals on (needed for wrap tangencies, E8-2,
    where in-orb intervals span a station the exact root never crosses).
  * Wrap boundaries keep their EXACT longitudes (360k) at cut points, so an
    arc never spans more than one revolution and the range-join predicate
    stays exact (inherited from w2g, kept because it is load-bearing).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

from scipy.interpolate import CubicSpline

ARCSEC_PER_DEG = 3600.0
DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC = 1.0
MAX_BISECTION_ITERATIONS = 80


def unwrap_degrees(values: Sequence[float]) -> list[float]:
    """Turn a wrapped [0,360) angle sequence into a continuous one.

    Branch-nearest rule (adopted from services/w2g/arcs.py:unwrap_degrees).
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


def _refine_boundary(
    evaluate: Callable[[float], float],
    lo_jd: float,
    hi_jd: float,
    level: float,
    tol_deg: float,
) -> float:
    """Bisect [lo_jd, hi_jd] for evaluate(jd) == level on a monotone stretch.

    Adopted from services/w2g/arcs.py:_refine_boundary. If not bracketed,
    returns the nearer endpoint rather than inventing a crossing.
    """
    f_lo = evaluate(lo_jd) - level
    f_hi = evaluate(hi_jd) - level
    if f_lo == 0.0:
        return lo_jd
    if f_hi == 0.0:
        return hi_jd
    if f_lo * f_hi > 0.0:
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


@dataclass(frozen=True)
class MonotoneArc:
    """One maximal interval on which longitude is monotone AND stays inside a
    single 360° band. Adopted from services/w2g/arcs.py:MonotoneArc.

    `evaluator` maps Julian day -> UNWRAPPED longitude (the continuous branch
    the spline was fitted on); excluded from equality so a DB round-trip arc
    compares equal to its in-memory twin.
    """

    body: str
    arc_index: int
    start_jd: float
    end_jd: float
    start_lon_unwrapped: float
    end_lon_unwrapped: float
    direction: int          # +1 direct, -1 retrograde
    wrap_index: int         # which 360° band this arc lives in
    station_bounded: tuple[bool, bool] = (False, False)
    # station_bounded: whether (start, end) is a confirmed station instant —
    # the episode branch classifier needs this to distinguish the internal
    # retrograde leg of a station pair (branch 'retrograde') from a bare
    # negative-slope stretch at a horizon edge (WP2 case 04b pins 'direct').

    evaluator: Callable[[float], float] | None = field(
        default=None, compare=False, repr=False, hash=False
    )

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

    def with_evaluator(self, evaluator: Callable[[float], float]) -> "MonotoneArc":
        return MonotoneArc(
            body=self.body,
            arc_index=self.arc_index,
            start_jd=self.start_jd,
            end_jd=self.end_jd,
            start_lon_unwrapped=self.start_lon_unwrapped,
            end_lon_unwrapped=self.end_lon_unwrapped,
            direction=self.direction,
            wrap_index=self.wrap_index,
            station_bounded=self.station_bounded,
            evaluator=evaluator,
        )

    def unwrapped_longitude_at(self, jd: float) -> float:
        if self.evaluator is None:
            raise ValueError(
                f"arc {self.body}#{self.arc_index} has no interpolant attached"
            )
        return float(self.evaluator(jd))

    def covers_degree(self, target_deg: float) -> bool:
        t = float(target_deg) % 360.0
        return self.lon_lo_deg - 1e-9 <= t <= self.lon_hi_deg + 1e-9


@dataclass
class ArcIndex:
    """One body's arc substrate over one knot window: the band-split monotone
    arcs (range-join index), the station-bounded segments (orb-interval
    solving), and the whole-horizon spline evaluator."""

    body: str
    knot_jds: tuple[float, ...]
    arcs: list[MonotoneArc]
    segments: list[MonotoneArc]      # station-bounded (or knot-bounded) monotone pieces
    stations: list[float]            # confirmed station instants (jd)
    evaluate: Callable[[float], float]
    spline: CubicSpline
    tolerance_arcsec: float

    def lon_unwrapped(self, jd: float) -> float:
        return float(self.evaluate(jd))

    def velocity(self, jd: float) -> float:
        return float(self.spline.derivative()(jd))

    def arcs_covering_degree(self, target_deg: float) -> list[MonotoneArc]:
        t = float(target_deg) % 360.0
        return [arc for arc in self.arcs if arc.covers_degree(t)]


def _station_times(spline: CubicSpline, jds: Sequence[float]) -> list[float]:
    """Real stations = sign-changing roots of the spline's velocity.

    E8-1 FIX: services/w2g merges roots within STATION_MERGE_DAYS (0.25 d)
    before the sign check, coalescing close station pairs; this version keeps
    every sign-confirmed root — no merge window exists here at all. A root
    that does not change the sign of the velocity is a tangency, not a
    station, and is rejected (inherited from w2g, kept).
    """
    derivative = spline.derivative()
    try:
        raw = [float(r) for r in derivative.roots(extrapolate=False)]
    except Exception:  # noqa: BLE001 — scipy version differences only
        raw = []

    lo, hi = float(jds[0]), float(jds[-1])
    candidates = sorted(r for r in raw if lo < r < hi)

    confirmed: list[float] = []
    eps = 0.05
    for r in candidates:
        before = float(derivative(max(lo, r - eps)))
        after = float(derivative(min(hi, r + eps)))
        if before == 0.0 or after == 0.0:
            continue
        if (before > 0.0) != (after > 0.0):
            confirmed.append(r)
    return confirmed


def build_arc_index(
    body: str,
    knot_jds: Sequence[float],
    wrapped_longitudes_deg: Sequence[float],
    tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
) -> ArcIndex:
    """Decompose one body's sidereal longitude history into an arc index.

    Raises ValueError on fewer than 4 knots — an empty arc set would silently
    drop every contact this body ever makes (inherited from w2g, kept).
    """
    if len(knot_jds) != len(wrapped_longitudes_deg):
        raise ValueError("knot and longitude sequences must be the same length")
    if len(knot_jds) < 4:
        raise ValueError(
            f"{body}: a cubic spline needs at least 4 knots, got {len(knot_jds)}"
        )

    unwrapped = unwrap_degrees(wrapped_longitudes_deg)
    spline = CubicSpline(list(knot_jds), list(unwrapped))

    def evaluate(jd: float) -> float:
        return float(spline(jd))

    tol_deg = float(tolerance_arcsec) / ARCSEC_PER_DEG
    stations = _station_times(spline, knot_jds)

    boundaries: list[float] = [float(knot_jds[0])]
    boundaries.extend(stations)
    boundaries.append(float(knot_jds[-1]))
    boundaries = sorted(set(boundaries))

    # Stage 1: station-bounded monotone segments (kept whole — the episode
    # layer solves orb intervals on these so a turnaround INSIDE the orb is
    # not mistaken for an orb exit; E8-2).
    segments: list[MonotoneArc] = []
    station_set = set(stations)
    seg_pairs = list(zip(boundaries, boundaries[1:]))
    for i, (seg_start, seg_end) in enumerate(seg_pairs):
        if seg_end - seg_start <= 0.0:
            continue
        lon_a = evaluate(seg_start)
        lon_b = evaluate(seg_end)
        segments.append(
            MonotoneArc(
                body=body,
                arc_index=i,
                start_jd=float(seg_start),
                end_jd=float(seg_end),
                start_lon_unwrapped=float(lon_a),
                end_lon_unwrapped=float(lon_b),
                direction=1 if lon_b >= lon_a else -1,
                wrap_index=0,  # segments live on the unwrapped branch
                station_bounded=(seg_start in station_set, seg_end in station_set),
                evaluator=evaluate,
            )
        )

    # Stage 2: split each segment at its 360° bands (wrap structure explicit).
    # Cut points carry their EXACT longitude where one is known — a wrap
    # boundary is at exactly 360k by definition (inherited from w2g).
    arcs: list[MonotoneArc] = []
    index = 0
    for seg, (seg_start, seg_end) in zip(segments, seg_pairs):
        if seg_end - seg_start <= 0.0:
            continue
        lon_a = evaluate(seg_start)
        lon_b = evaluate(seg_end)
        rising = lon_b >= lon_a
        direction = 1 if rising else -1

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
            # A wrap cut at an internal station is not a station; only the
            # segment ends keep the segment's station_bounded flags.
            a_is_seg_start = a_jd == seg_start
            b_is_seg_end = b_jd == seg_end
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
                    station_bounded=(
                        seg.station_bounded[0] if a_is_seg_start else False,
                        seg.station_bounded[1] if b_is_seg_end else False,
                    ),
                    evaluator=evaluate,
                )
            )
            index += 1

    return ArcIndex(
        body=body,
        knot_jds=tuple(float(j) for j in knot_jds),
        arcs=arcs,
        segments=segments,
        stations=stations,
        evaluate=evaluate,
        spline=spline,
        tolerance_arcsec=float(tolerance_arcsec),
    )


__all__ = [
    "ARCSEC_PER_DEG",
    "DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC",
    "ArcIndex",
    "MonotoneArc",
    "build_arc_index",
    "unwrap_degrees",
]
