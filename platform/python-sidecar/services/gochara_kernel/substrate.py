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
    "grid": "sign:30/nakshatra:13.20/kakshya:3.75/seam:0",
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
