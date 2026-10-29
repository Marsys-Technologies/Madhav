"""Rule Book engine (E3) — static planning: can the engine evaluate this card, and what does it read?

``plan_card`` takes a compiled IR (the attested one, or a fresh compile) and the card's
operand table. It either returns a ``CardPlan`` (every predicate mapped to a resolver
kind with its structural parameters) or raises ``Unsupported`` naming the first thing
it cannot do. The manifest builder and the evaluator share this code, so a card the
manifest calls evaluable is exactly a card the evaluator can run (§N.8: a status that
is computed by the thing it claims).

Nothing here reads a chart, a sky row or a daśā row.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .. import constants as RC
from ..ast import Node, Pred, iter_preds
from ..lints import p4_violations_ast
from . import constants as K
from .irtree import IRError, node_from_json


class Unsupported(Exception):
    """The engine cannot evaluate this card (fail closed). ``code`` is a short stable reason."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


# resolver kinds
TRANSIT_HOUSE = "transit_house"
NATAL_HOUSE = "natal_house"
NATAL_ASPECT = "natal_aspect"
NATAL_CONJOIN = "natal_conjoin"
NATAL_FLAG = "natal_flag"
LORD_OF = "lord_of"
BHAVA_LORD_HOUSE = "bhava_lord_house"
DASHA_IDENTITY = "dasha_identity"
DASHA_HOUSE = "dasha_house"
DASHA_FLAG = "dasha_flag"

FLAGS = ("retrograde", "exalted", "debilitated", "own_sign")
LEVEL_OF_ROLE = {"dasha_lord": K.DASHA_LEVEL_MD, "antardasha_lord": K.DASHA_LEVEL_AD}
IDENTITY_RELATION = {"dasha_lord": "is_dasha_lord", "antardasha_lord": "is_antardasha_lord"}


@dataclass(frozen=True)
class FrameSpec:
    kind: str  # lagna | moon | md_lord | graha
    graha: Optional[str] = None  # for kind == 'graha'

    def key(self) -> str:
        return self.kind if self.graha is None else f"{self.kind}:{self.graha}"


