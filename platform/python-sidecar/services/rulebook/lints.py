"""Rule Book engine (packet E1) — lints.

Severity:
- ``build_fail``  — P4 semantics, licence, testimony counting. CI fails.
- ``panel_return`` — vedha clause missing, frame unattested / sign_intrinsic
  proposal. The card goes back to the panel through the change register.

Lints read the raw card and/or the compiled IR. They never resolve a value.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import constants as C
from .ast import And, Node, Not, Or, Pred

BUILD_FAIL = "build_fail"
PANEL_RETURN = "panel_return"

_VEDHA_RE = re.compile(C.VEDHA_TERMS_RE, re.IGNORECASE)
_PID_TEXT_RE = re.compile(r"^([a-z0-9_]+?)(?:_v\d+)?_pg\d{4}_c\d{2}:")
_DNF_CAP = 4096
_P4_GRAHAS = frozenset({"guru", "shani"})
_P4_RELATIONS = frozenset({"transits", "occupies", "aspects", "in_bhava_group"})


@dataclass(frozen=True)
class LintFinding:
    lint: str
    code: str
    severity: str
    card_id: str
    detail: str

    def to_json(self) -> dict:
        return {
            "lint": self.lint,
            "code": self.code,
            "severity": self.severity,
            "card_id": self.card_id,
            "detail": self.detail,
        }


# ── P4 (D4): never require Jupiter and Saturn in transit on a shared target ──
# Works on a neutral "atom" form so that raw cards (even quarantined ones) and
# compiled ASTs are checked by the same code.
@dataclass(frozen=True)
class _Atom:
    oid: str
    role: str
    relation: str
    graha: Optional[str]
    frame: str
    houses: FrozenSet[int]
    target_role: Optional[str]


def _dnf(node: Any, kind_of, args_of, atom_of) -> List[FrozenSet[_Atom]]:
    """Positive-literal DNF: each clause is a set of atoms some firing requires."""
    kind = kind_of(node)
    if kind == "atom":
        return [frozenset({atom_of(node)})]
    if kind == "not":
        return [frozenset()]  # a negation requires no positive placement
    parts = [_dnf(a, kind_of, args_of, atom_of) for a in args_of(node)]
    if kind == "or":
        out = [c for p in parts for c in p]
    else:  # and
        out = [frozenset()]
        for p in parts:
            out = [a | b for a in out for b in p]
            if len(out) > _DNF_CAP:
                raise OverflowError("DNF expansion exceeds the cap")
    if len(out) > _DNF_CAP:
        raise OverflowError("DNF expansion exceeds the cap")
    return out


def _shared(j: _Atom, s: _Atom) -> bool:
    if j.target_role and j.target_role == s.oid or s.target_role and s.target_role == j.oid:
        return True
    if j.target_role and j.target_role == s.target_role:
        return True
    return j.frame == s.frame and bool(j.houses & s.houses)


def _clause_violations(clauses: Iterable[FrozenSet[_Atom]]) -> List[str]:
    out = []
    for clause in clauses:
        transit = [
            a for a in clause if a.role == "transiting_graha" and a.relation in _P4_RELATIONS and a.graha in _P4_GRAHAS
        ]
        jup = [a for a in transit if a.graha == "guru"]
        sat = [a for a in transit if a.graha == "shani"]
        for j, s in itertools.product(jup, sat):
            if _shared(j, s):
                out.append(f"requires guru ({j.oid}) and shani ({s.oid}) in transit on a shared target")
    return sorted(set(out))


def _houses(bhavas: Sequence[int], group: Optional[str]) -> FrozenSet[int]:
    hs = set(int(b) for b in bhavas)
    if group in C.BHAVA_GROUPS:
        hs |= set(C.BHAVA_GROUPS[group]["members"])
    return frozenset(hs)


def p4_violations_ast(nodes: Iterable[Node]) -> List[str]:
    def kind_of(n: Node) -> str:
        return {Pred: "atom", Not: "not", And: "and", Or: "or"}[type(n)]

    def args_of(n: Node):
        return n.args

    def atom_of(p: Pred) -> _Atom:
        return _Atom(
            p.operand_id, p.role, p.relation, p.graha, p.frame, _houses(p.bhavas, p.bhava_group), p.target_role
        )

    out: List[str] = []
    for n in nodes:
        try:
            out.extend(_clause_violations(_dnf(n, kind_of, args_of, atom_of)))
        except OverflowError as exc:
            out.append(f"unanalysable: {exc}")
    return sorted(set(out))


def p4_violations_card(card: Mapping[str, Any]) -> List[str]:
    """P4 on the raw card: runs even when the card cannot compile."""
    frame = ((card.get("field3_reference_frame") or {}).get("frame")) or "<none>"
    ops: Dict[str, Mapping[str, Any]] = {}
    for op in card.get("field5_typed_operands") or []:
        ops[op.get("id")] = op
    for exc in card.get("field6_exceptions") or []:
        for op in exc.get("operands") or []:
            ops[op.get("id")] = op

    def kind_of(e: Mapping[str, Any]) -> str:
        if "operand" in e:
            return "atom"
        return {"AND": "and", "OR": "or", "NOT": "not"}.get(e.get("op"), "and")

    def args_of(e: Mapping[str, Any]):
        return e.get("args") or []

    def atom_of(e: Mapping[str, Any]) -> _Atom:
        op = ops.get(e["operand"]) or {}
        bl = ([op["bhava"]] if op.get("bhava") else []) + list(op.get("target_bhavas") or [])
        return _Atom(
            e["operand"],
            op.get("role", ""),
            op.get("relation", ""),
            op.get("doctrinal_graha"),
            frame,
            _houses(bl, op.get("bhava_group")),
            op.get("target_role"),
        )

    exprs = [(card.get("field4_necessary_gate") or {}).get("expr")]
    exprs += [exc.get("condition") for exc in card.get("field6_exceptions") or []]
    out: List[str] = []
    for e in exprs:
        if not isinstance(e, Mapping):
            continue
        try:
            out.extend(_clause_violations(_dnf(e, kind_of, args_of, atom_of)))
        except OverflowError as exc:
            out.append(f"unanalysable: {exc}")
    return sorted(set(out))


def lint_p4(card: Mapping[str, Any], result: Any = None) -> List[LintFinding]:
    cid = str(card.get("card_id"))
    viols = set(p4_violations_card(card))
    if result is not None and getattr(result, "gate", None) is not None:
        viols |= set(p4_violations_ast([result.gate] + [e.condition for e in result.exceptions]))
    return [LintFinding("p4", "P4_DOUBLE_TRANSIT", BUILD_FAIL, cid, v) for v in sorted(viols)]


# ── vedha ───────────────────────────────────────────────────────────────────
def lint_vedha(card: Mapping[str, Any]) -> List[LintFinding]:
    """A gochara card whose cited verse carries vedha must encode it."""
    cid = str(card.get("card_id"))
    ops = list(card.get("field5_typed_operands") or [])
    for exc in card.get("field6_exceptions") or []:
        ops.extend(exc.get("operands") or [])
    is_gochara = (card.get("field2_target_scope") or {}).get("category") == "transit" or any(
        o.get("role") == "transiting_graha" for o in ops
    )
    quote = (card.get("field1_citation") or {}).get("quote") or ""
    if not is_gochara or not _VEDHA_RE.search(quote):
        return []
    vedha_ids = {o.get("id") for o in ops if o.get("relation") == "vedha_by"}

    def refs(e: Any) -> set:
        if not isinstance(e, Mapping):
            return set()
        if "operand" in e:
            return {e["operand"]}
        return set().union(*[refs(a) for a in e.get("args") or []]) if e.get("args") else set()

    used = refs((card.get("field4_necessary_gate") or {}).get("expr"))
    for exc in card.get("field6_exceptions") or []:
        used |= refs(exc.get("condition"))
    if vedha_ids & used:
        return []
    return [
        LintFinding(
            "vedha",
            "VEDHA_CLAUSE_MISSING",
            PANEL_RETURN,
            cid,
            "cited verse carries a vedha clause; the card encodes no vedha_by in its gate or field-6",
        )
    ]


# ── frame ───────────────────────────────────────────────────────────────────
def lint_frame(card: Mapping[str, Any], result: Any) -> List[LintFinding]:
    cid = str(card.get("card_id"))
    out: List[LintFinding] = []
    f3 = card.get("field3_reference_frame")
    if not isinstance(f3, Mapping) or not f3.get("frame"):
        return [LintFinding("frame", "FRAME_MISSING", PANEL_RETURN, cid, "no frame; never defaulted")]
    cat = (card.get("field2_target_scope") or {}).get("category")
    if cat == "dasha" and f3.get("frame") == "sign_of_transit_only":
        out.append(
            LintFinding(
                "frame",
                "FRAME_PROPOSE_SIGN_INTRINSIC",
                PANEL_RETURN,
                cid,
                "dasha card on sign_of_transit_only; propose sign_intrinsic (F-S3)",
            )
        )
    ir = getattr(result, "ir", None)
    if ir is not None:
        fr = ir["frame"]
        if fr["relevance"] == "relevant" and not fr["attested"]:
            out.append(
                LintFinding(
                    "frame",
                    "FRAME_UNATTESTED",
                    PANEL_RETURN,
                    cid,
                    f"frame {fr['declared']} counts the predicate but no frame_terms/frame_citation states it",
                )
            )
    return out


# ── testimony never counts toward N ────────────────────────────────────────
def lint_testimony(ir: Mapping[str, Any]) -> List[LintFinding]:
    cid = str(ir.get("card_id"))
    out = []
    counting = ir.get("counting") or {}
    testimony = ir.get("provenance") != "verse_cited"
    if testimony and counting.get("counts_toward_n") is not False:
        out.append(
            LintFinding(
                "testimony", "TESTIMONY_COUNTED", BUILD_FAIL, cid, "commentarial_practice card would increment N"
            )
        )
    if counting.get("testimony") is not testimony:
        out.append(
            LintFinding(
                "testimony",
                "TESTIMONY_FLAG_INCONSISTENT",
                BUILD_FAIL,
                cid,
                "counting.testimony disagrees with provenance",
            )
        )
    if ir.get("status") != "active" and counting.get("counts_toward_n") is not False:
        out.append(
            LintFinding("testimony", "QUARANTINED_COUNTED", BUILD_FAIL, cid, "a non-active card would increment N")
        )
    for e in ir.get("exceptions") or []:
        if e.get("effect") in C.NOTE_ONLY_EFFECTS and e.get("increments_n") is not False:
            out.append(
                LintFinding(
                    "testimony",
                    "NOTE_EFFECT_COUNTED",
                    BUILD_FAIL,
                    cid,
                    f"{e.get('effect')} exception would increment N",
                )
            )
    return out


# ── licence ─────────────────────────────────────────────────────────────────
def _walk_quotes(obj: Any, inherited_text: Optional[str], path: str) -> Iterable[Tuple[str, str, set, Optional[str]]]:
    if isinstance(obj, Mapping):
        own_text = obj.get("text_id")
        texts = set()
        if own_text:
            texts.add(own_text)
        for pid in obj.get("passage_ids") or []:
            m = _PID_TEXT_RE.match(str(pid))
            texts.add(m.group(1) if m else f"<unparsed:{pid}>")
        q = obj.get("quote")
        if isinstance(q, str) and q.strip():
            if not texts and inherited_text:
                texts.add(inherited_text)
            yield path, q, texts, obj.get("edition")
        for k, v in obj.items():
            if k == "quote":
                continue
            yield from _walk_quotes(v, own_text or inherited_text, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_quotes(v, inherited_text, f"{path}[{i}]")


def lint_licence(card: Mapping[str, Any], allowlist: Optional[Mapping[str, Any]] = None) -> List[LintFinding]:
    """Quote text present for an edition outside the public-domain allowlist fails."""
    allow = allowlist if allowlist is not None else C.licence_allowlist()
    pd = {e["text_id"]: e.get("edition") for e in allow.get("public_domain") or []}
    cid = str(card.get("card_id"))
    top_text = (card.get("field1_citation") or {}).get("text_id")
    out = []
    for path, _q, texts, edition in _walk_quotes(card, top_text, "card"):
        if not texts:
            out.append(
                LintFinding(
                    "licence",
                    "QUOTE_EDITION_UNKNOWN",
                    BUILD_FAIL,
                    cid,
                    f"{path}: quote text with no identifiable edition",
                )
            )
            continue
        for t in sorted(texts):
            if t not in pd:
                out.append(
                    LintFinding(
                        "licence",
                        "QUOTE_RESTRICTED_EDITION",
                        BUILD_FAIL,
                        cid,
                        f"{path}: quote text for {t}, which is not on the public-domain allowlist",
                    )
                )
            elif edition and pd[t] and edition != pd[t]:
                out.append(
                    LintFinding(
                        "licence",
                        "QUOTE_EDITION_MISMATCH",
                        BUILD_FAIL,
                        cid,
                        f"{path}: edition differs from the allowlisted {t} edition",
                    )
                )
    return out


# ── runner ──────────────────────────────────────────────────────────────────
def run_lints(
    card: Mapping[str, Any], result: Any, *, allowlist: Optional[Mapping[str, Any]] = None
) -> List[LintFinding]:
    out: List[LintFinding] = []
    out += lint_p4(card, result)
    out += lint_vedha(card)
    out += lint_frame(card, result)
    if getattr(result, "ir", None) is not None:
        out += lint_testimony(result.ir)
    out += lint_licence(card, allowlist)
    return out


def build_ok(findings: Iterable[LintFinding]) -> bool:
    return not any(f.severity == BUILD_FAIL for f in findings)
