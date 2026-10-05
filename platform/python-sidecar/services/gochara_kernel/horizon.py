"""The per-chart horizon of a Gochara 5 build (MEASURING_BUILD_CONTRACT MB-1; FINAL_BUILD_SCOPE FB-1 to FB-4; owner rulings 7 and 13).

AUTHORITY. For the pinned chart the owner-approved pair `RULED_HORIZON` = [1998-01-01, 2084-02-05) (Ruling 13, point 2) is the authority. The detector below is
EVIDENCE, guarded by `horizon_derivation_disagrees_with_ruling`: if the life-event log would derive anything else, the build is refused, never silently different.

THE DETECTOR (pure; no clock, no database). `derive_chart_horizon(birth_date, lel_events, build_date)`:

  END   = birth date + 100 years (`horizon_birth_anniversary_undefined` for a 29 February without an anniversary).
  START = 1 January of the year of the first FULLY DATED event that is not the birth row; with no rows, or none fully dated, the BUILD DATE (basis `build_date`).
  Half-open `[start, end)`, UTC midnight (steward OS-3).

It is applied to the RAW rows of the chart (`WHERE chart_id = <chart>`, migration 423), every row, never pre-filtered by a caller.

  * Vocabulary: `date_confidence` in {exact, month_known, year_only}, `shape` in {point, interval, chain}; anything else is refused by name
    (`lel_date_confidence_unknown`, `lel_shape_unknown`); an exact row without a date is `lel_date_missing`.
  * The BIRTH ROW is the unique row dated on the birth date whose birth word equals `birth` (steward OS-1: the stored column carrying the word is pinned from a
    read-only production read; until `LEL_BIRTH_WORD_COLUMN` is set the detector refuses `lel_birth_row_unidentifiable` for a chart that has rows).
  * FULLY DATED (steward ruling 2(c)): BOTH rules. Rule A: `date_confidence = 'exact'`. Rule B: the id reads `EVT.YYYY.MM.DD.NN` with real digits and the stored
    `event_date` equals the date the id encodes (migration 457 defaulted every legacy row to `exact`, so the flag alone cannot be trusted until the production
    read shows it is honest). A row is fully dated only if A and B both hold. Where the two rules would pick DIFFERENT first events the build is refused,
    `lel_dating_rules_disagree`, listing the rows. Both readings are pinned in the basis.
  * SHAPES. The date of an event of ANY shape is its own `event_date` (the literal reading of "the first event"). The detector also computes START under the two
    other readings, `interval_start` for intervals and the chain root's `event_date` for chains (a cycle or a missing parent is `lel_chain_unresolvable`), and
    refuses `lel_shape_reading_sensitive` if any reading gives a different START (the interval/chain reading is an open owner point).

`basis_record()` is the object pinned in the manifest vector beside the horizon (`horizon_basis/1`): the basis, the chosen event, the birth row and the column
used, EVERY consumed row (7 fields) with their digest, the counts and the readings, so a sealed generation stays explainable after the log is revised.

START-side and END-side refusals (`horizon_empty`, `horizon_start_before_birth`, `horizon_start_before_substrate_domain`, `horizon_start_in_future`,
`horizon_outside_substrate_domain`) are named, never clipped.
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
HORIZON_YEARS = 100
BIRTH_WORD = "birth"
CONFIDENCES = ("exact", "month_known", "year_only")
SHAPES = ("point", "interval", "chain")
_FULLY_DATED_ID = re.compile(r"^EVT\.(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})$")

#: Steward OS-1: the stored column that carries the birth word is pinned from a read-only production read AFTER the Suvarna release. Until then this is None and a
#: chart with rows is refused `lel_birth_row_unidentifiable`. The writer reads the column named here (one of LEL_BIRTH_WORD_COLUMNS).
LEL_BIRTH_WORD_COLUMN: str | None = None
LEL_BIRTH_WORD_COLUMNS = ("category", "event_type")

PINNED_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
PINNED_BIRTH_DATE = date(1984, 2, 5)
PINNED_FIRST_DATED_EVENT_ID = "EVT.1998.02.16.01"
#: The owner-approved horizon of the pinned chart (Ruling 13, point 2), as UTC-midnight instants: the AUTHORITY the detector is guarded against.
RULED_HORIZON = (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2084, 2, 5, tzinfo=timezone.utc))
RULED_HORIZONS = {PINNED_CHART_ID: RULED_HORIZON}


class HorizonRefusal(ValueError):
    """The horizon cannot be derived (never guessed). `code` is the refusal's NAME; the message starts with it."""
    code = "horizon_refusal"

    def __init__(self, message: str):
        super().__init__(f"{self.code}: {message}")


