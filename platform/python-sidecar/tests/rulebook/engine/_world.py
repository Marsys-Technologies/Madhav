"""Synthetic world for the engine tests: invented chart, invented sky, invented sunrise table.

Nothing here is a real chart, a real sky row or a real verse. Expected values in the tests are
computed with plain arithmetic in the test body, not with engine functions.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

JD_EPOCH = 2440587.5
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
MD_ORDER = ["shukra", "surya", "chandra", "mangala", "rahu", "guru", "shani", "budha", "ketu"]
MD_YEARS = {"ketu": 7, "shukra": 20, "surya": 6, "chandra": 10, "mangala": 7, "rahu": 18, "guru": 16, "shani": 19, "budha": 17}
YEAR_DAYS = 365.25


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jd_of(dt: datetime) -> float:
    return JD_EPOCH + dt.timestamp() / 86400.0


def utc(y: int, m: int, d: int, hh: int = 0, mm: int = 0, ss: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


def dasha_tables(md_start: datetime, first_md: str, n_md: int = 4) -> Dict[str, List[Dict[str, str]]]:
    """Vimshottari-style MD + AD rows (year = 365.25 d; AD = MD days x AD years / 120)."""
    mds, ads = [], []
    order = MD_ORDER[MD_ORDER.index(first_md):] + MD_ORDER[: MD_ORDER.index(first_md)]
    t = md_start
    for k in range(n_md):
        lord = order[k % 9]
        md_days = MD_YEARS[lord] * YEAR_DAYS
        md_end = t + timedelta(days=md_days)
        mds.append({"lord": lord, "start_utc": iso(t), "end_utc": iso(md_end)})
        a0 = t
        sub = order[(k % 9):] + order[: (k % 9)]
        for j, al in enumerate(sub):
            a1 = md_end if j == 8 else a0 + timedelta(days=md_days * MD_YEARS[al] / 120.0)
            ads.append({"lord": al, "start_utc": iso(a0), "end_utc": iso(a1)})
            a0 = a1
        t = md_end
    return {"mahadasha": mds, "antardasha": ads}


def chart_doc(birth_date: str = "2000-03-04", birth_utc_s: str = "2000-03-04T03:30:00Z", dasha: Optional[dict] = None, **over: Any) -> dict:
    doc: Dict[str, Any] = {
        "fixture_schema": "rulebook-engine-fixture-v1",
        "chart_key": "SYN-CHART",
        "birth": {"date": birth_date, "time_local": "09:00:00", "lat": 20.3, "lon": 85.8, "zone": "Asia/Kolkata", "birth_utc": birth_utc_s},
        "lagna_sign": 1,
        "graha": {
            "surya": {"sign": 5, "retrograde": False, "exalted": False, "debilitated": False, "dignity_state": "own"},
            "chandra": {"sign": 2, "retrograde": False, "exalted": True, "debilitated": False, "dignity_state": "exalted"},
            "mangala": {"sign": 3, "retrograde": False, "exalted": False, "debilitated": False, "dignity_state": "neutral"},
            "budha": {"sign": 1, "retrograde": True, "exalted": False, "debilitated": False, "dignity_state": "neutral"},
            "guru": {"sign": 9, "retrograde": False, "exalted": False, "debilitated": False, "dignity_state": "own"},
            "shukra": {"sign": 12, "retrograde": False, "exalted": True, "debilitated": False, "dignity_state": "exalted"},
            "shani": {"sign": 11, "retrograde": True, "exalted": False, "debilitated": False, "dignity_state": "own"},
            "rahu": {"sign": 7, "retrograde": True, "exalted": False, "debilitated": False, "dignity_state": "neutral"},
            "ketu": {"sign": 1, "retrograde": True, "exalted": False, "debilitated": False, "dignity_state": "neutral"},
        },
        "aspected_houses": {
            "surya": [11],
            "chandra": [8],
            "mangala": [6, 9, 10],
            "budha": [7],
            "guru": [1, 3, 5],
            "shukra": [6],
            "shani": [1, 5, 8],
            "rahu": [1, 3, 5],
            "ketu": [3, 5, 7],
        },
        "house_lord": {str(i + 1): g for i, g in enumerate(["mangala", "shukra", "budha", "chandra", "surya", "budha", "shukra", "mangala", "guru", "shani", "shani", "guru"])},
        "dasha": dasha if dasha is not None else dasha_tables(utc(2000, 3, 4, 3, 30), "shukra", 3),
    }
    doc.update(over)
    return doc


def sky_doc(first: datetime, last: datetime) -> dict:
    """Invented ingress rows: Moon every 2.5 d, Sun every 30 d, Mars 45 d, Mercury 25 d, Jupiter 365 d, Venus 28 d, Saturn 900 d.
    Signs advance by one each row. Coverage ends at the last Moon row."""
    periods = {"Moon": (2.5, 3), "Sun": (30.0, 5), "Mars": (45.0, 2), "Mercury": (25.0, 11), "Jupiter": (365.0, 8), "Venus": (28.0, 12), "Saturn": (900.0, 10)}
    rows = []
    rid = 1
    j0 = jd_of(first) - 1000.0
    j1 = jd_of(last)
    for body, (period, s0) in periods.items():
        k = 0
        while True:
            jd = j0 + k * period
            if jd > j1 + 3:
                break
            rows.append({"id": rid, "event_type": "ingress", "primary_body": body, "sign": SIGNS[(s0 - 1 + k) % 12], "event_jd": round(jd, 5)})
            rid += 1
            k += 1
    moon = [r["event_jd"] for r in rows if r["primary_body"] == "Moon"]
    return {"rows": rows, "coverage_end_jd": max(moon)}


def sunrise_table(first: date, last: date, hh: int = 0, mm: int = 30) -> Dict[str, str]:
    out = {}
    d = first
    while d <= last:
        out[d.isoformat()] = iso(datetime(d.year, d.month, d.day, hh, mm, 0, tzinfo=timezone.utc))
        d += timedelta(days=1)
    return out


def expected_sign(sky: dict, body: str, jd: float) -> Optional[int]:
    """Independent re-statement of sign_at (plain loop, no bisect)."""
    if jd > sky["coverage_end_jd"]:
        return None
    best = None
    for r in sky["rows"]:
        if r["primary_body"] == body and r["event_jd"] <= jd and (best is None or r["event_jd"] > best["event_jd"]):
            best = r
    return None if best is None else SIGNS.index(best["sign"]) + 1
