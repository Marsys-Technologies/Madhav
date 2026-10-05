"""The per-chart horizon of a Gochara 5 build (FINAL_BUILD_SCOPE FB-1 to FB-4; owner rulings 7 and 13).

ONE pure function is the authority for a chart's horizon: `derive_chart_horizon(birth_date, lel_events, build_date)`.

  END   = birth date + 100 years.
  START = 1 January of the year of the first FULLY DATED life-event-log event (the birth entry aside); a chart with no such
          event starts on the BUILD DATE, and the basis `build_date` is recorded with the horizon.
  Half-open `[start, end)`, UTC midnight, as everywhere in the writer.

The rule is applied HERE, to the RAW rows of `life_events`, never pre-filtered by a caller (MB-ADDITIONS 2). Literal reading, flagged for the owner:
the date of an event of ANY shape (point, interval, chain) is its `event_date` column; `interval_start` / `interval_end` and the chain links are NOT read.
There is no birth flag column in `life_events` (the birth entry is `category` other, `subcategory` birth in the markdown log only), so the birth entry is
taken as every row dated on or before the birth date. The derivation returns how many rows it excluded as the birth entry and as not fully dated.

"Fully dated" is decided from the event's own identity, never from a flag that a default could have filled: the id must read
EVT.YYYY.MM.DD.NN with real digits in the month and day places (an `XX` placeholder is a year-only or month-only event), its
`date_confidence` must be `exact` (migration 457 defaulted every legacy row to `exact`, so the flag alone cannot tell), and
the stored `event_date` must be the date the id encodes. The birth entry is any event on or before the birth date.

The pinned chart resolves to `[1998-01-01, 2084-02-05)` with basis `first_dated_event` (the first fully dated event after birth
is EVT.1998.02.16.01).

`require_inside_substrate_domain` is the FB-3 rule: a horizon must lie inside the convention's substrate domain or the build is
refused BY NAME (`horizon_outside_substrate_domain`), never clipped.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Iterable, NamedTuple

HORIZON_BASIS_SCHEMA = "gochara_horizon_basis/1"
BASIS_FIRST_DATED_EVENT = "first_dated_event"
BASIS_BUILD_DATE = "build_date"
HORIZON_YEARS = 100
_FULLY_DATED_ID = re.compile(r"^EVT\.(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})$")

# the pinned chart (CLAUDE.md section B): its birth date and the first fully dated life-event-log event after birth. The writer
# READS the log from the database at build time; these two constants exist so the pinned chart's derived horizon has a named,
# tested value (`PINNED_CHART_HORIZON`) for the slice validator's default outer bound and for the oracle tests.
PINNED_BIRTH_DATE = date(1984, 2, 5)
PINNED_FIRST_DATED_EVENT_ID = "EVT.1998.02.16.01"
PINNED_FIRST_DATED_EVENT_DATE = date(1998, 2, 16)


class HorizonDerivationRefusal(ValueError):
    """The horizon cannot be derived (never guessed): the message names the reason."""


class HorizonOutsideSubstrateDomain(HorizonDerivationRefusal):
    """FB-3: the horizon reaches outside the convention's sky-event substrate domain (`horizon_outside_substrate_domain`)."""


class HorizonStartBeforeBirth(HorizonDerivationRefusal):
    """`horizon_start_before_birth`: 1 January of the first dated event's year lies before the birth date (an event in the birth year)."""


class HorizonStartInTheFuture(HorizonDerivationRefusal):
    """`horizon_start_in_the_future`: the start lies after the build date (a dated event in the future, or a mis-dated row)."""


class LelEvent(NamedTuple):
    """The columns the derivation reads from a raw `life_events` row (`shape` is carried for the record only: see the module docstring)."""
    event_id: str
    event_date: date
    date_confidence: str
    shape: str = "point"


class ChartHorizon(NamedTuple):
    start: datetime
    end: datetime
    basis: str                      # BASIS_FIRST_DATED_EVENT | BASIS_BUILD_DATE
    first_event_id: str | None      # the event that fixed the start (None for basis build_date)
    first_event_date: date | None = None
    first_event_confidence: str | None = None
    first_event_shape: str | None = None
    build_date: date | None = None                 # the build date given to the derivation (a UTC date); the start itself when basis is build_date
    events_total: int = 0                          # raw rows read
    excluded_birth_entry: int = 0                  # rows dated on or before the birth date
    excluded_not_fully_dated: int = 0              # rows after birth that are NOT fully dated (placeholder id, flag not exact, or id/date disagreement)

    @property
    def bounds(self) -> tuple[datetime, datetime]:
        return (self.start, self.end)

    def basis_record(self) -> dict:
        """The record pinned beside the horizon in the manifest vector (MB-ADDITIONS 3): a sealed generation stays explainable from what it pinned even
        after the life-event log is revised. JSON-plain (strings, ints, null); the event is null for basis build_date."""
        first = None if self.first_event_id is None else {
            "event_id": self.first_event_id, "event_date": self.first_event_date.isoformat(),
            "date_confidence": self.first_event_confidence, "shape": self.first_event_shape}
        return {"schema": HORIZON_BASIS_SCHEMA, "kind": self.basis, "first_event": first,
                "build_date_utc": self.build_date.isoformat() if self.build_date else None,
                "horizon": [self.start.isoformat(), self.end.isoformat()],
                "counts": {"events_total": self.events_total, "excluded_birth_entry": self.excluded_birth_entry,
                           "excluded_not_fully_dated": self.excluded_not_fully_dated}}


