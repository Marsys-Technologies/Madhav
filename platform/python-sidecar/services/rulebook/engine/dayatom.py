"""Rule Book engine (E4) — the day atom: sunrise to sunrise at the birthplace.

Civil date D (in the birthplace zone) names the day that STARTS at D's sunrise;
its state is the configuration at that instant (ENGINE_PLAN §2.5, YARDSTICK §3.1).

Time zone fails closed (DF-04): the L1 writers fall back silently to IST, so a
chart is accepted only if its zone is an IST zone name AND the tz database gives
+05:30 for every date of the run. Anything else raises ``TimeZoneNotSupported``.

Sunrise comes from a provider. ``PanchangEngineSunrise`` calls the repo's own
``panchang_engine.timings.compute_sunrise_sunset`` (upper limb, refraction, the Drik
convention), the function that populates ``panchanga_daily``; its outputs
are cross-checked against the stored ``panchanga_daily`` rows in the tests where
that table has them. ``TableSunrise`` serves explicit instants (tests, oracles).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Mapping, Optional, Protocol

from . import constants as K
from .chart import Birth, ChartDataError, utc_to_jd


class TimeZoneNotSupported(ValueError):
    """The birthplace zone is not an IST zone (DF-04: no silent IST fallback)."""


class SunriseProvider(Protocol):
    name: str

    def sunrise_utc(self, d: date) -> Optional[datetime]: ...


def tzdb_version() -> str:
    """Best-effort tz database version string for the manifest ('unknown' if unreadable)."""
    try:
        import zoneinfo

        for base in zoneinfo.TZPATH:
            try:
                with open(f"{base}/tzdata.zi", "r", encoding="utf-8") as fh:
                    first = fh.readline().strip()
                if first.startswith("# version"):
                    return first.replace("# version", "").strip()
            except OSError:
                continue
        try:
            import tzdata  # type: ignore

            return "tzdata-" + str(tzdata.IANA_VERSION)
        except Exception:
            pass
    except Exception:
        pass
    return "unknown"


def require_ist(zone: Optional[str], first: date, last: date) -> None:
    """Raise unless ``zone`` is an IST zone with a constant +05:30 offset from ``first`` to ``last``."""
    if not zone or zone not in K.IST_ZONES:
        raise TimeZoneNotSupported(
            f"birthplace zone {zone!r} is not an IST zone; only IST charts are evaluated until DF-04 is fixed"
        )
    import zoneinfo

    try:
        z = zoneinfo.ZoneInfo(zone)
    except Exception as exc:  # tz database missing the name
        raise TimeZoneNotSupported(f"zone {zone!r} unreadable in the tz database: {exc}") from exc
    # offset at the day boundaries and mid-points; IST has no DST, so one step per year is ample
    d = first
    while d <= last:
        off = z.utcoffset(datetime.combine(d, time(12, 0)))
        if off is None or off != timedelta(minutes=K.IST_OFFSET_MINUTES):
            raise TimeZoneNotSupported(f"{zone} offset on {d} is {off}, not +05:30 (pre-1955 regional time?)")
        d = d + timedelta(days=366)
    off = z.utcoffset(datetime.combine(last, time(12, 0)))
    if off != timedelta(minutes=K.IST_OFFSET_MINUTES):
        raise TimeZoneNotSupported(f"{zone} offset on {last} is {off}, not +05:30")


def birth_utc(birth: Birth) -> datetime:
    """Birth instant in UTC. IST only (the caller must have passed ``require_ist``)."""
    if birth.zone not in K.IST_ZONES:
        raise TimeZoneNotSupported(f"zone {birth.zone!r}: no silent IST fallback")
    parts = [int(x) for x in birth.birth_time_local.split(":")]
    while len(parts) < 3:
        parts.append(0)
    local = datetime.combine(birth.birth_date, time(parts[0], parts[1], parts[2]))
    return (local - timedelta(minutes=K.IST_OFFSET_MINUTES)).replace(tzinfo=timezone.utc)


class TableSunrise:
    """Explicit sunrise instants by civil date (tests, oracle fixtures)."""

    name = "table"

    def __init__(self, table: Mapping[str, str]):
        from .chart import parse_utc

        self._t: Dict[date, datetime] = {date.fromisoformat(k): parse_utc(v) for k, v in table.items()}

    def sunrise_utc(self, d: date) -> datetime:
        try:
            return self._t[d]
        except KeyError:
            raise ChartDataError(f"no sunrise instant supplied for {d}") from None


class PanchangEngineSunrise:
    """Sunrise from the repo's panchang_engine (Swiss Ephemeris, serialized). IST birthplaces only."""

    name = "panchang_engine.timings.compute_sunrise_sunset"

    def __init__(self, lat: float, lon: float, tz_offset_minutes: int = K.IST_OFFSET_MINUTES):
        if tz_offset_minutes != K.IST_OFFSET_MINUTES:
            raise TimeZoneNotSupported("sunrise provider accepts the IST offset only (DF-04)")
        self.lat, self.lon, self.tz = lat, lon, tz_offset_minutes
        self._cache: Dict[date, datetime] = {}

    def sunrise_utc(self, d: date) -> datetime:
        hit = self._cache.get(d)
        if hit is not None:
            return hit
        from panchang_engine.timings import compute_sunrise_sunset

        rise, _set = compute_sunrise_sunset(d, self.lat, self.lon, self.tz)
        self._cache[d] = rise
        return rise


