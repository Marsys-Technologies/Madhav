"""The `near_miss` kind — BUILDER side (ND-P2-20261005 rules 1 and 2; FINAL_BUILD_SCOPE FB-24 … FB-29; migration 1308).

A NEAR-MISS is a COMPLETE, ROOTLESS point-contact stretch with POSITIVE clearance: the body enters the admission band of a ray level of a point
target, turns round at a station inside the band and leaves again WITHOUT ever reaching the ray level. `record_store.solve_point_edges` mints a
contact only around an exact root, so such a stretch has no contact; until ND-P2 a full build refused it at `verify:<class>` and a validated
test slice only reported it (the GRAZE-INTERIM of PR 3143).

ND-P2 rule 1: every such stretch belongs to the SEPARATE kind `near_miss`. ND-P2 rule 2: each opens its OWN standalone, lower-standing, UNSCORED
interval — one row of `ka_gochara_near_miss`: `standing = 'near_miss'`, `score` NULL with `score_reason = 'near_miss_unscored'`, and a geometric
PROXIMITY (never a "strength", never a weight). It is stored in its own tables with its own identity namespace and is read by NOTHING on the
scored path: no contact row, no relationship record, no evaluation window, no support union, no P4 influence, no peak, rank, candidate count or
coverage partition is derived from it. The module writes to the three near-miss tables and to no other table.

DETECTION is the builder's own, from the body's FULL-DOMAIN arc index (the same index the point-contact solve uses), never from the verifier's
reconstruction:

  * a stretch is found around the stations of the body that lie strictly inside the band of a ray level, and extended along the
    station-bounded monotone segments to the band edges;
  * it is ROOTLESS when the signed distance to the ray level keeps ONE sign at every station of the stretch and at both band edges (the pieces
    in between are monotone, so the level is not reached between them);
  * its CLEARANCE is the minimum over ALL stations of the stretch (not one reversal), refined directly on the ephemeris when a position source
    is given, and the refined value must confirm the side and the positive clearance;
  * a stationless body (Sun, Moon, mean nodes) has no stations, hence no near-miss, by construction.

UNRESOLVED is never a near-miss (FB-24): a rootless stretch whose clearance is below `MIN_CLEARANCE_DEG`, one whose ephemeris refinement
contradicts the arc index, and one that contains a station yet runs into the edge of the arc-index domain (its whole extent cannot be
established) are refused BY NAME (`NearMissUnresolved`) when they overlap the build horizon.

IDENTITY (FB-25): object = (body, relation, target, orb policy id, convention id); occurrence id = hash(object id, ordinal), the ordinal assigned
over the FULL-DOMAIN ordered near-miss set of the object (ordered by the closest instant), so a horizon or a class never renumbers.

The JUNCTION field (ND-P2 rule 1) is descriptive only: the sign ingresses and nakshatra ingresses of the transiting body and the MD/AD
boundaries falling inside [t_in, t_out), with their source identities and a completeness state per kind (missing coverage is `unknown`, never
`empty`). It admits nothing and scores nothing.

This module holds no rule-registry, enumerator or karaka knowledge and decides nothing about slow or fast bodies (ND-P2 rule 5: no blanket gate)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Sequence

from .contacts import _levels_for_relation
from .substrate import _uuid8_of, jd_to_utc

#: the layer's version (FB-28): stored with every search row; a generation with no search row has the layer OFF
LAYER_VERSION = 1
#: ND-P2 rule 2: the categorical standing of the interval a near-miss opens, and why it carries no score
STANDING = "near_miss"
SCORE_REASON = "near_miss_unscored"
#: FB-24: a rootless stretch must clear the ray level by at least this much (about 18 arcseconds) to be CERTIFIED a near-miss; below it the
#: stretch is UNRESOLVED and refused by name. The builder's own constant (the verifier keeps its own).
MIN_CLEARANCE_DEG = 5e-3
#: the closest instant is refined on the ephemeris until the bracket is this narrow (days; about 0.9 s)
CLOSEST_BRACKET_DAYS = 1e-5
_JD_UNIX_EPOCH = 2440587.5

OBJECT_TABLE = "ka_gochara_near_miss_object"
OCCURRENCE_TABLE = "ka_gochara_near_miss"
SEARCH_TABLE = "ka_gochara_near_miss_search"
TABLES = (OBJECT_TABLE, OCCURRENCE_TABLE, SEARCH_TABLE)
#: the point-contact relations a near-miss can exist for, and the kernel relation whose ray levels they use
KERNEL_RELATION = {"conjunction": "conjunction", "aspect": "drishti_contact"}
JUNCTION_SKY_KINDS = ("sign_ingress", "nakshatra_ingress")


class NearMissUnresolved(RuntimeError):
    """A rootless in-band stretch that can be established neither as a contact nor as a near-miss at the declared accuracy (FB-24). Never stored."""


class NearMissMismatch(RuntimeError):
    """A stored near-miss row or search row differs from what the same build derives again (a rebuild must REPLACE, never accrete or drift)."""


def _utc_to_jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + _JD_UNIX_EPOCH


def _iso(t: datetime) -> str:
    """UTC ISO-8601: the stored text never depends on the session's time zone."""
    return t.astimezone(timezone.utc).isoformat()


