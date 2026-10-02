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
sign_ingress sky events — the A2 global boundary table, read-only),
natal-fact edges (transit=False, contact_id NULL), and — interval_sweep
3/N — `conjunction`/`aspect` transit edges on point:<λ> targets, solved
through the kernel's arc index (`solve_point_edges`: roots per relation
level, Swiss-refined; full-domain ordinals; span = the in-orb interval at
the pinned WP1 §7 orb). When the arc index is unavailable the class
coverage names the deferral — the edges are never silently dropped and
never minted uncomputed.

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
import uuid as _uuid
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Sequence

from . import ledger as gk_ledger
from . import targets
from .contacts import find_roots
from .convention import ORB_TABLE
from .evaluator import RULE_VERSION, RecordEdge, record_uuid
from .materialise import (BoundaryCrossing, ResidenceSpan, aspect_spans, mint_natal_record,
                          mint_transit_records, residence_spans)
from .substrate import (DB_BODY, SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START,
                        IdentityCollisionError, PhysicalObjectId,
                        SubstrateContact, assign_occurrence_ordinals,
                        jd_to_utc)
from services.gochara_rules.frames import sign_of
from services.gochara_rules import predicates as rule_predicates
from services.gochara_rules import admission as rules_admission
from services.gochara_rules import favourable_houses as rules_favourable
from services.gochara_rules import permission as rules_permission
from services.gochara_rules import registry as rules_registry

logger = logging.getLogger(__name__)

SUPPORT_GRAIN_SPAN = "span"
DEFERRAL_POINT_SOLVE = ("aspect/conjunction contact solve needs the body's "
                        "arc index — unavailable in this run (named deferral)")

# Point solves (interval_sweep 3/N): the evaluator's transit point edges —
# (agent, conjunction|aspect, point:<λ full precision>) — solve through the
# kernel's arc index: roots per relation level (dṛṣṭi: body at target −
# angle; nodes cast none, N-14 — excluded at enumeration), Swiss-refined at
# the instant (plan §4.2), occurrence ordinals over the FULL convention
# domain (R3 amendment 1), span = the in-orb interval at the pinned
# relation-class orb (WP1 §7 ORB_TABLE — the same table the kernel emits
# episodes at; N7 restates the solve's own tolerance on the row).
POINT_KERNEL_RELATION = {"conjunction": "conjunction", "aspect": "drishti_contact"}
POINT_ORB_SOURCE = {"conjunction": "orb_conj_slow", "aspect": "orb_drishti_slow"}
#: The arc-index tolerance the point solve declares on its coverage rows
#: (arcs.DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC — the writer builds indexes at
#: the kernel default; N7 restates the solve's own tolerance).
POINT_SOLVE_INDEX_TOLERANCE_ARCSEC = 1.0
_JD_UNIX_EPOCH = 2440587.5


def _utc_to_jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + _JD_UNIX_EPOCH


def _dasharow(row: dict) -> dict:
    """Normalise an L1 chart_dashas read for the predicate evaluator:
    start/end as datetimes (the defensive reader hands dicts whose values
    may be str or datetime depending on the driver's row shape)."""
    def _dt(v):
        return v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
    return {"start_iso": _dt(row["start_iso"]), "end_iso": _dt(row["end_iso"])}



def _require_minted_record_uuid(record_id) -> None:
    """Refuse anything but a UUIDv8 (what `evaluator.record_uuid` returns)."""
    try:
        value = record_id if isinstance(record_id, _uuid.UUID) else _uuid.UUID(str(record_id))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(
            f"record_id {record_id!r} is not a UUID — records mint ONLY via evaluator.record_uuid "
            "(the sha256: property of RelationshipRecord is a different type and is never stored; "
            "IDENTITY_CANONICAL_BYTES_CONTRACT §7)") from None
    if value.version != 8:
        raise ValueError(
            f"record_id {value} is not a UUIDv8 — records mint ONLY via evaluator.record_uuid "
            "(IDENTITY_CANONICAL_BYTES_CONTRACT §7)")


@dataclass(frozen=True)
class PointOccurrence:
    """One solved point-contact occurrence of a (body, conjunction|aspect,
    point:<λ>) object: the refined root plus its in-orb span clipped to the
    requested horizon. t_exact None ⇔ truncated (the exact centre lies
    outside the requested horizon — the span overlaps it, N3 kept)."""

    contact: SubstrateContact
    level_deg: float
    t_in: datetime
    t_out: datetime
    t_exact: datetime | None
    truncated: bool
    solver_method: str
    delta_lambda: float | None
    delta_t: float | None
    precision_regime: str | None


def _in_orb_span_around_root(index, root, orb_deg: float) -> tuple[float, float]:
    """The in-orb interval around one refined root, derived from the root's
    OWN arc (monotone, station-bounded — a turnaround inside the orb closes
    the interval at the arc's station boundary, E8-2).

    Deliberately NOT episodes.in_orb_intervals: that helper resolves ONE
    unwrapped representative per SEGMENT (_segment_band_level, nearest the
    midpoint), so on a multi-revolution segment (any stationless body over
    years) every band but one is silently missed — reported to the steward
    2026-10-01 (M20261001T172758-6f81). The arc-local derivation is exact
    per occurrence by construction.
    """
    arc = root.arc
    tol_deg = max(index.tolerance_arcsec / 3600.0, 1e-9)
    lon_at_root = arc.unwrapped_longitude_at(root.exact_jd)
    level_u = root.level_deg + 360.0 * round((lon_at_root - root.level_deg) / 360.0)
    lo, hi = level_u - orb_deg, level_u + orb_deg
    span_lo = min(arc.start_lon_unwrapped, arc.end_lon_unwrapped)
    span_hi = max(arc.start_lon_unwrapped, arc.end_lon_unwrapped)

    def _bisect(jd_a: float, jd_b: float, target_u: float) -> float:
        fa = index.evaluate(jd_a) - target_u
        fb = index.evaluate(jd_b) - target_u
        for _ in range(80):
            mid = 0.5 * (jd_a + jd_b)
            fm = index.evaluate(mid) - target_u
            if abs(fm) <= tol_deg:
                return mid
            if (fa < 0) == (fm < 0):
                jd_a, fa = mid, fm
            else:
                jd_b, fb = mid, fm
        return mid

    a, b = arc.start_jd, arc.end_jd
    if arc.direction == 1:
        if span_lo < lo - 1e-12:
            a = _bisect(arc.start_jd, root.exact_jd, lo)
        if span_hi > hi + 1e-12:
            b = _bisect(root.exact_jd, arc.end_jd, hi)
    else:
        if span_hi > hi + 1e-12:
            a = _bisect(arc.start_jd, root.exact_jd, hi)
        if span_lo < lo - 1e-12:
            b = _bisect(root.exact_jd, arc.end_jd, lo)
    return a, b


