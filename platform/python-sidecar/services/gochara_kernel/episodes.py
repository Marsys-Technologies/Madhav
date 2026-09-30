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
  residence spans, never point contacts (residence_spans below). A residence
  span's entry/exit instants are coherent refined boundary events: every
  revolution band intersecting a segment is enumerated (R3), each edge
  crossing is refined directly (or reused from the caller's per-body
  boundary roots, R5) — never joined to a differently refined root by a
  sub-second timestamp match (R2). A retrograde body enters through the
  UPPER edge (N2) and the ingress episode names the boundary actually
  crossed. A span clipped at the horizon start whose true ingress lies
  outside carries t_exact=None / exact_crossing=False with
  truncated_at_horizon='start' (N3/O-SS-3 — never a fabricated ingress
  instant at the clip edge); a span clipped at BOTH edges keeps 'both' on
  both of its rows (the ingress episode and the residence row).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .arcs import ArcIndex, MonotoneArc, _refine_boundary
from .contacts import (
    BOUNDARY_RELATIONS,
    ContactRoot,
    _levels_for_relation,
    _refine_root,
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
    level_deg: float            # effective longitude reached (target−aspect mod 360)
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
    completeness_state: str            # 'applied' | 'unqualified' (F06 six-state set)
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


def _augment_open_edge_flag(
    flag: str | None,
    ci0: float,
    ci1: float,
    horizon: tuple[float, float],
    open_start: bool,
    open_end: bool,
) -> str | None:
    """Fold an unresolved knot-edge interval end into the truncation mark.

    An in-orb interval (or residence span) that reaches the END of the fitted
    knots without an observed exit crossing is OPEN: the true exit lies beyond
    the data. When the horizon ends there too, _clip_to_horizon sees
    t_out == h1 and reports no truncation — the contact would look complete.
    O-SS-3/F11-F12: such a span is truncated at 'end' (never absent, never a
    fabricated exact). Mirror rule for an open entry at the first knot and
    the horizon start.
    """
    h0, h1 = horizon
    marks: set[str] = set()
    if flag == "both":
        marks.update(("start", "end"))
    elif flag is not None:
        marks.add(flag)
    if open_start and ci0 <= h0 + 1e-9:
        marks.add("start")
    if open_end and ci1 >= h1 - 1e-9:
        marks.add("end")
    if not marks:
        return None
    if marks == {"start"}:
        return "start"
    if marks == {"end"}:
        return "end"
    return "both"


def build_episodes(
    index: ArcIndex,
    body: str,
    relation: str,
    target_deg: float,
    roots: list[ContactRoot],
    horizon: tuple[float, float],
    orb_source: str,
    orb_override_deg: float | None = None,
) -> list[Episode]:
    """Episodes for one (body, target, relation) at the declared orb.

    `roots` are the Swiss-refined exact-separation roots (contacts.find_roots
    with refine=True); every root must come from the arc index (the candidate
    set is auditable, not a black box).

    `orb_override_deg` (additive, default None): enumerate the in-orb band at
    this width instead of ORB_TABLE[orb_source]. The pinned table is NEVER
    mutated; the override rides the episode's orb_max_deg stamp while
    orb_source still names the §7 relation-class row id. WP10 step-6 use:
    M-1's ratified candidate-1 enumeration orb (linear_no_box × 5.0°) is a
    build parameter, not a re-pin of the table (brief §12.2).
    """
    if orb_source not in ORB_TABLE:
        raise ValueError(f"unknown orb_source {orb_source!r}")
    stamps = _episode_stamps(body, relation, orb_source)
    if orb_override_deg is not None:
        stamps["orb_max_deg"] = float(orb_override_deg)
    orb = stamps["orb_max_deg"]

    # Group roots by their effective level (dṛṣṭi angles each own a level).
    # R4: the level set comes from the RELATION's candidate levels
    # (contacts._levels_for_relation), not from the found roots — an in-orb
    # approach whose exact root lies outside the fitted knots (or never quite
    # reaches exactness) has no root at all yet still owns an in-orb interval
    # that must be emitted as a truncated/no-exact episode, never as absence
    # (N3/O-SS-3).
    by_level: dict[float, dict] = {}
    for aspect, level in _levels_for_relation(body, relation, target_deg):
        by_level[round(level, 6)] = {"aspect": aspect, "roots": []}
    for r in roots:
        by_level[round(r.level_deg, 6)]["roots"].append(r)

    episodes: list[Episode] = []
    data_start = float(index.knot_jds[0])
    data_end = float(index.knot_jds[-1])
    for level, entry in sorted(by_level.items()):
        aspect_deg = entry["aspect"]
        level_roots = entry["roots"]
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
                flag = _augment_open_edge_flag(
                    flag, t_in, t_out, horizon,
                    open_start=i0 <= data_start + 1e-9,
                    open_end=i1 >= data_end - 1e-9,
                )
                has_station = any(
                    t_in - 1e-9 <= s <= t_out + 1e-9 for s in index.stations
                )
                episodes.append(
                    Episode(
                        body=body,
                        relation=relation,
                        aspect_deg=aspect_deg,
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
                        completeness_state="applied" if has_station else "unqualified",
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
                flag = _augment_open_edge_flag(
                    flag, ci0, ci1, horizon,
                    open_start=k == 0 and i0 <= data_start + 1e-9,
                    open_end=k == len(inside) - 1 and i1 >= data_end - 1e-9,
                )
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
                            "unqualified" if unresolved else "applied"
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
    orb_override_deg: float | None = None,
) -> list[Episode]:
    """End-to-end: bracket roots on the arc index, refine by direct Swiss
    bisection at the instant, assemble episodes at the declared orb.

    `refine=False` keeps the spline-stage instants (synthetic-fixture use:
    the cubic is reproduced exactly, so the spline root IS the exact root).
    `orb_override_deg` passes through to build_episodes (additive; the pinned
    ORB_TABLE is never mutated)."""
    roots = find_roots(index, body, relation, target_deg, ephe_path, refine=refine)
    return build_episodes(index, body, relation, target_deg, roots, horizon,
                          orb_source, orb_override_deg=orb_override_deg)


def solve_boundary_episodes(
    index: ArcIndex,
    body: str,
    relation: str,
    horizon: tuple[float, float],
    ephe_path: str | None = None,
    refine: bool = True,
    roots: list[ContactRoot] | None = None,
) -> list[Episode]:
    """Boundary-exact ingress episodes (WP1 §7 orb_ingress): t_in = t_exact =
    t_out at the grid edge, no orb, never dropped at the horizon edge when the
    root falls inside it (closed interval — Codex v1.1 amendment 3 / R2Q3:
    "the domain start at 0 is a real crossing", so a root exactly AT the
    horizon start is INCLUDED; the 1e-9 slack absorbs float noise at either
    edge).

    `roots` (optional): pre-solved boundary roots for (body, relation) — the
    caller's per-body global boundary table (R5). When supplied, no solving
    happens here; the episodes are assembled from those exact roots.
    `refine=False` keeps the spline-stage instants (synthetic-fixture use —
    the same additive escape hatch solve_episodes/residence_spans already
    carry; the pinned default stays Swiss-refined)."""
    if relation not in BOUNDARY_RELATIONS:
        raise ValueError(f"{relation!r} is not a boundary relation")
    if roots is None:
        roots = find_boundary_roots(index, body, relation, ephe_path, refine=refine)
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
                completeness_state="unqualified" if unresolved else "applied",
                near_station_unresolved=unresolved,
                spline_exact_jd=root.spline_exact_jd,
                **stamps,
            )
        )
    episodes.sort(key=lambda e: e.t_exact)
    return episodes