def _signed(lon: float, level: float) -> float:
    """Signed distance lon − level folded to [−180, 180)."""
    return ((float(lon) - float(level) + 180.0) % 360.0) - 180.0


# ── identity ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def orb_policy_id(orb_source: str, orb_deg: float) -> str:
    """The orb policy a near-miss object is keyed on: the orb source AND its value, so a changed orb is a NEW object, never a renumbering (FB-25)."""
    return f"{orb_source}:{float(orb_deg):.6f}"


@dataclass(frozen=True)
class NearMissObject:
    """FB-25 natural key. `body` and `relation_kind` are the stored lowercase tokens."""

    body: str
    relation_kind: str
    canonical_target: str
    orb_policy_id: str
    convention_id: str

    @property
    def identity_bytes(self) -> str:
        return f"near_miss|{self.body}|{self.relation_kind}|{self.canonical_target}|{self.orb_policy_id}|{self.convention_id}"

    @property
    def uuid(self):
        return _uuid8_of(self.identity_bytes.encode("utf-8"))


def near_miss_id(obj: NearMissObject, ordinal: int):
    """hash(object id, ordinal). The `near_miss|` prefix of the object bytes keeps the namespace disjoint from contact identities."""
    return _uuid8_of(f"{obj.uuid}|{int(ordinal)}".encode("utf-8"))


# ── detection on the arc index ──────────────────────────────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Stretch:
    """One rootless in-band stretch of one ray level, over the WHOLE arc-index domain."""

    level_deg: float                 # the ray level in [0, 360)
    t_in_jd: float
    t_out_jd: float
    t_closest_jd: float              # the station of the stretch nearest the level
    clearance_deg: float             # > 0: the distance to the level there (arc index)
    side: int                        # +1 the body stays above the level, −1 below
    station_jds: tuple[float, ...]   # every station inside the stretch
    touches_domain_edge: bool        # the stretch runs into the index's first or last knot: its whole extent is not established


def _bisect(index, jd_a: float, jd_b: float, target_u: float) -> float:
    """The instant in the monotone piece [jd_a, jd_b] at which the unwrapped longitude equals `target_u` (same scheme as the contact spans)."""
    tol = max(index.tolerance_arcsec / 3600.0, 1e-9)
    fa = index.evaluate(jd_a) - target_u
    mid = 0.5 * (jd_a + jd_b)
    for _ in range(80):
        mid = 0.5 * (jd_a + jd_b)
        fm = index.evaluate(mid) - target_u
        if abs(fm) <= tol:
            return mid
        if (fa < 0) == (fm < 0):
            jd_a, fa = mid, fm
        else:
            jd_b = mid
    return mid


