"""Measuring scope records and the separate outcome-based measurement detector.

The field writer records ruled scope plus the chart's birth centenary, without
outcome inputs. The pure measurement detector below retains its supplied rows
for reproducible evaluation; it must not select the field writer's scope.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from typing import Iterable, NamedTuple

HORIZON_BASIS_SCHEMA = "horizon_basis/1"
RULE_NAME = "ruling7+ruling13"
BASIS_FIRST_DATED_EVENT = "first_dated_event"
BASIS_BUILD_DATE = "build_date"
BASIS_RULED_HORIZON = "ruled_horizon"
HORIZON_YEARS = 100
BIRTH_DOMAIN = "other/birth"
CONFIDENCES = ("exact", "month_known", "year_only")
SHAPES = ("point", "interval", "chain")
_FULLY_DATED_ID = re.compile(r"^EVT\.(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})$")
RULED_HORIZON = (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2084, 2, 5, tzinfo=timezone.utc))


class HorizonRefusal(ValueError):
    code = "horizon_refusal"

    def __init__(self, message):
        super().__init__(f"{self.code}: {message}")


HorizonDerivationRefusal = HorizonRefusal


class HorizonEmpty(HorizonRefusal):
    code = "horizon_empty"


class HorizonStartBeforeBirth(HorizonRefusal):
    code = "horizon_start_before_birth"


class HorizonStartBeforeSubstrateDomain(HorizonRefusal):
    code = "horizon_start_before_substrate_domain"


class HorizonStartInTheFuture(HorizonRefusal):
    code = "horizon_start_in_future"


class HorizonOutsideSubstrateDomain(HorizonRefusal):
    code = "horizon_outside_substrate_domain"


class HorizonBirthAnniversaryUndefined(HorizonRefusal):
    code = "horizon_birth_anniversary_undefined"


class LelBirthRowUnidentifiable(HorizonRefusal):
    code = "lel_birth_row_unidentifiable"


class LelDateConfidenceUnknown(HorizonRefusal):
    code = "lel_date_confidence_unknown"


class LelShapeUnknown(HorizonRefusal):
    code = "lel_shape_unknown"


class LelDateMissing(HorizonRefusal):
    code = "lel_date_missing"


class LelChainUnresolvable(HorizonRefusal):
    code = "lel_chain_unresolvable"


class LelShapeReadingSensitive(HorizonRefusal):
    code = "lel_shape_reading_sensitive"


class HorizonUnderivableLogHasNoDatedEvent(HorizonRefusal):
    code = "horizon_underivable_log_has_no_dated_event"


class HorizonDerivationDisagreesWithRuling(HorizonRefusal):
    code = "horizon_derivation_disagrees_with_ruling"


REFUSAL_CODES = tuple(cls.code for cls in (
    HorizonEmpty, HorizonStartBeforeBirth, HorizonStartBeforeSubstrateDomain,
    HorizonStartInTheFuture, HorizonOutsideSubstrateDomain, HorizonBirthAnniversaryUndefined,
    LelBirthRowUnidentifiable, LelDateConfidenceUnknown, LelShapeUnknown, LelDateMissing,
    LelChainUnresolvable, LelShapeReadingSensitive, HorizonUnderivableLogHasNoDatedEvent,
    HorizonDerivationDisagreesWithRuling))


class LelEvent(NamedTuple):
    event_id: str
    event_date: date | None
    date_confidence: str
    shape: str = "point"
    interval_start: date | None = None
    interval_end: date | None = None
    chain_parent_event_id: str | None = None
    category: str | None = None
    event_type: str | None = None
    domain: str | None = None
    provenance_lel_id: str | None = None
    provenance_subcategory: str | None = None
    date_tightened_at: str | None = None


def _iso(value):
    return None if value is None else value.isoformat()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class ChartHorizon(NamedTuple):
    start: datetime
    end: datetime
    basis: str
    first_event: LelEvent | None = None
    birth_row: LelEvent | None = None
    chart_id: str | None = None
    build_date: date | None = None
    birth_date: date | None = None
    consumed_rows: tuple = ()
    excluded_not_fully_dated: int = 0
    flag_exact_but_id_undated: tuple = ()
    rows_without_lel_id: tuple = ()
    fully_dated_readings: dict | None = None
    shape_readings: dict | None = None

    @property
    def bounds(self):
        return self.start, self.end

    @property
    def first_event_id(self):
        return None if self.first_event is None else self.first_event.event_id

    @property
    def consumed_rows_digest(self):
        return hashlib.sha256(_canonical(list(self.consumed_rows)).encode("utf-8")).hexdigest()

    def basis_record(self):
        chosen = None
        if self.first_event is not None:
            event = self.first_event
            chosen = {"event_id": event.event_id, "lel_id": event.provenance_lel_id,
                      "event_date": _iso(event.event_date), "date_confidence": event.date_confidence, "shape": event.shape}
        birth = None
        if self.birth_row is not None:
            event = self.birth_row
            birth = {"event_id": event.event_id, "lel_id": event.provenance_lel_id, "event_date": _iso(event.event_date),
                     "domain": event.domain, "provenance_subcategory": event.provenance_subcategory, "column_used": "domain"}
        return {
            "schema": HORIZON_BASIS_SCHEMA,
            "rule": "ruled_scope+birth_centenary" if self.basis == BASIS_RULED_HORIZON else RULE_NAME,
            "chart_id": self.chart_id,
            "birth_date": _iso(self.birth_date), "build_date": _iso(self.build_date),
            "horizon": [self.start.isoformat(), self.end.isoformat()], "basis": self.basis,
            "chosen": chosen, "birth_row": birth,
            "fully_dated_readings": dict(self.fully_dated_readings or {}), "shape_readings": dict(self.shape_readings or {}),
            "excluded_not_fully_dated": self.excluded_not_fully_dated,
            "flag_exact_but_id_undated": list(self.flag_exact_but_id_undated),
            "rows_without_lel_id": [dict(row) for row in self.rows_without_lel_id],
            "rows_total": len(self.consumed_rows), "consumed_rows": [dict(r) for r in self.consumed_rows],
            "consumed_rows_digest": self.consumed_rows_digest,
        }


def _utc_midnight(value):
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


def add_years(d: date, years: int):
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        raise HorizonBirthAnniversaryUndefined(f"{d} has no anniversary after {years} years") from None


def rule_flag_exact(e: LelEvent):
    return e.date_confidence == "exact"


def rule_id_digits(e: LelEvent):
    m = _FULLY_DATED_ID.match(e.provenance_lel_id or "")
    if m is None or e.event_date is None:
        return False
    try:
        return date(*(int(m.group(i)) for i in (1, 2, 3))) == e.event_date
    except ValueError:
        return False


def has_lel_id(e: LelEvent):
    return bool((e.provenance_lel_id or "").strip())


def is_fully_dated(e: LelEvent):
    return rule_flag_exact(e) and rule_id_digits(e)


def is_birth_row_candidate(e: LelEvent, birth_date: date):
    return e.event_date == birth_date and e.domain == BIRTH_DOMAIN


def _row_dict(event):
    row = dict(event._asdict())
    for key in ("event_date", "interval_start", "interval_end"):
        row[key] = _iso(row[key])
    return row


def _chain_root_date(event, by_id):
    seen = set()
    while event.chain_parent_event_id:
        if event.event_id in seen:
            raise LelChainUnresolvable(f"cycle through {event.event_id}")
        seen.add(event.event_id)
        parent = by_id.get(event.chain_parent_event_id)
        if parent is None:
            raise LelChainUnresolvable(f"missing parent {event.chain_parent_event_id}")
        event = parent
    return event.event_date


def _first_by(rows, keep, date_of):
    candidates = [(day, event.event_id, event) for event in rows if keep(event) and (day := date_of(event)) is not None]
    if not candidates:
        return None, None
    day, _, event = min(candidates, key=lambda item: item[:2])
    return event, day


def _year_start(day):
    return None if day is None else date(day.year, 1, 1).isoformat()


def derive_chart_horizon(birth_date: date, lel_events: Iterable[LelEvent], build_date: date, *, chart_id=None, ruled=None):
    for label, day in (("birth", birth_date), ("build", build_date)):
        if not isinstance(day, date) or isinstance(day, datetime):
            raise HorizonRefusal(f"{label} date {day!r} is not a date")
    end = _utc_midnight(add_years(birth_date, HORIZON_YEARS))
    rows = sorted(lel_events, key=lambda event: (event.event_date or date.min, event.event_id))
    bad = [e.event_id for e in rows if e.date_confidence not in CONFIDENCES]
    if bad:
        raise LelDateConfidenceUnknown(f"invalid date confidence on {bad}")
    bad = [e.event_id for e in rows if e.shape not in SHAPES]
    if bad:
        raise LelShapeUnknown(f"invalid shape on {bad}")
    bad = [e.event_id for e in rows if rule_flag_exact(e) and e.event_date is None]
    if bad:
        raise LelDateMissing(f"exact rows without dates: {bad}")

    birth_row = first_event = None
    excluded, undated, no_id = 0, (), ()
    readings = dict.fromkeys(("rule_F_start", "rule_I_start", "conjunction_start"))
    shape_readings = dict.fromkeys(("event_date_start", "interval_start_start", "chain_root_start"))
    start, basis = _utc_midnight(build_date), BASIS_BUILD_DATE
    if rows:
        candidates = [event for event in rows if is_birth_row_candidate(event, birth_date)]
        if len(candidates) != 1:
            raise LelBirthRowUnidentifiable(f"expected one birth row, found {len(candidates)}")
        birth_row = candidates[0]
        others = [event for event in rows if event is not birth_row]
        by_id = {event.event_id: event for event in rows}
        undated = tuple(sorted(event.event_id for event in others if rule_flag_exact(event) and has_lel_id(event) and not rule_id_digits(event)))
        no_id = tuple({"event_id": e.event_id, "event_date": _iso(e.event_date)} for e in rows if not has_lel_id(e))
        first_event, literal = _first_by(others, is_fully_dated, lambda event: event.event_date)
        readings = {
            "rule_F_start": _year_start(_first_by(others, rule_flag_exact, lambda event: event.event_date)[1]),
            "rule_I_start": _year_start(_first_by(others, rule_id_digits, lambda event: event.event_date)[1]),
            "conjunction_start": _year_start(literal),
        }
        interval = _first_by(others, is_fully_dated, lambda event: event.interval_start if event.shape == "interval" and event.interval_start is not None else event.event_date)[1]
        chain = _first_by(others, is_fully_dated, lambda event: _chain_root_date(event, by_id) if event.shape == "chain" else event.event_date)[1]
        shape_readings = {"event_date_start": _year_start(literal), "interval_start_start": _year_start(interval), "chain_root_start": _year_start(chain)}
        if len(set(shape_readings.values())) != 1:
            raise LelShapeReadingSensitive(f"conflicting start readings: {shape_readings}")
        if first_event is None:
            raise HorizonUnderivableLogHasNoDatedEvent(f"{len(rows)} rows exist but none beyond birth is fully dated")
        start, basis = _utc_midnight(date(literal.year, 1, 1)), BASIS_FIRST_DATED_EVENT
        excluded = sum(not is_fully_dated(event) for event in others)

    if not start < end:
        raise HorizonEmpty(f"empty interval [{start}, {end})")
    if start < _utc_midnight(birth_date):
        raise HorizonStartBeforeBirth(f"the start {start} precedes birth {birth_date}")
    if start > _utc_midnight(build_date):
        raise HorizonStartInTheFuture(f"the start {start} follows build {build_date}")
    require_inside_substrate_domain((start, end))
    if ruled is not None and (start, end) != tuple(ruled):
        raise HorizonDerivationDisagreesWithRuling(
            f"derived {[start.isoformat(), end.isoformat()]}, ruled {[day.isoformat() for day in ruled]}")
    return ChartHorizon(start, end, basis, first_event, birth_row, chart_id, build_date, birth_date,
                        tuple(_row_dict(event) for event in rows), excluded, undated, no_id, readings, shape_readings)


def require_inside_substrate_domain(horizon):
    from .substrate import SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END
    start, end = horizon
    if start < SUBSTRATE_DOMAIN_START:
        raise HorizonStartBeforeSubstrateDomain(f"the start {start} precedes {SUBSTRATE_DOMAIN_START}")
    if end > SUBSTRATE_DOMAIN_END:
        raise HorizonOutsideSubstrateDomain(f"the end {end} follows {SUBSTRATE_DOMAIN_END}")
    return horizon


def changed_row_ids(stored_rows, live_rows):
    before = {row["event_id"]: row for row in stored_rows}
    after = {row["event_id"]: row for row in live_rows}
    return sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
