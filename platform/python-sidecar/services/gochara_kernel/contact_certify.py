"""Certify the COMPLETE contact geometry of a class against the ephemeris (Codex round 9, R9-3).

Endpoint probes (a position just inside and just outside each end of a stored span) cannot see an INTERIOR exit and
re-entry, nor an omitted contact: residence [0,10) with the body outside the sign during [4,6) passes them. This module
reconstructs, from `position_at` alone (`contact_reconstruct`), the contact set every concrete transit obligation of the
class implies over the inventory horizon and compares it with the ledger BOTH WAYS:

  residence on a sign / nakṣatra     the in-cell intervals;
  aspect to a sign                   the union of the in-sign intervals of the source signs (target − angle/30);
  conjunction / aspect to a point    the intervals within the admission orb of the point (of each aspect point).

A reconstructed interval absent from the ledger (an OMITTED contact, or a support that bridges / truncates), and a ledger
contact of the same object that is not a reconstructed interval (invented), both fail. Role-token P1 obligations are
certified by `record_verifier.verify_p1_anchors` over the same reconstruction. INCOMPLETE evidence (no ephemeris, an
undeterminable position) raises `GeometryUnavailable`: no complete-search claim is made. The guarantee and its limit are
`contact_reconstruct.NAMED_LIMIT`, returned with every result.

This module is the VERIFIER's: its orb and aspect tables are its own (`window_verifier._POINT_ORB_DEG` /
`_ASPECT_ANGLES`), nothing is imported from the builder's geometry."""
from __future__ import annotations

from . import boundary_match as bm
from . import contact_reconstruct as cr

_TRANSIT = ("residence", "aspect", "conjunction")
#: stated in coverage and in every result (steward R9-9): the tolerance is derived, never a constant in seconds
BOUNDARY_TOLERANCE_STATEMENT = (
    "a reconstructed boundary equals a stored one within accuracy/|speed| + 1 s, where accuracy is the stored contact's "
    "own stated angular accuracy (the solver's 1 arcsecond when none) and speed the body's speed at that instant; at a "
    "station (|speed| < 1e-3 deg/day) the comparison is in angle, |dlon| <= accuracy + the reconstruction's location error; the "
    "ledger's contacts are compared as a UNION (the builder emits one episode per branch, so retrograde-loop episodes overlap and "
    "their seams are not boundaries of the contact set)")


