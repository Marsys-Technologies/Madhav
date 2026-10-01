"""A5.3 interval_sweep (2/N) — record store: the DB-touching half of contact
materialisation (design v1.1, brief §interval_sweep).

Two substep kinds, each one orchestrator transaction:

  1. `coverage:<event_class>` — write_class_coverage: the class-level
     event_class coverage partition. The frozen F7 guard (1155,
     ka_gochara_record_coverage_guard) pins partition_key = event_class, so
     ONE manifest row per (chart, generation, class) carries the class's
     whole-generation declared search across every bound path — computed
     from the static enumeration (identical from any grain), insert-if-absent
     with a full byte check (pin 4). Runs BEFORE any record grain of the
     class (pin 7, coverage FIRST = existence-before-records).
  2. `record:<event_class>:<path_id>` — materialise_record_grain: the
     contact chain for every minted occurrence (ka_gochara_physical_object
     insert-if-absent, ka_gochara_contact_identity, ka_gochara_contact) and
     the ka_gochara_relationship_record rows (E7 record_id from
     materialise.mint_*). Each record's coverage_facts are computed by the
     DB from the STORED partition row (N10/N14 — the record coverage guard
     byte-compares). A grain whose class partition is missing REFUSES
     (MissingCoverageError) — never an orphaned record.

Scope of THIS slice: `residence` transit edges (spans from the substrate's
sign_ingress sky events — the A2 global boundary table, read-only) and
natal-fact edges (transit=False, contact_id NULL). `aspect` / `conjunction`
transit edges solve through contacts.find_roots in interval_sweep 3/N; the
class coverage names only what ran in relations_searched and the deferral
in unsearched_reason — the edges are never silently dropped and never
minted uncomputed.

Contact-row model (ka_gochara_contact, 1153): coverage.truncated is exactly
"t_exact IS NULL" (kgc_t_exact_iff_truncated_ck). A span clipped at the
horizon START keeps no fabricated ingress (t_exact NULL, solver
'clipped_truncated', N3 / Tier-0-G truncated_contacts_kept). A span clipped
at the horizon END carries its exact ingress with t_out clipped to the
horizon — the occurrence (the ingress) is fully observed; the completed vs
requested horizon is reported on the coverage row (H-3), never by erasing
the span.

Ordinals (R3 amendment 1): spans are derived over the FULL convention
domain (stable, append-only) and only afterwards intersected with the
requested horizon — a clipped partition never renumbers.

temporal_support (spec v1.4 §1 amendment 1): transit rows 'computed' with
grain 'span' (the residence span IS the support interval; no grain
vocabulary is pinned anywhere in the frozen artefacts — named here, a
candidate for the v1.5 batch if Stream B legislates one) and the span as
the single half-open interval; natal-fact rows stay 'uncomputed'
(atemporal claims; precision NULL per §1 / kgrr_transit_natal_ck).

Idempotency (pin 4): every identity-bearing insert is insert-if-absent
followed by a byte-identity check — a collision with a non-identical
stored row is a loud build failure, never a silent dedup.
"""
from __future__ import annotations

import json as _json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence

from . import ledger as gk_ledger
from .evaluator import RecordEdge
from .materialise import (BoundaryCrossing, ResidenceSpan, mint_natal_record,
                          mint_transit_records, residence_spans)
from .substrate import (DB_BODY, SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START,
                        IdentityCollisionError, PhysicalObjectId,
                        SubstrateContact)

SUPPORT_GRAIN_SPAN = "span"
DEFERRAL_POINT_SOLVE = ("aspect/conjunction contact solve lands in "
                        "interval_sweep 3/N (named deferral)")

