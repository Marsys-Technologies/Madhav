"""W2G — the database-backed arc substrate: build it once, join against it forever.

TWO HALVES, AND THE LINE BETWEEN THEM IS THE ARCHITECTURE:

  * `build_arcs_for_body(query, body, ...)` — CHART-INDEPENDENT. Reads a body's
    `ephemeris_daily` rows and decomposes them into monotone arcs. When Saturn
    reaches 123.45° does not depend on anyone's birth data, so this runs ONCE,
    globally, as the `bg_gochara_arcs` L0 asset, and every chart that ever
    onboards reads the same rows. This is what makes the ≤15-minute
    full-century onboarding SLO (W2G design amendment 1) a different cost shape
    rather than a faster version of the same shape.

  * `DbArcSource` — the per-chart read path. TWO bulk queries for a whole
    chart's contact computation, both scoped by body, neither scoped by target:
    one for the arcs, one for the ephemeris knots the interpolant needs. The
    per-(target x primitive x window) query that cost v1 ~110-120ms a time has
    no counterpart here — there is nowhere for it to live.

QUERY SEAM. Both halves take a `QueryFn` (the same seam
`services/w2g_validations` established), so every statement is unit-testable
without a database and the live adapter is a one-liner. Every statement issued
by this module is a SELECT; the only writes in W2G's global path are the
writer's own delete-then-insert into `bg_gochara_arcs`.
"""
from __future__ import annotations

from typing import Any, Sequence

from services.w2g_validations._db import QueryFn

from .arcs import MonotoneArc, build_arcs, unwrap_degrees

EPHEMERIS_TABLE = "ephemeris_daily"
ARC_TABLE = "bg_gochara_arcs"
AYANAMSHA_ID = "tropical"


# ── knot abscissa ────────────────────────────────────────────────────────────
#
# NOON UT, because that is what `brahmagyan.l0_ephemeris` built every row at
# (`swe.julday(y, m, d, 12.0)`). V3 measured what assuming midnight would cost:
# half a day, ~6.6° for the Moon. Computed here with the plain Julian-day
# formula rather than via swisseph, so the arc builder has no ephemeris-library
# dependency at all — the numbers are already in the table.

def noon_ut_jd(year: int, month: int, day: int) -> float:
    """Julian day at 12:00 UT for a Gregorian calendar date."""
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    jd_midnight = (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + day
        + b
        - 1524.5
    )
    return jd_midnight + 0.5


def _row_date(value: Any):
    from datetime import date as _date

    if isinstance(value, _date):
        return value
    return _date.fromisoformat(str(value)[:10])


