"""Episodes: t_in / t_exact / t_out at a declared orb, with branch, dwell,
truncation and honesty flags (plan §4.2; WP1_CONTRACTS.md §7, §9; WP2 pins).

PINNED SEMANTICS (WP2_FIXTURES.md / wp2_geometry.json — the acceptance
fixtures; every rule below is traceable to a pin):

  One episode per exact root (case 01 pinning rule): an in-orb interval
  holding roots r_1..r_n is split at the interior exact roots —
      episode k spans [max(entry, r_{k-1}), min(exit, r_{k+1})]
  so a body that never vacates its orb across a close-station complex yields
  one episode per root with contiguous spans, never one merged blob and never
  dropped re-crossings.

  In-orb interval with NO exact root (E8-2 wrap tangency): emitted, not
  dropped — t_exact=None, exact_crossing=False, branch 'station' when the
  interval contains a station instant (the body turned back inside the orb);
  if it contains no station (knot-edge clipping) the spline cannot certify
  the root count and near_station_unresolved=True propagates
  completeness_state='unqualified' (never a silent boolean — plan §4.2).

  Horizon edges (E8-3, cases 04a/04b): episodes whose orb overlaps the horizon
  are emitted clipped to it — truncated_at_horizon in {'start','end','both'},
  and when t_exact lies outside the horizon the episode carries t_exact=None /
  exact_crossing=False (never dropped, never fabricated inside).

  branch ∈ {direct, retrograde, station} — the WP2-pinned classification:
      'station'    — t_exact within STATION_PROXIMITY_DAYS of a station
                     instant (also sets station_flag and, as an honesty
                     consequence of unresolved root multiplicity near a
                     turnaround, near_station_unresolved)
      'retrograde' — exact crossing on the internal retrograde leg of a
                     station pair (segment direction −1 bounded by stations
                     on BOTH ends). Any real retrograde loop satisfies this;
                     WP2 case 04b pins a bare negative-slope stretch truncated
                     at a horizon edge (station outside the horizon) as
                     'direct', which this rule reproduces.
      'direct'     — everything else.
  For no-exact episodes branch is 'station' when a station instant lies
  inside the episode span (E8-2), else 'direct' with near_station_unresolved.

  dwell_days — pinned by WP2 case 01: episode k dwells from the END of the
  previous episode of the same in-orb interval (its own orb entry for the
  first) until its own end: dwell_k = t_out,k − max(t_in,k, t_out,k−1).
  (Verified against all three case-01 pins: 10.2999 / 3.0 / 7.2999 days; no
  simpler rule fits all three.) For a solitary episode this reduces to
  t_out − t_in, matching cases 03/04a/04b.

  Boundary relations (sign_ingress, nakshatra_ingress, kakshya_cell_crossing)
  are boundary-exact (WP1 §7 orb_ingress): episodes rooted at the span edge
  with t_in = t_exact = t_out and no orb. Sign-level targets (M-5) get
  residence spans, never point contacts (residence_spans below).
"""
from __future__ import annotations

from dataclasses import dataclass

from .arcs import ArcIndex, MonotoneArc, _refine_boundary
from .contacts import (
    BOUNDARY_RELATIONS,
    ContactRoot,
    find_boundary_roots,
    find_roots,
)
from .convention import ORB_TABLE, declared_tolerance

STATION_PROXIMITY_DAYS = 1.0


@dataclass(frozen=True)
class Episode:
    """One contact episode at the declared orb."""

    body: str
    relation: str
    aspect_deg: float
    target_deg: float
    level_deg: float            # effective longitude reached (target+aspect mod 360)
    t_in: float                 # jd
    t_exact: float | None       # jd; None when no exact crossing inside the horizon
    t_out: float                # jd
    branch: str                 # 'direct' | 'retrograde' | 'station'
    station_flag: bool
    exact_crossing: bool
    orb_max_deg: float
    orb_source: str
    dwell_days: float
    truncated_at_horizon: str | None   # 'start' | 'end' | 'both' | None
    tolerance_arcsec: float
    bracket_seconds: int
    completeness_state: str            # 'qualified' | 'unqualified'
    near_station_unresolved: bool
    spline_exact_jd: float | None = None   # diagnostics: spline-stage root