def rootless_stretches(index, levels: Sequence[float], orb_deg: float) -> list[Stretch]:
    """Every rootless in-band stretch that contains at least one station, for each ray level, over the index's whole domain; ordered by the
    closest instant. A stretch in which the level is reached (a station on the other side, a band edge on the other side, or a station exactly
    on the level — a tangency has a root) is a CONTACT stretch and is not returned."""
    segs = list(index.segments)
    if not segs:
        return []
    bounds = [segs[0].start_jd] + [s.end_jd for s in segs]            # bounds[i] .. bounds[i+1] is segs[i]; interior bounds are stations
    lons = [float(index.evaluate(b)) for b in bounds]
    last = len(bounds) - 1
    orb = float(orb_deg)
    out: list[Stretch] = []
    for level in levels:
        level = float(level) % 360.0
        seen: set[int] = set()
        for i in range(1, last):
            if i in seen:
                continue
            d_i = _signed(lons[i], level)
            if not abs(d_i) < orb:
                continue
            level_u = lons[i] - d_i                                    # the unwrapped representative of the level this station is near
            f = lambda k: lons[k] - level_u                            # noqa: E731 — unwrapped signed distance of bound k
            group = [i]
            signs = set()
            touches = False
            j = i
            while True:                                                # extend to the LEFT along monotone segments
                if abs(f(j - 1)) < orb:
                    if j - 1 == 0:
                        touches, t_in = True, bounds[0]
                        break
                    j -= 1
                    group.append(j)
                    continue
                edge = orb if f(j - 1) > 0 else -orb
                signs.add(1 if edge > 0 else -1)
                t_in = _bisect(index, bounds[j - 1], bounds[j], level_u + edge)
                break
            j = i
            while True:                                                # and to the RIGHT
                if abs(f(j + 1)) < orb:
                    if j + 1 == last:
                        touches, t_out = True, bounds[last]
                        break
                    j += 1
                    group.append(j)
                    continue
                edge = orb if f(j + 1) > 0 else -orb
                signs.add(1 if edge > 0 else -1)
                t_out = _bisect(index, bounds[j], bounds[j + 1], level_u + edge)
                break
            seen.update(group)
            dists = {k: f(k) for k in group}
            if any(v == 0.0 for v in dists.values()):
                continue                                               # a station exactly on the level: a tangency has a root
            signs.update(1 if v > 0 else -1 for v in dists.values())
            if len(signs) != 1:
                continue                                               # the level is reached inside the stretch: a contact, not a near-miss
            k_min = min(sorted(group), key=lambda k: abs(dists[k]))
            out.append(Stretch(level_deg=level, t_in_jd=float(t_in), t_out_jd=float(t_out), t_closest_jd=float(bounds[k_min]),
                               clearance_deg=abs(dists[k_min]), side=next(iter(signs)),
                               station_jds=tuple(bounds[k] for k in sorted(group)), touches_domain_edge=touches))
    out.sort(key=lambda s: (s.t_closest_jd, s.t_in_jd, s.level_deg))
    return out


