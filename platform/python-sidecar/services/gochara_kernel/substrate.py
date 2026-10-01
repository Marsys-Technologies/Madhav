"""Sky-event substrate (GOCHARA_DESIGN_SPECS v1.4 §6/§6.1) — identity layer.

A5.3 geometry_store, implementation pins (steward 2026-10-01,
M20261001T015412-6df0; A5_3_REGISTERED_WRITER_BRIEF_v1_0.md).

Identity (pin 4, spec §6.1):
  * canonical identity bytes: `body|relation_kind|canonical_target|convention_id`
    for the physical object, `…|ordinal` for one contact — rendered with the
    body/relation/target EXACTLY as given (the serialization is pinned by
    oracle O-RX-1: 'Mars|conjunction|point:198.52|c0|1').
  * ids: sha256 over those canonical bytes, first 128 bits as a UUID with
    version-8/variant bits set (kernel canonical_digest precedent; no
    SHA-1/UUIDv5). A collision on insert is a loud build failure, never a
    silent dedup.
  * occurrence ordinals are assigned over the full-domain ordered crossing
    set of one physical tuple, ordered by solved t_exact. Partition extension
    inside the domain appends only: existing ordinals and published
    contact ids never change (R3 amendment 1).

`physical_object_id(...)` returns a `PhysicalObjectId` — the identity itself:
it carries the canonical components (so the store and the ordinal assigner
never re-ask for them) and hashes/compares by its §6.1 UUID. The persistence
layer stores `.uuid` (and the body lowercased for the kgpo_body_domain_ck
domain); the serialization always preserves the caller's casing.

The WP1 §3.2 scheme (ids.py: floored-minute t_exact inside the hash) is
explicitly forbidden here by spec §6.1 — rounded-time hashing splits one
crossing across precisions and role-qualified targets split one physical
contact across roles. This module never hashes a timestamp.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence


def _uuid8_of(canonical_bytes: bytes) -> uuid.UUID:
    """First 128 bits of sha256, version-8 / variant bits set (pin 4)."""
    digest = bytearray(hashlib.sha256(canonical_bytes).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80  # version 8
    digest[8] = (digest[8] & 0x3F) | 0x80  # RFC 4122 variant
    return uuid.UUID(bytes=bytes(digest))


@dataclass(frozen=True)
class PhysicalObjectId:
    """§6.1 physical-object identity: the canonical tuple plus its UUID.

    Equality and hashing are by the UUID alone — one physical object is one
    (body, relation_kind, canonical_target, convention_id) tuple, never a
    role- or label-qualified one.
    """

    body: str
    relation_kind: str
    canonical_target: str
    convention_id: str

    @property
    def identity_bytes(self) -> str:
        """§6.1 canonical serialization (no ordinal component)."""
        return (
            f"{self.body}|{self.relation_kind}"
            f"|{self.canonical_target}|{self.convention_id}"
        )

    @property
    def uuid(self) -> uuid.UUID:
        return _uuid8_of(self.identity_bytes.encode("utf-8"))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PhysicalObjectId):
            return self.uuid == other.uuid
        if isinstance(other, uuid.UUID):
            return self.uuid == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.uuid)


def physical_object_id(
    *, body: str, relation_kind: str, canonical_target: str, convention_id: str
) -> PhysicalObjectId:
    """§6.1: identity of hash(body, relation_kind, canonical_target,
    convention_id) — returned with its components (O-RX-1's assigner
    reconstructs the canonical bytes from the identity alone)."""
    return PhysicalObjectId(
        body=body,
        relation_kind=relation_kind,
        canonical_target=canonical_target,
        convention_id=convention_id,
    )


@dataclass(frozen=True)
class SubstrateContact:
    """One contact of a physical object: an occurrence under §6.1."""

    physical_object_id: PhysicalObjectId
    occurrence_ordinal: int
    t_exact: datetime | None  # None only for a truncated span (N3)

    @property
    def contact_id(self) -> uuid.UUID:
        """§6.1/NK-2: hash(physical_object_id, occurrence_ordinal) — via the
        canonical identity bytes (never a rounded t_exact)."""
        return _uuid8_of(contact_identity_bytes(self).encode("utf-8"))


def contact_identity_bytes(contact: SubstrateContact) -> str:
    """§6.1 canonical serialization:
    `body|relation_kind|canonical_target|convention_id|ordinal`."""
    return f"{contact.physical_object_id.identity_bytes}|{contact.occurrence_ordinal}"


def assign_occurrence_ordinals(
    *,
    physical_object_id: PhysicalObjectId,
    t_exact_list: Sequence[datetime],
) -> list[SubstrateContact]:
    """Ordinals 1..N over the full-domain ordered crossing set of one tuple.

    Ordered by solved t_exact at full precision (stable: equal instants keep
    input order). Append-only stable: re-running with additional, later
    crossings leaves every earlier ordinal and contact id unchanged (R3
    amendment 1) — the caller passes the FULL domain set, never a clipped
    partition.
    """
    ordered = sorted(enumerate(t_exact_list), key=lambda pair: (pair[1], pair[0]))
    return [
        SubstrateContact(
            physical_object_id=physical_object_id,
            occurrence_ordinal=ordinal,
            t_exact=t_exact,
        )
        for ordinal, (_, t_exact) in enumerate(ordered, start=1)
    ]


# ── Convention (pin 3) ────────────────────────────────────────────────────────

#: Domain pinned in the convention (spec §6.1 / migration 1153 self-test):
#: 1998-01-01 → 2085-01-01 UTC. A backward partition is a new convention_id.
SUBSTRATE_DOMAIN_START = datetime(1998, 1, 1, tzinfo=timezone.utc)
SUBSTRATE_DOMAIN_END = datetime(2085, 1, 1, tzinfo=timezone.utc)

#: The A5.3 convention vector (pin 3). `grid` is the kernel's existing grid
#: declaration; `method_version` the kernel's existing constant.
SUBSTRATE_CONVENTION_VECTOR = {
    "ephemeris_generation": "pyswisseph:20230604/swisseph:2.10.03",
    "ayanamsha": "lahiri_chitrapaksha",
    # L1's convention for 482012f1, read from chart_facts (mean node;
    # graha_position subjects RAH_MEAN/KET_MEAN — fact_id c520713087b97470).
    "node_convention": "mean",
    # AM-1 (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5): the nakṣatra span is
    # 13°20′ = 13⅓°, rendered `13d20m` — NEVER the decimal `13.20` (13.20° ≠
    # 13°20′). This deliberately corrects the 694d16e9c vector; it changes the
    # canonical bytes and therefore the convention_id, so it must land before
    # any row is written under the id (no production row exists yet).
    "grid": "sign:30/nakshatra:13d20m/kakshya:3.75/seam:0",
    "method_version": "1.0.0",
    "domain_start": "1998-01-01T00:00:00Z",
    "domain_end": "2085-01-01T00:00:00Z",
}


def convention_id_for(vector: dict[str, str] | None = None) -> str:
    """convention_id = sha256 tag over the canonical vector incl. the domain
    (spec §6.1: the ordinal domain is pinned in convention_id)."""
    v = vector if vector is not None else SUBSTRATE_CONVENTION_VECTOR
    canonical = "|".join(f"{k}={v[k]}" for k in sorted(v))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "SUBSTRATE_CONVENTION_VECTOR",
    "SUBSTRATE_DOMAIN_END",
    "SUBSTRATE_DOMAIN_START",
    "PhysicalObjectId",
    "SubstrateContact",
    "assign_occurrence_ordinals",
    "contact_identity_bytes",
    "convention_id_for",
    "physical_object_id",
]


# ── Sky-event store (persistence over migration 1153's §6.1 tables) ──────────

import json as _json
import os as _os
from typing import Any as _Any


class ConventionDivergenceError(RuntimeError):
    """Pin 3: a convention row exists under this convention_id with ANY
    different field — loud failure, never a silent reuse."""


class IdentityCollisionError(RuntimeError):
    """Pin 4: an id collision where the stored row is not byte-identical —
    loud build failure, never a silent dedup."""


#: Kernel body name → substrate (DB) body domain value (kgpo/kgse body checks).
DB_BODY = {
    "Sun": "sun", "Mars": "mars", "Mercury": "mercury", "Jupiter": "jupiter",
    "Venus": "venus", "Saturn": "saturn", "Rahu": "rahu", "Ketu": "ketu",
    "Moon": "moon",
}

#: Kernel boundary relation → §6.1 event_kind (kgse_event_kind_ck).
DB_EVENT_KIND = {
    "sign_ingress": "sign_ingress",
    "nakshatra_ingress": "nakshatra_ingress",
    "kakshya_cell_crossing": "kakshya_crossing",
}

#: The global substrate bodies — every body but the Moon (pin 6: Moon is
#: EPHEMERAL, generated on demand; kgse_body_domain_ck enforces it at the DB).
SUBSTRATE_BODIES = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

JD_UNIX_EPOCH = 2440587.5


def jd_to_utc(jd: float) -> datetime:
    return datetime.fromtimestamp((float(jd) - JD_UNIX_EPOCH) * 86400.0, tz=timezone.utc)


def boundary_target(level_deg: float) -> str:
    """§6.1 canonical target of a boundary crossing: `point:<λ full precision>`
    (boundary events are enumerated per body and joined to targets afterwards
    — §6.2 inv 5 — so the physical target is the boundary itself)."""
    return f"point:{float(level_deg)!r}"


@dataclass(frozen=True)
class SkyEvent:
    event_id: uuid.UUID
    physical_object_id: uuid.UUID
    convention_id: str
    body: str
    event_kind: str
    occurrence_ordinal: int
    t_exact: datetime | None
    longitude: float | None
    solver_method: str
    delta_lambda: float | None
    delta_t: float | None
    precision_regime: str | None
    coverage: dict


class SkyEventStore:
    """Persistence over ka_gochara_sky_convention / ka_gochara_physical_object /
    ka_gochara_sky_event (migration 1153, spec §6.1).

    Write side honours pin 3 (convention row: idempotent under the chart lock,
    any field divergence = loud failure) and pin 4 (id collision with a
    non-identical stored row = loud build failure). The tables are
    insert-only (triggers): idempotency here means insert-if-absent with a
    byte-equality check, never delete-then-insert.
    """

    def __init__(self, conn):
        self.conn = conn

    @classmethod
    def from_env(cls) -> "SkyEventStore":
        import psycopg

        dsn = _os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("SkyEventStore.from_env: DATABASE_URL not set")
        return cls(psycopg.connect(dsn))

    # ── read side ────────────────────────────────────────────────────────

    def count_rows(self, *, body: str | None = None) -> int:
        if body is None:
            row = self.conn.execute(
                "SELECT count(*) FROM public.ka_gochara_sky_event"
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT count(*) FROM public.ka_gochara_sky_event WHERE body = %s",
                (DB_BODY.get(body, body.lower()),),
            ).fetchone()
        return int(row[0])

    def events(self, *, event_kind: str | None = None, body: str | None = None) -> list[SkyEvent]:
        sql = ("SELECT event_id, physical_object_id, convention_id, body, event_kind,"
               " occurrence_ordinal, t_exact, longitude, solver_method, delta_lambda,"
               " delta_t, precision_regime, coverage FROM public.ka_gochara_sky_event")
        clauses, params = [], []
        if event_kind is not None:
            clauses.append("event_kind = %s")
            params.append(event_kind)
        if body is not None:
            clauses.append("body = %s")
            params.append(DB_BODY.get(body, body.lower()))
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY t_exact NULLS LAST, event_id"
        out = []
        for r in self.conn.execute(sql, tuple(params)).fetchall():
            out.append(SkyEvent(
                event_id=r[0], physical_object_id=r[1], convention_id=r[2],
                body=r[3], event_kind=r[4], occurrence_ordinal=r[5],
                t_exact=r[6], longitude=r[7], solver_method=r[8],
                delta_lambda=r[9], delta_t=r[10], precision_regime=r[11],
                coverage=r[12],
            ))
        return out

    # ── convention (pin 3) ───────────────────────────────────────────────

    def register_convention(self, vector: dict[str, str] | None = None) -> str:
        """Insert the convention row idempotently UNDER THE CHART LOCK (the
        caller's transaction declares gochara5.chart / holds the chart family
        key — the substrate chart-lock trigger enforces it). A row that
        already exists with ANY different field is a loud failure."""
        v = vector if vector is not None else SUBSTRATE_CONVENTION_VECTOR
        cid = convention_id_for(v)
        row = self.conn.execute(
            "SELECT ephemeris_generation, ayanamsha, node_convention, grid,"
            " method_version, domain_start, domain_end"
            " FROM public.ka_gochara_sky_convention WHERE convention_id = %s",
            (cid,),
        ).fetchone()
        if row is not None:
            def _utc_iso(dt: datetime) -> str:
                # timestamptz arrives in the SESSION tz; compare in UTC or a
                # non-UTC session fabricates a false divergence (pin 3 must
                # fire on real divergence, never on tz rendering)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            stored = {
                "ephemeris_generation": row[0], "ayanamsha": row[1],
                "node_convention": row[2], "grid": row[3], "method_version": row[4],
                "domain_start": _utc_iso(row[5]),
                "domain_end": _utc_iso(row[6]),
            }
            declared = {k: v[k] for k in stored}
            if stored != declared:
                raise ConventionDivergenceError(
                    f"convention {cid}: stored row diverges from the declared "
                    f"vector — stored {stored} vs declared {declared}"
                )
            return cid
        self.conn.execute(
            "INSERT INTO public.ka_gochara_sky_convention ("
            " convention_id, ephemeris_generation, ayanamsha, node_convention,"
            " grid, method_version, domain_start, domain_end)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (convention_id) DO NOTHING",
            (cid, v["ephemeris_generation"], v["ayanamsha"], v["node_convention"],
             v["grid"], v["method_version"], v["domain_start"], v["domain_end"]),
        )
        return cid

    # ── identity-bearing inserts (pin 4: collision = loud failure) ───────

    def insert_physical_object(self, poid: PhysicalObjectId) -> uuid.UUID:
        obj_uuid = poid.uuid
        self.conn.execute(
            "INSERT INTO public.ka_gochara_physical_object ("
            " physical_object_id, body, relation_kind, canonical_target, convention_id)"
            " VALUES (%s,%s,%s,%s,%s)"
            " ON CONFLICT (body, relation_kind, canonical_target, convention_id) DO NOTHING",
            (str(obj_uuid), DB_BODY[poid.body], poid.relation_kind,
             poid.canonical_target, poid.convention_id),
        )
        row = self.conn.execute(
            "SELECT physical_object_id FROM public.ka_gochara_physical_object"
            " WHERE body = %s AND relation_kind = %s AND canonical_target = %s"
            " AND convention_id = %s",
            (DB_BODY[poid.body], poid.relation_kind, poid.canonical_target,
             poid.convention_id),
        ).fetchone()
        if row is None or str(row[0]) != str(obj_uuid):
            raise IdentityCollisionError(
                f"physical object {poid.identity_bytes}: stored id "
                f"{row[0] if row else None} != derived {obj_uuid}"
            )
        return obj_uuid

    def insert_event(self, contact: SubstrateContact, *, event_kind: str,
                     longitude: float | None, solver_method: str,
                     delta_lambda: float | None, delta_t: float | None,
                     precision_regime: str | None,
                     coverage: dict) -> uuid.UUID:
        event_id = contact.contact_id
        poid = contact.physical_object_id
        truncated = bool(coverage.get("truncated", False))
        self.conn.execute(
            "INSERT INTO public.ka_gochara_sky_event ("
            " event_id, physical_object_id, convention_id, body, event_kind,"
            " occurrence_ordinal, t_exact, longitude, solver_method, delta_lambda,"
            " delta_t, precision_regime, coverage)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (physical_object_id, occurrence_ordinal) DO NOTHING",
            (str(event_id), str(poid.uuid), poid.convention_id, DB_BODY[poid.body],
             event_kind, contact.occurrence_ordinal,
             None if truncated else contact.t_exact, longitude, solver_method,
             delta_lambda, delta_t, precision_regime, _json.dumps(coverage)),
        )
        row = self.conn.execute(
            "SELECT event_id FROM public.ka_gochara_sky_event"
            " WHERE physical_object_id = %s AND occurrence_ordinal = %s",
            (str(poid.uuid), contact.occurrence_ordinal),
        ).fetchone()
        if row is None or str(row[0]) != str(event_id):
            raise IdentityCollisionError(
                f"event {contact_identity_bytes(contact)}: stored id "
                f"{row[0] if row else None} != derived {event_id}"
            )
        return event_id

    # ── phase-1 build: per-body boundary substrate + stations (pin 5) ────

    def build_boundary_substrate(
        self,
        body: str,
        *,
        index=None,
        ephe_path: str | None = None,
        refine: bool = True,
        convention_id: str | None = None,
    ) -> dict[str, int]:
        """Solve and persist one body's boundary events + stations over the
        pinned convention domain (1998-01-01 → 2085-01-01 UTC).

        The Moon is REFUSED (pin 6: EPHEMERAL; kgse_body_domain_ck also
        enforces it). Idempotent: every insert is insert-if-absent with a
        byte-identity check (pin 4), so a re-run of a completed body is a
        no-op and a partial earlier run resumes where it stopped.

        `index` may inject a prebuilt ArcIndex (tests); otherwise knots are
        sampled over the full domain and indexed per the kernel's defaults.
        Stations are always Swiss-refined (§7.1 / O-SM-3).
        """
        if body == "Moon":
            raise ValueError(
                "Moon boundary events are EPHEMERAL (pin 6 / §6.1): generated "
                "on demand with a moon_on_demand coverage record, never "
                "materialised into the global substrate"
            )
        if body not in SUBSTRATE_BODIES:
            raise ValueError(f"{body}: not a substrate body {SUBSTRATE_BODIES}")
        from services.gochara_kernel import arcs as gk_arcs
        from services.gochara_kernel import contacts as gk_contacts
        from services.gochara_kernel.knots import sample_knots

        cid = convention_id or self.register_convention()
        if index is None:
            ks = sample_knots(body, SUBSTRATE_DOMAIN_START.date(),
                              SUBSTRATE_DOMAIN_END.date(), ephe_path)
            index = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)

        solver_method = "swiss_refined" if refine else "arc_index_bracket"
        precision_regime = (
            "swiss_bisect_tol_1e-9d" if refine
            else f"arc_index_bracket_{index.tolerance_arcsec}arcsec"
        )
        delta_lambda = index.tolerance_arcsec / 3600.0
        delta_t = 1e-9 if refine else None

        counts = {"objects": 0, "events": 0, "stations": 0}
        for relation, event_kind in DB_EVENT_KIND.items():
            for level in gk_contacts.boundary_degrees(relation):
                poid = physical_object_id(
                    body=body, relation_kind=event_kind,
                    canonical_target=boundary_target(level), convention_id=cid,
                )
                self.insert_physical_object(poid)
                counts["objects"] += 1
            roots = gk_contacts.find_boundary_roots(
                index, body, relation, ephe_path, refine=refine
            )
            by_level: dict[float, list[datetime]] = {}
            for root in roots:
                by_level.setdefault(root.level_deg, []).append(jd_to_utc(root.exact_jd))
            for level, instants in by_level.items():
                poid = physical_object_id(
                    body=body, relation_kind=event_kind,
                    canonical_target=boundary_target(level), convention_id=cid,
                )
                for contact in assign_occurrence_ordinals(
                    physical_object_id=poid, t_exact_list=instants
                ):
                    self.insert_event(
                        contact, event_kind=event_kind, longitude=level % 360.0,
                        solver_method=solver_method, delta_lambda=delta_lambda,
                        delta_t=delta_t, precision_regime=precision_regime,
                        coverage={"truncated": False},
                    )
                    counts["events"] += 1

        # Stations — each at its own solved longitude (one object, ordinal 1);
        # ALWAYS swiss_refined (§7.1: δt unstable near a station).
        for jd_station in index.stations:
            lon = float(index.evaluate(jd_station)) % 360.0
            poid = physical_object_id(
                body=body, relation_kind="station",
                canonical_target=boundary_target(lon), convention_id=cid,
            )
            self.insert_physical_object(poid)
            counts["objects"] += 1
            (contact,) = assign_occurrence_ordinals(
                physical_object_id=poid, t_exact_list=[jd_to_utc(jd_station)]
            )
            self.insert_event(
                contact, event_kind="station", longitude=lon,
                solver_method="swiss_refined", delta_lambda=delta_lambda,
                delta_t=1e-9, precision_regime="swiss_bisect_tol_1e-9d",
                coverage={"truncated": False},
            )
            counts["stations"] += 1
        return counts


__all__ += [
    "ConventionDivergenceError",
    "DB_BODY",
    "DB_EVENT_KIND",
    "IdentityCollisionError",
    "SUBSTRATE_BODIES",
    "SkyEvent",
    "SkyEventStore",
    "boundary_target",
    "jd_to_utc",
]