def solve_point_edges(
    edges: Sequence[RecordEdge],
    *,
    arc_index_for: Callable[[str], object] | None,
    horizon: tuple[datetime, datetime],
    ephe_path: str | None = None,
    refine: bool = True,
) -> dict[int, list[PointOccurrence]]:
    """Solve the transit point edges (conjunction/aspect on point:<λ>).

    `arc_index_for(body)` yields the body's arc index over the FULL
    convention domain (injected — built once per body by the caller; the
    ordinal set is the full-domain ordered crossing set, R3 amendment 1).
    When arc_index_for is None nothing is solved (the class coverage named
    the deferral) — the edges are never silently dropped and never minted
    uncomputed. Returns {id(edge): [PointOccurrence, ...]} for edges whose
    span overlaps the requested horizon.
    """
    out: dict[int, list[PointOccurrence]] = {}
    if arc_index_for is None:
        return out
    h0, h1 = _utc_to_jd(horizon[0]), _utc_to_jd(horizon[1])
    for edge in edges:
        if not edge.transit or edge.relation not in POINT_KERNEL_RELATION:
            continue
        target = edge.obj.canonical_target
        assert target.startswith("point:"), target
        lam = float(target[len("point:"):])
        body = edge.agent.title()
        index = arc_index_for(body)
        kernel_rel = POINT_KERNEL_RELATION[edge.relation]
        orb = float(ORB_TABLE[POINT_ORB_SOURCE[edge.relation]]["orb_max_deg"])
        roots = find_roots(index, body, kernel_rel, lam, ephe_path,
                           refine=refine)
        contacts = assign_occurrence_ordinals(
            physical_object_id=edge.obj,
            t_exact_list=[jd_to_utc(r.exact_jd) for r in roots])
        occs: list[PointOccurrence] = []
        for root, contact in zip(roots, contacts):
            a, b = _in_orb_span_around_root(index, root, orb)
            if not (a - 1e-9 <= root.exact_jd <= b + 1e-9):
                raise RuntimeError(
                    f"{edge.agent} {edge.relation} {target}: refined root at "
                    f"jd {root.exact_jd} lies outside its own in-orb span "
                    f"[{a}, {b}] — solver defect, refusing to mint")
            if b <= h0 or a >= h1:
                continue  # outside the requested horizon entirely
            exact_inside = h0 <= root.exact_jd < h1
            t_in_jd, t_out_jd = max(a, h0), min(b, h1)
            if not t_in_jd < t_out_jd:
                # an overlap only AT the excluded end (half-open [h0, h1))
                # is not a legitimate truncated span — dropped (A2 v1.1)
                continue
            occs.append(PointOccurrence(
                contact=contact,
                level_deg=root.level_deg,
                t_in=jd_to_utc(t_in_jd),
                t_out=jd_to_utc(t_out_jd),
                t_exact=jd_to_utc(root.exact_jd) if exact_inside else None,
                truncated=not exact_inside,
                solver_method=("swiss_refined" if (exact_inside and refine)
                               else ("arc_index_bracket" if exact_inside
                                     else "clipped_truncated")),
                delta_lambda=(index.tolerance_arcsec / 3600.0
                              if exact_inside else None),
                delta_t=1e-9 if (exact_inside and refine) else None,
                precision_regime=(
                    ("swiss_bisect_tol_1e-9d" if refine
                     else f"arc_index_bracket_{index.tolerance_arcsec}arcsec")
                    if exact_inside else None),
            ))
        if occs:
            out[id(edge)] = occs
    return out

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


class SealedGenerationError(RuntimeError):
    """AM-3: a candidate rebuild (delete-then-insert) was attempted against a
    SEALED generation. A sealed generation is never reopened — a re-run under an
    existing sealed generation is a refusal; new evaluation is a new generation."""