# The WP1 §1.1 convention vector the kala coverage ledger keys on (the same
# values the '4.1' candidate chain pins in step06_candidate_build.py; the
# '5.0' writer shares the ephemeris/method, so it shares the vector). The
# kala ↔ sky convention mapping is bridged explicitly (F7).
KALA_CONVENTION_VECTOR = {
    "zodiac": "sidereal",
    "ayanamsha": "lahiri_chitrapaksha",
    "sidereal_method": "swe_flg_sidereal",
    "node_model": "mean",
    "node_source": "swiss_mean_node_flg_sidereal",
    "epoch_convention": "noon_ut_knot_abscissa",
    "time_scale": "ut_to_tt_swe_deltat",
    "house_system": "whole_sign",
    "ephemeris_mode": "flg_swieph",
    "method_version": "1.0.0",
}


@dataclass(frozen=True)
class CrossingInfo:
    """One sign_ingress sky event with its solve precision (N7: the record's
    precision restates the contact's, the contact's restates the sky event's)."""

    t: datetime
    level_deg: float
    solver_method: str
    delta_lambda: float | None
    delta_t: float | None
    precision_regime: str | None


def _byte_check(stored: tuple | None, expected: tuple, what: str) -> None:
    if stored is None or tuple(str(x) for x in stored) != tuple(str(x) for x in expected):
        raise IdentityCollisionError(
            f"{what}: stored {stored} != derived {expected}")


class MissingCoverageError(RuntimeError):
    """pin 7: a record grain ran before its class coverage partition."""


