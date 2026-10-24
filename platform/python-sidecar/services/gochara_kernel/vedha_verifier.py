"""SR-OD1 C2 — the verifier's OWN derivation of the vedha overlay (plan §3.4 "Verifier side").

The window verifier used to answer `fn` for every vedha-bearing record whenever a vedha source was bound, and the sweep's
record-wide boundary list could never vouch for vedha edges, so such a record was always blank. This module replaces that
blind answer with an INDEPENDENT derivation from the stored substrate, written without any builder code (it imports nothing
from `window_sweep`, `window_store` or the writer):

  * its own SQL reads the stored P2 records of the grain (agent, house from the janma-rāśi, target sign, support intervals),
    the generation's pinned sky CONVENTION (ayanāṃśa, node convention) and the L0 `bg_transit_rules` pairs;
  * the obstructors' sign residence (the seven stored grahas and Rāhu/Ketu) is DERIVED AT THE INSTANT from the pinned ephemeris by this
    module's own Swiss reader and own search (SR-VEDHA-RESIDENCE-SOURCE, K12: no code shared with the builder). It used to be read from
    the stored residence contacts, which exist only for the signs some rule edge names, so 52 % of the P2 records read as unknown. The
    node model and the ayanāṃśa are the stored sky convention's (`ka_gochara_sky_convention` via the bridge — the campaign's mean node,
    Lahiri sidereal; `substrate.py`, WP1 §1.1), mapped by name to Swiss ids here; a convention this module cannot map is refused, never replaced. Residence is
    a STEP factor: every sign ingress is located to a microsecond (the contract is the R-2 1 s state floor, SR-H2-1S);
    an instant the ephemeris cannot answer (outside the pinned files) has no residence — a coverage gap, never inactivity;
  * the pairs are validated by `vedha_derive.pairs_from_rows` (cited Phaladīpikā XXVI.3–8 rows only, the complete 36 + 6
    census) and each support is derived by `vedha_derive.derive_vedha` — the module whose docstring names it "also the
    INDEPENDENT re-derivation the verifier uses (no builder code)";
  * the Moon's sign (the janma-rāśi) is the caller's (L1 chart snapshot) or, absent that, the one every stored record
    implies — and every record's stored house must equal the house this sign gives its residence sign (a disagreement is
    refused, never trusted);

What the overlay answers for one record (`RecordVedha`): not applicable (adverse residence or a house with no cited pair —
the factor takes no part in the product); or a step function over the record's supports with the named reason of every
undeterminable stretch, the machine-readable scope of every 1.0, and the COMPLETE list of change instants. Completeness is
computed, not asserted: the segments must tile the record's supports exactly, or the derivation raises.

Doctrine values live in `vedha_derive` and L0; nothing here decides one.
"""
from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

import swisseph as swe

from panchang_engine.swiss_state import ephe_path_generation, serialized_swiss_state
from services.gochara_rules import vedha_derive as vd

#: the reason a record whose vedha value is undeterminable over EVERY instant of its supports carries (the verifier's own literal;
#: the sweep's equivalent is `window_sweep.build`'s `operand_undeterminable_over_support`, asserted equal by a test, never imported)
WHOLLY_UNKNOWN_REASON = "operand_undeterminable_over_support"
#: where the obstructors' residence comes from (the verifier's own literal; the builder's equivalent is `vedha_source.RESIDENCE_SOURCE`)
RESIDENCE_SOURCE = "ephemeris_derived_at_the_instant"

_TITLE = {"sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury", "jupiter": "Jupiter",
          "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu"}
#: the obstructors whose residence is derived (the Moon is never an obstructor source — its absence is the Moon scope label)
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
#: the generation's pinned sky convention: the class' coverage row -> the legacy-convention bridge -> the sky convention (the relations the
#: `gochara_verifier` principal may read: migrations 1240 / 1378)
_CONVENTION_SQL = (
    "SELECT s.ayanamsha, s.node_convention FROM public.kala_gochara_coverage cov"
    " JOIN public.ka_gochara_convention_bridge b ON b.kala_convention_id = cov.convention_id"
    " JOIN public.ka_gochara_sky_convention s ON s.convention_id = b.sky_convention_id"
    " WHERE cov.chart_id = %s AND cov.generation = %s AND cov.partition_kind = 'event_class' AND cov.partition_key = %s")


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
    def blank_reason(self) -> str:
        """The reason a wholly-unknown record is blank under: the ONE name its unknown stretches carry (the exact set of `Segment.reason`),
        else the generic `WHOLLY_UNKNOWN_REASON` when they differ — the builder's rule, derived exactly rather than sampled."""
        named = {s.reason for s in self.segments if s.value is None}
        return named.pop() if len(named) == 1 and None not in named else WHOLLY_UNKNOWN_REASON

    @property
    def scopes(self) -> list[str]:
        return sorted({s.scope for s in self.segments if s.scope})


