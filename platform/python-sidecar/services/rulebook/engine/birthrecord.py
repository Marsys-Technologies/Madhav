"""Rule Book engine — explicit-UT-offset birth input (SUR-RB-6): foreign births without DF-04.

The L1 writers fall back silently to IST when no offset reaches them (DF-04). This module is
the engine's own entrance for births outside India. It never touches L1 and never guesses:

1. The UT offset comes ONLY from the source record (``utc_offset_minutes``, east positive).
   Missing or malformed -> the chart is REFUSED (``ChartRefused``); no default, no IST, no zone
   lookup stands in for it.
2. The stated offset is cross-checked against the pinned tz database for that place and date
   (zone from the record's ``tz_iana``, else from the coordinates). Disagreement, a local time that
   does not exist, or a place that cannot be checked -> the chart is EXCLUDED (``ChartExcluded``)
   and counted in an ``ExclusionTally`` the caller reports.
3. Local birth time minus the stated offset is the true UT of birth. Every sky computation uses it.

Plain data in, plain data out; the only imports beyond the standard library are lazy
(``zoneinfo``; ``timezonefinder`` for the coordinates-to-zone fallback).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .chart import Birth, utc_to_jd

# refusals: the record itself is unusable
OFFSET_MISSING = "OFFSET_MISSING"
OFFSET_MALFORMED = "OFFSET_MALFORMED"
RECORD_MALFORMED = "RECORD_MALFORMED"
# exclusions: the record parses but cannot be trusted
TZ_DISAGREEMENT = "TZ_DISAGREEMENT"
TZ_LOCAL_TIME_NONEXISTENT = "TZ_LOCAL_TIME_NONEXISTENT"
TZ_UNCHECKABLE = "TZ_UNCHECKABLE"
TZDB_PIN_MISMATCH = "TZDB_PIN_MISMATCH"
L1_UT_MISMATCH = "L1_UT_MISMATCH"  # raised by the guards in birthcheck, counted with the rest
L1_BIRTH_MISMATCH = "L1_BIRTH_MISMATCH"  # the stored chart row is not the record's birth

OFFSET_LIMITS_MINUTES = (-14 * 60, 14 * 60)


class BirthRecordError(ValueError):
    code = "BIRTH_RECORD_ERROR"

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class ChartRefused(BirthRecordError):
    """The source record is missing or malformed in a field the engine will not default."""


class ChartExcluded(BirthRecordError):
    """The record parses, but a check against an independent source failed; the chart is out."""


class ExclusionTally:
    """Counts of refused and excluded charts by reason (reported with the run)."""

    def __init__(self) -> None:
        self._refused: Counter = Counter()
        self._excluded: Counter = Counter()
        self.accepted = 0

    def add(self, exc: BirthRecordError) -> None:
        (self._refused if isinstance(exc, ChartRefused) else self._excluded)[exc.code] += 1

    @property
    def refused(self) -> int:
        return sum(self._refused.values())

    @property
    def excluded(self) -> int:
        return sum(self._excluded.values())

    def to_json(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "refused": self.refused,
            "excluded": self.excluded,
            "refused_by_reason": dict(sorted(self._refused.items())),
            "excluded_by_reason": dict(sorted(self._excluded.items())),
        }


@dataclass(frozen=True)
class BirthRecord:
    """A birth as the source record states it. ``utc_offset_minutes`` is east-positive."""

    local_date: date
    local_time: str  # HH:MM[:SS]
    lat: float
    lon: float
    utc_offset_minutes: int
    source_zone_code: Optional[str] = None  # as the record gives it (e.g. an abbreviation); informational
    dst_applied: Optional[bool] = None  # the record's own note, if it gives one
    dst_note: Optional[str] = None
    tz_iana: Optional[str] = None  # zone used only for the cross-check; coordinates are the fallback

    def local_naive(self) -> datetime:
        return datetime.combine(self.local_date, _parse_time(self.local_time))


def _parse_time(text: str) -> time:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", str(text).strip())
    if not m:
        raise ChartRefused(RECORD_MALFORMED, "local time must be HH:MM or HH:MM:SS")
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if h > 23 or mi > 59 or s > 59:
        raise ChartRefused(RECORD_MALFORMED, "local time out of range")
    return time(h, mi, s)


def _offset_minutes(value: Any) -> int:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ChartRefused(OFFSET_MISSING, "the source record carries no UT offset; the chart is refused, never defaulted")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ChartRefused(OFFSET_MALFORMED, f"utc_offset_minutes must be a number, got {type(value).__name__}")
    if isinstance(value, float) and (not math.isfinite(value) or value != int(value)):
        raise ChartRefused(OFFSET_MALFORMED, "utc_offset_minutes must be a whole number of minutes")
    v = int(value)
    if not OFFSET_LIMITS_MINUTES[0] <= v <= OFFSET_LIMITS_MINUTES[1]:
        raise ChartRefused(OFFSET_MALFORMED, f"utc_offset_minutes {v} outside {OFFSET_LIMITS_MINUTES}")
    return v


def parse_birth_record(rec: Mapping[str, Any]) -> BirthRecord:
    """Validate a plain record. Raises ChartRefused (never returns a defaulted offset)."""
    if not isinstance(rec, Mapping):
        raise ChartRefused(RECORD_MALFORMED, "record is not an object")
    off = _offset_minutes(rec.get("utc_offset_minutes"))
    try:
        d = date.fromisoformat(str(rec["local_date"]))
        lat, lon = float(rec["lat"]), float(rec["lon"])
        t = str(rec["local_time"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ChartRefused(RECORD_MALFORMED, f"birth fields: {exc}") from exc
    if not (math.isfinite(lat) and math.isfinite(lon)) or abs(lat) > 90 or abs(lon) > 180:
        raise ChartRefused(RECORD_MALFORMED, "latitude/longitude out of range")
    _parse_time(t)
    dst = rec.get("dst_applied")
    if dst is not None and not isinstance(dst, bool):
        raise ChartRefused(RECORD_MALFORMED, "dst_applied must be true/false/null")
    return BirthRecord(
        local_date=d,
        local_time=t,
        lat=lat,
        lon=lon,
        utc_offset_minutes=off,
        source_zone_code=(str(rec["source_zone_code"]) if rec.get("source_zone_code") is not None else None),
        dst_applied=dst,
        dst_note=(str(rec["dst_note"]) if rec.get("dst_note") is not None else None),
        tz_iana=(str(rec["tz_iana"]) if rec.get("tz_iana") else None),
    )


# zone code: a letter abbreviation (PDT, IST, ...) or a numeric tz-database abbreviation (-03, -0330, +0545); the
# code is informational only: the offset is read from the h<H>(e|w)[<MM>] part and nowhere else.
_ADB_TZ = re.compile(r"^\s*([A-Za-z]{1,8}|[+-]\d{2}(?:\d{2})?)\s+h(\d{1,2})([ew])(\d{1,2})?\s*(?:\((.*)\))?\s*$")


def record_fields_from_adb_tz_raw(tz_raw: str) -> Dict[str, Any]:
    """Fields for a record from an Astro-Databank-style ``tz_raw`` such as ``PDT h7w (is daylight saving time)``.

    ``hNw`` / ``hNeMM`` state hours (and minutes) west / east of Greenwich AS WORN at birth, so the
    stated offset already includes any daylight-saving shift. Anything else (no ``h`` offset, an
    unknown shape) is malformed and the chart is refused: the offset is never inferred from the zone
    abbreviation.
    """
    m = _ADB_TZ.match(tz_raw or "")
    if not m:
        raise ChartRefused(OFFSET_MALFORMED, "tz_raw is not '<code> h<H>(e|w)[<MM>] [(note)]'")
    code, h, ew, mm, note = m.group(1), int(m.group(2)), m.group(3), int(m.group(4) or 0), m.group(5)
    if mm > 59:
        raise ChartRefused(OFFSET_MALFORMED, "minutes out of range")
    minutes = (h * 60 + mm) * (1 if ew == "e" else -1)
    out: Dict[str, Any] = {"utc_offset_minutes": minutes, "source_zone_code": code}
    if note is not None:
        out["dst_note"] = note.strip()
        low = note.lower()
        if "is daylight saving time" in low:
            out["dst_applied"] = True
        elif "standard" in low or "not daylight" in low:
            out["dst_applied"] = False
    return out


@dataclass(frozen=True)
class ResolvedBirth:
    record: BirthRecord
    utc: datetime  # true UT of birth
    jd_ut: float
    zone_checked: str  # IANA zone the offset was checked against
    tzdb: str

    def birth(self) -> Birth:
        r = self.record
        return Birth(
            birth_date=r.local_date,
            birth_time_local=r.local_time,
            lat=r.lat,
            lon=r.lon,
            zone=r.tz_iana or self.zone_checked,
            birth_utc=self.utc,
            utc_offset_minutes=r.utc_offset_minutes,
        )


def ut_of(record: BirthRecord) -> datetime:
    """Local birth time minus the stated offset. The only conversion the engine uses on this path."""
    return (record.local_naive() - timedelta(minutes=record.utc_offset_minutes)).replace(tzinfo=timezone.utc)


def _zone_name(record: BirthRecord) -> str:
    if record.tz_iana:
        return record.tz_iana
    try:
        from timezonefinder import TimezoneFinder  # lazy: only for the coordinates-to-zone fallback

        name = TimezoneFinder().timezone_at(lat=record.lat, lng=record.lon)
    except Exception as exc:  # library missing or failing: cannot check
        raise ChartExcluded(TZ_UNCHECKABLE, f"no zone for the place and no tz_iana in the record ({type(exc).__name__})") from exc
    if not name:
        raise ChartExcluded(TZ_UNCHECKABLE, "the coordinates fall in no tz zone and the record has no tz_iana")
    return name


def tz_valid_offsets_seconds(name: str, local: datetime) -> List[int]:
    """UT offsets (seconds) the tz database allows for a LOCAL wall-clock time (two at a DST fold, none in a gap)."""
    import zoneinfo

    try:
        z = zoneinfo.ZoneInfo(name)
    except Exception as exc:
        raise ChartExcluded(TZ_UNCHECKABLE, f"zone {name!r} not in the tz database ({type(exc).__name__})") from exc
    out = set()
    for fold in (0, 1):
        aware = local.replace(tzinfo=z, fold=fold)
        off = aware.utcoffset()
        if off is None:
            continue
        back = aware.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
        if back == local:  # the wall-clock time exists under this fold
            out.add(int(off.total_seconds()))
    return sorted(out)


def resolve_birth(
    record: BirthRecord,
    *,
    tally: Optional[ExclusionTally] = None,
    expected_tzdb: Optional[str] = None,
) -> ResolvedBirth:
    """Cross-check the stated offset and return the true UT. Raises ChartExcluded on any disagreement."""
    from .dayatom import tzdb_version

    try:
        db = tzdb_version()
        if expected_tzdb is not None and db != expected_tzdb:
            raise ChartExcluded(TZDB_PIN_MISMATCH, f"tz database is {db!r}, run is pinned to {expected_tzdb!r}")
        name = _zone_name(record)
        valid = tz_valid_offsets_seconds(name, record.local_naive())
        if not valid:
            raise ChartExcluded(TZ_LOCAL_TIME_NONEXISTENT, f"{name}: this wall-clock time does not exist (DST gap)")
        if record.utc_offset_minutes * 60 not in valid:
            raise ChartExcluded(
                TZ_DISAGREEMENT,
                f"stated offset {record.utc_offset_minutes} min, tz database ({name}) allows {[v // 60 for v in valid]} min",
            )
    except BirthRecordError as exc:
        if tally is not None:
            tally.add(exc)
        raise
    utc = ut_of(record)
    if tally is not None:
        tally.accepted += 1
    return ResolvedBirth(record=record, utc=utc, jd_ut=utc_to_jd(utc), zone_checked=name, tzdb=db)


def resolve_many(
    records: Iterable[Mapping[str, Any]], *, expected_tzdb: Optional[str] = None
) -> Tuple[List[Optional[ResolvedBirth]], ExclusionTally, List[Optional[str]]]:
    """Resolve a batch; a refused or excluded record yields None and a reason code, and is counted."""
    tally = ExclusionTally()
    resolved: List[Optional[ResolvedBirth]] = []
    codes: List[Optional[str]] = []
    for rec in records:
        try:
            br = parse_birth_record(rec)
            resolved.append(resolve_birth(br, tally=tally, expected_tzdb=expected_tzdb))
            codes.append(None)
        except ChartRefused as exc:
            tally.add(exc)
            resolved.append(None)
            codes.append(exc.code)
        except ChartExcluded as exc:  # already counted inside resolve_birth
            resolved.append(None)
            codes.append(exc.code)
    return resolved, tally, codes
