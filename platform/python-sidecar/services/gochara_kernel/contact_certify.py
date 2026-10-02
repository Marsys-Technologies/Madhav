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
    "station (|speed| < 1e-3 deg/day) the comparison is in angle, |dlon| <= accuracy + the reconstruction's location error")


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


def certify_contact_geometry(conn, *, chart_id: str, generation: str, event_class: str, position_at) -> dict:
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

        def same(w, h, _a=agent):
            # the tolerance is DERIVED (R9-9): the stored contact's own stated angular accuracy and the body's speed at
            # that instant; at a station the comparison is made in angle — never a constant in seconds
            return bm.intervals_agree(position_at, _a, (h[0], h[1]), w, h[2], lo, hi)
        positional = len(want) == len(have) and all(same(w, h) for w, h in zip(want, have))
        if positional:
            continue
        for w in want:
            if not any(same(w, h) for h in have):
                problems.append(f"{agent} {relation} {target}: expected contact [{w[0].isoformat()}, {w[1].isoformat()}) "
                                "is not in the ledger (omitted, bridged or truncated)")
        for h in have:
            if not any(same(w, h) for w in want):
                problems.append(f"{agent} {relation} {target}: ledger contact [{h[0].isoformat()}, {h[1].isoformat()}) "
                                "is not a reconstructed interval (invented, or its support differs)")
        if not problems or all(not p.startswith(f"{agent} {relation} {target}") for p in problems):
            problems.append(f"{agent} {relation} {target}: {len(have)} ledger contact(s) vs {len(want)} reconstructed — "
                            "the two sequences do not pair up boundary for boundary")
    if problems:
        raise RuntimeError(f"contact geometry certification failed {event_class}: " + "; ".join(problems))
    return {"obligations_certified": len(concrete), "contacts_expected": expected_total,
            "guarantee_assumption": cr.GUARANTEE_ASSUMPTION, "named_limit": cr.NAMED_LIMIT,
            "boundary_tolerance": BOUNDARY_TOLERANCE_STATEMENT}


__all__ = ["BOUNDARY_TOLERANCE_STATEMENT", "certify_contact_geometry", "expected_intervals"]