class RecordStore:
    """Persistence for one record grain (pin 5) over 1081/1153/1155.

    The caller's transaction holds the chart family key
    (ka_gochara_lock_chart) — the substrate chart-lock trigger admits the
    writes. Nothing here commits, rolls back or locks.
    """

    def __init__(self, conn):
        self.conn = conn

    def _ensure_object(self, poid: PhysicalObjectId) -> None:
        """insert-if-absent + byte check (pin 4). RecordEdge objects carry
        the DB-lowercase body already; SkyEventStore.insert_physical_object
        keys DB_BODY on Title case, so the insert is replicated here with
        the same tolerant mapping the read side uses."""
        body = DB_BODY.get(poid.body, poid.body.lower())
        self.conn.execute(
            "INSERT INTO public.ka_gochara_physical_object ("
            " physical_object_id, body, relation_kind, canonical_target, convention_id)"
            " VALUES (%s,%s,%s,%s,%s)"
            " ON CONFLICT (body, relation_kind, canonical_target, convention_id)"
            " DO NOTHING",
            (str(poid.uuid), body, poid.relation_kind,
             poid.canonical_target, poid.convention_id),
        )
        row = self.conn.execute(
            "SELECT physical_object_id FROM public.ka_gochara_physical_object"
            " WHERE body = %s AND relation_kind = %s AND canonical_target = %s"
            " AND convention_id = %s",
            (body, poid.relation_kind, poid.canonical_target, poid.convention_id),
        ).fetchone()
        if row is None or str(row[0]) != str(poid.uuid):
            raise IdentityCollisionError(
                f"physical object {poid.identity_bytes}: stored id "
                f"{row[0] if row else None} != derived {poid.uuid}")

    # ── read side: the A2 global boundary table (read-only) ──────────────

    def fetch_path_prerequisites(self, path_id: str,
                                 rule_version: str) -> list[list[str]]:
        """The path's DECLARED prerequisite membership (1154, seeded by
        rule_binding) in declared order. F5: a record's prerequisite
        membership must equal exactly this set — never a caller's guess."""
        rows = self.conn.execute(
            "SELECT predicate_id, predicate_rule_version"
            " FROM public.ka_gochara_rule_path_prerequisite"
            " WHERE path_id = %s AND rule_version = %s"
            " ORDER BY ordinal",
            (path_id, rule_version),
        ).fetchall()
        return [[r[0], r[1]] for r in rows]

    def fetch_crossings(self, body: str, convention_id: str) -> list[CrossingInfo]:
        rows = self.conn.execute(
            "SELECT t_exact, longitude, solver_method, delta_lambda, delta_t,"
            " precision_regime FROM public.ka_gochara_sky_event"
            " WHERE event_kind = 'sign_ingress' AND body = %s"
            " AND convention_id = %s AND t_exact IS NOT NULL"
            " ORDER BY t_exact",
            (DB_BODY.get(body, body.lower()), convention_id),
        ).fetchall()
        return [CrossingInfo(t=r[0], level_deg=float(r[1]), solver_method=r[2],
                             delta_lambda=r[3], delta_t=r[4],
                             precision_regime=r[5]) for r in rows]

    # ── conventions (kala coverage FK + the F7 bridge) ────────────────────

    def ensure_kala_convention(self, vector: dict | None = None,
                               probe: dict | None = None) -> str:
        return gk_ledger.register_convention(
            self.conn, vector or KALA_CONVENTION_VECTOR, probe or {})

    def ensure_bridge(self, kala_convention_id: str, sky_convention_id: str) -> None:
        self.conn.execute(
            "INSERT INTO public.ka_gochara_convention_bridge"
            " (kala_convention_id, sky_convention_id) VALUES (%s,%s)"
            " ON CONFLICT (kala_convention_id) DO NOTHING",
            (kala_convention_id, sky_convention_id),
        )
        row = self.conn.execute(
            "SELECT sky_convention_id FROM public.ka_gochara_convention_bridge"
            " WHERE kala_convention_id = %s",
            (kala_convention_id,),
        ).fetchone()
        _byte_check(row, (sky_convention_id,), f"convention bridge {kala_convention_id}")

    # ── coverage FIRST (pin 7) ────────────────────────────────────────────

    def write_coverage(self, *, chart_id: str, generation: str,
                       event_class: str,
                       convention_id: str,
                       horizon: tuple[datetime, datetime],
                       resolution: float,
                       relations_searched: list[str],
                       targets_requested: int, targets_resolved: int,
                       state_counts: dict, unavailable_inputs: dict,
                       unsearched_reason: str | None,
                       build_id: str) -> None:
        """The class-level event_class coverage partition. The frozen F7
        guard (1155) pins key = event_class: ONE manifest row per
        (chart, generation, class), written by the coverage substep before
        any record grain of the class runs (coverage FIRST — pin 7 is
        existence-before-records; an earlier committed substep satisfies
        it). Insert-if-absent with a full byte check (pin 4)."""
        key = event_class
        rng = f"[{horizon[0].isoformat()},{horizon[1].isoformat()})"
        payload = (chart_id, generation, "event_class", key, convention_id,
                   rng, rng, resolution, relations_searched,
                   targets_requested, targets_resolved,
                   targets_requested - targets_resolved,
                   _json.dumps(state_counts), _json.dumps(unavailable_inputs),
                   unsearched_reason, build_id)
        self.conn.execute(
            "INSERT INTO public.kala_gochara_coverage ("
            " chart_id, generation, partition_kind, partition_key, convention_id,"
            " requested_horizon, completed_horizon, resolution, relations_searched,"
            " targets_requested, targets_resolved, targets_unresolved,"
            " target_resolution_state_counts, unavailable_inputs,"
            " unsearched_reason, build_id)"
            " VALUES (%s,%s,%s,%s,%s,%s::tstzrange,%s::tstzrange,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (chart_id, generation, partition_kind, partition_key)"
            " DO NOTHING",
            payload,
        )
        row = self.conn.execute(
            "SELECT convention_id, requested_horizon::text, relations_searched,"
            " targets_requested, targets_resolved, build_id"
            " FROM public.kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'event_class' AND partition_key = %s",
            (chart_id, generation, key),
        ).fetchone()
        if row is None or row[0] != convention_id or row[3:] != (
                targets_requested, targets_resolved, build_id):
            raise IdentityCollisionError(
                f"coverage {key}: stored row {row} diverges from the grain's "
                f"own facts (convention {convention_id}, targets "
                f"{targets_requested}/{targets_resolved}, build {build_id})")

    def stored_coverage_facts_json(self, *, chart_id: str, generation: str,
                                   event_class: str) -> str:
        """N10/N14: the record's coverage_facts are computed by
        ka_gochara_coverage_facts FROM THE STORED PARTITION ROW — never
        hand-shaped and never from grain-local parameters (the record
        coverage guard byte-compares against the partition as it stands).
        Fail-closed when the class partition is missing (coverage FIRST)."""
        row = self.conn.execute(
            "SELECT public.ka_gochara_coverage_facts(convention_id,"
            " completed_horizon, relations_searched)::text"
            " FROM public.kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'event_class' AND partition_key = %s",
            (chart_id, generation, event_class),
        ).fetchone()
        if row is None:
            raise MissingCoverageError(
                f"event_class coverage partition {event_class!r} absent for "
                f"(chart {chart_id}, generation {generation}) — the coverage "
                "substep runs before any record grain (pin 7); a record "
                "without its coverage manifest is refused, never orphaned")
        return row[0]

    # ── contact chain (identity → chart-ledger contact) ───────────────────

    def insert_contact(self, *, chart_id: str, generation: str,
                       contact: SubstrateContact, span: ResidenceSpan,
                       poid: PhysicalObjectId, convention_id: str,
                       crossing: CrossingInfo | None,
                       horizon_end: datetime) -> None:
        self._ensure_object(poid)
        self.conn.execute(
            "INSERT INTO public.ka_gochara_contact_identity"
            " (contact_id, physical_object_id, occurrence_ordinal)"
            " VALUES (%s,%s,%s) ON CONFLICT (contact_id) DO NOTHING",
            (str(contact.contact_id), str(poid.uuid), contact.occurrence_ordinal),
        )
        row = self.conn.execute(
            "SELECT physical_object_id, occurrence_ordinal"
            " FROM public.ka_gochara_contact_identity WHERE contact_id = %s",
            (str(contact.contact_id),),
        ).fetchone()
        _byte_check(row, (str(poid.uuid), contact.occurrence_ordinal),
                    f"contact identity {contact.contact_id}")

        truncated = span.t_exact is None
        t_in = span.t_in
        t_out = span.t_out if span.t_out is not None else horizon_end
        solver = ("clipped_truncated" if truncated
                  else (crossing.solver_method if crossing else "swiss_refined"))
        coverage = {"truncated": truncated}
        params = (
            chart_id, generation, str(contact.contact_id), str(poid.uuid),
            contact.occurrence_ordinal, convention_id, DB_BODY.get(poid.body, poid.body.lower()),
            "residence", t_in, t_out, None if truncated else span.t_exact,
            solver,
            None if truncated else (crossing.delta_lambda if crossing else None),
            None if truncated else (crossing.delta_t if crossing else None),
            None if truncated else (crossing.precision_regime if crossing else None),
            _json.dumps(coverage),
        )
        self.conn.execute(
            "INSERT INTO public.ka_gochara_contact ("
            " chart_id, generation, contact_id, physical_object_id,"
            " occurrence_ordinal, convention_id, body, relation_kind,"
            " t_in, t_out, t_exact, solver_method, delta_lambda, delta_t,"
            " precision_regime, coverage)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (chart_id, generation, contact_id) DO NOTHING",
            params,
        )
        row = self.conn.execute(
            "SELECT physical_object_id, occurrence_ordinal, body, relation_kind"
            " FROM public.ka_gochara_contact"
            " WHERE chart_id = %s AND generation = %s AND contact_id = %s",
            (chart_id, generation, str(contact.contact_id)),
        ).fetchone()
        _byte_check(row, (str(poid.uuid), contact.occurrence_ordinal,
                          DB_BODY.get(poid.body, poid.body.lower()), "residence"),
                    f"contact {contact.contact_id}")

    # ── record rows (kgrr) ────────────────────────────────────────────────

    def insert_record(self, *, chart_id: str, generation: str,
                      edge: RecordEdge, record_id, contact_id: str | None,
                      support_state: str, support_intervals: list[str],
                      precision: dict | None,
                      coverage_key: str, coverage_facts: str,
                      source_fact_ids: list[str],
                      prerequisites: list[list[str]],
                      house_from_frame: int | None = None) -> None:
        params = (
            str(record_id), chart_id, generation, contact_id, edge.event_class,
            edge.affected_person, edge.frame_kind, edge.frame_arg, edge.agent,
            edge.relation, str(edge.obj.uuid), edge.object_kind, edge.object_role,
            edge.path_id, edge.rule_version, support_state,
            SUPPORT_GRAIN_SPAN if support_state != "uncomputed" else None,
            support_intervals, "event_class", coverage_key,
            coverage_facts,
            _json.dumps(precision) if precision is not None else None,
            edge.source_text, edge.source_page, _json.dumps(source_fact_ids),
            edge.provenance, edge.operator_role, edge.ruling_ref,
            "unqualified", house_from_frame, 0.0, 0.0, "unqualified", 0.0,
        )
        self.conn.execute(
            "INSERT INTO public.ka_gochara_relationship_record ("
            " record_id, chart_id, generation, contact_id, event_class,"
            " affected_person, frame_kind, frame_arg, agent, relation,"
            " object_id, object_kind, object_role, path_id, rule_version,"
            " temporal_support_state, temporal_support_grain,"
            " temporal_support_intervals, coverage_partition_kind,"
            " coverage_partition_key, coverage_facts, precision,"
            " source_text, source_page, source_fact_ids, provenance,"
            " operator_role, ruling_ref, admission_state, house_from_frame,"
            " evidence_for_occurrence, evidence_against_occurrence,"
            " outcome_valence_for_native, severity)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
            " %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (record_id) DO NOTHING",
            params,
        )
        row = self.conn.execute(
            "SELECT chart_id::text, generation, event_class, path_id, rule_version"
            " FROM public.ka_gochara_relationship_record WHERE record_id = %s",
            (str(record_id),),
        ).fetchone()
        _byte_check(row, (chart_id, generation, edge.event_class,
                          edge.path_id, edge.rule_version),
                    f"record {record_id}")
        # F5 prerequisite membership: exactly the path's declared set, in
        # declared order; result NULL = not yet evaluated (counts as
        # unknown — the finalize check at COMMIT derives 'unqualified').
        for ordinal, (predicate_id, predicate_version) in enumerate(prerequisites, start=1):
            self.conn.execute(
                "INSERT INTO public.ka_gochara_record_prerequisite ("
                " record_id, chart_id, generation, ordinal, predicate_id,"
                " predicate_rule_version, result)"
                " VALUES (%s,%s,%s,%s,%s,%s,NULL)"
                " ON CONFLICT (record_id, ordinal) DO NOTHING",
                (str(record_id), chart_id, generation, ordinal,
                 predicate_id, predicate_version),
            )
        stored = self.conn.execute(
            "SELECT predicate_id, predicate_rule_version"
            " FROM public.ka_gochara_record_prerequisite"
            " WHERE record_id = %s ORDER BY ordinal",
            (str(record_id),),
        ).fetchall()
        _byte_check(stored, [tuple(p) for p in prerequisites],
                    f"record {record_id} prerequisite membership")