HorizonDerivationRefusal = HorizonRefusal            # the earlier name


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


class LelDatingRulesDisagree(HorizonRefusal):
    code = "lel_dating_rules_disagree"


class HorizonDerivationDisagreesWithRuling(HorizonRefusal):
    code = "horizon_derivation_disagrees_with_ruling"


REFUSAL_CODES = tuple(c.code for c in (
    HorizonEmpty, HorizonStartBeforeBirth, HorizonStartBeforeSubstrateDomain, HorizonStartInTheFuture, HorizonOutsideSubstrateDomain,
    HorizonBirthAnniversaryUndefined, LelBirthRowUnidentifiable, LelDateConfidenceUnknown, LelShapeUnknown, LelDateMissing, LelChainUnresolvable,
    LelShapeReadingSensitive, LelDatingRulesDisagree, HorizonDerivationDisagreesWithRuling))


class LelEvent(NamedTuple):
    """The columns the detector reads from a raw `life_events` row. `birth_word` is the value of the pinned birth-word column (None when unpinned)."""
    event_id: str
    event_date: date | None
    date_confidence: str
    shape: str = "point"
    interval_start: date | None = None
    interval_end: date | None = None
    chain_parent_event_id: str | None = None
    birth_word: str | None = None


def _iso(d) -> str | None:
    return None if d is None else d.isoformat()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class ChartHorizon(NamedTuple):
    start: datetime
    end: datetime
    basis: str                                   # BASIS_FIRST_DATED_EVENT | BASIS_BUILD_DATE
    first_event: LelEvent | None = None          # the event that fixed the start (None for basis build_date)
    birth_row: LelEvent | None = None
    birth_word_column: str | None = None
    build_date: date | None = None
    birth_date: date | None = None
    consumed_rows: tuple = ()                    # every row of the chart, as plain dicts, sorted by event_id
    excluded_not_fully_dated: int = 0
    readings: dict | None = None                 # {event_date, interval_start, chain_root} -> the START each reading gives (ISO)
    dating_rules: dict | None = None             # {flag_exact, id_digits} -> the first event each rule picks (event id or None)

    @property
    def bounds(self) -> tuple[datetime, datetime]:
        return (self.start, self.end)

    @property
    def first_event_id(self) -> str | None:
        return None if self.first_event is None else self.first_event.event_id

    @property
    def consumed_rows_digest(self) -> str:
        return hashlib.sha256(_canonical(list(self.consumed_rows)).encode("utf-8")).hexdigest()

    def basis_record(self) -> dict:
        """The record pinned in the manifest vector beside the horizon (MB-1.4), JSON-plain."""
        chosen = None if self.first_event is None else {
            "event_id": self.first_event.event_id, "event_date": _iso(self.first_event.event_date),
            "date_confidence": self.first_event.date_confidence, "shape": self.first_event.shape}
        birth = None if self.birth_row is None else {"event_id": self.birth_row.event_id, "column_used": self.birth_word_column}
        return {"schema": HORIZON_BASIS_SCHEMA, "rule": RULE_NAME, "birth_date": _iso(self.birth_date), "build_date": _iso(self.build_date),
                "basis": self.basis, "chosen": chosen, "birth_row": birth, "consumed_rows": [dict(r) for r in self.consumed_rows],
                "consumed_rows_digest": self.consumed_rows_digest, "excluded_not_fully_dated": self.excluded_not_fully_dated,
                "readings": dict(self.readings or {}), "dating_rules": dict(self.dating_rules or {}),
                "horizon": [self.start.isoformat(), self.end.isoformat()]}