class Overlay:
    """record_id -> `RecordVedha`, plus what the derivation consumed (the L0 pairs identity, the Moon sign)."""

    def __init__(self, records: dict, *, moon_sign: int | None, pairs_digest: str, census: dict,
                 convention: dict | None = None, residence_unanswered_seconds: dict | None = None):
        self._records = records
        self.moon_sign = moon_sign
        self.pairs_digest = pairs_digest
        self.census = census
        self.convention = convention
        self.residence_unanswered_seconds = residence_unanswered_seconds or {}

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
                "residence_source": RESIDENCE_SOURCE, "convention": self.convention,
                "residence_unanswered_seconds": dict(sorted(self.residence_unanswered_seconds.items()))}


# ── loading ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def load_pairs(conn) -> "vd.VedhaPairs":
    try:
        return vd.pairs_from_rows(_rows(conn, _PAIRS_SQL, ()))
    except vd.VedhaPairsError as exc:
        raise VedhaDerivationError(f"the L0 vedha pairs cannot be established: {exc}") from exc


# ── the obstructors' residence, derived at the instant (this module's own Swiss reader and search) ──────────────────────
#: the names the pinned convention uses, mapped to Swiss ids. A convention outside this table is REFUSED (never replaced by a default).
_SIDEREAL_MODE = {"lahiri_chitrapaksha": swe.SIDM_LAHIRI}
_NODE_ID = {"mean": swe.MEAN_NODE}
_BODY_ID = {"Sun": swe.SUN, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
            "Saturn": swe.SATURN}
#: this module's own bound on |sidereal longitudinal speed| in degrees/day, above the Swiss maxima (Sun 1.02, Mars 0.80, Mercury 2.2,
#: Venus 1.26, Jupiter 0.25, Saturn 0.13, mean node 0.053) — a test measures the Swiss speeds against it. The search below is exact under it.
_VMAX_DPS = {"Sun": 1.2, "Mars": 1.0, "Mercury": 2.6, "Venus": 1.6, "Jupiter": 0.35, "Saturn": 0.2, "Rahu": 0.08, "Ketu": 0.08}
_RESOLUTION = timedelta(seconds=1)              # the R-2 state floor (SR-H2-1S): no step is smaller; a sign held for less is not excluded
_MICRO = timedelta(microseconds=1)
_UNIX_JD = 2440587.5


class EphemerisUnavailable(RuntimeError):
    """The pinned ephemeris cannot answer at an instant (outside its files' range, or not the Swiss backend)."""