# ── residence spans (M-5 interval objects for sign-level targets) ────────────

def _match_boundary_root(
    boundary_roots: list[ContactRoot] | None,
    level_w: float,
    spline_jd: float,
    direction: int,
) -> ContactRoot | None:
    """The shared per-body boundary event for this span-edge crossing, when the
    caller supplied the body's solved boundary roots (R5: residence REUSES the
    same refined events, never re-solves them). EXPLICIT crossing association
    (A2.2 amendment 4): level (mod 360), direction, and STRUCTURAL containment
    — the crossing's spline instant lies inside the root's own bracket arc —
    never a timestamp-tolerance join (the 1e-3-day join missed real matches
    when the two spline brackets disagreed by >86 s at ordinary tolerance)."""
    if not boundary_roots:
        return None
    matches = []
    for r in boundary_roots:
        if r.arc.direction != direction:
            continue
        if ((r.level_deg - level_w) % 360.0) > 1e-6 and \
                ((level_w - r.level_deg) % 360.0) > 1e-6:
            continue
        lo, hi = r.bracket
        if lo - 1e-9 <= spline_jd <= hi + 1e-9:
            matches.append(r)
    if not matches:
        return None
    if len(matches) > 1:
        # A crossing exactly at a wrap cut is contained by both adjacent arcs;
        # the roots list holds one deduped root per physical crossing, so this
        # can only be a defect — take the nearest spline instant and never
        # invent a merge.
        matches.sort(key=lambda r: abs(r.spline_exact_jd - spline_jd))
    return matches[0]


