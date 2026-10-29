"""Rule Book engine (E3) — rule state per day for one chart.

``evaluate_plan`` walks a card's gate with strong Kleene connectives (the reference
semantics in ``..ast``) over predicate series. A rule with several member cards
(the consolidation key merged them) takes the cards' common state; where member
cards disagree on a day the rule is NOT_ASSESSED that day (the encodings are rival
readings of one rule: neither wins by order). A node-excluded or unsupported card is
never evaluated.

``tally_day`` is the plan §3 N-of-3 count for one day, delegated to ``..ast.tally``:
only active, verse-cited cards increment N; testimony is a separate flagged count.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..ast import And, CardOutcome, NOT_ASSESSED, Node, Not, Or, Pred, Tri, k_and, k_not, k_or, tally
from . import constants as K
from .plan import CardPlan
from .resolve import EvalContext
from .series import Series


class NotEvaluable(RuntimeError):
    """The card is node-excluded (or otherwise not evaluable) and must not be evaluated."""


def evaluate_plan(plan: CardPlan, ctx: EvalContext) -> Series:
    if plan.excluded_node:
        raise NotEvaluable(f"{plan.card_id}: reads a node position ({', '.join(plan.node_named)}); excluded (DF-03)")
    return _eval(plan.gate, plan, ctx)


def _eval(node: Node, plan: CardPlan, ctx: EvalContext) -> Series:
    if isinstance(node, Pred):
        return ctx.pred(plan.preds[node.operand_id], plan.frame)
    if isinstance(node, And):
        return Series.zip(k_and, *(_eval(a, plan, ctx) for a in node.args))
    if isinstance(node, Or):
        return Series.zip(k_or, *(_eval(a, plan, ctx) for a in node.args))
    if isinstance(node, Not):
        return _eval(node.arg, plan, ctx).map(k_not)
    raise TypeError(f"not an AST node: {type(node).__name__}")  # pragma: no cover


def _agree(*states: Tri) -> Tri:
    first = states[0]
    return first if all(s is first for s in states) else NOT_ASSESSED


def combine_member_cards(series: Sequence[Series]) -> Series:
    """The rule's state from its member cards' states: common value, else NOT_ASSESSED."""
    if len(series) == 1:
        return series[0]
    return Series.zip(_agree, *series)


def card_outcome_at(plan: CardPlan, state: Tri) -> CardOutcome:
    """The CardOutcome ``..ast.tally`` consumes. No active card has an exception in v1."""
    testimony = plan.provenance != "verse_cited"
    return CardOutcome(plan.card_id, plan.category, plan.polarity, state, not testimony, testimony, ())


def tally_day(outcomes: Iterable[CardOutcome], polarity: str) -> dict:
    """Plan §3 for one day and one polarity (promotive and obstructive are never summed)."""
    return tally(outcomes, polarity)
