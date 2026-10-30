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


def ephemeris_moon_sidereal(jd_ut: float) -> Optional[float]:
    """Moon's Lahiri sidereal longitude by DIRECT Swiss Ephemeris at jd_ut (true geometric position, the L1 convention).
    None if the pinned .se1 files are not in use (Moshier fallback): the check then fails closed."""
    import os

    import swisseph as swe

    swe.set_ephe_path(os.environ.get("SE_EPHE_PATH") or None)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    xx, ret = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_TRUEPOS)
    if not ret & swe.FLG_SWIEPH:
        return None
    return xx[0] % 360.0


def pre_window_dasha_problems(chart: NatalChart, birth_jd: float) -> List[str]:
    """SUR-RB-49: a birth before the stored window start. The FIRST stored level-1 row must carry the lord that an
    independent 120-year walk from the ephemeris Moon at the true UT gives at the window start, and its END must lie within
    START_TOLERANCE_S of that walk's end after the SUR-RB-30 allowance for the L1-vs-ephemeris Moon difference."""
    if not chart.md.rows:
        return ["no stored level-1 daśā row"]
    first = chart.md.rows[0]
    if first.start_jd > DASHA_WINDOW_START_JD + 1e-9:
        return ["first stored level-1 row does not start at the stored window start"]
    moon = ephemeris_moon_sidereal(birth_jd)
    if moon is None:
        return ["pinned ephemeris not in use: the pre-window Vimshottari check cannot run"]
    span = 360.0 / 27.0
    idx = min(int(moon // span), 26)
    frac = (moon - idx * span) / span
    i, start = idx % 9, birth_jd - frac * VIMSHOTTARI_YEARS[VIMSHOTTARI_ORDER[idx % 9]] * YEAR_DAYS
    ref = None
    while start < DASHA_WINDOW_START_JD + 130 * YEAR_DAYS:
        lord = VIMSHOTTARI_ORDER[i % 9]
        end = start + VIMSHOTTARI_YEARS[lord] * YEAR_DAYS
        if start <= first.start_jd < end:
            ref = (lord, end)
            break
        start, i = end, i + 1
    if ref is None:
        return ["the independent walk does not reach the stored window start"]
    if first.lord != ref[0]:
        return [f"first stored daśā is {first.lord}, the ephemeris walk gives {ref[0]} at the window start"]
    l1_moon = chart.graha("chandra").longitude
    allowance = 0.0
    if l1_moon is not None:
        dm = (l1_moon - moon + 180.0) % 360.0 - 180.0
        allowance = -dm / span * VIMSHOTTARI_YEARS[VIMSHOTTARI_ORDER[idx % 9]] * YEAR_DAYS
    diff = abs(first.end_jd - (ref[1] + allowance)) * K.SECONDS_PER_DAY
    if diff > START_TOLERANCE_S:
        return [f"first stored {first.lord} end differs from the ephemeris walk by {diff:.0f} s (limit {START_TOLERANCE_S:.0f} s)"]
    return []


def dasha_start_problems(chart: NatalChart, birth_jd: float) -> List[str]:
    if birth_jd < DASHA_WINDOW_START_JD:
        return pre_window_dasha_problems(chart, birth_jd)
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