# ── grain orchestration (one substep = one call = one transaction) ────────

def write_class_coverage(
    store: RecordStore,
    *,
    chart_id: str,
    generation: str,
    event_class: str,
    class_edges: Sequence[RecordEdge],
    horizon: tuple[datetime, datetime],
    position_at: Callable[[datetime], float] | None,
    sky_convention_id: str,
    kala_convention_id: str,
    build_id: str,
) -> None:
    """The `coverage:<event_class>` substep: ONE class-level event_class
    coverage partition (the frozen F7 key convention), written before any
    record grain of the class. Facts are the class's whole-generation
    declared search across every bound path (deterministic from the static
    enumeration — any grain recomputes the identical row, so pin-4
    insert-if-absent is consistent):

      * relations_searched — the relations this slice actually searches
        (residence with a probe; natal_fact always); deferred relations
        (point solves, 3/N) are named in unsearched_reason, never searched
        silently;
      * targets — edge-level counts over the class's full enumeration:
        resolved = edges under searched relations, unavailable = edges
        under deferred/underivable ones;
      * resolution — the largest solve tolerance (arcsec) of the crossings
        actually read (N7); 0.0 with a named non-claim when no angular
        solve happened.
    """
    residence = [e for e in class_edges if e.transit and e.relation == "residence"]
    natal = [e for e in class_edges if not e.transit]
    deferred = sorted({e.relation for e in class_edges
                       if e.transit and e.relation != "residence"})
    relations_searched = (
        (["residence"] if residence and position_at is not None else [])
        + (["natal_fact"] if natal else []))
    unavailable: dict = {}
    unsearched = DEFERRAL_POINT_SOLVE if deferred else None
    if residence and position_at is None:
        unavailable["position_probe"] = ("ephemeris probe unavailable — no "
                                         "span derived (named, never fabricated)")
        unsearched = "; ".join(x for x in (
            unsearched, "residence spans underived without a position probe") if x)
    eps: list[float] = []
    if residence and position_at is not None:
        for body in sorted({e.agent for e in residence}):
            eps += [c.delta_lambda * 3600.0
                    for c in store.fetch_crossings(body, sky_convention_id)
                    if c.delta_lambda is not None]
    resolution = max(eps) if eps else 0.0
    if not eps:
        unavailable["resolution"] = ("no angular solve in this class's searched "
                                     "relations — resolution not applicable "
                                     "(0.0 is a non-claim)")
    searched = len(residence if position_at is not None else []) + len(natal)
    total = len(class_edges)
    store.ensure_bridge(kala_convention_id, sky_convention_id)
    store.write_coverage(
        chart_id=chart_id, generation=generation, event_class=event_class,
        convention_id=kala_convention_id, horizon=horizon,
        resolution=resolution, relations_searched=relations_searched,
        targets_requested=total, targets_resolved=searched,
        state_counts={"resolved": searched, "unavailable": total - searched,
                      "unqualified": 0},
        unavailable_inputs=unavailable, unsearched_reason=unsearched,
        build_id=build_id,
    )