@dataclass(frozen=True)
class ResidenceSpan:
    """M-5 interval object for a sign-level target: the body resides in the
    target's whole-sign span [span_lo_deg, span_hi_deg) for [t_enter, t_exit].
    Interval targets produce residence spans and ingress episodes, never
    point contacts."""

    body: str
    span_lo_deg: float
    span_hi_deg: float
    t_enter: float
    t_exit: float
    truncated_at_horizon: str | None
    ingress_episode: "Episode"


# ── in-orb intervals ─────────────────────────────────────────────────────────

def _segment_band_level(segment: MonotoneArc, level_wrapped: float) -> float:
    """The unwrapped representative of `level_wrapped` nearest the segment's
    longitude range — so a level of 0° tests as 360° inside a segment that
    peaks at 359.9° (the wrap-tangency geometry)."""
    mid = 0.5 * (segment.start_lon_unwrapped + segment.end_lon_unwrapped)
    k = round((mid - float(level_wrapped)) / 360.0)
    return float(level_wrapped) + 360.0 * k


def in_orb_intervals(
    index: ArcIndex,
    level_wrapped_deg: float,
    orb_deg: float,
) -> list[tuple[float, float]]:
    """Merged intervals on the unwrapped curve where |λ(t) − level| ≤ orb.

    Solved per station-bounded monotone segment (the spline is only trusted
    inside its fitted span), so a turnaround INSIDE the orb closes the
    interval at the station rather than leaking through it (E8-2).
    """
    if orb_deg <= 0.0:
        return []
    tol_deg = max(index.tolerance_arcsec / 3600.0, 1e-9)
    intervals: list[tuple[float, float]] = []
    for seg in index.segments:
        level_u = _segment_band_level(seg, level_wrapped_deg)
        lo = level_u - orb_deg
        hi = level_u + orb_deg
        span_lo = min(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        span_hi = max(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        if span_hi < lo - 1e-12 or span_lo > hi + 1e-12:
            continue
        # Entry/exit edges depend on direction: a RISING segment enters at the
        # band's lower edge and leaves at the upper; a FALLING segment enters
        # at the upper edge and leaves at the lower (a retrograde body crosses
        # the orb top first). Missing the direction assigns the whole segment
        # to the wrong side of the band.
        a = seg.start_jd
        b = seg.end_jd
        if seg.direction == 1:
            if span_lo < lo - 1e-12:
                a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo, tol_deg)
            if span_hi > hi + 1e-12:
                b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi, tol_deg)
        else:
            if span_hi > hi + 1e-12:
                a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi, tol_deg)
            if span_lo < lo - 1e-12:
                b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo, tol_deg)
        intervals.append((a, b))
    intervals.sort()
    merged: list[tuple[float, float]] = []
    for a, b in intervals:
        if merged and a <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


# ── branch classification ────────────────────────────────────────────────────

def _nearest_station_distance(index: ArcIndex, jd: float) -> float | None:
    if not index.stations:
        return None
    return min(abs(jd - s) for s in index.stations)


def classify_branch(index: ArcIndex, root: ContactRoot) -> tuple[str, bool, bool]:
    """(branch, station_flag, near_station_unresolved) for a rooted episode."""
    d = _nearest_station_distance(index, root.exact_jd)
    if d is not None and d < STATION_PROXIMITY_DAYS:
        return "station", True, True
    arc = root.arc
    if arc.direction == -1 and arc.station_bounded == (True, True):
        return "retrograde", False, False
    return "direct", False, False


# ── episode assembly ─────────────────────────────────────────────────────────

