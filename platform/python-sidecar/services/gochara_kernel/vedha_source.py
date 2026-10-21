"""SR-OD1 C1 — the BUILDER's vedha operand source for P2 (plan §3.4 Part C; owner rulings VEDHA-SOURCE, ND-NODE-VEDHA,
ND-VIPAREETA in /Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl; text fast/owner-doctrine-answers/ANSWERS.md v2.1 §C).

What it answers. For ONE P2 residence record (a graha in a house from the janma-rāśi, over its stored supports) the sweep needs the
vedha factor as a STEP function of time with the COMPLETE list of its change instants, or a declaration that the factor takes no
part in the record's product. This module derives that from the stored substrate and hands it over as a `RecordOverlay`:

  * the pairs are the L0 `bg_transit_rules` rows, validated and loaded by `vedha_derive.load_pairs` (cited Phaladīpikā XXVI.3-8
    rows only, the complete 36 + 6 census) — never copied here (VEDHA-SOURCE: classical house-vedha only; the Sarvatobhadra / latta
    mechanisms are never folded in);
  * the obstructors' residence is read from the stored RESIDENCE contacts (`ka_gochara_contact`, relation `residence`, a numbered
    sign target) of the seven stored bodies and Rāhu/Ketu: the nodes obstruct like any graha (ND-NODE-VEDHA (i)); the Moon is not a
    stored agent, so every 1.0 carries the machine-readable scope `excluding_on_demand_moon_obstruction` (VEDHA-SOURCE Q11 a);
  * a contact stored without an end (`coverage.truncated`) is closed at the completed horizon of THE EVENT CLASS being built; with
    no horizon it is left out, so its absence reads as a coverage gap (`obstructor_residence_unknown`), never as inactivity;
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
from datetime import datetime, timezone

from services.gochara_rules import vedha_derive as vd

from .window_sweep import graha_title

_SIGN_TARGET = re.compile(r"^span:([1-9]|1[0-2])$")
#: the bodies whose residence the contact ledger can hold as obstructors (the Moon is never a stored agent)
_OBSTRUCTOR_BODIES = ("sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
_TITLE = {b: b.capitalize() for b in _OBSTRUCTOR_BODIES}

_RESIDENCE_SQL = (
    "SELECT c.body, o.canonical_target, c.t_in, COALESCE(c.t_out, upper(cov.completed_horizon))"
    " FROM public.ka_gochara_contact c"
    " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id"
    " LEFT JOIN public.kala_gochara_coverage cov ON cov.chart_id = c.chart_id AND cov.generation = c.generation"
    "   AND cov.partition_kind = 'event_class' AND cov.partition_key = %s"
    " WHERE c.chart_id = %s AND c.generation = %s AND c.relation_kind = 'residence' AND c.body = ANY(%s)"
    " ORDER BY c.body, c.t_in")


class VedhaSourceError(RuntimeError):
    """The vedha overlay cannot be derived from what is stored (named, never a silent default)."""


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat()


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

    def __init__(self, conn, *, chart_id: str, generation: str, event_class: str, records, moon_sign: int | None = None):
        self._conn = conn
        self._grain = (chart_id, generation, event_class)
        self._records = tuple(records)
        self._supplied_moon_sign = moon_sign
        self._loaded = False
        self._pairs = None
        self._moon_sign: int | None = None
        self._residence: dict = {}
        self._skipped_open = 0
        self._memo: dict = {}

    # -- loading (lazy: a grain with no vedha-bearing record reads nothing) -------------------------------------------------
    def _load(self) -> None:
        if self._loaded:
            return
        try:
            self._pairs = vd.load_pairs(self._conn.cursor())
        except vd.VedhaPairsError as exc:
            raise VedhaSourceError(f"the L0 vedha pairs cannot be established: {exc}") from exc
        self._moon_sign = self._implied_moon_sign()
        chart_id, generation, event_class = self._grain
        rows = self._conn.execute(_RESIDENCE_SQL, (event_class, chart_id, generation, list(_OBSTRUCTOR_BODIES))).fetchall()
        per: dict[str, list] = {_TITLE[b]: [] for b in _OBSTRUCTOR_BODIES}
        for row in rows:
            body, target, t_in, t_out = tuple(row.values()) if isinstance(row, dict) else tuple(row)
            m = _SIGN_TARGET.match(target)
            if m is None:
                continue                          # a non-sign residence target is not a sign residence span
            if t_out is None:
                self._skipped_open += 1           # truncated and no horizon to close it at: absent ⇒ a coverage gap
                continue
            per[_TITLE[body]].append((t_in.astimezone(timezone.utc), t_out.astimezone(timezone.utc), int(m.group(1))))
        self._residence = {}
        for graha, spans in per.items():
            spans.sort(key=lambda s: s[0])
            for prev, cur in zip(spans, spans[1:]):
                if cur[0] < prev[1]:
                    raise VedhaSourceError(f"{graha}: stored residence contacts overlap ({prev[0].isoformat()}..{prev[1].isoformat()}"
                                           f" / {cur[0].isoformat()}..{cur[1].isoformat()}) — a graha is in one sign at a time")
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
                "pairs_digest": None if self._pairs is None else self._pairs.content_digest,
                "open_contacts_without_horizon": self._skipped_open}


class VedhaSource:
    """The writer's binding (`VEDHA_SOURCE`): a source that is bound to a grain on demand."""

    def for_grain(self, conn, *, chart_id: str, generation: str, event_class: str, records,
                  moon_sign: int | None = None) -> VedhaProvider:
        return VedhaProvider(conn, chart_id=chart_id, generation=generation, event_class=event_class, records=records,
                             moon_sign=moon_sign)


SOURCE = VedhaSource()

__all__ = ["RecordOverlay", "SOURCE", "Segment", "VedhaProvider", "VedhaSource", "VedhaSourceError"]