class SolarSunrise:
    """Sunrise in UT from latitude and longitude alone; the civil date is the LOCAL SOLAR date.

    For civil date D at the birthplace, the day that starts at sunrise on D is found like this:
    local solar midnight of D is 00:00 UT of D minus longitude/15 hours; the first sunrise after
    it is accepted if its own local solar date (UT + longitude/15 h) is D. No time zone and no tz
    database is consulted (SUR-RB-6; YARDSTICK 3.1). If the Sun does not rise on D (polar day or
    night) the result is None and the day reads NOT_ASSESSED. Works at any longitude, including the
    far east and far west where the sunrise falls on a different UT date from D.
    """

    name = "swisseph.rise_trans@local-solar-date(lon/15h)"

    def __init__(self, lat: float, lon: float):
        import math

        if not (math.isfinite(lat) and math.isfinite(lon)) or abs(lat) > 90 or abs(lon) > 180:
            raise ValueError("latitude/longitude out of range")
        self.lat, self.lon = float(lat), float(lon)
        self._cache: Dict[date, Optional[datetime]] = {}

    def sunrise_utc(self, d: date) -> Optional[datetime]:
        if d in self._cache:
            return self._cache[d]
        out = self._compute(d)
        self._cache[d] = out
        return out

    def _compute(self, d: date) -> Optional[datetime]:
        import swisseph as swe
        from panchang_engine.swiss_state import serialized_swiss_state

        @serialized_swiss_state
        def rise(jd_start: float):
            return swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (self.lon, self.lat, 0.0), 1013.25, 10.0)

        jd_mid = swe.julday(d.year, d.month, d.day, 0.0) - self.lon / 360.0  # local solar midnight of D, in UT
        res = rise(jd_mid)
        if res[0] == -2:
            return None  # the Sun does not rise (circumpolar)
        jd_rise = res[1][0]
        y, m, dd, _h = swe.revjul(jd_rise + self.lon / 360.0)
        if date(int(y), int(m), int(dd)) != d:
            return None  # the first sunrise after solar midnight belongs to a later solar date: none on D
        secs = round((jd_rise - K.JD_UNIX_EPOCH) * K.SECONDS_PER_DAY)
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=secs)


@dataclass
class DayGrid:
    """Consecutive civil dates and the sunrise instant that starts each (None = the Sun does not rise that date)."""

    first: date
    n: int
    sunrise_jd: List[Optional[float]]
    sunrise_utc: List[Optional[datetime]]
    provider: str

    @property
    def no_sunrise_days(self) -> int:
        return sum(1 for j in self.sunrise_jd if j is None)

    def date_at(self, i: int) -> date:
        return self.first + timedelta(days=i)

    @property
    def last(self) -> date:
        return self.first + timedelta(days=self.n - 1)


def build_grid(first: date, last: date, provider: SunriseProvider) -> DayGrid:
    if last < first:
        raise ValueError("empty date range")
    n = (last - first).days + 1
    utcs: List[Optional[datetime]] = []
    jds: List[Optional[float]] = []
    for i in range(n):
        u = provider.sunrise_utc(first + timedelta(days=i))
        if u is None:
            utcs.append(None)
            jds.append(None)
            continue
        if u.tzinfo is None:
            raise ChartDataError("sunrise provider returned a naive datetime")
        utcs.append(u.astimezone(timezone.utc))
        jds.append(utc_to_jd(u))
    known = [j for j in jds if j is not None]
    for a, b in zip(known, known[1:]):
        if not b > a:
            raise ChartDataError("sunrise instants are not strictly increasing")
    return DayGrid(first=first, n=n, sunrise_jd=jds, sunrise_utc=utcs, provider=provider.name)


def first_day_at_or_after(provider: SunriseProvider, jd: float, search_days: int = 8) -> Optional[date]:
    """First civil date whose sunrise instant is at or after ``jd`` (None if none within ``search_days`` days).

    Used for the per-family horizon starts: the first day a family's inputs exist at the sunrise that states the day.
    """
    y, m, d, _h = _revjul(jd)
    start = date(y, m, d) - timedelta(days=2)
    for i in range(search_days + 3):
        day = start + timedelta(days=i)
        try:
            u = provider.sunrise_utc(day)
        except ChartDataError:  # a table provider that has no instant for this date (tests, oracle fixtures)
            continue
        if u is not None and utc_to_jd(u) >= jd:
            return day
    return None


def _revjul(jd: float):
    t = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd - K.JD_UNIX_EPOCH)
    return t.year, t.month, t.day, t.hour
