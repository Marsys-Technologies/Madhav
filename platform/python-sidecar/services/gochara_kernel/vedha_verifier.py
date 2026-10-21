"""SR-OD1 C2 — the verifier's OWN derivation of the vedha overlay (plan §3.4 "Verifier side").

The window verifier used to answer `fn` for every vedha-bearing record whenever a vedha source was bound, and the sweep's
record-wide boundary list could never vouch for vedha edges, so such a record was always blank. This module replaces that
blind answer with an INDEPENDENT derivation from the stored substrate, written without any builder code (it imports nothing
from `window_sweep`, `window_store` or the writer):

  * its own SQL reads the stored P2 records of the grain (agent, house from the janma-rāśi, target sign, support intervals),
    the stored RESIDENCE contacts of the obstructors (nodes included), and the L0 `bg_transit_rules` pairs;
  * the pairs are validated by `vedha_derive.pairs_from_rows` (cited Phaladīpikā XXVI.3–8 rows only, the complete 36 + 6
    census) and each support is derived by `vedha_derive.derive_vedha` — the module whose docstring names it "also the
    INDEPENDENT re-derivation the verifier uses (no builder code)";
  * the Moon's sign (the janma-rāśi) is the caller's (L1 chart snapshot) or, absent that, the one every stored record
    implies — and every record's stored house must equal the house this sign gives its residence sign (a disagreement is
    refused, never trusted);
  * a contact stored without an end (`coverage.truncated`) is closed at the event class's completed horizon; with no
    horizon it is left out, so its absence reads as a coverage gap (`obstructor_residence_unknown`), never as inactivity.

What the overlay answers for one record (`RecordVedha`): not applicable (adverse residence or a house with no cited pair —
the factor takes no part in the product); or a step function over the record's supports with the named reason of every
undeterminable stretch, the machine-readable scope of every 1.0, and the COMPLETE list of change instants. Completeness is
computed, not asserted: the segments must tile the record's supports exactly, or the derivation raises.

Doctrine values live in `vedha_derive` and L0; nothing here decides one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from services.gochara_rules import vedha_derive as vd

#: the reason a record whose vedha value is undeterminable over EVERY instant of its supports carries (the verifier's own literal;
#: the sweep's equivalent is `window_sweep.build`'s `operand_undeterminable_over_support`, asserted equal by a test, never imported)
WHOLLY_UNKNOWN_REASON = "operand_undeterminable_over_support"

_TITLE = {"sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury", "jupiter": "Jupiter",
          "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu"}
#: obstructor bodies the contact ledger can hold (the Moon is never a stored agent — its absence is the Moon scope label)
_OBSTRUCTOR_BODIES = ("sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
_SIGN_TARGET = re.compile(r"^span:([1-9]|1[0-2])$")


class VedhaDerivationError(RuntimeError):
    """The verifier cannot derive the vedha overlay from what is stored (named, never a silent default)."""


# ── the verifier's own SQL ───────────────────────────────────────────────────────────────────────────────────────────
_PAIRS_SQL = ("SELECT graha, primary_house, vedha_house, classical_citation, rule_type"
              " FROM public.bg_transit_rules WHERE vedha_house IS NOT NULL")
_RECORDS_SQL = (
    "SELECT r.record_id::text, r.agent, r.house_from_frame, o.canonical_target, lower(s.x), upper(s.x)"
    " FROM public.ka_gochara_relationship_record r"
    " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
    " CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x)"
    " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s AND r.path_id = %s AND r.rule_version = %s"
    " AND r.admission_state = 'admitted' AND r.operator_role = 'scored' ORDER BY 1, 5")
_RESIDENCE_SQL = (
    "SELECT c.body, o.canonical_target, c.t_in, COALESCE(c.t_out, upper(cov.completed_horizon))"
    " FROM public.ka_gochara_contact c"
    " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id"
    " LEFT JOIN public.kala_gochara_coverage cov ON cov.chart_id = c.chart_id AND cov.generation = c.generation"
    "   AND cov.partition_kind = 'event_class' AND cov.partition_key = %s"
    " WHERE c.chart_id = %s AND c.generation = %s AND c.relation_kind = 'residence' AND c.body = ANY(%s)"
    " ORDER BY c.body, c.t_in")


def _rows(conn, sql: str, params) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(sql, params).fetchall()]


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat()


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


# ── the per-record answer ────────────────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Segment:
    t_in: datetime
    t_out: datetime
    state: str                 # active | inactive | unqualified
    value: float | None        # 0.0 | 1.0 | None
    reason: str | None         # the named reason an unqualified stretch carries
    scope: str | None          # `excluding_on_demand_moon_obstruction` on a 1.0 (not Mercury's)


@dataclass(frozen=True)
class RecordVedha:
    """What the verifier derived for ONE record. `applicable=False` ⇒ the factor is declared not-applicable (it takes no part in
    the product). Otherwise `segments` tile the record's supports and `complete` says the change-instant list is complete."""
    applicable: bool
    segments: tuple = ()
    complete: bool = False
    not_applicable_reason: str | None = None

    def _at(self, t: datetime):
        for seg in self.segments:
            if seg.t_in <= t < seg.t_out:
                return seg
        return None

    def value_at(self, t: datetime) -> float | None:
        seg = self._at(t)
        return None if seg is None else seg.value

    def unknown_reason_at(self, t: datetime) -> str | None:
        seg = self._at(t)
        return None if seg is None or seg.value is not None else seg.reason

    def boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        """Every change instant strictly inside (lo, hi): every segment edge (a superset of the instants where the value changes)."""
        edges = {e for seg in self.segments for e in (seg.t_in, seg.t_out)}
        return sorted(e for e in edges if lo < e < hi)

    @property
    def wholly_unknown(self) -> bool:
        return self.applicable and bool(self.segments) and all(s.value is None for s in self.segments)

    @property
    def scopes(self) -> list[str]:
        return sorted({s.scope for s in self.segments if s.scope})


