"""Contact materialisation for the '5.0' writer (Pravāha A5.3,
interval_sweep) — the PURE core: no DB, no ephemeris calls of its own.

Given the enumerated RecordEdges of a grain (evaluator.py) and the body's
boundary crossings (the A2 global boundary table — sky events per body,
joined to targets afterwards per §6.2 inv 5), derive the edge's contact
occurrences and mint one record per occurrence:

  * residence on span:<X> — a span is [ingress into X, egress). Between
    two CONSECUTIVE crossings the body crosses no boundary, so the resided
    sign is constant over the interval and is decided by ONE position probe
    at the interval's midpoint (`position_at`, injected — this module never
    calls an ephemeris itself). This handles every case uniformly: direct
    passage, retrograde re-entry across the SAME boundary (equal consecutive
    levels — ambiguous without a probe, never guessed), and the 0° seam.
  * aspect on span:<X> (aspect-to-span, evaluator E8: "the aspect point's ingress into the span") —
    each special-dṛṣṭi angle (SPECIAL_DRISHTI_DEG, BPHS ch.26; nodes cast none, N-14) is a whole
    number of signs, so a body aspects sign X exactly while it RESIDES in a source sign
    X − angle/30 (mod 12). The occurrences are the maximal CONTIGUOUS runs of the body's residence
    spans over those source signs (union within an agent: a body that passes straight from one
    source sign into the next is aspecting continuously — one occurrence), labelled with the target
    sign. They inherit the residence derivation's half-open [t_in, t_out) intervals, its
    multi-revolution handling (every crossing of the full-domain crossing set) and its N3
    truncation flags.
  * horizon truncation: a span whose ingress lies outside the horizon is
    TRUNCATED (t_exact NULL, N3; solver_method 'clipped_truncated' per
    kgc_solver_method_ck) — kept as a span, never treated as absence
    (Tier-0-G truncated_contacts_kept). Endpoint occupancy comes from one
    probe at the horizon instant; without `position_at` NO span is emitted
    (unknown is recorded in coverage, never fabricated).
  * occurrence ordinals: assigned over the FULL-domain ordered span set of
    the physical object (R3 amendment 1 — append-only stable; a clipped
    partition never renumbers), truncated spans ordering by clipped start.

Record minting (E7): record_id = evaluator.record_uuid over the canonical
natural key with contact_id bound (transit) or None (natal fact).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence

from services.gochara_rules.frames import SIGNS, sign_of
from . import targets
from .convention import SPECIAL_DRISHTI_DEG
from .evaluator import RecordEdge, record_uuid
from .substrate import PhysicalObjectId, SubstrateContact

SOLVER_CLIPPED = "clipped_truncated"
SOLVER_REFINED = "swiss_refined"


@dataclass(frozen=True)
class BoundaryCrossing:
    """One sign-boundary crossing of a body (a sign_ingress sky event,
    reduced to what the join needs)."""

    t: datetime
    level_deg: float          # the boundary crossed (0, 30, …, 330)


@dataclass(frozen=True)
class ResidenceSpan:
    """One residence span of a body in a sign — half-open [t_in, t_out)
    (§4.0 interval convention). t_exact is the ingress instant, None when
    the span is truncated at the horizon's start (N3)."""

    sign: str
    t_in: datetime            # clipped to the horizon
    t_out: datetime | None    # None ⇒ truncated at the horizon's end
    t_exact: datetime | None  # ingress instant; None ⇒ truncated at start
    truncated: bool

    @property
    def solver_method(self) -> str:
        return SOLVER_CLIPPED if self.truncated else SOLVER_REFINED


def _mid(a: datetime, b: datetime) -> datetime:
    return a + (b - a) / 2


def residence_spans(
    crossings: Sequence[BoundaryCrossing],
    *,
    horizon: tuple[datetime, datetime],
    position_at: Callable[[datetime], float] | None = None,
) -> list[ResidenceSpan]:
    """All residence spans (every sign) of one body over the horizon,
    derived from its ordered sign-boundary crossings.

    One `position_at` probe per interval decides the resided sign (midpoint
    for interior intervals, the horizon instant for the edge intervals).
    Without it, nothing is emitted — unknown, never fabricated.
    """
    if position_at is None:
        return []
    h_start, h_end = horizon
    inside = sorted(
        (c for c in crossings if h_start <= c.t < h_end),
        key=lambda c: c.t,
    )
    spans: list[ResidenceSpan] = []

    # Leading edge: h_start → first crossing (truncated ingress).
    first_out = inside[0].t if inside else None
    lead_end = first_out if first_out is not None else None
    spans.append(ResidenceSpan(
        sign=sign_of(position_at(h_start) % 360.0),
        t_in=h_start, t_out=lead_end, t_exact=None, truncated=True))

    # Interior: crossing_i → crossing_{i+1}, ingress exact at crossing_i.
    for prev, nxt in zip(inside, inside[1:]):
        spans.append(ResidenceSpan(
            sign=sign_of(position_at(_mid(prev.t, nxt.t)) % 360.0),
            t_in=prev.t, t_out=nxt.t, t_exact=prev.t, truncated=False))

    # Trailing edge: last crossing → h_end (truncated egress).
    if inside:
        last = inside[-1]
        spans.append(ResidenceSpan(
            sign=sign_of(position_at(h_end) % 360.0),
            t_in=last.t, t_out=None, t_exact=last.t, truncated=True))
    return spans


