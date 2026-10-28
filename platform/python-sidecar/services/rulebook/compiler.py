"""Rule Book engine (packet E1) — card JSON (Rule Card v1.1) → IR + ir_sha256.

The compiler never guesses. Anything it cannot type from the card's own
fields is a typed quarantine finding (quarantine.Reason); the card is then
QUARANTINED_NOT_EVALUABLE — stored, never counted. No value is resolved and
no database is touched: every predicate carries the operand-source
descriptor of E0's matrix for E3/E4 to resolve later.

Lexical checks read only words the card itself carries (quote_terms and the
cited quote), using the closed patterns in constants.py. Quote text never
enters the IR; the IR carries passage_ids and the quote sha256.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import constants as C
from . import schema as rb_schema
from .ast import And, Comparison, ExceptionNode, Node, Not, ObstructorSet, Or, Pred, iter_preds
from .lints import p4_violations_ast
from .quarantine import Finding, Reason

_RE = {
    name: re.compile(getattr(C, name), re.IGNORECASE)
    for name in (
        "MEAN_TERMS_RE",
        "TRUE_NODE_TERMS_RE",
        "VEDHA_TERMS_RE",
        "VEDHA_EXEMPTION_RE",
        "VERSE_DISJUNCTION_RE",
        "OBSTRUCTOR_CLASS_RE",
        "REKHA_TERMS_RE",
        "DOT_TERMS_RE",
        "SELF_DECLARED_BENEFIC_RE",
    )
}

_ROLES = frozenset(C.ROLE_PLANE)
_RELATIONS = frozenset(
    {
        "occupies",
        "transits",
        "aspects",
        "conjoins",
        "lord_of",
        "is_dasha_lord",
        "is_antardasha_lord",
        "exalted",
        "debilitated",
        "own_sign",
        "combust",
        "retrograde",
        "vedha_by",
        "bindus",
        "in_bhava_group",
    }
)
_CLASS_GROUPS = frozenset(C.CLASS_GROUPS)
_PASSAGE_TEXT_RE = re.compile(r"^([a-z0-9_]+?)(?:_v\d+)?_pg\d{4}_c\d{2}:")


# ── canonical hashing ──────────────────────────────────────────────────────
def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def text_id_of_passage(passage_id: str) -> Optional[str]:
    m = _PASSAGE_TEXT_RE.match(passage_id or "")
    return m.group(1) if m else None


# ── result ─────────────────────────────────────────────────────────────────
@dataclass
class CompileResult:
    card_id: str
    status: str  # active | quarantined_not_evaluable
    findings: List[Finding]
    ir: Optional[Dict[str, Any]] = None
    ir_sha256: Optional[str] = None
    logic_sha256: Optional[str] = None
    gate: Optional[Node] = None
    exceptions: Tuple[ExceptionNode, ...] = ()
    convention_pending: List[str] = field(default_factory=list)

    @property
    def quarantined(self) -> bool:
        return self.status != "active"

    @property
    def reasons(self) -> List[str]:
        return sorted({f.reason.value for f in self.findings})

    def to_json(self) -> dict:
        return {
            "card_id": self.card_id,
            "status": self.status,
            "findings": [f.to_json() for f in self.findings],
            "ir_sha256": self.ir_sha256,
            "logic_sha256": self.logic_sha256,
            "convention_pending": list(self.convention_pending),
        }


class _Unbuildable(Exception):
    """The AST cannot be constructed (structure); findings already recorded."""


# ── compiler ───────────────────────────────────────────────────────────────
class _CardCompiler:
    def __init__(self, card: Mapping[str, Any]):
        self.card = card
        self.findings: List[Finding] = []
        self.pending: set = set()
        self.card_id = str(card.get("card_id") or "<missing card_id>")
        self.unbuildable = False

    # findings ----------------------------------------------------------------
    def q(self, reason: Reason, operand_id: Optional[str], detail: str) -> None:
        self.findings.append(Finding(reason, operand_id, detail))

    def fatal(self, reason: Reason, operand_id: Optional[str], detail: str) -> None:
        self.q(reason, operand_id, detail)
        self.unbuildable = True

    # entry -------------------------------------------------------------------
    def run(self) -> CompileResult:
        if not self._structure():
            return self._result(None, None, ())
        try:
            gate = self._build(self.card["field4_necessary_gate"]["expr"], self.quote, "gate")
        except _Unbuildable:
            gate = None
        excs = self._exceptions()
        # the *_of_role frame's reference operand is typed like any predicate
        fr = self.f3.get("frame_role")
        self.frame_role_pred = self._pred(fr) if self.frame in C.FRAMES_OF_ROLE and fr in self.ops else None
        if gate is not None:
            self._plane_roles(gate)
            self._tautologies(gate)
            for viol in p4_violations_ast([gate] + [e.condition for e in excs]):
                self.q(Reason.P4_DOUBLE_TRANSIT, None, viol)
        return self._result(gate, excs if gate is not None else (), self.referenced)

    # structure ---------------------------------------------------------------
    def _structure(self) -> bool:
        card = self.card
        required = (
            "card_id",
            "schema_version",
            "field1_citation",
            "field2_target_scope",
            "field4_necessary_gate",
            "field5_typed_operands",
            "field6_exceptions",
            "field7_discrete_arithmetic",
            "polarity",
            "provenance",
        )
        missing = [k for k in required if k not in card]
        if missing:
            self.q(Reason.SCHEMA_INVALID, None, f"missing fields: {', '.join(missing)}")
            return False
        if card["schema_version"] not in C.SUPPORTED_SCHEMA_VERSIONS:
            self.q(Reason.SCHEMA_INVALID, None, f"schema_version {card['schema_version']!r} unsupported")
            return False
        f3 = card.get("field3_reference_frame")
        if not isinstance(f3, Mapping) or not f3.get("frame"):
            self.q(Reason.FRAME_MISSING, None, "field3_reference_frame.frame absent; no default is applied")
            return False
        errs = rb_schema.validate_card(card)
        if errs:
            self.q(
                Reason.SCHEMA_INVALID,
                None,
                "; ".join(errs[:6]) + (f" (+{len(errs) - 6} more)" if len(errs) > 6 else ""),
            )
            return False
        feats = rb_schema.v12_features(card)
        if feats:
            # validated, but not evaluated: the evaluator for v1.2 fields does not exist yet
            self.q(Reason.V12_FIELD_NOT_EVALUATED, None, "v1.2 field(s) validated, not evaluated: " + ", ".join(feats))
            return False
        scope = card["field2_target_scope"] or {}
        self.category = scope.get("category")
        self.class_groups = rb_schema.class_groups(card) or []
        if self.category not in C.CATEGORIES or not self.class_groups or not set(self.class_groups) <= _CLASS_GROUPS:
            self.q(Reason.SCHEMA_INVALID, None, "field2 category/class_group not in the v1.1 enums")
            return False
        if card["polarity"] not in C.POLARITIES or card["provenance"] not in C.PROVENANCES:
            self.q(Reason.SCHEMA_INVALID, None, "polarity/provenance not in the v1.1 enums")
            return False
        cite = card["field1_citation"] or {}
        self.cite = cite
        self.quote = cite.get("quote") or ""
        pids = list(cite.get("passage_ids") or [])
        self.text_id = cite.get("text_id") or (text_id_of_passage(pids[0]) if pids else None)
        if card["provenance"] == "verse_cited" and (not pids or not self.quote):
            self.q(Reason.SCHEMA_INVALID, None, "verse_cited card needs passage_ids and quote")
            return False
        # frame: never defaulted
        f3 = card.get("field3_reference_frame")
        self.frame = (f3 or {}).get("frame") if isinstance(f3, Mapping) else None
        self.f3 = f3 if isinstance(f3, Mapping) else {}
        if not self.frame:
            self.q(Reason.FRAME_MISSING, None, "field3_reference_frame.frame absent; no default is applied")
            return False
        if self.frame not in C.FRAMES_ALL:
            self.q(Reason.SCHEMA_INVALID, None, f"frame {self.frame!r} not in the v1.1 enum")
            return False
        # operands
        self.ops: Dict[str, Mapping[str, Any]] = {}
        all_ops = list(card["field5_typed_operands"] or [])
        for exc in card["field6_exceptions"] or []:
            all_ops.extend(exc.get("operands") or [])
        for op in all_ops:
            oid = op.get("id")
            if not oid or op.get("role") not in _ROLES or op.get("relation") not in _RELATIONS:
                self.q(Reason.SCHEMA_INVALID, oid, "operand id/role/relation not in the v1.1 enums")
                return False
            if oid in self.ops and dict(self.ops[oid]) != dict(op):
                self.q(Reason.SCHEMA_INVALID, oid, "operand id declared twice with different content")
                return False
            g = op.get("doctrinal_graha")
            if g is not None and g not in C.GRAHAS:
                self.q(Reason.SCHEMA_INVALID, oid, f"doctrinal_graha {g!r} not in the enum")
                return False
            self.ops[oid] = op
        for item in card["field7_discrete_arithmetic"] or []:
            if not isinstance(item, Mapping) or item.get("kind") not in (
                "rasi_binary",
                "kakshya_cell",
                "drishti_pada",
                "bindus_of_8",
                "combustion_orb_int",
            ):
                self.q(Reason.SCHEMA_INVALID, None, "field7 item kind not in the v1.1 enum")
                return False
        self.referenced: set = set()
        self.linked_by: Dict[str, List[str]] = {}
        for oid, op in self.ops.items():
            tr = op.get("target_role")
            if tr:
                self.linked_by.setdefault(tr, []).append(oid)
        self._frame_checks()
        return True

    def _frame_checks(self) -> None:
        frame = self.frame
        if frame in C.FRAMES_DEFERRED:
            self.q(Reason.FRAME_UNSUPPORTED_V1, None, f"frame {frame} is deferred in v1 (plan §2.3)")
        if frame in C.FRAME_PLANE_CONTRADICTIONS[self.category]:
            extra = " (propose a sign_intrinsic frame, F-S3)" if frame == "sign_of_transit_only" else ""
            self.q(Reason.FRAME_PLANE_CONTRADICTION, None, f"{self.category} card on {frame}{extra}")
        if frame in C.FRAMES_OF_ROLE:
            fr = self.f3.get("frame_role")
            if not fr or fr not in self.ops:
                self.q(Reason.FRAME_ROLE_UNBOUND, None, f"{frame} needs frame_role naming a declared operand")
            else:
                self.referenced.add(fr)

    # gate construction ---------------------------------------------------------
    def _build(self, expr: Any, quote: str, where: str) -> Node:
        if not isinstance(expr, Mapping):
            self.fatal(Reason.SCHEMA_INVALID, None, f"{where}: expression is not an object")
            raise _Unbuildable
        if "operand" in expr:
            oid = expr["operand"]
            if oid not in self.ops:
                self.fatal(Reason.DANGLING_OPERAND_REF, oid, f"{where} references undeclared operand")
                raise _Unbuildable
            self.referenced.add(oid)
            return self._pred(oid)
        op, args = expr.get("op"), expr.get("args")
        if op not in ("AND", "OR", "NOT") or not isinstance(args, list) or not args:
            self.fatal(Reason.SCHEMA_INVALID, None, f"{where}: op/args malformed")
            raise _Unbuildable
        if op == "NOT":
            if len(args) != 1:
                self.fatal(Reason.SCHEMA_INVALID, None, f"{where}: NOT takes exactly one argument")
                raise _Unbuildable
            return Not(self._build(args[0], quote, where))
        built = tuple(self._build(a, quote, where) for a in args)
        if op == "AND":
            return And(built)
        if not _RE["VERSE_DISJUNCTION_RE"].search(quote or ""):
            self.fatal(Reason.OR_NOT_VERSE_STATED, None, f"{where}: OR without a disjunction in the cited quote")
            raise _Unbuildable
        return Or(built, verse_disjunction=True)

    def _terms(self, op: Mapping[str, Any]) -> str:
        return " | ".join(str(t) for t in (op.get("quote_terms") or []))

    def _pred(self, oid: str) -> Pred:
        op = self.ops[oid]
        role, rel = op["role"], op["relation"]
        graha = op.get("doctrinal_graha")
        gclass = op.get("graha_class")
        plane = C.ROLE_PLANE[role]
        terms = self._terms(op)

        # source (E0 matrix)
        source = C.OPERAND_SOURCES.get((role, rel))
        if source is None:
            if rel == "bindus" or role in ("ashtakavarga_bav", "ashtakavarga_sav"):
                self.q(Reason.ROLE_RELATION_MISMATCH, oid, f"{role} + {rel}: bindus belongs to an ashtakavarga role")
            elif role == "graha_class":
                pass  # class handled below
            else:
                self.q(Reason.OPERAND_SOURCE_UNMAPPED, oid, f"{role} x {rel} has no source in the E0 matrix")
            source = {"table": None, "key": None, "status": "unmapped"}
        source = dict(source)
        if source.get("status") == "non_unique":
            self.q(Reason.NON_UNIQUE_LOOKUP, oid, source.get("uniqueness", "non-unique lookup"))
        if source.get("convention_pending"):
            self.pending.add(source["convention_pending"])
        if source.get("status") == "gap":
            self.pending.add(f"source_gap:{role}.{rel}")

        # graha binding
        if role == "graha_class" or gclass:
            self._graha_class(oid, gclass)
        elif role in C.ROLES_NEEDING_GRAHA and not graha:
            self.q(Reason.UNBOUND_OPERAND, oid, f"{role} needs one graha; none is bound")

        # mean / node model
        node_model = None
        may_be_node = (graha in C.NODES) or (
            graha is None and role in ("dasha_lord", "antardasha_lord", "transiting_graha", "natal_graha", "bhava_lord")
        )
        if may_be_node:
            node_model = C.NODE_MODEL_BY_PLANE[plane]
        says_mean = bool(_RE["MEAN_TERMS_RE"].search(terms))
        says_true = bool(_RE["TRUE_NODE_TERMS_RE"].search(terms))
        if graha in C.NODES:
            if (says_mean and node_model != "mean") or (says_true and node_model != "true"):
                stated = "mean" if says_mean else "true"
                self.q(
                    Reason.NODE_MODEL_MISMATCH,
                    oid,
                    f"verse states the {stated} node; the {plane} source is {node_model}",
                )
        elif says_mean:
            self.q(Reason.MEAN_OPERAND, oid, "madhya/mean position named; no mean-motion source in v1")

        # bhāvas, groups, targets
        bhavas: Tuple[int, ...] = ()
        if rel != "vedha_by":
            bl = ([op["bhava"]] if op.get("bhava") else []) + list(op.get("target_bhavas") or [])
            bhavas = tuple(sorted(set(int(b) for b in bl)))
        group = op.get("bhava_group")
        if group is not None:
            if group not in C.BHAVA_GROUPS:
                self.q(Reason.SCHEMA_INVALID, oid, f"bhava_group {group!r} unknown")
            elif group in C.BHAVA_GROUPS_DF02_OPEN:
                self.q(
                    Reason.BHAVA_GROUP_DF02_OPEN,
                    oid,
                    f"{group}: cockpit DF-02 open (L0 group incomplete); package set is cited but held",
                )
        if rel == "in_bhava_group" and group is None:
            self.q(Reason.TARGET_UNBOUND, oid, "in_bhava_group without bhava_group")
        tr = op.get("target_role")
        if tr is not None:
            if tr not in self.ops:
                self.q(Reason.DANGLING_OPERAND_REF, oid, f"target_role {tr!r} undeclared")
            else:
                self.referenced.add(tr)
        if rel in ("transits", "occupies", "aspects") and not bhavas and not group and not tr:
            linked = self.frame == "sign_of_transit_only" and self.linked_by.get(oid)
            if not linked:
                self.q(Reason.TARGET_UNBOUND, oid, f"{rel} has no bhava, group or linked sign")

        comparison = None
        if rel == "bindus":
            comparison = self._bindus(oid, op, terms)
        obstructors = None
        if rel == "vedha_by":
            obstructors = self._vedha(oid, op, terms)
        return Pred(
            operand_id=oid,
            role=role,
            relation=rel,
            plane=plane,
            frame=self.frame,
            source=source,
            graha=graha,
            graha_class=gclass,
            bhavas=bhavas,
            bhava_group=group,
            target_role=tr,
            node_model=node_model,
            comparison=comparison,
            obstructors=obstructors,
        )

    def _graha_class(self, oid: str, gclass: Optional[str]) -> None:
        entry = C.GRAHA_CLASS_TABLE.get(gclass) if gclass else None
        if entry is None:
            self.q(Reason.UNBOUND_OPERAND, oid, "graha_class operand without a class")
            return
        if not entry["sense_pinned"]:
            self.q(Reason.GRAHA_CLASS_SENSE_UNPINNED, oid, f"{gclass}: natural vs functional not pinned")
        # Every class admits the Moon and Mercury only under a condition; v1.1
        # has no field to carry the verse's condition (DF-01).
        self.q(
            Reason.GRAHA_CLASS_CONDITION_MISSING,
            oid,
            f"{gclass}: Moon/Mercury membership needs the verse's condition (paksha / association); DF-01",
        )

    def _bindus(self, oid: str, op: Mapping[str, Any], terms: str) -> Optional[Comparison]:
        if not op.get("target_role") and not op.get("bhava"):
            self.q(Reason.BINDU_TARGET_UNLINKED, oid, "no target_role/bhava naming the sign whose bindus are read")
        # convention
        conv_map = C.bindu_conventions()
        haystack = terms
        meaning = None
        if _RE["SELF_DECLARED_BENEFIC_RE"].search(haystack):
            meaning = conv_map["self_declaring"]["benefic_dot"]["meaning"]
        else:
            text_conv = (conv_map.get("texts") or {}).get(self.text_id or "", {})
            if _RE["REKHA_TERMS_RE"].search(haystack):
                meaning = (text_conv.get("rekha") or {}).get("meaning")
            elif _RE["DOT_TERMS_RE"].search(haystack):
                meaning = (text_conv.get("dot") or {}).get("meaning")
        if meaning == "malefic":
            self.q(
                Reason.BINDU_CONVENTION_UNDECLARED, oid, "malefic-count convention: no 8 - n rewrite exists (CR-006)"
            )
            meaning = None
        elif meaning != "benefic":
            meaning = None  # absent or 'undeclared' in the map: typed absence, never a polarity
            self.q(
                Reason.BINDU_CONVENTION_UNDECLARED,
                oid,
                f"count term not declared for text {self.text_id!r} in bindu_conventions.json",
            )
        # comparator: exactly one bindus_of_8 for exactly one bindus operand
        items = [i for i in (self.card["field7_discrete_arithmetic"] or []) if i.get("kind") == "bindus_of_8"]
        n_bindu_ops = sum(1 for o in self.ops.values() if o.get("relation") == "bindus")
        if not items:
            self.q(Reason.MISSING_COMPARATOR, oid, "no field-7 bindus_of_8; no threshold is supplied")
            return None
        if len(items) != 1 or n_bindu_ops != 1:
            self.q(
                Reason.AMBIGUOUS_COMPARATOR_BINDING,
                oid,
                f"{len(items)} comparator(s) for {n_bindu_ops} bindus operand(s)",
            )
            return None
        if meaning is None:
            return None
        return Comparison(
            kind="bindus_of_8",
            op=items[0]["comparator"],
            value=int(items[0]["bindus"]),
            count_convention=f"{meaning}_points",
        )

    def _vedha(self, oid: str, op: Mapping[str, Any], terms: str) -> Optional[ObstructorSet]:
        primary = op.get("doctrinal_graha")
        if not op.get("target_bhavas"):
            self.q(Reason.TARGET_UNBOUND, oid, "vedha_by without the vedha place (target_bhavas)")
        if _RE["VEDHA_EXEMPTION_RE"].search(terms) or (
            _RE["VEDHA_TERMS_RE"].search(self.quote) and _RE["VEDHA_EXEMPTION_RE"].search(self.quote)
        ):
            self.q(
                Reason.VEDHA_EXEMPTION_NOT_ENCODABLE,
                oid,
                "cited verse exempts an obstructor; v1.1 has no exemption field (schema v1.2 proposal)",
            )
        if not primary:
            self.q(
                Reason.UNDECLARED_OBSTRUCTOR_SET, oid, "vedha primary graha unbound; obstructor set cannot be formed"
            )
            return None
        if _RE["OBSTRUCTOR_CLASS_RE"].search(terms):
            self.q(Reason.UNDECLARED_OBSTRUCTOR_SET, oid, "obstructors named as a class; the set is not declared")
            return None
        undeclared = tuple(g for g in C.VEDHA_UNDECLARED_OBSTRUCTORS if g != primary)
        certain = tuple(g for g in C.GRAHAS if g != primary and g not in C.VEDHA_UNDECLARED_OBSTRUCTORS)
        self.pending.add("vedha_obstructor_status_moon_nodes")
        return ObstructorSet(primary=primary, certain=certain, undeclared=undeclared, exempt=())

    # whole-card checks -----------------------------------------------------------
    def _plane_roles(self, gate: Node) -> None:
        roles = {p.role for p in iter_preds(gate)}
        planes = {C.ROLE_PLANE[r] for r in roles}
        if self.category == "transit" and "transiting_graha" not in roles:
            self.q(Reason.PLANE_ROLE_CONTRADICTION, None, "transit card without a transiting_graha predicate")
        if self.category == "dasha" and not roles & {"dasha_lord", "antardasha_lord"}:
            self.q(Reason.PLANE_ROLE_CONTRADICTION, None, "dasha card without a dasha-lord predicate")
        if self.category == "natal_promise" and planes & {"transit", "dasha"}:
            self.q(Reason.PLANE_ROLE_CONTRADICTION, None, "natal_promise card with time-varying predicates")

    def _tautologies(self, gate: Node) -> None:
        pairs = ({"benefic", "malefic"}, {"natural_benefic", "natural_malefic"})

        def walk(n: Node) -> None:
            if isinstance(n, Or):
                classes = {a.graha_class for a in n.args if isinstance(a, Pred) and a.graha_class}
                if any(p <= classes for p in pairs):
                    self.q(Reason.TAUTOLOGICAL_DISJUNCTION, None, "OR of complementary graha classes")
            if isinstance(n, (And, Or)):
                for a in n.args:
                    walk(a)
            elif isinstance(n, Not):
                walk(n.arg)

        walk(gate)

    def _exceptions(self) -> Tuple[ExceptionNode, ...]:
        out = []
        for i, exc in enumerate(self.card["field6_exceptions"] or []):
            effect, scope = exc.get("effect"), exc.get("school_scope")
            if effect not in C.EXCEPTION_EFFECTS or scope not in (
                set(C.SCHOOL_SCOPE_TEXTS) | set(C.NON_DEFAULT_SCOPES)
            ):
                self.fatal(Reason.SCHEMA_INVALID, None, f"exception {i}: effect/school_scope not in the enum")
                continue
            ecite = exc.get("citation") or {}
            equote = ecite.get("quote") or self.quote
            try:
                cond = self._build(exc.get("condition"), equote, f"exception {i}")
            except _Unbuildable:
                continue
            if scope in C.NON_DEFAULT_SCOPES:
                texts: Tuple[str, ...] = ()
                served = False
            else:
                listed = C.SCHOOL_SCOPE_TEXTS[scope]
                if listed == "card_text":
                    texts, served = ((self.text_id,) if self.text_id else ()), True
                else:
                    self.q(
                        Reason.SCHOOL_SCOPE_TEXTS_UNDECLARED,
                        None,
                        f"exception {i}: scope {scope} has no explicit text list (Q10)",
                    )
                    texts, served = (), True
            out.append(
                ExceptionNode(
                    condition=cond,
                    effect=effect,
                    school_scope=scope,
                    scope_texts=texts,
                    default_served=served,
                    passage_ids=tuple(ecite.get("passage_ids") or ()),
                )
            )
        return tuple(out)

    # assembly --------------------------------------------------------------------
    def _result(self, gate: Optional[Node], excs: Sequence[ExceptionNode], referenced: Iterable[str]) -> CompileResult:
        uniq = {(f.reason.value, f.operand_id or "", f.detail): f for f in self.findings}
        findings = [uniq[k] for k in sorted(uniq)]
        status = "active" if not findings and gate is not None and not self.unbuildable else "quarantined_not_evaluable"
        pending = sorted(self.pending)
        if gate is None or self.unbuildable:
            return CompileResult(self.card_id, "quarantined_not_evaluable", findings, convention_pending=pending)
        ir = self._ir(gate, excs, status, findings, pending, set(referenced))
        # logic_sha256: the card's logic with drafter-chosen operand ids renamed
        # positionally, so consolidated members drafted independently compare equal.
        names: Dict[str, str] = {}
        logic = _alpha_rename({"gate": ir["gate"], "exceptions": ir["exceptions"]}, names)
        logic.update({k: ir[k] for k in ("category", "polarity", "provenance")})
        logic["frame"] = ir["frame"]["declared"]
        return CompileResult(
            self.card_id,
            status,
            findings,
            ir=ir,
            ir_sha256=sha256_hex(ir),
            logic_sha256=sha256_hex(logic),
            gate=gate,
            exceptions=tuple(excs),
            convention_pending=pending,
        )

    def _ir(
        self,
        gate: Node,
        excs: Sequence[ExceptionNode],
        status: str,
        findings: List[Finding],
        pending: List[str],
        referenced: set,
    ) -> Dict[str, Any]:
        card = self.card
        verse = card["provenance"] == "verse_cited"
        preds = list(iter_preds(gate))
        relevant = (
            self.frame in C.FRAMES_OF_ROLE
            or self.frame == "sign_of_transit_only"
            or any(p.bhavas or p.bhava_group or p.obstructors or p.target_role for p in preds)
        )
        fc = self.f3.get("frame_citation") or {}
        kind, ref_src = C.FRAME_SOURCES.get(self.frame, (None, None))
        gap = any(p.source.get("status") == "gap" for p in preds)
        return {
            "ast_version": C.AST_VERSION,
            "compiler_version": C.COMPILER_VERSION,
            "graha_class_table_version": C.GRAHA_CLASS_TABLE_VERSION,
            "bhava_groups_version": C.BHAVA_GROUPS_VERSION,
            "card_id": self.card_id,
            "schema_version": card["schema_version"],
            "status": status,
            "category": self.category,
            "polarity": card["polarity"],
            "provenance": card["provenance"],
            "counting": {"counts_toward_n": bool(verse and status == "active"), "testimony": not verse},
            "class_groups": sorted(self.class_groups),
            "frame": {
                "declared": self.frame,
                "frame_role": self.f3.get("frame_role"),
                "attested": bool(self.f3.get("frame_terms") or fc.get("passage_ids")),
                "relevance": "relevant" if relevant else "invariant",
                "frames_py_kind": kind,
                "reference_sign_source": ref_src,
                "role_operand": self.frame_role_pred.to_json() if self.frame_role_pred else None,
            },
            "citation": {
                "text_id": self.text_id,
                "chunk_id": self.cite.get("chunk_id"),
                "locus": self.cite.get("locus"),
                "passage_ids": list(self.cite.get("passage_ids") or []),
                "quote_sha256": hashlib.sha256(self.quote.encode("utf-8")).hexdigest() if self.quote else None,
                "frame_passage_ids": list(fc.get("passage_ids") or []),
            },
            "gate": gate.to_json(),
            "exceptions": [e.to_json() for e in excs],
            "convention_pending": pending,
            "assessability": "not_assessed_by_gap" if gap else "evaluable",
            "unused_operands": sorted(set(self.ops) - referenced),
            "quarantine": [f.to_json() for f in findings],
        }


def _alpha_rename(obj: Any, names: Dict[str, str]) -> Any:
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            if k in ("operand_id", "target_role") and isinstance(v, str):
                out[k] = names.setdefault(v, f"o{len(names)}")
            else:
                out[k] = _alpha_rename(v, names)
        return out
    if isinstance(obj, list):
        return [_alpha_rename(v, names) for v in obj]
    return obj


def compile_card(card: Mapping[str, Any]) -> CompileResult:
    """Compile one Rule Card v1.1 dict. Pure, deterministic, no I/O beyond the package data files."""
    return _CardCompiler(card).run()


def compile_cards(cards: Iterable[Mapping[str, Any]]) -> List[CompileResult]:
    return [compile_card(c) for c in cards]
