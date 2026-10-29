"""Rule Book engine — tripwires on the birth instant (explicit-offset charts).

The engine takes true UT from the source record. The chart facts it reads (L1) were built by
someone else, possibly with the wrong offset (DF-04). Two independent checks, using only stored
data, catch a chart whose facts were built for a different instant:

1. Sky signs: at the true birth instant the L0 ingress table (computed separately from L1) and
   the L1 natal signs must agree for the seven true grahas. A disagreement is excused only when the
   L1 longitude sits within 0.02 degree of the sign boundary (two ephemerides may round a hair apart).
2. Vimshottari start: the level-1 row covering the birth instant must belong to the lord of the
   Moon's nakshatra, and (unless the row is clipped at the stored window start) must begin where the
   Moon's elapsed nakshatra fraction says it began, to within 120 s (year = 365.25 days, as L1).

Any problem excludes the chart (``L1_UT_MISMATCH``); the caller counts it.
"""

from __future__ import annotations

from typing import List, Optional

from . import constants as K
from .birthrecord import L1_UT_MISMATCH, ChartExcluded
from .chart import NatalChart, utc_to_jd
from .sky import SkyTable

BOUNDARY_EXCUSE_DEG = 0.02
START_TOLERANCE_S = 120.0
DASHA_WINDOW_START_JD = 2433282.5  # 1950-01-01T00:00Z, where the stored Vimshottari window is clipped

VIMSHOTTARI_ORDER = ("ketu", "shukra", "surya", "chandra", "mangala", "rahu", "guru", "shani", "budha")
VIMSHOTTARI_YEARS = {"ketu": 7, "shukra": 20, "surya": 6, "chandra": 10, "mangala": 7, "rahu": 18, "guru": 16, "shani": 19, "budha": 17}
YEAR_DAYS = 365.25


def sky_sign_problems(chart: NatalChart, sky: SkyTable, birth_jd: float) -> List[str]:
    out: List[str] = []
    for g in K.GRAHAS:
        if g in K.NODES:
            continue
        a, b = sky.sign_at(K.L0_BODY[g], birth_jd), chart.sign_of(g)
        if a is None or b is None or a == b:
            continue
        lon = chart.graha(g).longitude
        if lon is not None:
            edge = min(lon % 30.0, 30.0 - lon % 30.0)
            if edge < BOUNDARY_EXCUSE_DEG:
                continue
        out.append(f"{g}: sky ingress table says sign {a} at the stated UT, L1 says {b}")
    return out


def dasha_start_problems(chart: NatalChart, birth_jd: float) -> List[str]:
    lon = chart.graha("chandra").longitude
    if lon is None:
        return ["Moon longitude missing: Vimshottari start cannot be checked"]
    span = 360.0 / 27.0
    idx = min(int(lon // span), 26)
    lord = VIMSHOTTARI_ORDER[idx % 9]
    frac = (lon - idx * span) / span
    row = None
    for r in chart.md.rows:
        if r.start_jd <= birth_jd < r.end_jd:
            row = r
    if row is None:
        return ["no level-1 daśā row covers the stated UT of birth"]
    if row.lord != lord:
        return [f"daśā at the stated UT is {row.lord}, the Moon's nakshatra lord is {lord}"]
    if row.start_jd <= DASHA_WINDOW_START_JD + 1e-9:
        return []  # clipped at the stored window start: the true start is not stored
    expected = birth_jd - frac * VIMSHOTTARI_YEARS[lord] * YEAR_DAYS
    diff = abs(row.start_jd - expected) * K.SECONDS_PER_DAY
    if diff > START_TOLERANCE_S:
        return [f"Vimshottari {lord} start differs from the Moon-fraction start by {diff:.0f} s (limit {START_TOLERANCE_S:.0f} s)"]
    return []


def utc_consistency_problems(chart: NatalChart, sky: Optional[SkyTable]) -> List[str]:
    if chart.birth.birth_utc is None:
        return ["birth instant not resolved"]
    jd = utc_to_jd(chart.birth.birth_utc)
    out = dasha_start_problems(chart, jd)
    if sky is not None:
        out = sky_sign_problems(chart, sky, jd) + out
    return out


def require_consistent(chart: NatalChart, sky: Optional[SkyTable]) -> None:
    problems = utc_consistency_problems(chart, sky)
    if problems:
        raise ChartExcluded(L1_UT_MISMATCH, "; ".join(problems))
