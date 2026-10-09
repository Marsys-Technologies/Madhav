"""Typed F1 promise-graph primitives.

L1 facts remain authoritative: this graph carries only their identifiers. L2
MSR, CGM and Pratijna material attaches to an admitted mechanism; it cannot
introduce one or copy an L1-computed value.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from services.kala_core.ontology import CLASS_ROSTER


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


class EdgePolarity(StrEnum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"


class AttachmentSource(StrEnum):
    MSR = "MSR"
    CGM = "CGM"
    PRATIJNA = "Pratijna"


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
    polarity: EdgePolarity
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
    source: AttachmentSource
    fact_ids: tuple[str, ...]
    state: FactState = FactState.PRESENT


@dataclass(frozen=True)
class AttachmentInput:
    """A source row reduced to L1 references, never source values."""

    attachment_id: str
    source: AttachmentSource
    fact_ids: tuple[str, ...]
    evaluated_empty: bool = False


@dataclass(frozen=True)
class Mechanism:
    mechanism_id: str
    route: MechanismRoute
    event_class_id: str
    participant_node_ids: tuple[str, ...]
    fact_ids: tuple[str, ...]
    source_status: str


def load_l2_attachments(
    mechanism_id: str,
    inputs: Iterable[AttachmentInput],
    chart_fact_ids: Iterable[str],
) -> tuple[Attachment, ...]:
    """Load L2 references while distinguishing upstream absence from emptiness."""
    available = set(chart_fact_ids)
    attachments = []
    for item in inputs:
        state = (
            FactState.MISSING_FACT
            if not set(item.fact_ids) <= available
            else FactState.EVALUATED_EMPTY
            if item.evaluated_empty
            else FactState.PRESENT
        )
        attachments.append(Attachment(item.attachment_id, mechanism_id, item.source, item.fact_ids, state))
    return tuple(attachments)


def attachment_input_from_mapping(row: Mapping[str, object]) -> AttachmentInput:
    """Accept the narrow attachment contract and reject copied L1 values."""
    allowed = {"attachment_id", "source", "fact_ids", "evaluated_empty"}
    unknown = set(row) - allowed
    if unknown:
        raise ValueError(f"L2 attachment may not restate values: {sorted(unknown)!r}")
    try:
        return AttachmentInput(
            attachment_id=str(row["attachment_id"]),
            source=AttachmentSource(str(row["source"])),
            fact_ids=tuple(str(item) for item in row["fact_ids"]),  # type: ignore[index, union-attr]
            evaluated_empty=bool(row.get("evaluated_empty", False)),
        )
    except (KeyError, TypeError) as error:
        raise ValueError("attachment requires attachment_id, source and fact_ids") from error


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

    def add_edge(self, edge: PromiseEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("edge references unknown node")
        self.edges.append(edge)

    def add_mechanism(self, mechanism: Mechanism) -> None:
        if mechanism.event_class_id not in CLASS_ROSTER:
            raise ValueError("mechanism event class is outside the canonical ontology roster")
        if mechanism.route is MechanismRoute.ADMITTED and not mechanism.fact_ids:
            raise ValueError("admitted mechanisms require L1 facts")
        if any(node not in self.nodes for node in mechanism.participant_node_ids):
            raise ValueError("mechanism references unknown node")
        self.mechanisms[mechanism.mechanism_id] = mechanism

    def add_conclusion(self, conclusion: Conclusion) -> None:
        """Register the candidate rule conclusion without collapsing its formation.

        Conclusions are intentionally separate from mechanisms: bhaṅga and
        apavāda target a rule conclusion, never the underlying chart formation.
        Both admitted and testimony mechanisms may carry a candidate conclusion;
        their routes remain distinct on the mechanism itself.
        """
        if conclusion.mechanism_id not in self.mechanisms:
            raise ValueError("conclusion references unknown mechanism")
        if conclusion.conclusion_id in self.conclusions:
            raise ValueError(f"duplicate conclusion {conclusion.conclusion_id}")
        self.conclusions[conclusion.conclusion_id] = conclusion

    def add_defeat(self, defeat: Defeat) -> None:
        """Attach typed bhaṅga/apavāda evidence to exactly one conclusion."""
        if defeat.conclusion_id not in self.conclusions:
            raise ValueError("defeat references unknown conclusion")
        self.defeats.append(defeat)

    def validate_node_facts(self, chart_fact_ids: Iterable[str]) -> None:
        available = set(chart_fact_ids)
        unresolved = {
            node.node_id: tuple(fact_id for fact_id in node.fact_ids if fact_id not in available)
            for node in self.nodes.values()
        }
        unresolved = {node_id: fact_ids for node_id, fact_ids in unresolved.items() if fact_ids}
        if unresolved:
            raise ValueError(f"node L1 fact ids do not resolve in chart_facts: {unresolved!r}")

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


__all__ = [
    "Attachment", "AttachmentInput", "AttachmentSource", "Conclusion", "Defeat", "EdgePolarity",
    "EffectiveState", "FactState", "Mechanism", "MechanismRoute", "PromiseEdge", "PromiseGraph",
    "PromiseNode", "attachment_input_from_mapping", "load_l2_attachments",
]
