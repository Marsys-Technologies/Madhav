"""SR-OD1 C1 — the BUILDER's vedha operand source for P2 (plan §3.4 Part C; owner rulings VEDHA-SOURCE, ND-NODE-VEDHA,
ND-VIPAREETA in /Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl; text fast/owner-doctrine-answers/ANSWERS.md v2.1 §C).

What it answers. For ONE P2 residence record (a graha in a house from the janma-rāśi, over its stored supports) the sweep needs the
vedha factor as a STEP function of time with the COMPLETE list of its change instants, or a declaration that the factor takes no
part in the record's product. This module derives that from the stored substrate and hands it over as a `RecordOverlay`:

  * the pairs are the L0 `bg_transit_rules` rows, validated and loaded by `vedha_derive.load_pairs` (cited Phaladīpikā XXVI.3-8
    rows only, the complete 36 + 6 census) — never copied here (VEDHA-SOURCE: classical house-vedha only; the Sarvatobhadra / latta
    mechanisms are never folded in);
  * the obstructors' sign residence is DERIVED AT THE INSTANT from the pinned ephemeris (SR-VEDHA-RESIDENCE-SOURCE; before it the stored
    RESIDENCE contacts were read, and those exist only for the signs some rule edge names — nodes: 6 of 12 signs — so 52 % of the P2
    records read `obstructor_residence_unknown`). Every obstructor — the seven stored grahas and Rāhu/Ketu, which obstruct like any
    graha (ND-NODE-VEDHA (i)) — gets its sign from the sidereal longitude the writer's `position_at` returns, i.e. the campaign
    convention (`record_store.KALA_CONVENTION_VECTOR` / `convention.CONVENTION_VECTOR`: Lahiri sidereal, MEAN node — `knots.py`
    N-4a(b″); the sky ledger and every contact use the same seam, none is a constant here). Residence is a STEP factor: its
    boundaries are the sign ingresses, found by the R-2 state device (`contact_reconstruct._core` at `STATE_MIN_EXCURSION_SECONDS`
    = 1 s, SR-H2-1S) and refined to a microsecond, so the sweep and the solver see every ingress. The Moon is not an obstructor
    source (VEDHA-SOURCE Q11 a), so every 1.0 carries the machine-readable scope `excluding_on_demand_moon_obstruction`;
  * an obstructor whose longitude the ephemeris cannot answer (outside the pinned files' range) has NO residence over that stretch:
    the derivation reads it as a coverage gap — a named `obstructor_residence_unknown` / `node_residence_unknown`, never inactivity;
  * each support is derived by `vedha_derive.derive_vedha` and returned through `vedha_callback_result`, so the segments carry their
    state, value, scope and the named reason of every undeterminable stretch (`obstructor_residence_unknown`,
    `node_residence_unknown`) — the sweep passes the reason through instead of its generic `objective_unknown_over_component`;
  * not-applicable (adverse residence; a house with no cited pair; a node as the transiting body, ND-NODE-VEDHA (ii)) is declared,
    never a 1;
  * completeness is COMPUTED, not asserted: the segments must tile the record's supports exactly or the derivation raises.

`VEDHA_SOURCE` in the writer is a `VedhaSource`; `for_grain` binds it to one grain (one chart × generation × event class) and the
residence and pairs are read lazily, on the first record that needs them — a grain without a vedha-bearing record reads nothing.
Doctrine values live in `vedha_derive` and L0; nothing here decides one.
"""
from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import swisseph as swe

from services.gochara_rules import vedha_derive as vd

from .contact_reconstruct import (STATE_MIN_EXCURSION_SECONDS, VMAX_DPS, GeometryUnavailable, _cell, _core,
                                  _dist_to_cell_edge)
from .window_sweep import graha_title