def aspect_source_signs(body: str, target_sign_index: int) -> frozenset[int]:
    """0-based sign indexes whose residents aspect sign `target_sign_index` (0-based): each
    special-dṛṣṭi angle of `body` shifts a whole number of signs (all pinned angles are multiples
    of 30°), so the source of an aspect onto X is X − angle/30 (mod 12). Nodes: empty (N-14)."""
    out = set()
    for angle in SPECIAL_DRISHTI_DEG.get(body.title(), []):
        if angle % 30.0:
            raise ValueError(f"{body}: dṛṣṭi angle {angle}° is not a whole number of signs — "
                             "the sign-based aspect derivation does not apply")
        out.add((target_sign_index - int(angle // 30.0)) % 12)
    return frozenset(out)


def aspect_spans(
    body_spans: Sequence[ResidenceSpan], *, body: str, target_sign: str,
) -> list[ResidenceSpan]:
    """The aspect-to-span occurrences of `body` onto `target_sign` over the span set's domain:
    the maximal CONTIGUOUS runs (equal consecutive crossing instants — the same boundary event)
    of the body's residence spans over the aspect source signs, labelled with the TARGET sign.

    `t_exact` is the ingress into the first source sign of the run (None when the run starts at
    the domain's start — truncated, N3); `t_out` is the egress from the last (None when it runs
    to the domain's end). A body that leaves a source sign for a non-source sign and later
    returns (retrograde loops, ordinary revolutions) yields separate occurrences."""
    target_idx = [n.lower() for n in targets.SIGN_NAMES].index(target_sign.lower())
    sources = {SIGNS[i].lower() for i in aspect_source_signs(body, target_idx)}
    if not sources:
        return []
    mine = sorted((s for s in body_spans if s.sign.lower() in sources), key=lambda s: s.t_in)
    runs: list[list[ResidenceSpan]] = []
    for span in mine:
        if runs and runs[-1][-1].t_out is not None and runs[-1][-1].t_out == span.t_in:
            runs[-1].append(span)
        else:
            runs.append([span])
    label = SIGNS[target_idx]
    return [
        ResidenceSpan(
            sign=label, t_in=run[0].t_in, t_out=run[-1].t_out, t_exact=run[0].t_exact,
            truncated=run[0].truncated or run[-1].truncated)
        for run in runs]


def spans_for_object(
    spans: Sequence[ResidenceSpan],
    obj: PhysicalObjectId,
) -> list[SubstrateContact]:
    """The contact occurrences of one residence object (body × span:<X>):
    ordinals 1..N over the FULL-domain ordered span set (R3 amendment 1 —
    truncated spans order by their clipped start; append-only stable)."""
    sign = targets.span_sign_name(obj.canonical_target)
    mine = sorted(
        (s for s in spans if s.sign.lower() == sign.lower()),
        key=lambda s: s.t_in,
    )
    return [
        SubstrateContact(
            physical_object_id=obj,
            occurrence_ordinal=i,
            t_exact=s.t_exact,
        )
        for i, s in enumerate(mine, start=1)
    ]


def mint_transit_records(
    edge: RecordEdge,
    spans: Sequence[ResidenceSpan],
    *,
    chart_id: str,
    generation: str,
    prerequisites: list[list[str]],
) -> list[dict]:
    """One record per contact occurrence of a transit residence edge.
    Returns dicts: {natural_key, record_id, contact, span}."""
    assert edge.transit and (
        edge.relation == "residence"
        or (edge.relation == "aspect" and edge.obj.canonical_target.startswith("span:"))), (
        f"mint_transit_records: {edge.relation} edge on {edge.obj.canonical_target} — only "
        "residence spans and aspect-to-span spans materialise through this path (point "
        "conjunction/aspect solve per the boundary solver; natal facts mint directly)")
    sign = targets.span_sign_name(edge.obj.canonical_target)
    mine = sorted(
        (s for s in spans if s.sign.lower() == sign.lower()),
        key=lambda s: s.t_in,
    )
    contacts = spans_for_object(spans, edge.obj)
    out = []
    for contact in contacts:
        span = mine[contact.occurrence_ordinal - 1]
        key = edge.natural_key(
            chart_id=chart_id, generation=generation,
            contact_id=str(contact.contact_id),
            prerequisites=prerequisites, source_text=edge.source_text)
        out.append({
            "natural_key": key,
            "record_id": record_uuid(key),
            "contact": contact,
            "span": span,
        })
    return out


def mint_natal_record(
    edge: RecordEdge,
    *,
    chart_id: str,
    generation: str,
    prerequisites: list[list[str]],
) -> dict:
    """A natal-fact edge (transit=False): one record, contact_id NULL
    (kgrr transit rows carry the NOT NULL; natal rows never solve)."""
    assert not edge.transit, "natal minting is for transit=False edges only"
    key = edge.natural_key(
        chart_id=chart_id, generation=generation, contact_id=None,
        prerequisites=prerequisites, source_text=edge.source_text)
    return {"natural_key": key, "record_id": record_uuid(key),
            "contact": None, "span": None}


__all__ = [
    "BoundaryCrossing",
    "aspect_source_signs",
    "aspect_spans",
    "ResidenceSpan",
    "mint_natal_record",
    "mint_transit_records",
    "residence_spans",
    "spans_for_object",
]
