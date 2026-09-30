"""Predicate evaluator (GOCHARA_DESIGN_SPECS_v1_4 §2.1 predicate contract).

Operators: eq | in_set | within_orb | house_from | overlaps |
period_running_at | declaration_exists. Tri-state true|false|unknown;
unknown ≠ false (unknown_is_false: false) — an unknown necessary predicate
makes admission `unqualified`, never excluded (§2.2 inv 2).
"""
from __future__ import annotations

from typing import Any

TRUE = "true"
FALSE = "false"
UNKNOWN = "unknown"

OPERATORS = frozenset({
    "eq", "in_set", "within_orb", "house_from", "overlaps",
    "period_running_at", "declaration_exists",
})

ADMITTED = "admitted"
EXCLUDED = "excluded"
UNQUALIFIED = "unqualified"


def _state(ok: bool | None):
    return UNKNOWN if ok is None else (TRUE if ok else FALSE)


def evaluate(operator: str, operands: dict[str, Any]) -> str:
    """Evaluate one predicate to a tri-state. Any missing (None) operand
    yields UNKNOWN — never FALSE."""
    if operator not in OPERATORS:
        raise ValueError(f"unknown predicate operator {operator!r}")

    if operator == "eq":
        a, b = operands.get("a"), operands.get("b")
        return _state(None if a is None or b is None else a == b)

    if operator == "in_set":
        x, s = operands.get("value"), operands.get("set")
        return _state(None if x is None or s is None else x in s)

    if operator == "within_orb":
        delta, orb = operands.get("delta_deg"), operands.get("orb_deg")
        return _state(None if delta is None or orb is None else abs(delta) <= orb)

    if operator == "house_from":
        house, houses = operands.get("house"), operands.get("houses")
        return _state(None if house is None or houses is None else house in houses)

    if operator == "overlaps":
        # half-open [start, end) overlap (§4.0 interval convention)
        a, b = operands.get("a"), operands.get("b")
        if a is None or b is None:
            return UNKNOWN
        return _state(a[0] < b[1] and b[0] < a[1])

    if operator == "period_running_at":
        rows, t = operands.get("rows"), operands.get("t")
        if rows is None or t is None:
            return UNKNOWN
        return _state(any(r["start_iso"] <= t < r["end_iso"] for r in rows))

    if operator == "declaration_exists":
        declarations, key = operands.get("declarations"), operands.get("key")
        if declarations is None or key is None:
            return UNKNOWN
        return _state(key in declarations)

    raise AssertionError("unreachable")


def admission_state(necessary_states: list[str]) -> str:
    """Admission over a path's necessary predicates (§2.2 inv 2):
    any false ⇒ excluded; else any unknown ⇒ unqualified; else admitted."""
    if any(s == FALSE for s in necessary_states):
        return EXCLUDED
    if any(s == UNKNOWN for s in necessary_states):
        return UNQUALIFIED
    return ADMITTED