@dataclass(frozen=True)
class PredPlan:
    operand_id: str
    kind: str
    params: Tuple[Tuple[str, Any], ...]  # sorted (name, value); values are JSON-able
    positional: bool  # counts houses in the card's frame

    def p(self, name: str, default: Any = None) -> Any:
        for k, v in self.params:
            if k == name:
                return v
        return default

    def signature(self, frame: Optional[FrameSpec]) -> str:
        """Cache key: independent of operand ids, dependent on the frame only if positional."""
        return json.dumps(
            [self.kind, list(self.params), frame.key() if (self.positional and frame) else None],
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass
class CardPlan:
    card_id: str
    category: str
    polarity: str
    provenance: str
    gate: Node
    preds: Dict[str, PredPlan]
    frame: FrameSpec
    node_named: List[str] = field(default_factory=list)  # nodes whose position/state a predicate reads
    lord_generic: bool = False  # reads 'the' daśā/antardaśā lord: node-lord days are NOT_ASSESSED
    transit_bodies: List[str] = field(default_factory=list)

    @property
    def excluded_node(self) -> bool:
        return bool(self.node_named)


def _group_members(group: Optional[str]) -> Tuple[int, ...]:
    if group is None:
        return ()
    if group not in RC.BHAVA_GROUPS:
        raise Unsupported("BHAVA_GROUP_UNKNOWN", group)
    return tuple(RC.BHAVA_GROUPS[group]["members"])


def _targets(op: Mapping[str, Any]) -> Tuple[int, ...]:
    houses = set()
    if op.get("bhava") is not None:
        houses.add(int(op["bhava"]))
    houses.update(int(x) for x in op.get("target_bhavas") or [])
    houses.update(_group_members(op.get("bhava_group")))
    return tuple(sorted(houses))


def plan_card(ir: Mapping[str, Any], operands: Mapping[str, Mapping[str, Any]]) -> CardPlan:
    if ir.get("status") != "active":
        raise Unsupported("NOT_ACTIVE", str(ir.get("status")))
    if ir.get("exceptions"):
        raise Unsupported("EXCEPTIONS_NOT_EVALUATED", "v1 evaluates no exception (cancels/reduces/reverses/delays); none is on an active card")
    if (ir.get("counting") or {}).get("testimony"):
        pass  # testimony is evaluated but flagged; plan carries provenance for the tally
    try:
        gate = node_from_json(ir["gate"])
    except IRError as exc:
        raise Unsupported("IR_INVALID", str(exc)) from exc
    viol = p4_violations_ast([gate])
    if viol:
        raise Unsupported("P4_DOUBLE_TRANSIT", viol[0])

    fr_decl = (ir.get("frame") or {}).get("declared")
    fr_role = (ir.get("frame") or {}).get("frame_role")
    node_named: List[str] = []
    state = {"frame_used": False, "lord_generic": False}
    plans: Dict[str, PredPlan] = {}
    bodies: List[str] = []

    def note_node(g: Optional[str], why: str) -> None:
        if g in K.NODES:
            tag = f"{g}:{why}"
            if tag not in node_named:
                node_named.append(tag)

    for pred in iter_preds(gate):
        if pred.operand_id in plans:
            continue
        op = operands.get(pred.operand_id)
        if op is None:
            raise Unsupported("OPERAND_MISSING", pred.operand_id)
        plans[pred.operand_id] = _plan_pred(pred, op, operands, note_node, state, bodies)

    frame = _plan_frame(fr_decl, fr_role, operands, plans, note_node, state)
    if frame.kind != "md_lord" and any(p.p("via_md_target") for p in plans.values()):
        raise Unsupported("TARGET_ROLE_FRAME_MISMATCH", "a target_role onto the daśā lord needs the dasha_lord_natal_position frame")
    return CardPlan(
        card_id=ir["card_id"],
        category=ir["category"],
        polarity=ir["polarity"],
        provenance=ir["provenance"],
        gate=gate,
        preds=plans,
        frame=frame,
        node_named=sorted(node_named),
        lord_generic=bool(state["lord_generic"] or (state["frame_used"] and frame.kind == "md_lord")),
        transit_bodies=sorted(set(bodies)),
    )


def _plan_frame(
    fr_decl: Optional[str],
    fr_role: Optional[str],
    operands: Mapping[str, Mapping[str, Any]],
    plans: Mapping[str, PredPlan],
    note_node,
    state: Dict[str, bool],
) -> FrameSpec:
    spec: Optional[FrameSpec] = None
    if fr_decl == "janma_lagna":
        spec = FrameSpec("lagna")
    elif fr_decl == "chandra_lagna":
        spec = FrameSpec("moon")
    elif fr_decl == "dasha_lord_natal_position":
        spec = FrameSpec("md_lord")
    elif fr_decl == "natal_position_of_role":
        fo = operands.get(fr_role or "")
        g = fo.get("doctrinal_graha") if fo else None
        if fo and fo.get("role") == "dasha_lord" and fo.get("relation") == "is_dasha_lord" and not g:
            spec = FrameSpec("md_lord")  # 'natal position of the daśā lord' encoded through a role operand
        elif not fo or fo.get("role") != "natal_graha" or not g:
            if state["frame_used"]:
                raise Unsupported("FRAME_ROLE_UNBOUND", f"frame_role {fr_role!r} must be a natal_graha bound to one graha")
            spec = FrameSpec("lagna")  # never consulted: no predicate counts houses
        else:
            if state["frame_used"]:
                note_node(g, "frame_reference")
            spec = FrameSpec("graha", g)
    else:
        if state["frame_used"]:
            raise Unsupported("FRAME_UNSUPPORTED", str(fr_decl))
        spec = FrameSpec("lagna")  # never consulted
    return spec


def _plan_pred(
    pred: Pred,
    op: Mapping[str, Any],
    operands: Mapping[str, Mapping[str, Any]],
    note_node,
    state: Dict[str, bool],
    bodies: List[str],
) -> PredPlan:
    role, rel, g = pred.role, pred.relation, pred.graha
    oid = pred.operand_id

    def mk(kind: str, positional: bool, **params: Any) -> PredPlan:
        if positional:
            state["frame_used"] = True
        return PredPlan(oid, kind, tuple(sorted(params.items())), positional)

    # IR/card agreement: the IR must say what the operand says (a stale or mismatched bundle fails closed)
    if (op.get("role"), op.get("relation")) != (role, rel):
        raise Unsupported("IR_OPERAND_MISMATCH", f"{oid}: IR {role}/{rel} vs card {op.get('role')}/{op.get('relation')}")
    if op.get("doctrinal_graha") != g:
        raise Unsupported("IR_OPERAND_MISMATCH", f"{oid}: graha differs between IR and card")
    if rel != "vedha_by" and tuple(
        sorted(set(int(x) for x in ([op["bhava"]] if op.get("bhava") else []) + list(op.get("target_bhavas") or [])))
    ) != tuple(pred.bhavas):
        raise Unsupported("IR_OPERAND_MISMATCH", f"{oid}: house list differs between IR and card")

    # ── transit ────────────────────────────────────────────────────────────
    if role == "transiting_graha":
        if rel in ("transits", "occupies", "in_bhava_group"):
            if not g:
                raise Unsupported("UNBOUND_OPERAND", oid)
            note_node(g, "transit_position")
            tg = _targets(op)
            if not tg:
                raise Unsupported("TARGET_UNBOUND", oid)
            if g not in K.NODES:
                bodies.append(g)
            return mk(TRANSIT_HOUSE, True, graha=g, targets=list(tg))
        if rel == "vedha_by":
            obs = pred.obstructors
            if obs is None:
                raise Unsupported("VEDHA_SET_UNDECLARED", oid)
            for n in obs.undeclared + obs.certain:
                note_node(n, "vedha_obstructor")
            if any(n in K.NODES for n in obs.undeclared + obs.certain):
                if g and g not in K.NODES:
                    bodies.append(g)
                return mk(TRANSIT_HOUSE, True, graha=g, targets=[0])  # placeholder: never evaluated (node-excluded)
            raise Unsupported("VEDHA_NOT_EVALUATED", "vedha place table (bg_transit_rules) is not read in v1")
        raise Unsupported("RELATION_UNSUPPORTED", f"{role}/{rel}")

    # ── natal ──────────────────────────────────────────────────────────────
    if role == "natal_graha":
        if not g:
            raise Unsupported("UNBOUND_OPERAND", oid)
        if rel in ("occupies", "in_bhava_group"):
            note_node(g, "natal_position")
            tg = _targets(op)
            if not tg:
                raise Unsupported("TARGET_UNBOUND", oid)
            return mk(NATAL_HOUSE, True, graha=g, targets=list(tg))
        if rel == "aspects":
            note_node(g, "natal_aspect")
            tr = op.get("target_role")
            tg = _targets(op)
            if tr and tg:
                raise Unsupported("ASPECT_TARGET_AMBIGUOUS", oid)
            if tr:
                partner = _partner(oid, tr, operands)
                note_node(partner, "natal_aspect_target")
                return mk(NATAL_ASPECT, False, graha=g, partner=partner)
            if not tg:
                raise Unsupported("TARGET_UNBOUND", oid)
            return mk(NATAL_ASPECT, True, graha=g, targets=list(tg))
        if rel == "conjoins":
            note_node(g, "natal_conjunction")
            tr = op.get("target_role")
            if not tr:
                raise Unsupported("TARGET_UNBOUND", oid)
            partner = _partner(oid, tr, operands)
            note_node(partner, "natal_conjunction_partner")
            return mk(NATAL_CONJOIN, False, graha=g, partner=partner)
        if rel in FLAGS:
            note_node(g, "natal_flag_" + rel)
            return mk(NATAL_FLAG, False, graha=g, flag=rel)
        raise Unsupported("RELATION_UNSUPPORTED", f"{role}/{rel}")

    # ── bhāva lord ─────────────────────────────────────────────────────────
    if role == "bhava_lord":
        b = op.get("bhava")
        if b is None:
            raise Unsupported("BHAVA_LORD_WITHOUT_BHAVA", oid)
        if rel == "lord_of":
            if not g:
                raise Unsupported("UNBOUND_OPERAND", oid)
            note_node(g, "bhava_lord")
            return mk(LORD_OF, True, graha=g, bhava=int(b))
        if rel in ("occupies", "in_bhava_group"):
            if rel == "occupies" and not op.get("target_bhavas"):
                raise Unsupported("TARGET_UNBOUND", oid)
            if rel == "in_bhava_group" and not op.get("bhava_group"):
                raise Unsupported("TARGET_UNBOUND", oid)
            tg = tuple(sorted(set(int(x) for x in op.get("target_bhavas") or []) | set(_group_members(op.get("bhava_group")))))
            if g:
                note_node(g, "bhava_lord")
            return mk(BHAVA_LORD_HOUSE, True, graha=g, bhava=int(b), targets=list(tg))
        raise Unsupported("RELATION_UNSUPPORTED", f"{role}/{rel}")

    # ── daśā lords ─────────────────────────────────────────────────────────
    if role in LEVEL_OF_ROLE:
        level = LEVEL_OF_ROLE[role]
        if rel == IDENTITY_RELATION[role]:
            return mk(DASHA_IDENTITY, False, level=level, graha=g)  # identity only: reads no node position
        if rel in ("occupies", "in_bhava_group"):
            tr = op.get("target_role")
            if tr:
                t = operands.get(tr)
                if not (level == K.DASHA_LEVEL_AD and t and t.get("role") == "dasha_lord" and t.get("relation") == "is_dasha_lord"):
                    raise Unsupported("TARGET_ROLE_UNSUPPORTED", f"{oid} -> {tr}")
            tg = _targets(op)
            if not tg:
                raise Unsupported("TARGET_UNBOUND", oid)
            if g:
                note_node(g, "dasha_lord_position")
            else:
                state["lord_generic"] = True
            return mk(DASHA_HOUSE, True, level=level, graha=g, targets=list(tg), via_md_target=bool(tr))
        if rel in ("retrograde", "exalted", "debilitated", "own_sign"):
            if g:
                note_node(g, "dasha_lord_flag_" + rel)
            else:
                state["lord_generic"] = True
            return mk(DASHA_FLAG, False, level=level, graha=g, flag=rel)
        raise Unsupported("RELATION_UNSUPPORTED", f"{role}/{rel}")

    raise Unsupported("ROLE_UNSUPPORTED", role)


def _partner(oid: str, target_role: str, operands: Mapping[str, Mapping[str, Any]]) -> str:
    t = operands.get(target_role)
    if not t:
        raise Unsupported("TARGET_ROLE_UNDECLARED", f"{oid} -> {target_role}")
    if t.get("role") != "natal_graha" or not t.get("doctrinal_graha"):
        raise Unsupported("TARGET_ROLE_UNBOUND", f"{oid} -> {target_role}")
    return str(t["doctrinal_graha"])