def materialise_record_grain(
    store: RecordStore,
    *,
    chart_id: str,
    generation: str,
    event_class: str,
    path_id: str,
    edges: Sequence[RecordEdge],
    horizon: tuple[datetime, datetime],
    position_at: Callable[[datetime], float] | None,
    house_for: Callable[[RecordEdge, str], int | None],
    sky_convention_id: str,
    source_fact_ids: list[str],
    prerequisites: list[list[str]] | None = None,
) -> dict[str, int]:
    """Materialise one `record:<event_class>:<path_id>` grain: contacts,
    then records, bound to the class's ALREADY-WRITTEN coverage partition
    (pin 7 — the coverage substep runs first; a grain without it refuses
    via stored_coverage_facts_json, never orphans a record).

    `position_at` probes sidereal longitudes for span derivation (one probe
    per interval; injected — this module never touches an ephemeris).
    Without it no transit span is derived: nothing is minted (the class
    coverage named the probe's absence), never fabricated.
    """
    residence_edges = [e for e in edges if e.transit and e.relation == "residence"]
    natal_edges = [e for e in edges if not e.transit]
    coverage_key = event_class
    if prerequisites is None:
        rule_version = edges[0].rule_version if edges else "1.0.0"
        prerequisites = store.fetch_path_prerequisites(path_id, rule_version)

    # Derive full-domain spans per body (stable ordinals), then intersect
    # with the requested horizon. One crossing read + one span set per body.
    spans_by_body: dict[str, list[ResidenceSpan]] = {}
    crossings_by_body: dict[str, dict[datetime, CrossingInfo]] = {}
    if residence_edges and position_at is not None:
        for body in sorted({e.agent for e in residence_edges}):
            infos = store.fetch_crossings(body, sky_convention_id)
            crossings_by_body[body] = {c.t: c for c in infos}
            spans_by_body[body] = residence_spans(
                [BoundaryCrossing(t=c.t, level_deg=c.level_deg) for c in infos],
                horizon=(SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END),
                position_at=position_at,
            )

    # Work list (pass 1, no writes): the in-horizon minted occurrences with
    # their house resolved. kgrr_evaluated_has_house_ck requires
    # house_from_frame on every computed row — an occurrence whose frame
    # anchor is unknown is NOT minted (a state, never an omission).
    h_start, h_end = horizon
    work: list[tuple[RecordEdge, dict, int]] = []
    for e in residence_edges:
        body_spans = spans_by_body.get(e.agent, [])
        if not body_spans:
            continue
        for m in mint_transit_records(
                e, body_spans, chart_id=chart_id, generation=generation,
                prerequisites=prerequisites):
            span = m["span"]
            if not (span.t_in < h_end and (span.t_out is None or span.t_out > h_start)):
                continue  # full-domain span outside the requested horizon
            house = house_for(e, span.sign)
            if house is None:
                continue
            work.append((e, m, house))

    coverage_facts = store.stored_coverage_facts_json(
        chart_id=chart_id, generation=generation, event_class=event_class)
    counts = {"contacts": 0, "records": 0, "natal_records": 0,
              "truncated_contacts": 0}
    for edge, m, house in work:
        span = m["span"]
        crossing = crossings_by_body.get(edge.agent, {}).get(span.t_exact) if span.t_exact else None
        store.insert_contact(
            chart_id=chart_id, generation=generation,
            contact=m["contact"], span=span, poid=edge.obj,
            convention_id=sky_convention_id, crossing=crossing,
            horizon_end=h_end)
        counts["contacts"] += 1
        counts["truncated_contacts"] += 1 if span.t_exact is None else 0
        precision = None
        if span.t_exact is not None:
            precision = {
                "solver_method": crossing.solver_method if crossing else "swiss_refined",
                "delta_lambda": crossing.delta_lambda if crossing else None,
                "delta_t": crossing.delta_t if crossing else None,
            }
        interval = f"[{span.t_in.isoformat()},{(span.t_out or h_end).isoformat()})"
        store.insert_record(
            chart_id=chart_id, generation=generation, edge=edge,
            record_id=m["record_id"],
            contact_id=str(m["contact"].contact_id),
            support_state="computed", support_intervals=[interval],
            precision=precision, coverage_key=coverage_key,
            coverage_facts=coverage_facts, source_fact_ids=source_fact_ids,
            prerequisites=prerequisites, house_from_frame=house)
        counts["records"] += 1
    for edge in natal_edges:
        m = mint_natal_record(edge, chart_id=chart_id, generation=generation,
                              prerequisites=prerequisites)
        store.insert_record(
            chart_id=chart_id, generation=generation, edge=edge,
            record_id=m["record_id"], contact_id=None,
            support_state="uncomputed", support_intervals=[],
            precision=None, coverage_key=coverage_key,
            coverage_facts=coverage_facts, source_fact_ids=source_fact_ids,
            prerequisites=prerequisites)
        counts["natal_records"] += 1
    return counts


def _edge_sign(edge: RecordEdge) -> str:
    return edge.obj.canonical_target.removeprefix("span:").lower()


__all__ = [
    "CrossingInfo",
    "DEFERRAL_POINT_SOLVE",
    "KALA_CONVENTION_VECTOR",
    "MissingCoverageError",
    "RecordStore",
    "SUPPORT_GRAIN_SPAN",
    "materialise_record_grain",
    "write_class_coverage",
]