def residence_spans(
    index: ArcIndex,
    body: str,
    span: tuple[float, float],
    horizon: tuple[float, float],
    target_type: str,
    ephe_path: str | None = None,
    refine: bool = True,
    boundary_roots: list[ContactRoot] | None = None,
) -> list[ResidenceSpan]:
    """Whole-sign (or any ≤30°) residence intervals — interval targets per
    M-5: residence spans and sign-ingress episodes, NEVER point contacts.
    The stored arudha longitude is a sign-cusp placeholder (F-20), so an
    arudha-typed target must arrive here as its sign span, never as a point
    (the WP1 §2.2 resolution contract is the caller's job; this function
    refuses point-shaped input by construction — it only accepts spans).

    Geometry discipline (Pravāha A2 rework, R2/R3):
      * EVERY revolution band intersecting a segment is enumerated (R3 — a
        station-bounded segment can span several revolutions; choosing one
        band from the segment midpoint loses repeated residences).
      * Entry/exit instants are ONE coherent refined boundary event each
        (R2): the spline crossing of the actual span edge is Swiss-refined
        directly (or reused from the caller's per-body boundary roots — R5),
        never joined to a differently refined root by a sub-second timestamp
        match. A rising body enters at the LOWER edge lo_w, a falling
        (retrograde) body enters at the UPPER edge hi_w (N2), and the ingress
        episode carries the boundary actually crossed (Kimi review #1: a
        retrograde entry through 30° says 30°, never 0°).
      * A span clipped at the horizon start (true ingress outside the
        horizon) keeps t_exact=None / exact_crossing=False with
        truncated_at_horizon='start' (N3/O-SS-3 — never a fabricated ingress
        instant at the clip edge); 'both' is preserved verbatim on both rows
        of the span (Kimi review #2 — one physical span, one truncation mark).

    `boundary_roots` (optional): the body's already-solved sign_ingress
    ContactRoots (the step06 global boundary table); span edges of whole-sign
    targets are sign cusps, so the entry/exit instants are reused from that
    set when present and refined directly otherwise."""
    lo_w, hi_w = float(span[0]) % 360.0, float(span[1]) % 360.0
    if hi_w == 0.0 and float(span[1]) > float(span[0]):
        # A span ending exactly on the circle's end (e.g. the Pisces
        # whole-sign span (330, 360)) wraps hi to 0 under % 360 and would be
        # wrongly refused; the end of the circle is 360, not 0.
        hi_w = 360.0
    if hi_w <= lo_w:
        raise ValueError(f"span must satisfy lo < hi in [0,360): got {span}")
    width = hi_w - lo_w
    tol_deg = max(index.tolerance_arcsec / 3600.0, 1e-9)

    # Per segment × revolution band: the in-span interval with its edge
    # crossings. entry/exit carry (wrapped boundary level, spline jd, SEGMENT)
    # — each edge keeps the segment that OWNS it, so a span spanning a station
    # still refines its exit against the exit's own segment (A2.2 amendment 1:
    # the pre-fix merge retained the entry segment and refined the exit
    # against it — Mars 2025 [60,90] came out at 84.72° instead of 2 April
    # 90°). None when the body was already inside / never left within the
    # segment. An endpoint sitting exactly ON the edge is an observed crossing
    # at that endpoint (A2.2 amendment 2: a domain start on the boundary is an
    # ingress at day 0, not a null-exact span).
    intervals: list[tuple[float, float, tuple | None, tuple | None]] = []
    for seg in index.segments:
        span_lo = min(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        span_hi = max(seg.start_lon_unwrapped, seg.end_lon_unwrapped)
        rising = seg.direction == 1
        # R3: every revolution band [lo_w+360k, hi_w+360k] meeting the segment.
        k_min = math.ceil((span_lo - lo_w - width) / 360.0 - 1e-9)
        k_max = math.floor((span_hi - lo_w) / 360.0 + 1e-9)
        for k in range(k_min, k_max + 1):
            lo_u = lo_w + 360.0 * k
            hi_u = lo_u + width
            if span_hi < lo_u - 1e-12 or span_lo > hi_u + 1e-12:
                continue
            a = seg.start_jd
            b = seg.end_jd
            entry_crossing: tuple | None = None
            exit_crossing: tuple | None = None
            if rising:
                if span_lo < lo_u + 1e-9:
                    a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo_u, tol_deg)
                    entry_crossing = (lo_w, a, seg)
                if span_hi > hi_u - 1e-9:
                    b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi_u, tol_deg)
                    exit_crossing = (hi_w % 360.0, b, seg)
            else:
                # Falling: the body enters the span at its TOP edge and
                # leaves at its BOTTOM edge.
                if span_hi > hi_u - 1e-9:
                    a = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, hi_u, tol_deg)
                    entry_crossing = (hi_w % 360.0, a, seg)
                if span_lo < lo_u + 1e-9:
                    b = _refine_boundary(index.evaluate, seg.start_jd, seg.end_jd, lo_u, tol_deg)
                    exit_crossing = (lo_w, b, seg)
            intervals.append((a, b, entry_crossing, exit_crossing))
    intervals.sort(key=lambda iv: iv[0])
    merged: list[list] = []
    for iv in intervals:
        if merged and iv[0] <= merged[-1][1] + 1e-9:
            # Contiguous across a station INSIDE the span: the entry stays
            # with the first piece, the exit with the last — WITH ITS OWN
            # segment (amendment 1).
            merged[-1][1] = max(merged[-1][1], iv[1])
            merged[-1][3] = iv[3]
        else:
            merged.append([iv[0], iv[1], iv[2], iv[3]])

    def _refined_edge(crossing: tuple) -> float:
        """One coherent refined boundary event (R2): reuse the shared
        boundary root when supplied (R5), else Swiss-refine the spline
        crossing directly against the crossing's OWN segment. No timestamp
        join between differently refined instants; a bracket that does not
        contain the crossing is a defect and raises, never silently
        mis-refines."""
        level_w, spline_jd, seg = crossing
        if not (seg.start_jd - 1e-9 <= spline_jd <= seg.end_jd + 1e-9):
            raise ValueError(
                f"residence edge crossing at jd {spline_jd} is outside its "
                f"segment [{seg.start_jd}, {seg.end_jd}] — edge provenance "
                "defect, refusing to refine against the wrong bracket")
        root = _match_boundary_root(boundary_roots, level_w, spline_jd, seg.direction)
        if root is not None:
            return root.exact_jd
        if refine:
            jd, _ = _refine_root(body, seg, spline_jd, level_w, ephe_path)
            return jd
        return spline_jd

    spans: list[ResidenceSpan] = []
    h0, h1 = horizon
    data_start = float(index.knot_jds[0])
    data_end = float(index.knot_jds[-1])
    for a, b, entry_crossing, exit_crossing in merged:
        entry_exact = _refined_edge(entry_crossing) if entry_crossing else None
        exit_exact = _refined_edge(exit_crossing) if exit_crossing else None
        raw_a = entry_exact if entry_exact is not None else a
        raw_b = exit_exact if exit_exact is not None else b
        ca, cb, flag, overlaps = _clip_to_horizon(raw_a, raw_b, horizon)
        if not overlaps:
            continue
        # O-SS-3/F12: a span whose exit (entry) was never observed because the
        # fitted knots ran out is truncated at the data edge; when the horizon
        # ends (starts) there too, _clip_to_horizon alone reports None.
        flag = _augment_open_edge_flag(
            flag, ca, cb, horizon,
            open_start=entry_crossing is None and a <= data_start + 1e-9,
            open_end=exit_crossing is None and b >= data_end - 1e-9,
        )
        # The ingress is OBSERVED only when its refined instant lies inside
        # the horizon; a crossing before h0 is a clipped span (truncated
        # start), never a fabricated exact stamp (N3).
        ingress_observed = (
            entry_exact is not None and h0 - 1e-9 <= entry_exact <= h1 + 1e-9
        )
        stamps = _episode_stamps(body, "sign_ingress", "orb_ingress")
        if ingress_observed:
            entry_seg = entry_crossing[2]
            entry_root = _match_boundary_root(
                boundary_roots, entry_crossing[0], entry_crossing[1],
                entry_seg.direction)
            if entry_root is not None:
                branch, station_flag, unresolved = classify_branch(index, entry_root)
            else:
                branch, station_flag, unresolved = classify_branch(
                    index,
                    ContactRoot(
                        body=body, relation="sign_ingress",
                        target_deg=entry_crossing[0], aspect_deg=0.0,
                        level_deg=entry_crossing[0],
                        spline_exact_jd=entry_crossing[1],
                        exact_jd=entry_exact,
                        bracket=(entry_seg.start_jd, entry_seg.end_jd),
                        arc=entry_seg,
                    ),
                )
            entry_level = entry_crossing[0]
        else:
            branch, station_flag, unresolved = "direct", False, False
            entry_level = lo_w
        ingress_episode = Episode(
            body=body,
            relation="sign_ingress",
            aspect_deg=0.0,
            target_deg=entry_level,
            level_deg=entry_level,
            t_in=ca,
            t_exact=entry_exact if ingress_observed else None,
            t_out=ca,
            branch=branch,
            station_flag=station_flag,
            exact_crossing=ingress_observed,
            orb_source="orb_ingress",
            dwell_days=0.0,
            # Kimi review #2: one span, one truncation mark — the ingress row
            # carries the SAME mark as the residence row ('start', 'end' or
            # 'both'; never 'both' silently collapsed to 'start', never an
            # 'end' erased to NULL — O-SS-3/F11).
            truncated_at_horizon=flag,
            completeness_state="unqualified" if unresolved else "applied",
            near_station_unresolved=unresolved,
            spline_exact_jd=entry_crossing[1] if entry_crossing else None,
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
