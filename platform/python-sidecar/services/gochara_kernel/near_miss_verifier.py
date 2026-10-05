"""Independent verifier side of the `near_miss` kind (ND-P2-20261005 rules 1-2 reconciled; FINAL_BUILD_SCOPE FB-24..FB-29).

Written from the decision text and FB-24..FB-29 ALONE, before the builder branch (`pravaha/d-near-miss-storage`) was read.
It imports nothing from the builder or from `contact_certify`; the verification job's real ephemeris re-derivation will
call `derive_near_misses` below with its own `dist_at`, and the FB-38-style equality comparison with the builder is done
as data later.

THE BAND (stated once): the 1-degree point band is drawn INCLUSIVELY — a body at exactly `orb` degrees is inside — exactly as the
built band does (`contact_reconstruct.band_intervals`: `gap <= 0`), `classify_graze` and `nd_h_tables.kb_edge_licensed`. A test compares
`derive_near_misses`' stretch edges with `band_intervals` on the same curve so there is one band, not two.

NOT DONE (stated plainly): the STATIONLESS-BODY duty of FB-24 (a Sun/Moon/mean-node stretch must never become a near-miss for lack of an
observed root) has no detector here and no parameter pretending to be one; the stored rows' `precision_regime`/`delta_t`/`solver_method`
fields are not checked; the ephemeris-backed derivation (the job supplies `dist_at`) is not wired.

What a verifier must ACCEPT and REFUSE for the kind:
  * the three states of a rootless-or-rooted stretch (`classify_stretch`): CONTACT (a verified root, tangency included),
    NEAR-MISS (a COMPLETE rootless stretch with CERTIFIED POSITIVE clearance), UNRESOLVED (neither: a named refusal,
    never a near-miss); no threshold turns a small positive distance into a contact;
  * the stored row (`row_problems`): standing, NULL score with reason, positive clearance, proximity = 1 - clearance/orb,
    the closest-instant states, the junction field (`junction_field`: ingress at t_in included, at t_out excluded, missing
    coverage = unknown, never empty);
  * ordinals over the FULL-DOMAIN set (`assign_ordinals`);
  * set comparison with the re-derived set (`compare_sets`): missing / extra / unresolved / reported-but-unstored /
    stored-but-unreported are refused by name; verified-empty coverage (`coverage_problems`);
  * noninterference (`noninterference_problems`): layer on and off must give identical scored outputs.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

KIND = "near_miss"
STANDING = "near_miss"
UNSCORED_REASON = "near_miss_unscored"
LAYER_VERSION = 1
GRAZE_MIN_APPROACH_DEG = 5e-3          # "as today" (FB-24): a clearance below it cannot be certified at the declared accuracy
PROXIMITY_NAME = "proximity"           # never "strength"
# ND-P2 rule 1: "an actual MD/AD boundary" — a PD boundary is NOT a junction kind (an event of any other kind is refused).
JUNCTION_KINDS = frozenset({"sign_ingress", "nakshatra_ingress", "dasha_md_ad_boundary"})
# The verifier's OWN per-body speed bound (degrees/day), written from the kernel's stated bound; a test pins it equal to
# `contact_reconstruct.VMAX_DPS` as data. A caller-supplied bound BELOW it is refused (an understated bound certifies a crossing).
VMAX_DPS = {"sun": 1.2, "moon": 16.0, "mars": 1.0, "mercury": 2.6, "venus": 1.6, "jupiter": 0.35, "saturn": 0.2,
            "rahu": 0.08, "ketu": 0.08}
PROXIMITY_TOL = 1.5e-4                 # proximity and clearance are stored rounded to 4 decimals; a refusal below this would be a seam, above it a blind spot
CLEARANCE_TOL_DEG = 1e-3               # re-derived vs stored closest approach
CLOSEST_TOL_SECONDS = 600.0            # re-derived vs stored instant of closest approach (a flat minimum is shallow)
CLOSEST_STATES = frozenset({"placed", "edge_unplaced"})
# Everything the layer must NOT change when it is switched on (FB-29): scored extracts, supports, members, peaks,
# rankings, candidate counts and all five endpoints (including the T-honesty endpoint).
NONINTERFERENCE_KEYS = ("scored_extracts", "supports", "members", "peaks", "rankings", "candidate_counts",
                        "coverage_accounting", "endpoint_1", "endpoint_2", "endpoint_3", "endpoint_4", "endpoint_5_t_honesty",
                        "contact_identity_bytes")


class NearMissError(ValueError):
    pass


# ── the three states ──────────────────────────────────────────────────────────────────────────────────────────────
def classify_stretch(*, rooted: bool, complete: bool, clipped_followed: bool = True, clearance_deg: float | None = None,
                     clearance_certified: bool = False) -> tuple[str, str | None]:
    """-> (state, reason). A verified exact root (tangency included) is a CONTACT whatever else holds. A rootless stretch is
    a NEAR-MISS only when it is the COMPLETE maximal stretch (a horizon-clipped piece must have been followed beyond the
    edge and certified whole), its clearance is the CERTIFIED global minimum over all extrema, and that clearance is at
    least GRAZE_MIN_APPROACH_DEG; anything less is UNRESOLVED with a named reason. (The stationless-body duty is NOT implemented
    here: see the module's not-done list.)"""
    if rooted:
        return "contact", None
    if not complete:
        return "unresolved", "stretch_incomplete"
    if not clipped_followed:
        return "unresolved", "clipped_stretch_not_followed"
    if clearance_deg is None or not clearance_certified:
        return "unresolved", "clearance_not_certified"
    if not clearance_deg > 0:
        return "unresolved", "clearance_not_positive"
    if clearance_deg < GRAZE_MIN_APPROACH_DEG:
        return "unresolved", "clearance_below_min_approach"
    return "near_miss", None


# ── independent derivation from a signed-distance function (the verifier's own band logic) ─────────────────────────
MIN_STEP_SECONDS = 1.0


def _in_band(d: float, orb: float) -> bool:
    return abs(d) <= orb                # INCLUSIVE, as the built band (gap <= 0)


def _proved_no_crossing(dist_at, t0, t1, d0, d1, vmax_dps) -> bool:
    """True only when the signed distance PROVABLY does not reach zero inside (t0, t1): |d0|+|d1| > vmax * gap proves it;
    otherwise bisect; a sign change or a zero at a midpoint is a crossing; an unproved step at the floor is False."""
    gap = (t1 - t0).total_seconds()
    if abs(d0) + abs(d1) > vmax_dps / 86400.0 * gap:
        return True
    if gap <= MIN_STEP_SECONDS:
        return False
    tm = t0 + (t1 - t0) / 2
    dm = dist_at(tm)
    if dm == 0 or (dm > 0) != (d0 > 0):
        return False
    return (_proved_no_crossing(dist_at, t0, tm, d0, dm, vmax_dps)
            and _proved_no_crossing(dist_at, tm, t1, dm, d1, vmax_dps))


def derive_near_misses(dist_at, lo: datetime, hi: datetime, *, body: str, orb_deg: float,
                       vmax_dps: float | None = None, step_seconds: float = 3600.0) -> list[dict]:
    """The maximal in-band stretches (|signed distance| <= orb, inclusive) of `dist_at` over [lo, hi), each classified.
    `dist_at(t)` is the signed distance in degrees from the transiting `body` to the ray LEVEL, normalised to [-180, 180]
    (a value outside it is refused: `distance_not_normalised`, never a silent miss at the 0/360 wrap). The speed bound is the
    verifier's OWN table `VMAX_DPS[body]`; a caller-supplied `vmax_dps` below it is refused (`speed_bound_below_table`), a
    larger one is allowed (more conservative). Returns dicts {t_in, t_out, state, reason, clearance_deg, t_closest, clipped}.
    A stretch touching `lo` or `hi` is `clipped` and reported UNRESOLVED (`clipped_stretch_not_followed`): following it beyond
    the edge is the caller's job."""
    table = VMAX_DPS.get(body)
    if table is None:
        raise NearMissError(f"unknown_body: {body!r}")
    if vmax_dps is not None and vmax_dps < table:
        raise NearMissError(f"speed_bound_below_table: {vmax_dps} < {table} for {body}")
    vmax = table if vmax_dps is None else vmax_dps
    step = timedelta(seconds=step_seconds)
    n = int((hi - lo) / step)
    ts = [lo + i * step for i in range(n + 1)]
    if ts[-1] < hi:
        ts.append(hi)
    ds = [dist_at(t) for t in ts]
    if any(abs(d) > 180.0 + 1e-9 for d in ds):
        raise NearMissError("distance_not_normalised: dist_at must return a signed distance within [-180, 180] degrees")
    out = []
    i = 0
    while i < len(ts):
        if not _in_band(ds[i], orb_deg):
            i += 1
            continue
        j = i
        while j + 1 < len(ts) and _in_band(ds[j + 1], orb_deg):
            j += 1
        clipped = i == 0 or j == len(ts) - 1
        seg = range(i, j + 1)
        rooted = any(ds[k] == 0 for k in seg) or any((ds[k] > 0) != (ds[k + 1] > 0) for k in range(i, j))
        t_in = ts[i] if i == 0 else _edge(dist_at, ts[i - 1], ts[i], orb_deg)
        t_out = ts[j] if j == len(ts) - 1 else _edge(dist_at, ts[j], ts[j + 1], orb_deg)
        rec = {"t_in": t_in, "t_out": t_out, "clipped": clipped}
        if rooted:
            rec.update(state="contact", reason=None, clearance_deg=0.0, t_closest=None)
        else:
            sign = 1 if ds[i] > 0 else -1
            proved = all(_proved_no_crossing(dist_at, ts[k], ts[k + 1], ds[k], ds[k + 1], vmax)
                         for k in range(max(i - 1, 0), min(j + 1, len(ts) - 1)) if sign * ds[k] > 0 and sign * ds[k + 1] > 0)
            k0 = min(seg, key=lambda k: abs(ds[k]))
            t_c, c = _refine_min(dist_at, ts[max(k0 - 1, 0)], ts[min(k0 + 1, len(ts) - 1)])
            state, reason = classify_stretch(rooted=False, complete=True, clipped_followed=not clipped,
                                             clearance_deg=c, clearance_certified=proved)
            rec.update(state=state, reason=reason, clearance_deg=c, t_closest=t_c)
        out.append(rec)
        i = j + 1
    return out


def _edge(dist_at, t_a, t_b, orb) -> datetime:
    """The instant |d| = orb between a and b (one inside the band, one outside) by bisection to one second."""
    a_in = _in_band(dist_at(t_a), orb)
    while (t_b - t_a).total_seconds() > 1.0:
        tm = t_a + (t_b - t_a) / 2
        if _in_band(dist_at(tm), orb) == a_in:
            t_a = tm
        else:
            t_b = tm
    return t_a + (t_b - t_a) / 2


def _refine_min(dist_at, a: datetime, b: datetime):
    """Golden-section minimum of |d| on [a, b] to about a second; -> (instant, clearance)."""
    g = (math.sqrt(5) - 1) / 2
    f = lambda t: abs(dist_at(t))                                      # noqa: E731
    c, d = b - (b - a) * g, a + (b - a) * g
    fc, fd = f(c), f(d)
    while (b - a).total_seconds() > 1.0:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - (b - a) * g
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + (b - a) * g
            fd = f(d)
    t = a + (b - a) / 2
    return t, f(t)


# ── the junction field (ND-P2 rule 1) ─────────────────────────────────────────────────────────────────────────────
def junction_field(t_in: datetime, t_out: datetime, events, *, coverage_complete: bool) -> dict:
    """`events`: (kind, instant) pairs on the CURRENT pinned sky and dasha conventions. A junction at t_in is INCLUDED,
    at t_out EXCLUDED. Only MD/AD boundaries are dasha junctions (a PD boundary is an unknown kind and refused). Missing
    coverage = unknown (kinds None), never empty. -> {'kinds': sorted list | None, 'complete': bool}. The field means
    'contains a junction'; it admits nothing and scores nothing."""
    bad = sorted({k for k, _ in events} - JUNCTION_KINDS)
    if bad:
        raise NearMissError(f"junction_kind_unknown: {bad}")
    if not coverage_complete:
        return {"kinds": None, "complete": False}
    kinds = sorted({k for k, t in events if t_in <= t < t_out})
    return {"kinds": kinds, "complete": True}


# ── the stored row ────────────────────────────────────────────────────────────────────────────────────────────────
_REQUIRED_FIELDS = ("t_in", "t_out", "standing", "score", "score_reason", "clearance_deg", "orb_deg", "proximity",
                    "closest_state", "t_closest", "junction", "junction_complete")


def row_problems(row: dict, *, domain: tuple | None = None) -> list[str]:
    """Every reason, by name, a stored `ka_gochara_near_miss` row is not acceptable (empty = acceptable). A missing field
    is a named refusal (`row_field_missing`), never a crash. `domain` = (first, last instant) of the full-domain search: an
    `edge_unplaced` row must touch it (its stretch starts at the first or ends at the last instant) — without a domain that
    claim cannot be checked and is refused (`edge_unplaced_unverifiable_without_domain`)."""
    missing = [f for f in _REQUIRED_FIELDS if f not in row]
    if missing:
        return [f"row_field_missing: {missing}"]
    p: list[str] = []
    if row.get("standing") != STANDING:
        p.append(f"standing_not_near_miss: {row.get('standing')!r}")
    if row.get("score") is not None:
        p.append("near_miss_scored: score must be NULL")
    if row.get("score_reason") != UNSCORED_REASON:
        p.append(f"score_reason_not_near_miss_unscored: {row.get('score_reason')!r}")
    c, orb = row.get("clearance_deg"), row.get("orb_deg")
    if c is None or not c > 0:
        p.append(f"clearance_not_positive: {c!r}")
    elif c < GRAZE_MIN_APPROACH_DEG:
        p.append(f"clearance_below_min_approach: {c}")
    if orb is None or not orb > 0:
        p.append(f"orb_not_positive: {orb!r}")
    if c and orb and c > 0 and orb > 0:
        if c > orb:                                                    # inclusive band: a clearance equal to the orb is on the edge
            p.append(f"clearance_not_inside_orb: {c} > {orb}")
        elif row.get("proximity") is None or abs(row["proximity"] - (1.0 - c / orb)) > PROXIMITY_TOL:
            p.append(f"proximity_not_one_minus_clearance_over_orb: {row.get('proximity')!r}")
    if not row["t_in"] < row["t_out"]:
        p.append("interval_empty")
    state, tc = row.get("closest_state"), row.get("t_closest")
    if state not in CLOSEST_STATES:
        p.append(f"closest_state_unknown: {state!r}")
    elif state == "placed" and not (tc is not None and row["t_in"] <= tc < row["t_out"]):
        p.append("t_closest_outside_interval")
    elif state == "edge_unplaced":
        if tc is not None:
            p.append("edge_unplaced_has_t_closest")
        if domain is None:
            p.append("edge_unplaced_unverifiable_without_domain")
        elif not (row["t_in"] <= domain[0] or row["t_out"] >= domain[1]):
            p.append("edge_unplaced_not_at_domain_edge")
    j, done = row.get("junction"), row.get("junction_complete")
    if done is False and j is not None:
        p.append("junction_present_without_complete_coverage")
    if done is True and (j is None or not isinstance(j, (list, tuple)) or not set(j) <= JUNCTION_KINDS):
        p.append(f"junction_malformed: {j!r}")
    if done not in (True, False):
        p.append("junction_complete_missing")
    return p


# ── ordinals (FB-25) ──────────────────────────────────────────────────────────────────────────────────────────────
def object_key(body: str, relation: str, target: str, orb_policy_id: str, convention_id: str) -> tuple:
    """Natural key of the object. The orb policy id is IN the key: an orb change is a NEW object, never a renumbering."""
    return (body, relation, target, orb_policy_id, convention_id)


def assign_ordinals(full_domain_set) -> list[tuple[int, dict]]:
    """Ordinals 1..n over the FULL-DOMAIN near-miss set of ONE object: placed stretches by (`t_closest`, `t_in`, `t_out`), then
    edge-unplaced ones (t_closest None) by (`t_in`, `t_out`). The key is TOTAL: two stretches with the same key are a duplicate
    and refused (`duplicate_near_miss`), so the order never depends on input order. The set must be the full-domain one (adding
    a horizon or a class changes no ordinal because the caller never passes a subset)."""
    key_placed = lambda r: (r["t_closest"], r["t_in"], r["t_out"])        # noqa: E731
    key_unplaced = lambda r: (r["t_in"], r["t_out"])                      # noqa: E731
    placed = sorted((r for r in full_domain_set if r.get("t_closest") is not None), key=key_placed)
    unplaced = sorted((r for r in full_domain_set if r.get("t_closest") is None), key=key_unplaced)
    for group, key in ((placed, key_placed), (unplaced, key_unplaced)):
        for a, b in zip(group, group[1:]):
            if key(a) == key(b):
                raise NearMissError(f"duplicate_near_miss: {key(a)!r}")
    return [(i + 1, r) for i, r in enumerate(placed + unplaced)]


# ── set comparison and coverage (FB-28) ───────────────────────────────────────────────────────────────────────────
def compare_sets(rederived, stored, *, junction_source, reported_count: int | None = None, tol_seconds: float = 2.0) -> list[str]:
    """`rederived`: dicts from `derive_near_misses` (state 'near_miss' or 'unresolved'); `stored`: stored rows.
    Refused by name: near_miss_missing (re-derived, not stored), near_miss_extra (stored, not re-derived), near_miss_unresolved,
    near_miss_reported_not_stored / near_miss_stored_not_reported, and — for every MATCHED pair — near_miss_clearance_mismatch,
    near_miss_t_closest_mismatch (a placed row must carry the re-derived instant of closest approach) and
    near_miss_junction_mismatch (the stored junction must equal `junction_field` recomputed from `junction_source`).
    `junction_source` = (events, coverage_complete) is REQUIRED: a stored junction is never accepted on shape alone."""
    events, coverage_complete = junction_source
    p: list[str] = []
    want = [r for r in rederived if r["state"] == "near_miss"]
    for r in rederived:
        if r["state"] == "unresolved":
            p.append(f"near_miss_unresolved: {r['t_in'].isoformat()} {r['reason']}")
    used = set()
    for w in want:
        hit = next((i for i, s in enumerate(stored) if i not in used
                    and abs((s["t_in"] - w["t_in"]).total_seconds()) <= tol_seconds
                    and abs((s["t_out"] - w["t_out"]).total_seconds()) <= tol_seconds), None)
        if hit is None:
            p.append(f"near_miss_missing: {w['t_in'].isoformat()}..{w['t_out'].isoformat()}")
            continue
        used.add(hit)
        s = stored[hit]
        if abs(s["clearance_deg"] - w["clearance_deg"]) > CLEARANCE_TOL_DEG:
            p.append(f"near_miss_clearance_mismatch: stored {s['clearance_deg']} vs re-derived {w['clearance_deg']:.6f}")
        if s.get("closest_state") == "placed" and (s.get("t_closest") is None or
                abs((s["t_closest"] - w["t_closest"]).total_seconds()) > CLOSEST_TOL_SECONDS):
            p.append(f"near_miss_t_closest_mismatch: stored {s.get('t_closest')} vs re-derived {w['t_closest'].isoformat()}")
        expect = junction_field(s["t_in"], s["t_out"], events, coverage_complete=coverage_complete)
        stored_kinds = None if s.get("junction") is None else sorted(s["junction"])
        if (expect["kinds"], expect["complete"]) != (stored_kinds, s.get("junction_complete")):
            p.append(f"near_miss_junction_mismatch: stored {stored_kinds}/{s.get('junction_complete')} vs recomputed "
                     f"{expect['kinds']}/{expect['complete']}")
    p += [f"near_miss_extra: {s['t_in'].isoformat()}..{s['t_out'].isoformat()}" for i, s in enumerate(stored) if i not in used]
    if reported_count is not None:
        if reported_count > len(stored):
            p.append(f"near_miss_reported_not_stored: reported {reported_count}, stored {len(stored)}")
        elif reported_count < len(stored):
            p.append(f"near_miss_stored_not_reported: reported {reported_count}, stored {len(stored)}")
    return p


def coverage_problems(search: dict, stored_count: int, *, horizon: tuple) -> list[str]:
    """One `ka_gochara_near_miss_search` row (body, relation, target, orb): an empty result is a VERIFIED empty result
    only when the search completed over the whole horizon and its count equals the stored rows."""
    p = []
    if search.get("searched_complete") is not True:
        p.append("near_miss_search_incomplete")
    if tuple(search.get("horizon", ())) != tuple(horizon):
        p.append(f"near_miss_search_horizon_mismatch: {search.get('horizon')!r} != {tuple(horizon)!r}")
    if search.get("count") != stored_count:
        p.append(f"near_miss_count_mismatch: search {search.get('count')!r}, stored {stored_count}")
    return p


# ── noninterference (FB-29) ───────────────────────────────────────────────────────────────────────────────────────
def noninterference_problems(layer_on: dict, layer_off: dict) -> list[str]:
    """Every output the layer is forbidden to change, compared with the layer present and absent (coverage accounting
    included, ND-P2 rule 2). A key missing on either side is refused (an unmeasured output is not an identical one)."""
    p = []
    for k in NONINTERFERENCE_KEYS:
        if k not in layer_on or k not in layer_off:
            p.append(f"noninterference_key_missing: {k}")
        elif layer_on[k] != layer_off[k]:
            p.append(f"noninterference_violated: {k}")
    return p


def utc(y, m, d, hh=0, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)
