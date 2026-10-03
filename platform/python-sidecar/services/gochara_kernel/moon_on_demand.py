"""Moon / day tier — EPHEMERAL (AM-4, GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5).

The transiting Moon moves ≈13°/day: materialising its boundary events century-wide
would be ≈4.5×10⁵ rows per 250 y, so `ka_gochara_sky_event` refuses it
(kgse_body_domain_ck) and the substrate refuses it by name. A Moon / day query is
instead answered ON DEMAND:

  * the Moon's boundary events (sign / nakṣatra ingress) over the requested interval
    are solved with the kernel's own arcs + Swiss refinement — nothing is persisted;
  * the query writes ONE durable coverage identity, a `moon_on_demand` partition of
    `kala_gochara_coverage` keyed `moon:interval:<start>/<end>` (1081's key shape),
    under the chart lock like any coverage row — distinct from build coverage by
    `partition_kind`, so the sealed generation's manifest digest (computed over the
    build partitions only) never moves, whether the query runs before or after sealing;
  * the answer carries a RECEIPT binding five things — (1) the generation's manifest
    id / digest, (2) the partition key and the `coverage_facts` snapshot it answered
    under, (3) the query interval, (4) the input identity (sky convention + the natal
    fact ids consumed), (5) a result digest over the canonical answer rendering. The
    receipt is RETURNED; it is never written to a ka_gochara family table, no
    membership row is written, and nothing in the sealed generation mutates. Replay =
    re-issue the same interval against the same coverage facts and compare the result
    digest.

Held (AM-4 deferred / AM-8): P6 parent-context and temporal-containment rules — no
P6 annotation, record or window is produced here. Transit-Moon CONTACTS to natal
targets are not part of this query; the partition's `relations_searched` names exactly
what was searched, so the coverage never over-claims.

The Moon's Swiss backend is proven by the kernel's file-level probe on every Moon calc
(knots._assert_moon_file_backend, SS N-28): a Moshier Moon cannot reach this module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import arcs as gk_arcs
from . import contacts as gk_contacts
from .knots import sample_knots
from .substrate import jd_to_utc

#: relation → the event kind the substrate would use (DB_EVENT_KIND vocabulary).
MOON_RELATIONS: tuple[str, ...] = ("sign_ingress", "nakshatra_ingress")
MOON_PARTITION_KIND = "moon_on_demand"
_PAD = timedelta(days=2)   # arcs must bracket a root that lies just inside the edge


@dataclass(frozen=True)
class MoonEvent:
    """One solved Moon boundary event. Ephemeral — never an identity row."""

    relation: str
    level_deg: float
    t_exact: datetime
    solver_method: str          # swiss_refined | arc_index_bracket
    delta_lambda: float         # degrees
    delta_t: float | None       # days (None for an unrefined bracket)
    precision_regime: str


def _utc_z(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_interval(start: datetime, end: datetime) -> None:
    for name, t in (("start", start), ("end", end)):
        if t.tzinfo is None or t.utcoffset() != timedelta(0):
            raise ValueError(f"moon query {name} must be a UTC-aware datetime")
    if not start < end:
        raise ValueError("moon query interval must be non-empty: start < end")
    if (end - start) > timedelta(days=400):
        raise ValueError("moon query interval is on-demand: at most 400 days "
                         "(a longer span is a materialisation request, refused)")


def partition_key(start: datetime, end: datetime) -> str:
    """1081's key shape: `moon:interval:<start>/<end>` (UTC, `Z`)."""
    _require_interval(start, end)
    return f"moon:interval:{_utc_z(start)}/{_utc_z(end)}"


def solve_moon_events(
    start: datetime, end: datetime, *, ephe_path: str | None = None,
    refine: bool = True, index: Any = None,
) -> tuple[list[MoonEvent], Any]:
    """The Moon's sign / nakṣatra ingress events with `start <= t_exact < end`
    (half-open, like every horizon in the family), time-ordered. Returns
    (events, arc_index). `index` may inject a prebuilt ArcIndex (tests)."""
    _require_interval(start, end)
    if index is None:
        ks = sample_knots("Moon", (start - _PAD).date(), (end + _PAD).date(), ephe_path)
        index = gk_arcs.build_arc_index("Moon", ks.knot_jds, ks.longitudes_deg)
    solver_method = "swiss_refined" if refine else "arc_index_bracket"
    precision_regime = (
        "swiss_bisect_tol_1e-9d" if refine
        else f"arc_index_bracket_{index.tolerance_arcsec}arcsec")
    delta_lambda = index.tolerance_arcsec / 3600.0
    delta_t = 1e-9 if refine else None
    events: list[MoonEvent] = []
    for relation in MOON_RELATIONS:
        for root in gk_contacts.find_boundary_roots(
                index, "Moon", relation, ephe_path, refine=refine):
            t = jd_to_utc(root.exact_jd)
            if start <= t < end:
                events.append(MoonEvent(
                    relation=relation, level_deg=float(root.level_deg) % 360.0,
                    t_exact=t, solver_method=solver_method,
                    delta_lambda=delta_lambda, delta_t=delta_t,
                    precision_regime=precision_regime))
    events.sort(key=lambda e: (e.t_exact, e.relation, e.level_deg))
    return events, index


