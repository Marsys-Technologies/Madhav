"""Rule Book engine (packet E1) — the closed AST.

Node types are fixed here and nowhere else (ENGINE_PLAN v0.2 §2.1, M11):

- ``Pred``  — one typed predicate (role, relation, graha | graha_class, bhāva
  set, frame). It records the frame and the operand source it will need
  (fact_key / L0 table per E0's matrix) and the node model it requires. No
  value is resolved here.
- ``And`` / ``Or`` / ``Not`` — strong Kleene connectives. ``Or`` exists only
  where the cited verse states a disjunction (the compiler checks).
- ``Comparison`` — attached to a predicate; operators are exactly the ones
  field 7 admits (eq/ge/le/gt/lt over bindus_of_8).

There is no eval of card strings anywhere in this package.

The module also carries the *reference semantics* the E3 evaluator must
reproduce: Kleene truth tables, the exception table of plan §2.4 and the N
tally of plan §3. These operate on truth values supplied by the caller; they
never look anything up.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

from . import constants as C


# ── three-valued logic ─────────────────────────────────────────────────────
class NotAssessedError(TypeError):
    """Raised when NOT_ASSESSED is used where a Python bool is expected."""


class Tri(enum.Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    NOT_ASSESSED = "NOT_ASSESSED"

    def __bool__(self) -> bool:  # §N.7.6: an honest null is never coerced
        if self is Tri.NOT_ASSESSED:
            raise NotAssessedError("NOT_ASSESSED used as a Python bool")
        raise TypeError("Tri is not a bool; compare with `is Tri.TRUE`")

    @classmethod
    def of(cls, value: bool) -> "Tri":
        if not isinstance(value, bool):
            raise TypeError(f"Tri.of expects bool, got {type(value).__name__}")
        return cls.TRUE if value else cls.FALSE


NOT_ASSESSED = Tri.NOT_ASSESSED


def k_and(*vals: Tri) -> Tri:
    """Strong Kleene AND: F dominates, then NA, else T."""
    _check(vals)
    if any(v is Tri.FALSE for v in vals):
        return Tri.FALSE
    if any(v is Tri.NOT_ASSESSED for v in vals):
        return Tri.NOT_ASSESSED
    return Tri.TRUE


def k_or(*vals: Tri) -> Tri:
    """Strong Kleene OR: T dominates, then NA, else F."""
    _check(vals)
    if any(v is Tri.TRUE for v in vals):
        return Tri.TRUE
    if any(v is Tri.NOT_ASSESSED for v in vals):
        return Tri.NOT_ASSESSED
    return Tri.FALSE


def k_not(val: Tri) -> Tri:
    _check((val,))
    if val is Tri.NOT_ASSESSED:
        return Tri.NOT_ASSESSED
    return Tri.FALSE if val is Tri.TRUE else Tri.TRUE


def _check(vals: Iterable[Any]) -> None:
    vals = tuple(vals)
    if not vals:
        raise ValueError("Kleene connective needs at least one argument")
    for v in vals:
        if not isinstance(v, Tri):
            raise TypeError(f"expected Tri, got {type(v).__name__}")


def render_tri(val: Tri) -> str:
    """The only renderer: NOT_ASSESSED is never shown as false or 0."""
    _check((val,))
    return {Tri.TRUE: "true", Tri.FALSE: "false", Tri.NOT_ASSESSED: "not_assessed"}[val]


# ── nodes ──────────────────────────────────────────────────────────────────
COMPARATORS = ("eq", "ge", "le", "gt", "lt")


@dataclass(frozen=True)
class Comparison:
    kind: str            # field-7 kind; v1 admits bindus_of_8 only
    op: str              # one of COMPARATORS
    value: int
    count_convention: str  # e.g. "benefic_points"; never defaulted

    def __post_init__(self) -> None:
        if self.op not in COMPARATORS:
            raise ValueError(f"comparator {self.op!r} not in the closed set")
        if self.kind != "bindus_of_8":
            raise ValueError(f"comparison kind {self.kind!r} not in the closed set")
        if not (isinstance(self.value, int) and 0 <= self.value <= 8):
            raise ValueError("bindus_of_8 value must be an int 0..8")

    def to_json(self) -> dict:
        return {"kind": self.kind, "op": self.op, "value": self.value,
                "count_convention": self.count_convention}


@dataclass(frozen=True)
class ObstructorSet:
    """Vedha obstructors. ``undeclared`` members make an occupancy NA, never F."""
    primary: str
    certain: Tuple[str, ...]
    undeclared: Tuple[str, ...]
    exempt: Tuple[str, ...]  # always empty in v1.1: the schema cannot encode it

    def to_json(self) -> dict:
        return {"primary": self.primary, "certain": list(self.certain),
                "undeclared": list(self.undeclared), "exempt": list(self.exempt)}


@dataclass(frozen=True)
class Pred:
    operand_id: str
    role: str
    relation: str
    plane: str                      # natal | dasha | transit (where the value comes from)
    frame: str                      # the card's declared frame; never defaulted
    source: Mapping[str, Any]       # E0 matrix descriptor (table, key, status, ...)
    graha: Optional[str] = None
    graha_class: Optional[str] = None
    bhavas: Tuple[int, ...] = ()
    bhava_group: Optional[str] = None
    target_role: Optional[str] = None
    node_model: Optional[str] = None  # required node model when the graha may be a node
    comparison: Optional[Comparison] = None
    obstructors: Optional[ObstructorSet] = None

    def to_json(self) -> dict:
        out: dict = {
            "node": "pred", "operand_id": self.operand_id, "role": self.role,
            "relation": self.relation, "plane": self.plane, "frame": self.frame,
            "source": dict(self.source), "graha": self.graha, "graha_class": self.graha_class,
            "bhavas": list(self.bhavas), "bhava_group": self.bhava_group,
            "target_role": self.target_role, "node_model": self.node_model,
        }
        out["comparison"] = self.comparison.to_json() if self.comparison else None
        out["obstructors"] = self.obstructors.to_json() if self.obstructors else None
        return out


@dataclass(frozen=True)
class And:
    args: Tuple["Node", ...]

    def to_json(self) -> dict:
        return {"node": "and", "args": [a.to_json() for a in self.args]}


@dataclass(frozen=True)
class Or:
    args: Tuple["Node", ...]
    verse_disjunction: bool = True  # the compiler only builds Or when the verse states one

    def __post_init__(self) -> None:
        if not self.verse_disjunction:
            raise ValueError("Or exists only for a disjunction the verse states")

    def to_json(self) -> dict:
        return {"node": "or", "verse_disjunction": True, "args": [a.to_json() for a in self.args]}


@dataclass(frozen=True)
class Not:
    arg: "Node"

    def to_json(self) -> dict:
        return {"node": "not", "arg": self.arg.to_json()}


Node = Union[Pred, And, Or, Not]


@dataclass(frozen=True)
class ExceptionNode:
    condition: Node
    effect: str            # cancels | reduces | reverses_polarity | delays
    school_scope: str
    scope_texts: Tuple[str, ...]
    default_served: bool   # False for nadi/kerala/tajaka (drill-down alternates)
    passage_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.effect not in C.EXCEPTION_EFFECTS:
            raise ValueError(f"exception effect {self.effect!r} not in the closed set")

    @property
    def increments_n(self) -> bool:
        return self.effect not in C.NOTE_ONLY_EFFECTS

    def to_json(self) -> dict:
        return {"condition": self.condition.to_json(), "effect": self.effect,
                "school_scope": self.school_scope, "scope_texts": list(self.scope_texts),
                "default_served": self.default_served, "increments_n": self.increments_n,
                "passage_ids": list(self.passage_ids)}


def iter_preds(node: Node) -> Iterable[Pred]:
    if isinstance(node, Pred):
        yield node
    elif isinstance(node, (And, Or)):
        for a in node.args:
            yield from iter_preds(a)
    elif isinstance(node, Not):
        yield from iter_preds(node.arg)
    else:  # pragma: no cover - closed set
        raise TypeError(f"not an AST node: {type(node).__name__}")


# ── reference semantics (what E3 must reproduce) ───────────────────────────
class QuarantinedCardError(RuntimeError):
    """A quarantined card can never be evaluated or counted."""


def evaluate(node: Node, assignment: Mapping[str, Tri]) -> Tri:
    """Kleene evaluation over caller-supplied predicate truth values.

    A predicate missing from ``assignment`` is NOT_ASSESSED (a missing fact
    gives NA, Q1); it is never False.
    """
    if isinstance(node, Pred):
        v = assignment.get(node.operand_id, Tri.NOT_ASSESSED)
        _check((v,))
        return v
    if isinstance(node, And):
        return k_and(*(evaluate(a, assignment) for a in node.args))
    if isinstance(node, Or):
        return k_or(*(evaluate(a, assignment) for a in node.args))
    if isinstance(node, Not):
        return k_not(evaluate(node.arg, assignment))
    raise TypeError(f"not an AST node: {type(node).__name__}")  # pragma: no cover


@dataclass(frozen=True)
class CardOutcome:
    card_id: str
    category: str
    polarity: str                 # after any reverses_polarity
    state: Tri
    increments_n: bool            # False for testimony and for reduces/delays
    testimony: bool
    notes: Tuple[str, ...] = field(default=())


def card_outcome(ir: Mapping[str, Any], gate: Node, exceptions: Sequence[ExceptionNode],
                 assignment: Mapping[str, Tri]) -> CardOutcome:
    """Apply plan §2.4 to one compiled card.

    ``ir`` is the compiled IR dict (status, category, polarity, provenance);
    ``gate``/``exceptions`` are its AST. Exceptions outside the default scopes
    are recorded as alternates and not applied.
    """
    if ir.get("status") != "active":
        raise QuarantinedCardError(f"{ir.get('card_id')}: status {ir.get('status')!r} is never evaluated")
    testimony = ir["provenance"] != "verse_cited"
    polarity = ir["polarity"]
    state = evaluate(gate, assignment)
    increments = not testimony
    notes = []
    if state is Tri.FALSE:
        return CardOutcome(ir["card_id"], ir["category"], polarity, state, increments, testimony, ())
    for exc in exceptions:
        if not exc.default_served:
            notes.append(f"alternate:{exc.school_scope}:{exc.effect}")
            continue
        cond = evaluate(exc.condition, assignment)
        if cond is Tri.FALSE:
            continue
        if cond is Tri.NOT_ASSESSED:
            # NA in an exception propagates NA, whatever the effect (incl. a flip)
            state = Tri.NOT_ASSESSED
            notes.append(f"exception_not_assessed:{exc.effect}")
            continue
        if exc.effect == "cancels":
            state = Tri.FALSE
            notes.append("cancelled")
        elif exc.effect == "reverses_polarity":
            polarity = "obstructive" if polarity == "promotive" else "promotive"
            notes.append("polarity_reversed")
        else:  # reduces / delays: a qualified note, never an increment
            increments = False
            notes.append(f"qualified:{exc.effect}")
    return CardOutcome(ir["card_id"], ir["category"], polarity, state, increments, testimony, tuple(notes))


CATEGORY_STATUSES = ("matched", "not_matched", "not_assessed")


def tally(outcomes: Iterable[CardOutcome], polarity: str) -> dict:
    """Plan §3: per-category status for one polarity; N of 3; testimony apart.

    Only verse-cited outcomes with ``increments_n`` decide a category. A
    category with no such cards, or whose every card is NA, is
    ``not_assessed`` — never ``not_matched`` and never 0.
    """
    if polarity not in C.POLARITIES:
        raise ValueError(polarity)
    outcomes = list(outcomes)
    cats: dict = {}
    testimony_true = 0
    notes = 0
    for cat in C.CATEGORIES:
        rows = [o for o in outcomes if o.category == cat and o.polarity == polarity]
        counted = [o for o in rows if o.increments_n and not o.testimony]
        testimony_true += sum(1 for o in rows if o.testimony and o.state is Tri.TRUE)
        notes += sum(1 for o in rows if not o.testimony and not o.increments_n and o.state is Tri.TRUE)
        if not counted or all(o.state is Tri.NOT_ASSESSED for o in counted):
            cats[cat] = "not_assessed"
        elif any(o.state is Tri.TRUE for o in counted):
            cats[cat] = "matched"
        else:
            cats[cat] = "not_matched"
    return {
        "polarity": polarity,
        "categories": cats,
        "categories_matched": sum(1 for s in cats.values() if s == "matched"),
        "of": len(C.CATEGORIES),
        "testimony_matched_flagged": testimony_true,
        "qualified_notes": notes,
    }
