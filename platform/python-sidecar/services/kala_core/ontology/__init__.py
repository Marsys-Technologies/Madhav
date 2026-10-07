"""The one Kāla event-ontology loader.

The vocabulary authority is ``gochara_rules.registry.CLASS_UNIVERSE``.  This
module reads metadata from the L0 ontology table but refuses to turn a partial
or widened database result into a different event-class universe.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from services.gochara_rules.registry import CLASS_UNIVERSE
from services.kala_core.vocab import NullReason


CLASS_ROSTER: tuple[str, ...] = tuple(row["class"] for row in CLASS_UNIVERSE)
assert len(CLASS_ROSTER) == 27


@dataclass(frozen=True)
class EventOntology:
    """A database-backed ontology row, keyed by the canonical class id."""

    event_class_id: str
    name_en: str
    domain: str
    signature_model: Any
    magnitude_floor: str
    temporal_shape: str | None
    milestone_template: Any
    evidence_requirements: Any
    valence: None
    valence_reason: str


def _mapping(cursor: Any, row: Any) -> Mapping[str, Any]:
    if isinstance(row, Mapping):
        return row
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row, strict=True))


def load_event_ontology(conn: Any) -> tuple[EventOntology, ...]:
    """Return precisely the declared 27-class roster in registry order.

    A missing row is not interpreted as absence, and an unknown row is not
    silently accepted.  Callers therefore receive one stable universe rather
    than a database-shaped subset.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT event_class_id, name_en, domain, signature_model,
                      magnitude_floor, temporal_shape, milestone_template,
                      evidence_requirements
                 FROM brahma_event_ontology
                WHERE event_class_id = ANY(%s)""",
            (list(CLASS_ROSTER),),
        )
        rows = [_mapping(cursor, row) for row in cursor.fetchall()]

    by_id = {str(row["event_class_id"]): row for row in rows}
    found = set(by_id)
    expected = set(CLASS_ROSTER)
    if found != expected:
        missing = sorted(expected - found)
        unexpected = sorted(found - expected)
        raise ValueError(
            "brahma_event_ontology must match the 27-class registry; "
            f"missing={missing!r}, unexpected={unexpected!r}"
        )

    return tuple(
        EventOntology(
            event_class_id=event_class_id,
            name_en=str(by_id[event_class_id]["name_en"]),
            domain=str(by_id[event_class_id]["domain"]),
            signature_model=by_id[event_class_id]["signature_model"],
            magnitude_floor=str(by_id[event_class_id]["magnitude_floor"]),
            temporal_shape=by_id[event_class_id]["temporal_shape"],
            milestone_template=by_id[event_class_id]["milestone_template"],
            evidence_requirements=by_id[event_class_id]["evidence_requirements"],
            # Class polarity is not an ontology fact supplied by L0.  Preserve
            # that unknown rather than inferring favourable/unfavourable valence.
            valence=None,
            valence_reason=NullReason.CLASS_POLARITY_NOT_DECLARED_UPSTREAM.value,
        )
        for event_class_id in CLASS_ROSTER
    )


__all__ = ["CLASS_ROSTER", "EventOntology", "load_event_ontology"]
