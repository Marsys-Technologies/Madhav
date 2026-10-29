"""Rule Book engine (E3) — rebuild the closed AST from stored IR JSON, and the operand table.

The L0 store keeps each card's compiled IR (``ir_json``) and the card itself. The
IR flattens a few operand fields the evaluator must tell apart (``bhava`` versus
``target_bhavas``), so the evaluator also reads the card's own typed operands. This
module turns both into plain values; it resolves nothing.

``operand_table`` keeps only structural fields (ids, roles, houses, graha, links).
It never carries a quote or a quote term, so a bundle built from it is word-free.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from ..ast import And, Comparison, Node, Not, ObstructorSet, Or, Pred

OPERAND_FIELDS = ("id", "role", "relation", "doctrinal_graha", "bhava", "target_bhavas", "target_role", "bhava_group")


class IRError(ValueError):
    pass


def node_from_json(obj: Mapping[str, Any]) -> Node:
    kind = obj.get("node")
    if kind == "pred":
        cmp_ = obj.get("comparison")
        obs = obj.get("obstructors")
        return Pred(
            operand_id=obj["operand_id"],
            role=obj["role"],
            relation=obj["relation"],
            plane=obj["plane"],
            frame=obj["frame"],
            source=dict(obj.get("source") or {}),
            graha=obj.get("graha"),
            graha_class=obj.get("graha_class"),
            bhavas=tuple(obj.get("bhavas") or ()),
            bhava_group=obj.get("bhava_group"),
            target_role=obj.get("target_role"),
            node_model=obj.get("node_model"),
            comparison=Comparison(cmp_["kind"], cmp_["op"], cmp_["value"], cmp_["count_convention"]) if cmp_ else None,
            obstructors=ObstructorSet(
                obs["primary"], tuple(obs["certain"]), tuple(obs["undeclared"]), tuple(obs["exempt"])
            )
            if obs
            else None,
        )
    if kind == "and":
        return And(tuple(node_from_json(a) for a in obj["args"]))
    if kind == "or":
        if obj.get("verse_disjunction") is not True:
            raise IRError("Or without a verse-stated disjunction")
        return Or(tuple(node_from_json(a) for a in obj["args"]), verse_disjunction=True)
    if kind == "not":
        return Not(node_from_json(obj["arg"]))
    raise IRError(f"unknown AST node {kind!r}")


def operand_table(card: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Structural fields of every typed operand of a card (gate and exceptions), by id."""
    out: Dict[str, Dict[str, Any]] = {}
    ops: List[Mapping[str, Any]] = list(card.get("field5_typed_operands") or [])
    for exc in card.get("field6_exceptions") or []:
        ops.extend(exc.get("operands") or [])
    for op in ops:
        rec = {k: op[k] for k in OPERAND_FIELDS if k in op and op[k] is not None}
        if "target_bhavas" in rec:
            rec["target_bhavas"] = [int(x) for x in rec["target_bhavas"]]
        out[op["id"]] = rec
    return out


def frame_role_of(card: Mapping[str, Any]) -> Optional[str]:
    return (card.get("field3_reference_frame") or {}).get("frame_role")