def _merge(intervals):
    out: list[list] = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def expected_intervals(position_at, body: str, relation: str, target: str, lo, hi) -> list[tuple]:
    """The reconstructed contact intervals of one (body, relation, target) over [lo, hi)."""
    from .window_verifier import _ASPECT_ANGLES, _POINT_ORB_DEG
    kind, _, arg = target.partition(":")
    if relation == "residence" and kind == "span":
        return cr.cached_partition_intervals(position_at, body, 12, lo, hi)[int(arg) - 1]
    if relation == "residence" and kind == "star":
        return cr.cached_partition_intervals(position_at, body, 27, lo, hi)[int(arg) - 1]
    if relation == "aspect" and kind == "span":
        n = int(arg) - 1
        signs = {(n - int(a // 30.0)) % 12 for a in _ASPECT_ANGLES[body]}
        cells = cr.cached_partition_intervals(position_at, body, 12, lo, hi)
        return _merge([iv for s in signs for iv in cells[s]])
    if kind == "point" and relation in ("conjunction", "aspect"):
        lam = float(arg) % 360.0
        angles = (0.0,) if relation == "conjunction" else _ASPECT_ANGLES[body]
        return cr.band_intervals(position_at, body, [(lam - a) % 360.0 for a in angles], _POINT_ORB_DEG[relation], lo, hi)
    raise cr.GeometryUnavailable(f"no independent geometry for {relation} on {target!r}")


#: A graze's closest approach must clear this many degrees (about 18 arcseconds) of the ray level, so a near-miss the builder SHOULD have minted a
#: contact for (an exact root with a tiny penetration) is never classified as a graze: it stays an omission and still raises.
GRAZE_MIN_APPROACH_DEG = 5e-3


def _no_crossing_proved(position_at, body: str, level: float, t0, d0: float, t1, d1: float) -> bool:
    """True only when the body PROVABLY does not reach `level` between t0 and t1 (signed distances d0, d1, both non-zero and of ONE sign): the pair
    clears the movement the speed bound allows (|d0| + |d1| > VMAX x step), else the step is bisected down to `contact_reconstruct.MIN_EXCURSION_SECONDS`.
    A sign change or a zero at a midpoint is a crossing (False); a step unproved at the floor is False. See `classify_graze`."""
    vmax = cr.VMAX_DPS[body.lower()] / 86400.0
    gap = (t1 - t0).total_seconds()
    if abs(d0) + abs(d1) > vmax * gap:
        return True
    if gap <= cr.MIN_EXCURSION_SECONDS:
        return False
    tm = t0 + (t1 - t0) / 2
    dm = ((float(position_at(body, tm)) - level + 180.0) % 360.0) - 180.0
    if dm == 0.0 or (dm > 0.0) != (d0 > 0.0):
        return False
    return (_no_crossing_proved(position_at, body, level, t0, d0, tm, dm)
            and _no_crossing_proved(position_at, body, level, tm, dm, t1, d1))


def _full_stretch(position_at, body: str, levels, orb: float, a, b, lo, hi, *, max_extension_days: float = 1500.0):
    """(A, B) | None: the whole in-band stretch that contains the horizon-clipped interval (a, b), followed BEYOND the horizon edge(s) it is clipped at, from
    `position_at` alone, to the stretch's own band exits. None when the extension cannot be settled within `max_extension_days` (the window doubles until the
    stretch's ends are interior to it)."""
    from datetime import timedelta
    ext = 60.0
    while ext <= max_extension_days:
        w_lo = lo - timedelta(days=ext) if a <= lo else lo
        w_hi = hi + timedelta(days=ext) if b >= hi else hi
        stretches = cr.band_intervals(position_at, body, levels, orb, w_lo, w_hi)
        mine = [s for s in stretches if s[0] < b and a < s[1]]
        if len(mine) != 1:
            return None
        A, B = mine[0]
        if not ((a <= lo and A <= w_lo) or (b >= hi and B >= w_hi)):
            return A, B
        ext *= 2.0
    return None


def classify_graze(position_at, body: str, relation: str, target: str, interval, lo, hi, *, step_seconds: float = 3600.0):
    """Is the reconstructed in-band `interval` of a POINT contact a GRAZE: the body is inside the 1 degree band yet NEVER reaches the ray level (the signed
    distance to every level of the target keeps one sign throughout)? Independent of the ledger, from the ephemeris alone. Returns a dict (body,
    relation, target, interval, closest approach in degrees and its instant, peak activity = 1 - closest/orb) or None when it is not a graze.

    Conservative by construction: None (so the omission stays an omission) for a span target, for an interval clipped by the horizon whose extension cannot be
    settled (see `_full_stretch`: a clipped stretch is followed beyond the horizon and the proof applies to the whole of it), when any ray level is crossed (a sign change inside the interval), when the
    closest approach is within `GRAZE_MIN_APPROACH_DEG` of a level, or when "no exact crossing" cannot be PROVED (steward VERIFIER-CODEX-2, item 1).

    THE PROOF (not an inference from samples): between two instants t0 < t1 the body's distance to the ray level can change by at most
    VMAX_DPS[body] x (t1 - t0) (the kernel's own per-body speed bound, the same one `contact_reconstruct` relies on). If the level were reached at t* in
    (t0, t1), |d0| <= VMAX (t* - t0) and |d1| <= VMAX (t1 - t*), so |d0| + |d1| <= VMAX (t1 - t0). Hence |d0| + |d1| > VMAX (t1 - t0) PROVES no crossing
    inside that step. A step that does not satisfy it is bisected (the midpoint is evaluated: a sign change or a zero there is a crossing, so None) down to
    `contact_reconstruct.MIN_EXCURSION_SECONDS`; a step still unproved at that floor is NOT a graze (None, the omission raises), whatever the sampling
    showed. The proof is as strong as the speed bound, the same assumption the whole certification carries (`contact_reconstruct.NAMED_LIMIT`)."""
    from datetime import timedelta
    from .window_verifier import _ASPECT_ANGLES, _POINT_ORB_DEG
    kind, _, arg = target.partition(":")
    if kind != "point" or relation not in ("conjunction", "aspect"):
        return None
    a, b = interval
    lam = float(arg) % 360.0
    angles = (0.0,) if relation == "conjunction" else _ASPECT_ANGLES[body]
    levels = [(lam - ang) % 360.0 for ang in angles]
    orb = _POINT_ORB_DEG[relation]
    clipped = []
    horizon_interval = (a, b)
    if a <= lo or b >= hi:
        # A stretch CLIPPED by the horizon (steward VERIFIER-CODEX-3, item 2). The builder decides from the WHOLE stretch: it mints a contact (clipped, no
        # exact instant when the crossing is outside) iff the ray level is crossed ANYWHERE in the stretch, inside the horizon or not. So the stretch is
        # followed beyond the horizon edge(s) it is clipped at, from the ephemeris (available outside the horizon, and outside the builder's own
        # arc-index domain), to its true band exits, and the same proof is applied to ALL of it. A crossing that exists only outside the builder's domain is
        # an omission too (the builder could not see it, the contact exists): it is not a graze and raises.
        full = _full_stretch(position_at, body, levels, orb, a, b, lo, hi)
        if full is None:
            return None                                        # the extension could not be settled: never classified
        a, b = full
        clipped = [x for x, hit in (("start", horizon_interval[0] <= lo), ("end", horizon_interval[1] >= hi)) if hit]
    n = max(3, int((b - a).total_seconds() // step_seconds) + 2)
    times = [a + (b - a) * k / (n - 1) for k in range(n)]
    lons = [float(position_at(body, t)) for t in times]
    best = None
    for lv in levels:
        d = [((x - lv + 180.0) % 360.0) - 180.0 for x in lons]
        if min(abs(v) for v in d) > orb + 1e-9:
            continue                                           # this ray's band is not the one the interval belongs to
        if min(d) <= 0.0 <= max(d):
            return None                                        # the ray level is reached: an exact crossing exists, not a graze
        if not all(_no_crossing_proved(position_at, body, lv, times[i], d[i], times[i + 1], d[i + 1]) for i in range(n - 1)):
            return None                                        # a crossing cannot be excluded between two samples: not a graze, the omission raises
        k = min(range(n), key=lambda i: abs(d[i]))
        if best is None or abs(d[k]) < best[0]:
            best = (abs(d[k]), times[k], lv)
    if best is None or best[0] < GRAZE_MIN_APPROACH_DEG:
        return None
    out = {"body": body, "relation": relation, "target": target, "level_deg": round(best[2], 4),
           "interval": [a.isoformat(), b.isoformat()], "closest_approach_deg": round(best[0], 4),
           "closest_approach_at": best[1].isoformat(), "peak_activity": round(1.0 - best[0] / orb, 4)}
    if clipped:
        out["clipped_by_horizon"] = clipped                     # the interval above is the WHOLE stretch; the horizon part is `horizon_interval`
        out["horizon_interval"] = [horizon_interval[0].isoformat(), horizon_interval[1].isoformat()]
    return out


def compare_contact_sets(position_at, body: str, relation: str, target: str, want, have, lo, hi, graze_sink=None) -> list[str]:
    """Compare the reconstructed in-geometry intervals `want` with the ledger's contacts `have` — [(t_in, t_out, accuracy_deg)]
    clipped to [lo, hi) — for ONE (body, relation, target). Returns the problems (empty = they agree).

    The ledger's contacts are the BUILDER's episodes: on a retrograde loop the solver emits one episode per branch, so
    they may OVERLAP (Saturn, October 2025: one episode for the direct pass and one for the retrograde pass, the retrograde
    one ending at an arc seam inside the band) where the reconstruction gives the maximal in-geometry interval. What is
    certified is therefore the UNION of the ledger's contacts: it must equal the reconstructed set, interval for interval
    (the two sequences pair up boundary for boundary, every union boundary compared with a DERIVED tolerance —
    `boundary_match` — never a constant in seconds). A seam between overlapping episodes lies inside the union and is
    not a boundary of the contact SET, so it is not (and must not be) required to sit on an edge."""
    label = f"{body} {relation} {target}"
    problems: list[str] = []
    if graze_sink is not None:
        # INTERIM (steward GRAZE-INTERIM), only when the caller holds a VALIDATED test-slice marker: an in-band interval with NO ledger contact touching it and
        # NO exact crossing of any ray level (a graze: the builder mints a point contact only around an exact root) is REPORTED into `graze_sink` instead
        # of raised; every other difference still raises. Without a sink (any full build, the verification job) nothing changes.
        kept = []
        for w in want:
            if not any(h[0] < w[1] and w[0] < h[1] for h in have):
                g = classify_graze(position_at, body, relation, target, w, lo, hi)
                if g is not None:
                    graze_sink.append(g)
                    continue
            kept.append(w)
        want = kept
    acc = max([h[2] for h in have] or [bm.DEFAULT_ACCURACY_DEG])
    union = _merge([(h[0], h[1]) for h in have])

    def same(w, h):
        return bm.intervals_agree(position_at, body, h, w, acc, lo, hi)
    if not (len(want) == len(union) and all(same(w, h) for w, h in zip(want, union))):
        for w in want:
            if not any(same(w, h) for h in union):
                problems.append(f"{label}: expected contact [{w[0].isoformat()}, {w[1].isoformat()}) is not in the ledger "
                                "(omitted, bridged or truncated)")
        for h in union:
            if not any(same(w, h) for w in want):
                problems.append(f"{label}: ledger contact [{h[0].isoformat()}, {h[1].isoformat()}) is not a reconstructed "
                                "interval (invented, or its support differs)")
        if not problems:
            problems.append(f"{label}: {len(union)} ledger contact interval(s) vs {len(want)} reconstructed — the two "
                            "sequences do not pair up boundary for boundary")
    return problems


def certify_contact_geometry(conn, *, chart_id: str, generation: str, event_class: str, position_at, graze_sink=None) -> dict:
    """Compare the ledger's contacts with the reconstructed ones for every concrete transit obligation of the class."""
    from .inventory_verifier import Unverifiable
    if position_at is None:
        raise cr.GeometryUnavailable("no ephemeris position source: the complete contact set cannot be certified")
    hdr = conn.execute("SELECT lower(horizon), upper(horizon) FROM public.ka_gochara_search_inventory"
                       " WHERE chart_id = %s AND generation = %s AND event_class = %s",
                       (chart_id, generation, event_class)).fetchone()
    if hdr is None:
        raise Unverifiable(f"{event_class}: no inventory horizon to certify the contact set over")
    lo, hi = (tuple(hdr.values()) if isinstance(hdr, dict) else tuple(hdr))
    obligations = {(r[0], r[1], r[2]) for r in (tuple(x.values()) if isinstance(x, dict) else tuple(x)
                   for x in conn.execute(
        "SELECT o.agent, o.relation, o.target FROM public.ka_gochara_search_obligation o"
        " JOIN public.ka_gochara_search_path_pin p ON (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)"
        "   = (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version) AND p.disposition = 'included'"
        " WHERE o.chart_id = %s AND o.generation = %s AND o.event_class = %s", (chart_id, generation, event_class)
    ).fetchall())}
    concrete = sorted((a, r, t) for a, r, t in obligations
                      if not a.startswith("period_lord:") and r in _TRANSIT and a != "moon")
    ledger: dict[tuple, list[tuple]] = {}
    for body, rel, target, t_in, t_out, dl in (tuple(x.values()) if isinstance(x, dict) else tuple(x) for x in conn.execute(
            "SELECT c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out, c.delta_lambda"
            " FROM public.ka_gochara_contact c"
            " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id"
            " WHERE c.chart_id = %s AND c.generation = %s", (chart_id, generation)).fetchall()):
        ledger.setdefault((body, rel, target), []).append(
            (max(t_in, lo), hi if t_out is None else min(t_out, hi), bm.accuracy_degrees(dl)))
    problems: list[str] = []
    expected_total = 0
    for agent, relation, target in concrete:
        want = expected_intervals(position_at, agent, relation, target, lo, hi)
        have = sorted(ledger.get((agent, relation, target), []))
        expected_total += len(want)
        problems.extend(compare_contact_sets(position_at, agent, relation, target, want, have, lo, hi, graze_sink=graze_sink))
    if problems:
        raise RuntimeError(f"contact geometry certification failed {event_class}: " + "; ".join(problems))
    return {"obligations_certified": len(concrete), "contacts_expected": expected_total,
            **({"grazes": list(graze_sink)} if graze_sink is not None else {}),
            "guarantee_assumption": cr.GUARANTEE_ASSUMPTION, "named_limit": cr.NAMED_LIMIT,
            "boundary_tolerance": BOUNDARY_TOLERANCE_STATEMENT}


__all__ = ["BOUNDARY_TOLERANCE_STATEMENT", "GRAZE_MIN_APPROACH_DEG", "certify_contact_geometry", "classify_graze", "compare_contact_sets", "expected_intervals"]