_SIGN_TARGET = re.compile(r"^span:([1-9]|1[0-2])$")
#: the obstructor bodies whose residence is derived (the seven stored grahas and the nodes; the Moon is never an obstructor source, Q11 a)
_OBSTRUCTOR_BODIES = ("sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
_TITLE = {b: b.capitalize() for b in _OBSTRUCTOR_BODIES}

#: SR-OD1 D3: the owner rulings this operand stands on — the ledger ids (B.3) that the build's ruling list, the substep's notes and the
#: vedha_attenuation@1.3.0 / P2@1.3.0 registry rows all carry (`registry.VEDHA_RULINGS` is the registry's copy; a test asserts they agree)
RULINGS = {
    "VEDHA-SOURCE": "phaladeepika_xxvi_house_vedha_only_moon_on_demand_excluded_and_labelled",
    "ND-NODE-VEDHA": "nodes_obstruct_like_any_graha_transiting_nodes_carry_no_vedha_factor",
    "ND-VIPAREETA": "no_vipareeta_cancellation_in_this_version",
}

#: what "the ephemeris cannot answer" looks like from `position_at`: Swiss out of its file range (`swe.Error`), a non-Swiss backend (the
#: probe's own refusal, F-14), or the R-2 device's `GeometryUnavailable`. Anything else is a defect and propagates.
_EPHEMERIS_UNAVAILABLE = (RuntimeError, swe.Error, GeometryUnavailable)
_REFINE_TO = timedelta(microseconds=1)
#: residence is derived in fixed calendar blocks (366 days from a fixed epoch) so the work is shared by every class of one process that
#: reads the same position source (`position_at.cache_key`), whatever horizon each class has
_BLOCK = timedelta(days=366)
_BLOCK_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_BLOCK_CACHE: dict = {}


#: where the obstructors' residence comes from (SR-VEDHA-RESIDENCE-SOURCE) — carried in the summary, so a note says what the overlay stood on
RESIDENCE_SOURCE = "ephemeris_derived_at_the_instant"


class VedhaSourceError(RuntimeError):
    """The vedha overlay cannot be derived from what is stored (named, never a silent default)."""


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat()


# ── the obstructors' residence, derived at the instant ───────────────────────────────────────────────────────────────────
def _sign_spans(position_at, graha: str, lo: datetime, hi: datetime) -> list[tuple[int, datetime, datetime]]:
    """[(sign 1..12, t_in, t_out)] tiling [lo, hi): the sign `graha` is in, from `position_at`, with every ingress located by the R-2 state device
    (`contact_reconstruct._core` at the 1 s state floor) and refined to a microsecond. A change instant belongs to the NEW sign (half-open).
    Raises when `position_at` cannot answer anywhere in the interval (the caller decides what that means)."""
    cache: dict = {}

    def lon(t: datetime) -> float:
        if t not in cache:
            cache[t] = float(position_at(graha, t))
        return cache[t]
    state = lambda t: _cell(lon(t), 30.0)                       # noqa: E731
    edge = lambda t: _dist_to_cell_edge(lon(t), 30.0)           # noqa: E731

    def exact(b: datetime) -> datetime:
        a = max(lo, b - timedelta(seconds=1.001))
        if state(a) == state(b):
            return b
        base = state(a)
        while b - a > _REFINE_TO:
            m = a + (b - a) / 2
            if m == a:
                break
            if state(m) == base:
                a = m
            else:
                b = m
        return b
    spans, starts, cur = [], lo, state(lo)
    last = hi - _REFINE_TO                          # [lo, hi) is half-open: `hi` itself is never probed
    for c in (_core(state, edge, VMAX_DPS[graha.lower()], lo, last, min_excursion_seconds=STATE_MIN_EXCURSION_SECONDS) if last > lo else ()):
        c = exact(c)
        if c <= starts:
            continue
        spans.append((cur + 1, starts, c))
        starts, cur = c, state(c)
    spans.append((cur + 1, starts, hi))
    return spans


def _answers(position_at, graha: str, t: datetime) -> bool:
    try:
        position_at(graha, t)
        return True
    except _EPHEMERIS_UNAVAILABLE:
        return False


def _edge_of_answer(position_at, graha: str, ok: datetime, bad: datetime) -> tuple[datetime, datetime]:
    """(ok, bad): the neighbouring microseconds where `position_at` stops answering, between an instant that answers and one that does not."""
    while abs(bad - ok) > _REFINE_TO:
        m = ok + (bad - ok) / 2
        if m in (ok, bad):
            break
        ok, bad = (m, bad) if _answers(position_at, graha, m) else (ok, m)
    return ok, bad


def _spans_where_answered(position_at, graha: str, lo: datetime, hi: datetime) -> list[tuple[int, datetime, datetime]]:
    """`_sign_spans`, honest where the ephemeris cannot answer: the stretch it cannot answer has NO span (a coverage gap, never a guessed sign).
    The pinned Swiss files cover one contiguous range, so a failing interval is an answered part plus an unanswered part, each end found
    to a microsecond; an interval whose both ends fail (or that fails inside while both ends answer) is wholly unanswered."""
    try:
        return _sign_spans(position_at, graha, lo, hi)
    except _EPHEMERIS_UNAVAILABLE:
        pass
    last = hi - _REFINE_TO
    lo_ok, hi_ok = _answers(position_at, graha, lo), _answers(position_at, graha, last)
    if lo_ok and not hi_ok:
        _, bad = _edge_of_answer(position_at, graha, lo, last)
        return _spans_where_answered(position_at, graha, lo, bad) if bad > lo else []
    if hi_ok and not lo_ok:
        ok, _ = _edge_of_answer(position_at, graha, last, lo)
        return _spans_where_answered(position_at, graha, ok, hi) if ok < hi else []
    return []


def _join(spans: list) -> list:
    """Merge abutting spans of one sign (a block seam is not an ingress)."""
    out: list = []
    for sign, a, b in sorted(spans, key=lambda x: x[1]):
        if out and out[-1][0] == sign and out[-1][2] == a:
            out[-1] = (sign, out[-1][1], b)
        else:
            out.append((sign, a, b))
    return out


def derive_residence(position_at, graha: str, lo: datetime, hi: datetime, *, memo: dict) -> list[tuple[int, datetime, datetime]]:
    """The sign residence of `graha` over [lo, hi), clipped to it, as [(sign, t_in, t_out)] (no span where the ephemeris cannot answer).
    Derived per calendar block and memoised in `memo` (and, when the position source declares an identity `cache_key`, across grains)."""
    key = getattr(position_at, "cache_key", None)
    first = int((lo - _BLOCK_EPOCH) // _BLOCK)
    last = int((hi - _BLOCK_EPOCH - _REFINE_TO) // _BLOCK)
    spans: list = []
    for k in range(first, last + 1):
        blo = _BLOCK_EPOCH + k * _BLOCK
        slot = (key, graha, k) if key is not None else None
        store = _BLOCK_CACHE if slot is not None else memo
        slot = slot if slot is not None else (graha, k)
        if slot not in store:
            store[slot] = _spans_where_answered(position_at, graha, blo, blo + _BLOCK)
        spans += store[slot]
    return [(sign, max(a, lo), min(b, hi)) for sign, a, b in _join(spans) if a < hi and b > lo]


# ── the per-record answer ────────────────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Segment:
    t_in: datetime
    t_out: datetime
    state: str                      # active | inactive | unqualified
    value: float | None             # 0.0 | 1.0 | None
    reason: str | None              # the named reason an unqualified stretch carries
    scope: str | None               # `excluding_on_demand_moon_obstruction` on a 1.0 (not Mercury's)
    obstructors: tuple = ()         # the grahas (nodes included) that settled an `active` stretch


@dataclass(frozen=True)
class RecordOverlay:
    """What was derived for ONE record. `applicable=False` ⇒ the factor is declared not-applicable and takes no part in the
    product. Otherwise `segments` tile the record's supports and `complete` says the change-instant list is complete."""
    applicable: bool
    segments: tuple = ()
    complete: bool = False
    not_applicable_reason: str | None = None
    _starts: tuple = field(init=False, repr=False, compare=False, default=())

    def __post_init__(self):
        object.__setattr__(self, "_starts", tuple(s.t_in for s in self.segments))     # segments are ordered and disjoint (`_tiles`)

    def _at(self, t: datetime):
        i = bisect_right(self._starts, t) - 1
        return self.segments[i] if i >= 0 and t < self.segments[i].t_out else None

    def value_at(self, t: datetime) -> float | None:
        seg = self._at(t)
        return None if seg is None else seg.value

    def unknown_reason_at(self, t: datetime) -> str | None:
        seg = self._at(t)
        return None if seg is None or seg.value is not None else seg.reason

    def boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        """Every segment edge strictly inside (lo, hi) — a superset of the instants at which the value changes."""
        edges = {e for seg in self.segments for e in (seg.t_in, seg.t_out)}
        return sorted(e for e in edges if lo < e < hi)

    @property
    def scopes(self) -> list[str]:
        return sorted({s.scope for s in self.segments if s.scope})


def _tiles(segments: list, supports: list) -> bool:
    """The segments are exactly the supports, partitioned: ordered, abutting inside a support, none outside, none missing."""
    for lo, hi in supports:
        inside = sorted((s for s in segments if lo <= s.t_in and s.t_out <= hi), key=lambda s: s.t_in)
        if not inside or inside[0].t_in != lo or inside[-1].t_out != hi:
            return False
        if any(a.t_out != b.t_in for a, b in zip(inside, inside[1:])):
            return False
    return sum(1 for s in segments for lo, hi in supports if lo <= s.t_in and s.t_out <= hi) == len(segments)


# ── the grain-bound provider ─────────────────────────────────────────────────────────────────────────────────────────
class VedhaProvider:
    """The vedha overlay of one grain. The sweep reads `overlay(rec, factor_ref)`; everything else is derived lazily and memoised."""

    def __init__(self, conn, *, chart_id: str, generation: str, event_class: str, records, moon_sign: int | None = None,
                 position_at=None):
        self._conn = conn
        self._grain = (chart_id, generation, event_class)
        self._records = tuple(records)
        self._supplied_moon_sign = moon_sign
        self._position_at = position_at
        self._loaded = False
        self._pairs = None
        self._moon_sign: int | None = None
        self._residence: dict = {}
        self._unanswered: dict[str, float] = {}
        self._memo: dict = {}
        self._blocks: dict = {}

    # -- loading (lazy: a grain with no vedha-bearing record reads nothing) -------------------------------------------------
    def _load(self) -> None:
        if self._loaded:
            return
        if self._position_at is None:
            raise VedhaSourceError("the obstructors' residence is derived from the ephemeris, but no position probe (`position_at`) was bound to this grain")
        try:
            self._pairs = vd.load_pairs(self._conn.cursor())
        except vd.VedhaPairsError as exc:
            raise VedhaSourceError(f"the L0 vedha pairs cannot be established: {exc}") from exc
        self._moon_sign = self._implied_moon_sign()
        supports = [s for rec in self._records for s in rec.supports]
        envelope = (min(lo for lo, _ in supports), max(hi for _, hi in supports)) if supports else None
        self._residence = {}
        for body in _OBSTRUCTOR_BODIES:
            graha = _TITLE[body]
            spans = [] if envelope is None else derive_residence(self._position_at, graha, *envelope, memo=self._blocks)
            spans = [(a.astimezone(timezone.utc), b.astimezone(timezone.utc), sign) for sign, a, b in spans]
            spans.sort(key=lambda x: x[0])
            self._unanswered[graha] = 0.0 if envelope is None else (envelope[1] - envelope[0]).total_seconds() - sum((b - a).total_seconds() for a, b, _ in spans)
            self._residence[graha] = ([s[0] for s in spans], [s[1] for s in spans], spans)
        self._loaded = True

    def _implied_moon_sign(self) -> int:
        """The janma-rāśi sign: the one every stored P2 record's (residence sign, house from the Moon) implies; a supplied sign must agree."""
        implied: set[int] = set()
        for rec in self._records:
            m = _SIGN_TARGET.match(rec.canonical_target or "")
            if m is not None and rec.house_from_frame is not None:
                implied.add((int(m.group(1)) - int(rec.house_from_frame)) % 12 + 1)
        supplied = self._supplied_moon_sign
        if supplied is not None:
            if not (isinstance(supplied, int) and not isinstance(supplied, bool) and 1 <= supplied <= 12):
                raise VedhaSourceError(f"moon_sign must be 1..12, got {supplied!r}")
            if implied - {supplied}:
                raise VedhaSourceError(f"the stored houses imply janma-rāśi sign(s) {sorted(implied)}, not the supplied {supplied}")
            return supplied
        if len(implied) != 1:
            raise VedhaSourceError(f"the stored records imply {sorted(implied) or 'no'} janma-rāśi sign(s) — exactly one is needed")
        return next(iter(implied))

    def _slice(self, lo: datetime, hi: datetime) -> dict:
        """The residence spans overlapping [lo, hi) — a span that merely abuts it can change neither coverage nor a hit."""
        out = {}
        for graha, (ins, outs, spans) in self._residence.items():
            first, last = bisect_right(outs, lo), bisect_left(ins, hi)
            out[graha] = [(sign, _iso(a), _iso(b)) for a, b, sign in spans[first:last]]
        return out

    # -- the overlay of one record --------------------------------------------------------------------------------------
    def overlay(self, rec, factor_ref: tuple) -> RecordOverlay:
        key = (rec.record_id, tuple(factor_ref))
        if key not in self._memo:
            self._memo[key] = self._derive(rec, tuple(factor_ref))
        return self._memo[key]

    def _derive(self, rec, ref: tuple) -> RecordOverlay:
        if rec.house_from_frame is None:
            raise VedhaSourceError(f"record {rec.record_id}: a P2 record without a house from the janma-rāśi cannot be derived from")
        self._load()
        graha, house = graha_title(rec.agent), int(rec.house_from_frame)
        supports = sorted(rec.supports)
        segments: list[Segment] = []
        for lo, hi in supports:
            derived = vd.derive_vedha(graha, house, (_iso(lo), _iso(hi)), moon_sign=self._moon_sign,
                                      residence=self._slice(lo, hi), pairs=self._pairs)
            result = vd.check_callback_result(vd.vedha_callback_result(derived, factor_ref=ref), ref)
            if not result["applicable"]:
                return RecordOverlay(applicable=False, not_applicable_reason=result["results"][0]["reason"])
            segments += [Segment(datetime.fromisoformat(r["t_in"]), datetime.fromisoformat(r["t_out"]), r["state"], r["value"],
                                 r["reason"], r["scope"], tuple(r["obstructors"])) for r in result["results"]]
        segments.sort(key=lambda s: s.t_in)
        if not _tiles(segments, supports):
            raise VedhaSourceError(f"record {rec.record_id}: the derived vedha segments do not tile the record's supports")
        return RecordOverlay(applicable=True, segments=tuple(segments), complete=True)

    def summary(self) -> dict:
        """What the derivation consumed and produced so far (for the substep's notes)."""
        derived = [o for o in self._memo.values() if o.applicable]
        return {"records": len(self._memo), "applicable": len(derived), "not_applicable": len(self._memo) - len(derived),
                "scopes": sorted({s for o in derived for s in o.scopes}), "moon_sign": self._moon_sign,
                "rulings": sorted(RULINGS), "pairs_digest": None if self._pairs is None else self._pairs.content_digest,
                "residence_source": RESIDENCE_SOURCE,
                "residence_unanswered_seconds": {g: round(v, 6) for g, v in sorted(self._unanswered.items()) if v > 0}}


class VedhaSource:
    """The writer's binding (`VEDHA_SOURCE`): a source that is bound to a grain on demand."""

    def for_grain(self, conn, *, chart_id: str, generation: str, event_class: str, records,
                  moon_sign: int | None = None, position_at=None) -> VedhaProvider:
        return VedhaProvider(conn, chart_id=chart_id, generation=generation, event_class=event_class, records=records,
                             moon_sign=moon_sign, position_at=position_at)


SOURCE = VedhaSource()

__all__ = ["RESIDENCE_SOURCE", "RULINGS", "RecordOverlay", "SOURCE", "Segment", "VedhaProvider", "VedhaSource", "VedhaSourceError",
           "derive_residence"]