def swiss_longitude(ephe_path: str | None, convention: dict) -> Callable:
    """`longitude_at(graha, t)` — this module's own Swiss reader: sidereal longitude in [0, 360) under the PINNED convention (`convention`:
    ayanamsha, node_convention as stored). Ketu is the mean node + 180°. The Swiss files are the ones under `ephe_path` or, absent that,
    the environment's `SE_EPHE_PATH` (the single source of truth the Swiss library itself honours); with neither it is refused."""
    path = ephe_path or os.environ.get("SE_EPHE_PATH")
    if not path:
        raise VedhaDerivationError("the obstructors' residence is derived from the ephemeris, but no ephemeris path is configured "
                                   "(pass ephe_path or set SE_EPHE_PATH)")
    if convention.get("ayanamsha") not in _SIDEREAL_MODE or convention.get("node_convention") not in _NODE_ID:
        raise VedhaDerivationError(f"the pinned sky convention {convention!r} is not one this verifier can reproduce "
                                   f"(ayanāṃśa {sorted(_SIDEREAL_MODE)}; node convention {sorted(_NODE_ID)})")
    sid_mode, node_id = _SIDEREAL_MODE[convention["ayanamsha"]], _NODE_ID[convention["node_convention"]]

    memo = threading.local()    # SR-EPHE-PATH-ONCE: this verifier's own memo — the path is set once per thread

    @serialized_swiss_state
    def longitude_at(graha: str, t: datetime) -> float:
        # `set_ephe_path` closes the library's files (≈75 µs against ≈0.24 µs for a probe): set it only when this thread has not set
        # THIS path since any caller last did (the process-wide counter moves on every set); the sidereal mode (≈0.1 µs) is set on every probe
        if getattr(memo, "state", None) != (path, ephe_path_generation()):
            before = ephe_path_generation()
            swe.set_ephe_path(path)
            memo.state = (path, before + 1) if ephe_path_generation() == before + 1 else None
        swe.set_sid_mode(sid_mode)
        ipl = node_id if graha in vd.NODES else _BODY_ID[graha]
        try:
            xx, flags = swe.calc_ut(t.timestamp() / 86400.0 + _UNIX_JD, ipl, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        except swe.Error as exc:
            raise EphemerisUnavailable(f"{graha} @ {t.isoformat()}: {exc}") from exc
        if not flags & swe.FLG_SWIEPH:
            raise EphemerisUnavailable(f"{graha} @ {t.isoformat()}: not served by the Swiss files (flags {int(flags)})")
        return (xx[0] + 180.0) % 360.0 if graha == "Ketu" else xx[0] % 360.0
    return longitude_at


def load_convention(conn, *, chart_id: str, generation: str, event_class: str) -> dict:
    """The sky convention the generation was built under, from its own stored rows (class coverage → bridge → `ka_gochara_sky_convention`)."""
    rows = _rows(conn, _CONVENTION_SQL, (chart_id, generation, event_class))
    if len(rows) != 1:
        raise VedhaDerivationError(f"the generation's pinned sky convention is not readable ({len(rows)} coverage rows for class "
                                   f"{event_class!r}) — the residence cannot be derived under an unknown node model")
    ayanamsha, node_convention = rows[0]
    return {"ayanamsha": ayanamsha, "node_convention": node_convention}


def _sign_index(lon: float) -> int:
    return int((lon % 360.0) // 30.0)


def _signs_between(longitude_at, graha: str, lo: datetime, hi: datetime) -> list[tuple[int, datetime, datetime]]:
    """[(sign 1..12, t_in, t_out)] tiling [lo, hi): a leap-frog under the speed bound — from distance d to the nearest sign edge the sign cannot
    change before d/vmax, so the next probe is that far ahead (never less than the 1 s floor); where the sign differs at the probe the
    ingress is bisected to a microsecond. The new sign owns the ingress instant (half-open)."""
    vmax = (getattr(longitude_at, "max_speed_dps", None) or _VMAX_DPS[graha]) / 86400.0      # a source may declare its own bound (a test sky); the Swiss reader's is the table
    sign = lambda t: _sign_index(longitude_at(graha, t))        # noqa: E731
    t, start, cur = lo, lo, sign(lo)
    spans: list = []
    while t < hi:
        lon = longitude_at(graha, t)
        edge = min(lon % 30.0, 30.0 - lon % 30.0)
        nxt = min(t + max(timedelta(seconds=edge / vmax), _RESOLUTION), hi)
        probe = min(nxt, hi - _MICRO)
        if probe <= t:
            break
        if sign(probe) != cur:
            a, b = t, probe                                     # sign(a) == cur, sign(b) != cur
            while b - a > _MICRO:
                m = a + (b - a) / 2
                if m in (a, b):
                    break
                a, b = (m, b) if sign(m) == cur else (a, m)
            spans.append((cur + 1, start, b))
            start, cur, t = b, sign(b), b
        elif nxt >= hi:
            break
        else:
            t = nxt
    spans.append((cur + 1, start, hi))
    return spans


def _answered(longitude_at, graha: str, t: datetime) -> bool:
    try:
        longitude_at(graha, t)
        return True
    except EphemerisUnavailable:
        return False


def _spans_where_answered(longitude_at, graha: str, lo: datetime, hi: datetime) -> list:
    """`_signs_between`, honest where the ephemeris cannot answer: that stretch has NO span (a coverage gap, never a guessed sign). The pinned
    files are one contiguous range, so an interval that fails is an answered part and an unanswered part, each end found to a microsecond;
    an interval whose ends both fail (or that fails only inside) is wholly unanswered."""
    try:
        return _signs_between(longitude_at, graha, lo, hi)
    except EphemerisUnavailable:
        pass
    last = hi - _MICRO
    first_ok, last_ok = _answered(longitude_at, graha, lo), _answered(longitude_at, graha, last)
    if first_ok == last_ok:
        return []
    ok, bad = (lo, last) if first_ok else (last, lo)
    while abs(bad - ok) > _MICRO:
        m = ok + (bad - ok) / 2
        if m in (ok, bad):
            break
        ok, bad = (m, bad) if _answered(longitude_at, graha, m) else (ok, m)
    if first_ok:                                        # answers up to `ok`; `bad` is the first microsecond it does not
        return _spans_where_answered(longitude_at, graha, lo, bad) if bad > lo else []
    return _spans_where_answered(longitude_at, graha, ok, hi) if ok < hi else []


def derive_residence(longitude_at: Callable, lo: datetime, hi: datetime) -> tuple[dict, dict]:
    """({Graha: [(sign, t_in, t_out, iso_in, iso_out)]}, {Graha: seconds of [lo, hi) the ephemeris could not answer}) for every obstructor."""
    out, unanswered = {}, {}
    for body in _OBSTRUCTOR_BODIES:
        graha = _TITLE[body]
        spans = _spans_where_answered(longitude_at, graha, lo, hi)
        out[graha] = [(sign, a, b, _iso(a), _iso(b)) for sign, a, b in spans]
        gap = (hi - lo).total_seconds() - sum((b - a).total_seconds() for _, a, b in spans)
        if gap > 1e-6:
            unanswered[graha] = round(gap, 6)
    return out, unanswered


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
                   moon_sign: int | None = None, ephe_path: str | None = None, longitude_at: Callable | None = None) -> Overlay:
    """The vedha overlay of one grain: the stored records, the L0 pairs and the obstructors' residence DERIVED from the ephemeris (see the
    module docstring). `longitude_at(graha, t)` is the position source: by default this module's own Swiss reader over `ephe_path` (or the
    environment's `SE_EPHE_PATH`) under the generation's pinned convention; a caller (a test) may supply its own."""
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
    convention = None
    residence: dict = {g: [] for g in (_TITLE[b] for b in _OBSTRUCTOR_BODIES)}
    unanswered: dict = {}
    supports_all = [s for rec in stored.values() for s in rec["supports"]]
    if supports_all:
        if longitude_at is None:
            convention = load_convention(conn, chart_id=chart_id, generation=generation, event_class=event_class)
            longitude_at = swiss_longitude(ephe_path, convention)
        residence, unanswered = derive_residence(longitude_at, min(lo for lo, _ in supports_all), max(hi for _, hi in supports_all))
    out: dict[str, RecordVedha] = {}
    for rid, rec in stored.items():
        segs: list[Segment] = []
        applicable = True
        for lo, hi in sorted(rec["supports"]):
            res = _slice(residence, lo, hi)
            try:
                d = vd.derive_vedha(rec["agent"], rec["house"], (_iso(lo), _iso(hi)), moon_sign=moon, residence=res,
                                    pairs=pairs)
            except vd.VedhaPairsError as exc:         # malformed / overlapping residence spans: a defect
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
                   convention=convention, residence_unanswered_seconds=unanswered)


def _slice(residence: dict, lo: datetime, hi: datetime) -> dict:
    """The residence spans that overlap [lo, hi) — a span that merely abuts it can change neither coverage nor a hit."""
    return {g: [(s, a, b) for s, ta, tb, a, b in spans if ta < hi and tb > lo] for g, spans in residence.items()}


#: the callable the window verifier is given (record_id -> RecordVedha)
OverlayLookup = Callable[[str], RecordVedha]

__all__ = ["EphemerisUnavailable", "Overlay", "OverlayLookup", "RESIDENCE_SOURCE", "RecordVedha", "Segment", "VedhaDerivationError",
           "WHOLLY_UNKNOWN_REASON", "derive_overlay", "derive_residence", "load_convention", "load_pairs", "swiss_longitude"]