def _utc_midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def add_years(d: date, years: int) -> date:
    """`d` plus whole years; a 29 February whose target year has no 29 February is REFUSED (an unstated choice between 28 February and 1 March is never made)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        raise HorizonBirthAnniversaryUndefined(
            f"birth date {d.isoformat()} plus {years} years has no calendar day (29 February into a non-leap year): the end of the horizon is never guessed") from None


def rule_flag_exact(e: LelEvent) -> bool:
    """Rule A: the row's own confidence word is `exact`."""
    return e.date_confidence == "exact"


def rule_id_digits(e: LelEvent) -> bool:
    """Rule B: the id reads EVT.YYYY.MM.DD.NN with real digits and the stored date equals the id's date."""
    m = _FULLY_DATED_ID.match(e.event_id or "")
    if m is None or e.event_date is None:
        return False
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) == e.event_date
    except ValueError:
        return False


def is_fully_dated(e: LelEvent) -> bool:
    """Fully dated = rule A AND rule B."""
    return rule_flag_exact(e) and rule_id_digits(e)


def _row_dict(e: LelEvent) -> dict:
    return {"event_id": e.event_id, "event_date": _iso(e.event_date), "date_confidence": e.date_confidence, "shape": e.shape,
            "interval_start": _iso(e.interval_start), "interval_end": _iso(e.interval_end), "chain_parent_event_id": e.chain_parent_event_id}


def _chain_root_date(e: LelEvent, by_id: dict) -> date | None:
    seen, cur = set(), e
    while cur.chain_parent_event_id:
        if cur.event_id in seen:
            raise LelChainUnresolvable(f"the chain through {e.event_id} has a cycle at {cur.event_id}")
        seen.add(cur.event_id)
        parent = by_id.get(cur.chain_parent_event_id)
        if parent is None:
            raise LelChainUnresolvable(f"{cur.event_id} names parent {cur.chain_parent_event_id!r}, which is not a row of the chart")
        cur = parent
    return cur.event_date


def _first_by(rows: list[LelEvent], date_of) -> tuple[LelEvent | None, date | None]:
    """The first FULLY dated row by the date `date_of(row)` gives, and that date (ties broken by id)."""
    pool = [(date_of(e), e.event_id, e) for e in rows if is_fully_dated(e) and date_of(e) is not None]
    if not pool:
        return None, None
    d, _i, e = min(pool, key=lambda t: (t[0], t[1]))
    return e, d


def _year_start(d: date | None) -> str | None:
    return None if d is None else date(d.year, 1, 1).isoformat()


