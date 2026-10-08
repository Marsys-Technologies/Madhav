"""Typed F1 promise-graph primitives.

The graph deliberately stores L1 fact references, never their computed values.
L2 material is an attachment to an already-admitted mechanism, not a source of
new admitted mechanisms.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class MechanismRoute(StrEnum):
    ADMITTED = "admitted"
    TESTIMONY = "testimony"


class FactState(StrEnum):
    PRESENT = "present"
    MISSING_FACT = "missing_fact"
    EVALUATED_EMPTY = "evaluated_empty"


class EffectiveState(StrEnum):
    IN_FORCE = "in_force"
    DEFEATED = "defeated"
    PARTLY_DEFEATED = "partly_defeated"
    CONTESTED = "contested"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class FactRef:
    """An L1 reference; a value field is intentionally absent."""

    fact_id: str


@dataclass(frozen=True)
class PromiseNode:
    node_id: str
    kind: str
    fact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.fact_ids:
            raise ValueError("every F1 node must cite L1 fact ids")


@dataclass(frozen=True)
class PromiseEdge:
    source_id: str
    target_id: str
    relation: str
    frame: str
    rule_id: str
    rule_version: str
    provenance: str


@dataclass(frozen=True)
class Conclusion:
    conclusion_id: str
    mechanism_id: str
    candidate_state: FactState
    fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class Defeat:
    conclusion_id: str
    fact_ids: tuple[str, ...]
    rule_id: str
    kind: str = "defeats"

    def __post_init__(self) -> None:
        if self.kind not in {"defeats", "excepts"}:
            raise ValueError("defeat kind must be defeats or excepts")


@dataclass(frozen=True)
class Attachment:
    attachment_id: str
    mechanism_id: str
    source: str
    state: FactState = FactState.PRESENT


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: str
    route: MechanismRoute
    event_class_id: str
    participant_node_ids: tuple[str, ...]
    fact_ids: tuple[str, ...]
    source_status: str


@dataclass
class PromiseGraph:
    nodes: dict[str, PromiseNode] = field(default_factory=dict)
    edges: list[PromiseEdge] = field(default_factory=list)
    mechanisms: dict[str, Mechanism] = field(default_factory=dict)
    conclusions: dict[str, Conclusion] = field(default_factory=dict)
    defeats: list[Defeat] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)

    def add_node(self, node: PromiseNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate node {node.node_id}")
        self.nodes[node.node_id] = node

    def add_mechanism(self, mechanism: Mechanism) -> None:
        if mechanism.route is MechanismRoute.ADMITTED and not mechanism.fact_ids:
            raise ValueError("admitted mechanisms require L1 facts")
        if any(node not in self.nodes for node in mechanism.participant_node_ids):
            raise ValueError("mechanism references unknown node")
        self.mechanisms[mechanism.mechanism_id] = mechanism

    def attach(self, attachment: Attachment) -> None:
        if attachment.mechanism_id not in self.mechanisms:
            raise ValueError("attachment references unknown mechanism")
        self.attachments.append(attachment)

    def effective_state(self, conclusion_id: str, available_fact_ids: Iterable[str]) -> EffectiveState:
        conclusion = self.conclusions[conclusion_id]
        facts = set(available_fact_ids)
        if not set(conclusion.fact_ids) <= facts:
            return EffectiveState.UNRESOLVED
        defeats = [d for d in self.defeats if d.conclusion_id == conclusion_id]
        if not defeats:
            return EffectiveState.IN_FORCE
        active = [d for d in defeats if set(d.fact_ids) <= facts]
        if not active:
            return EffectiveState.IN_FORCE
        return EffectiveState.DEFEATED if len(active) == len(defeats) else EffectiveState.PARTLY_DEFEATED

    def fact_state(self, mechanism_id: str, available_fact_ids: Iterable[str]) -> FactState:
        mechanism = self.mechanisms[mechanism_id]
        return FactState.PRESENT if set(mechanism.fact_ids) <= set(available_fact_ids) else FactState.MISSING_FACT

    def attachments_for(self, mechanism_id: str) -> tuple[Attachment, ...]:
        return tuple(item for item in self.attachments if item.mechanism_id == mechanism_id)


__all__ = ["Attachment", "Conclusion", "Defeat", "EffectiveState", "FactState", "Mechanism", "MechanismRoute", "PromiseEdge", "PromiseGraph", "PromiseNode"]