def _clip_to_horizon(
    t_in: float,
    t_out: float,
    horizon: tuple[float, float],
) -> tuple[float, float, str | None, bool]:
    """Clip [t_in, t_out] to the horizon. Returns (t_in, t_out, truncated,
    overlaps). Episodes with no overlap are dropped by the caller."""
    h0, h1 = horizon
    if t_out < h0 or t_in > h1:
        return t_in, t_out, None, False
    truncated: list[str] = []
    if t_in < h0:
        t_in = h0
        truncated.append("start")
    if t_out > h1:
        t_out = h1
        truncated.append("end")
    flag: str | None
    if not truncated:
        flag = None
    elif len(truncated) == 1:
        flag = truncated[0]
    else:
        flag = "both"  # WP1 §3.1 allows 'start'|'end'|NULL; the kernel keeps
        # the precise 'both' and WP6 maps it at persistence time (documented).
    return t_in, t_out, flag, True


def _episode_stamps(body: str, relation: str, orb_source: str) -> dict:
    orb = ORB_TABLE[orb_source]["orb_max_deg"]
    tol = declared_tolerance(body, relation)
    return {"orb_max_deg": orb, **tol}


def build_episodes(
    index: ArcIndex,
    body: str,
    relation: str,
    target_deg: float,
    roots: list[ContactRoot],
    horizon: tuple[float, float],
    orb_source: str,
) -> list[Episode]:
    """Episodes for one (body, target, relation) at the declared orb.

    `roots` are the Swiss-refined exact-separation roots (contacts.find_roots
    with refine=True); every root must come from the arc index (the candidate
    set is auditable, not a black box).
    """
    if orb_source not in ORB_TABLE:
        raise ValueError(f"unknown orb_source {orb_source!r}")
    stamps = _episode_stamps(body, relation, orb_source)
    orb = stamps["orb_max_deg"]

    # Group roots by their effective level (dṛṣṭi angles each own a level).
    by_level: dict[float, list[ContactRoot]] = {}
    for r in roots:
        by_level.setdefault(round(r.level_deg, 6), []).append(r)

    episodes: list[Episode] = []
    for level, level_roots in sorted(by_level.items()):
        intervals = in_orb_intervals(index, level, orb)
        for (i0, i1) in intervals:
            inside = [r for r in level_roots if i0 - 1e-9 <= r.exact_jd <= i1 + 1e-9]
            inside.sort(key=lambda r: r.exact_jd)
            if not inside:
                # In-orb overlap without an exact root (E8-2 wrap tangency,
                # or a root just outside the fitted knots).
                t_in, t_out, flag, overlaps = _clip_to_horizon(i0, i1, horizon)
                if not overlaps:
                    continue
                has_station = any(
                    t_in - 1e-9 <= s <= t_out + 1e-9 for s in index.stations
                )
                episodes.append(
                    Episode(
                        body=body,
                        relation=relation,
                        aspect_deg=level_roots[0].aspect_deg if level_roots else 0.0,
                        target_deg=float(target_deg) % 360.0,
                        level_deg=level,
                        t_in=t_in,
                        t_exact=None,
                        t_out=t_out,
                        branch="station" if has_station else "direct",
                        station_flag=has_station,
                        exact_crossing=False,
                        orb_source=orb_source,
                        dwell_days=t_out - t_in,
                        truncated_at_horizon=flag,
                        completeness_state="qualified" if has_station else "unqualified",
                        near_station_unresolved=not has_station,
                        **stamps,
                    )
                )
                continue

            # One episode per root, split at interior exact roots (WP2 case 01
            # pinning rule: episode k spans [max(entry, r_{k-1}),
            # min(exit, r_{k+1})]).
            prev_t_out: float | None = None
            for k, root in enumerate(inside):
                t_in = max(i0, inside[k - 1].exact_jd) if k > 0 else i0
                t_out = min(i1, inside[k + 1].exact_jd) if k < len(inside) - 1 else i1
                branch, station_flag, unresolved = classify_branch(index, root)
                ci0, ci1, flag, overlaps = _clip_to_horizon(t_in, t_out, horizon)
                if not overlaps:
                    continue
                h0, h1 = horizon
                exact_inside = h0 - 1e-9 <= root.exact_jd <= h1 + 1e-9
                dwell_base = prev_t_out if prev_t_out is not None else ci0
                episodes.append(
                    Episode(
                        body=body,
                        relation=relation,
                        aspect_deg=root.aspect_deg,
                        target_deg=root.target_deg,
                        level_deg=root.level_deg,
                        t_in=ci0,
                        t_exact=root.exact_jd if exact_inside else None,
                        t_out=ci1,
                        branch=branch,
                        station_flag=station_flag,
                        exact_crossing=exact_inside,
                        orb_source=orb_source,
                        dwell_days=ci1 - max(ci0, dwell_base),
                        truncated_at_horizon=flag,
                        completeness_state=(
                            "unqualified" if unresolved else "qualified"
                        ),
                        near_station_unresolved=unresolved,
                        spline_exact_jd=root.spline_exact_jd,
                        **stamps,
                    )
                )
                prev_t_out = ci1
    episodes.sort(key=lambda e: (e.t_in, e.relation, e.aspect_deg))
    return episodes