class Overlay:
    """record_id -> `RecordVedha`, plus what the derivation consumed (the L0 pairs identity, the Moon sign)."""

    def __init__(self, records: dict, *, moon_sign: int | None, pairs_digest: str, census: dict,
                 open_contacts_without_horizon: int = 0):
        self._records = records
        self.moon_sign = moon_sign
        self.pairs_digest = pairs_digest
        self.census = census
        self.open_contacts_without_horizon = open_contacts_without_horizon

    def __call__(self, record_id: str) -> RecordVedha:
        try:
            return self._records[record_id]
        except KeyError:
            raise VedhaDerivationError(f"no vedha derivation for record {record_id} — it is not an admitted scored "
                                       "record of the grain the overlay was derived for") from None

    def summary(self) -> dict:
        derived = [r for r in self._records.values() if r.applicable]
        return {"records": len(self._records), "applicable": len(derived),
                "not_applicable": len(self._records) - len(derived),
                "wholly_unknown": sum(1 for r in derived if r.wholly_unknown),
                "scopes": sorted({s for r in derived for s in r.scopes}), "moon_sign": self.moon_sign,
                "pairs_digest": self.pairs_digest, "pairs_census": self.census,
                "open_contacts_without_horizon": self.open_contacts_without_horizon}


# ── loading ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def load_pairs(conn) -> "vd.VedhaPairs":
    try:
        return vd.pairs_from_rows(_rows(conn, _PAIRS_SQL, ()))
    except vd.VedhaPairsError as exc:
        raise VedhaDerivationError(f"the L0 vedha pairs cannot be established: {exc}") from exc


def load_residence(conn, *, chart_id: str, generation: str, event_class: str):
    """({Graha: [(sign, t_in, t_out, iso_in, iso_out)]}, open contacts left out for want of a horizon)."""
    out: dict[str, list] = {_TITLE[b]: [] for b in _OBSTRUCTOR_BODIES}
    skipped = 0
    for body, target, t_in, t_out in _rows(conn, _RESIDENCE_SQL,
                                           (event_class, chart_id, generation, list(_OBSTRUCTOR_BODIES))):
        m = _SIGN_TARGET.match(target)
        if m is None:
            continue                          # a non-sign residence target is not a sign residence span
        if t_out is None:
            skipped += 1                      # truncated and no horizon to close it at: absent ⇒ a coverage gap
            continue
        out[_TITLE[body]].append((int(m.group(1)), t_in, t_out, _iso(t_in), _iso(t_out)))
    return out, skipped


