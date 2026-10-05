"""Independent verifier side of the `near_miss` kind (ND-P2-20261005 rules 1-2 reconciled; FINAL_BUILD_SCOPE FB-24..FB-29).

Written from the decision text and FB-24..FB-29 ALONE, before the builder branch (`pravaha/d-near-miss-storage`) was read.
It imports nothing from the builder or from `contact_certify`; the verification job's real ephemeris re-derivation will
call `derive_near_misses` below with its own `position_at`, and the FB-38-style equality comparison with the builder is done
as data later.

THE BAND (stated once): the 1-degree point band is drawn INCLUSIVELY — a body at exactly `orb` degrees is inside — exactly as the
built band does (`contact_reconstruct.band_intervals`: `gap <= 0`), `classify_graze` and `nd_h_tables.kb_edge_licensed`. `derive_near_misses` takes its
stretches FROM `band_intervals` (a test with an off-grid dip proves it), so there is one band, not two.

NOT DONE (stated plainly): the STATIONLESS-BODY duty of FB-24 (a Sun/Moon/mean-node stretch must never become a near-miss for lack of an
observed root) has no detector here and no parameter pretending to be one; the stored rows' `precision_regime`/`delta_t`/`solver_method`
fields are not checked; the ephemeris-backed derivation (the job supplies `position_at`) is not wired.

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
# Per-body speed bound (degrees/day), PINNED EQUAL to the kernel table `contact_reconstruct.VMAX_DPS` (the builder's certifier also reads
# it): the equality test is a DRIFT ALARM, not independence. The basis is the astronomical maxima of the apparent sidereal motion (Sun 1.2,
# Moon 16, Mars 1.0, Mercury 2.6, Venus 1.6, Jupiter 0.35, Saturn 0.2 deg/day, mean nodes 0.08); a stated bound that is true is a true
# upper bound. A caller-supplied bound BELOW it is refused (an understated bound certifies a crossing).
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
    edge and certified whole), its clearance is the global minimum of the stretch CERTIFIED WITHIN `tol` degrees by the speed-bound branch-and-bound of `_analyse_stretch`, and that clearance is at
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


# ── derivation: the stretches come from the kernel's band logic; this module classifies and refines ──────────────────
FLOOR_SECONDS = 1.0                    # the finest bisection step of the certification
CERT_TOL_DEG = GRAZE_MIN_APPROACH_DEG / 10   # the stated resolution of the certified minimum (5e-4 deg): a tenth of the smallest clearance that counts
STEP_SECONDS_MAX = 3600.0              # the coarsest first-pass step (finer for short stretches, coarser for very long ones)
MAX_SAMPLES = 512
MAX_EVALS = 40_000                     # work budget per stretch: a certificate that would need more is UNCERTIFIED (never a silent blow-up)
CANDIDATE_RESOLUTION_SECONDS = 300.0   # the granularity at which the set of candidate closest TIMES is reported
CLOSEST_SLACK_SECONDS = 5.0            # a stored closest instant may sit this far outside a candidate interval (storage rounding)


def _signed_offset(lon: float, centre: float) -> float:
    return ((lon - centre + 180.0) % 360.0) - 180.0


class _BudgetExhausted(Exception):
    pass


def _analyse_stretch(dist_at, a: datetime, b: datetime, vmax_dps: float, *, max_evals: int = MAX_EVALS) -> dict:
    """One in-band stretch [a, b]: is a root inside, and — when none — the GLOBAL minimum of |d| certified WITHIN `tol`, and the SET of times at
    which that minimum can lie. `dist_at(t)` is the signed offset to the nearest level (continuous inside a stretch). A first pass samples the
    stretch; a sign change or a zero is a root. Otherwise a branch-and-bound over EVERY sampled step uses the speed bound: inside a step of length
    g with end values d0, d1 the value cannot fall below `max(0, (|d0| + |d1| - v g) / 2)`; a step whose lower bound is not below (best - tol)
    is pruned (it cannot hide a lower dip, however narrow and wherever it sits between samples); any other step is bisected, a sign change at a
    midpoint is a root, and a step still not pruned at FLOOR_SECONDS makes the minimum UNCERTIFIED. A SECOND pass keeps every step whose lower
    bound does not exceed (best + tol) and bisects it to CANDIDATE_RESOLUTION_SECONDS: those intervals are where the minimiser can be — with two
    nearly equal minima BOTH are candidates, because the search proves the VALUE, not a unique TIME. More than `max_evals` evaluations leaves the
    result uncertified (`reason` = work_budget_exhausted).
    -> {rooted, certified, clearance_deg, t_closest, closest_candidates, closest_certified, reason}. `tol` = CERT_TOL_DEG (5e-4 degrees): the
    stated resolution of the claim; a speed bound so large that a step of FLOOR_SECONDS can still hide a lower value leaves the minimum UNCERTIFIED."""
    v = vmax_dps / 86400.0                                             # degrees per second
    tol = CERT_TOL_DEG
    count = [0]

    def f(t):
        count[0] += 1
        if count[0] > max_evals:
            raise _BudgetExhausted()
        return dist_at(t)

    span = (b - a).total_seconds()
    step = max(min(STEP_SECONDS_MAX, span), span / MAX_SAMPLES, FLOOR_SECONDS)
    ts = [a]
    while ts[-1] + timedelta(seconds=step) < b:
        ts.append(ts[-1] + timedelta(seconds=step))
    ts.append(b)
    best = float("inf")
    best_t = None
    try:
        ds = [f(t) for t in ts]
        if any(d == 0 for d in ds) or any((ds[k] > 0) != (ds[k + 1] > 0) for k in range(len(ds) - 1)):
            return {"rooted": True, "certified": True, "clearance_deg": 0.0, "t_closest": None, "closest_candidates": [],
                    "closest_certified": False, "reason": None}
        k0 = min(range(len(ds)), key=lambda k: abs(ds[k]))
        best_t, best = _refine_min(f, ts[max(k0 - 1, 0)], ts[min(k0 + 1, len(ts) - 1)])
        if abs(ds[k0]) < best:
            best, best_t = abs(ds[k0]), ts[k0]
        certified = True
        steps = [(ts[k], ts[k + 1], ds[k], ds[k + 1]) for k in range(len(ts) - 1)]
        stack = list(steps)
        while stack:
            t0, t1, d0, d1 = stack.pop()
            gap = (t1 - t0).total_seconds()
            lower = max(0.0, (abs(d0) + abs(d1) - v * gap) / 2.0)
            if lower >= best - tol:
                continue                                               # this step cannot hide anything lower
            if gap <= FLOOR_SECONDS:
                certified = False                                      # cannot be excluded at the finest step
                continue
            tm = t0 + (t1 - t0) / 2
            dm = f(tm)
            if dm == 0 or (dm > 0) != (d0 > 0):
                return {"rooted": True, "certified": True, "clearance_deg": 0.0, "t_closest": None, "closest_candidates": [],
                        "closest_certified": False, "reason": None}
            if abs(dm) < best:
                best, best_t = abs(dm), tm
            stack.append((t0, tm, d0, dm))
            stack.append((tm, t1, dm, d1))
        cands: list[tuple[datetime, datetime]] = []
        stack = list(steps)
        while stack:
            t0, t1, d0, d1 = stack.pop()
            gap = (t1 - t0).total_seconds()
            lower = max(0.0, (abs(d0) + abs(d1) - v * gap) / 2.0)
            if lower > best + tol:
                continue
            if gap <= CANDIDATE_RESOLUTION_SECONDS:
                cands.append((t0, t1))
                continue
            tm = t0 + (t1 - t0) / 2
            dm = f(tm)
            stack.append((t0, tm, d0, dm))
            stack.append((tm, t1, dm, d1))
        merged: list[list[datetime]] = []
        for lo, hi in sorted(cands):
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        return {"rooted": False, "certified": certified, "clearance_deg": best, "t_closest": best_t,
                "closest_candidates": [(lo, hi) for lo, hi in merged], "closest_certified": certified,
                "reason": None if certified else "minimum_not_excluded_at_floor"}
    except _BudgetExhausted:
        return {"rooted": False, "certified": False, "clearance_deg": best if best_t is not None else None, "t_closest": best_t,
                "closest_candidates": [(a, b)], "closest_certified": False, "reason": "work_budget_exhausted"}


class NearMissSearch(list):
    """The result of `derive_near_misses`: the classified stretches plus the LIMIT the shared band detector carries. `contact_reconstruct` finds
    every in-band interval of at least `MIN_EXCURSION_SECONDS` and does NOT exclude shorter excursions, so an EMPTY result is
    'nothing found at that resolution', never an unqualified 'verified empty' or 'complete'."""
    resolution_limit_seconds: float = 60.0
    named_limit: str = ""
    complete: bool = False
    verified_empty: bool = False


def derive_near_misses(position_at, body: str, centres, lo: datetime, hi: datetime, *, orb_deg: float,
                       vmax_dps: float | None = None) -> list[dict]:
    """The maximal in-band stretches of `body` over [lo, hi) around the longitude `centres` (inclusive band), each classified.
    THE STRETCHES COME FROM `contact_reconstruct.band_intervals` — the kernel's own band logic, so there is ONE band, not two
    (a 57-minute dip that bottoms between samples is found there; a sampler of our own would miss it). This module only
    CLASSIFIES each stretch and refines its closest approach (`_analyse_stretch`). `position_at(body, t)` is the longitude in
    degrees. The speed bound is the verifier's table `VMAX_DPS[body]` (pinned equal to the kernel's); a caller-supplied
    `vmax_dps` below it is refused (`speed_bound_below_table`), a larger one is allowed (more conservative). Returns dicts
    {t_in, t_out, state, reason, clearance_deg, t_closest, closest_candidates, clipped}; a stretch touching `lo` or `hi` is `clipped` and
    UNRESOLVED (`clipped_stretch_not_followed`): following it beyond the edge is the caller's job. The result is a `NearMissSearch`: it carries the
    shared detector's NAMED LIMIT (excursions shorter than 60 s are not excluded), so it is never an unqualified complete / verified-empty signal;
    a non-finite position is refused (`geometry_unavailable`), never read as 'nothing found'."""
    from . import contact_reconstruct as cr
    table = VMAX_DPS.get(body.lower())
    if table is None:
        raise NearMissError(f"unknown_body: {body!r}")
    if vmax_dps is not None and vmax_dps < table:
        raise NearMissError(f"speed_bound_below_table: {vmax_dps} < {table} for {body}")
    if not hi > lo:
        raise NearMissError(f"window_empty: {lo.isoformat()} .. {hi.isoformat()}")
    vmax = table if vmax_dps is None else vmax_dps
    centres = [float(c) % 360.0 for c in centres]
    if not all(math.isfinite(c) for c in centres) or not math.isfinite(float(orb_deg)) or not orb_deg > 0:
        raise NearMissError("non_finite: centres and orb must be finite and the orb positive")

    def checked(b, t):
        v = position_at(b, t)
        if v is None or not math.isfinite(float(v)):
            raise NearMissError(f"geometry_unavailable: {b} position at {t.isoformat()} is {v!r}")
        return v

    def dist_at(t):
        lon = float(checked(body, t))
        return min((_signed_offset(lon, c) for c in centres), key=abs)

    out = NearMissSearch()
    out.resolution_limit_seconds = cr.MIN_EXCURSION_SECONDS
    out.named_limit = cr.NAMED_LIMIT
    for t_in, t_out in cr.band_intervals(checked, body, centres, orb_deg, lo, hi):
        clipped = t_in == lo or t_out == hi
        res = _analyse_stretch(dist_at, t_in, t_out, vmax)
        rec = {"t_in": t_in, "t_out": t_out, "clipped": clipped}
        if res["rooted"]:
            rec.update(state="contact", reason=None, clearance_deg=0.0, t_closest=None)
        else:
            state, reason = classify_stretch(rooted=False, complete=True, clipped_followed=not clipped,
                                             clearance_deg=res["clearance_deg"], clearance_certified=res["certified"])
            rec.update(state=state, reason=reason, clearance_deg=res["clearance_deg"], t_closest=res["t_closest"],
                       closest_candidates=res["closest_candidates"], closest_certified=res["closest_certified"], certificate_reason=res["reason"])
        out.append(rec)
    return out


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


def _in_band(d: float, orb: float) -> bool:
    return abs(d) <= orb                # INCLUSIVE, as the built band (gap <= 0)


# ── the junction field (ND-P2 rule 1) ─────────────────────────────────────────────────────────────────────────────
def junction_field(t_in: datetime, t_out: datetime, events, *, coverage_complete: bool) -> dict:
    """`events`: (kind, instant) pairs on the CURRENT pinned sky and dasha conventions. A junction at t_in is INCLUDED,
    at t_out EXCLUDED. Only MD/AD boundaries are dasha junctions (a PD boundary is an unknown kind and refused). Missing
    coverage = unknown (kinds None), never empty. -> {'kinds': sorted list | None, 'complete': bool}. The field means
    'contains a junction'; it admits nothing and scores nothing."""
    events = list(events)                                              # an iterator is consumed ONCE here, never twice
    bad = sorted({k for k, _ in events} - JUNCTION_KINDS)
    if bad:
        raise NearMissError(f"junction_kind_unknown: {bad}")
    if not coverage_complete:
        return {"kinds": None, "complete": False}
    kinds = sorted({k for k, t in events if t_in <= t < t_out})
    return {"kinds": kinds, "complete": True}


# ── the stored row ────────────────────────────────────────────────────────────────────────────────────────────────
def _num(x):
    """A stored REAL / NUMERIC arrives as float or Decimal: compare as float, never raise a TypeError."""
    return None if x is None else float(x)


_REQUIRED_FIELDS = ("t_in", "t_out", "standing", "score", "score_reason", "clearance_deg", "orb_deg", "proximity",
                    "closest_state", "t_closest", "junction", "junction_complete", "ordinal", "object_id")
_NOT_NONE = ("t_in", "t_out", "orb_deg", "proximity", "clearance_deg", "ordinal", "object_id")     # a present-but-NULL value is a missing field
_NUMERIC = ("clearance_deg", "orb_deg", "proximity")


def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def row_problems(row: dict, *, domain: tuple | None = None) -> list[str]:
    """Every reason, by name, a stored `ka_gochara_near_miss` row is not acceptable (empty = acceptable). A missing field
    is a named refusal (`row_field_missing`), never a crash. `domain` = (first, last instant) of the full-domain search: an
    `edge_unplaced` row must touch it (its stretch starts at the first or ends at the last instant) — without a domain that
    claim cannot be checked and is refused (`edge_unplaced_unverifiable_without_domain`)."""
    missing = [f for f in _REQUIRED_FIELDS if f not in row or (f in _NOT_NONE and row[f] is None)]
    if missing:
        return [f"row_field_missing: {missing}"]
    nonfinite = [f for f in _NUMERIC if not _finite(row[f])]
    if nonfinite:
        return [f"non_finite_value: {nonfinite}"]
    p: list[str] = []
    if row.get("standing") != STANDING:
        p.append(f"standing_not_near_miss: {row.get('standing')!r}")
    if row.get("score") is not None:
        p.append("near_miss_scored: score must be NULL")
    if row.get("score_reason") != UNSCORED_REASON:
        p.append(f"score_reason_not_near_miss_unscored: {row.get('score_reason')!r}")
    c, orb = _num(row.get("clearance_deg")), _num(row.get("orb_deg"))
    if c is None or not c > 0:
        p.append(f"clearance_not_positive: {c!r}")
    elif c < GRAZE_MIN_APPROACH_DEG:
        p.append(f"clearance_below_min_approach: {c}")
    if orb is None or not orb > 0:
        p.append(f"orb_not_positive: {orb!r}")
    if c and orb and c > 0 and orb > 0:
        if c > orb:                                                    # inclusive band: a clearance equal to the orb is on the edge
            p.append(f"clearance_not_inside_orb: {c} > {orb}")
        elif row.get("proximity") is None or abs(_num(row["proximity"]) - (1.0 - c / orb)) > PROXIMITY_TOL:
            p.append(f"proximity_not_one_minus_clearance_over_orb: {row.get('proximity')!r}")
    if not row["t_in"] < row["t_out"]:
        p.append("interval_empty")
    if not isinstance(row["ordinal"], int) or isinstance(row["ordinal"], bool) or row["ordinal"] < 1:
        p.append(f"ordinal_not_a_positive_integer: {row['ordinal']!r}")
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
def compare_sets(rederived, stored, *, junction_source, expected_orb_deg: float, expected_object_id,
                 reported_count: int | None = None, tol_seconds: float = 2.0) -> list[str]:
    """`rederived`: dicts from `derive_near_misses` over the FULL-DOMAIN search of ONE object (state 'near_miss' or 'unresolved'); `stored`: stored
    rows. Refused by name: near_miss_missing (re-derived, not stored), near_miss_extra (stored, not re-derived), near_miss_unresolved,
    near_miss_reported_not_stored / near_miss_stored_not_reported, and — for every MATCHED pair — near_miss_clearance_mismatch,
    near_miss_t_closest_mismatch (a placed row's instant must lie in one of the re-derived CANDIDATE intervals: with nearly equal minima several
    are, and the search proves the value, not a unique time), near_miss_junction_mismatch (the stored junction must equal `junction_field`
    recomputed from `junction_source`, REQUIRED: a stored junction is never accepted on shape alone), near_miss_orb_mismatch (the stored orb is
    the object's orb), near_miss_object_mismatch (the stored `object_id` is `expected_object_id`, REQUIRED) and near_miss_ordinal_mismatch (the
    stored ordinal is the stretch's position in the full-domain ordering, `assign_ordinals`). Stored numbers are normalised (Decimal) at this
    boundary and a non-finite value is refused (`non_finite_value`)."""
    events, coverage_complete = junction_source
    events = list(events)                                              # materialised ONCE: an iterator would be exhausted by the first row
    if not _finite(expected_orb_deg) or not expected_orb_deg > 0:
        raise NearMissError(f"non_finite: expected_orb_deg {expected_orb_deg!r}")
    p: list[str] = []
    want = [r for r in rederived if r["state"] == "near_miss"]
    for r in rederived:
        if r["state"] == "unresolved":
            p.append(f"near_miss_unresolved: {r['t_in'].isoformat()} {r['reason']}")
    try:
        ordered = assign_ordinals(want)
    except NearMissError as exc:
        p.append(str(exc))
        ordered = []
    ordinal_of = {id(r): o for o, r in ordered}
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
        bad = [k for k in ("clearance_deg", "orb_deg") if not _finite(s.get(k))]
        if bad:
            p.append(f"non_finite_value: {bad} at {s['t_in'].isoformat()}")
            continue
        if abs(float(s["clearance_deg"]) - w["clearance_deg"]) > CLEARANCE_TOL_DEG:
            p.append(f"near_miss_clearance_mismatch: stored {float(s['clearance_deg'])} vs re-derived {w['clearance_deg']:.6f}")
        if abs(float(s["orb_deg"]) - float(expected_orb_deg)) > 1e-9:
            p.append(f"near_miss_orb_mismatch: stored {float(s['orb_deg'])} vs the object's {float(expected_orb_deg)}")
        if s.get("object_id") != expected_object_id:
            p.append(f"near_miss_object_mismatch: stored {s.get('object_id')!r} vs expected {expected_object_id!r}")
        if s.get("ordinal") != ordinal_of.get(id(w)):
            p.append(f"near_miss_ordinal_mismatch: stored {s.get('ordinal')!r} vs the full-domain position {ordinal_of.get(id(w))!r}")
        if s.get("closest_state") == "placed":
            tc = s.get("t_closest")
            cands = w.get("closest_candidates") or [(w["t_in"], w["t_out"])]
            slack = timedelta(seconds=CLOSEST_SLACK_SECONDS)
            if tc is None or not any(lo - slack <= tc <= hi + slack for lo, hi in cands):
                p.append(f"near_miss_t_closest_mismatch: stored {tc} is in none of the {len(cands)} candidate interval(s)")
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
    if search.get("resolution_limit_seconds") != 60.0:
        p.append(f"near_miss_search_resolution_unstated: {search.get('resolution_limit_seconds')!r} (the band detector does not exclude excursions "
                 "shorter than 60 s: an empty or complete result must say so)")
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