def fetch_body_series(
    query: QueryFn,
    body: str,
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> tuple[list[float], list[float]]:
    """One bulk SELECT -> (noon-UT Julian days, wrapped tropical longitudes)."""
    sql = (
        f"SELECT date, tropical_longitude FROM {EPHEMERIS_TABLE} "
        f"WHERE body = %s AND ayanamsha_id = %s"
    )
    params: list[Any] = [body, AYANAMSHA_ID]
    if start_date is not None:
        sql += " AND date >= %s"
        params.append(start_date)
    if end_date is not None:
        sql += " AND date <= %s"
        params.append(end_date)
    sql += " ORDER BY date"

    rows = query(sql, params)
    jds: list[float] = []
    lons: list[float] = []
    for row in rows:
        d = _row_date(row["date"])
        jds.append(noon_ut_jd(d.year, d.month, d.day))
        lons.append(float(row["tropical_longitude"]))
    return jds, lons


def build_arcs_for_body(
    query: QueryFn,
    body: str,
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> tuple[list[MonotoneArc], int]:
    """Decompose one body's stored ephemeris into arcs. Returns (arcs, knots).

    The knot count comes back with the arcs because it is an input to the arc
    fingerprint — computing it here means the caller never has to re-query for
    it, and never has to guess.
    """
    jds, lons = fetch_body_series(query, body, start_date, end_date)
    if len(jds) < 4:
        raise ValueError(
            f"{body}: {EPHEMERIS_TABLE} returned {len(jds)} rows for "
            f"ayanamsha_id={AYANAMSHA_ID!r} — a cubic spline needs at least 4. "
            "This is an honest failure, not an empty arc set: an empty arc set "
            "would silently drop every contact this body ever makes."
        )
    return build_arcs(body, jds, lons), len(jds)


def _arc_from_row(row: dict[str, Any]) -> MonotoneArc:
    return MonotoneArc(
        body=str(row["body"]),
        arc_index=int(row["arc_index"]),
        start_jd=float(row["start_jd"]),
        end_jd=float(row["end_jd"]),
        start_lon_unwrapped=float(row["start_lon_unwrapped_deg"]),
        end_lon_unwrapped=float(row["end_lon_unwrapped_deg"]),
        direction=int(row["direction"]),
        wrap_index=int(row["wrap_index"]),
    )


class DbArcSource:
    """`ArcSource` over `bg_gochara_arcs` + `ephemeris_daily`.

    EXACTLY TWO QUERIES PER `load()`, both bulk and both scoped by body only:

      1. the arcs for the requested bodies;
      2. the ephemeris knots those bodies' interpolants are fitted over.

    Not two per body, not two per target — two. `queries_issued` counts them
    so the property is measured rather than asserted in prose.
    """

    def __init__(
        self,
        query: QueryFn,
        substrate_version: str,
        start_date: Any | None = None,
        end_date: Any | None = None,
    ):
        self._query = query
        self._substrate_version = substrate_version
        self._start_date = start_date
        self._end_date = end_date
        self.queries_issued = 0

    def load(self, bodies: Sequence[str]) -> dict[str, list[MonotoneArc]]:
        bodies = tuple(bodies)
        if not bodies:
            return {}

        arc_rows = self._query(
            f"SELECT body, arc_index, start_jd, end_jd, start_lon_unwrapped_deg, "
            f"end_lon_unwrapped_deg, direction, wrap_index FROM {ARC_TABLE} "
            f"WHERE substrate_version = %s AND body = ANY(%s) "
            f"ORDER BY body, arc_index",
            [self._substrate_version, list(bodies)],
        )
        self.queries_issued += 1

        sql = (
            f"SELECT body, date, tropical_longitude FROM {EPHEMERIS_TABLE} "
            f"WHERE ayanamsha_id = %s AND body = ANY(%s)"
        )
        params: list[Any] = [AYANAMSHA_ID, list(bodies)]
        if self._start_date is not None:
            sql += " AND date >= %s"
            params.append(self._start_date)
        if self._end_date is not None:
            sql += " AND date <= %s"
            params.append(self._end_date)
        sql += " ORDER BY body, date"
        ephe_rows = self._query(sql, params)
        self.queries_issued += 1

        series: dict[str, tuple[list[float], list[float]]] = {}
        for row in ephe_rows:
            body = str(row["body"])
            d = _row_date(row["date"])
            jds, lons = series.setdefault(body, ([], []))
            jds.append(noon_ut_jd(d.year, d.month, d.day))
            lons.append(float(row["tropical_longitude"]))

        evaluators: dict[str, Any] = {}
        for body, (jds, lons) in series.items():
            if len(jds) < 4:
                continue
            from .arcs import _make_unwrapped_evaluator  # local: private by design

            evaluators[body] = _make_unwrapped_evaluator(jds, unwrap_degrees(lons))

        out: dict[str, list[MonotoneArc]] = {b: [] for b in bodies}
        for row in arc_rows:
            arc = _arc_from_row(row)
            evaluator = evaluators.get(arc.body)
            out.setdefault(arc.body, []).append(
                arc.with_evaluator(evaluator) if evaluator is not None else arc
            )
        return out


__all__ = [
    "ARC_TABLE",
    "AYANAMSHA_ID",
    "DbArcSource",
    "EPHEMERIS_TABLE",
    "build_arcs_for_body",
    "fetch_body_series",
    "noon_ut_jd",
]