def _moon_sign(records: dict, supplied: int | None) -> int | None:
    """The janma-rāśi sign (1..12). Every record's stored house must be the house this sign gives its residence sign."""
    implied: set[int] = set()
    for rid, rec in records.items():
        implied.add((rec["sign"] - rec["house"]) % 12 + 1)
    if supplied is not None:
        if not (isinstance(supplied, int) and not isinstance(supplied, bool) and 1 <= supplied <= 12):
            raise VedhaDerivationError(f"moon_sign must be 1..12, got {supplied!r}")
        bad = sorted(rid for rid, rec in records.items() if vd.house_from_moon(rec["sign"], supplied) != rec["house"])
        if bad:
            raise VedhaDerivationError(
                f"the stored house of record(s) {bad[:5]} disagrees with the janma-rāśi sign {supplied} "
                f"(sign {records[bad[0]]['sign']} is house {vd.house_from_moon(records[bad[0]]['sign'], supplied)}, "
                f"stored {records[bad[0]]['house']})")
        return supplied
    if len(implied) > 1:
        raise VedhaDerivationError(f"the stored records imply different janma-rāśi signs {sorted(implied)}")
    return next(iter(implied), None)


def _tiles(segments: list, supports: list) -> bool:
    """The segments are exactly the supports, partitioned: ordered, abutting inside a support, none outside, none missing."""
    edges = sorted(supports)
    for lo, hi in edges:
        inside = sorted((s for s in segments if lo <= s.t_in and s.t_out <= hi), key=lambda s: s.t_in)
        if not inside or inside[0].t_in != lo or inside[-1].t_out != hi:
            return False
        if any(a.t_out != b.t_in for a, b in zip(inside, inside[1:])):
            return False
    covered = sum(1 for s in segments for lo, hi in edges if lo <= s.t_in and s.t_out <= hi)
    return covered == len(segments)


def derive_overlay(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str,
                   moon_sign: int | None = None) -> Overlay:
    """The vedha overlay of one grain, derived from the stored substrate (see the module docstring)."""
    pairs = load_pairs(conn)
    stored: dict[str, dict] = {}
    for rid, agent, house, target, lo, hi in _rows(conn, _RECORDS_SQL,
                                                   (chart_id, generation, event_class, path_id, rule_version)):
        rec = stored.get(rid)
        if rec is None:
            m = _SIGN_TARGET.match(target or "")
            if m is None:
                raise VedhaDerivationError(f"record {rid}: target {target!r} is not a sign residence span")
            if house is None or agent not in _TITLE:
                raise VedhaDerivationError(f"record {rid}: agent {agent!r} / house {house!r} cannot be derived from")
            rec = stored[rid] = {"agent": _TITLE[agent], "house": int(house), "sign": int(m.group(1)), "supports": []}
        rec["supports"].append((lo, hi))
    moon = _moon_sign(stored, moon_sign)
    residence, skipped = load_residence(conn, chart_id=chart_id, generation=generation, event_class=event_class)
    out: dict[str, RecordVedha] = {}
    for rid, rec in stored.items():
        segs: list[Segment] = []
        applicable = True
        for lo, hi in sorted(rec["supports"]):
            res = _slice(residence, lo, hi)
            try:
                d = vd.derive_vedha(rec["agent"], rec["house"], (_iso(lo), _iso(hi)), moon_sign=moon, residence=res,
                                    pairs=pairs)
            except vd.VedhaPairsError as exc:         # malformed / overlapping stored residence spans: a data defect
                raise VedhaDerivationError(f"record {rid}: {exc}") from exc
            if not d["applicable"]:
                applicable = False
                break
            segs += [Segment(_parse(s["t_in"]), _parse(s["t_out"]), s["state"], s["value"], s["reason"], s["scope"])
                     for s in d["segments"]]
        if not applicable:
            out[rid] = RecordVedha(applicable=False, not_applicable_reason="no_cited_vedha_pair_for_this_house")
            continue
        segs.sort(key=lambda s: s.t_in)
        supports = [(lo, hi) for lo, hi in rec["supports"]]
        if not _tiles(segs, supports):
            raise VedhaDerivationError(f"record {rid}: the derived vedha segments do not tile the record's supports")
        out[rid] = RecordVedha(applicable=True, segments=tuple(segs), complete=True)
    return Overlay(out, moon_sign=moon, pairs_digest=pairs.content_digest, census=dict(pairs.census),
                   open_contacts_without_horizon=skipped)


def _slice(residence: dict, lo: datetime, hi: datetime) -> dict:
    """The residence spans that overlap [lo, hi) — a span that merely abuts it can change neither coverage nor a hit."""
    return {g: [(s, a, b) for s, ta, tb, a, b in spans if ta < hi and tb > lo] for g, spans in residence.items()}


#: the callable the window verifier is given (record_id -> RecordVedha)
OverlayLookup = Callable[[str], RecordVedha]

__all__ = ["Overlay", "OverlayLookup", "RecordVedha", "Segment", "VedhaDerivationError", "WHOLLY_UNKNOWN_REASON",
           "derive_overlay", "load_pairs", "load_residence"]
