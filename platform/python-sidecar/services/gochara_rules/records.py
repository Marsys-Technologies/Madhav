"""relationship_record (GOCHARA_DESIGN_SPECS_v1_4 §1).

Deterministic record_id = hash of the natural key INCLUDING generation and
contact_id (amendment 1); root_id := contact_id on transit-relation rows,
:= object_id on natal-fact rows (§2.1 amendment 2); affliction is a
predicate, not a label (§1.2 inv 8).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .predicates import FALSE, TRUE, UNKNOWN

TRANSIT_RELATIONS = frozenset({"residence", "aspect", "conjunction"})
NATAL_RELATIONS = frozenset({
    "dispositorship", "association", "ownership", "occupancy", "period_running",
})
OBJECT_ROLES = frozenset({
    "lord", "occupant", "karaka", "dispositor", "maraka_of_house",
    "period_lord", "yoga_constituent", "pada", "signature_house",
})
AFFECTED_PERSONS = frozenset({
    "native", "father", "mother", "spouse", "child", "sibling",
})
# Afflicter set per the citing rule (§1.2 inv 8).
AFFLICTERS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})

NATURAL_KEY_FIELDS = (
    "chart_id", "generation", "event_class", "affected_person", "frame",
    "agent", "relation", "object_id", "object_role", "contact_id",
    "path_id", "rule_version", "prerequisites", "source_text",
)


@dataclass
class RelationshipRecord:
    chart_id: str
    generation: str
    event_class: str
    affected_person: str
    frame: str
    agent: str
    relation: str
    object_id: str
    object_kind: str
    object_role: str
    contact_id: str | None
    path_id: str
    rule_version: str
    prerequisites: list[tuple[str, str]]
    provenance: str
    operator_role: str
    ruling_ref: str | None = None
    source_text: str | None = None
    source_page: str | None = None
    temporal_support: dict = field(
        default_factory=lambda: {"state": "uncomputed", "grain": None, "intervals": []}
    )
    source_fact_ids: list = field(default_factory=list)
    fixture: bool = False
    evidence_for_occurrence: float = 0.0
    evidence_against_occurrence: float = 0.0
    outcome_valence_for_native: str = "unqualified"
    # severity is defined by no spec rule (§1.1: "interpretive, rank-only"): the honest default is a
    # named NULL, never an invented 0.0 (CLAUDE.md §N.7 item 6; 1156 permits NULL)
    severity: float | None = None
    precision: dict | None = None

    def __post_init__(self):
        if self.relation in TRANSIT_RELATIONS and self.contact_id is None:
            raise ValueError("contact_id NOT NULL on transit-relation rows (§1.1)")
        if self.relation in NATAL_RELATIONS and self.contact_id is not None:
            raise ValueError("natal-fact rows carry contact_id NULL (§1.1)")
        if self.relation not in TRANSIT_RELATIONS | NATAL_RELATIONS:
            raise ValueError(f"unknown relation {self.relation!r} (F6a)")
        if self.object_role not in OBJECT_ROLES:
            raise ValueError(f"unknown object_role {self.object_role!r}")
        if self.affected_person not in AFFECTED_PERSONS:
            raise ValueError(f"unknown affected_person {self.affected_person!r}")
        if self.provenance == "uncited_extension" and not self.ruling_ref:
            raise ValueError("uncited_extension ⇒ ruling_ref NOT NULL (§1.2 inv 2)")
        for ref in self.prerequisites:
            if not (isinstance(ref, (tuple, list)) and len(ref) == 2 and all(ref)):
                raise ValueError("bare predicate id rejected — composite "
                                 "(predicate_id, rule_version) required (§1.1)")

    @property
    def natural_key(self) -> dict:
        key = {f: getattr(self, f) for f in NATURAL_KEY_FIELDS}
        key["prerequisites"] = [list(r) for r in self.prerequisites]
        return key

    @property
    def record_id(self) -> str:
        """PK — deterministic hash of the natural key; generation and
        contact_id are IN the key (amendment 1)."""
        canonical = json.dumps(self.natural_key, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False)
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def root_id(self) -> str:
        """root_id := contact_id on transit rows, := object_id on natal rows
        (§2.1 amendment 2, R4-S01)."""
        return self.contact_id if self.contact_id is not None else self.object_id


def afflicted(object_id: str, rows: list[RelationshipRecord] | None,
              afflicter_set: frozenset[str] = AFFLICTERS) -> str:
    """§1.2 inv 8 — affliction is a predicate: afflicted(x) iff ∃ a row with
    agent ∈ the named afflicter set, relation ∈ {conjunction, aspect},
    object = x. An UNEVALUATED claim (rows=None) is `unknown`, never assumed
    (unqualified)."""
    if rows is None:
        return UNKNOWN
    for r in rows:
        if (r.object_id == object_id and r.agent in afflicter_set
                and r.relation in {"conjunction", "aspect"}):
            return TRUE
    return FALSE