def solve_episodes(
    index: ArcIndex,
    body: str,
    relation: str,
    target_deg: float,
    horizon: tuple[float, float],
    orb_source: str,
    ephe_path: str | None = None,
    refine: bool = True,
) -> list[Episode]:
    """End-to-end: bracket roots on the arc index, refine by direct Swiss
    bisection at the instant, assemble episodes at the declared orb.

    `refine=False` keeps the spline-stage instants (synthetic-fixture use:
    the cubic is reproduced exactly, so the spline root IS the exact root)."""
    roots = find_roots(index, body, relation, target_deg, ephe_path, refine=refine)
    return build_episodes(index, body, relation, target_deg, roots, horizon, orb_source)


def solve_boundary_episodes(
    index: ArcIndex,
    body: str,
    relation: str,
    horizon: tuple[float, float],
    ephe_path: str | None = None,
) -> list[Episode]:
    """Boundary-exact ingress episodes (WP1 §7 orb_ingress): t_in = t_exact =
    t_out at the grid edge, no orb, never dropped at the horizon edge when the
    root falls inside it (closed interval)."""
    if relation not in BOUNDARY_RELATIONS:
        raise ValueError(f"{relation!r} is not a boundary relation")
    roots = find_boundary_roots(index, body, relation, ephe_path, refine=True)
    stamps = _episode_stamps(body, relation, "orb_ingress")
    h0, h1 = horizon
    episodes: list[Episode] = []
    for root in roots:
        if not (h0 - 1e-9 <= root.exact_jd <= h1 + 1e-9):
            continue
        branch, station_flag, unresolved = classify_branch(index, root)
        episodes.append(
            Episode(
                body=body,
                relation=relation,
                aspect_deg=0.0,
                target_deg=root.level_deg,
                level_deg=root.level_deg,
                t_in=root.exact_jd,
                t_exact=root.exact_jd,
                t_out=root.exact_jd,
                branch=branch,
                station_flag=station_flag,
                exact_crossing=True,
                orb_source="orb_ingress",
                dwell_days=0.0,
                truncated_at_horizon=None,
                completeness_state="unqualified" if unresolved else "qualified",
                near_station_unresolved=unresolved,
                spline_exact_jd=root.spline_exact_jd,
                **stamps,
            )
        )
    episodes.sort(key=lambda e: e.t_exact)
    return episodes


# ── residence spans (M-5 interval objects for sign-level targets) ────────────

