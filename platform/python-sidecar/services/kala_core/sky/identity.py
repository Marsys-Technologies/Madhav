"""Canonical physical identity of sky events (Gochara spec v1.4 §6.1).

The kernel's identity layer is imported, never restated: one physical object
is `body|relation_kind|point:<λ>|convention_id`, one occurrence adds its
ordinal. Body spellings from the kernel, the Kāla vocabulary or the stored
lowercase domain resolve to one token, so the same crossing reached through
two source paths has one id. A time is never hashed.
"""
from __future__ import annotations

import uuid
from typing import Iterable, Protocol

from services.gochara_kernel import targets
from services.gochara_kernel.substrate import (
    DB_BODY, DB_EVENT_KIND, IdentityCollisionError, PhysicalObjectId,
    SubstrateContact, physical_object_id,
)
from services.kala_core.vocab import GrahaId

# Vocabulary ids for the mean nodes map to the kernel's node names; the true
# nodes are a different convention and have no identity here.
_VOCAB_BODY = {
    GrahaId.SUN: "Sun", GrahaId.MOON: "Moon", GrahaId.MARS: "Mars",
    GrahaId.MERCURY: "Mercury", GrahaId.JUPITER: "Jupiter", GrahaId.VENUS: "Venus",
    GrahaId.SATURN: "Saturn", GrahaId.RAHU_MEAN: "Rahu", GrahaId.KETU_MEAN: "Ketu",
}
_STORED_BODY = {token: name for name, token in DB_BODY.items()}

# Two crossings of one physical object closer than this are one crossing seen
# twice (refined roots agree to well under a second; a real re-crossing needs
# a station, which takes days).
SAME_EVENT_TOLERANCE_DAYS = 1.0 / 86400.0


def kernel_body(value: str) -> str:
    """The kernel's body name ('Mars') from any accepted spelling."""
    if value in DB_BODY:
        return value
    if value in _STORED_BODY:
        return _STORED_BODY[value]
    try:
        return _VOCAB_BODY[GrahaId(value)]
    except (ValueError, KeyError):
        raise ValueError(f"no sky body for {value!r} under the mean-node convention") from None


def event_object(body: str, relation: str, level_deg: float,
                 convention_id: str) -> PhysicalObjectId:
    return physical_object_id(
        body=DB_BODY[kernel_body(body)],
        relation_kind=DB_EVENT_KIND.get(relation, relation),
        canonical_target=targets.point_target(float(level_deg)),
        convention_id=convention_id,
    )


def occurrence_id(obj: PhysicalObjectId, ordinal: int) -> uuid.UUID:
    return SubstrateContact(obj, int(ordinal), None).contact_id


class _Identified(Protocol):
    @property
    def event_id(self) -> uuid.UUID: ...
    @property
    def jd(self) -> float: ...


def merge_events(*streams: Iterable[_Identified]) -> tuple:
    """Union of event streams by canonical id, in time order.

    One id seen twice at the same instant is one event. One id at two
    different instants is a collision and fails loudly (pin 4).
    """
    seen: dict[uuid.UUID, _Identified] = {}
    for stream in streams:
        for event in stream:
            prior = seen.setdefault(event.event_id, event)
            if abs(prior.jd - event.jd) > SAME_EVENT_TOLERANCE_DAYS:
                raise IdentityCollisionError(
                    f"event id {event.event_id} names two instants: {prior.jd} and {event.jd}")
    return tuple(sorted(seen.values(), key=lambda e: (e.jd, str(e.event_id))))


__all__ = ["SAME_EVENT_TOLERANCE_DAYS", "event_object", "kernel_body",
           "merge_events", "occurrence_id"]