def derive_chart_horizon(birth_date: date, lel_events: Iterable[LelEvent], build_date: date, *, birth_word_column: str | None = None,
                         ruled: tuple[datetime, datetime] | None = None) -> ChartHorizon:
    """The horizon of one chart. Pure. `birth_word_column` names the pinned column the rows' `birth_word` came from (None = unpinned). `ruled`, when given, is the
    owner-approved pair the derivation must equal (`horizon_derivation_disagrees_with_ruling`)."""
    if not isinstance(birth_date, date) or isinstance(birth_date, datetime):
        raise HorizonRefusal(f"birth date {birth_date!r} is not a date")
    if not isinstance(build_date, date) or isinstance(build_date, datetime):
        raise HorizonRefusal(f"build date {build_date!r} is not a date")
    end = _utc_midnight(add_years(birth_date, HORIZON_YEARS))
    rows = sorted(lel_events, key=lambda e: e.event_id)
    bad = [e.event_id for e in rows if e.date_confidence not in CONFIDENCES]
    if bad:
        raise LelDateConfidenceUnknown(f"rows {bad} carry a date_confidence outside {list(CONFIDENCES)}")
    bad = [e.event_id for e in rows if e.shape not in SHAPES]
    if bad:
        raise LelShapeUnknown(f"rows {bad} carry a shape outside {list(SHAPES)}")
    bad = [e.event_id for e in rows if e.date_confidence == "exact" and e.event_date is None]
    if bad:
        raise LelDateMissing(f"exact rows {bad} have no event_date")
    consumed = tuple(_row_dict(e) for e in rows)
    readings: dict = {"event_date": None, "interval_start": None, "chain_root": None}
    dating_rules: dict = {"flag_exact": None, "id_digits": None}
    birth_row = first_event = None
    excluded = 0
    if not rows:
        start, basis = _utc_midnight(build_date), BASIS_BUILD_DATE
    else:
        if birth_word_column is None:
            raise LelBirthRowUnidentifiable(f"the stored column that carries the birth word is not pinned yet (steward OS-1), so the birth row cannot be told "
                                            f"from the {len(rows)} rows of the chart")
        candidates = [e for e in rows if e.event_date == birth_date and e.birth_word == BIRTH_WORD]
        if len(candidates) != 1:
            raise LelBirthRowUnidentifiable(f"{len(candidates)} rows are dated {birth_date.isoformat()} with {birth_word_column} = {BIRTH_WORD!r}; exactly one is required")
        birth_row = candidates[0]
        others = [e for e in rows if e is not birth_row]
        by_id = {e.event_id: e for e in rows}
        # the two dating rules, each on its own (steward ruling 2(c)): they must agree on the first event
        a_first = min((e for e in others if rule_flag_exact(e) and e.event_date is not None), key=lambda e: (e.event_date, e.event_id), default=None)
        b_first = min((e for e in others if rule_id_digits(e)), key=lambda e: (e.event_date, e.event_id), default=None)
        dating_rules = {"flag_exact": None if a_first is None else a_first.event_id, "id_digits": None if b_first is None else b_first.event_id}
        if dating_rules["flag_exact"] != dating_rules["id_digits"]:
            listed = [_row_dict(r) for r in (a_first, b_first) if r is not None]
            raise LelDatingRulesDisagree(f"the flag rule (date_confidence exact) picks {dating_rules['flag_exact']!r} as the first event and the id rule "
                                         f"(EVT.YYYY.MM.DD.NN, stored date equal to the id's date) picks {dating_rules['id_digits']!r}; rows: {listed}")
        # START under the three readings of "the date of an event"
        first_event, d_literal = _first_by(others, lambda e: e.event_date)
        _e, d_interval = _first_by(others, lambda e: e.interval_start if (e.shape == "interval" and e.interval_start is not None) else e.event_date)
        _e, d_chain = _first_by(others, lambda e: _chain_root_date(e, by_id) if e.shape == "chain" else e.event_date)
        readings = {"event_date": _year_start(d_literal), "interval_start": _year_start(d_interval), "chain_root": _year_start(d_chain)}
        if len(set(readings.values())) != 1:
            raise LelShapeReadingSensitive(f"the three readings of an event's date give different starts {readings}: the owner's open point on interval and chain "
                                           "events would change the build")
        if first_event is None:
            start, basis = _utc_midnight(build_date), BASIS_BUILD_DATE
        else:
            start, basis = _utc_midnight(date(d_literal.year, 1, 1)), BASIS_FIRST_DATED_EVENT
        excluded = sum(1 for e in others if not is_fully_dated(e))
    got = ChartHorizon(start, end, basis, first_event, birth_row, birth_word_column if rows else None, build_date, birth_date, consumed, excluded,
                       readings, dating_rules)
    # the refusals, in the contract's order; never clipped
    if not start < end:
        raise HorizonEmpty(f"the derived horizon [{start.isoformat()}, {end.isoformat()}) is empty or inverted (basis {basis})")
    if start < _utc_midnight(birth_date):
        raise HorizonStartBeforeBirth(f"the start {start.isoformat()} (basis {basis}) lies before the birth date {birth_date.isoformat()}")
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    if start < SUBSTRATE_DOMAIN_START:
        raise HorizonStartBeforeSubstrateDomain(f"the start {start.isoformat()} lies before the substrate domain start {SUBSTRATE_DOMAIN_START.isoformat()}")
    if start > _utc_midnight(build_date):
        raise HorizonStartInTheFuture(f"the start {start.isoformat()} (basis {basis}) lies after the build date {build_date.isoformat()}")
    if end > SUBSTRATE_DOMAIN_END:
        raise HorizonOutsideSubstrateDomain(f"the end {end.isoformat()} lies after the substrate domain end {SUBSTRATE_DOMAIN_END.isoformat()}")
    if ruled is not None and (start, end) != tuple(ruled):
        raise HorizonDerivationDisagreesWithRuling(
            f"the life-event log derives [{start.isoformat()}, {end.isoformat()}) (basis {basis}, first event {got.first_event_id!r}) but the owner-approved "
            f"horizon is [{ruled[0].isoformat()}, {ruled[1].isoformat()})")
    return got