def _utc_midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def add_years(d: date, years: int) -> date:
    """`d` plus whole years; a 29 February whose target year has no 29 February is REFUSED (an unstated choice between 28
    February and 1 March is never made for the owner)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        raise HorizonDerivationRefusal(
            f"birth date {d.isoformat()} plus {years} years has no calendar day (29 February into a non-leap year): "
            "refused, the end of the horizon is never guessed") from None


def is_fully_dated(event: LelEvent) -> bool:
    """True when the event's day is known: a real-digit id, confidence `exact`, and a stored date equal to the id's date."""
    m = _FULLY_DATED_ID.match(event.event_id or "")
    if m is None or event.date_confidence != "exact":
        return False
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) == event.event_date
    except ValueError:
        return False


def derive_chart_horizon(birth_date: date, lel_events: Iterable[LelEvent], build_date: date) -> ChartHorizon:
    """The horizon of one chart, FB-1. Pure: no clock, no database."""
    if not isinstance(birth_date, date) or isinstance(birth_date, datetime):
        raise HorizonDerivationRefusal(f"birth date {birth_date!r} is not a date — refused")
    if not isinstance(build_date, date) or isinstance(build_date, datetime):
        raise HorizonDerivationRefusal(f"build date {build_date!r} is not a date — refused")
    end = _utc_midnight(add_years(birth_date, HORIZON_YEARS))
    rows = list(lel_events)
    after_birth = [e for e in rows if e.event_date > birth_date]
    dated = sorted((e for e in after_birth if is_fully_dated(e)), key=lambda e: (e.event_date, e.event_id))
    counts = dict(events_total=len(rows), excluded_birth_entry=len(rows) - len(after_birth),
                  excluded_not_fully_dated=len(after_birth) - len(dated), build_date=build_date)
    if dated:
        first = dated[0]
        start = _utc_midnight(date(first.event_date.year, 1, 1))
        got = ChartHorizon(start, end, BASIS_FIRST_DATED_EVENT, first.event_id, first.event_date, first.date_confidence, first.shape, **counts)
    else:
        start = _utc_midnight(build_date)
        got = ChartHorizon(start, end, BASIS_BUILD_DATE, None, **counts)
    if not start < end:
        raise HorizonDerivationRefusal(
            f"the derived horizon [{start.isoformat()}, {end.isoformat()}) is empty or inverted (basis {got.basis}) — refused")
    # the START edge (MB-ADDITIONS 1): refused by name, never clipped
    if start < _utc_midnight(birth_date):
        raise HorizonStartBeforeBirth(
            f"horizon_start_before_birth: the start {start.isoformat()} (basis {got.basis}) lies before the birth date {birth_date.isoformat()} — refused")
    if start > _utc_midnight(build_date):
        raise HorizonStartInTheFuture(
            f"horizon_start_in_the_future: the start {start.isoformat()} (basis {got.basis}) lies after the build date {build_date.isoformat()} — refused")
    require_inside_substrate_domain((start, end))            # FB-3 on BOTH edges: the substrate domain start (1998-01-01) and end (2085-01-01)
    return got


def require_inside_substrate_domain(horizon: tuple[datetime, datetime]) -> tuple[datetime, datetime]:
    """FB-3: the horizon must lie inside `[SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END]`; refused by name otherwise."""
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    start, end = horizon
    if start < SUBSTRATE_DOMAIN_START or end > SUBSTRATE_DOMAIN_END:
        edge = "start" if start < SUBSTRATE_DOMAIN_START else "end"
        raise HorizonOutsideSubstrateDomain(
            f"horizon_outside_substrate_domain ({edge} edge): [{start.isoformat()}, {end.isoformat()}) is not inside the convention substrate "
            f"domain [{SUBSTRATE_DOMAIN_START.isoformat()}, {SUBSTRATE_DOMAIN_END.isoformat()}] — refused, never clipped "
            "(a longer horizon needs a new convention-domain generation)")
    return horizon


# the pinned chart's horizon, derived through the same function from the two documented inputs (not typed in); the build date is fixed so the
# value is a constant of the module, and is after the first event (so the future-start refusal cannot fire here)
PINNED_CHART_HORIZON = derive_chart_horizon(
    PINNED_BIRTH_DATE,
    [LelEvent(PINNED_FIRST_DATED_EVENT_ID, PINNED_FIRST_DATED_EVENT_DATE, "exact")],
    date(2000, 1, 1))


__all__ = ["BASIS_BUILD_DATE", "BASIS_FIRST_DATED_EVENT", "ChartHorizon", "HORIZON_BASIS_SCHEMA", "HORIZON_YEARS", "HorizonDerivationRefusal",
           "HorizonOutsideSubstrateDomain", "HorizonStartBeforeBirth", "HorizonStartInTheFuture", "LelEvent", "PINNED_BIRTH_DATE", "PINNED_CHART_HORIZON", "PINNED_FIRST_DATED_EVENT_DATE",
           "PINNED_FIRST_DATED_EVENT_ID", "add_years", "derive_chart_horizon", "is_fully_dated", "require_inside_substrate_domain"]