def coverage_row(
    *, start: datetime, end: datetime, convention_id: str, index: Any,
    build_id: str,
) -> dict[str, Any]:
    """The `moon_on_demand` partition this query owns. It claims exactly what
    was searched: the two boundary relations over every grid level
    (12 sign cusps + 27 nakṣatra cusps), completed over the whole interval."""
    levels = sum(len(gk_contacts.boundary_degrees(r)) for r in MOON_RELATIONS)
    return {
        "partition_kind": MOON_PARTITION_KIND,
        "partition_key": partition_key(start, end),
        "convention_id": convention_id,
        "horizon": (start, end),
        "resolution": float(index.tolerance_arcsec),
        "relations_searched": sorted(MOON_RELATIONS),
        "targets_requested": levels, "targets_resolved": levels,
        "state_counts": {"resolved": levels},
        "unavailable_inputs": {},
        "unsearched_reason": None,
        "build_id": build_id,
    }


def result_rendering(events: list[MoonEvent]) -> str:
    """The canonical answer rendering the result digest covers: sorted keys,
    compact separators, UTC microsecond instants — and NO self-referential or
    audit field (no digest, no receipt, no wall-clock)."""
    return json.dumps(
        [{"relation": e.relation, "level_deg": e.level_deg,
          "t_exact": e.t_exact.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
          "solver_method": e.solver_method, "delta_lambda": e.delta_lambda,
          "delta_t": e.delta_t, "precision_regime": e.precision_regime}
         for e in events],
        sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def result_digest(events: list[MoonEvent]) -> str:
    return "sha256:" + hashlib.sha256(result_rendering(events).encode("utf-8")).hexdigest()


def build_receipt(
    *, manifest: dict[str, Any] | None, key: str, coverage_facts: Any,
    start: datetime, end: datetime, sky_convention_id: str,
    natal_target_fact_ids: list[str], events: list[MoonEvent],
) -> dict[str, Any]:
    """The five-part receipt (AM-4). `manifest` is the generation's published/
    candidate manifest binding ({manifest_id, content_digest, status}) or None
    when the generation has no manifest row — stated, never invented."""
    return {
        "manifest": manifest,
        "coverage": {"partition_kind": MOON_PARTITION_KIND,
                     "partition_key": key, "coverage_facts": coverage_facts},
        "query_interval": [_utc_z(start), _utc_z(end)],
        "input_identity": {"sky_convention_id": sky_convention_id,
                           "natal_target_fact_ids": sorted(natal_target_fact_ids)},
        "result_digest": result_digest(events),
    }


@dataclass(frozen=True)
class MoonQueryResult:
    events: list[MoonEvent]
    coverage: dict[str, Any]
    receipt: dict[str, Any]


def run_moon_query(
    store: Any, *, chart_id: str, generation: str, start: datetime, end: datetime,
    sky_convention_id: str, kala_convention_id: str,
    natal_target_fact_ids: list[str] | None = None, build_id: str = "moon_on_demand",
    ephe_path: str | None = None, refine: bool = True, index: Any = None,
) -> MoonQueryResult:
    """Answer one Moon / day query. The CALLER's transaction holds the chart family
    key (ka_gochara_lock_chart) before this runs — the coverage write is the only
    write. Idempotent: re-issuing the same interval re-derives the same receipt."""
    events, idx = solve_moon_events(start, end, ephe_path=ephe_path,
                                    refine=refine, index=index)
    cov = coverage_row(start=start, end=end, convention_id=kala_convention_id,
                       index=idx, build_id=build_id)
    store.write_moon_coverage(chart_id=chart_id, generation=generation, **{
        k: v for k, v in cov.items() if k not in ("partition_kind",)})
    facts = store.moon_coverage_facts(chart_id=chart_id, generation=generation,
                                      partition_key=cov["partition_key"])
    receipt = build_receipt(
        manifest=store.manifest_binding(chart_id=chart_id, generation=generation),
        key=cov["partition_key"], coverage_facts=facts, start=start, end=end,
        sky_convention_id=sky_convention_id,
        natal_target_fact_ids=list(natal_target_fact_ids or []), events=events)
    return MoonQueryResult(events=events, coverage=cov, receipt=receipt)


__all__ = ["MOON_PARTITION_KIND", "MOON_RELATIONS", "MoonEvent", "MoonQueryResult",
           "build_receipt", "coverage_row", "partition_key", "result_digest",
           "result_rendering", "run_moon_query", "solve_moon_events"]