def require_inside_substrate_domain(horizon: tuple[datetime, datetime]) -> tuple[datetime, datetime]:
    """FB-3: a horizon must lie inside `[SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END]`; refused by name, never clipped (the start edge and the end edge are
    different refusals)."""
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    start, end = horizon
    if start < SUBSTRATE_DOMAIN_START:
        raise HorizonStartBeforeSubstrateDomain(f"[{start.isoformat()}, {end.isoformat()}) starts before the substrate domain start {SUBSTRATE_DOMAIN_START.isoformat()}")
    if end > SUBSTRATE_DOMAIN_END:
        raise HorizonOutsideSubstrateDomain(f"[{start.isoformat()}, {end.isoformat()}) ends after the substrate domain end {SUBSTRATE_DOMAIN_END.isoformat()} "
                                            "(a longer horizon needs a new convention-domain generation)")
    return horizon


def changed_row_ids(stored_rows: Iterable[dict], live_rows: Iterable[dict]) -> list[str]:
    """The event ids whose consumed row differs between a pinned basis and a live derivation (added, removed or changed): the report line a mid-build log edit
    that does NOT change the horizon produces (`horizon_basis_rows_changed`)."""
    a = {r["event_id"]: r for r in stored_rows}
    b = {r["event_id"]: r for r in live_rows}
    return sorted(i for i in set(a) | set(b) if a.get(i) != b.get(i))


__all__ = ["BASIS_BUILD_DATE", "BASIS_FIRST_DATED_EVENT", "BIRTH_WORD", "ChartHorizon", "HORIZON_BASIS_SCHEMA", "HORIZON_YEARS", "HorizonBirthAnniversaryUndefined",
           "HorizonDerivationDisagreesWithRuling", "HorizonDerivationRefusal", "HorizonEmpty", "HorizonOutsideSubstrateDomain", "HorizonRefusal",
           "HorizonStartBeforeBirth", "HorizonStartBeforeSubstrateDomain", "HorizonStartInTheFuture", "LEL_BIRTH_WORD_COLUMN", "LEL_BIRTH_WORD_COLUMNS",
           "LelBirthRowUnidentifiable", "LelChainUnresolvable", "LelDateConfidenceUnknown", "LelDateMissing", "LelDatingRulesDisagree", "LelEvent",
           "LelShapeReadingSensitive", "LelShapeUnknown", "PINNED_BIRTH_DATE", "PINNED_CHART_ID", "PINNED_FIRST_DATED_EVENT_ID", "REFUSAL_CODES", "RULED_HORIZON",
           "RULED_HORIZONS", "RULE_NAME", "add_years", "changed_row_ids", "derive_chart_horizon", "is_fully_dated", "require_inside_substrate_domain",
           "rule_flag_exact", "rule_id_digits"]
