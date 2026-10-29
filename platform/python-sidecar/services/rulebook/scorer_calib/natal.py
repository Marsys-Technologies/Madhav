"""A natal chart for the engine, computed from birth data alone (calibration use).

The engine reads a ``NatalChart`` (signs, retrograde and exaltation flags, Parashari aspects, D1 house lords,
Vimshottari level 1 and 2). Production gets these from L1 ``chart_facts`` / ``chart_dashas``. The calibration
has no L1 build for its charts, so this module computes the same operands directly: Swiss Ephemeris (Moshier),
Lahiri sidereal, whole-sign houses, the standard sign lordships, sign-based exaltation / debilitation, the
classical Parashari special aspects, and Vimshottari from the Moon's longitude (year = 365.25 days, the L1
convention) with the stored window clipped at 1950-01-01 like L1. Nodes are left unknown (nodes-out policy).

It is a CALIBRATION fixture: the timelines it yields are used to measure the scorer's behaviour, never to
make a claim about a person's chart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..engine import constants as K
from ..engine.birthcheck import DASHA_WINDOW_START_JD, VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, YEAR_DAYS
from ..engine.chart import Birth, DashaLevel, DashaRow, GrahaFacts, NatalChart, utc_to_jd
from .births import BirthRow

# card graha -> swisseph body id name
_BODY = {"surya": "SUN", "chandra": "MOON", "mangala": "MARS", "budha": "MERCURY", "guru": "JUPITER", "shukra": "VENUS", "shani": "SATURN"}
# sign (1..12) -> lord (card name)
SIGN_LORD = {1: "mangala", 2: "shukra", 3: "budha", 4: "chandra", 5: "surya", 6: "budha", 7: "shukra", 8: "mangala", 9: "guru", 10: "shani", 11: "shani", 12: "guru"}
EXALT = {"surya": 1, "chandra": 2, "mangala": 10, "budha": 6, "guru": 4, "shukra": 12, "shani": 7}
DEBIL = {g: (s + 5) % 12 + 1 for g, s in EXALT.items()}
# houses aspected counted from the graha's own house (inclusive): every graha the 7th; Mars 4,8; Jupiter 5,9; Saturn 3,10
SPECIAL = {"mangala": (4, 8), "guru": (5, 9), "shani": (3, 10)}


def _swe():
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe


def build_natal(b: BirthRow, minute_shift: int = 0, key: Optional[str] = None) -> NatalChart:
    """NatalChart for birth ``b``; ``minute_shift`` moves the birth time (birth-time stability builds, C2)."""
    swe = _swe()
    h, m = (int(x) for x in b.local_time.split(":")[:2])
    local = datetime(b.local_date.year, b.local_date.month, b.local_date.day, h, m) + timedelta(minutes=minute_shift)
    utc = (local - timedelta(minutes=b.utc_offset_minutes)).replace(tzinfo=timezone.utc)
    jd = utc_to_jd(utc)
    fl = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    lon: Dict[str, float] = {}
    retro: Dict[str, bool] = {}
    for g, nm in _BODY.items():
        xx, _ret = swe.calc_ut(jd, getattr(swe, nm), fl)
        lon[g] = xx[0] % 360.0
        retro[g] = bool(xx[3] < 0) if g not in ("surya", "chandra") else False
    _cusps, ascmc = swe.houses_ex(jd, b.lat, b.lon, b"W", swe.FLG_SIDEREAL)
    lagna = int((ascmc[0] % 360.0) // 30) + 1
    sign = {g: int(lon[g] // 30) + 1 for g in lon}
    grahas: Dict[str, GrahaFacts] = {}
    aspected: Dict[str, Optional[frozenset]] = {}
    for g in K.GRAHAS:
        if g in K.NODES:
            grahas[g] = GrahaFacts()
            aspected[g] = None
            continue
        grahas[g] = GrahaFacts(
            sign=sign[g], retrograde=retro[g], exalted=sign[g] == EXALT[g], debilitated=sign[g] == DEBIL[g], dignity_state=None, longitude=lon[g]
        )
        own_house = (sign[g] - lagna) % 12 + 1
        offs = {7} | set(SPECIAL.get(g, ()))
        aspected[g] = frozenset((own_house + o - 2) % 12 + 1 for o in offs)
    lords = {h_: SIGN_LORD[(lagna + h_ - 2) % 12 + 1] for h_ in range(1, 13)}
    md, ad = _vimshottari(lon["chandra"], jd)
    birth = Birth(
        birth_date=local.date(),
        birth_time_local=local.strftime("%H:%M:%S"),
        lat=b.lat,
        lon=b.lon,
        zone=None,
        birth_utc=utc,
        utc_offset_minutes=b.utc_offset_minutes,
    )
    return NatalChart(
        chart_key=key or b.code,
        birth=birth,
        lagna_sign=lagna,
        grahas=grahas,
        aspected_houses=aspected,
        house_lords=lords,
        md=DashaLevel(md),
        ad=DashaLevel(ad),
    )


def _vimshottari(moon_lon: float, birth_jd: float, span_years: float = 125.0):
    span = 360.0 / 27.0
    idx = min(int(moon_lon // span), 26)
    k = idx % 9
    frac = (moon_lon - idx * span) / span
    start = birth_jd - frac * VIMSHOTTARI_YEARS[VIMSHOTTARI_ORDER[k]] * YEAR_DAYS
    end_all = birth_jd + span_years * YEAR_DAYS
    md: List[DashaRow] = []
    ad: List[DashaRow] = []
    t = start
    i = k
    while t < end_all:
        lord = VIMSHOTTARI_ORDER[i % 9]
        dur = VIMSHOTTARI_YEARS[lord] * YEAR_DAYS
        _push(md, lord, t, t + dur)
        a = t
        for j in range(9):
            al = VIMSHOTTARI_ORDER[(i + j) % 9]
            ad_dur = dur * VIMSHOTTARI_YEARS[al] / 120.0
            _push(ad, al, a, a + ad_dur)
            a += ad_dur
        t += dur
        i += 1
    return md, ad


def _push(rows: List[DashaRow], lord: str, s: float, e: float) -> None:
    """Append a row clipped to the stored window (starts 1950-01-01), like L1; rows wholly before it are dropped."""
    if e <= DASHA_WINDOW_START_JD:
        return
    rows.append(DashaRow(lord, max(s, DASHA_WINDOW_START_JD), e))
