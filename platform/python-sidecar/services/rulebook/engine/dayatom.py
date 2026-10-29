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

    def sunrise_utc(self, d: date) -> datetime: ...


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


@dataclass
class DayGrid:
    """Consecutive civil dates and the sunrise instant that starts each."""

    first: date
    n: int
    sunrise_jd: List[float]
    sunrise_utc: List[datetime]
    provider: str

    def date_at(self, i: int) -> date:
        return self.first + timedelta(days=i)

    @property
    def last(self) -> date:
        return self.first + timedelta(days=self.n - 1)


def build_grid(first: date, last: date, provider: SunriseProvider) -> DayGrid:
    if last < first:
        raise ValueError("empty date range")
    n = (last - first).days + 1
    utcs: List[datetime] = []
    jds: List[float] = []
    for i in range(n):
        u = provider.sunrise_utc(first + timedelta(days=i))
        if u.tzinfo is None:
            raise ChartDataError("sunrise provider returned a naive datetime")
        utcs.append(u.astimezone(timezone.utc))
        jds.append(utc_to_jd(u))
    for a, b in zip(jds, jds[1:]):
        if not b > a:
            raise ChartDataError("sunrise instants are not strictly increasing")
    return DayGrid(first=first, n=n, sunrise_jd=jds, sunrise_utc=utcs, provider=provider.name)