def residence_spans(
    index: ArcIndex,
    body: str,
    span: tuple[float, float],
    horizon: tuple[float, float],
    target_type: str,
    ephe_path: str | None = None,
    refine: bool = True,
) -> list[ResidenceSpan]:
    """Whole-sign (or any ≤30°) residence intervals — interval targets per
    M-5: residence spans and sign-ingress episodes, NEVER point contacts.
    The stored arudha longitude is a sign-cusp placeholder (F-20), so an
    arudha-typed target must arrive here as its sign span, never as a point
    (the WP1 §2.2 resolution contract is the caller's job; this function
    refuses point-shaped input by construction — it only accepts spans)."""
    lo_w, hi_w = float(span[0]) % 360.0, float(span[1]) % 360.0
    if hi_w <= lo_w:
        raise ValueError(f"span must satisfy lo < hi in [0,360): got {span}")
    ingress_roots = [
        r
        for r in find_boundary_roots(index, body, "sign_ingress", ephe_path, refine=refine)
        if abs(r.level_deg - lo_w) < 1e-6
    ]
    spans: list[ResidenceSpan] = []
    tol_deg = max(index.tolerance_arcsec / 3600.0, 1e-9)
    intervals: list[tuple[float, float]] = []
    for seg in index.segments:
        mid = 0.5 * (seg.start_lon_unwrapped + seg.end_lon_unwrapped)
        lo_u = lo_w + 360.0 * round((mid - lo_w) / 360.0)
        hi_u = lo_u + (hi_w - lo_w)
        span_lo = min(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        span_hi = max(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        if span_hi < lo_u - 1e-12 or span_lo > hi_u + 1e-12:
            continue
        a = seg.start_jd
        b = seg.end_jd
        rising = seg.direction == 1
        if rising:
            if span_lo < lo_u - 1e-12:
                a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo_u, tol_deg)
            if span_hi > hi_u + 1e-12:
                b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi_u, tol_deg)
        else:
            # Falling: the body enters the span at its TOP edge and leaves at
            # its BOTTOM edge.
            if span_hi > hi_u + 1e-12:
                a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi_u, tol_deg)
            if span_lo < lo_u - 1e-12:
                b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo_u, tol_deg)
        intervals.append((a, b))
    intervals.sort()
    merged: list[tuple[float, float]] = []
    for a, b in intervals:
        if merged and a <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    for (a, b) in merged:
        ca, cb, flag, overlaps = _clip_to_horizon(a, b, horizon)
        if not overlaps:
            continue
        ingress = next(
            (r for r in ingress_roots if abs(r.exact_jd - ca) < 1e-6), None
        )
        stamps = _episode_stamps(body, "sign_ingress", "orb_ingress")
        ingress_episode = Episode(
            body=body,
            relation="sign_ingress",
            aspect_deg=0.0,
            target_deg=lo_w,
            level_deg=lo_w,
            t_in=ca,
            t_exact=ingress.exact_jd if ingress else ca,
            t_out=ca,
            branch="direct",
            station_flag=False,
            exact_crossing=True,
            orb_source="orb_ingress",
            dwell_days=0.0,
            truncated_at_horizon="start" if flag == "start" else None,
            completeness_state="qualified",
            near_station_unresolved=False,
            spline_exact_jd=ingress.spline_exact_jd if ingress else None,
            **stamps,
        )
        spans.append(
            ResidenceSpan(
                body=body,
                span_lo_deg=lo_w,
                span_hi_deg=hi_w,
                t_enter=ca,
                t_exit=cb,
                truncated_at_horizon=flag,
                ingress_episode=ingress_episode,
            )
        )
    return spans


def attribute_partition(
    episodes: list[Episode],
    partitions: list[tuple[float, float]],
) -> dict[int, list[Episode]]:
    """Attribute each episode to exactly one partition (WP2 case 03 seam
    rule: a contact whose t_exact equals a partition seam belongs to the
    partition whose END it equals — end-closed). Episodes are solved ONCE over
    the whole horizon and attributed, never re-solved per partition (re-solving
    would duplicate or truncate seam episodes)."""
    out: dict[int, list[Episode]] = {i: [] for i in range(len(partitions))}
    for ep in episodes:
        key = ep.t_exact if ep.t_exact is not None else 0.5 * (ep.t_in + ep.t_out)
        owner: int | None = None
        for i, (p0, p1) in enumerate(partitions):
            # Half-open (p0, p1] per partition: the partition whose END
            # equals the key owns it (WP2 case 03 pin). First match wins, so
            # a seam instant lands in the partition that ends there.
            if p0 - 1e-9 < key <= p1 + 1e-9:
                owner = i
                break
        if owner is None:
            raise ValueError(f"episode at {key} belongs to no partition")
        out[owner].append(ep)
    return out


__all__ = [
    "STATION_PROXIMITY_DAYS",
    "Episode",
    "ResidenceSpan",
    "attribute_partition",
    "build_episodes",
    "in_orb_intervals",
    "residence_spans",
    "solve_boundary_episodes",
    "solve_episodes",
]
