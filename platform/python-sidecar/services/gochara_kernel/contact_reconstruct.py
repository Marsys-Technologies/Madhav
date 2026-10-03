"""INDEPENDENT reconstruction of residence contacts from the ephemeris (Codex round 9, R9-2 iii and R9-3).

The verifier does not trust the builder's contact ledger, its endpoint probes or its supports: it re-derives, from
`position_at(body, t)` alone (the Swiss ephemeris), the maximal intervals over a horizon during which a body's sidereal
longitude lies in each zodiac sign. Nothing here imports the builder's geometry (`contacts`, `arcs`, `knots`, `materialise`,
`targets`); the speed bounds and the guarantee are this module's own.

GUARANTEE (a sentence with its assumption — stated in coverage, never left as silence):
  Under SMOOTH MOTION (a body's longitude is continuous and its speed never exceeds `VMAX_DPS[body]` degrees/day), every
  interval of at least `MIN_EXCURSION_SECONDS` during which the body is in, or out of, a sign is found, and each
  boundary crossing is located to within `BISECT_SECONDS`. Excursions SHORTER than `MIN_EXCURSION_SECONDS` are NOT
  excluded: a body hovering on a sign boundary through a station can enter and leave faster than the refinement
  resolves, and such a flicker is not certified absent. This is a NAMED LIMIT, carried into every verification report.

METHOD: sample every `STEP_SECONDS`. From a sample at distance `d` from the nearest sign boundary the body cannot reach a
boundary within `dt` seconds when `d > VMAX * dt` — so such a step is constant, with no further evaluation. Any other step
is bisected (recursively) down to `MIN_EXCURSION_SECONDS`; where the sign differs across a refined step the crossing is
bisected to `BISECT_SECONDS`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

#: maximum |sidereal longitudinal speed| in degrees/day, with margin (this module's own table)
VMAX_DPS = {"sun": 1.2, "moon": 16.0, "mars": 1.0, "mercury": 2.6, "venus": 1.6, "jupiter": 0.35, "saturn": 0.2,
            "rahu": 0.08, "ketu": 0.08}
STEP_SECONDS = 6 * 3600
MIN_EXCURSION_SECONDS = 60
BISECT_SECONDS = 1.0
#: the named limit, verbatim, for every report that relies on this reconstruction
NAMED_LIMIT = (f"contact geometry is certified under smooth motion (speed <= the stated per-body bound): every in-sign / "
               f"out-of-sign interval of at least {MIN_EXCURSION_SECONDS} s is found and each crossing located to within "
               f"{BISECT_SECONDS} s; excursions shorter than {MIN_EXCURSION_SECONDS} s are not excluded")
GUARANTEE_ASSUMPTION = "smooth_motion_speed_bounded"

UTC = timezone.utc


class GeometryUnavailable(RuntimeError):
    """The ephemeris needed to reconstruct the geometry is not available: no complete-search claim can be made."""


def _cell(lon: float, width: float) -> int:
    return int((lon % 360.0) // width)


def _dist_to_cell_edge(lon: float, width: float) -> float:
    m = (lon % 360.0) % width
    return min(m, width - m)


def _angdiff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _core(state_at, edge_distance, vmax_dps: float, lo: datetime, hi: datetime) -> list[datetime]:
    """The instants in (lo, hi) at which `state_at` changes, located to BISECT_SECONDS, found under the speed bound:
    from a sample at distance `d` from a state edge the state cannot flip within `dt` seconds when `d > vmax*dt`
    (the quantity `edge_distance(t)` is a distance in degrees to the nearest edge of the state)."""
    if hi <= lo:
        raise ValueError("empty horizon")
    vmax = vmax_dps / 86400.0                                     # degrees per second
    changes: list[datetime] = []

    def crossing(a: datetime, b: datetime) -> datetime:
        base = state_at(a)
        while (b - a).total_seconds() > BISECT_SECONDS:
            m = a + (b - a) / 2
            if state_at(m) == base:
                a = m
            else:
                b = m
        return b

    def refine(a: datetime, b: datetime) -> None:
        dt = (b - a).total_seconds()
        sa, sb = state_at(a), state_at(b)
        if sa == sb and edge_distance(a) > vmax * dt and edge_distance(b) > vmax * dt:
            return                                                # cannot reach an edge within the step
        if dt <= MIN_EXCURSION_SECONDS:
            if sa != sb:
                changes.append(crossing(a, b))
            return
        m = a + (b - a) / 2
        refine(a, m)
        refine(m, b)

    t = lo
    step = timedelta(seconds=STEP_SECONDS)
    while t < hi:
        nxt = min(t + step, hi)
        refine(t, nxt)
        t = nxt
    return sorted(changes)


def _lon_source(position_at, body: str):
    cache: dict[datetime, float] = {}

    def lon_at(t: datetime) -> float:
        if t not in cache:
            v = position_at(body, t)
            if v is None:
                raise GeometryUnavailable(f"{body} position undeterminable at {t.isoformat()}")
            cache[t] = float(v)
        return cache[t]
    return lon_at


def partition_intervals(position_at, body: str, cells: int, lo: datetime, hi: datetime,
                        ) -> dict[int, list[tuple[datetime, datetime]]]:
    """{cell_index: [(t_in, t_out), …]} — the maximal intervals within [lo, hi) during which `body`'s sidereal longitude
    lies in each of `cells` equal cells of the zodiac (12 = signs, 27 = nakṣatras), clipped to the horizon. A position
    that cannot be determined raises `GeometryUnavailable` (incomplete evidence prevents a complete-search claim)."""
    width = 360.0 / cells
    lon_at = _lon_source(position_at, body)
    changes = _core(lambda t: _cell(lon_at(t), width), lambda t: _dist_to_cell_edge(lon_at(t), width),
                    VMAX_DPS[body.lower()], lo, hi)
    out: dict[int, list[tuple[datetime, datetime]]] = {i: [] for i in range(cells)}
    starts, cur = lo, _cell(lon_at(lo), width)
    for c in changes:
        if c <= starts:
            continue
        out[cur].append((starts, c))
        starts, cur = c, _cell(lon_at(c), width)
    out[cur].append((starts, hi))
    return out


def residence_intervals(position_at, body: str, lo: datetime, hi: datetime, *, step_seconds: int = STEP_SECONDS,
                        ) -> dict[int, list[tuple[datetime, datetime]]]:
    """The sign case of `partition_intervals` (12 cells; 0 = Aries)."""
    return partition_intervals(position_at, body, 12, lo, hi)


def band_intervals(position_at, body: str, centres, orb_deg: float, lo: datetime, hi: datetime,
                   ) -> list[tuple[datetime, datetime]]:
    """The maximal intervals within [lo, hi) during which `body` is within `orb_deg` of ANY longitude in `centres`
    (a conjunction point, or the aspect points λ − angle for each directed angle) — the point-contact geometry."""
    lon_at = _lon_source(position_at, body)
    centres = [float(c) % 360.0 for c in centres]

    def gap(t):
        x = lon_at(t)
        return min(_angdiff(x, c) for c in centres) - orb_deg       # <= 0 inside the band

    changes = _core(lambda t: gap(t) <= 0.0, lambda t: abs(gap(t)), VMAX_DPS[body.lower()], lo, hi)
    out: list[tuple[datetime, datetime]] = []
    inside, starts = gap(lo) <= 0.0, lo
    for c in changes:
        if c <= starts:
            continue
        if inside:
            out.append((starts, c))
        starts, inside = c, gap(c) <= 0.0
    if inside:
        out.append((starts, hi))
    return out


_CACHE: dict = {}


def cached_partition_intervals(position_at, body: str, cells: int, lo: datetime, hi: datetime):
    """`partition_intervals`, memoised across classes when the source declares a `cache_key` (see below)."""
    key = getattr(position_at, "cache_key", None)
    if key is None:
        return partition_intervals(position_at, body, cells, lo, hi)
    full = (key, body, cells, lo, hi)
    if full not in _CACHE:
        _CACHE[full] = partition_intervals(position_at, body, cells, lo, hi)
    return _CACHE[full]


def cached_residence_intervals(position_at, body: str, lo: datetime, hi: datetime):
    """`residence_intervals`, memoised ACROSS CLASSES when the position source declares an identity
    (`position_at.cache_key`, e.g. ("swiss", ephe_path)): the reconstruction depends only on (source, body, horizon), and a
    26-class build would otherwise redo the same 28-year sweep per class. A source without a `cache_key` (a test
    stand-in) is never cached."""
    return cached_partition_intervals(position_at, body, 12, lo, hi)


__all__ = ["BISECT_SECONDS", "band_intervals", "cached_partition_intervals", "cached_residence_intervals", "partition_intervals", "GUARANTEE_ASSUMPTION", "GeometryUnavailable", "MIN_EXCURSION_SECONDS", "NAMED_LIMIT",
           "STEP_SECONDS", "VMAX_DPS", "residence_intervals"]