def refine_closest(lon_at: Callable[[float], float], level_deg: float, jd_lo: float, jd_hi: float) -> tuple[float, float, float]:
    """(jd, signed distance, bracket width in days): the instant in [jd_lo, jd_hi] at which |lon − level| is least, by golden-section search
    directly on `lon_at` (the ephemeris). The caller brackets ONE station, on either side of which the distance is monotone."""
    g = 0.6180339887498949
    a, b = float(jd_lo), float(jd_hi)
    dist = lambda jd: abs(_signed(lon_at(jd), level_deg))             # noqa: E731
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = dist(c), dist(d)
    while b - a > CLOSEST_BRACKET_DAYS:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = dist(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = dist(d)
    jd = 0.5 * (a + b)
    return jd, _signed(lon_at(jd), level_deg), b - a


@dataclass(frozen=True)
class NearMiss:
    """One certified near-miss occurrence of an object = the standalone unscored interval it opens."""

    obj: NearMissObject
    ordinal: int
    level_deg: float
    t_in: datetime                   # the WHOLE stretch, never clipped to the horizon
    t_out: datetime
    t_closest: datetime
    clearance_deg: float
    orb_deg: float
    solver_method: str
    delta_t: float | None
    precision_regime: str
    coverage: dict

    @property
    def near_miss_id(self):
        return near_miss_id(self.obj, self.ordinal)

    @property
    def proximity(self) -> float:
        """Geometric PROXIMITY = 1 − clearance/orb, in [0, 1). Descriptive; it is not a strength, a weight or a score."""
        return 1.0 - self.clearance_deg / self.orb_deg


def solve_object_near_misses(*, obj: NearMissObject, index, orb_deg: float, horizon: tuple[datetime, datetime],
                             position_at: Callable[[str, datetime], float] | None = None) -> list[NearMiss]:
    """The certified near-misses of one object whose stretch overlaps the half-open `horizon`, with FULL-DOMAIN ordinals.

    `index` is the body's arc index over the full convention domain. `position_at(body, t)` (the ephemeris) refines the closest instant and
    must confirm the side and the positive clearance; without it the arc-index values are stored and the method says so. Raises
    `NearMissUnresolved` for a stretch overlapping the horizon that cannot be certified."""
    kind, _, arg = obj.canonical_target.partition(":")
    if kind != "point" or obj.relation_kind not in KERNEL_RELATION:
        return []
    levels = [lv for _a, lv in _levels_for_relation(obj.body.title(), KERNEL_RELATION[obj.relation_kind], float(arg))]
    stretches = rootless_stretches(index, levels, orb_deg)
    h0, h1 = _utc_to_jd(horizon[0]), _utc_to_jd(horizon[1])
    label = f"{obj.body} {obj.relation_kind} {obj.canonical_target}"
    placed = [s for s in stretches if not s.touches_domain_edge]
    out: list[NearMiss] = []
    for s in stretches:
        if s.t_out_jd <= h0 or s.t_in_jd >= h1:
            continue
        span = f"[{jd_to_utc(s.t_in_jd).isoformat()}, {jd_to_utc(s.t_out_jd).isoformat()})"
        if s.touches_domain_edge:
            raise NearMissUnresolved(
                f"near_miss_unresolved_domain_edge: {label} level {s.level_deg:.4f}: the rootless in-band stretch {span} turns at a station and "
                "runs into the edge of the arc-index domain — its whole extent cannot be established, so it is neither a contact nor a near-miss")
        if s.clearance_deg < MIN_CLEARANCE_DEG:
            raise NearMissUnresolved(
                f"near_miss_unresolved_clearance: {label} level {s.level_deg:.4f}: the rootless in-band stretch {span} clears the ray level by "
                f"{s.clearance_deg:.6f} deg, below the certified minimum {MIN_CLEARANCE_DEG} — neither a contact nor a near-miss")
        t_closest_jd, clearance = s.t_closest_jd, s.clearance_deg
        method, delta_t = "arc_index_extremum", None
        regime = f"arc_index_extremum_{index.tolerance_arcsec}arcsec"
        coverage: dict = {"arc_index_clearance_deg": round(s.clearance_deg, 9), "stations": len(s.station_jds), "side": s.side}
        if position_at is not None:
            # the bracket holds ONE station: half-way to the neighbouring stations of the stretch, else to the stretch's own ends
            k = s.station_jds.index(s.t_closest_jd)
            lo = 0.5 * (s.station_jds[k - 1] + s.t_closest_jd) if k > 0 else s.t_in_jd
            hi = 0.5 * (s.station_jds[k + 1] + s.t_closest_jd) if k + 1 < len(s.station_jds) else s.t_out_jd
            jd, signed, width = refine_closest(lambda j: position_at(obj.body, jd_to_utc(j)), s.level_deg, lo, hi)
            if signed == 0.0 or (signed > 0) != (s.side > 0) or abs(signed) < MIN_CLEARANCE_DEG:
                raise NearMissUnresolved(
                    f"near_miss_unresolved_refinement: {label} level {s.level_deg:.4f}: the ephemeris puts the closest approach of {span} at "
                    f"{signed:.6f} deg (arc index {s.side * s.clearance_deg:.6f}) — the side or the certified minimum {MIN_CLEARANCE_DEG} is not "
                    "confirmed, so the stretch is neither a contact nor a near-miss")
            t_closest_jd, clearance = jd, abs(signed)
            method, delta_t, regime = "swiss_refined_extremum", width, f"swiss_golden_section_tol_{CLOSEST_BRACKET_DAYS:g}d"
        if not clearance < orb_deg:
            raise NearMissUnresolved(f"near_miss_unresolved_clearance: {label}: clearance {clearance} is not inside the orb {orb_deg}")
        clipped = [name for name, hit in (("start", s.t_in_jd < h0), ("end", s.t_out_jd > h1)) if hit]
        if clipped:
            coverage["clipped_by_horizon"] = clipped
            coverage["horizon_interval"] = [jd_to_utc(max(s.t_in_jd, h0)).isoformat(), jd_to_utc(min(s.t_out_jd, h1)).isoformat()]
        out.append(NearMiss(
            obj=obj, ordinal=placed.index(s) + 1, level_deg=s.level_deg, t_in=jd_to_utc(s.t_in_jd), t_out=jd_to_utc(s.t_out_jd),
            t_closest=jd_to_utc(t_closest_jd), clearance_deg=float(clearance), orb_deg=float(orb_deg), solver_method=method,
            delta_t=delta_t, precision_regime=regime, coverage=coverage))
    return out


# ── the junction field (descriptive; ND-P2 rule 1) ──────────────────────────────────────────────────────────────────────────────────

def dasha_junctions(rows, t_in: datetime, t_out: datetime, horizon: tuple[datetime, datetime]) -> dict:
    """The MD/AD boundaries inside [t_in, t_out) among the snapshot's consumed daśā rows (`inventory.DashaRow`: row_id, level, start, end).

    `state` is 'complete' only when the stretch lies inside the build horizon (the snapshot consumes exactly the rows overlapping it) AND the
    MD rows and the AD rows each cover [t_in, t_out) without a gap; otherwise 'unknown' — the boundaries found are still listed, but an empty
    list then means NOT KNOWN, never none."""
    events: list[dict] = []
    covered = horizon[0] <= t_in and t_out <= horizon[1]
    for level in (1, 2):
        mine = sorted((r for r in rows if int(r.level) == level), key=lambda r: r.start)
        cursor = t_in
        for r in mine:
            if r.start <= cursor < r.end:
                cursor = r.end
        if cursor < t_out:
            covered = False
        seen: set = set()
        for r in mine:
            for instant, edge in ((r.start, "start"), (r.end, "end")):
                if t_in <= instant < t_out and instant not in seen:      # a boundary AT t_in is inside, AT t_out is not
                    seen.add(instant)
                    events.append({"level": "MD" if level == 1 else "AD", "t": _iso(instant), "dasha_row_id": str(r.row_id),
                                   "row_edge": edge})
    events.sort(key=lambda e: (e["t"], e["level"]))
    return {"state": "complete" if covered else "unknown", "events": events}


# ── storage ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

_ROW_COLUMNS = ("near_miss_id", "near_miss_object_id", "ordinal", "level_deg", "t_in", "t_out", "t_closest", "closest_state", "clearance_deg",
                "orb_deg", "proximity", "standing", "score", "score_reason", "junction", "junction_complete", "coverage", "solver_method",
                "delta_t", "precision_regime")


def _row(r):
    return tuple(r.values()) if isinstance(r, dict) else tuple(r)


def _json(v):
    return v if isinstance(v, (dict, list)) else json.loads(v)


class NearMissStore:
    """Reads and writes the three near-miss tables of migration 1308 on the caller's connection (never commits, never closes it)."""

    def __init__(self, conn):
        self.conn = conn

    def layer_present(self) -> bool:
        """Is the near-miss storage (migration 1308) applied? Read from the catalog, never assumed. Absent = the layer is OFF: nothing is
        stored and a full build keeps its pre-ND-P2 behaviour (a graze is refused at verify)."""
        row = self.conn.execute(
            "SELECT " + " AND ".join(f"to_regclass('public.{t}') IS NOT NULL" for t in TABLES)).fetchone()
        return row is not None and bool(_row(row)[0])          # no answer is not a yes: the layer is OFF

    def delete_generation(self, *, chart_id: str, generation: str) -> dict[str, int]:
        """The chart × generation REPLACE: every near-miss row and every search row of the generation goes (objects are global and
        insert-only, like physical objects). The caller has already refused a sealed generation and a non-candidate manifest
        (`RecordStore.delete_generation_chain` runs first); the tables' own guards refuse a sealed generation again."""
        out = {}
        for key, table in (("near_misses", OCCURRENCE_TABLE), ("searches", SEARCH_TABLE)):
            cur = self.conn.execute(f"DELETE FROM public.{table} WHERE chart_id = %s AND generation = %s", (chart_id, generation))
            out[key] = int(cur.rowcount or 0)
        return out

    def junction(self, *, obj: NearMissObject, t_in: datetime, t_out: datetime, horizon, dasha_rows) -> tuple[dict, bool]:
        """(junction, junction_complete) of one stretch on the CURRENT pinned sky convention and the snapshot's consumed daśā rows."""
        dom = self.conn.execute("SELECT domain_start, domain_end FROM public.ka_gochara_sky_convention WHERE convention_id = %s",
                                (obj.convention_id,)).fetchone()
        in_domain = dom is not None and _row(dom)[0] <= t_in and t_out <= _row(dom)[1]
        out: dict = {"interval_rule": "[t_in, t_out)", "sky_convention_id": obj.convention_id}
        for kind in JUNCTION_SKY_KINDS:
            built, truncated = _row(self.conn.execute(
                "SELECT count(*), count(*) FILTER (WHERE t_exact IS NULL) FROM public.ka_gochara_sky_event"
                " WHERE convention_id = %s AND body = %s AND event_kind = %s", (obj.convention_id, obj.body, kind)).fetchone())
            events = [{"t": _iso(r[1]), "event_id": str(r[0])} for r in map(_row, self.conn.execute(
                "SELECT e.event_id, e.t_exact FROM public.ka_gochara_sky_event e"
                " WHERE e.convention_id = %s AND e.body = %s AND e.event_kind = %s AND e.t_exact >= %s AND e.t_exact < %s"
                "   AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_sky_event n WHERE n.supersedes_event_id = e.event_id)"
                " ORDER BY e.t_exact, e.event_id", (obj.convention_id, obj.body, kind, t_in, t_out)).fetchall())]
            complete = bool(in_domain and built and not truncated)
            out[kind] = {"state": "complete" if complete else "unknown", "events": events}
        out["dasha_boundary"] = dasha_junctions(dasha_rows, t_in, t_out, horizon)
        parts = [out[k] for k in (*JUNCTION_SKY_KINDS, "dasha_boundary")]
        complete = all(p["state"] == "complete" for p in parts)
        found = any(p["events"] for p in parts)
        out["contains_junction"] = True if found else (False if complete else None)       # None = not known, never "none"
        return out, complete

    def _ensure_object(self, obj: NearMissObject) -> None:
        self.conn.execute(
            f"INSERT INTO public.{OBJECT_TABLE} (near_miss_object_id, body, relation_kind, canonical_target, orb_policy_id, convention_id)"
            " VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (obj.uuid, obj.body, obj.relation_kind, obj.canonical_target, obj.orb_policy_id, obj.convention_id))
        got = self.conn.execute(
            f"SELECT body, relation_kind, canonical_target, orb_policy_id, convention_id FROM public.{OBJECT_TABLE}"
            " WHERE near_miss_object_id = %s", (obj.uuid,)).fetchone()
        want = (obj.body, obj.relation_kind, obj.canonical_target, obj.orb_policy_id, obj.convention_id)
        if got is None or _row(got) != want:
            raise NearMissMismatch(f"near-miss object {obj.uuid}: stored {got and _row(got)} != derived {want} (identity collision)")

    def _params(self, chart_id, generation, nm: NearMiss, junction: dict, junction_complete: bool) -> tuple:
        return (chart_id, generation, nm.near_miss_id, nm.obj.uuid, nm.ordinal, nm.level_deg, nm.t_in, nm.t_out, nm.t_closest, "placed",
                nm.clearance_deg, nm.orb_deg, nm.proximity, STANDING, None, SCORE_REASON, json.dumps(junction, sort_keys=True),
                junction_complete, json.dumps(nm.coverage, sort_keys=True), nm.solver_method, nm.delta_t, nm.precision_regime)

    def stored_object_rows(self, *, chart_id: str, generation: str, obj: NearMissObject) -> list[tuple]:
        return [_row(r) for r in self.conn.execute(
            f"SELECT near_miss_id, ordinal, t_in, t_out, t_closest, clearance_deg FROM public.{OCCURRENCE_TABLE}"
            " WHERE chart_id = %s AND generation = %s AND near_miss_object_id = %s ORDER BY ordinal",
            (chart_id, generation, obj.uuid)).fetchall()]

    def write_object(self, *, chart_id: str, generation: str, obj: NearMissObject, horizon: tuple[datetime, datetime],
                     near_misses: Sequence[NearMiss], dasha_rows) -> dict[str, int]:
        """Store one object's search result for the generation: its near-miss rows (each the standalone unscored interval it opens) and ONE
        search row, so an object with no near-miss is a VERIFIED-EMPTY result (FB-28), not an absent one.

        Several classes share an object. The first writer of the generation inserts; a later one finds the search row and must derive the
        SAME rows (ids, ordinals, bounds, clearance) — a difference raises `NearMissMismatch`; nothing is updated in place and nothing is
        added twice. The generation's rows are removed only by `delete_generation` (the snapshot substep's replace)."""
        have = self.conn.execute(
            f"SELECT lower(horizon), upper(horizon), near_miss_count FROM public.{SEARCH_TABLE}"
            " WHERE chart_id = %s AND generation = %s AND near_miss_object_id = %s", (chart_id, generation, obj.uuid)).fetchone()
        derived = [(nm.near_miss_id, nm.ordinal, nm.t_in, nm.t_out, nm.t_closest, nm.clearance_deg) for nm in near_misses]
        if have is not None:
            stored = self.stored_object_rows(chart_id=chart_id, generation=generation, obj=obj)
            same = (_row(have) == (horizon[0], horizon[1], len(near_misses)) and len(stored) == len(derived)
                    and all(str(s[0]) == str(d[0]) and tuple(s[1:5]) == tuple(d[1:5]) and float(s[5]) == float(d[5])
                            for s, d in zip(stored, derived)))
            if not same:
                raise NearMissMismatch(
                    f"near-miss search of {obj.body} {obj.relation_kind} {obj.canonical_target} is already stored for (chart {chart_id}, "
                    f"generation {generation}) with different content (stored search {_row(have)}, {len(stored)} row(s); derived horizon "
                    f"{horizon[0].isoformat()} to {horizon[1].isoformat()}, {len(derived)} row(s)) — one object has one near-miss set per generation")
            return {"near_misses": 0, "searches": 0, "reused": 1}
        self._ensure_object(obj)
        cols = "chart_id, generation, " + ", ".join(_ROW_COLUMNS)
        for nm in near_misses:
            junction, complete = self.junction(obj=obj, t_in=nm.t_in, t_out=nm.t_out, horizon=horizon, dasha_rows=dasha_rows)
            self.conn.execute(
                f"INSERT INTO public.{OCCURRENCE_TABLE} ({cols}) VALUES ({', '.join(['%s'] * (len(_ROW_COLUMNS) + 2))})",
                self._params(chart_id, generation, nm, junction, complete))
        self.conn.execute(
            f"INSERT INTO public.{SEARCH_TABLE} (chart_id, generation, near_miss_object_id, layer_version, searched_complete, horizon,"
            " near_miss_count) VALUES (%s, %s, %s, %s, true, tstzrange(%s, %s, '[)'), %s)",
            (chart_id, generation, obj.uuid, LAYER_VERSION, horizon[0], horizon[1], len(near_misses)))
        return {"near_misses": len(near_misses), "searches": 1, "reused": 0}

    def stored_for_keys(self, *, chart_id: str, generation: str, keys) -> list[dict]:
        """The generation's near-miss rows of the objects named by `keys` = {(body, relation, canonical target)}."""
        rows = self.conn.execute(
            f"SELECT o.body, o.relation_kind, o.canonical_target, n.near_miss_id, n.t_in, n.t_out, n.clearance_deg"
            f" FROM public.{OCCURRENCE_TABLE} n JOIN public.{OBJECT_TABLE} o ON o.near_miss_object_id = n.near_miss_object_id"
            " WHERE n.chart_id = %s AND n.generation = %s ORDER BY o.body, o.relation_kind, o.canonical_target, n.t_in",
            (chart_id, generation)).fetchall()
        keys = set(keys)
        return [{"body": r[0], "relation": r[1], "target": r[2], "near_miss_id": str(r[3]), "t_in": r[4], "t_out": r[5],
                 "clearance_deg": float(r[6])} for r in map(_row, rows) if (r[0], r[1], r[2]) in keys]

    def searched_keys(self, *, chart_id: str, generation: str) -> set[tuple]:
        return {_row(r) for r in self.conn.execute(
            f"SELECT o.body, o.relation_kind, o.canonical_target FROM public.{SEARCH_TABLE} s"
            f" JOIN public.{OBJECT_TABLE} o ON o.near_miss_object_id = s.near_miss_object_id"
            " WHERE s.chart_id = %s AND s.generation = %s AND s.searched_complete", (chart_id, generation)).fetchall()}


def reconcile_with_certifier(*, reported: Sequence[dict], stored: Sequence[dict], searched: set, obligations: Sequence[tuple],
                             horizon: tuple[datetime, datetime]) -> list[str]:
    """The in-build cross-check of two INDEPENDENT derivations for one class: `reported` is what the contact-geometry certifier classified
    from the ephemeris alone (its graze dicts: body, relation, target, interval = the whole stretch), `stored` the builder's rows for the
    class's point obligations. Named problems (empty = they agree):

      near_miss_unsearched            a point obligation of the class has no complete near-miss search row;
      near_miss_reported_but_unstored the certifier found a near-miss the builder did not store;
      near_miss_stored_but_unreported the builder stored one, overlapping the horizon, the certifier did not find.

    Pairing is one to one by object and overlap of the whole stretches. Agreement of the bounds to a derived tolerance is the independent
    verifier's duty, not this self-check's."""
    problems: list[str] = []
    for body, relation, target in sorted(set(obligations) - set(searched)):
        problems.append(f"near_miss_unsearched: {body} {relation} {target} has no complete near-miss search row in this generation")
    free = [s for s in stored if s["t_in"] < horizon[1] and s["t_out"] > horizon[0]]
    for g in reported:
        a, b = (datetime.fromisoformat(x) for x in g["interval"])
        match = next((s for s in free if (s["body"], s["relation"], s["target"]) == (g["body"], g["relation"], g["target"])
                      and s["t_in"] < b and a < s["t_out"]), None)
        if match is None:
            problems.append(f"near_miss_reported_but_unstored: {g['body']} {g['relation']} {g['target']} [{g['interval'][0]}, {g['interval'][1]}) "
                            f"closest {g.get('closest_approach_deg')} deg")
        else:
            free.remove(match)
    for s in free:
        problems.append(f"near_miss_stored_but_unreported: {s['body']} {s['relation']} {s['target']} [{s['t_in'].isoformat()}, "
                        f"{s['t_out'].isoformat()}) clearance {s['clearance_deg']} deg (id {s['near_miss_id']})")
    return problems


__all__ = ["LAYER_VERSION", "MIN_CLEARANCE_DEG", "NearMiss", "NearMissMismatch", "NearMissObject", "NearMissStore", "NearMissUnresolved",
           "SCORE_REASON", "STANDING", "TABLES", "Stretch", "dasha_junctions", "near_miss_id", "orb_policy_id", "reconcile_with_certifier",
           "refine_closest", "rootless_stretches", "solve_object_near_misses"]