class RecordStore:
    """Persistence for one record grain (pin 5) over 1081/1153/1155.

    The caller's transaction holds the chart family key
    (ka_gochara_lock_chart) — the substrate chart-lock trigger admits the
    writes. Nothing here commits, rolls back or locks.
    """

    def __init__(self, conn):
        self.conn = conn

    def ensure_object(self, poid: PhysicalObjectId) -> None:
        """Public: a record's object must EXIST (FK) whether or not a transit contact was ever
        materialised for it — a natal occupancy/ownership row shares the occupant/owner's
        residence-span object (E8) and must not depend on the transit solve having produced one."""
        self._ensure_object(poid)

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

    def stored_contact_keys(self, *, chart_id: str, generation: str) -> set[tuple]:
        """The `transit_relation` declarations: (body, relation_kind, physical_object_id)
        of every contact row stored for this chart × generation — READ BACK from the
        database, never built from the minting loop."""
        rows = self.conn.execute(
            "SELECT body, relation_kind, physical_object_id::text"
            " FROM public.ka_gochara_contact WHERE chart_id = %s AND generation = %s",
            (chart_id, generation)).fetchall()
        return {(r[0], r[1], r[2]) for r in rows}

    # ── candidate replacement in dependency order (AM-3; §N.3) ───────────
    #
    # The chart × generation tables are rebuilt by delete-then-insert at the
    # OWNED grain, never by insert-if-absent: a rebuild REPLACES, it never
    # accretes and never raises on a legitimate input change. Dependency order
    # (FK closure of 1081/1153/1155/1156): window membership → windows →
    # records (prerequisites cascade) → the contacts those records alone
    # referenced → the class coverage partition. A contact another path's records
    # still reference is NEVER deleted (P3/P4 share one contact). The global
    # tables (physical objects, contact identities, sky events) are untouched —
    # they stay insert-if-absent. A sealed generation is refused up front (the
    # DB's own DELETE guards would refuse it too; this names it).

    def _refuse_if_sealed(self, chart_id: str, generation: str, what: str) -> None:
        row = self.conn.execute(
            "SELECT public.ka_gochara_generation_is_sealed(%s::uuid, %s)",
            (chart_id, generation)).fetchone()
        if row and row[0]:
            raise SealedGenerationError(
                f"{what}: (chart {chart_id}, generation {generation}) is SEALED — a "
                "sealed generation is never rebuilt in place; evaluate under a new "
                "generation label")

    def _delete_orphaned_contacts(self, chart_id: str, generation: str,
                                  contact_ids: list) -> int:
        if not contact_ids:
            return 0
        cur = self.conn.execute(
            "DELETE FROM public.ka_gochara_contact c"
            " WHERE c.chart_id = %s AND c.generation = %s"
            "   AND c.contact_id = ANY(%s::uuid[])"
            "   AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_relationship_record r"
            "                    WHERE r.chart_id = c.chart_id"
            "                      AND r.generation = c.generation"
            "                      AND r.contact_id = c.contact_id)",
            (chart_id, generation, [str(c) for c in contact_ids]))
        return cur.rowcount

    def delete_record_grain(self, *, chart_id: str, generation: str,
                            event_class: str, path_id: str,
                            rule_version: str) -> dict[str, int]:
        """Replace-prelude of one `record:` grain: the grain's windows, its
        records (and their prerequisites), then the contacts only they used."""
        self._refuse_if_sealed(chart_id, generation,
                               f"record grain {event_class}/{path_id}")
        grain = (chart_id, generation, event_class, path_id, rule_version)
        where = (" WHERE chart_id = %s AND generation = %s AND event_class = %s"
                 " AND path_id = %s AND rule_version = %s")
        windows = self.conn.execute(
            "DELETE FROM public.ka_gochara_eval_window" + where, grain).rowcount
        contact_ids = [r[0] for r in self.conn.execute(
            "SELECT DISTINCT contact_id FROM public.ka_gochara_relationship_record"
            + where + " AND contact_id IS NOT NULL", grain).fetchall()]
        records = self.conn.execute(
            "DELETE FROM public.ka_gochara_relationship_record" + where,
            grain).rowcount
        contacts = self._delete_orphaned_contacts(chart_id, generation, contact_ids)
        return {"windows": windows, "records": records, "contacts": contacts}

    def delete_class_chain(self, *, chart_id: str, generation: str,
                           event_class: str) -> dict[str, int]:
        """Replace-prelude of one CLASS: every path's windows and records of the
        class, the contacts only they used, then the class coverage partition
        itself (records/windows FK it, so it goes last)."""
        self._refuse_if_sealed(chart_id, generation, f"class {event_class}")
        key = (chart_id, generation, event_class)
        where = (" WHERE chart_id = %s AND generation = %s AND event_class = %s")
        windows = self.conn.execute(
            "DELETE FROM public.ka_gochara_eval_window" + where, key).rowcount
        contact_ids = [r[0] for r in self.conn.execute(
            "SELECT DISTINCT contact_id FROM public.ka_gochara_relationship_record"
            + where + " AND contact_id IS NOT NULL", key).fetchall()]
        records = self.conn.execute(
            "DELETE FROM public.ka_gochara_relationship_record" + where,
            key).rowcount
        contacts = self._delete_orphaned_contacts(chart_id, generation, contact_ids)
        coverage = self.conn.execute(
            "DELETE FROM public.kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'event_class' AND partition_key = %s",
            key).rowcount
        return {"windows": windows, "records": records, "contacts": contacts,
                "coverage": coverage}

    # ── Moon / day tier (AM-4): one durable coverage identity per query ────

    def write_moon_coverage(self, *, chart_id: str, generation: str,
                            partition_key: str, convention_id: str,
                            horizon: tuple[datetime, datetime],
                            resolution: float, relations_searched: list[str],
                            targets_requested: int, targets_resolved: int,
                            state_counts: dict, unavailable_inputs: dict,
                            unsearched_reason: str | None,
                            build_id: str) -> None:
        """The `moon_on_demand` partition of ONE query interval. A query-identity
        row, not build output: insert-if-absent, and a re-issued query must
        agree on every claimed fact (convention, horizon, relations, counts) or
        it fails loudly — a durable coverage identity is never overwritten."""
        rng = f"[{horizon[0].isoformat()},{horizon[1].isoformat()})"
        self.conn.execute(
            "INSERT INTO public.kala_gochara_coverage ("
            " chart_id, generation, partition_kind, partition_key, convention_id,"
            " requested_horizon, completed_horizon, resolution, relations_searched,"
            " targets_requested, targets_resolved, targets_unresolved,"
            " target_resolution_state_counts, unavailable_inputs,"
            " unsearched_reason, build_id)"
            " VALUES (%s,%s,'moon_on_demand',%s,%s,%s::tstzrange,%s::tstzrange,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (chart_id, generation, partition_kind, partition_key)"
            " DO NOTHING",
            (chart_id, generation, partition_key, convention_id, rng, rng,
             resolution, relations_searched, targets_requested, targets_resolved,
             targets_requested - targets_resolved, _json.dumps(state_counts),
             _json.dumps(unavailable_inputs), unsearched_reason, build_id))
        row = self.conn.execute(
            "SELECT convention_id, relations_searched, targets_requested,"
            " targets_resolved, resolution::float8 FROM public.kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'moon_on_demand' AND partition_key = %s",
            (chart_id, generation, partition_key)).fetchone()
        _byte_check(row, (convention_id, relations_searched, targets_requested,
                          targets_resolved, float(resolution)),
                    f"moon coverage {partition_key}")

    def moon_coverage_facts(self, *, chart_id: str, generation: str,
                            partition_key: str):
        """The coverage_facts snapshot the answer was given under, computed by
        the DB's own helper from the stored partition row."""
        row = self.conn.execute(
            "SELECT public.ka_gochara_coverage_facts(convention_id,"
            " completed_horizon, relations_searched)"
            " FROM public.kala_gochara_coverage"
            " WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'moon_on_demand' AND partition_key = %s",
            (chart_id, generation, partition_key)).fetchone()
        if row is None:
            raise MissingCoverageError(f"moon coverage {partition_key!r} absent")
        return row[0]

    def manifest_binding(self, *, chart_id: str, generation: str) -> dict | None:
        """The generation's manifest id / digest / status for the receipt, or None
        when it has no manifest row (stated in the receipt, never invented)."""
        row = self.conn.execute(
            "SELECT manifest_id, content_digest, status"
            " FROM public.kala_gochara_publication"
            " WHERE chart_id = %s AND generation = %s",
            (chart_id, generation)).fetchone()
        if row is None:
            return None
        return {"manifest_id": str(row[0]), "content_digest": row[1], "status": row[2]}

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
        it). A candidate REBUILD replaces the class's whole dependent chain
        (AM-3/§N.3) and writes the partition afresh — it never accretes and a
        changed input (new build, new horizon, new relations) never raises; a
        sealed generation is refused."""
        key = event_class
        rng = f"[{horizon[0].isoformat()},{horizon[1].isoformat()})"
        payload = (chart_id, generation, "event_class", key, convention_id,
                   rng, rng, resolution, relations_searched,
                   targets_requested, targets_resolved,
                   targets_requested - targets_resolved,
                   _json.dumps(state_counts), _json.dumps(unavailable_inputs),
                   unsearched_reason, build_id)
        self.delete_class_chain(chart_id=chart_id, generation=generation,
                                event_class=event_class)
        self.conn.execute(
            "INSERT INTO public.kala_gochara_coverage ("
            " chart_id, generation, partition_kind, partition_key, convention_id,"
            " requested_horizon, completed_horizon, resolution, relations_searched,"
            " targets_requested, targets_resolved, targets_unresolved,"
            " target_resolution_state_counts, unavailable_inputs,"
            " unsearched_reason, build_id)"
            " VALUES (%s,%s,%s,%s,%s,%s::tstzrange,%s::tstzrange,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            payload,
        )

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
            poid.relation_kind, t_in, t_out, None if truncated else span.t_exact,
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
                          DB_BODY.get(poid.body, poid.body.lower()), poid.relation_kind),
                    f"contact {contact.contact_id}")

    # ── point contacts (conjunction/aspect on point:<λ>, 3/N) ─────────────

    def insert_point_contact(self, *, chart_id: str, generation: str,
                             occ: PointOccurrence, poid: PhysicalObjectId,
                             convention_id: str) -> None:
        self._ensure_object(poid)
        self.conn.execute(
            "INSERT INTO public.ka_gochara_contact_identity"
            " (contact_id, physical_object_id, occurrence_ordinal)"
            " VALUES (%s,%s,%s) ON CONFLICT (contact_id) DO NOTHING",
            (str(occ.contact.contact_id), str(poid.uuid),
             occ.contact.occurrence_ordinal),
        )
        row = self.conn.execute(
            "SELECT physical_object_id, occurrence_ordinal"
            " FROM public.ka_gochara_contact_identity WHERE contact_id = %s",
            (str(occ.contact.contact_id),),
        ).fetchone()
        _byte_check(row, (str(poid.uuid), occ.contact.occurrence_ordinal),
                    f"contact identity {occ.contact.contact_id}")

        params = (
            chart_id, generation, str(occ.contact.contact_id), str(poid.uuid),
            occ.contact.occurrence_ordinal, convention_id,
            DB_BODY.get(poid.body, poid.body.lower()), poid.relation_kind,
            occ.t_in, occ.t_out, occ.t_exact,
            occ.solver_method, occ.delta_lambda, occ.delta_t,
            occ.precision_regime, _json.dumps({"truncated": occ.truncated}),
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
            (chart_id, generation, str(occ.contact.contact_id)),
        ).fetchone()
        _byte_check(row, (str(poid.uuid), occ.contact.occurrence_ordinal,
                          DB_BODY.get(poid.body, poid.body.lower()),
                          poid.relation_kind),
                    f"contact {occ.contact.contact_id}")

    # ── record rows (kgrr) ────────────────────────────────────────────────

    def insert_record(self, *, chart_id: str, generation: str,
                      edge: RecordEdge, record_id, contact_id: str | None,
                      support_state: str, support_intervals: list[str],
                      precision: dict | None,
                      coverage_key: str, coverage_facts: str,
                      source_fact_ids: list[str],
                      prerequisites: list[list[str]],
                      house_from_frame: int | None = None) -> None:
        # F-3 §7: a record is minted ONLY through `evaluator.record_uuid` (UUIDv8 over the
        # canonical natural key). The older `RelationshipRecord.record_id` property returns a
        # `sha256:`-tagged hex string over the same bytes — a different TYPE; it must never
        # be stored or compared (the DB column is UUID).
        _require_minted_record_uuid(record_id)
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

    def set_prerequisite_result(self, *, record_id, ordinal: int,
                                predicate_id: str, predicate_version: str,
                                result: str) -> None:
        """The trigger's result_only path (1155: ONLY `result` may change on
        UPDATE). A rerun computing a DIFFERENT result for the same row is
        nondeterminism — loud failure, never a silent overwrite."""
        assert result in ("true", "false", "unknown"), result
        self.conn.execute(
            "UPDATE public.ka_gochara_record_prerequisite SET result = %s"
            " WHERE record_id = %s AND ordinal = %s AND predicate_id = %s"
            " AND predicate_rule_version = %s",
            (result, str(record_id), ordinal, predicate_id,
             predicate_version),
        )
        row = self.conn.execute(
            "SELECT result FROM public.ka_gochara_record_prerequisite"
            " WHERE record_id = %s AND ordinal = %s",
            (str(record_id), ordinal),
        ).fetchone()
        _byte_check(row, (result,),
                    f"prerequisite result {record_id}/{ordinal} "
                    f"({predicate_id})")
        # F5 (1155): the record's admission_state must EQUAL the state derived
        # from its prerequisite results at COMMIT (any false ⇒ not_admitted;
        # else any unknown/unevaluated ⇒ unqualified; else admitted). Writing
        # a result without re-deriving the state is a COMMIT-time failure for
        # every record whose result is not 'unknown'. Derived IN SQL from the
        # stored results — the finalisation trigger is the detector that
        # catches this expression drifting from the contract's rule.
        self.conn.execute(
            "UPDATE public.ka_gochara_relationship_record SET admission_state ="
            " (SELECT CASE"
            "   WHEN count(*) FILTER (WHERE m.result = 'false') > 0"
            "     THEN 'not_admitted'"
            "   WHEN count(*) FILTER (WHERE m.result IS DISTINCT FROM 'true'"
            "                          AND m.result IS DISTINCT FROM 'false') > 0"
            "     THEN 'unqualified'"
            "   ELSE 'admitted' END"
            "  FROM public.ka_gochara_record_prerequisite m"
            "  WHERE m.record_id = %s)"
            " WHERE record_id = %s",
            (str(record_id), str(record_id)),
        )


# ── grain orchestration (one substep = one call = one transaction) ────────

def write_class_coverage(
    store: RecordStore,
    *,
    chart_id: str,
    generation: str,
    event_class: str,
    class_edges: Sequence[RecordEdge],
    horizon: tuple[datetime, datetime],
    position_at: Callable[[str, datetime], float] | None,
    sky_convention_id: str,
    kala_convention_id: str,
    build_id: str,
    arc_index_available: bool = False,
    inventory_facts: dict | None = None,
    ephemeral_tier_excluded: int = 0,
) -> None:
    """The `coverage:<event_class>` substep: ONE class-level event_class
    coverage partition (the frozen F7 key convention), written before any
    record grain of the class. Facts are the class's whole-generation
    declared search across every bound path (deterministic from the static
    enumeration — any grain recomputes the identical row, so pin-4
    insert-if-absent is consistent):

      * relations_searched — the relations this slice actually searches
        (residence with a probe; conjunction/aspect point solves when the
        arc index is available; natal_fact always); unsolved relations (no
        arc index in this run) are named in unsearched_reason, never
        searched silently;
      * targets — edge-level counts over the class's full enumeration:
        resolved = edges under searched relations, unavailable = edges
        under deferred/underivable ones;
      * resolution — the largest solve tolerance (arcsec) of the crossings
        actually read plus the point-solve arc-index tolerance when point
        solves are searched (N7); 0.0 with a named non-claim when no
        angular solve happened.
    """
    residence = [e for e in class_edges if e.transit and e.relation == "residence"]
    natal = [e for e in class_edges if not e.transit]
    point = [e for e in class_edges
             if e.transit and e.relation in POINT_KERNEL_RELATION
             and e.obj.canonical_target.startswith("point:")]
    aspect_span = [e for e in class_edges
                   if e.transit and e.relation == "aspect"
                   and e.obj.canonical_target.startswith("span:")]
    point_solved = bool(point) and arc_index_available
    # aspect-to-span derives from the body's residence spans: searched iff the position probe is
    aspect_span_solved = bool(aspect_span) and position_at is not None
    deferred = sorted({e.relation for e in class_edges
                       if e.transit and e.relation != "residence"
                       and e.relation not in POINT_KERNEL_RELATION})
    relations_searched = (
        (["residence"] if residence and position_at is not None else [])
        + (sorted({e.relation for e in point}) if point_solved else [])
        + (["aspect"] if aspect_span_solved and not point_solved else [])
        + (["natal_fact"] if natal else []))
    unavailable: dict = {}
    unsearched_parts: list[str] = []
    if point and not arc_index_available:
        unavailable["arc_index"] = ("no arc index in this run — point "
                                    "contacts unsolved (named, never fabricated)")
        unsearched_parts.append(DEFERRAL_POINT_SOLVE)
    if deferred:
        unsearched_parts.append("relations with no solver: "
                                + ", ".join(deferred))
    if ephemeral_tier_excluded:
        # named account of the tier this stored build does NOT own (AM-4): the Moon-agent transit
        # edges are excluded from the stored enumeration BY RULE (evaluator.EPHEMERAL_TIER_AGENTS)
        unavailable["moon_on_demand"] = (
            f"{ephemeral_tier_excluded} Moon-agent transit edge(s) excluded from the stored "
            "enumeration by rule: the Moon is an EPHEMERAL tier (AM-4) — served by a "
            "moon_on_demand partition at query time, never stored by this build")
        unsearched_parts.append("Moon-agent edges are on-demand (AM-4)")
    if aspect_span and not aspect_span_solved:
        unavailable["aspect_span_solver"] = (
            f"{len(aspect_span)} aspect-to-span edge(s) need the position probe (they derive from "
            "the body's residence spans) — unsolved, named, never fabricated")
        unsearched_parts.append("aspect-to-span needs the position probe")
    unsearched = "; ".join(unsearched_parts) or None
    if residence and position_at is None:
        unavailable["position_probe"] = ("ephemeris probe unavailable — no "
                                         "span derived (named, never fabricated)")
        unsearched = "; ".join(x for x in (
            unsearched, "residence spans underived without a position probe") if x)
    eps: list[float] = []
    if (residence or aspect_span_solved) and position_at is not None:
        for body in sorted({e.agent for e in residence + (aspect_span if aspect_span_solved else [])}):
            eps += [c.delta_lambda * 3600.0
                    for c in store.fetch_crossings(body, sky_convention_id)
                    if c.delta_lambda is not None]
    if point_solved:
        eps.append(POINT_SOLVE_INDEX_TOLERANCE_ARCSEC)
    resolution = max(eps) if eps else 0.0
    if not eps:
        unavailable["resolution"] = ("no angular solve in this class's searched "
                                     "relations — resolution not applicable "
                                     "(0.0 is a non-claim)")
    searched = (len(residence if position_at is not None else [])
                + (len(aspect_span) if aspect_span_solved else 0)
                + (len(point) if point_solved else 0) + len(natal))
    total = len(class_edges)
    if inventory_facts is not None:
        # AM-5: the partition is only the guard-facing SUMMARY of the stored inventory —
        # its horizon IS the inventory horizon and its relations_searched are EXACTLY the
        # obligations' distinct relations (`partition_overclaims` is a seal violation).
        horizon = inventory_facts["horizon"]
        relations_searched = list(inventory_facts["relations"])
        total = inventory_facts["obligations"]
        searched = total - inventory_facts["missing_inputs"]
        if inventory_facts["missing_inputs"]:
            unavailable["inventory"] = (f"{inventory_facts['missing_inputs']} obligation(s) "
                                        "carry a missing_inputs interval (a seal refusal)")
            unsearched = "; ".join(x for x in (unsearched, "obligations with missing inputs")
                                   if x)
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
    position_at: Callable[[str, datetime], float] | None,
    house_for: Callable[[RecordEdge, str], int | None],
    sky_convention_id: str,
    source_fact_ids: list[str],
    prerequisites: list[list[str]] | None = None,
    arc_index_for: Callable[[str], object] | None = None,
    ephe_path: str | None = None,
    refine: bool = True,
    dasha_rows_for: Callable[[str], list[dict]] | None = None,
    chart: dict | None = None,
) -> dict[str, int]:
    """Materialise one `record:<event_class>:<path_id>` grain: contacts,
    then records, bound to the class's ALREADY-WRITTEN coverage partition
    (pin 7 — the coverage substep runs first; a grain without it refuses
    via stored_coverage_facts_json, never orphans a record).

    `position_at(body, t)` probes sidereal longitudes for span
    derivation (one probe per interval; injected — this module never
    touches an ephemeris). Without it no transit span is derived: nothing
    is minted (the class coverage named the probe's absence), never
    fabricated.

    `arc_index_for(body)` (3/N point solves) yields the body's full-domain
    arc index for conjunction/aspect edges on point:<λ> targets. Without
    it no point contact is solved or minted (the class coverage named the
    deferral), never fabricated.
    """
    residence_edges = [e for e in edges if e.transit and e.relation == "residence"]
    # conjunction/aspect on `point:<λ>` are point-root solves; an `aspect` on a house `span:<sign>`
    # is the aspect point's ingress into the span — a DIFFERENT solve this slice does not have
    # (E8): its edges are never solved, never minted uncomputed, and never routed to the point
    # solver (which would assert on a span target). They are counted and named.
    point_edges = [e for e in edges
                   if e.transit and e.relation in POINT_KERNEL_RELATION
                   and e.obj.canonical_target.startswith("point:")]
    aspect_span_edges = [e for e in edges if e.transit and e.relation == "aspect"
                         and e.obj.canonical_target.startswith("span:")]
    # aspect-to-span derives from the body's residence spans (like residence itself), so it needs
    # the position probe: without one nothing is minted — counted and named, never fabricated
    aspect_span_deferred = len(aspect_span_edges) if position_at is None else 0
    natal_edges = [e for e in edges if not e.transit]
    skipped_natal_p1 = 0
    if path_id == "P1":
        # AM-11 pin (b): P1's natal-fact rows (contact_id NULL) are NOT admission-
        # bearing records — F5 demands every declared prerequisite and 1155 has no
        # "not applicable". Prerequisite (2) is evaluated on the TRANSIT record.
        skipped_natal_p1, natal_edges = len(natal_edges), []
    unwritable_testimony = 0
    _licence_cache: dict[str, dict] = {}

    def _p1_relation(agent: str) -> dict | None:
        """P1 prerequisite (2) via Stream B's permission.period_lord_relation over L1
        natal positions + sign lordship + the H truth table. None = not evaluable."""
        if chart is None:
            return None
        if agent not in _licence_cache:
            try:
                _licence_cache[agent] = rules_permission.period_lord_relation(
                    agent.title(), event_class, chart)
            except KeyError:           # the lord's natal position is unreadable
                _licence_cache[agent] = {"relation": "unknown", "licence": "none"}
        return _licence_cache[agent]

    def _unwritable(agent: str) -> bool:
        """A TESTIMONY-licence period lord (non-node dispositorship/association) has no
        ruling_ref to satisfy kgrr_ruling_ck (D3): its transit records are not minted —
        named in the counts, never silently dropped."""
        rel = _p1_relation(agent) if path_id == "P1" else None
        return bool(rel and rel["licence"] == "testimony")
    coverage_key = event_class
    if prerequisites is None:
        rule_version = edges[0].rule_version if edges else "1.0.0"
        prerequisites = store.fetch_path_prerequisites(path_id, rule_version)

    # Point solves (3/N): full-domain roots + ordinals, then the horizon
    # intersection — solved BEFORE any write, per edge.
    point_occs = solve_point_edges(
        point_edges, arc_index_for=arc_index_for, horizon=horizon,
        ephe_path=ephe_path, refine=refine) if point_edges else {}

    # Derive full-domain spans per body (stable ordinals), then intersect
    # with the requested horizon. One crossing read + one span set per body.
    spans_by_body: dict[str, list[ResidenceSpan]] = {}
    crossings_by_body: dict[str, dict[datetime, CrossingInfo]] = {}
    if (residence_edges or aspect_span_edges) and position_at is not None:
        for body in sorted({e.agent for e in residence_edges + aspect_span_edges}):
            infos = store.fetch_crossings(body, sky_convention_id)
            crossings_by_body[body] = {c.t: c for c in infos}
            spans_by_body[body] = residence_spans(
                [BoundaryCrossing(t=c.t, level_deg=c.level_deg) for c in infos],
                horizon=(SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END),
                position_at=lambda t, b=body: position_at(b, t),
            )

    # Work list (pass 1, no writes): the in-horizon minted occurrences with
    # their house resolved. kgrr_evaluated_has_house_ck requires
    # house_from_frame on every computed row — an occurrence whose frame
    # anchor is unknown is NOT minted (a state, never an omission).
    h_start, h_end = horizon
    work: list[tuple[RecordEdge, dict, int]] = []
    for e in residence_edges + (aspect_span_edges if position_at is not None else []):
        body_spans = spans_by_body.get(e.agent, [])
        if not body_spans:
            continue
        if e.relation == "aspect":
            # aspect-to-span: the contiguous runs of the body's residence spans over the aspect
            # source signs, labelled with the target sign (materialise.aspect_spans)
            body_spans = aspect_spans(
                body_spans, body=e.agent,
                target_sign=targets.span_sign_name(e.obj.canonical_target))
            if not body_spans:
                continue
        for m in mint_transit_records(
                e, body_spans, chart_id=chart_id, generation=generation,
                prerequisites=prerequisites):
            span = m["span"]
            if not (span.t_in < h_end and (span.t_out is None or span.t_out > h_start)):
                continue  # full-domain span outside the requested horizon
            # The stored contact and record SUPPORT must lie inside the class partition's
            # completed horizon (F7/C7, enforced by the database): clip the full-domain span to the
            # requested half-open horizon [h_start, h_end). An ingress before h_start is not an
            # exact instant of THIS horizon — t_exact NULL, a truncated span (N3), never absence;
            # an egress after h_end is open-ended (t_out NULL ⇒ truncated at the horizon's end).
            # Identity is untouched: ordinals were assigned over the full-domain set above.
            span = ResidenceSpan(
                sign=span.sign, t_in=max(span.t_in, h_start),
                t_out=span.t_out if (span.t_out is not None and span.t_out <= h_end) else None,
                t_exact=(span.t_exact if (span.t_exact is not None
                                          and h_start <= span.t_exact < h_end) else None),
                truncated=span.truncated or span.t_in < h_start
                or span.t_out is None or span.t_out > h_end)
            m = {**m, "span": span, "span_full_domain": m["span"]}
            house = house_for(e, span.sign)
            if house is None:
                continue
            if _unwritable(e.agent):
                unwritable_testimony += 1
                continue
            work.append((e, m, house))

    # Point occurrences (3/N): house from the TARGET point's sign (the natal
    # house the transit contacts). An unresolvable anchor ⇒ not minted
    # (kgrr_evaluated_has_house_ck — a state, never an omission).
    point_work: list[tuple[RecordEdge, PointOccurrence, str, int]] = []
    for e in point_edges:
        occs = point_occs.get(id(e), [])
        if not occs:
            continue
        target = e.obj.canonical_target
        assert target.startswith("point:"), target
        sign = sign_of(float(target[len("point:"):]) % 360.0)
        for occ in occs:
            house = house_for(e, sign)
            if house is None:
                continue
            if _unwritable(e.agent):
                unwritable_testimony += 1
                continue
            key = e.natural_key(
                chart_id=chart_id, generation=generation,
                contact_id=str(occ.contact.contact_id),
                prerequisites=prerequisites, source_text=e.source_text)
            point_work.append((e, occ, record_uuid(key), house))

    coverage_facts = store.stored_coverage_facts_json(
        chart_id=chart_id, generation=generation, event_class=event_class)
    # AM-3/§N.3: a candidate rebuild REPLACES the grain — its windows, records
    # and the contacts only they used are deleted (dependency order) and the
    # derived rows inserted afresh. Coverage presence is checked FIRST (above),
    # so a grain without its partition refuses with no side effect; a sealed
    # generation is refused by the store; a contact another path still
    # references survives.
    store.delete_record_grain(
        chart_id=chart_id, generation=generation, event_class=event_class,
        path_id=path_id,
        rule_version=edges[0].rule_version if edges else RULE_VERSION)
    counts = {"contacts": 0, "records": 0, "natal_records": 0,
              "truncated_contacts": 0, "prereq_evaluated": 0,
              "skipped_natal_p1": skipped_natal_p1,
              "aspect_span_deferred": aspect_span_deferred,
              "unwritable_testimony": unwritable_testimony,
              "p3_enumeration_defects": 0}
    # Per-record evaluation context for the prerequisite result pass below
    # (v1.0 item 5): the occurrence instant (t_exact; the observed span
    # start for a truncated contact — flagged v1.5 binding) and the support
    # interval. Natal rows carry neither — atemporal claims.
    evaluated: list[dict] = []
    supports_by_agent: dict[str, list[tuple[datetime, datetime]]] = {}
    searched_agents: set[str] = set()
    if position_at is not None:
        searched_agents |= {e.agent for e in residence_edges + aspect_span_edges}
    if arc_index_for is not None:
        searched_agents |= {e.agent for e in point_edges}
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
        # kgrr_transit_natal_ck: a TRANSIT record always restates a precision object (N7); a
        # truncated contact restates 'clipped_truncated' with null deltas (1155 precision_ok)
        precision = ({
            "solver_method": crossing.solver_method if crossing else "swiss_refined",
            "delta_lambda": crossing.delta_lambda if crossing else None,
            "delta_t": crossing.delta_t if crossing else None,
        } if span.t_exact is not None else {
            "solver_method": "clipped_truncated", "delta_lambda": None, "delta_t": None})
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
        full = m["span_full_domain"]
        evaluated.append({
            "record_id": m["record_id"], "edge": edge, "kind": "transit",
            "house": house,
            # the occurrence instant is the EXACT ingress even when it lies before the requested
            # horizon (the stored contact is clipped; the evaluation is not — v1.5 binding)
            "instant": full.t_exact or full.t_in,
            "support": (span.t_in, span.t_out or h_end)})
        supports_by_agent.setdefault(edge.agent, []).append(
            (span.t_in, span.t_out or h_end))
    for edge, occ, record_id, house in point_work:
        store.insert_point_contact(
            chart_id=chart_id, generation=generation, occ=occ,
            poid=edge.obj, convention_id=sky_convention_id)
        counts["contacts"] += 1
        counts["truncated_contacts"] += 1 if occ.truncated else 0
        precision = ({
            "solver_method": occ.solver_method,
            "delta_lambda": occ.delta_lambda,
            "delta_t": occ.delta_t,
        } if occ.t_exact is not None else {
            "solver_method": "clipped_truncated", "delta_lambda": None, "delta_t": None})
        interval = f"[{occ.t_in.isoformat()},{occ.t_out.isoformat()})"
        store.insert_record(
            chart_id=chart_id, generation=generation, edge=edge,
            record_id=record_id,
            contact_id=str(occ.contact.contact_id),
            support_state="computed", support_intervals=[interval],
            precision=precision, coverage_key=coverage_key,
            coverage_facts=coverage_facts, source_fact_ids=source_fact_ids,
            prerequisites=prerequisites, house_from_frame=house)
        counts["records"] += 1
        evaluated.append({
            "record_id": record_id, "edge": edge, "kind": "transit",
            "house": house,
            "instant": occ.t_exact or occ.t_in,
            "support": (occ.t_in, occ.t_out)})
        supports_by_agent.setdefault(edge.agent, []).append(
            (occ.t_in, occ.t_out))
    for edge in natal_edges:
        m = mint_natal_record(edge, chart_id=chart_id, generation=generation,
                              prerequisites=prerequisites)
        store.ensure_object(edge.obj)      # insert-if-absent: the natal row's FK target
        store.insert_record(
            chart_id=chart_id, generation=generation, edge=edge,
            record_id=m["record_id"], contact_id=None,
            support_state="uncomputed", support_intervals=[],
            precision=None, coverage_key=coverage_key,
            coverage_facts=coverage_facts, source_fact_ids=source_fact_ids,
            prerequisites=prerequisites)
        counts["natal_records"] += 1
        evaluated.append({"record_id": m["record_id"], "edge": edge, "kind": "natal",
                          "house": None, "instant": None, "support": None})

    # Prerequisite result evaluation at materialisation (steward 2026-10-02, from
    # Stream B's PREREQUISITE_EVALUATION_ANSWER; AM-11): EVERY declared prerequisite of
    # the path is evaluated — none hard-coded, none left NULL on a decidable predicate
    # ("unevaluated" is not "unknown", §N.8; an undecidable one is stored as an EXPLICIT
    # 'unknown'). The 1155 trigger's result_only path; the record's admission_state is
    # re-derived with each result (F5). The rule logic is Stream B's
    # (gochara_rules.permission / registry / favourable_houses / admission): called,
    # never re-implemented here.
    contact_keys = (store.stored_contact_keys(chart_id=chart_id, generation=generation)
                    if any(r["kind"] == "transit" for r in evaluated) else set())

    def _period_running_at(rec):
        if dasha_rows_for is None or rec["kind"] != "transit":
            return "unknown"           # no L1 dasha reader / atemporal row
        rows = dasha_rows_for(rec["edge"].agent)
        if not rows:
            return "unknown"           # L1 dasha rows absent — never false
        return rule_predicates.evaluate(
            "period_running_at",
            {"rows": [_dasharow(r) for r in rows], "t": rec["instant"]})

    def _p4_double_transit(rec):
        agent = rec["edge"].agent
        other = {"jupiter": "saturn", "saturn": "jupiter"}.get(agent)
        assert other is not None, (
            f"P4 record on non-Jupiter/Saturn agent {agent!r} — "
            "O-RP-3 violated upstream, refusing to evaluate")
        if other not in searched_agents:
            return "unknown"           # the other planet was not searched
        for b_span in supports_by_agent.get(other, []):
            if rule_predicates.evaluate(
                    "overlaps", {"a": rec["support"], "b": b_span}) == "true":
                return rule_predicates.TRUE
        return rule_predicates.FALSE

    def _natal_bhava_relationship(rec):
        rel = _p1_relation(rec["edge"].agent)
        if rel is None or rel["relation"] == "unknown":
            return "unknown"           # H unknown / lord's natal position unreadable
        # scored AND testimony kinds store 'true' (AM-11 pin a): the record's ROLE, not
        # the result, stops a testimony kind admitting; 'none' is a real false.
        return "true" if rel["licence"] in ("scored", "testimony") else "false"

    def _transit_relation(rec):
        if rec["kind"] != "transit":
            return "unknown"           # a natal annotation has no transit contact
        obj = rec["edge"].obj
        # READ-BACK of the stored contact rows — never a literal true (AM-11 pin b)
        return rule_predicates.evaluate(
            "declaration_exists",
            {"declarations": contact_keys,
             "key": (obj.body, obj.relation_kind, str(obj.uuid))})

    def _house_from_moon(rec):
        edge = rec["edge"]
        if (chart is None or "Moon" not in (chart.get("natal") or {})
                or edge.frame_kind != "moon" or rec["house"] is None):
            return "unknown"           # natal Moon unreadable / not a Moon-frame row
        agent = edge.agent.title()
        try:
            cited = set(rules_favourable.favourable_houses(agent))
        except (KeyError, ValueError):
            return "unknown"           # no cited set for this graha
        # AM-11 pin (c): h in the cited favourable ∪ adverse set; POLARITY (the D-RQ5
        # evidence channel) belongs to the valence step, not to admission.
        if agent in rules_admission.ADVERSE_RESIDENCE_BODIES:
            cited |= set(rules_admission.ADVERSE_RESIDENCE_HOUSES)
        return "true" if rec["house"] in cited else "false"

    def _p3_contact_house_or_lord(rec):
        edge = rec["edge"]
        if chart is None or rec["kind"] != "transit":
            return "unknown"
        houses = rules_registry.signature_houses(event_class, chart)
        if houses is None:
            return "unknown"           # H unknown (the eight classes)
        lords = rules_registry.signature_lords(event_class, chart) or frozenset()
        target = edge.obj.canonical_target
        if edge.object_role == "signature_house":
            ok = (edge.relation in ("residence", "aspect")
                  and target in {targets.span_target(sg) for sg in houses})
        elif edge.object_role == "lord":
            if any(lord not in chart["natal"] for lord in lords):
                return "unknown"       # a lord's natal position is unreadable
            ok = (edge.relation in ("conjunction", "aspect")
                  and target in {targets.point_target(chart["natal"][lord])
                                 for lord in lords})
        else:
            ok = False
        if not ok:
            # an enumeration defect: the record names an object outside H ∪ L(H) or a
            # relation not permitted for its kind — reported loudly, never absorbed
            counts["p3_enumeration_defects"] += 1
            logger.error("[ka_gochara_v5] P3 enumeration defect: %s %s %s %s not in H ∪ L(H)",
                         event_class, edge.agent, edge.relation, target)
        return "true" if ok else "false"

    _EVALUATORS = {
        "period_running_at": _period_running_at,
        "p4_double_transit": _p4_double_transit,
        "natal_bhava_relationship": _natal_bhava_relationship,
        "transit_relation": _transit_relation,
        "house_from_moon": _house_from_moon,
        "p3_contact_house_or_lord": _p3_contact_house_or_lord,
    }
    for rec in evaluated:
        for ordinal, (pid, _pv) in enumerate(prerequisites, start=1):
            fn = _EVALUATORS.get(pid)
            if fn is None:
                # P5/P6 predicates: no P5/P6 record is materialised by this grain
                continue
            store.set_prerequisite_result(
                record_id=rec["record_id"], ordinal=ordinal, predicate_id=pid,
                predicate_version=rec["edge"].rule_version, result=fn(rec))
            counts["prereq_evaluated"] += 1
    return counts


def _edge_sign(edge: RecordEdge) -> str:
    return targets.span_sign_name(edge.obj.canonical_target)


__all__ = [
    "CrossingInfo",
    "DEFERRAL_POINT_SOLVE",
    "KALA_CONVENTION_VECTOR",
    "MissingCoverageError",
    "SealedGenerationError",
    "POINT_KERNEL_RELATION",
    "POINT_ORB_SOURCE",
    "POINT_SOLVE_INDEX_TOLERANCE_ARCSEC",
    "PointOccurrence",
    "RecordStore",
    "SUPPORT_GRAIN_SPAN",
    "materialise_record_grain",
    "solve_point_edges",
    "write_class_coverage",
]
